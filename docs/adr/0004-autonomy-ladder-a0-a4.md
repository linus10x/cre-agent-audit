# ADR-0004 · Autonomy Ladder™ A0 → A4

**Status:** Accepted · inherited from finserv-agent-audit
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

Three case-of-record regulatory matters — *In re Trans Union Rental Screening Solutions* (Oct 2023, $15M FTC/CFPB), *Louis v. SafeRent Solutions* (D. Mass., Nov 2024, ~$2.275M class settlement), *U.S. v. RealPage* (M.D.N.C., Aug 2024, ongoing Sherman § 1 litigation) — all involved AI operating above the autonomy level its **assurance case** (Kelly & Weaver 2004; Bloomfield et al. 2021) could defend. The pattern this ADR describes is how to size autonomy to the evidence stack a regulator, an opposing counsel, or an audit committee would actually accept.

"Is this AI program ready for production?" is the wrong question. The question is "at what level of autonomy is this program ready, and what is the next promotable tier?" A program at full autonomy on a low-risk read-only task is shipping. A program at full autonomy on a sovereign-veto-required task is a settlement waiting to happen. A program at human-in-loop on every decision at portfolio scale is unscalable and underperforming the unit economics that justified the AI investment in the first place.

The conventional answer is a binary "human-in-loop" / "fully autonomous." The binary is wrong. Regulators (EU AI Act Article 14, NIST AI RMF Govern), institutional investors (LP letters specifying explainability requirements), and internal risk committees all distinguish between tiers of autonomy with different controls at each tier.

## Decision

Adopt the **Autonomy Ladder™ A0 → A4**, five named maturity tiers with a documented compose pattern at each tier and an explicit promotion gate between tiers.

```
A0 · INFORMATIONAL
   Agent reads. Agent recommends. No write authority.
   Use case: lease-clause flagging for human reviewer.

A1 · ASSISTED
   Agent reads. Agent drafts. Human approves every write.
   Use case: lease-abstraction drafts presented for reviewer signature.

A2 · DELEGATED
   Agent reads and writes for low-risk decisions inside a hard envelope.
   Human approves a sampled subset and all out-of-envelope decisions.
   Use case: routine maintenance request routing, rent-comp ingestion.

   ─── A2 → A3 promotion is the regulator-visible boundary. ───
   ─── Runtime circuit-breaker MUST exist AND be tested.    ───

A3 · SUPERVISED AUTONOMOUS
   Agent reads and writes for in-scope decision class autonomously.
   Sovereign-veto layer is non-overridable. Audit ledger is live.
   Human supervises by exception, not by approval.
   Use case: tenant-screening decisions inside the Fair-Housing gate.

A4 · PRODUCTION AUTONOMOUS
   A3 plus inter-agent orchestration, monitor-led promotion of new
   capabilities, and operator-validated escalation paths.
   Use case: portfolio-wide rent-optimization with sovereign veto on
   antitrust coordination.
```

The A2 → A3 promotion gate is the regulator-visible boundary. Promotion requires:

1. **Sovereign-veto layer (ADR-0002) live and load-tested** under representative traffic.
2. **Audit ledger (ADR-0003) running for ≥ 90 days** with a regulator-replayable subset.
3. **Shadow Mode (ADR-0006) ran for ≥ 30 days** with no material divergence between shadow and production.
4. **Circuit-breaker tested** at least quarterly, with the test recorded on the audit ledger.

The promotion gate is the work, not the framework.

## Consequences

**Positive.** Programs have a documented promotion path with regulator-defensible criteria. LP letters can specify "operating at A3 with audited circuit-breaker" — a more meaningful claim than "AI-enabled." Board committees have a tier to point to when explaining their AI program.

**Negative.** Adds vocabulary the organization must learn. Mitigated by the fact that the alternative — implicit, unstated, inconsistent autonomy levels per workflow — costs more in regulatory exposure than the vocabulary investment costs in training.

## Regulatory anchor

- EU AI Act Article 14 (human oversight requirements scale by risk class)
- NIST AI RMF Manage function (MANAGE 2.3 — risk decisions documented)
- CO AI Act SB 26-189 (impact assessments for consequential decisions — A2 → A3 promotion is the audit-trigger event)

## CRE-specific notes

Lease abstraction is naturally A1-A2 because the material clauses warrant reviewer signatures. Tenant screening can run A3 only with the Fair-Housing Pre-Flight Gate (ADR-0008) as the sovereign veto. Rent optimization should not exceed A3 in 2026 because of the antitrust-coordination surface RealPage exposed.

## Prior art and relationship to existing frameworks

The A0→A4 ladder structure is intentionally isomorphic to staged-autonomy frameworks already familiar to engineering and regulatory audiences. The contribution of this ADR is **not the ladder structure itself** — that is borrowed and acknowledged. The contribution is the **CRE-vertical mapping of autonomy tier to specific patterns and to specific regulatory matters** in the Context above. The ladder is the scaffolding; the per-tier-per-pattern + per-tier-per-matter mapping is the novel work.

Prior art:

- **SAE J3016** — *Taxonomy and Definitions for Terms Related to Driving Automation Systems for On-Road Motor Vehicles* (SAE International, 2014/2018/2021). The 0–5 ladder structure originates here. Autonomy Ladder A0→A4 is a five-tier adaptation for governed agentic AI in regulated workflows.
- **OECD AI Principles** (2019) — staged-oversight language for AI systems.
- **NIST AI RMF 1.0** (2023) — MANAGE 2.3 maturity scaffolding for human oversight scaling with risk.
- **Shavit et al.** (2023) — *Practices for Governing Agentic AI Systems* (OpenAI) — tier-based agent-autonomy framing.
- **Anderljung et al.** (2023) — *Frontier AI Regulation: Managing Emerging Risks to Public Safety* — staged-deployment framing.
- **Assurance Case methodology** — Kelly & Weaver (2004); Bloomfield, Bishop, Penny (2021) — the safety-critical-systems framing for "evidence stack that defends operation at a given assurance level."

See [`docs/PRIOR-ART.md`](../../docs/PRIOR-ART.md) for full intellectual lineage.

## What this does NOT cover

- **Per-task numerical scoring of autonomy** (each tier is qualitative + compose-pattern-defined, not a number; calibration is per-deployer)
- **Cross-organization autonomy transferability** (an A3 in one operator's stack is not necessarily A3 in another's; the tier is local to the assurance case)
- **Reverting from A4 back to A3** (this is operationally messy; documented in the operator's runbook, not the framework)
- **The trademark itself** — *Autonomy Ladder™* is a common-law mark; USPTO registration planned (see repo-root README License + Trademark section)

## Related

- All other ADRs — every pattern lives at a defined autonomy tier
- ADR-0006 (Shadow Mode) — required for A2 → A3 promotion
- ADR-0010 (Retention/Privilege) — privilege envelope on the A2→A3 promotion evidence pack
- [autonomy-ladder.io](https://autonomy-ladder.io) — self-score web demo for the framework
