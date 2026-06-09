# The Autonomy Ladder — A0 → A4, and where the nine patterns sit

`cre-agent-audit` is one of six co-equal regulated-vertical libraries in the
[**Autonomy Ladder family**](https://github.com/linus10x/autonomy-ladder-libraries). The
framework itself — the discipline of *Regulated-Operations AI Governance* — lives at
[autonomy-ladder.io](https://autonomy-ladder.io). This file maps the nine governance
patterns in this repo onto the ladder, so you can see which rung each one enforces.

## The ladder

The Autonomy Ladder is a deployment-authority scale, not a capability scale. It answers
one question: *how much authority does the agent have to act without a human in the loop,
and what must be true before it earns the next rung?* Every rung is **demotable** — a
control that fires, a monitor that diverges, or an operator who pulls the lever sends the
system back down. No rung is permanent.

| Rung | Name | What the agent may do | Human posture |
|---|---|---|---|
| **A0** | Informational | Read and summarize only; no writes | Human does everything |
| **A1** | Assisted | Propose a write; every write needs approval before commit | Human approves each one |
| **A2** | Delegated | Write **inside a hard pre-defined envelope**; everything out of envelope escalates | Human reviews a sample + all exceptions |
| **A3** | Supervised autonomous | Write without per-decision approval | Human supervises **by exception** |
| **A4** | Production autonomous | Full autonomy within the envelope | Human monitors; circuit-breakers enforce |

The regulator-visible boundary is **A2 → A3**: promotion requires the sovereign-veto layer
load-tested under representative traffic, the audit ledger running ≥ 90 days, shadow mode
running ≥ 30 days with no material divergence, and a circuit-breaker tested at least
quarterly. That gate is codified in
[`autonomy_ladder.check_a2_to_a3_promotion`](src/cre_agent_audit/governance/autonomy_ladder.py).

## The nine patterns, mapped to the ladder

| # | Pattern (module) | A0 | A1 | A2 | A3 | A4 | What it enforces on the ladder |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| 1 | **DEFCON** (`defcon`) | ● | ● | ● | ● | ● | Per-state capability allowlist — gates *which rung any capability may operate at right now*; a DEFCON demotion mechanically pauses capabilities regardless of their nominal rung |
| 2 | **Sovereign Veto** (`sovereign_veto`) | | ● | ● | ● | ● | The non-overridable boundary that makes A2+ safe — a separate-authority check the agent cannot switch off; bypass needs a named owner + regulatory basis, logged |
| 3 | **Audit Chain** (`audit_chain`) | ● | ● | ● | ● | ● | The hash-chained evidence record every rung above A0 depends on; the A2→A3 gate requires ≥ 90 days of it |
| 4 | **Autonomy Ladder** (`autonomy_ladder`) | ● | ● | ● | ● | ● | The ladder itself — tier semantics (`can_write`, `requires_envelope`, `requires_sampled_review`, `requires_human_exception_supervision`) + the A2→A3 promotion gate |
| 5 | **Regulation Loader** (`regulation_loader`) | ● | ● | ● | ● | ● | Binds each pattern to its regulatory anchor; governs all the others, at every rung |
| 6 | **Shadow Mode** (`shadow_mode`) | | | ● | ● | | The promotion mechanism into A3 — the agent runs in parallel without committing; ≥ 30 days with no material divergence is a precondition for A2 → A3 |
| 7 | **Lease Provenance** (`lease_provenance`) | ● | ● | ● | ● | ● | CRE-specific — clause-level source/confidence provenance so an A2+ extraction is defensible in discovery |
| 8 | **Fair-Housing Pre-Flight** (`fair_housing_preflight`) | | ● | ● | ● | ● | CRE-specific — the A2 envelope boundary for tenant-screening; out-of-envelope (protected-class-adjacent) decisions are vetoed and escalated |
| 9 | **Tenant PII Residency** (`tenant_pii_residency`) | ● | ● | ● | ● | ● | CRE-specific — cross-jurisdiction PII flow is tagged or blocked at every rung |

● = the pattern is active / load-bearing at that rung.

### How to read the map

- **A0–A1** lean on the evidence and binding patterns (audit chain, regulation loader,
  provenance, residency). There is little autonomy to constrain yet, but the record starts
  on day one.
- **A2** is where the envelope patterns earn their keep — the **Fair-Housing Pre-Flight
  Gate** and the **Sovereign Veto** define and enforce the hard boundary, and the audit
  chain records every pass and every veto.
- **A2 → A3** is the regulator-visible promotion. **Shadow Mode** is the proving ground;
  the **Autonomy Ladder** promotion gate is the check; the **audit chain** supplies the
  ≥ 90-day evidence.
- **DEFCON** sits across all of it: a demotion pauses capabilities mechanically, so a
  recurring veto pattern can pull a nominally-A3 capability back to "paused" without
  rewriting any agent.

For the end-to-end walkthrough of one decision class moving down the ladder — agent acts →
pre-flight catches it → audit entry → demotion — see [`WORKED_EXAMPLE.md`](WORKED_EXAMPLE.md).

## The family

| Vertical | Library |
|---|---|
| Cross-vertical financial services | [`finserv-agent-audit`](https://github.com/linus10x/finserv-agent-audit) |
| Banking | [`banking-agent-audit`](https://github.com/linus10x/banking-agent-audit) |
| Payments | [`payments-agent-audit`](https://github.com/linus10x/payments-agent-audit) |
| Health-insurance payer | [`payer-agent-audit`](https://github.com/linus10x/payer-agent-audit) |
| SEC-registered investment advisers | [`private-capital-agent-audit`](https://github.com/linus10x/private-capital-agent-audit) |
| Commercial real estate | **[`cre-agent-audit`](https://github.com/linus10x/cre-agent-audit)** (this repo) |

One framework, six co-equal regulated verticals, one author. Framework + whitepaper:
[autonomy-ladder.io](https://autonomy-ladder.io). Family index:
[autonomy-ladder-libraries](https://github.com/linus10x/autonomy-ladder-libraries).
