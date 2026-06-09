# Worked example — Fair-Housing Pre-Flight on a tenant-screening decision

This is the one example to read first. It walks a single decision class — **tenant
screening** — from an agent acting, through the Fair-Housing Pre-Flight Gate catching
an out-of-envelope case, to the audit entry, to the demotion that pauses the capability
until a human clears it.

Tenant screening is the canonical Fair-Housing surface, and it is where the recent
enforcement record is sharpest: the *Louis v. SafeRent Solutions* class settlement
(D. Mass., approximately $2.275M, November 20, 2024) named a screening model that scored
voucher-holding applicants below threshold with no documented reason, and carried a
five-year score-use injunction. This example shows the rail that would have caught that
pattern at decision time.

Everything below uses the **real public API** — no mocks, no stubs. The runnable companion
is [`examples/worked_example_fair_housing_preflight.py`](examples/worked_example_fair_housing_preflight.py).

```bash
pip install -e .
python examples/worked_example_fair_housing_preflight.py
```

---

## The five steps

### 1 — The decision class

Tenant screening is a Fair-Housing surface. Four primitives gate it: the **DEFCON** state
filter (is the capability even open right now?), the hash-chain **Audit Ledger**, the
**Fair-Housing Pre-Flight Gate**, and the **Sovereign Veto** dispatcher that the gate
registers under.

```python
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

defcon = DefconController(initial_state=DefconState.NORMAL)
ledger = AuditLedger()
gate = FairHousingPreflightGate(disparate_impact_monitor=DisparateImpactMonitor(window_days=90))
veto = SovereignVeto(ledger=ledger).register("tenant_screening", gate)
```

At `DEFCON-5 NORMAL`, `defcon.is_allowed(Capability.TENANT_SCREENING)` is `True` — the
capability is open.

### 2 — An agent acts

The screening agent submits two decisions for execution. The first is bounded — it reasons
only over credit and rent-to-income. The second has reached for a **housing-voucher**
feature: a source-of-income / protected-class-adjacent signal, and the exact pattern the
SafeRent matter named.

```python
bounded = ScreeningDecision(
    decision_id="dec-201", applicant_id_anon="anon-201",
    surface=ProtectedSurface.TENANT_SCREENING,
    features={"credit_score": 0.78, "rent_to_income": 0.30},
    score=0.78, decision=Decision.APPROVE,
    jurisdiction="TX", model_version="screening-agent-v1",
)
out_of_envelope = ScreeningDecision(
    decision_id="dec-202", applicant_id_anon="anon-202",
    surface=ProtectedSurface.TENANT_SCREENING,
    features={"has_section_8_voucher": True, "credit_score": 0.78},
    score=0.40, decision=Decision.DENY,
    jurisdiction="TX", model_version="screening-agent-v1",
)
```

### 3 — The pre-flight catches the out-of-envelope case

Each decision routes through the Sovereign Veto, which dispatches to the registered
Fair-Housing Pre-Flight Gate. The bounded decision passes. The voucher-status decision is
**vetoed** with a named, regulator-readable reason code — `FHA-VOUCHER` — and a named owner
who alone could authorize a logged bypass.

```python
r_bounded = veto.check(ScreeningDecisionAction(action_class="tenant_screening", decision=bounded))
# → PASS

r_out = veto.check(ScreeningDecisionAction(action_class="tenant_screening", decision=out_of_envelope))
# → VETO  reason_code="FHA-VOUCHER"  owner_required="compliance:fair_housing_officer"
```

A veto is not "no." It is a named reason code plus the owner who would have to put their
name on a bypass. That is the artifact a regulator asks for.

### 4 — The audit entry

Both decisions are written to the hash-chained ledger — the veto recorded as fully as the
pass. Each entry carries the SHA-256 of the previous one, so altering any past entry breaks
`verify_chain()` at that point and every entry after it.

```python
for entry in ledger.entries:
    print(entry.sequence, entry.decision_type, entry.gate_verdicts)
ledger.verify_chain()        # raises AuditChainTamperError if any link is broken
ledger.chain_head()          # the digest you anchor to an external witness register
```

### 5 — The demotion

A recurring Fair-Housing veto is an operational signal, not a one-off. The operator demotes
the system one DEFCON rung. At `DEFCON-3 RESTRICTED` the tenant-screening capability is
**mechanically paused** — the agent cannot run it again until a human re-promotes. Lease
abstraction continues, but now requires a co-sign. The audit ledger keeps writing through
every state.

```python
defcon.transition_to(
    DefconState.RESTRICTED,
    actor="compliance:fair_housing_officer",
    reason="recurring FHA-VOUCHER veto pattern on tenant_screening",
)
defcon.is_allowed(Capability.TENANT_SCREENING)   # → False  (paused)
defcon.is_allowed(Capability.LEASE_ABSTRACTION)  # → True
defcon.requires_cosign(Capability.LEASE_ABSTRACTION)  # → True
```

---

## Output

Running the companion script end-to-end produces (the chain-head digest varies per run
because entries are stamped with the local clock):

```
Worked example — Fair-Housing Pre-Flight on tenant screening
================================================================

[1] Decision class: tenant_screening (a Fair-Housing surface)
    DEFCON state: NORMAL (level 5) — capability allowed: True

[2] Agent submits two screening decisions for execution.

[3] Each decision routes through the Sovereign Veto → Pre-Flight Gate.
    dec-201 (credit + rent-to-income only) → PASS
    dec-202 (voucher-status feature)        → VETO [FHA-VOUCHER]
        owner required to clear: compliance:fair_housing_officer

[4] Audit ledger — every decision recorded, veto as fully as pass.
    entries written: 2
      seq 0: sovereign_veto verdict=PASS reason=-
      seq 1: sovereign_veto verdict=VETO reason=FHA-VOUCHER
    chain head: 6d3c266f6f4e33b7…  (verify_chain intact)

[5] Demotion — recurring FHA veto demotes the system one rung.
    DEFCON state: RESTRICTED (level 3)
    tenant_screening now allowed: False  (capability paused)
    lease_abstraction still allowed: True (co-sign required: True)

Done. The agent reached out of its envelope; the gate caught it, the
veto stopped it, the ledger recorded it, and the demotion paused the
capability until a human clears it. Every step is evidence.
```

---

## What this maps to

| Step | Pattern | A0→A4 rung it enforces |
|---|---|---|
| 1 — decision class open? | DEFCON state machine | per-state capability allowlist (any rung) |
| 2 — agent acts | Autonomy Ladder | A2 delegated within a hard envelope |
| 3 — pre-flight catches it | Fair-Housing Pre-Flight Gate + Sovereign Veto | A2 envelope boundary + non-overridable veto |
| 4 — audit entry | Hash-chained Audit Ledger | the evidence every rung above A1 requires |
| 5 — demotion | DEFCON transition | mechanical demotion — no rung is permanent |

The full A0→A4 mapping for all nine patterns is in [`AUTONOMY_LADDER.md`](AUTONOMY_LADDER.md).
The framework and whitepaper live at [autonomy-ladder.io](https://autonomy-ladder.io).
