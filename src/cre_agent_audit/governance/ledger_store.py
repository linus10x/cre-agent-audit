"""Pluggable persistence layer for the audit ledger — ADR-0012.

The original `AuditLedger` stored entries in a single in-memory list. v0.2.1
factors storage behind a Protocol so deployers can plug in SQLite (this repo),
JSONL (this repo), or downstream backends (Postgres+WAL, S3+Object Lock,
DynamoDB conditional writes) without touching `AuditLedger` or hash semantics.

This module ships the Protocol + the in-memory reference implementation.
Backends live in `ledger_store_sqlite.py` and `ledger_store_jsonl.py`.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    AuditEntry,
)


class LedgerStore(Protocol):
    """Storage Protocol for `AuditLedger`. Append-only; never mutates."""

    def append(self, entry: AuditEntry) -> None: ...
    def __iter__(self) -> Iterator[AuditEntry]: ...
    def __len__(self) -> int: ...
    def get(self, sequence: int) -> AuditEntry: ...
    def head_sequence(self) -> int: ...
    def head_self_hash(self) -> str: ...


class InMemoryLedgerStore:
    """Reference in-memory store — preserves v0.2.0 behavior."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def __iter__(self) -> Iterator[AuditEntry]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, sequence: int) -> AuditEntry:
        if sequence < 0 or sequence >= len(self._entries):
            raise IndexError(f"sequence {sequence} out of range [0, {len(self._entries)})")
        return self._entries[sequence]

    def head_sequence(self) -> int:
        return len(self._entries) - 1

    def head_self_hash(self) -> str:
        if not self._entries:
            return GENESIS_PRIOR_HASH
        return self._entries[-1].self_hash
