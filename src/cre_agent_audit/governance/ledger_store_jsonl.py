"""Append-only JSONL LedgerStore — ADR-0012 § Persistence backends.

One JSON object per line. Survives crash mid-write only if `fsync=True`
(the default). For higher durability, deployers should use an
external append-only object store (S3 + Object Lock) and write a
custom backend implementing `LedgerStore` against the same Protocol.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)


class JsonlLedgerStore:
    """JSONL file-backed `LedgerStore`.

    **Concurrency posture (ADR-0012).** This backend is safe for
    single-writer workloads. Concurrent ``append`` from multiple threads or
    processes is NOT supported; the deployer must serialize writes (one
    writer thread, an application-level lock, or an S3+Object-Lock backend
    instead). The class also requires ``path.parent`` to exist — the
    constructor fails fast otherwise so the first ``append`` does not
    surface a deferred ``FileNotFoundError``.
    """

    def __init__(self, path: Path | str, *, fsync: bool = True) -> None:
        self._path = Path(path)
        self._fsync = fsync
        if not self._path.parent.exists():
            raise FileNotFoundError(f"parent directory {self._path.parent!s} does not exist")
        self._path.touch(exist_ok=True)

    def append(self, entry: AuditEntry) -> None:
        payload: dict[str, object] = {
            "sequence": entry.sequence,
            "timestamp": entry.timestamp.isoformat(),
            "actor_kind": entry.actor_kind.value,
            "actor_id": entry.actor_id,
            "decision_type": entry.decision_type,
            "action_payload_hex": entry.action_payload.hex(),
            "gate_verdicts": dict(sorted(entry.gate_verdicts.items())),
            "prior_hash": entry.prior_hash,
            "self_hash": entry.self_hash,
            "corrects_sequence": entry.corrects_sequence,
            "timestamp_token_b64": entry.timestamp_token_b64,
        }
        line = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            if self._fsync:
                os.fsync(f.fileno())

    def __iter__(self) -> Iterator[AuditEntry]:
        with open(self._path, encoding="utf-8") as f:
            for raw in f:
                stripped = raw.strip()
                if not stripped:
                    continue
                yield self._decode(stripped)

    def __len__(self) -> int:
        with open(self._path, encoding="utf-8") as f:
            return sum(1 for ln in f if ln.strip())

    def get(self, sequence: int) -> AuditEntry:
        for entry in self:
            if entry.sequence == sequence:
                return entry
        raise IndexError(f"sequence {sequence} not found")

    def head_sequence(self) -> int:
        last = -1
        for entry in self:
            if entry.sequence > last:
                last = entry.sequence
        return last

    def head_self_hash(self) -> str:
        head = GENESIS_PRIOR_HASH
        max_seq = -1
        for entry in self:
            if entry.sequence > max_seq:
                max_seq = entry.sequence
                head = entry.self_hash
        return head

    @staticmethod
    def _decode(line: str) -> AuditEntry:
        d = json.loads(line)
        return AuditEntry(
            sequence=int(d["sequence"]),
            timestamp=datetime.fromisoformat(d["timestamp"]),
            actor_kind=ActorKind(d["actor_kind"]),
            actor_id=d["actor_id"],
            decision_type=d["decision_type"],
            action_payload=bytes.fromhex(d["action_payload_hex"]),
            gate_verdicts=d["gate_verdicts"],
            prior_hash=d["prior_hash"],
            self_hash=d["self_hash"],
            corrects_sequence=d.get("corrects_sequence"),
            timestamp_token_b64=d.get("timestamp_token_b64"),
        )
