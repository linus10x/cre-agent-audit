"""Worked example — Fair-Housing Pre-Flight on a tenant-screening decision.

This is the runnable companion to ``WORKED_EXAMPLE.md``. It walks the five
steps a regulator (or a risk committee) asks an operator to evidence:

    1. The decision class           — tenant screening, a Fair-Housing surface.
    2. An agent acting              — two screening decisions submitted for execution.
    3. The pre-flight / envelope    — the Fair-Housing Pre-Flight Gate catches the
                                      protected-class-adjacent (voucher-status) case
                                      and the Sovereign Veto stops it.
    4. The audit entry              — every decision (pass AND veto) is hash-chained.
    5. The demotion                 — the recurring veto pattern demotes the system
                                      one DEFCON rung, mechanically pausing the
                                      capability until a human clears it.

Uses the real public API. No mocks. Run:

    python examples/worked_example_fair_housing_preflight.py
"""

from __future__ import annotations

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.governance.defcon import Capability, DefconController, DefconState
from cre_agent_audit.governance.fair_housing_preflight import (
    DisparateImpactMonitor,
    FairHousingPreflightGate,
    ScreeningDecisionAction,
)
from cre_agent_audit.governance.sovereign_veto import SovereignVeto, VetoVerdict
from cre_agent_audit.schemas.screening_decision import (
    Decision,
    ProtectedSurface,
    ScreeningDecision,
)


def screening_decision(
    *,
    decision_id: str,
    features: dict[str, float | str | bool],
    outcome: Decision,
    score: float,
) -> ScreeningDecision:
    return ScreeningDecision(
        decision_id=decision_id,
        applicant_id_anon=f"anon-{decision_id[-3:]}",
        surface=ProtectedSurface.TENANT_SCREENING,
        features=features,
        score=score,
        decision=outcome,
        jurisdiction="TX",
        model_version="screening-agent-v1",
    )


def main() -> int:
    print("Worked example — Fair-Housing Pre-Flight on tenant screening")
    print("=" * 64)

    # --- Step 1: the decision class -------------------------------------- #
    # Tenant screening is a Fair-Housing surface. We stand up the four
    # primitives that gate it: DEFCON state filter, hash-chain ledger,
    # the Fair-Housing Pre-Flight Gate, and the Sovereign Veto dispatcher.
    defcon = DefconController(initial_state=DefconState.NORMAL)
    ledger = AuditLedger()
    monitor = DisparateImpactMonitor(window_days=90)
    gate = FairHousingPreflightGate(disparate_impact_monitor=monitor)
    veto = SovereignVeto(ledger=ledger).register("tenant_screening", gate)

    print("\n[1] Decision class: tenant_screening (a Fair-Housing surface)")
    print(
        f"    DEFCON state: {defcon.state.name} "
        f"(level {defcon.state.level}) — capability allowed: "
        f"{defcon.is_allowed(Capability.TENANT_SCREENING)}"
    )

    # --- Step 2: an agent acts ------------------------------------------- #
    # The screening agent submits two decisions for execution. The first is
    # bounded (credit + rent-to-income only). The second has reached for a
    # housing-voucher feature — a protected-class-adjacent signal and the
    # exact pattern named in the Louis v. SafeRent settlement.
    print("\n[2] Agent submits two screening decisions for execution.")

    bounded = screening_decision(
        decision_id="dec-201",
        features={"credit_score": 0.78, "rent_to_income": 0.30},
        outcome=Decision.APPROVE,
        score=0.78,
    )
    out_of_envelope = screening_decision(
        decision_id="dec-202",
        features={"has_section_8_voucher": True, "credit_score": 0.78},
        outcome=Decision.DENY,
        score=0.40,
    )

    # --- Step 3: the pre-flight / envelope catches the bad case ---------- #
    print("\n[3] Each decision routes through the Sovereign Veto → Pre-Flight Gate.")

    r_bounded = veto.check(
        ScreeningDecisionAction(action_class="tenant_screening", decision=bounded)
    )
    print(f"    dec-201 (credit + rent-to-income only) → {r_bounded.verdict.value}")

    r_out = veto.check(
        ScreeningDecisionAction(action_class="tenant_screening", decision=out_of_envelope)
    )
    print(
        f"    dec-202 (voucher-status feature)        → {r_out.verdict.value} [{r_out.reason_code}]"
    )
    print(f"        owner required to clear: {r_out.owner_required}")
    assert r_bounded.verdict is VetoVerdict.PASS
    assert r_out.verdict is VetoVerdict.VETO
    assert r_out.reason_code == "FHA-VOUCHER"

    # --- Step 4: the audit entry ----------------------------------------- #
    # Both decisions are recorded — the veto as fully as the pass. The chain
    # is hash-linked; tampering with any entry breaks verify_chain().
    print("\n[4] Audit ledger — every decision recorded, veto as fully as pass.")
    print(f"    entries written: {len(ledger.entries)}")
    for entry in ledger.entries:
        verdict = entry.gate_verdicts.get("verdict", "-")
        reason = entry.gate_verdicts.get("reason_code", "-")
        print(
            f"      seq {entry.sequence}: {entry.decision_type} verdict={verdict} reason={reason}"
        )
    ledger.verify_chain()
    print(f"    chain head: {ledger.chain_head()[:16]}…  (verify_chain intact)")

    # --- Step 5: demotion ------------------------------------------------ #
    # A recurring Fair-Housing veto pattern is an operational signal, not a
    # one-off. The operator demotes the system one DEFCON rung. At DEFCON-3
    # RESTRICTED the tenant-screening capability is mechanically paused —
    # the agent cannot run it again until a human re-promotes. The audit
    # ledger keeps writing through every state.
    print("\n[5] Demotion — recurring FHA veto demotes the system one rung.")
    defcon.transition_to(
        DefconState.RESTRICTED,
        actor="compliance:fair_housing_officer",
        reason="recurring FHA-VOUCHER veto pattern on tenant_screening",
    )
    print(f"    DEFCON state: {defcon.state.name} (level {defcon.state.level})")
    print(
        f"    tenant_screening now allowed: "
        f"{defcon.is_allowed(Capability.TENANT_SCREENING)}  (capability paused)"
    )
    print(
        f"    lease_abstraction still allowed: "
        f"{defcon.is_allowed(Capability.LEASE_ABSTRACTION)} "
        f"(co-sign required: {defcon.requires_cosign(Capability.LEASE_ABSTRACTION)})"
    )
    assert defcon.is_allowed(Capability.TENANT_SCREENING) is False

    print("\nDone. The agent reached out of its envelope; the gate caught it, the")
    print("veto stopped it, the ledger recorded it, and the demotion paused the")
    print("capability until a human clears it. Every step is evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
