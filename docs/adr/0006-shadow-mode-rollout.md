# ADR-0006 · Shadow Mode Rollout

**Status:** Accepted · inherited from finserv-agent-audit
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

## Context

A new agent capability — a new lease-clause classifier, an updated tenant-screening model, a revised rent-optimization rule set — must be promoted from "works in the lab" to "live in production" without becoming the cause of the next settled case. The conventional approach is a canary: ship the new capability to a small percentage of traffic. The conventional approach is wrong for regulated decisions because even 1% of regulated traffic is a measurable settled-liability surface.

The correct approach is to run the new capability **in parallel with the current production path on the same input**, observe the divergence between them, and promote only when divergence is understood and within an acceptable band. This is shadow mode.

## Decision

Adopt **Shadow Mode Rollout** as the mandatory promotion path for any agent capability whose decisions cross a sovereign-veto surface (ADR-0002).

```
Production traffic
     │
     ├──► Live agent  ──►  Sovereign Veto  ──►  Audit ledger  ──►  Action executes
     │
     └──► Shadow agent ──► Sovereign Veto  ──►  Audit ledger (shadow) ──►  Silent
```

Both paths run on the same input. Both write to the audit ledger. The live path executes the action; the shadow path's output is recorded but not acted on. A divergence monitor compares the two paths on every decision and produces:

- **Aggregate divergence rate** — % of decisions where the two paths disagreed on outcome
- **Veto divergence rate** — % of decisions where one path vetoed and the other did not
- **Direction of veto divergence** — does the shadow veto *more* than live (conservative) or *less* (aggressive)?
- **Cohort-specific divergence** — disparate impact analysis on the divergence itself (a shadow that vetoes a protected cohort more than the live system is itself a fair-housing concern)

**Promotion gate to live:**

| Decision class | Minimum shadow duration | Maximum divergence |
|---|---|---|
| Informational / classification | 7 days | < 5% on aggregate; no veto direction worse |
| Material lease clauses | 30 days | < 2% on aggregate; no veto direction worse |
| Fair-housing surfaces (tenant screening) | 60 days | < 1% on aggregate; **zero** worse-direction veto on any protected cohort |
| Rent optimization | 90 days | < 1% on aggregate; antitrust check zero-divergence |

The promotion writes an audit-ledger entry recording the shadow-period summary, the operator who promoted, and the reason.

## Consequences

**Positive.** New capabilities never reach a regulated decision surface untested under production traffic. Divergence becomes a structured data signal, not a post-incident postmortem. The audit ledger records the promotion decision and the data behind it.

**Negative.** Cost doubles during shadow periods (two paths running). The cost is real but small relative to the cost of a settled fair-housing case. Mitigation: shadow periods are time-boxed by decision class; only capabilities that pass the gate consume the cost.

**Operational.** A capability stuck in shadow indefinitely is a signal — either the divergence will not converge (the new capability is wrong) or the operator is afraid to promote (the program is in a stuck state). The monitor agent (per ARCHITECTURE.md) flags shadow-mode time-in-state as a board-level metric.

## Regulatory anchor

- SR 11-7 (Federal Reserve model-risk-management guidance) — analog for property-domain models
- NIST AI RMF Measure function (MEASURE 2.1 — testing under representative conditions)

## CRE-specific notes

Tenant-screening shadow periods are 60 days because a single fair-housing decision cycle (application → decision → tenancy outcome) spans 30+ days. Two cycles are required to observe whether the new capability produces outcomes consistent with the prior generation.

## Related

- ADR-0001 (DEFCON) — DEFCON-3 forces every new capability to shadow indefinitely
- ADR-0004 (Autonomy Ladder) — shadow-mode duration is a required input for A2 → A3 promotion
- ADR-0008 (Fair-Housing Pre-Flight) — zero-worse-direction veto rule applies most stringently here
