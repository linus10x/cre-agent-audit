"""Internally-Consistent Hash-Chained Audit Ledger — ADR-0003.

Every decision event is appended to a chain where each entry contains the
SHA-256 hash of the previous entry. Modifying any past entry breaks the
SHA-256 link at the modified point and every entry that follows — detectable
by an honest holder of the current chain head.

**Important framing.** This ledger is *internally consistent* by construction.
It is **not adversarially tamper-evident on its own**: an attacker with full
write access to the storage layer can regenerate the entire chain end-to-end,
and the regenerated chain will pass `verify_chain()`. For adversarial
integrity, the chain head (`chain_head()`) must be periodically anchored to
an **external witness register** that the deployer does not control alone:
OpenTimestamps, Sigstore Rekor, a regulator-side append-only log, or a
notarized blockchain anchor. Then post-incident the deployer can prove what
the chain head was at time T.

See ADR-0003 § "Audit evidence properties" for the SOC 2 / SOX 404 / FFIEC
framing, and ADR-0010 for retention, privilege, and discovery posture.

The implementation is intentionally dependency-free (stdlib only) so the
governance ledger keeps writing even when the rest of the system is in
DEFCON-1 (per ADR-0001).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cre_agent_audit.governance.ledger_store import LedgerStore
    from cre_agent_audit.governance.timestamp_source import TimestampSource

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
    timestamp_token_b64: str | None = None
    """Base64-encoded RFC 3161 TSR token (if a trusted TSA was used).
    None for local-clock entries (backward-compatible default)."""

    def canonical_bytes_for_hashing(self) -> bytes:
        """Return the bytes whose SHA-256 is ``self_hash``.

        Excludes ``self_hash`` itself (otherwise the hash includes itself,
        which is uncomputable). Order is fixed: sequence, timestamp ISO 8601,
        actor_kind value, actor_id, decision_type, action_payload (raw bytes),
        gate_verdicts (sorted JSON), prior_hash, corrects_sequence.
        """
        payload: dict[str, object] = {
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
        # Include token only when present — preserves backward-compat with
        # v0.2.0 ledgers that never had this field. Mixing local-clock and
        # TSA-stamped entries in the same ledger is supported.
        if self.timestamp_token_b64 is not None:
            payload["timestamp_token_b64"] = self.timestamp_token_b64
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
    timestamp_token_b64: str | None = None,
) -> str:
    """Internal helper — compute self_hash before constructing the frozen entry."""
    payload: dict[str, object] = {
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
    if timestamp_token_b64 is not None:
        payload["timestamp_token_b64"] = timestamp_token_b64
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass
class AuditLedger:
    """Append-only ledger of governance decisions.

    The ledger is the system of record for every agent decision, every gate
    verdict, and every operator transition. There is no public delete or
    truncate API by design (ADR-0003 invariant).

    Storage is pluggable via the `LedgerStore` Protocol (see ledger_store.py).
    The default backend is in-memory; deployers can inject SqliteLedgerStore,
    JsonlLedgerStore, or a custom backend (Postgres+WAL, S3+Object Lock,
    DynamoDB) per ADR-0012.
    """

    store: LedgerStore | None = None
    timestamp_source: TimestampSource | None = None

    def __post_init__(self) -> None:
        # Local imports to avoid circular imports at module load.
        from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore
        from cre_agent_audit.governance.timestamp_source import LocalClockTimestampSource

        if self.store is None:
            self.store = InMemoryLedgerStore()
        if self.timestamp_source is None:
            self.timestamp_source = LocalClockTimestampSource()

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        """Return an immutable view of the entries."""
        assert self.store is not None  # set in __post_init__
        return tuple(self.store)

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
        assert self.store is not None  # set in __post_init__
        assert self.timestamp_source is not None  # set in __post_init__
        sequence = len(self.store)
        prior_hash = self.chain_head()

        # Defensive copy so the ledger entry cannot be mutated via caller-held dicts.
        gate_verdicts_copy = dict(gate_verdicts)

        # The TSA attests to the payload BEFORE the timestamp is bound. The
        # token + timestamp are then folded into the canonical self_hash so
        # the chain binds both.
        if now is not None:
            timestamp = now
            timestamp_token: str | None = None
        else:
            payload_digest = hashlib.sha256(
                json.dumps(
                    {
                        "sequence": sequence,
                        "actor_kind": actor_kind.value,
                        "actor_id": actor_id,
                        "decision_type": decision_type,
                        "action_payload_hex": action_payload.hex(),
                        "gate_verdicts": dict(sorted(gate_verdicts_copy.items())),
                        "prior_hash": prior_hash,
                        "corrects_sequence": corrects_sequence,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).digest()
            attested = self.timestamp_source.stamp(payload_digest)
            timestamp = attested.asserted_at
            timestamp_token = attested.tsr_token_b64

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
            timestamp_token_b64=timestamp_token,
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
            timestamp_token_b64=timestamp_token,
        )
        self.store.append(entry)
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
        assert self.store is not None  # set in __post_init__
        if corrects_sequence < 0 or corrects_sequence >= len(self.store):
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
        """Return ``self_hash`` of the last entry (the chain head digest).

        Publish this value periodically to an external witness register
        (OpenTimestamps, Sigstore Rekor, regulator log) to convert the
        internally-consistent chain into an adversarially tamper-evident
        record. The genesis sentinel (SHA-256 zeroes) is returned for an
        empty ledger.
        """
        assert self.store is not None  # set in __post_init__
        return self.store.head_self_hash()

    def verify_chain(self) -> None:
        """Raise ``AuditChainTamperError`` if any entry is inconsistent.

        Two failure modes are detected:
        - ``self_hash mismatch`` — the entry's stored ``self_hash`` does not match
          a freshly-computed hash of its canonical bytes (something inside the
          entry was changed after writing).
        - ``prior_hash mismatch`` — the entry's ``prior_hash`` does not match the
          previous entry's ``self_hash`` (chain link broken).
        """
        assert self.store is not None  # set in __post_init__
        previous_self_hash = GENESIS_PRIOR_HASH
        for index, entry in enumerate(self.store):
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
                timestamp_token_b64=entry.timestamp_token_b64,
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
        # Test-only seam. Requires the underlying store to expose mutation;
        # only InMemoryLedgerStore does. Production stores (SQLite, JSONL)
        # have no UPDATE path by Protocol design.
        from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore

        if not isinstance(self.store, InMemoryLedgerStore):
            raise TypeError("_replace_entry_for_tests only supported on InMemoryLedgerStore")
        self.store._entries[index] = replacement
