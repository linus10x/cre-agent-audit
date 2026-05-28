"""Tests for hash-chain audit ledger — ADR-0003."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest

from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditChainTamperError,
    AuditEntry,
    AuditLedger,
)

GENESIS_HASH = "0" * 64  # the documented "no prior entry" sentinel


def _now() -> datetime:
    return datetime(2026, 5, 22, 12, 0, 0, tzinfo=timezone.utc)


class TestLedgerAppend:
    def test_first_entry_uses_genesis_prior_hash(self) -> None:
        ledger = AuditLedger()
        entry = ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="strategy_agent_v1",
            decision_type="screening",
            action_payload=b'{"applicant_id": "anon-123"}',
            gate_verdicts={"defcon": "NORMAL", "fha_preflight": "PASS"},
            now=_now(),
        )
        assert entry.sequence == 0
        assert entry.prior_hash == GENESIS_HASH

    def test_subsequent_entries_chain_to_prior_self_hash(self) -> None:
        ledger = AuditLedger()
        e1 = ledger.append(
            actor_kind=ActorKind.SYSTEM,
            actor_id="defcon",
            decision_type="transition",
            action_payload=b"NORMAL->HEIGHTENED",
            gate_verdicts={},
        )
        e2 = ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="strategy_agent_v1",
            decision_type="screening",
            action_payload=b'{"applicant_id": "anon-124"}',
            gate_verdicts={"defcon": "HEIGHTENED"},
        )
        assert e2.prior_hash == e1.self_hash
        assert e2.sequence == e1.sequence + 1

    def test_sequence_is_monotonic(self) -> None:
        ledger = AuditLedger()
        for _ in range(5):
            ledger.append(
                actor_kind=ActorKind.AGENT,
                actor_id="a",
                decision_type="d",
                action_payload=b"p",
                gate_verdicts={},
            )
        sequences = [entry.sequence for entry in ledger.entries]
        assert sequences == list(range(5))


class TestSelfHashDoesNotIncludeSelfHashField:
    def test_self_hash_computed_over_everything_except_self_hash(self) -> None:
        ledger = AuditLedger()
        entry = ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="strategy_agent_v1",
            decision_type="screening",
            action_payload=b"payload",
            gate_verdicts={"defcon": "NORMAL"},
            now=_now(),
        )
        expected = hashlib.sha256(
            entry.canonical_bytes_for_hashing(),
        ).hexdigest()
        assert entry.self_hash == expected

    def test_two_identical_payload_entries_have_different_self_hashes_due_to_sequence(
        self,
    ) -> None:
        ledger = AuditLedger()
        now = _now()
        e1 = ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="a",
            decision_type="d",
            action_payload=b"p",
            gate_verdicts={},
            now=now,
        )
        e2 = ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="a",
            decision_type="d",
            action_payload=b"p",
            gate_verdicts={},
            now=now,
        )
        assert e1.self_hash != e2.self_hash


class TestTamperDetection:
    def test_verify_chain_passes_on_intact_chain(self) -> None:
        ledger = AuditLedger()
        for i in range(3):
            ledger.append(
                actor_kind=ActorKind.AGENT,
                actor_id=f"agent_{i}",
                decision_type="screening",
                action_payload=f"payload_{i}".encode(),
                gate_verdicts={"defcon": "NORMAL"},
            )
        # Should not raise.
        ledger.verify_chain()

    def test_verify_chain_detects_payload_tamper(self) -> None:
        ledger = AuditLedger()
        for i in range(3):
            ledger.append(
                actor_kind=ActorKind.AGENT,
                actor_id=f"agent_{i}",
                decision_type="screening",
                action_payload=f"payload_{i}".encode(),
                gate_verdicts={"defcon": "NORMAL"},
            )
        # Tamper with the middle entry's payload via direct slot mutation.
        # AuditEntry is frozen — go through __dict__ to simulate disk corruption.
        tampered = AuditEntry(
            sequence=ledger.entries[1].sequence,
            timestamp=ledger.entries[1].timestamp,
            actor_kind=ledger.entries[1].actor_kind,
            actor_id=ledger.entries[1].actor_id,
            decision_type=ledger.entries[1].decision_type,
            action_payload=b"tampered_payload",
            gate_verdicts=ledger.entries[1].gate_verdicts,
            prior_hash=ledger.entries[1].prior_hash,
            self_hash=ledger.entries[1].self_hash,  # stale hash — does not match new payload
        )
        ledger._replace_entry_for_tests(1, tampered)
        with pytest.raises(AuditChainTamperError, match="self_hash mismatch"):
            ledger.verify_chain()

    def test_verify_chain_detects_broken_prior_link(self) -> None:
        ledger = AuditLedger()
        for i in range(3):
            ledger.append(
                actor_kind=ActorKind.AGENT,
                actor_id=f"agent_{i}",
                decision_type="screening",
                action_payload=f"payload_{i}".encode(),
                gate_verdicts={},
            )
        # Replace entry[1] with one whose prior_hash does not match entry[0].self_hash.
        broken = AuditEntry(
            sequence=ledger.entries[1].sequence,
            timestamp=ledger.entries[1].timestamp,
            actor_kind=ledger.entries[1].actor_kind,
            actor_id=ledger.entries[1].actor_id,
            decision_type=ledger.entries[1].decision_type,
            action_payload=ledger.entries[1].action_payload,
            gate_verdicts=ledger.entries[1].gate_verdicts,
            prior_hash="f" * 64,  # not the previous entry's self_hash
            self_hash=ledger.entries[1].self_hash,
        )
        ledger._replace_entry_for_tests(1, broken)
        with pytest.raises(AuditChainTamperError):
            ledger.verify_chain()


class TestCorrectionEntries:
    def test_correction_references_prior_sequence(self) -> None:
        ledger = AuditLedger()
        original = ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="agent_a",
            decision_type="screening",
            action_payload=b"original",
            gate_verdicts={},
        )
        correction = ledger.append_correction(
            corrects_sequence=original.sequence,
            actor_kind=ActorKind.HUMAN,
            actor_id="ops:kunjar",
            action_payload=b"corrected",
            gate_verdicts={},
            reason="manual review override",
        )
        assert correction.decision_type == "correction"
        assert correction.corrects_sequence == original.sequence
        assert correction.sequence == original.sequence + 1
        # Original entry still present and intact.
        assert ledger.entries[0] == original


class TestLedgerInvariants:
    def test_ledger_does_not_support_delete(self) -> None:
        ledger = AuditLedger()
        ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="a",
            decision_type="d",
            action_payload=b"p",
            gate_verdicts={},
        )
        # AuditLedger intentionally exposes no delete API. Confirmed via attribute check.
        for forbidden in ("delete", "remove", "pop", "clear", "truncate"):
            assert not hasattr(ledger, forbidden), (
                f"AuditLedger MUST NOT expose a {forbidden!r} method"
            )

    def test_entries_property_returns_immutable_view(self) -> None:
        ledger = AuditLedger()
        ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="a",
            decision_type="d",
            action_payload=b"p",
            gate_verdicts={},
        )
        view = ledger.entries
        # Mutating the view must not mutate the ledger.
        if isinstance(view, list):
            view.pop()
            assert len(ledger.entries) == 1
        else:
            # Tuples and frozen sequences raise on mutation attempts.
            with pytest.raises((AttributeError, TypeError)):
                view.pop()  # type: ignore[attr-defined]


class TestAnchorCheckpoint:
    def test_chain_head_returns_self_hash_of_last_entry(self) -> None:
        ledger = AuditLedger()
        e1 = ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="a",
            decision_type="d",
            action_payload=b"p1",
            gate_verdicts={},
        )
        assert ledger.chain_head() == e1.self_hash
        e2 = ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id="a",
            decision_type="d",
            action_payload=b"p2",
            gate_verdicts={},
        )
        assert ledger.chain_head() == e2.self_hash

    def test_chain_head_returns_genesis_when_empty(self) -> None:
        ledger = AuditLedger()
        assert ledger.chain_head() == GENESIS_HASH


# ---------------------------------------------------------------------------
# Pluggable LedgerStore (Task B4)
# ---------------------------------------------------------------------------


class TestPluggableLedgerStore:
    """v0.2.1 — verifies AuditLedger accepts an injected LedgerStore."""

    def test_default_store_is_in_memory(self) -> None:
        from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore

        ledger = AuditLedger()
        assert isinstance(ledger.store, InMemoryLedgerStore)

    def test_accepts_injected_in_memory_store(self) -> None:
        from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore

        store = InMemoryLedgerStore()
        ledger = AuditLedger(store=store)
        entry = ledger.append(
            actor_kind=ActorKind.SYSTEM,
            actor_id="test",
            decision_type="t",
            action_payload=b"",
            gate_verdicts={},
        )
        assert len(store) == 1
        assert store.get(0) == entry

    def test_accepts_injected_sqlite_store(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from cre_agent_audit.governance.ledger_store_sqlite import SqliteLedgerStore

        store = SqliteLedgerStore(tmp_path / "ledger.db")
        ledger = AuditLedger(store=store)
        ledger.append(
            actor_kind=ActorKind.SYSTEM,
            actor_id="test",
            decision_type="t",
            action_payload=b"",
            gate_verdicts={},
        )
        # Survives verify_chain over the injected store.
        ledger.verify_chain()
        assert len(store) == 1
