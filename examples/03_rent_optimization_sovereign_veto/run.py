"""Example 03 — Rent Optimization with Sovereign Veto.

This example exercises the full DEFCON + Sovereign Veto + Audit Ledger stack
on a rent-optimization action. The constraint check models operator-side
controls relevant to U.S. v. RealPage, Inc. et al., M.D.N.C., filed
August 23, 2024 (ongoing antitrust litigation, alleged Sherman § 1 violations,
not adjudicated). Restrictions modeled: data older than 12 months only,
state-level granularity only, no coordinated price recommendations across
owners in the same market. Not legal advice — consult antitrust counsel.

Run:
    python examples/03_rent_optimization_sovereign_veto/run.py
"""

from __future__ import annotations

from dataclasses import dataclass

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.governance.defcon import Capability, DefconController, DefconState
from cre_agent_audit.governance.sovereign_veto import (
    AgentAction,
    ConstraintCheck,
    SovereignVeto,
    VetoResult,
)


@dataclass(frozen=True)
class RentOptimizationAction(AgentAction):
    market_geo_granularity: str  # 'state' | 'metro' | 'submarket' | 'building'
    training_data_age_months: int
    coordinated_with_other_owners: bool
    recommended_rent: float


class RealPageAntitrustCheck(ConstraintCheck):
    """Pre-flight constraint check modeling operator-side controls relevant to U.S. v. RealPage, Inc. et al., M.D.N.C., filed August 23, 2024 — ongoing antitrust litigation, not adjudicated."""

    MAX_GRANULARITY = "state"
    MIN_DATA_AGE_MONTHS = 12

    def evaluate(self, action: AgentAction) -> VetoResult:
        rent_action = action  # narrow at use sites
        granularity = getattr(rent_action, "market_geo_granularity", "")
        data_age = getattr(rent_action, "training_data_age_months", 0)
        coordinated = getattr(rent_action, "coordinated_with_other_owners", False)

        if granularity != self.MAX_GRANULARITY:
            return VetoResult.veto(
                reason_code="ANTITRUST-GEO-GRANULARITY",
                owner_required="legal:antitrust_counsel",
                detail=(
                    f"Rent-pricing AI emitted recommendation at {granularity!r} granularity. "
                    f"U.S. v. RealPage, Inc. et al., M.D.N.C., filed August 23, 2024 — "
                    f"ongoing antitrust litigation, ALLEGED conduct. Operator control "
                    f"restricts recommendations to {self.MAX_GRANULARITY!r}-level granularity. "
                    f"Consult antitrust counsel re: Sherman § 1 exposure."
                ),
            )
        if data_age < self.MIN_DATA_AGE_MONTHS:
            return VetoResult.veto(
                reason_code="ANTITRUST-DATA-FRESHNESS",
                owner_required="legal:antitrust_counsel",
                detail=(
                    f"Training data is {data_age} months old. Operator control requires "
                    f"data ≥ {self.MIN_DATA_AGE_MONTHS} months old. "
                    f"U.S. v. RealPage, Inc. et al., M.D.N.C., filed August 23, 2024 — "
                    f"ongoing antitrust litigation, ALLEGED conduct. "
                    f"Consult antitrust counsel re: Sherman § 1 exposure."
                ),
            )
        if coordinated:
            return VetoResult.veto(
                reason_code="ANTITRUST-COORDINATION",
                owner_required="legal:antitrust_counsel",
                detail=(
                    "Recommendation includes coordination signal across owners in the same market. "
                    "U.S. v. RealPage, Inc. et al., M.D.N.C., filed August 23, 2024 — "
                    "ongoing antitrust litigation, ALLEGED conduct re: coordinated pricing. "
                    "Consult antitrust counsel re: Sherman § 1 exposure."
                ),
            )
        return VetoResult.passing()


def main() -> int:
    print("Example 03 — Rent Optimization Sovereign Veto")
    print("=" * 60)

    defcon = DefconController(initial_state=DefconState.NORMAL)
    ledger = AuditLedger()
    veto = SovereignVeto(ledger=ledger).register("rent_optimization", RealPageAntitrustCheck())

    if not defcon.is_allowed(Capability.RENT_OPTIMIZATION):
        print(f"DEFCON state {defcon.state.name} blocks RENT_OPTIMIZATION — aborting.")
        return 1

    cases = [
        (
            "Clean recommendation (state + 14mo data + uncoordinated)",
            RentOptimizationAction(
                action_class="rent_optimization",
                market_geo_granularity="state",
                training_data_age_months=14,
                coordinated_with_other_owners=False,
                recommended_rent=2450.0,
            ),
        ),
        (
            "Submarket granularity (RealPage prohibition)",
            RentOptimizationAction(
                action_class="rent_optimization",
                market_geo_granularity="submarket",
                training_data_age_months=14,
                coordinated_with_other_owners=False,
                recommended_rent=2475.0,
            ),
        ),
        (
            "Data 6 months old (RealPage prohibition)",
            RentOptimizationAction(
                action_class="rent_optimization",
                market_geo_granularity="state",
                training_data_age_months=6,
                coordinated_with_other_owners=False,
                recommended_rent=2480.0,
            ),
        ),
        (
            "Coordinated signal (direct RealPage violation)",
            RentOptimizationAction(
                action_class="rent_optimization",
                market_geo_granularity="state",
                training_data_age_months=14,
                coordinated_with_other_owners=True,
                recommended_rent=2520.0,
            ),
        ),
    ]

    for label, action in cases:
        result = veto.check(action)
        suffix = f" reason: {result.reason_code}" if result.reason_code else ""
        print(f"{label}")
        print(f"  → {result.verdict.value}{suffix}")

    print(f"\nTotal audit entries: {len(ledger.entries)} (every decision recorded)")
    ledger.verify_chain()
    print("Audit chain verified intact ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
