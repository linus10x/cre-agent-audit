# ADR-0002 · Sovereign Veto

**Status:** Accepted · inherited from finserv-agent-audit
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

## Context

An AI agent operating inside a CRE workflow will, given enough time and enough decisions, propose an action it does not have authority to take. The failure mode is not random — it is concentrated in decisions where the agent's training distribution misaligns with regulatory or fiduciary constraint surfaces. Examples in CRE: a tenant-screening agent inferring on a proxy variable for protected class; a rent-pricing agent recommending coordinated pricing across competing properties; a lease-abstraction agent confidently fabricating a clause from a partial document scan.

The standard fix is "human in the loop." At CRE-portfolio scale (tens of thousands of decisions per quarter at a mid-size operator), human review is theatre, a bottleneck, or both.

The agent itself cannot be the arbiter of its own authority. The check must come from outside the agent and must be non-overridable by the agent.

## Decision

Implement a **Sovereign Veto** — a non-overridable check that runs at the agent boundary before any action that crosses a constraint surface the agent does not have authority to clear.

Properties:

1. **Non-overridable by the agent.** No prompt, no chain-of-thought, no reasoning step can bypass the veto. The veto sits outside the agent's reachable code path.
2. **Bypass-able by a human only with logged exception.** A human can override the veto for a single decision, but the override generates a logged exception that carries a named owner, a regulatory basis, and a timestamp. The exception is durable; it cannot be edited or deleted.
3. **Constraint-surface-specific.** The veto runs different checks for different action classes. Tenant screening runs the Fair-Housing Pre-Flight Gate (ADR-0008). Lease abstraction runs the Provenance Chain check (ADR-0007). Rent optimization runs an antitrust-coordination check.
4. **Returns a structured reason code.** Vetoes are not "no." Vetoes are `FHA-VOUCHER`, `PROV-INCOMPLETE-MATERIAL`, `RESIDENCY-CROSS-JURISDICTION-UNTAGGED`, etc. The code is logged. The code is the regulator-readable explanation.

```python
class SovereignVeto:
    def check(self, action: AgentAction, context: AuditContext) -> VetoResult:
        # Returns VetoResult.PASS, or VetoResult.VETO(reason_code, owner_required)
        ...
```

A vetoed action is written to the audit ledger (ADR-0003) with full context. The agent receives the veto and either proposes a corrected action or escalates to a human in the workflow.

## Consequences

**Positive.** Regulator-defensible architecture. Every decision the agent did not take is as recoverable as every decision it did. The bypass log becomes the board-level governance artifact ("show me the exception log") — a thing regulators, LPs, and chief risk officers ask for by name.

**Negative.** Decisions take longer. The compose-order placement means the veto runs only if upstream checks passed, which keeps the cost off the hot path for unsafe-state cases. Calibration risk: an over-tight veto produces a flood of bypass exceptions; an under-tight veto produces settled liability. Calibration is the work of the program, not the framework.

**Architectural.** The veto layer must be outside the agent's process or, at minimum, outside the agent's reasoning context. In this reference repo it is a separate Python module the agent code cannot mutate. In a production deployment it is a separate service.

## Regulatory anchor

- Three-lines-of-defense model (first line: business · second line: risk and compliance · third line: internal audit). The veto is a second-line control implemented at runtime.
- NIST AI RMF Manage function (MANAGE 2.3 — risk decisions and tradeoffs documented)

## CRE-specific notes

CRE governance has two veto-rich surfaces: fair-housing (ADR-0008) and lease-clause integrity (ADR-0007). A third (antitrust coordination) is implied by the RealPage settlement and implemented as a configurable pattern in `src/governance/sovereign_veto.py` with rules surfaced in `config/compliance_rules.yaml`.

## Related

- ADR-0001 (DEFCON) — DEFCON state filters which veto checks are even loaded
- ADR-0003 (Hash-chain Audit) — every veto is recorded immutably
- ADR-0007 (Lease Provenance) — primary domain check for lease abstraction
- ADR-0008 (Fair-Housing Pre-Flight) — primary domain check for tenant screening
- ADR-0009 (Tenant-PII Residency) — primary domain check for cross-jurisdiction data flows
