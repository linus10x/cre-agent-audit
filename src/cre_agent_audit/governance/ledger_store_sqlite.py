"""SQLite-backed LedgerStore — ADR-0012 § Persistence backends.

Uses stdlib `sqlite3`. Single-table schema; no UPDATE / DELETE codepath
(append-only is enforced by absence of methods, not by triggers — the
LedgerStore Protocol intentionally exposes no mutation surface).

For production deployments needing Postgres+WAL, S3+Object Lock, or
DynamoDB conditional writes: write a sibling backend in your codebase
implementing the `LedgerStore` Protocol. ADR-0012 documents the
integration shape; the repo does not pull driver libraries.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)

# Strict identifier — ASCII letters/digits/underscore only, must start with a
# letter or underscore. Tighter than ``str.isalnum`` (which admits Unicode
# letters) so a SQL identifier cannot smuggle non-ASCII codepoints.
_SAFE_TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SqliteLedgerStore:
    """sqlite3-backed `LedgerStore`. One row per `AuditEntry`.

    **Concurrency posture (ADR-0012).** This backend is safe for single-writer
    workloads. Concurrent ``append`` from multiple threads or processes is
    NOT supported; the deployer must serialize writes (one writer thread, an
    application-level lock, or a write-ahead Postgres backend instead).
    """

    def __init__(self, db_path: Path | str, *, table: str = "audit_chain") -> None:
        if not _SAFE_TABLE_NAME.match(table):
            raise ValueError(f"table name {table!r} must match [A-Za-z_][A-Za-z0-9_]*")
        self._table = table
        self._conn = sqlite3.connect(str(db_path), isolation_level=None)
        self._conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                sequence INTEGER PRIMARY KEY,
                timestamp_iso TEXT NOT NULL,
                actor_kind TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                action_payload BLOB NOT NULL,
                gate_verdicts_json TEXT NOT NULL,
                prior_hash TEXT NOT NULL,
                self_hash TEXT NOT NULL,
                corrects_sequence INTEGER,
                timestamp_token_b64 TEXT
            )
            """
        )

    def append(self, entry: AuditEntry) -> None:
        self._conn.execute(
            f"INSERT INTO {self._table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.sequence,
                entry.timestamp.isoformat(),
                entry.actor_kind.value,
                entry.actor_id,
                entry.decision_type,
                entry.action_payload,
                json.dumps(dict(sorted(entry.gate_verdicts.items())), sort_keys=True),
                entry.prior_hash,
                entry.self_hash,
                entry.corrects_sequence,
                entry.timestamp_token_b64,
            ),
        )

    def __iter__(self) -> Iterator[AuditEntry]:
        rows = self._conn.execute(
            f"SELECT sequence, timestamp_iso, actor_kind, actor_id, decision_type, "
            f"action_payload, gate_verdicts_json, prior_hash, self_hash, corrects_sequence, "
            f"timestamp_token_b64 "
            f"FROM {self._table} ORDER BY sequence ASC"
        )
        for row in rows:
            yield self._row_to_entry(row)

    def __len__(self) -> int:
        cur = self._conn.execute(f"SELECT COUNT(*) FROM {self._table}")
        result: int = cur.fetchone()[0]
        return result

    def get(self, sequence: int) -> AuditEntry:
        cur = self._conn.execute(
            f"SELECT sequence, timestamp_iso, actor_kind, actor_id, decision_type, "
            f"action_payload, gate_verdicts_json, prior_hash, self_hash, corrects_sequence, "
            f"timestamp_token_b64 "
            f"FROM {self._table} WHERE sequence = ?",
            (sequence,),
        )
        row = cur.fetchone()
        if row is None:
            raise IndexError(f"sequence {sequence} not found")
        return self._row_to_entry(row)

    def head_sequence(self) -> int:
        cur = self._conn.execute(f"SELECT MAX(sequence) FROM {self._table}")
        result = cur.fetchone()[0]
        return -1 if result is None else int(result)

    def head_self_hash(self) -> str:
        cur = self._conn.execute(
            f"SELECT self_hash FROM {self._table} ORDER BY sequence DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row is None:
            return GENESIS_PRIOR_HASH
        return str(row[0])

    @staticmethod
    def _row_to_entry(row: tuple[object, ...]) -> AuditEntry:
        sequence_raw = row[0]
        action_payload_raw = row[5]
        corrects_raw = row[9]
        token_raw = row[10] if len(row) > 10 else None
        assert isinstance(sequence_raw, int)
        assert isinstance(action_payload_raw, (bytes, bytearray))
        assert corrects_raw is None or isinstance(corrects_raw, int)
        assert token_raw is None or isinstance(token_raw, str)
        return AuditEntry(
            sequence=sequence_raw,
            timestamp=datetime.fromisoformat(str(row[1])),
            actor_kind=ActorKind(str(row[2])),
            actor_id=str(row[3]),
            decision_type=str(row[4]),
            action_payload=bytes(action_payload_raw),
            gate_verdicts=json.loads(str(row[6])),
            prior_hash=str(row[7]),
            self_hash=str(row[8]),
            corrects_sequence=corrects_raw,
            timestamp_token_b64=token_raw,
        )
