# First 90 Days — engineering deliverables that feed your GC's privileged AI risk assessment

> **⚠ Reference cadence, not legal or operational advice.** This document sketches an engineering deployment cadence for an interim or fractional CTO/CAIO adopting the cre-agent-audit patterns inside a CRE operating company. The cadence is reframed from a public "audit-baseline report" output to **engineering rails that feed your General Counsel's privileged risk assessment** under attorney-direction. See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md).

## Why this cadence and not the consultant version

The standard consulting cadence is "Day 30: publish an audit-baseline report." At a real operating company that report is discoverable; it anchors the operator to a specific Day-30 posture, before the engineering rails are in place to defend it. A General Counsel will not approve that output, and rightly so. This cadence instead frames Days 1–30 as **engineering inventory + privilege scoping**: the artifact is a *running inventory* that feeds the GC's privileged work-product assessment, not a published baseline. Days 31–60 are engineering deliverables (Sovereign Veto + Audit Ledger rails) that produce the evidence the GC's privileged assessment uses on Day 90.

---

## Days 1–30: Engineering inventory + privilege scoping

**Artifact produced:** `RUNNING-INVENTORY.md` — engineering working document, not for external distribution.

**Person owning:** VP Eng (joint with General Counsel for privilege scoping).

**Failure mode prevented:** a discoverable "audit-baseline report" that anchors the operator to a specific Day-30 posture before the rails to defend it exist.

**Day-1 specific tasks:**

1. Ask the GC for (a) the last three AI-system exception logs and (b) the last RFP response to an enterprise customer's AI-governance questionnaire. Those two documents tell you what governance debt you inherited.
2. Confirm with the GC the privilege framing for the next 30 days' inventory work (attorney-direction memo; work-product protection scope).
3. Read [`docs/SHIP-RECEIPT.md`](../docs/SHIP-RECEIPT.md) (if you adopted this repo via fork) and `ROADMAP.md` to know what is here and what is v0.3.

**Day-15 target:**

Every consequential AI decision touching a tenant, borrower, or counterparty is named in `RUNNING-INVENTORY.md`, with: model version, training-data source (in-house or vendor), decision-log location, decision-volume per quarter, and current human-in-loop posture.

**Day-30 target:**

Each AI surface scored against A0–A4 (per ADR-0004); the misclassified flagged to GC; no published "baseline report" — the inventory feeds the GC's privileged work-product assessment under attorney-direction.

---

## Days 31–60: Sovereign Veto + Audit Ledger rails

**Artifact produced:** deployed `SovereignVeto` (ADR-0002) on every A2+ decision class; deployed `AuditLedger` (ADR-0003) capturing every decision going forward; published RACI per ADR-0002 "Designating the Sovereign" subsection.

**Persons owning:** VP Eng (build) + General Counsel + Chief Compliance Officer (authority designation).

**Failure modes prevented:**
- A regulatory event with no forward decision-record
- An undocumented veto invocation that becomes a personnel dispute
- A bypass owner without IdP-verified identity

**Day-31 to Day-60 sequence:**

