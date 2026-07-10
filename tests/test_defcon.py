"""Tests for DEFCON state machine — ADR-0001."""

from __future__ import annotations

import pytest

from cre_agent_audit.governance.defcon import (
    Capability,
    DefconController,
    DefconDeEscalationError,
    DefconOverrideRejectedError,
    DefconState,
    DefconTransition,
)


class _AllowAuthorizer:
    def authorize(self, operator_id: str, action: str, context: dict) -> bool:  # type: ignore[type-arg]
        return True


class _RejectAuthorizer:
    def authorize(self, operator_id: str, action: str, context: dict) -> bool:  # type: ignore[type-arg]
        return False


class TestDefconInitialState:
    def test_starts_at_normal(self) -> None:
        controller = DefconController()
        assert controller.state == DefconState.NORMAL

    def test_normal_is_defcon_5(self) -> None:
        assert DefconState.NORMAL.level == 5

    def test_shutdown_is_defcon_1(self) -> None:
        assert DefconState.SHUTDOWN.level == 1


class TestDefconCapabilityAllowlist:
    def test_normal_allows_all_capabilities(self) -> None:
        controller = DefconController()
        for capability in Capability:
            assert controller.is_allowed(capability) is True

    def test_heightened_requires_cosign_for_material_writes(self) -> None:
        controller = DefconController(initial_state=DefconState.HEIGHTENED)
        # Material writes are allowed but flagged as requiring co-sign.
        assert controller.is_allowed(Capability.LEASE_MATERIAL_WRITE) is True
        assert controller.requires_cosign(Capability.LEASE_MATERIAL_WRITE) is True
        # Non-material capabilities remain unchanged.
        assert controller.requires_cosign(Capability.RENT_COMP_INGEST) is False

    def test_restricted_pauses_tenant_screening_and_rent_optimization(self) -> None:
        controller = DefconController(initial_state=DefconState.RESTRICTED)
        assert controller.is_allowed(Capability.TENANT_SCREENING) is False
        assert controller.is_allowed(Capability.RENT_OPTIMIZATION) is False
        # Lease abstraction continues with mandatory reviewer signature.
        assert controller.is_allowed(Capability.LEASE_ABSTRACTION) is True
        assert controller.requires_cosign(Capability.LEASE_ABSTRACTION) is True

    def test_containment_pauses_all_writes_keeps_audit(self) -> None:
        controller = DefconController(initial_state=DefconState.CONTAINMENT)
        # Reads remain allowed.
        assert controller.is_allowed(Capability.LEASE_ABSTRACTION_READ) is True
        # All writes paused.
        assert controller.is_allowed(Capability.LEASE_MATERIAL_WRITE) is False
        assert controller.is_allowed(Capability.TENANT_SCREENING) is False
        assert controller.is_allowed(Capability.RENT_OPTIMIZATION) is False
        # Audit ledger keeps writing.
        assert controller.is_allowed(Capability.AUDIT_WRITE) is True

    def test_shutdown_offline_keeps_audit(self) -> None:
        controller = DefconController(initial_state=DefconState.SHUTDOWN)
        # Agents offline.
        for capability in Capability:
            if capability is Capability.AUDIT_WRITE:
                continue
            assert controller.is_allowed(capability) is False, (
                f"Capability {capability!r} should be blocked at SHUTDOWN"
            )
        # Audit ledger continues writing.
        assert controller.is_allowed(Capability.AUDIT_WRITE) is True


class TestDefconTransitions:
    def test_operator_transition_records_actor_reason_and_states(self) -> None:
        controller = DefconController()
        transition = controller.transition_to(
            DefconState.HEIGHTENED,
            actor="operator:kunjar",
            reason="anomaly: veto-rate spike in last 60 min",
        )
        assert isinstance(transition, DefconTransition)
        assert transition.prior_state is DefconState.NORMAL
        assert transition.new_state is DefconState.HEIGHTENED
        assert transition.actor == "operator:kunjar"
        assert transition.reason.startswith("anomaly:")
        assert controller.state is DefconState.HEIGHTENED

    def test_transition_estimated_duration_defaults_to_none(self) -> None:
        controller = DefconController()
        transition = controller.transition_to(
            DefconState.HEIGHTENED, actor="operator:kunjar", reason="lease season"
        )
        assert transition.estimated_duration is None

    def test_transition_estimated_duration_is_preserved(self) -> None:
        from datetime import timedelta

        controller = DefconController()
        duration = timedelta(hours=4)
        transition = controller.transition_to(
            DefconState.HEIGHTENED,
            actor="operator:kunjar",
            reason="lease season",
            estimated_duration=duration,
        )
        assert transition.estimated_duration == duration

    def test_history_records_every_transition_in_order(self) -> None:
        controller = DefconController()
        controller.transition_to(DefconState.HEIGHTENED, actor="op", reason="r1")
        controller.transition_to(DefconState.RESTRICTED, actor="op", reason="r2")
        # P4 — de-escalation (RESTRICTED -> NORMAL) must go through the
        # Authorizer-gated manual_override path, not the unguarded transition_to.
        controller.manual_override(
            DefconState.NORMAL,
            authorizer=_AllowAuthorizer(),
            operator_id="op",
            reason="r3 — back to normal",
        )
        history = controller.history
        assert len(history) == 3
        assert [t.new_state for t in history] == [
            DefconState.HEIGHTENED,
            DefconState.RESTRICTED,
            DefconState.NORMAL,
        ]
        assert [t.prior_state for t in history] == [
            DefconState.NORMAL,
            DefconState.HEIGHTENED,
            DefconState.RESTRICTED,
        ]


