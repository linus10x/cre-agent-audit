"""Fair-Housing Pre-Flight Gate — ADR-0008 (CRE-native).

Every agent action that touches a protected decision surface routes through
this gate before execution. The gate runs five ordered checks; each check
that fires raises a sovereign veto (ADR-0002) with a specific reason code.

    FHA-PROXY       protected-class proxy detected in input features
    FHA-VOUCHER     housing-voucher feature present (SafeRent failure mode)
    FHA-SOI         income-source feature in SOI-protected jurisdiction
    FHA-CRIM        blanket criminal disqualification or lookback breach
    FHA-DISPARATE   four-fifths rule breached on output cohort selection rates

A human can bypass any single veto for any single decision by filing a
FairHousingException. Three bypasses by the same owner in 90 days escalate
to the GC. Five bypasses on the same reason code in 90 days force the
program to DEFCON-4 (ADR-0001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from cre_agent_audit.governance.sovereign_veto import (
    AgentAction,
    ConstraintCheck,
    VetoResult,
)
from cre_agent_audit.schemas.screening_decision import (
    DEFAULT_SOI_PROTECTED_JURISDICTIONS,
    FairHousingException,
    JurisdictionRules,
    ScreeningDecision,
)

_DEFAULT_OWNER = "compliance:fair_housing_officer"
_DEFAULT_LOOKBACK_DAYS = 90
_FOUR_FIFTHS_RATIO = 0.80

# Voucher-correlated feature names. Per ADR-0008 / SafeRent.
_VOUCHER_FEATURE_NAMES: frozenset[str] = frozenset(
    {
        "has_section_8_voucher",
        "section_8",
        "housing_voucher",
        "voucher_status",
        "voucher_penalty_score",
        "rental_assistance",
    }
)

# Source-of-income feature names. Triggers FHA-SOI in SOI-protected jurisdictions.
_SOI_FEATURE_NAMES: frozenset[str] = frozenset(
    {
        "income_source_type",
        "income_source",
        "ssi_income",
        "ssdi_income",
        "social_security_income",
        "child_support_income",
    }
)

# Criminal-history features.
_CRIM_BLANKET_FEATURES: frozenset[str] = frozenset(
    {"criminal_history_blanket_deny", "no_criminal_history_allowed"}
)
_CRIM_YEARS_SINCE_FEATURE = "criminal_history_years_since"


@dataclass(frozen=True)
class ScreeningDecisionAction(AgentAction):
    """An agent-proposed screening decision routed through the Fair-Housing gate."""

    decision: ScreeningDecision = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.decision is None:
            raise ValueError("ScreeningDecisionAction requires a ScreeningDecision")


@dataclass
class _MonitorEntry:
    cohort: str
    approved: bool
    when: datetime


@dataclass
class DisparateImpactMonitor:
    """Running window of decisions across cohorts for the four-fifths rule.

    Each ``record`` call adds one outcome. ``lowest_cohort_ratio`` returns
    the minimum selection-rate ratio across cohorts inside the window. The
    ratio is computed as ``min_cohort_rate / max_cohort_rate``; a ratio
    below ``0.80`` is the four-fifths-rule breach.
    """

    window_days: int = _DEFAULT_LOOKBACK_DAYS
    _entries: list[_MonitorEntry] = field(default_factory=list, init=False, repr=False)

    def record(self, *, cohort: str, approved: bool, when: datetime) -> None:
        self._entries.append(_MonitorEntry(cohort=cohort, approved=approved, when=when))

    def lowest_cohort_ratio(self, *, now: datetime) -> float:
        cutoff = now - timedelta(days=self.window_days)
        rates: dict[str, list[bool]] = {}
        for entry in self._entries:
            if entry.when < cutoff:
                continue
            rates.setdefault(entry.cohort, []).append(entry.approved)
        if not rates:
            return 1.0  # no data → no detected disparity
        cohort_rates = {c: (sum(v) / len(v) if v else 0.0) for c, v in rates.items()}
        max_rate = max(cohort_rates.values())
        if max_rate <= 0.0:
            return 1.0
        min_rate = min(cohort_rates.values())
        return min_rate / max_rate


@dataclass
class BypassRegistry:
    """Tracks FairHousingException entries and surfaces auto-escalation signals.

    Per ADR-0008:
    - 3 bypasses by the same owner in 90 days → escalate to GC.
    - 5 bypasses on the same reason code in 90 days → force DEFCON-4.
    """

    window_days: int = _DEFAULT_LOOKBACK_DAYS
    _exceptions: list[FairHousingException] = field(default_factory=list, init=False, repr=False)

    def record(self, exception: FairHousingException) -> None:
        self._exceptions.append(exception)

    def should_escalate_to_gc(self, *, owner: str, now: datetime) -> bool:
        cutoff = now - timedelta(days=self.window_days)
        same_owner = [
            e for e in self._exceptions if e.bypass_owner == owner and e.timestamp >= cutoff
        ]
        return len(same_owner) >= 3

    def should_force_defcon_4(self, *, reason_code: str, now: datetime) -> bool:
        cutoff = now - timedelta(days=self.window_days)
        same_reason = [
            e
            for e in self._exceptions
            if e.veto_reason_code == reason_code and e.timestamp >= cutoff
        ]
        return len(same_reason) >= 5


@dataclass
class FairHousingPreflightGate(ConstraintCheck):
    """The five-check Fair-Housing Pre-Flight Gate.

    Constraint check registered against the protected-surface action classes
    (TENANT_SCREENING, RENEWAL_PRICING, MARKETING_AUDIENCE_TARGETING,
    HOUSING_CREDIT_DECISION, TENANT_COMMUNICATION_PERSONALIZATION).
    """

    jurisdiction_rules: dict[str, JurisdictionRules] = field(default_factory=dict)
    disparate_impact_monitor: DisparateImpactMonitor | None = None
    bypass_registry: BypassRegistry = field(default_factory=BypassRegistry)

    def _resolve_rules(self, jurisdiction: str) -> JurisdictionRules:
        override = self.jurisdiction_rules.get(jurisdiction)
        if override is not None:
            return override
        soi_protected = jurisdiction in DEFAULT_SOI_PROTECTED_JURISDICTIONS
        return JurisdictionRules(jurisdiction=jurisdiction, soi_protected=soi_protected)

    def evaluate(self, action: AgentAction) -> VetoResult:
        if not isinstance(action, ScreeningDecisionAction):
            return VetoResult.veto(
                reason_code="UNKNOWN-ACTION-CLASS",
                owner_required=_DEFAULT_OWNER,
                detail=(
                    "FairHousingPreflightGate received an action that is not a "
                    "ScreeningDecisionAction."
                ),
            )

        decision = action.decision
        rules = self._resolve_rules(decision.jurisdiction)

        # 1. Protected-class proxy detection.
        proxy_hit = next(
            (name for name in decision.features if name in rules.proxy_features_blocked),
            None,
        )
        if proxy_hit is not None:
            return VetoResult.veto(
                reason_code="FHA-PROXY",
                owner_required=_DEFAULT_OWNER,
                detail=(
                    f"Feature {proxy_hit!r} is on the protected-class-proxy "
                    f"blocklist for {decision.jurisdiction}."
                ),
            )

        # 2. Voucher-status (SafeRent failure mode).
        voucher_hit = next(
            (name for name in decision.features if name in _VOUCHER_FEATURE_NAMES),
            None,
        )
        if voucher_hit is not None:
            return VetoResult.veto(
                reason_code="FHA-VOUCHER",
                owner_required=_DEFAULT_OWNER,
                detail=(
                    f"Feature {voucher_hit!r} is voucher-correlated. SafeRent "
                    f"precedent (Nov 2024 · $2.3M settlement) governs."
                ),
            )

        # 3. Source-of-income (jurisdiction-specific).
        if rules.soi_protected:
            soi_hit = next(
                (name for name in decision.features if name in _SOI_FEATURE_NAMES),
                None,
            )
            if soi_hit is not None:
                return VetoResult.veto(
                    reason_code="FHA-SOI",
                    owner_required=_DEFAULT_OWNER,
                    detail=(
                        f"Feature {soi_hit!r} introduces income source into the "
                        f"decision in SOI-protected jurisdiction "
                        f"{decision.jurisdiction!r}."
                    ),
                )

        # 4. Criminal-history use bans.
        blanket_hit = next(
            (name for name in decision.features if name in _CRIM_BLANKET_FEATURES),
            None,
        )
        if blanket_hit is not None:
            return VetoResult.veto(
                reason_code="FHA-CRIM",
                owner_required=_DEFAULT_OWNER,
                detail=(
                    "Blanket criminal-history disqualification feature detected. "
                    "HUD 2016 guidance requires individualized assessment."
                ),
            )
        if (
            rules.criminal_history_lookback_limit_years is not None
            and _CRIM_YEARS_SINCE_FEATURE in decision.features
        ):
            years_since = float(decision.features[_CRIM_YEARS_SINCE_FEATURE])
            if years_since > rules.criminal_history_lookback_limit_years:
                return VetoResult.veto(
                    reason_code="FHA-CRIM",
                    owner_required=_DEFAULT_OWNER,
                    detail=(
                        f"Criminal-history input is {years_since:.1f} years old; "
                        f"jurisdiction {decision.jurisdiction!r} lookback limit "
                        f"is {rules.criminal_history_lookback_limit_years} years."
                    ),
                )

        # 5. Disparate-impact monitor on outputs.
        if self.disparate_impact_monitor is not None:
            ratio = self.disparate_impact_monitor.lowest_cohort_ratio(
                now=datetime.now(timezone.utc)
            )
            if ratio < _FOUR_FIFTHS_RATIO:
                return VetoResult.veto(
                    reason_code="FHA-DISPARATE",
                    owner_required=_DEFAULT_OWNER,
                    detail=(
                        f"Four-fifths rule breached. Lowest cohort selection-rate "
                        f"ratio is {ratio:.2f} < {_FOUR_FIFTHS_RATIO:.2f}."
                    ),
                )

        return VetoResult.passing()
