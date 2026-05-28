# ADR-0001 · DEFCON State Machine

**Status:** Accepted · inherited from finserv-agent-audit
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

A CRE-AI program touches workflows where the cost of an unsafe operating state — degraded model availability, unverified deployment, regulator inquiry in flight, data-quality incident — is asymmetric. A single hour of agent autonomy during a known-unsafe condition can produce hundreds of decisions that later require manual unwind. Per-decision risk checks are necessary but insufficient: some risk conditions are system-wide and need a system-wide brake.

The conventional "feature flag" approach is too granular and too distributed. A flag-per-capability creates a combinatorial blast radius when the operator needs to roll back fast.

## Decision

Adopt a **DEFCON state machine** with discrete named states, named transition conditions, and a per-state allowlist of agent capabilities.

```
DEFCON-5 (NORMAL)      All capabilities active. Standard audit.
DEFCON-4 (HEIGHTENED)  Material-clause writes require human co-sign. Other capabilities active.
DEFCON-3 (RESTRICTED)  Tenant-screening + rent-optimization paused. Read-only mode for those.
                       Lease abstraction continues with mandatory reviewer signature.
DEFCON-2 (CONTAINMENT) All writes paused. Agents read-only. Audit ledger continues writing.
DEFCON-1 (SHUTDOWN)    Agents offline. Audit ledger continues writing. Operator-only mode.
```

State is global, owned by a single `DefconController` actor. Transitions are triggered by:

- **Operator command** — explicit operator escalation or de-escalation (logged)
- **Monitor alerts** — anomaly thresholds breached on the audit ledger (e.g., veto rate exceeds calibrated band)
- **External signal** — regulator notice, named third-party-vendor incident, court order
- **Scheduled** — pre-announced regulatory window, e.g., quarterly audit lockdown

Every state transition writes an immutable entry to the audit ledger (ADR-0003) with reason, actor, prior state, new state, and an estimated duration.

## Consequences

**Positive.** A single switch can stop the bleed. Operators have a calibrated, well-documented escalation ladder rather than ad-hoc flag flipping. Regulators see a structured response to incidents. The DEFCON state is the first check in the compose order (see ARCHITECTURE.md), so unsafe-state actions are killed before downstream cost.

**Negative.** Adds latency to every agent action (one state read). Mitigated by caching state in-process with a 1-second TTL and a force-invalidate hook on transition events.

**Operational.** DEFCON-3 and below are not normal operating modes. Time-in-state metrics are reported to the board. A program that spends more than 5% of operating hours below DEFCON-5 is showing a structural issue, not a tactical one.

## Regulatory anchor

- Operational-risk frameworks (Basel III analog for property operations)
- NIST AI RMF Govern function (GOVERN 1.6 — incident response)
- Internal-controls best practice

## CRE-specific notes

CRE workflows have predictable seasonal heightened-risk windows (lease renewal season at major property classes, tax-year reporting, rent-roll audit cycles). The DEFCON ladder includes scheduled-elevation hooks for these windows by default.

## Related

- ADR-0002 (Sovereign Veto) — runs after DEFCON check
- ADR-0003 (Hash-chain Audit) — records every transition
- ADR-0006 (Shadow Mode) — DEFCON-3 forces new capabilities to shadow indefinitely
