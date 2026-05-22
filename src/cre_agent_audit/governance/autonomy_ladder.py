"""Autonomy Ladder™ A0 → A4 — ADR-0004.

Five named maturity tiers and an explicit A2 → A3 promotion gate. The A2 →
A3 promotion is the regulator-visible boundary: it requires the sovereign
veto layer load-tested under representative traffic, the audit ledger
running for ≥ 90 days, the shadow mode running for ≥ 30 days with no
material divergence, and a circuit-breaker tested at least quarterly.

The promotion gate is the work, not the framework. This module codifies
the *check*; the *evidence* for each criterion is gathered by the program
team and supplied to ``check_a2_to_a3_promotion``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum


class AutonomyTier(Enum):
    """Five-tier Autonomy Ladder™ maturity scaffold.

    Each tier carries semantic flags read by the orchestrator and surfaced
    on the audit ledger. Tier objects are intentionally lightweight — they
    describe *what the tier permits*, not *how to implement* it.
    """

    A0_INFORMATIONAL = "A0"
    A1_ASSISTED = "A1"
    A2_DELEGATED = "A2"
    A3_SUPERVISED_AUTONOMOUS = "A3"
    A4_PRODUCTION_AUTONOMOUS = "A4"

    @property
    def can_write(self) -> bool:
        return self is not AutonomyTier.A0_INFORMATIONAL

    @property
    def requires_human_approval(self) -> bool:
        """Every write requires human approval before commit."""
        return self is AutonomyTier.A1_ASSISTED

    @property
    def requires_envelope(self) -> bool:
        """Writes must live inside a hard pre-defined envelope (A2 only)."""
        return self is AutonomyTier.A2_DELEGATED

    @property
    def requires_sampled_review(self) -> bool:
        """Human reviews a sampled subset; all out-of-envelope decisions still reviewed."""
        return self is AutonomyTier.A2_DELEGATED

    @property
    def requires_human_exception_supervision(self) -> bool:
        """A3+: humans supervise by exception, not by approval."""
        return self in (
            AutonomyTier.A3_SUPERVISED_AUTONOMOUS,
            AutonomyTier.A4_PRODUCTION_AUTONOMOUS,
        )


@dataclass(frozen=True)
class PromotionRequirements:
    """Evidence required to clear the A2 → A3 promotion gate.

    Each field corresponds 1:1 to a criterion in ADR-0004's "promotion
    requires" list.
    """

    sovereign_veto_load_tested: bool
    audit_ledger_running_for: timedelta
    shadow_mode_running_for: timedelta
    circuit_breaker_test_recent: bool


class PromotionGateNotMet(RuntimeError):
    """Raised by ``PromotionGateReport.raise_if_blocked`` on a failed gate."""


@dataclass(frozen=True)
class PromotionGateReport:
    """Structured result of the A2 → A3 promotion gate check.

    ``failures`` is a tuple of short human-readable strings — one per failed
    criterion. ``passed`` is True only when ``failures`` is empty.
    """

    passed: bool
    failures: tuple[str, ...]

    def raise_if_blocked(self) -> None:
        if not self.passed:
            raise PromotionGateNotMet(
                "A2 → A3 promotion gate not met: " + " · ".join(self.failures)
            )


_MIN_AUDIT_LEDGER_DAYS = 90
_MIN_SHADOW_MODE_DAYS = 30


def check_a2_to_a3_promotion(requirements: PromotionRequirements) -> PromotionGateReport:
    """Evaluate the four promotion criteria.

    Returns a report with the full list of failures (not just the first one)
    so the program team sees every gap in one pass.
    """
    failures: list[str] = []
    if not requirements.sovereign_veto_load_tested:
        failures.append(
            "sovereign_veto not load-tested under representative traffic"
        )
    if requirements.audit_ledger_running_for < timedelta(days=_MIN_AUDIT_LEDGER_DAYS):
        days = requirements.audit_ledger_running_for.days
        failures.append(
            f"audit_ledger has been running for {days}d; "
            f"minimum is {_MIN_AUDIT_LEDGER_DAYS}d"
        )
    if requirements.shadow_mode_running_for < timedelta(days=_MIN_SHADOW_MODE_DAYS):
        days = requirements.shadow_mode_running_for.days
        failures.append(
            f"shadow_mode has been running for {days}d; "
            f"minimum is {_MIN_SHADOW_MODE_DAYS}d"
        )
    if not requirements.circuit_breaker_test_recent:
        failures.append("circuit_breaker test not recent (must be tested ≥ quarterly)")

    return PromotionGateReport(passed=not failures, failures=tuple(failures))
