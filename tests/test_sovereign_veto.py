"""Tests for Sovereign Veto — ADR-0002."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger
from cre_agent_audit.governance.sovereign_veto import (
    AgentAction,
    ConstraintCheck,
    SovereignBypass,
    SovereignVeto,
    VetoResult,
    VetoVerdict,
)


@dataclass(frozen=True)
class _SimpleAction(AgentAction):
    """Minimal AgentAction used to drive the veto in tests."""

    action_class: str
    payload: dict[str, object]


class _AlwaysPassCheck(ConstraintCheck):
    def evaluate(self, action: AgentAction) -> VetoResult:
        return VetoResult.passing()


class _AlwaysVetoCheck(ConstraintCheck):
    REASON_CODE = "TEST-VETO"

    def evaluate(self, action: AgentAction) -> VetoResult:
        return VetoResult.veto(
            reason_code=self.REASON_CODE,
            owner_required="ops:on_call_compliance",
            detail="test-only veto for unit tests",
        )


class TestPassThrough:
    def test_clean_action_passes(self) -> None:
        veto = SovereignVeto()
        veto.register("tenant_screening", _AlwaysPassCheck())
        result = veto.check(_SimpleAction(action_class="tenant_screening", payload={}))
        assert result.verdict is VetoVerdict.PASS

    def test_pass_carries_no_reason_code(self) -> None:
        result = VetoResult.passing()
        assert result.verdict is VetoVerdict.PASS
        assert result.reason_code is None
        assert result.owner_required is None


class TestVetoVerdict:
    def test_veto_action_blocked_with_reason(self) -> None:
        veto = SovereignVeto()
        veto.register("tenant_screening", _AlwaysVetoCheck())
        result = veto.check(_SimpleAction(action_class="tenant_screening", payload={}))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "TEST-VETO"
        assert result.owner_required == "ops:on_call_compliance"

    def test_unknown_action_class_is_vetoed_conservatively(self) -> None:
        veto = SovereignVeto()
        result = veto.check(_SimpleAction(action_class="never_registered", payload={}))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "UNKNOWN-ACTION-CLASS"


class TestAuditIntegration:
    def test_veto_records_decision_on_audit_ledger(self) -> None:
        ledger = AuditLedger()
        veto = SovereignVeto(ledger=ledger)
        veto.register("tenant_screening", _AlwaysVetoCheck())
        veto.check(_SimpleAction(action_class="tenant_screening", payload={"applicant": "anon"}))
        # Exactly one audit entry — the veto.
        assert len(ledger.entries) == 1
        entry = ledger.entries[0]
        assert entry.decision_type == "sovereign_veto"
        assert entry.gate_verdicts["verdict"] == "VETO"
        assert entry.gate_verdicts["reason_code"] == "TEST-VETO"

    def test_pass_also_records_to_ledger(self) -> None:
        ledger = AuditLedger()
        veto = SovereignVeto(ledger=ledger)
        veto.register("tenant_screening", _AlwaysPassCheck())
        veto.check(_SimpleAction(action_class="tenant_screening", payload={}))
        assert len(ledger.entries) == 1
        assert ledger.entries[0].gate_verdicts["verdict"] == "PASS"


class TestBypass:
    def test_bypass_requires_named_owner(self) -> None:
        with pytest.raises(ValueError, match="owner"):
            SovereignBypass(
                veto_reason_code="FHA-VOUCHER",
                owner="",
                regulatory_basis="State SOI ordinance carve-out",
                justification="Voucher status not used as a decision input here.",
            )

    def test_bypass_requires_regulatory_basis(self) -> None:
        with pytest.raises(ValueError, match="regulatory_basis"):
            SovereignBypass(
                veto_reason_code="FHA-VOUCHER",
                owner="compliance:director",
                regulatory_basis="",
                justification="Voucher status not used as a decision input here.",
            )

    def test_bypass_logged_to_audit_ledger(self) -> None:
        ledger = AuditLedger()
        veto = SovereignVeto(ledger=ledger)
        veto.register("tenant_screening", _AlwaysVetoCheck())
        # Original veto entry.
        veto.check(_SimpleAction(action_class="tenant_screening", payload={}))
        # Human-owner bypass entry.
        bypass = SovereignBypass(
            veto_reason_code="TEST-VETO",
            owner="compliance:director",
            regulatory_basis="Internal escalation policy v3.2 §4.1",
            justification="Reviewer confirmed input feature is not protected-class proxy.",
        )
        veto.record_bypass(bypass)
        assert len(ledger.entries) == 2
        bypass_entry = ledger.entries[1]
        assert bypass_entry.decision_type == "sovereign_bypass"
        assert bypass_entry.actor_kind is ActorKind.HUMAN
        assert bypass_entry.actor_id == "compliance:director"
        assert bypass_entry.gate_verdicts["veto_reason_code"] == "TEST-VETO"

    def test_bypass_cannot_remove_original_veto(self) -> None:
        ledger = AuditLedger()
        veto = SovereignVeto(ledger=ledger)
        veto.register("tenant_screening", _AlwaysVetoCheck())
        veto.check(_SimpleAction(action_class="tenant_screening", payload={}))
        veto.record_bypass(
            SovereignBypass(
                veto_reason_code="TEST-VETO",
                owner="compliance:director",
                regulatory_basis="basis",
                justification="just",
            )
        )
        # Original veto entry preserved verbatim.
        assert ledger.entries[0].gate_verdicts["verdict"] == "VETO"


class TestRegistrationAndDispatch:
    def test_register_returns_self_for_chaining(self) -> None:
        veto = SovereignVeto()
        result = veto.register("tenant_screening", _AlwaysPassCheck())
        assert result is veto

    def test_check_dispatches_to_registered_constraint_surface(self) -> None:
        veto = SovereignVeto()
        veto.register("tenant_screening", _AlwaysVetoCheck())
        veto.register("lease_abstraction", _AlwaysPassCheck())
        screening_result = veto.check(_SimpleAction(action_class="tenant_screening", payload={}))
        abstraction_result = veto.check(_SimpleAction(action_class="lease_abstraction", payload={}))
        assert screening_result.verdict is VetoVerdict.VETO
        assert abstraction_result.verdict is VetoVerdict.PASS

    def test_register_must_provide_non_empty_action_class(self) -> None:
        veto = SovereignVeto()
        with pytest.raises(ValueError, match="action_class"):
            veto.register("", _AlwaysPassCheck())
