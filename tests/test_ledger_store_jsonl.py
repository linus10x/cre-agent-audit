"""Tests for the JSONL-backed LedgerStore."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)
from cre_agent_audit.governance.ledger_store_jsonl import JsonlLedgerStore


def _entry(seq: int) -> AuditEntry:
    return AuditEntry(
        sequence=seq,
        timestamp=datetime(2026, 5, 28, tzinfo=timezone.utc),
        actor_kind=ActorKind.HUMAN,
        actor_id="user:gc",
        decision_type="bypass",
        action_payload=b"payload",
        gate_verdicts={"sovereign_veto": "BYPASSED"},
        prior_hash=GENESIS_PRIOR_HASH,
        self_hash="b" * 64,
    )


def test_empty_file_genesis(tmp_path: Path) -> None:
    store = JsonlLedgerStore(tmp_path / "ledger.jsonl")
    assert store.head_self_hash() == GENESIS_PRIOR_HASH
    assert len(store) == 0


def test_append_and_persist(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    store = JsonlLedgerStore(p)
    e = _entry(0)
    store.append(e)
    assert p.exists()
    assert len(store) == 1
    assert store.get(0) == e


def test_reopen_reads_existing(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    a = JsonlLedgerStore(p)
    a.append(_entry(0))
    a.append(_entry(1))
    del a
    b = JsonlLedgerStore(p)
    assert len(b) == 2


def test_corrupted_line_raises(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    p.write_text('{"sequence": "this-is-not-an-int"}\n')
    with pytest.raises((ValueError, KeyError)):
        list(JsonlLedgerStore(p))


def test_fsync_can_be_disabled(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    store = JsonlLedgerStore(p, fsync=False)
    store.append(_entry(0))
    assert len(store) == 1


def test_get_not_found_raises(tmp_path: Path) -> None:
    store = JsonlLedgerStore(tmp_path / "ledger.jsonl")
    store.append(_entry(0))
    with pytest.raises(IndexError):
        store.get(99)
