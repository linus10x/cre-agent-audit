"""AL-PROBE re-authored as committed tests (S1 hardening, 2026-06-05).

cre-side probes. Mapping to the G-SIB-scale assurance catalog rows:

  * AL-PROBE-01  level-gate refuses promotion when lower gates are unmet, and
                 is honestly labelled advisory unless run with independent
                 attestation.
  * AL-PROBE-03  AuditLedger.verify_chain passes on an intact chain and detects
                 an in-place payload tamper.
  * AL-PROBE-04  DEFCON transition-direction guard: a one-call de-escalation
                 (SHUTDOWN -> NORMAL) is REFUSED; de-escalation requires the
                 Authorizer-gated manual_override (fail-closed). This is the cre
                 gap the catalog found (no direction guard), now fixed.
  * AL-PROBE-05  N/A — cre has NO effective-challenge primitive. Recorded as a
                 documented skip, NEVER fabricated as a pass.

AL-PROBE-02 (sovereign veto un-self-clearable with an authenticated operator)
is a finserv-side probe: cre's SovereignVeto is a constraint-check gate, not
the operator/clear kill-switch the catalog probed, so the catalog scoped
AL-PROBE-02 to finserv. See finserv-agent-audit/tests/adversarial/test_al_probes.py.
"""

from __future__ import annotations

import importlib
from datetime import timedelta

import pytest

from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditChainTamperError,
    AuditEntry,
    AuditLedger,
)
from cre_agent_audit.governance.autonomy_ladder import (
    PromotionGateNotMet,
    PromotionRequirements,
    check_a2_to_a3_promotion,
)
from cre_agent_audit.governance.defcon import (
    DefconController,
    DefconDeEscalationError,
    DefconOverrideRejectedError,
    DefconState,
)


class _AllowAll:
    def authorize(self, operator_id: str, action: str, context: dict) -> bool:  # type: ignore[type-arg]
        return True


class _RejectAll:
    def authorize(self, operator_id: str, action: str, context: dict) -> bool:  # type: ignore[type-arg]
        return False


# --------------------------------------------------------------------------- #
# AL-PROBE-01 — promotion-without-lower-gates is refused.
# --------------------------------------------------------------------------- #


def test_al_probe_01_promotion_refused_when_all_lower_gates_unmet() -> None:
    reqs = PromotionRequirements(
        sovereign_veto_load_tested=False,
        audit_ledger_running_for=timedelta(days=3),
        shadow_mode_running_for=timedelta(days=1),
        circuit_breaker_test_recent=False,
    )
    report = check_a2_to_a3_promotion(reqs)
    assert report.passed is False
    assert len(report.failures) == 4
    with pytest.raises(PromotionGateNotMet):
        report.raise_if_blocked()


def test_al_probe_01_passes_when_all_met_but_is_advisory() -> None:
    reqs = PromotionRequirements(
        sovereign_veto_load_tested=True,
        audit_ledger_running_for=timedelta(days=120),
        shadow_mode_running_for=timedelta(days=45),
        circuit_breaker_test_recent=True,
    )
    report = check_a2_to_a3_promotion(reqs)
    assert report.passed is True
    assert report.advisory is True


# --------------------------------------------------------------------------- #
# AL-PROBE-03 — ledger verify passes on intact chain; in-place tamper detected.
# --------------------------------------------------------------------------- #


def _seed_ledger(n: int = 3) -> AuditLedger:
    ledger = AuditLedger()
    for i in range(n):
        ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id=f"agent_{i}",
            decision_type="screening",
            action_payload=f"payload_{i}".encode(),
            gate_verdicts={"defcon": "NORMAL"},
        )
    return ledger


def test_al_probe_03_clean_chain_verifies() -> None:
    ledger = _seed_ledger()
    ledger.verify_chain()  # must NOT raise


def test_al_probe_03_inplace_tamper_detected() -> None:
    ledger = _seed_ledger()
    tampered = AuditEntry(
        sequence=ledger.entries[1].sequence,
        timestamp=ledger.entries[1].timestamp,
        actor_kind=ledger.entries[1].actor_kind,
        actor_id=ledger.entries[1].actor_id,
        decision_type=ledger.entries[1].decision_type,
        action_payload=b"TAMPERED",
        gate_verdicts=ledger.entries[1].gate_verdicts,
        prior_hash=ledger.entries[1].prior_hash,
        self_hash=ledger.entries[1].self_hash,  # stale hash
    )
    ledger._replace_entry_for_tests(1, tampered)
    with pytest.raises(AuditChainTamperError, match="self_hash mismatch"):
        ledger.verify_chain()


# --------------------------------------------------------------------------- #
# AL-PROBE-04 — illegal one-call DEFCON de-escalation fails safe (cre gap fixed).
# --------------------------------------------------------------------------- #


def test_al_probe_04_one_call_shutdown_to_normal_refused() -> None:
    c = DefconController()
    c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
    # The catalog's exact construction: a single unguarded call relaxing
    # containment all the way to NORMAL. Now REFUSED; stays SHUTDOWN.
    with pytest.raises(DefconDeEscalationError):
        c.transition_to(DefconState.NORMAL, actor="rogue", reason="resume")
    assert c.state == DefconState.SHUTDOWN


def test_al_probe_04_manual_override_fail_closed_without_authorizer() -> None:
    c = DefconController()
    c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
    with pytest.raises(DefconOverrideRejectedError):
        c.manual_override(DefconState.NORMAL, authorizer=None, operator_id="op", reason="resume")
    assert c.state == DefconState.SHUTDOWN


def test_al_probe_04_manual_override_rejected_stays_shutdown() -> None:
    c = DefconController()
    c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
    with pytest.raises(DefconOverrideRejectedError):
        c.manual_override(
            DefconState.NORMAL, authorizer=_RejectAll(), operator_id="op", reason="resume"
        )
    assert c.state == DefconState.SHUTDOWN


def test_al_probe_04_approved_override_deescalates() -> None:
    c = DefconController()
    c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
    c.manual_override(
        DefconState.NORMAL, authorizer=_AllowAll(), operator_id="op", reason="reviewed; safe"
    )
    assert c.state == DefconState.NORMAL


# --------------------------------------------------------------------------- #
# AL-PROBE-05 — N/A: cre has no effective-challenge primitive. NEVER fabricated.
# --------------------------------------------------------------------------- #


def test_al_probe_05_not_applicable_no_effective_challenge_primitive() -> None:
    """AL-PROBE-05 is N/A for cre — there is no effective-challenge primitive.

    Effective challenge (SR 11-7 §V.1) exists only in finserv-agent-audit. cre
    has no such module, so there is nothing to probe. We assert the absence and
    record the N/A as a documented skip rather than fabricating a pass.
    """
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("cre_agent_audit.governance.effective_challenge_harness")
    pytest.skip(
        "AL-PROBE-05 N/A — cre has no effective-challenge primitive "
        "(documented, not fabricated; effective challenge lives in finserv only)."
    )
