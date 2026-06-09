"""Example 04 — RealPage Antitrust Replay (Standalone Entrypoint).

Operator-side governance signals relevant to U.S. v. RealPage, Inc. et al.,
filed August 23, 2024 (DOJ + 8 state AGs; Sherman Act §§ 1 AND 2). Current
posture: DOJ filed a proposed consent judgment with RealPage on Nov 24, 2025
(pending Tunney Act approval); co-defendant final judgments entered (e.g.,
Greystar, Mar 2, 2026). Resolved without admission of liability — allegations
NEVER adjudicated, NOT "ongoing litigation."

Patterns engaged:
- ADR-0001: DEFCON State Machine (RENT_OPTIMIZATION capability check)
- ADR-0002: Sovereign Veto (ANTITRUST-COORDINATION + ANTITRUST-GEO-GRANULARITY)
- ADR-0003: Hash-Chained Audit Ledger (every decision recorded)
- ADR-0011: VendorScoreGate (cohort-drift signal across 50 synthetic decisions)

Input: 50 synthetic rental pricing decisions across three DFW submarkets
(Uptown Dallas · Plano · Fort Worth). No real data. random.seed(42).

Not legal advice. Patterns are software; regulatory citations are reference
mappings. Consult antitrust counsel re: Sherman Act §§ 1 and 2 exposure.

For the full 6-artifact evidence bundle run:
    cre-replay run 03_realpage_consent_judgment

Run:
    python examples/04_realpage_antitrust_replay/run.py
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.governance.defcon import Capability, DefconController, DefconState
from cre_agent_audit.governance.sovereign_veto import (
    AgentAction,
    ConstraintCheck,
    SovereignVeto,
    VetoResult,
)
from cre_agent_audit.governance.vendor_score_gate import InMemoryVendorScoreGate


@dataclass(frozen=True)
class PricingDecision(AgentAction):
    market_geo_granularity: str  # 'state' | 'metro' | 'submarket' | 'building'
    training_data_age_months: int
    coordinated_with_other_owners: bool
    recommended_rent: float
    vendor_score: float


class RealPageAntitrustCheck(ConstraintCheck):
    """Pre-flight constraint check modeling operator-side controls relevant to
    U.S. v. RealPage, Inc. et al., filed August 23, 2024 (DOJ + 8 state AGs;
    Sherman Act §§ 1 and 2) — resolved by proposed consent judgment
    (DOJ filed Nov 24, 2025, pending Tunney Act approval), never adjudicated."""

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
                    f"U.S. v. RealPage, Inc. et al., filed August 23, 2024 (Sherman Act §§ 1 "
                    f"and 2) — ALLEGED conduct, resolved by proposed consent judgment, never "
                    f"adjudicated. Operator control "
                    f"restricts recommendations to {self.MAX_GRANULARITY!r}-level granularity. "
                    f"Consult antitrust counsel re: Sherman Act §§ 1 and 2 exposure."
                ),
            )
        if data_age < self.MIN_DATA_AGE_MONTHS:
            return VetoResult.veto(
                reason_code="ANTITRUST-DATA-FRESHNESS",
                owner_required="legal:antitrust_counsel",
                detail=(
                    f"Training data is {data_age} months old. Operator control requires "
                    f"data ≥ {self.MIN_DATA_AGE_MONTHS} months old. "
                    f"U.S. v. RealPage, Inc. et al., filed August 23, 2024 (Sherman Act §§ 1 "
                    f"and 2) — ALLEGED conduct, resolved by proposed consent judgment, never "
                    f"adjudicated. "
                    f"Consult antitrust counsel re: Sherman Act §§ 1 and 2 exposure."
                ),
            )
        if coordinated:
            return VetoResult.veto(
                reason_code="ANTITRUST-COORDINATION",
                owner_required="legal:antitrust_counsel",
                detail=(
                    "Recommendation includes coordination signal across owners in the same market. "
                    "U.S. v. RealPage, Inc. et al., filed August 23, 2024 (Sherman Act §§ 1 and 2) "
                    "— ALLEGED conduct re: coordinated pricing, resolved by proposed consent "
                    "judgment, never adjudicated. "
                    "Consult antitrust counsel re: Sherman Act §§ 1 and 2 exposure."
                ),
            )
        return VetoResult.passing()


_SUBMARKETS = ["Uptown Dallas", "Plano", "Fort Worth"]
_SEED = 42


def _make_decisions() -> list[PricingDecision]:
    rng = random.Random(_SEED)
    decisions = []
    for i in range(50):
        # Inject two specific violations at known indices
        coordinated = i == 3
        granularity = "submarket" if i == 17 else "state"
        decisions.append(
            PricingDecision(
                action_class="rent_optimization",
                market_geo_granularity=granularity,
                training_data_age_months=rng.randint(12, 24),
                coordinated_with_other_owners=coordinated,
                recommended_rent=round(2200.0 + rng.uniform(-200, 300), 2),
                vendor_score=round(0.75 + (i % 5) * 0.01, 3),
            )
        )
    return decisions


def main() -> int:
    # DEFCON check
    defcon = DefconController(initial_state=DefconState.NORMAL)
    allowed = defcon.is_allowed(Capability.RENT_OPTIMIZATION)
    status = "ALLOWED" if allowed else "BLOCKED"
    print(
        f"[DEFCON] RENT_OPTIMIZATION capability: {status} "
        f"(DEFCON-{defcon.state.value} {defcon.state.name})"
    )
    if not allowed:
        print(f"  DEFCON-{defcon.state.value} blocks RENT_OPTIMIZATION — aborting.")
        return 1

    # Ledgers — keep sovereign veto and vendor gate on separate chains
    ledger = AuditLedger()
    vendor_ledger = AuditLedger()

    veto = SovereignVeto(ledger=ledger).register("rent_optimization", RealPageAntitrustCheck())
    vendor_gate = InMemoryVendorScoreGate(ledger=vendor_ledger, raise_on_drift=False)

    decisions = _make_decisions()
    veto_count = 0
    scores: list[float] = []

    for i, decision in enumerate(decisions):
        result = veto.check(decision)
        if result.reason_code:
            veto_count += 1
            label = {
                "ANTITRUST-COORDINATION": "coordinated signal detected",
                "ANTITRUST-GEO-GRANULARITY": "cross-submarket granularity",
                "ANTITRUST-DATA-FRESHNESS": "data-freshness violation",
            }.get(result.reason_code, result.reason_code)
            print(f"[VETO] Decision {i:02d}: {result.reason_code} — {label}")

        event = vendor_gate.emit(
            vendor_id="vendor-pricing-realpage",
            input_hash=f"synthetic-decision-{i:04d}",
            score=decision.vendor_score,
            model_version="v-alleged-clustering-mark",
        )
        scores.append(event.score)

    # Cohort clustering signal
    score_std = statistics.stdev(scores) if len(scores) > 1 else 0.0
    clustering = "HIGH" if score_std < 0.05 else "MEDIUM" if score_std < 0.15 else "LOW"
    veto_pct = veto_count / len(decisions) * 100
    print(
        f"[VENDOR] Cohort-drift signal: {len(decisions)} decisions, "
        f"{veto_count} vetoed ({veto_pct:.1f}%). Score clustering: {clustering}"
    )

    # Audit chain
    ledger.verify_chain()
    chain_sha = ledger.chain_head()[:8]
    print(f"[LEDGER] {len(ledger.entries)} entries. Chain verified intact. SHA-256: {chain_sha}...")

    print("---")
    print(
        f"{len(decisions)} decisions logged. {veto_count} coordination signals flagged. "
        "Audit chain intact."
    )
    print("Full 6-artifact evidence bundle: cre-replay run 03_realpage_consent_judgment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
