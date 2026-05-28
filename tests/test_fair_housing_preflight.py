"""Tests for Fair-Housing Pre-Flight Gate — ADR-0008."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cre_agent_audit.governance.fair_housing_preflight import (
    BypassRegistry,
    DisparateImpactMonitor,
    FairHousingPreflightGate,
    ScreeningDecisionAction,
)
from cre_agent_audit.governance.sovereign_veto import VetoVerdict
from cre_agent_audit.schemas.screening_decision import (
    AuthorityLevel,
    Decision,
    FairHousingException,
    JurisdictionRules,
    ProtectedSurface,
    ScreeningDecision,
)


def _ts(offset_days: int = 0) -> datetime:
    return datetime(2026, 5, 22, 12, 0, 0, tzinfo=timezone.utc) + timedelta(days=offset_days)


def _decision(
    *,
    jurisdiction: str = "TX",
    features: dict[str, float | str | bool] | None = None,
    decision: Decision = Decision.APPROVE,
) -> ScreeningDecision:
    return ScreeningDecision(
        decision_id="dec-001",
        applicant_id_anon="anon-aaaa",
        surface=ProtectedSurface.TENANT_SCREENING,
        features=features or {"credit_score": 0.78, "rent_to_income": 0.32},
        score=0.72,
        decision=decision,
        jurisdiction=jurisdiction,
        model_version="claude-opus-4-7",
    )


def _action(decision: ScreeningDecision) -> ScreeningDecisionAction:
    return ScreeningDecisionAction(action_class="tenant_screening", decision=decision)


class TestCleanDecisionPasses:
    def test_clean_features_pass(self) -> None:
        gate = FairHousingPreflightGate()
        result = gate.evaluate(_action(_decision()))
        assert result.verdict is VetoVerdict.PASS


class TestProxyDetection:
    def test_zip_only_feature_triggers_proxy_veto(self) -> None:
        gate = FairHousingPreflightGate()
        decision = _decision(features={"applicant_zip_only": "75201"})
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-PROXY"

    def test_preferred_language_feature_triggers_proxy_veto(self) -> None:
        gate = FairHousingPreflightGate()
        decision = _decision(features={"preferred_language": "es"})
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-PROXY"


class TestVoucherProtection:
    def test_voucher_in_features_vetoes_saferent_failure_mode(self) -> None:
        gate = FairHousingPreflightGate()
        decision = _decision(features={"has_section_8_voucher": True})
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-VOUCHER"

    def test_voucher_score_feature_vetoes(self) -> None:
        gate = FairHousingPreflightGate()
        decision = _decision(features={"voucher_penalty_score": 0.42})
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-VOUCHER"


class TestSourceOfIncome:
    def test_income_source_in_soi_protected_jurisdiction_vetoes(self) -> None:
        gate = FairHousingPreflightGate()
        decision = _decision(
            jurisdiction="CA",
            features={"income_source_type": "social_security"},
        )
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-SOI"

    def test_income_source_in_non_protected_jurisdiction_passes(self) -> None:
        gate = FairHousingPreflightGate()
        decision = _decision(
            jurisdiction="TX",
            features={"income_source_type": "social_security"},
        )
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.PASS

    def test_jurisdiction_rules_override_default(self) -> None:
        # Operator explicitly opts a non-default jurisdiction in.
        custom_rules = {
            "FL": JurisdictionRules(jurisdiction="FL", soi_protected=True),
        }
        gate = FairHousingPreflightGate(jurisdiction_rules=custom_rules)
        decision = _decision(
            jurisdiction="FL",
            features={"income_source_type": "ssi"},
        )
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-SOI"


class TestCriminalHistory:
    def test_blanket_criminal_disqualification_vetoes(self) -> None:
        gate = FairHousingPreflightGate()
        decision = _decision(
            features={"criminal_history_blanket_deny": True},
            decision=Decision.DENY,
        )
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-CRIM"

    def test_old_conviction_beyond_lookback_vetoes(self) -> None:
        gate = FairHousingPreflightGate()
        # Default lookback per JurisdictionRules is 7 years; 10 years exceeds it.
        decision = _decision(
            features={"criminal_history_years_since": 10.0},
            decision=Decision.DENY,
        )
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-CRIM"


class TestDisparateImpactMonitor:
    def test_four_fifths_rule_breach_vetoes(self) -> None:
        monitor = DisparateImpactMonitor(window_days=90)
        # Cohort A: 100 decisions, 80 approvals → 0.80 selection rate.
        # Cohort B: 100 decisions, 50 approvals → 0.50 selection rate.
        # Ratio = 0.50 / 0.80 = 0.625 → BELOW four-fifths (0.80).
        for _ in range(80):
            monitor.record(cohort="A", approved=True, when=_ts(-30))
        for _ in range(20):
            monitor.record(cohort="A", approved=False, when=_ts(-30))
        for _ in range(50):
            monitor.record(cohort="B", approved=True, when=_ts(-30))
        for _ in range(50):
            monitor.record(cohort="B", approved=False, when=_ts(-30))
        ratio = monitor.lowest_cohort_ratio(now=_ts())
        assert ratio < 0.80
        gate = FairHousingPreflightGate(disparate_impact_monitor=monitor)
        result = gate.evaluate(_action(_decision()))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-DISPARATE"

    def test_clean_disparate_impact_passes(self) -> None:
        monitor = DisparateImpactMonitor(window_days=90)
        # Both cohorts at 0.80 selection rate.
        for _ in range(80):
            monitor.record(cohort="A", approved=True, when=_ts(-30))
        for _ in range(20):
            monitor.record(cohort="A", approved=False, when=_ts(-30))
        for _ in range(80):
            monitor.record(cohort="B", approved=True, when=_ts(-30))
        for _ in range(20):
            monitor.record(cohort="B", approved=False, when=_ts(-30))
        gate = FairHousingPreflightGate(disparate_impact_monitor=monitor)
        result = gate.evaluate(_action(_decision()))
        assert result.verdict is VetoVerdict.PASS

    def test_monitor_window_excludes_stale_decisions(self) -> None:
        monitor = DisparateImpactMonitor(window_days=90)
        # Stale skew (180 days ago) should NOT count.
        for _ in range(80):
            monitor.record(cohort="A", approved=True, when=_ts(-180))
        for _ in range(20):
            monitor.record(cohort="B", approved=True, when=_ts(-180))
        # Recent balanced sample.
        for _ in range(10):
            monitor.record(cohort="A", approved=True, when=_ts(-10))
        for _ in range(10):
            monitor.record(cohort="B", approved=True, when=_ts(-10))
        ratio = monitor.lowest_cohort_ratio(now=_ts())
        assert ratio == 1.0


class TestBypassRegistry:
    def _bypass(self, owner: str, reason: str, *, days_ago: int = 0) -> FairHousingException:
        return FairHousingException(
            exception_id=f"exc-{owner}-{reason}-{days_ago}",
            decision_id="dec-x",
            veto_reason_code=reason,
            bypass_owner=owner,
            bypass_justification="reviewer confirmed feature is not protected-class proxy",
            bypass_authority=AuthorityLevel.MANAGER,
            timestamp=_ts(-days_ago),
            audit_chain_sigil="f" * 64,
        )

    def test_three_bypasses_same_owner_in_90_days_escalates_to_gc(self) -> None:
        registry = BypassRegistry()
        for i in range(3):
            registry.record(self._bypass("ops:alice", "FHA-VOUCHER", days_ago=10 + i))
        assert registry.should_escalate_to_gc(owner="ops:alice", now=_ts()) is True

    def test_two_bypasses_same_owner_no_escalation(self) -> None:
        registry = BypassRegistry()
        registry.record(self._bypass("ops:alice", "FHA-VOUCHER", days_ago=5))
        registry.record(self._bypass("ops:alice", "FHA-PROXY", days_ago=10))
        assert registry.should_escalate_to_gc(owner="ops:alice", now=_ts()) is False

    def test_five_bypasses_same_reason_code_forces_defcon_4(self) -> None:
        registry = BypassRegistry()
        for i in range(5):
            registry.record(self._bypass(f"ops:reviewer{i}", "FHA-PROXY", days_ago=10 + i))
        assert registry.should_force_defcon_4(reason_code="FHA-PROXY", now=_ts()) is True

    def test_four_bypasses_same_reason_code_no_defcon_4(self) -> None:
        registry = BypassRegistry()
        for i in range(4):
            registry.record(self._bypass(f"ops:reviewer{i}", "FHA-PROXY", days_ago=10 + i))
        assert registry.should_force_defcon_4(reason_code="FHA-PROXY", now=_ts()) is False


class TestMIThresholdDetectorIntegration:
    """v0.2.2: Fair-Housing Pre-Flight Gate accepts an opt-in MIThresholdDetector
    that flags features carrying mutual-information signal about a protected
    class (the SafeRent failure mode)."""

    def test_gate_with_no_detector_preserves_v021_behavior(self) -> None:
        """``FairHousingPreflightGate()`` with no detector is the v0.2.1 default."""
        gate = FairHousingPreflightGate()
        result = gate.evaluate(_action(_decision()))
        assert result.verdict is VetoVerdict.PASS

    def test_gate_with_detector_flags_voucher_proxy(self) -> None:
        """When the detector is wired, applicant features above MI threshold veto."""
        from cre_agent_audit.governance.mi_threshold_detector import (
            MIThresholdDetector,
        )
        from tests.fixtures.saferent_shaped_reference import (
            saferent_shaped_reference,
        )

        ref = saferent_shaped_reference()
        detector = MIThresholdDetector(reference=ref, mi_threshold=0.10)
        gate = FairHousingPreflightGate(mi_proxy_detector=detector)
        decision = _decision(
            features={
                "zip_code_quintile": 5,
                "credit_score": 720,
                "income_x_rent": 3.5,
            }
        )
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "FHA-MI-PROXY"
        assert "zip_code_quintile" in (result.detail or "")

    def test_gate_with_detector_passes_clean_features(self) -> None:
        """Features below MI threshold do not produce FHA-MI-PROXY vetoes."""
        from cre_agent_audit.governance.mi_threshold_detector import (
            MIThresholdDetector,
        )
        from tests.fixtures.saferent_shaped_reference import (
            saferent_shaped_reference,
        )

        ref = saferent_shaped_reference()
        detector = MIThresholdDetector(reference=ref, mi_threshold=0.10)
        gate = FairHousingPreflightGate(mi_proxy_detector=detector)
        decision = _decision(
            features={
                "credit_score": 720,
                "income_x_rent": 3.5,
            }
        )
        result = gate.evaluate(_action(decision))
        assert result.verdict is VetoVerdict.PASS
