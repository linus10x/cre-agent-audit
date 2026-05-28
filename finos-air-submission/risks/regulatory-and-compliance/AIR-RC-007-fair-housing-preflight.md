---
risk_id: AIR-RC-007
title: "Tenant-screening, renewal-pricing, marketing-audience-targeting, or housing-credit AI executes without Fair Housing Act pre-flight gating"
category: regulatory-and-compliance
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
related_mitigations:
  - AIR-MIT-RC-FHA-01
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0008-fair-housing-preflight-gate.md"
license: MIT
---

## Description

In commercial-real-estate workflows, AI agents touching tenant screening, renewal pricing, marketing audience targeting, housing credit decisioning, or tenant-communication personalization operate on protected decision surfaces under the Fair Housing Act (42 U.S.C. § 3604), the Equal Credit Opportunity Act (15 U.S.C. § 1691), HUD AI guidance (2024), the Colorado AI Act (SB 26-189, effective January 1, 2027), and the disparate-impact standard (24 C.F.R. § 100.500). Without a pre-flight gate that runs before the action executes, the agent can produce a screening decision, a price recommendation, or a marketing audience that violates one or more of these statutes — typically through a feature that proxies for protected class, includes voucher-status as a negative signal, or produces a disparate impact across protected cohorts that breaches the four-fifths rule.

## Contributing factors and root causes

- Input features that proxy for protected class (zip-only screening proxies for race; language preference proxies for national origin)
- Voucher-status or rental-assistance features encoded as scoring inputs (the SafeRent failure mode)
- Income-source features used in jurisdictions with source-of-income protections (CA · CT · DC · MA · MN · NJ · NY · OR · VT · WA plus municipal layers)
- Criminal-history features with blanket disqualifications, lookback periods exceeding state limits, or arrest-not-conviction inputs
- Output disparate impact across protected cohorts where the lowest-cohort selection rate falls below 80% of the highest-cohort selection rate (the four-fifths rule)
- Lack of a runtime gate that runs BEFORE execution — vendor "AI fairness reports" produced AFTER the fact do not prevent the harm

## CRE-specific examples

- Tenant-screening AI scoring voucher applicants negatively → SafeRent failure mode ($2.3M settlement, November 20, 2024, 5-year prohibition on score-based screening)
- Tenant-screening AI relying on inaccurate eviction-record data → TransUnion failure mode ($15M FTC + CFPB settlement, October 2023)
- Renewal-pricing AI using zip-code as a primary feature → race proxy
- Marketing audience-targeting AI using preferred-language as a feature → national-origin proxy
- Housing-credit AI using income source as a decision input in a source-of-income-protected jurisdiction → state-law violation
- Tenant-screening AI with blanket criminal-history disqualifications → HUD 2016 guidance violation

## Severity classification

**Severity: Critical.** Each named example carries either a settled-case precedent ($15M TransUnion · $2.3M SafeRent · binding HUD guidance) or a binding regulatory standard (FHA, ECOA, CO SB 26-189, disparate-impact framework). The cost of an unmitigated failure is measured in millions per incident plus reputational damage and operational restrictions imposed by consent decree.

## Related research

- Autonomy Ladder™ ADR-0008 (Fair-Housing Pre-Flight Gate, CRE-native) — `github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0008-fair-housing-preflight-gate.md`
- Reference implementation in MIT-licensed code — `github.com/linus10x/cre-agent-audit/blob/main/src/cre_agent_audit/governance/fair_housing_preflight.py`
- Louis v. SafeRent Solutions consent order (D. Mass., November 20, 2024)
- TransUnion Rental Screening Solutions FTC + CFPB settlement (October 2023)
- HUD Fair Housing Act AI guidance (2024 HUD memorandum on AI and Fair Housing)
- Colorado AI Act SB 26-189 (signed 2026 · effective January 1, 2027)
- HUD 2016 criminal-history-screening guidance
- DOJ-RealPage consent decree (parallel antitrust surface · November 24, 2025)

## Detection

A program lacking this control will show one or more of:
- Vendor "AI fairness reports" produced AFTER decisions are executed
- Absence of runtime checks against voucher-status feature inclusion
- Decision logs that do not record gate-verdict reason codes
- No state-by-state SOI ordinance mapping in the program's compliance baseline
- No 90-day rolling disparate-impact monitor on output cohorts

## Related mitigations

- `AIR-MIT-RC-FHA-01` — Autonomy Ladder™ Fair-Housing Pre-Flight Gate (preventative control with 5 ordered checks + bypass auto-escalation)
