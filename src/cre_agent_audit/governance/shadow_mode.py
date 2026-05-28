"""Shadow Mode Rollout — ADR-0006.

Routes production traffic to both a *live* agent path and a *shadow* agent
path. The live path executes; the shadow path is recorded but silent. A
divergence monitor compares the two and exposes:

- Aggregate divergence rate
- Veto direction (shadow more conservative · shadow more aggressive · equivalent)
- Cohort-specific divergence (disparate impact on the divergence itself)
- Promotion verdict against the ADR-0006 promotion-gate matrix
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class VetoDirection(Enum):
    SHADOW_MORE_CONSERVATIVE = "shadow_more_conservative"
    """Shadow vetoes more often than live → live should *think* before promotion."""

    SHADOW_MORE_AGGRESSIVE = "shadow_more_aggressive"
    """Shadow vetoes less often than live → never promote without explicit risk owner."""

    EQUIVALENT = "equivalent"
    """Veto rates are equal (within float tolerance)."""


class DecisionClass(Enum):
    """Per-class promotion-gate thresholds per ADR-0006."""

    INFORMATIONAL = "informational"
    MATERIAL_LEASE = "material_lease"
    FAIR_HOUSING = "fair_housing"
    RENT_OPTIMIZATION = "rent_optimization"


@dataclass(frozen=True)
class _GateConfig:
    min_shadow_duration: timedelta
    max_aggregate_divergence: float
    require_zero_worse_direction_per_cohort: bool = False


_GATE_MATRIX: dict[DecisionClass, _GateConfig] = {
    DecisionClass.INFORMATIONAL: _GateConfig(
        min_shadow_duration=timedelta(days=7),
        max_aggregate_divergence=0.05,
    ),
    DecisionClass.MATERIAL_LEASE: _GateConfig(
        min_shadow_duration=timedelta(days=30),
        max_aggregate_divergence=0.02,
    ),
    DecisionClass.FAIR_HOUSING: _GateConfig(
        min_shadow_duration=timedelta(days=60),
        max_aggregate_divergence=0.01,
        require_zero_worse_direction_per_cohort=True,
    ),
    DecisionClass.RENT_OPTIMIZATION: _GateConfig(
        min_shadow_duration=timedelta(days=90),
        max_aggregate_divergence=0.01,
    ),
}


@dataclass(frozen=True)
class DecisionOutcome:
    """Generic outcome shape both paths must agree on for divergence comparison."""

    outcome: str  # 'APPROVE' | 'DENY' | 'REVIEW' | 'VETO'
    veto_reason_code: str | None = None
    cohort: str | None = None


@dataclass(frozen=True)
class _Observation:
    when: datetime
    live: DecisionOutcome
    shadow: DecisionOutcome


@dataclass(frozen=True)
class PromotionVerdict:
    """Structured result of a shadow-to-live promotion check."""

    passed: bool
    failures: tuple[str, ...]


AgentFn = Callable[..., DecisionOutcome]


@dataclass
class ShadowRouter:
    """Routes one input through both the live and shadow agent paths."""

    live_fn: AgentFn
    shadow_fn: AgentFn
    observations: list[_Observation] = field(default_factory=list, init=False, repr=False)

    def route(self, action: object, *, now: datetime) -> DecisionOutcome:
        """Run both paths. Record the observation. Return the *live* outcome."""
        live = self.live_fn(action, now=now)
        shadow = self.shadow_fn(action, now=now)
        self.observations.append(_Observation(when=now, live=live, shadow=shadow))
        return live

    # ----------------------------- metrics ------------------------------ #

    def _entries_in_window(self, *, now: datetime, window: timedelta | None) -> list[_Observation]:
        if window is None:
            return list(self.observations)
        cutoff = now - window
        return [o for o in self.observations if o.when >= cutoff]

    def aggregate_divergence_rate(
        self,
        *,
        now: datetime | None = None,
        window: timedelta | None = None,
    ) -> float:
        if not self.observations:
            return 0.0
        # When window is None we use all observations; ``now`` is unused.
        if window is not None and now is None:
            raise ValueError("window requires now")
        entries = (
            self._entries_in_window(now=now, window=window)  # type: ignore[arg-type]
            if window is not None
            else list(self.observations)
        )
        if not entries:
            return 0.0
        disagreements = sum(1 for e in entries if e.live.outcome != e.shadow.outcome)
        return disagreements / len(entries)

    def veto_direction(self) -> VetoDirection:
        if not self.observations:
            return VetoDirection.EQUIVALENT
        live_vetoes = sum(1 for e in self.observations if e.live.outcome == "VETO")
        shadow_vetoes = sum(1 for e in self.observations if e.shadow.outcome == "VETO")
        if shadow_vetoes > live_vetoes:
            return VetoDirection.SHADOW_MORE_CONSERVATIVE
        if shadow_vetoes < live_vetoes:
            return VetoDirection.SHADOW_MORE_AGGRESSIVE
        return VetoDirection.EQUIVALENT

    def cohort_divergence_rate(self, cohort: str) -> float:
        cohort_entries = [
            e for e in self.observations if (e.live.cohort == cohort or e.shadow.cohort == cohort)
        ]
        if not cohort_entries:
            return 0.0
        disagreements = sum(1 for e in cohort_entries if e.live.outcome != e.shadow.outcome)
        return disagreements / len(cohort_entries)

    def shadow_time_in_state(self, *, now: datetime) -> timedelta:
        if not self.observations:
            return timedelta(0)
        first = min(o.when for o in self.observations)
        return now - first

    # ---------------------------- promotion ----------------------------- #

    def promotion_check(self, decision_class: DecisionClass, *, now: datetime) -> PromotionVerdict:
        config = _GATE_MATRIX[decision_class]
        failures: list[str] = []

        duration = self.shadow_time_in_state(now=now)
        if duration < config.min_shadow_duration:
            failures.append(
                f"shadow duration {duration.days}d below minimum shadow duration "
                f"{config.min_shadow_duration.days}d for {decision_class.value}"
            )

        divergence = self.aggregate_divergence_rate()
        if divergence > config.max_aggregate_divergence:
            failures.append(
                f"aggregate divergence {divergence:.4f} exceeds threshold "
                f"{config.max_aggregate_divergence:.4f} for {decision_class.value}"
            )

        if config.require_zero_worse_direction_per_cohort:
            # Fair-housing rule: zero shadow-more-conservative vetoes on any
            # protected cohort. A worse-direction veto on a protected cohort
            # is itself a fair-housing concern.
            cohorts: set[str] = {
                o.live.cohort for o in self.observations if o.live.cohort is not None
            } | {o.shadow.cohort for o in self.observations if o.shadow.cohort is not None}
            for cohort in cohorts:
                live_vetoes = sum(
                    1
                    for o in self.observations
                    if o.live.cohort == cohort and o.live.outcome == "VETO"
                )
                shadow_vetoes = sum(
                    1
                    for o in self.observations
                    if o.shadow.cohort == cohort and o.shadow.outcome == "VETO"
                )
                if shadow_vetoes > live_vetoes:
                    failures.append(
                        f"protected cohort {cohort!r} has {shadow_vetoes} shadow "
                        f"vetoes vs {live_vetoes} live vetoes (worse direction)"
                    )

        return PromotionVerdict(passed=not failures, failures=tuple(failures))
