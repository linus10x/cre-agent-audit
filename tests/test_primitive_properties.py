"""Property-based invariants for the hardened cre primitives (§7 volume tier).

Hundreds of generated cases per property (thousands across the module), pinning
the invariants the S1 hardening established for cre: P1 level-gate, P3 ledger
tamper-evidence, P4 DEFCON transition-direction guard.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditChainTamperError,
    AuditEntry,
    AuditLedger,
)
from cre_agent_audit.governance.autonomy_ladder import (
    CriterionAttestation,
    PromotionRequirements,
    check_a2_to_a3_promotion,
)
from cre_agent_audit.governance.defcon import (
    DefconController,
    DefconDeEscalationError,
    DefconOverrideRejectedError,
    DefconState,
)

_CRITERIA = (
    "sovereign_veto_load_tested",
    "audit_ledger_running_for",
    "shadow_mode_running_for",
    "circuit_breaker_test_recent",
)


class _Allow:
    def authorize(self, operator_id: str, action: str, context: dict[str, Any]) -> bool:
        return True


class _Reject:
    def authorize(self, operator_id: str, action: str, context: dict[str, Any]) -> bool:
        return False


# --------------------------------------------------------------------------- #
# P1 — level-gate monotonicity + advisory/strict invariants.
# --------------------------------------------------------------------------- #


@settings(max_examples=400)
@given(
    veto=st.booleans(),
    ledger_days=st.integers(min_value=0, max_value=400),
    shadow_days=st.integers(min_value=0, max_value=400),
    cb=st.booleans(),
)
def test_p1_passes_iff_all_criteria_met(
    veto: bool, ledger_days: int, shadow_days: int, cb: bool
) -> None:
    reqs = PromotionRequirements(
        sovereign_veto_load_tested=veto,
        audit_ledger_running_for=timedelta(days=ledger_days),
        shadow_mode_running_for=timedelta(days=shadow_days),
        circuit_breaker_test_recent=cb,
    )
    report = check_a2_to_a3_promotion(reqs)
    all_met = veto and cb and ledger_days >= 90 and shadow_days >= 30
    assert report.passed is all_met
    assert report.advisory is True


@settings(max_examples=300)
@given(line=st.integers(min_value=1, max_value=3))
def test_p1_strict_requires_independent_attestation(line: int) -> None:
    reqs = PromotionRequirements(
        sovereign_veto_load_tested=True,
        audit_ledger_running_for=timedelta(days=120),
        shadow_mode_running_for=timedelta(days=45),
        circuit_breaker_test_recent=True,
    )
    atts = {
        k: CriterionAttestation(
            criterion=k,
            attestor_id="x",
            line_of_defense=line,
            attested_at="2026-06-05T00:00:00+00:00",
        )
        for k in _CRITERIA
    }
    report = check_a2_to_a3_promotion(reqs, attestations=atts, require_attestation=True)
    assert report.passed is (line in (2, 3))
    assert report.advisory is False


# --------------------------------------------------------------------------- #
# P3 — ledger: clean chain verifies; any in-place tamper detected.
# --------------------------------------------------------------------------- #


def _seed(n: int) -> AuditLedger:
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


@settings(max_examples=200, deadline=None)
@given(n=st.integers(min_value=1, max_value=15))
def test_p3_clean_chain_verifies(n: int) -> None:
    _seed(n).verify_chain()  # must NOT raise


@settings(max_examples=200, deadline=None)
@given(data=st.data())
def test_p3_inplace_tamper_always_detected(data: Any) -> None:
    n = data.draw(st.integers(min_value=1, max_value=12))
    ledger = _seed(n)
    idx = data.draw(st.integers(min_value=0, max_value=n - 1))
    e = ledger.entries[idx]
    tampered = AuditEntry(
        sequence=e.sequence,
        timestamp=e.timestamp,
        actor_kind=e.actor_kind,
        actor_id=e.actor_id,
        decision_type=e.decision_type,
        action_payload=b"TAMPERED_" + str(idx).encode(),
        gate_verdicts=e.gate_verdicts,
        prior_hash=e.prior_hash,
        self_hash=e.self_hash,  # stale
    )
    ledger._replace_entry_for_tests(idx, tampered)
    with pytest.raises(AuditChainTamperError):
        ledger.verify_chain()


# --------------------------------------------------------------------------- #
# P4 — transition-direction guard: de-escalation via transition_to always
# refused; manual_override fail-closed without an approving Authorizer.
# --------------------------------------------------------------------------- #

_STATES = list(DefconState)


@settings(max_examples=300, suppress_health_check=[HealthCheck.filter_too_much])
@given(data=st.data())
def test_p4_deescalation_via_transition_to_always_refused(data: Any) -> None:
    start = data.draw(st.sampled_from(_STATES))
    target = data.draw(st.sampled_from(_STATES))
    c = DefconController(initial_state=start)
    if target.level > start.level:
        # De-escalation (toward NORMAL) — must be refused.
        with pytest.raises(DefconDeEscalationError):
            c.transition_to(target, actor="op", reason="r")
        assert c.state == start
    else:
        # Escalation or same-state — allowed.
        c.transition_to(target, actor="op", reason="r")
        assert c.state == target


@settings(max_examples=200)
@given(data=st.data(), approve=st.booleans())
def test_p4_manual_override_fail_closed(data: Any, approve: bool) -> None:
    # Start contained; attempt to de-escalate to a less-severe state.
    c = DefconController(initial_state=DefconState.SHUTDOWN)
    target = data.draw(
        st.sampled_from([s for s in _STATES if s.level >= DefconState.SHUTDOWN.level])
    )
    authorizer = _Allow() if approve else _Reject()
    if approve:
        c.manual_override(target, authorizer=authorizer, operator_id="op", reason="reviewed")
        assert c.state == target
    else:
        with pytest.raises(DefconOverrideRejectedError):
            c.manual_override(target, authorizer=authorizer, operator_id="op", reason="x")
        assert c.state == DefconState.SHUTDOWN


@settings(max_examples=100)
@given(target=st.sampled_from(_STATES))
def test_p4_manual_override_none_authorizer_fail_closed(target: DefconState) -> None:
    c = DefconController(initial_state=DefconState.SHUTDOWN)
    with pytest.raises(DefconOverrideRejectedError):
        c.manual_override(target, authorizer=None, operator_id="op", reason="x")
    assert c.state == DefconState.SHUTDOWN
