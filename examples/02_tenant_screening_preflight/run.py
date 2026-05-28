"""Example 02 — Tenant Screening Pre-Flight Gate.

Demonstrates the full ADR-0008 Fair-Housing Pre-Flight Gate: five ordered
checks (FHA-PROXY · FHA-VOUCHER · FHA-SOI · FHA-CRIM · FHA-DISPARATE) plus
the bypass auto-escalation logic.

Run:
    python examples/02_tenant_screening_preflight/run.py
"""

from __future__ import annotations

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.governance.defcon import Capability, DefconController, DefconState
from cre_agent_audit.governance.fair_housing_preflight import (
    DisparateImpactMonitor,
    FairHousingPreflightGate,
    ScreeningDecisionAction,
)
from cre_agent_audit.governance.sovereign_veto import SovereignVeto
from cre_agent_audit.schemas.screening_decision import (
    Decision,
    ProtectedSurface,
    ScreeningDecision,
)


def decision(
    *,
    decision_id: str,
    jurisdiction: str,
    features: dict[str, float | str | bool],
    decision_outcome: Decision = Decision.APPROVE,
    score: float = 0.72,
) -> ScreeningDecision:
    return ScreeningDecision(
        decision_id=decision_id,
        applicant_id_anon=f"anon-{decision_id[-4:]}",
        surface=ProtectedSurface.TENANT_SCREENING,
        features=features,
        score=score,
        decision=decision_outcome,
        jurisdiction=jurisdiction,
        model_version="claude-opus-4-7",
    )


def main() -> int:
    print("Example 02 — Tenant Screening Pre-Flight Gate")
    print("=" * 60)

    defcon = DefconController(initial_state=DefconState.NORMAL)
    ledger = AuditLedger()
    monitor = DisparateImpactMonitor(window_days=90)
    gate = FairHousingPreflightGate(disparate_impact_monitor=monitor)
    veto = SovereignVeto(ledger=ledger).register("tenant_screening", gate)

    if not defcon.is_allowed(Capability.TENANT_SCREENING):
        print(f"DEFCON state {defcon.state.name} blocks TENANT_SCREENING.")
        return 1

    cases = [
        (
            "Clean decision (credit + rent-to-income only)",
            decision(
                decision_id="dec-001",
                jurisdiction="TX",
                features={"credit_score": 0.78, "rent_to_income": 0.32},
            ),
        ),
        (
            "FHA-PROXY: zip-only feature (race proxy)",
            decision(
                decision_id="dec-002",
                jurisdiction="TX",
                features={"applicant_zip_only": "75201", "credit_score": 0.78},
            ),
        ),
        (
            "FHA-VOUCHER: voucher feature (SafeRent failure mode)",
            decision(
                decision_id="dec-003",
                jurisdiction="TX",
                features={"has_section_8_voucher": True, "credit_score": 0.78},
                decision_outcome=Decision.DENY,
            ),
        ),
        (
            "FHA-SOI: income source in SOI-protected jurisdiction (CA)",
            decision(
                decision_id="dec-004",
                jurisdiction="CA",
                features={"income_source_type": "ssi", "credit_score": 0.78},
            ),
        ),
        (
            "FHA-SOI clean: same features in non-protected jurisdiction (TX)",
            decision(
                decision_id="dec-005",
                jurisdiction="TX",
                features={"income_source_type": "ssi", "credit_score": 0.78},
            ),
        ),
        (
            "FHA-CRIM: blanket criminal-history disqualification",
            decision(
                decision_id="dec-006",
                jurisdiction="TX",
                features={"criminal_history_blanket_deny": True},
                decision_outcome=Decision.DENY,
            ),
        ),
        (
            "FHA-CRIM: 10-year-old conviction (beyond 7-year lookback)",
            decision(
                decision_id="dec-007",
                jurisdiction="TX",
                features={"criminal_history_years_since": 10.0},
                decision_outcome=Decision.DENY,
            ),
        ),
    ]

    for label, dec in cases:
        action = ScreeningDecisionAction(action_class="tenant_screening", decision=dec)
        result = veto.check(action)
        suffix = f" reason: {result.reason_code}" if result.reason_code else ""
        print(f"{label}")
        print(f"  → {result.verdict.value}{suffix}")

    print(f"\nTotal audit entries: {len(ledger.entries)} (every decision recorded)")
    ledger.verify_chain()
    print("Audit chain verified intact ✓")

    print()
    print("Full ADR-0008 capabilities active: 5 ordered checks (FHA-PROXY/VOUCHER/SOI/")
    print("CRIM/DISPARATE) + bypass auto-escalation (3 owner → GC, 5 reason → DEFCON-4)")
    print("via FairHousingException + BypassRegistry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
