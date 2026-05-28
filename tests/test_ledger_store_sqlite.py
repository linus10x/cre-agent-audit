"""Tests for the SQLite-backed LedgerStore."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)
from cre_agent_audit.governance.ledger_store_sqlite import SqliteLedgerStore


def _entry(seq: int, prior: str = GENESIS_PRIOR_HASH) -> AuditEntry:
    return AuditEntry(
        sequence=seq,
        timestamp=datetime(2026, 5, 28, 12, 34, 56, tzinfo=timezone.utc),
        actor_kind=ActorKind.AGENT,
        actor_id="agent:test",
        decision_type="screening_decision",
        action_payload=b"\x01\x02\x03",
        gate_verdicts={"fair_housing": "PASS", "defcon": "PASS"},
        prior_hash=prior,
        self_hash="abc" * 21 + "d",  # 64 chars
    )


def test_empty_db_returns_genesis(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    assert store.head_self_hash() == GENESIS_PRIOR_HASH
    assert store.head_sequence() == -1
    assert len(store) == 0


def test_append_round_trip(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    e = _entry(0)
    store.append(e)
    assert len(store) == 1
    assert store.get(0) == e
    assert store.head_self_hash() == e.self_hash


def test_persists_across_reopen(tmp_path: Path) -> None:
    db = tmp_path / "ledger.db"
    store_a = SqliteLedgerStore(db)
    store_a.append(_entry(0))
    store_a.append(_entry(1, prior="abc" * 21 + "d"))
    del store_a

    store_b = SqliteLedgerStore(db)
    assert len(store_b) == 2
    assert [e.sequence for e in store_b] == [0, 1]


def test_iter_preserves_order_with_many_entries(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    for i in range(50):
        store.append(_entry(i))
    seqs = [e.sequence for e in store]
    assert seqs == list(range(50))


def test_no_update_path(tmp_path: Path) -> None:
    """The Protocol does not expose UPDATE; verify there is no method to mutate."""
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    for forbidden in ("update", "delete", "truncate", "set"):
        assert not hasattr(store, forbidden), f"SqliteLedgerStore must not expose {forbidden}"


def test_get_out_of_range_raises(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    store.append(_entry(0))
    with pytest.raises(IndexError):
        store.get(99)


def test_custom_table_name(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db", table="custom_audit")
    store.append(_entry(0))
    assert len(store) == 1


def test_invalid_table_name_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        SqliteLedgerStore(tmp_path / "ledger.db", table="bad; DROP TABLE")
