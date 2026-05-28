# ADR-0002 · Sovereign Veto

**Status:** Accepted · inherited from finserv-agent-audit
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

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

## Designating the sovereign

**Who holds veto authority is the operator's organizational design, not this pattern's prescription.** The `AuthorityLevel.MANAGER | DIRECTOR | GC` enum in the reference code is a placeholder; map to your IdP groups (Okta, Azure AD, SAML) before adoption.

A workable model RACI by surface:

| Surface | Primary holder | Backstop | Board notification trigger |
|---|---|---|---|
| Tenant-screening | Chief Compliance Officer + General Counsel (joint) | Chief Risk Officer | Any A3+ veto event |
| Pricing / revenue management | Chief Revenue Officer + General Counsel (joint) | Chief Financial Officer | Audit Committee on any DEFCON-3+ veto event |
| Lease abstraction | General Counsel + lease-administration lead | Chief Operating Officer | Material-clause exception only |
| Tenant PII / cross-jurisdiction | Chief Information Security Officer + General Counsel | Data Protection Officer | Any cross-jurisdiction-untagged flow |
| Marketing audience targeting | Chief Marketing Officer + General Counsel (joint) | Chief Compliance Officer | Any FHA-PROXY veto on a campaign |

The RACI must be documented in writing before adoption. Most enterprise risk committees require the audit-committee or full-board notification path for any A3+ veto event; document the escalation path in the same artifact that designates the sovereign.

## What this does NOT cover

- **Vendor-side veto authority.** When a third-party vendor model is in the decision path (typical for tenant-screening: SafeRent, RentGrow, TransUnion SmartMove), the operator's sovereign veto fires on the operator's *use* of the vendor output — not on the vendor's model itself. See ADR-0011 (Vendor-Output Adapter) and [`docs/vendor-clauses/screening.md`](../../docs/vendor-clauses/screening.md).
- **Adversarial bypass via prompt injection.** Sovereign veto is non-overridable *by the agent*; it does NOT defend against an attacker with privileged access to the IdP impersonating an authorized human bypass owner. Identity-and-access controls are out of scope.
- **Quorum or two-party-control veto.** The reference enum is single-authority. Two-person rule (one CCO + one GC must both approve) is a deployer extension, not a pattern primitive.

## Related

- ADR-0001 (DEFCON) — DEFCON state filters which veto checks are even loaded
- ADR-0003 (Hash-chain Audit) — every veto is recorded immutably
- ADR-0007 (Lease Provenance) — primary domain check for lease abstraction
- ADR-0008 (Fair-Housing Pre-Flight) — primary domain check for tenant screening
- ADR-0009 (Tenant-PII Residency) — primary domain check for cross-jurisdiction data flows
- ADR-0010 (Retention/Privilege/Discovery) — privilege routing on bypass justifications
- ADR-0011 (Vendor-Output Adapter) — for vendor-mediated AI surfaces
