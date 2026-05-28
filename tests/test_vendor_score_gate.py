"""Tests for VendorScoreGate (third-party AI scoring with audit-chain emit).

Implements the test surface named in ADR-0011 update / v0.2.1 § deferred-3:
round-trip emit + read-back, score-drift detection on same (input_hash,
model_version), model-version change recorded not absorbed, chain-verify
parity for vendor entries.

Score drift is the load-bearing assertion. A vendor silently shipping a
patched model is the exact failure FAILURE-MODES.md § Row 8 names.
"""

from __future__ import annotations

import hashlib

import pytest

from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger
from cre_agent_audit.governance.vendor_score_gate import (
    InMemoryVendorScoreGate,
    VendorScoreDriftDetected,
    VendorScoreEntry,
    VendorScoreGate,
)


def _input_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


# --------------------------------------------------------------------------- #
# 1. Protocol conformance                                                     #
# --------------------------------------------------------------------------- #


def test_in_memory_vendor_score_gate_is_a_vendor_score_gate() -> None:
    gate: VendorScoreGate = InMemoryVendorScoreGate(ledger=AuditLedger())
    assert hasattr(gate, "emit")
    assert hasattr(gate, "history_for")


# --------------------------------------------------------------------------- #
# 2. Round-trip emit + read-back                                              #
# --------------------------------------------------------------------------- #


def test_emit_records_vendor_score_to_audit_chain() -> None:
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger)
    entry = gate.emit(
        vendor_id="acme-screen",
        input_hash=_input_hash(b"applicant-1"),
        score=0.82,
        model_version="v3.1.0",
    )
    assert isinstance(entry, VendorScoreEntry)
    assert entry.vendor_id == "acme-screen"
    assert entry.score == pytest.approx(0.82)
    assert entry.model_version == "v3.1.0"
    # Chain has exactly one entry, decision_type names a vendor score.
    assert len(ledger.entries) == 1
    chain_entry = ledger.entries[0]
    assert chain_entry.decision_type == "vendor_score_emit"
    assert chain_entry.actor_kind == ActorKind.SYSTEM
    assert chain_entry.actor_id == "acme-screen"


def test_history_for_returns_entries_in_emit_order() -> None:
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger)
    input_hash = _input_hash(b"applicant-2")
    gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.50,
        model_version="v3.1.0",
    )
    gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.50,
        model_version="v3.2.0",
    )
    history = gate.history_for(vendor_id="acme-screen", input_hash=input_hash)
    assert [h.model_version for h in history] == ["v3.1.0", "v3.2.0"]


# --------------------------------------------------------------------------- #
# 3. Score-drift detection                                                    #
# --------------------------------------------------------------------------- #


def test_same_input_same_model_different_score_raises_drift() -> None:
    """The exact silent-vendor-patch failure: same input + same model_version,
    score moves. Must be detected, not absorbed.
    """
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger)
    input_hash = _input_hash(b"applicant-3")
    gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.50,
        model_version="v3.1.0",
    )
    with pytest.raises(VendorScoreDriftDetected) as excinfo:
        gate.emit(
            vendor_id="acme-screen",
            input_hash=input_hash,
            score=0.65,
            model_version="v3.1.0",
        )
    msg = str(excinfo.value)
    assert "acme-screen" in msg
    assert "v3.1.0" in msg


def test_drift_entry_recorded_to_chain_even_when_raising() -> None:
    """The drift detection itself is an auditable event; the flagged entry
    must hit the chain before the exception propagates.
    """
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger)
    input_hash = _input_hash(b"applicant-4")
    gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.50,
        model_version="v3.1.0",
    )
    with pytest.raises(VendorScoreDriftDetected):
        gate.emit(
            vendor_id="acme-screen",
            input_hash=input_hash,
            score=0.65,
            model_version="v3.1.0",
        )
    # Two chain entries: original emit + drift flag.
    assert len(ledger.entries) == 2
    drift_entry = ledger.entries[1]
    assert drift_entry.decision_type == "vendor_score_drift"
    assert drift_entry.actor_id == "acme-screen"
    assert drift_entry.gate_verdicts.get("vendor_score_drift") == "flagged"


def test_strict_drift_mode_can_be_disabled() -> None:
    """When raise_on_drift=False, drift is recorded but does not raise."""
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger, raise_on_drift=False)
    input_hash = _input_hash(b"applicant-5")
    gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.50,
        model_version="v3.1.0",
    )
    entry = gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.65,
        model_version="v3.1.0",
    )
    assert entry.drift_detected is True
    assert entry.previous_score == pytest.approx(0.50)
    # Chain still records both emits.
    assert len(ledger.entries) == 2


# --------------------------------------------------------------------------- #
# 4. Model-version change recorded, not absorbed                              #
# --------------------------------------------------------------------------- #


def test_same_input_different_model_version_is_not_drift() -> None:
    """A new model_version is a legitimate vendor change. The new score is
    recorded in the chain as its own entry; no drift exception.
    """
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger)
    input_hash = _input_hash(b"applicant-6")
    gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.50,
        model_version="v3.1.0",
    )
    second = gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.65,
        model_version="v3.2.0",
    )
    assert second.drift_detected is False
    assert len(ledger.entries) == 2
    assert ledger.entries[1].decision_type == "vendor_score_emit"


# --------------------------------------------------------------------------- #
# 5. Vendor entries pass standard verify_chain                                #
# --------------------------------------------------------------------------- #


def test_vendor_entries_pass_standard_verify_chain() -> None:
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger)
    for i in range(3):
        gate.emit(
            vendor_id="acme-screen",
            input_hash=_input_hash(f"applicant-{i}".encode()),
            score=0.5 + i * 0.1,
            model_version="v3.1.0",
        )
    ledger.verify_chain()  # must not raise


def test_vendor_drift_entries_pass_standard_verify_chain() -> None:
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger, raise_on_drift=False)
    input_hash = _input_hash(b"applicant-X")
    gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.50,
        model_version="v3.1.0",
    )
    gate.emit(
        vendor_id="acme-screen",
        input_hash=input_hash,
        score=0.99,
        model_version="v3.1.0",
    )
    assert len(ledger.entries) == 2
    ledger.verify_chain()  # must not raise


# --------------------------------------------------------------------------- #
# 6. Score range validation at gate level                                     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("bad_score", [-0.01, 1.01, float("nan"), float("inf")])
def test_emit_rejects_out_of_range_score(bad_score: float) -> None:
    gate = InMemoryVendorScoreGate(ledger=AuditLedger())
    with pytest.raises(ValueError):
        gate.emit(
            vendor_id="acme-screen",
            input_hash=_input_hash(b"applicant-x"),
            score=bad_score,
            model_version="v3.1.0",
        )


def test_emit_rejects_empty_input_hash() -> None:
    gate = InMemoryVendorScoreGate(ledger=AuditLedger())
    with pytest.raises(ValueError):
        gate.emit(
            vendor_id="acme-screen",
            input_hash="",
            score=0.5,
            model_version="v3.1.0",
        )
