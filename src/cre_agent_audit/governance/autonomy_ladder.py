"""Autonomy Ladder™ A0 → A4 — ADR-0004.

Five named maturity tiers and an explicit A2 → A3 promotion gate. The A2 →
A3 promotion is the regulator-visible boundary: it requires the sovereign
veto layer load-tested under representative traffic, the audit ledger
running for ≥ 90 days, the shadow mode running for ≥ 30 days with no
material divergence, and a circuit-breaker tested at least quarterly.

The promotion gate is the work, not the framework. This module codifies
the *check*; the *evidence* for each criterion is gathered by the program
team and supplied to ``check_a2_to_a3_promotion``.

**Advisory by default (P1).** The default check is ADVISORY: it evaluates
the caller-asserted ``PromotionRequirements`` and trusts those inputs — it
does not itself collect or verify the evidence. The returned report carries
``advisory=True`` and must NOT be presented as an enforcing control. To make
the gate enforcing, run it with ``require_attestation=True`` and a mapping of
independent (second- or third-line) ``CriterionAttestation`` records.
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
class CriterionAttestation:
    """P1 — independent attestation of one promotion criterion's evidence.

    ``line_of_defense``: 1 = program team (NOT independent), 2 = model
    validation / MRM, 3 = internal audit. Independent attestation requires
    line 2 or 3 — a first-line self-attestation does not clear the strict
    gate.
    """

    criterion: str
    attestor_id: str
    line_of_defense: int
    attested_at: str
    statement: str = ""

    @property
    def is_independent(self) -> bool:
        return self.line_of_defense in (2, 3)


@dataclass(frozen=True)
class PromotionGateReport:
    """Structured result of the A2 → A3 promotion gate check.

    ``failures`` is a tuple of short human-readable strings — one per failed
    criterion. ``passed`` is True only when ``failures`` is empty.

    ``advisory`` is True when the check ran WITHOUT independent attestation
    (the default): the result reflects only caller-asserted inputs and is NOT
    an enforcing control.
    """

    passed: bool
    failures: tuple[str, ...]
    advisory: bool = True

    def raise_if_blocked(self) -> None:
        if not self.passed:
            raise PromotionGateNotMet(
                "A2 → A3 promotion gate not met: " + " · ".join(self.failures)
            )


_MIN_AUDIT_LEDGER_DAYS = 90
_MIN_SHADOW_MODE_DAYS = 30

_CRITERION_KEYS = (
    "sovereign_veto_load_tested",
    "audit_ledger_running_for",
    "shadow_mode_running_for",
    "circuit_breaker_test_recent",
)


def check_a2_to_a3_promotion(
    requirements: PromotionRequirements,
    *,
    attestations: dict[str, CriterionAttestation] | None = None,
    require_attestation: bool = False,
) -> PromotionGateReport:
    """Evaluate the four promotion criteria.

    Returns a report with the full list of failures (not just the first one)
    so the program team sees every gap in one pass.

    **P1 — advisory vs enforcing.** Advisory by default (trusts caller-asserted
    inputs; report ``advisory=True``). Pass ``require_attestation=True`` plus an
    ``attestations`` mapping (criterion key -> :class:`CriterionAttestation`) to
    run the STRICT gate: every otherwise-satisfied criterion must carry an
    INDEPENDENT (line-2/3) attestation or it is recorded as a failure. Opt-in;
    does not change the default.
    """
    attestations = attestations or {}
    failures: list[str] = []

    def _satisfied(key: str) -> bool:
        if key == "sovereign_veto_load_tested":
            return requirements.sovereign_veto_load_tested
        if key == "audit_ledger_running_for":
            return requirements.audit_ledger_running_for >= timedelta(days=_MIN_AUDIT_LEDGER_DAYS)
        if key == "shadow_mode_running_for":
            return requirements.shadow_mode_running_for >= timedelta(days=_MIN_SHADOW_MODE_DAYS)
        return requirements.circuit_breaker_test_recent

    if not requirements.sovereign_veto_load_tested:
        failures.append("sovereign_veto not load-tested under representative traffic")
    if requirements.audit_ledger_running_for < timedelta(days=_MIN_AUDIT_LEDGER_DAYS):
        days = requirements.audit_ledger_running_for.days
        failures.append(
            f"audit_ledger has been running for {days}d; minimum is {_MIN_AUDIT_LEDGER_DAYS}d"
        )
    if requirements.shadow_mode_running_for < timedelta(days=_MIN_SHADOW_MODE_DAYS):
        days = requirements.shadow_mode_running_for.days
        failures.append(
            f"shadow_mode has been running for {days}d; minimum is {_MIN_SHADOW_MODE_DAYS}d"
        )
    if not requirements.circuit_breaker_test_recent:
        failures.append("circuit_breaker test not recent (must be tested ≥ quarterly)")

    if require_attestation:
        for key in _CRITERION_KEYS:
            if not _satisfied(key):
                continue
            att = attestations.get(key)
            if att is None:
                failures.append(f"{key}: no independent attestation supplied (strict mode)")
            elif not att.is_independent:
                failures.append(
                    f"{key}: attestation by {att.attestor_id!r} is line-{att.line_of_defense} "
                    "(not independent; requires second- or third-line)"
                )

    return PromotionGateReport(
        passed=not failures,
        failures=tuple(failures),
        advisory=not require_attestation,
    )