class TestDefconValidation:
    def test_transition_actor_must_be_non_empty(self) -> None:
        controller = DefconController()
        with pytest.raises(ValueError, match="actor"):
            controller.transition_to(DefconState.HEIGHTENED, actor="", reason="r")

    def test_transition_reason_must_be_non_empty(self) -> None:
        controller = DefconController()
        with pytest.raises(ValueError, match="reason"):
            controller.transition_to(DefconState.HEIGHTENED, actor="op", reason="")

    def test_audit_write_capability_is_always_allowed(self) -> None:
        # The ledger MUST continue across every state — verified once across all states.
        for state in DefconState:
            controller = DefconController(initial_state=state)
            assert controller.is_allowed(Capability.AUDIT_WRITE) is True, (
                f"Audit write must remain allowed at {state!r}"
            )


# --------------------------------------------------------------------------- #
# P4 — transition-direction guard: no one-call de-escalation via transition_to;
# de-escalation requires manual_override + a wired Authorizer (fail-closed).
# --------------------------------------------------------------------------- #


class TestDefconTransitionDirectionGuard:
    def test_escalation_via_transition_to_allowed(self) -> None:
        c = DefconController()
        c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
        assert c.state == DefconState.SHUTDOWN

    def test_one_call_deescalation_shutdown_to_normal_refused(self) -> None:
        c = DefconController()
        c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
        with pytest.raises(DefconDeEscalationError, match="not permitted via transition_to"):
            c.transition_to(DefconState.NORMAL, actor="rogue", reason="resume")
        assert c.state == DefconState.SHUTDOWN  # fail-safe: stays contained

    def test_manual_override_without_authorizer_fails_closed(self) -> None:
        c = DefconController()
        c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
        with pytest.raises(DefconOverrideRejectedError, match="requires a wired Authorizer"):
            c.manual_override(
                DefconState.NORMAL, authorizer=None, operator_id="op", reason="resume"
            )
        assert c.state == DefconState.SHUTDOWN

    def test_manual_override_rejected_by_authorizer_stays_shutdown(self) -> None:
        c = DefconController()
        c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
        with pytest.raises(DefconOverrideRejectedError, match="rejected"):
            c.manual_override(
                DefconState.NORMAL,
                authorizer=_RejectAuthorizer(),
                operator_id="op",
                reason="resume",
            )
        assert c.state == DefconState.SHUTDOWN

    def test_manual_override_approved_deescalates(self) -> None:
        c = DefconController()
        c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
        c.manual_override(
            DefconState.NORMAL,
            authorizer=_AllowAuthorizer(),
            operator_id="op",
            reason="reviewed; safe to resume",
        )
        assert c.state == DefconState.NORMAL

    def test_idempotent_same_state_allowed_via_transition_to(self) -> None:
        c = DefconController()
        t = c.transition_to(DefconState.NORMAL, actor="op", reason="noop")
        assert t.new_state == DefconState.NORMAL

    def test_manual_override_empty_operator_id_rejected(self) -> None:
        c = DefconController()
        c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
        with pytest.raises(ValueError, match="operator_id"):
            c.manual_override(
                DefconState.NORMAL, authorizer=_AllowAuthorizer(), operator_id="", reason="r"
            )

    def test_manual_override_empty_reason_rejected(self) -> None:
        c = DefconController()
        c.transition_to(DefconState.SHUTDOWN, actor="risk", reason="kill")
        with pytest.raises(ValueError, match="reason"):
            c.manual_override(
                DefconState.NORMAL, authorizer=_AllowAuthorizer(), operator_id="op", reason=""
            )
