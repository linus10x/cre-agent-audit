# PE Due-Diligence Checklist — AI Governance Posture at a CRE Portco

> **Reference checklist, not investment-decision advice.** Adapt to the operating-partner's investment thesis + the portco's regulatory exposure profile in consultation with PE counsel and CRE-specialist outside counsel. See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md).

A 10-question checklist for a PE operating partner conducting an AI-governance review of a CRE portfolio company. Hand to the portco CTO with a 14-day response window. Use the responses to (a) score the portco's AI-governance maturity against a portfolio-wide baseline, (b) identify the highest-leverage 90-day interventions, (c) inform the portco's next operating-cadence review.

The 10 questions below are designed to be answerable in ≤2 pages each. A portco CTO who cannot answer them is the answer.

---

## Question 1 — Pattern adoption surface

**Of the 9 patterns in [`linus10x/cre-agent-audit`](https://github.com/linus10x/cre-agent-audit), which are live in production, which are stubbed, and which are not yet considered? List by AI surface (tenant-screening, lease-abstraction, pricing, vendor-data flow, etc.).**

**Why it matters.** The patterns are the operating-partner's vocabulary for the AI-governance conversation. A portco that has not yet considered each pattern is operating below the assurance level the regulatory landscape is moving toward.

**Defensible answer shape.** A table by surface × pattern with status (live / stubbed / not started / not applicable + reason).

**Maps to.** [`docs/controls/`](controls/) for the per-pattern Control Description Tables.

---

## Question 2 — Exception-log review cadence

**Show me the last 90 days of `FairHousingException` log entries (or equivalent for your vendor-mediated screening flow). For each, name the bypass owner, the regulatory basis, and the auto-escalation status.**

**Why it matters.** Bypass-event volume is a leading indicator of either calibration drift (too many bypasses → gate is over-tuning) or governance theater (too few → either the gate is not firing or bypasses are not being logged).

**Defensible answer shape.** The actual log entries (redacted for PII as needed) + a summary of bypass-owner distribution, reason-code distribution, and auto-escalation events.

**Maps to.** ADR-0008 `FairHousingException` + ADR-0002 `SovereignBypass`.

---

## Question 3 — Disparate-impact monitor output

**Show me the disparate-impact monitor's last 90-day output for each consequential-decision surface. For each protected cohort with reportable demographics, what is the four-fifths-rule ratio? Has any cohort approached or fallen below 0.80?**

**Why it matters.** The four-fifths-rule is the threshold of regulatory attention. A cohort below 0.80 is settled-liability territory under disparate-impact analysis per *Texas Dept. of Housing v. Inclusive Communities Project*, 576 U.S. 519 (2015) and HUD 24 C.F.R. § 100.500.

**Defensible answer shape.** The monitor's structured output for the period, with the four-fifths-rule ratios + the operator's response to any cohort below threshold.

**Maps to.** ADR-0008 `DisparateImpactMonitor`.

---

## Question 4 — Sovereign Veto authority designation

**Name the General Counsel + Chief Compliance Officer + Chief Risk Officer who hold Sovereign Veto authority per the [ADR-0002 Designating-the-Sovereign RACI](adr/0002-sovereign-veto.md). Show me the written RACI document.**

**Why it matters.** If the veto authority is unnamed or undocumented, the bypass log is a personnel dispute waiting to happen. The RACI must be in writing, IdP-resolvable, and known to the board's risk committee.

**Defensible answer shape.** The written RACI (one-page is sufficient if specific) + the IdP groups it resolves to + the board-notification trigger thresholds.

**Maps to.** ADR-0002 "Designating the Sovereign" subsection.

---

## Question 5 — Audit-chain witness-anchor cadence

**Where is the audit-chain `chain_head()` digest published (which external witness register, which cadence)? Show me the last 4 publication records.**

**Why it matters.** Without external witness anchoring, the audit chain is internally-consistent but not adversarially tamper-evident. A portco that has not anchored the chain head is one privileged-host-compromise away from a regulator-facing problem they cannot prove they did not cause.

**Defensible answer shape.** The publication endpoint (OpenTimestamps URL, Sigstore Rekor entry, regulator-side log reference) + cadence (weekly is sufficient for most operators) + the last 4 entries.

**Maps to.** [ADR-0003 Audit Evidence Properties section](adr/0003-hash-chain-audit.md).

---

## Question 6 — Retention schedule

**What is the retention schedule for the audit chain? Which statutes of limitations does it synchronize to?**

**Why it matters.** Audit-chain entries are discoverable evidence. Indefinite retention is indefinite liability surface; too-short retention is a spoliation risk. The schedule must be SOL-synchronized + litigation-hold-integrated.

**Defensible answer shape.** A retention schedule by entry type (decision log, exception log, residency request, etc.) keyed to the SOL of each applicable statute (FHA 2yr, ECOA 5yr, state-statute SOL by jurisdiction), with the deletion process documented and the litigation-hold integration named.

**Maps to.** [ADR-0010 Audit-Chain Retention, Privilege & Discovery Posture](adr/0010-audit-chain-retention-privilege-discovery.md).

---

## Question 7 — Vendor-mediated AI surface coverage

**Most CRE-operator AI surface is vendor-mediated (SafeRent, RentGrow, RealPage, Yardi, MRI, EliseAI, etc.). For each vendor-mediated surface, show me the executed contract addendum implementing the relevant template at [`docs/vendor-clauses/`](vendor-clauses/) — DPA + model-risk addendum + fairness reporting SLA for screening, provenance-disclosure SLA for abstraction, independent-decision clause + data-input-topology disclosure for pricing.**

**Why it matters.** If 80% of the AI surface is vendor-mediated and the vendor contracts do not obligate the data the operator's governance rails need, the engineering rails are governing 20% of the surface.

**Defensible answer shape.** An inventory of vendor surfaces × contract-addendum-execution status. If a vendor refuses to negotiate the addendum, that itself is a finding.

**Maps to.** [ADR-0011 Vendor-Output Adapter Pattern](adr/0011-vendor-output-adapter-pattern.md) + `docs/vendor-clauses/`.

---

## Question 8 — Promotion-gate evidence packs

**For every workflow currently running at Autonomy Ladder A3 or A4, show me the promotion-gate evidence pack per [ADR-0004's four-criterion requirement](adr/0004-autonomy-ladder-a0-a4.md): (i) Sovereign Veto load-tested, (ii) Audit Ledger ≥ 90 days, (iii) Shadow Mode ≥ 30 days no material divergence, (iv) Circuit-breaker tested + recorded on the ledger.**

**Why it matters.** A3 is the regulator-visible boundary. A workflow at A3 without the four-criterion evidence is operating above the assurance level it can defend — exactly the failure mode the three named regulatory matters (TransUnion, SafeRent, RealPage) demonstrated.

**Defensible answer shape.** For each A3+ workflow, the four-criterion evidence pack (1 page per criterion + the load-test results + the divergence report + the circuit-breaker test record).

**Maps to.** ADR-0004 promotion gate + ADR-0006 Shadow Mode.

---

## Question 9 — Litigation-hold integration

**What is the integration between Operator's litigation-hold workflow and the audit-chain retention engine? Show me the documented process for: (i) hold issuance, (ii) chain-scope identification, (iii) retention-engine suspension, (iv) hold release.**

**Why it matters.** A retention engine that does not pause on litigation hold is a spoliation risk regardless of how good the engineering is. The integration must be documented in writing and tested at least annually.

**Defensible answer shape.** The written process + the most recent hold-cycle test result.

**Maps to.** [ADR-0010 section 4](adr/0010-audit-chain-retention-privilege-discovery.md).

---

## Question 10 — Annual GC + outside-counsel review

**When was the most recent annual GC + outside-counsel review of [ADR-0010 (audit-chain retention/privilege/discovery posture)](adr/0010-audit-chain-retention-privilege-discovery.md)? Who from outside counsel attended? What were the findings?**

**Why it matters.** The policy layer in ADR-0010 is the operator's work, not the framework's. It needs counsel review to stay current with jurisdiction-specific privilege rule changes, SOL changes, and litigation-hold-process changes. Annual cadence is the floor.

**Defensible answer shape.** The date + outside-counsel firm name + findings memo summary (the memo itself is typically privileged; the existence and date are not).

**Maps to.** ADR-0010.

---

## Scoring rubric (operating-partner use)

| Score | Meaning |
|---|---|
| **A — Adopted in full** | Every pattern live in production; every question has a defensible documented answer; annual counsel review on cadence |
| **B — In progress** | Patterns 2 + 3 (Sovereign Veto + Audit Ledger) live; Pattern 8 (Fair Housing Pre-Flight) live; remaining patterns scoped with named owner + 90-day plan |
| **C — Scoped but not built** | Patterns identified; engineering plan exists; nothing in production yet |
| **D — Not considered** | Portco CTO has not heard of the patterns; no engineering plan; no GC review |

A B-or-above score is the floor for a PE operating partner to call the portco's AI-governance posture "defensible." Anything below B is a 90-day-priority intervention.

## What this checklist does NOT do

- Does not replace a full IT-general-controls or SOC 2 audit
- Does not cover non-AI cybersecurity posture (separate review)
- Does not assess the operator's data-quality program (separate)
- Does not address vertical-specific frameworks beyond CRE (multifamily-specific HUD-funded posture, industrial-specific OSHA AI posture, etc. — consult specialists)
- Does not constitute legal advice — the operating partner's counsel should review the questions + the responses