1. Wire `SovereignVeto.check()` into the agent boundary on every A2+ decision class identified in `RUNNING-INVENTORY.md`.
2. Wire `AuditLedger.append()` into every decision class — vetoed *and* executed.
3. Resolve the "Designating the Sovereign" RACI to your IdP groups (Okta, Azure AD). Document the resolution.
4. Build the `BypassAuthorityResolver` integration (the most-likely 4–6-month item if you don't already have SOX SOX-style IdP plumbing).
5. Wire `AuditLedger.chain_head()` publication to an external witness register (OpenTimestamps is free; Sigstore Rekor if your CD pipeline already has Sigstore). Weekly cadence is sufficient for most operators.

**Day-60 target:**

- Tamper-evident (via external witness anchor) audit trail for forward decisions.
- Veto-event count on the operating-partner review.
- IdP-verified bypass authority on every authorized override.

---

## Days 61–90: Fair-Housing Pre-Flight + Provenance + DEFCON cadence

**Artifact produced:** deployed Fair-Housing Pre-Flight Gate (ADR-0008) on tenant-screening + credit-screening surfaces; deployed Lease Provenance (ADR-0007) on lease-abstraction workflows; DEFCON state (ADR-0001) wired into the weekly operating cadence.

**Persons owning:** VP Eng + Chief Compliance Officer; Chief Revenue Officer consulted on lease + pricing surfaces; General Counsel reviews disparate-impact monitor output.

**Failure modes prevented:**
- A SafeRent-pattern fact pattern with no exception log
- A contested lease clause with no extraction-confidence record
- A protected-class proxy feature that ships without lexical-blocklist screening
- A four-fifths-rule disparate-impact event with no veto and no auto-escalation

**Day-61 to Day-90 sequence:**

1. Wire `FairHousingPreflightGate.evaluate()` on the tenant-screening surface. Tune the per-jurisdiction blocklist with the GC.
2. Confirm the disparate-impact monitor's reportable-demographics inputs are GC-approved.
3. Wire `LeaseProvenanceCheck.evaluate()` on the lease-abstraction workflow. If the vendor doesn't expose clause-level provenance, file a contract change-order using [`docs/vendor-clauses/abstraction.md`](../docs/vendor-clauses/abstraction.md).
4. Stand up the DEFCON weekly operating cadence: state transitions are an operating-partner review item, not an engineering-only signal.
5. Document the discovery / retention / privilege posture per ADR-0010 — retention schedule synced to FHA SOL (2 years admin + private), ECOA SOL (5 years), state-statute SOLs; litigation-hold integration.

**Day-90 target:**

- Artifact stack defensible under the named regulatory matters.
- Pattern 7 + 8 evidence chains demonstrable to outside counsel.
- Annual review of ADR-0010 booked with outside counsel.

---

## Day 91+: Promotion gate cadence

- **Autonomy Ladder (ADR-0004)** governs further promotions; A2→A3 requires the four-criterion gate clearance (sovereign veto load-tested · audit ledger ≥90 days · shadow mode ≥30 days no material divergence · circuit-breaker tested + recorded on ledger).
- **Shadow Mode (ADR-0006)** for any new model touching an A2+ surface.
- **Quarterly review** against the regulation-mapping table (Pattern 5) and the four-framework matrices ([`docs/MAPPING-MATRICES.md`](../docs/MAPPING-MATRICES.md)).
- **Annual review** of ADR-0010 (audit-chain retention, privilege, discovery posture) with outside counsel.

---

## Notes on vendor-mediated AI surfaces

Most CRE operators do NOT run in-house screening, abstraction, or pricing models. They buy from SafeRent, Yardi/RentCafe, RentGrow, RealPage, AppFolio, Yardi Revenue IQ, Leverton/MRI, V7, etc. For vendor-mediated surfaces, the patterns translate to **procurement-clause power** in addition to engineering rails:

- [`docs/vendor-clauses/screening.md`](../docs/vendor-clauses/screening.md) — DPA + model-risk addendum + four-fifths-rule reporting SLA for tenant-screening vendors
- [`docs/vendor-clauses/abstraction.md`](../docs/vendor-clauses/abstraction.md) — lease-vendor SLA + clause-level provenance-disclosure requirement
- [`docs/vendor-clauses/pricing.md`](../docs/vendor-clauses/pricing.md) — independent-decision contract clause + data-input-topology disclosure for revenue-management vendors

ADR-0011 documents the design for the `VendorScoreGate` adapter that bridges vendor outputs (score, recommendation, reason-codes) into the operator's audit ledger + sovereign-veto layer without requiring feature-level access.

---

## Notes on what this cadence does NOT do

- Does NOT replace a privileged risk assessment by outside counsel. The cadence produces the engineering rails the GC's assessment uses.
- Does NOT cover the contractual addendum negotiation with vendors (that's a procurement workstream on a parallel track).
- Does NOT implement the v0.3 follow-ups (pluggable persistence, RFC 3161 timestamps, witness-anchor reference integration, VendorScoreGate concrete implementation, MI-threshold learned-proxy detection). Plan the deployment around v0.2.0's bounded claims; track v0.3 as a budgeted v0.3 follow-on.
