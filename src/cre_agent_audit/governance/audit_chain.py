"""Hash-chain Audit Ledger — ADR-0003.

Every decision event is appended to a chain where each entry contains the
SHA-256 hash of the previous entry. Tampering with any entry invalidates every
entry that follows. The ledger is append-only — corrections are new entries
that reference the prior entry's sequence, never edits.

The implementation is intentionally dependency-free (stdlib only) so the
governance ledger keeps writing even when the rest of the system is in
DEFCON-1 (per ADR-0001).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

GENESIS_PRIOR_HASH = "0" * 64
"""Sentinel value for the first entry's ``prior_hash``. SHA-256 zeroes."""


class ActorKind(Enum):
    AGENT = "agent"
    HUMAN = "human"
    SYSTEM = "system"


class AuditChainTamperError(RuntimeError):
    """Raised by ``AuditLedger.verify_chain`` when an inconsistency is detected.

    The error message names the failing sequence index and the failure mode
    (self_hash mismatch vs prior_hash mismatch) so a regulator-facing
    investigation can pinpoint the corruption window.
    """


@dataclass(frozen=True)
class AuditEntry:
    """One immutable ledger entry.

    The structure mirrors ADR-0003 verbatim. Fields are sorted in
    ``canonical_bytes_for_hashing`` so the SHA-256 input is deterministic
    across platforms and serializers.
    """

    sequence: int
    timestamp: datetime
    actor_kind: ActorKind
    actor_id: str
    decision_type: str
    action_payload: bytes
    gate_verdicts: dict[str, str]
    prior_hash: str
    self_hash: str
    corrects_sequence: int | None = None

    def canonical_bytes_for_hashing(self) -> bytes:
        """Return the bytes whose SHA-256 is ``self_hash``.

        Excludes ``self_hash`` itself (otherwise the hash includes itself,
        which is uncomputable). Order is fixed: sequence, timestamp ISO 8601,
        actor_kind value, actor_id, decision_type, action_payload (raw bytes),
        gate_verdicts (sorted JSON), prior_hash, corrects_sequence.
        """
        payload = {
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat(),
            "actor_kind": self.actor_kind.value,
            "actor_id": self.actor_id,
            "decision_type": self.decision_type,
            # action_payload is included verbatim — base64-encode for JSON safety,
            # decoders can recover original bytes from the hex digest at verify time.
            "action_payload_hex": self.action_payload.hex(),
            "gate_verdicts": dict(sorted(self.gate_verdicts.items())),
            "prior_hash": self.prior_hash,
            "corrects_sequence": self.corrects_sequence,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _compute_self_hash(
    *,
    sequence: int,
    timestamp: datetime,
    actor_kind: ActorKind,
    actor_id: str,
    decision_type: str,
    action_payload: bytes,
    gate_verdicts: dict[str, str],
    prior_hash: str,
    corrects_sequence: int | None,
) -> str:
    """Internal helper — compute self_hash before constructing the frozen entry."""
    payload = {
        "sequence": sequence,
        "timestamp": timestamp.isoformat(),
        "actor_kind": actor_kind.value,
        "actor_id": actor_id,
        "decision_type": decision_type,
        "action_payload_hex": action_payload.hex(),
        "gate_verdicts": dict(sorted(gate_verdicts.items())),
        "prior_hash": prior_hash,
        "corrects_sequence": corrects_sequence,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass
class AuditLedger:
    """Append-only ledger of governance decisions.

    The ledger is the system of record for every agent decision, every gate
    verdict, and every operator transition. There is no public delete or
    truncate API by design (ADR-0003 invariant).
    """

    _entries: list[AuditEntry] = field(default_factory=list, init=False, repr=False)

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        """Return an immutable view of the entries."""
        return tuple(self._entries)

    def append(
        self,
        *,
        actor_kind: ActorKind,
        actor_id: str,
        decision_type: str,
        action_payload: bytes,
        gate_verdicts: dict[str, str],
        now: datetime | None = None,
        corrects_sequence: int | None = None,
    ) -> AuditEntry:
        """Append a new entry to the ledger and return it."""
        sequence = len(self._entries)
        prior_hash = self.chain_head()
        timestamp = now or datetime.now(timezone.utc)

        # Defensive copy so the ledger entry cannot be mutated via caller-held dicts.
        gate_verdicts_copy = dict(gate_verdicts)

        self_hash = _compute_self_hash(
            sequence=sequence,
            timestamp=timestamp,
            actor_kind=actor_kind,
            actor_id=actor_id,
            decision_type=decision_type,
            action_payload=action_payload,
            gate_verdicts=gate_verdicts_copy,
            prior_hash=prior_hash,
            corrects_sequence=corrects_sequence,
        )
        entry = AuditEntry(
            sequence=sequence,
            timestamp=timestamp,
            actor_kind=actor_kind,
            actor_id=actor_id,
            decision_type=decision_type,
            action_payload=action_payload,
            gate_verdicts=gate_verdicts_copy,
            prior_hash=prior_hash,
            self_hash=self_hash,
            corrects_sequence=corrects_sequence,
        )
        self._entries.append(entry)
        return entry

    def append_correction(
        self,
        *,
        corrects_sequence: int,
        actor_kind: ActorKind,
        actor_id: str,
        action_payload: bytes,
        gate_verdicts: dict[str, str],
        reason: str,
        now: datetime | None = None,
    ) -> AuditEntry:
        """Append a correction entry that references a prior sequence.

        The correction does not edit the prior entry — it adds a new entry with
        ``decision_type="correction"`` and ``corrects_sequence=<prior>``.
        Reason is folded into ``gate_verdicts["correction_reason"]`` so it
        flows through the canonical hashing path.
        """
        if corrects_sequence < 0 or corrects_sequence >= len(self._entries):
            raise ValueError(f"corrects_sequence {corrects_sequence} not in ledger")
        if not reason.strip():
            raise ValueError("correction reason must be non-empty")

        gate_verdicts_with_reason = {**gate_verdicts, "correction_reason": reason}
        return self.append(
            actor_kind=actor_kind,
            actor_id=actor_id,
            decision_type="correction",
            action_payload=action_payload,
            gate_verdicts=gate_verdicts_with_reason,
            now=now,
            corrects_sequence=corrects_sequence,
        )

    def chain_head(self) -> str:
        """Return ``self_hash`` of the last entry, or the genesis sentinel if empty."""
        if not self._entries:
            return GENESIS_PRIOR_HASH
        return self._entries[-1].self_hash

    def verify_chain(self) -> None:
        """Raise ``AuditChainTamperError`` if any entry is inconsistent.

        Two failure modes are detected:
        - ``self_hash mismatch`` — the entry's stored ``self_hash`` does not match
          a freshly-computed hash of its canonical bytes (something inside the
          entry was changed after writing).
        - ``prior_hash mismatch`` — the entry's ``prior_hash`` does not match the
          previous entry's ``self_hash`` (chain link broken).
        """
        previous_self_hash = GENESIS_PRIOR_HASH
        for index, entry in enumerate(self._entries):
            recomputed = _compute_self_hash(
                sequence=entry.sequence,
                timestamp=entry.timestamp,
                actor_kind=entry.actor_kind,
                actor_id=entry.actor_id,
                decision_type=entry.decision_type,
                action_payload=entry.action_payload,
                gate_verdicts=entry.gate_verdicts,
                prior_hash=entry.prior_hash,
                corrects_sequence=entry.corrects_sequence,
            )
            if recomputed != entry.self_hash:
                raise AuditChainTamperError(
                    f"self_hash mismatch at sequence {entry.sequence} (index {index})"
                )
            if entry.prior_hash != previous_self_hash:
                raise AuditChainTamperError(
                    f"prior_hash mismatch at sequence {entry.sequence} (index {index}): "
                    f"expected {previous_self_hash!r}, got {entry.prior_hash!r}"
                )
            previous_self_hash = entry.self_hash

    # --------------------------------------------------------------------- #
    # Test seam — used only by unit tests to simulate disk-level corruption. #
    # Production callers should never invoke this method.                    #
    # --------------------------------------------------------------------- #
    def _replace_entry_for_tests(self, index: int, replacement: AuditEntry) -> None:
        self._entries[index] = replacement
