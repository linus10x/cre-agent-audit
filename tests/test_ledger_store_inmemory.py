"""Tests for the in-memory reference LedgerStore."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)
from cre_agent_audit.governance.ledger_store import (
    InMemoryLedgerStore,
    LedgerStore,
)


def _make_entry(seq: int, prior: str = GENESIS_PRIOR_HASH) -> AuditEntry:
    return AuditEntry(
        sequence=seq,
        timestamp=datetime(2026, 5, 28, tzinfo=timezone.utc),
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
        prior_hash=prior,
        self_hash="a" * 64,
    )


def test_empty_store_head_returns_genesis() -> None:
    store: LedgerStore = InMemoryLedgerStore()
    assert store.head_self_hash() == GENESIS_PRIOR_HASH
    assert store.head_sequence() == -1
    assert len(store) == 0


def test_append_then_get() -> None:
    store: LedgerStore = InMemoryLedgerStore()
    e0 = _make_entry(0)
    store.append(e0)
    assert len(store) == 1
    assert store.get(0) == e0
    assert store.head_sequence() == 0


def test_iter_returns_entries_in_order() -> None:
    store: LedgerStore = InMemoryLedgerStore()
    for i in range(3):
        store.append(_make_entry(i))
    assert [e.sequence for e in store] == [0, 1, 2]


def test_get_out_of_range_raises() -> None:
    store: LedgerStore = InMemoryLedgerStore()
    store.append(_make_entry(0))
    with pytest.raises(IndexError):
        store.get(5)


def test_protocol_conformance_via_method_set() -> None:
    store = InMemoryLedgerStore()
    for method in ("append", "__iter__", "__len__", "get", "head_sequence", "head_self_hash"):
        assert hasattr(store, method)
