> **Provenance.** This file was drafted by the author in the FINOS AI Risk Initiative artifact format.
> **It has not been reviewed, endorsed, or accepted by FINOS or the AIR Working Group as of v0.2.0 (2026-06-02).**
> It is released independently under MIT alongside the patterns it accompanies. The full 19-artifact submission
> package — including 16 additional risk and mitigation files in author-draft form — is under separate
> working-group-bound development on a private branch (`finos-submission-wip`) and is not in this folder by design.
>
> Adopters: fork freely; cite in your own control catalog; do not infer FINOS endorsement from the use of the
> FINOS AIR schema. See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md).

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

- Tenant-screening AI scoring voucher applicants negatively → SafeRent failure mode (approximately $2.275M class settlement, November 20, 2024, 5-year prohibition on score-based screening)
- Tenant-screening AI relying on inaccurate eviction-record data → TransUnion failure mode ($15M FTC + CFPB settlement, October 2023)
- Renewal-pricing AI using zip-code as a primary feature → race proxy
- Marketing audience-targeting AI using preferred-language as a feature → national-origin proxy
- Housing-credit AI using income source as a decision input in a source-of-income-protected jurisdiction → state-law violation
- Tenant-screening AI with blanket criminal-history disqualifications → HUD 2016 guidance violation

## Severity classification

**Severity: Critical.** Each named example carries either a settled-case precedent ($15M Trans Union Rental Screening Solutions · approximately $2.275M SafeRent class settlement · binding HUD guidance) or a binding regulatory standard (FHA, ECOA, CO SB 26-189, disparate-impact framework). The cost of an unmitigated failure is measured in millions per incident plus reputational damage and operational restrictions that may be imposed by regulatory settlement or enforcement action.

## Related research

- Autonomy Ladder™ ADR-0008 (Fair-Housing Pre-Flight Gate, CRE-native) — `github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0008-fair-housing-preflight-gate.md`
- Reference implementation in MIT-licensed code — `github.com/linus10x/cre-agent-audit/blob/main/src/cre_agent_audit/governance/fair_housing_preflight.py`
- Louis v. SafeRent Solutions consent order (D. Mass., November 20, 2024)
- TransUnion Rental Screening Solutions FTC + CFPB settlement (October 2023)
- HUD Fair Housing Act AI guidance (2024 HUD memorandum on AI and Fair Housing)
- Colorado AI Act (SB 24-205, as amended by SB 26-189 signed May 14, 2026) — compliance horizon January 1, 2027
- HUD 2016 criminal-history-screening guidance
- U.S. v. RealPage, Inc. et al., DOJ + 8 state AGs, filed August 23, 2024 (Sherman Act §§ 1 and 2; resolved by DOJ proposed consent judgment Nov 24, 2025, pending Tunney Act approval, never adjudicated) — parallel antitrust surface

## Detection

A program lacking this control will show one or more of:
- Vendor "AI fairness reports" produced AFTER decisions are executed
- Absence of runtime checks against voucher-status feature inclusion
- Decision logs that do not record gate-verdict reason codes
- No state-by-state SOI ordinance mapping in the program's compliance baseline
- No 90-day rolling disparate-impact monitor on output cohorts

## Related mitigations

- `AIR-MIT-RC-FHA-01` — Autonomy Ladder™ Fair-Housing Pre-Flight Gate (preventative control with 5 ordered checks + bypass auto-escalation)
