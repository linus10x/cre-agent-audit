# Vendor clause — Revenue-management / pricing AI

> **Reference contract addendum, not legal advice.** Adapt to your jurisdictions and risk appetite in consultation with counsel. **Antitrust counsel must independently assess data-input topology; software-governance clauses do not substitute for input-side antitrust review.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

Drop-in contract language for the operator's next vendor contract renewal or change-order with a revenue-management AI vendor (RealPage YieldStar, RealPage LRO, AppFolio Property Manager, Yardi Revenue IQ, or equivalent). The clauses below pair with [ADR-0011 (Vendor-Output Adapter)](../adr/0011-vendor-output-adapter-pattern.md) and the documented stance in [ADR-0008's section on pricing-coordination defense framing](../adr/0008-fair-housing-preflight-gate.md).

**Operator note.** *U.S. v. RealPage* is ongoing civil antitrust litigation (DOJ + 8 state AGs, M.D.N.C., filed Aug 23, 2024). These clauses are drafted to support **process evidence relevant to good-faith defenses under § 1 rule-of-reason analysis**. They **do not cure per se exposure from data-pooling**; Operator's antitrust counsel must independently assess whether the Vendor's data-input topology creates per se exposure regardless of these contractual provisions.

## Section 1 — Data-input topology disclosure

1.1 **Input-data sources.** Vendor shall disclose to Operator: (i) the categories of data sources Vendor uses to generate pricing recommendations for Operator's properties (e.g., Operator-supplied data only; aggregated competitor data; market-survey data; public lease records), (ii) the granularity of any competitor data (property-level, asset-class-level, market-level, state-level), (iii) the recency of any competitor data (most-recent timestamp + freshness SLA).

1.2 **Independent-decision attestation.** Vendor shall attest that the pricing recommendation Vendor produces for Operator's Property A is generated without reference to any Operator's competitor's *non-public, current* pricing data, lease terms, occupancy data, or revenue-management decisions.

1.3 **Data-input change notification.** Vendor shall provide Operator no fewer than 30 days' written notice of any material change to the data-input topology disclosed under Section 1.1 (e.g., addition of a new competitor-data source, change in data-recency cadence, change in granularity).

## Section 2 — Independent-decision process evidence

2.1 **Per-asset recommendation record.** For every pricing recommendation Vendor produces for an Operator property, Vendor shall provide Operator a structured record containing at minimum: (i) the asset identifier, (ii) the recommendation (price + effective period), (iii) the reason codes supporting the recommendation, (iv) the model version that generated the recommendation, (v) the data-input snapshot the recommendation was based on (or a stable reference to it).

2.2 **No-coordination representation.** Vendor shall represent that Vendor does not use Operator's data to influence pricing recommendations to Operator's competitors, and conversely shall not use any competitor's non-public current data to influence pricing recommendations to Operator.

2.3 **Operator-discretion preservation.** Vendor shall acknowledge that the pricing recommendation is non-binding on Operator; Operator retains sole authority to set rent prices; Vendor shall not condition continued service on Operator's acceptance of any specific recommendation.

## Section 3 — Antitrust-defensibility cooperation

3.1 **Regulatory inquiry cooperation.** In the event of a regulatory inquiry, civil investigative demand, or antitrust litigation involving Operator's pricing decisions, Vendor shall cooperate with Operator's defense and shall make available within 15 business days of Operator's request: (i) the data-input topology disclosure (Section 1.1) for the period in question, (ii) the per-asset recommendation records (Section 2.1) for the period in question, (iii) Vendor's internal documentation of independent-decision design choices.

3.2 **Expert witness availability.** Vendor shall, at Operator's reasonable cost, make available a qualified Vendor representative to explain Vendor's model design, data-input topology, and independent-decision attestation in deposition or trial.

3.3 **Operator-discretion documentation.** Vendor shall periodically (no less than quarterly) provide Operator a summary of: (i) the number of Vendor recommendations Operator's staff accepted, (ii) the number Operator's staff modified, (iii) the number Operator's staff overrode. This summary supports Operator's documentation of independent decision-making.

## Section 4 — Audit-trail integration

4.1 **Audit-chain compatibility.** Vendor's per-asset recommendation records (Section 2.1) shall be deliverable in a structured format Operator can ingest into Operator's audit-chain (per [ADR-0003](../adr/0003-hash-chain-audit.md)) without manual transformation.

4.2 **Override audit support.** When Operator's staff override a Vendor recommendation, Operator shall record the override + the reason in Operator's audit chain. Vendor shall accept that the override-and-reason record is the controlling decision for that asset and that period.

## Section 5 — Disparate-impact monitoring (housing-rent vendors)

5.1 **Renter-impact reporting.** For multifamily Operators only: Vendor shall provide Operator a quarterly report showing the distribution of recommended rent changes across Operator's properties grouped by: (i) census-tract median income decile, (ii) census-tract racial composition (where lawfully available). This report supports Operator's monitoring for disparate impact on housing-cost burden.

5.2 **Voucher-respect requirement.** Vendor's pricing recommendations shall not condition on the housing-voucher status of current or prospective tenants at the Operator's properties.

## Section 6 — Term, Termination, and Survival

6.1 **Term.** This addendum shall be coterminous with the master services agreement.

6.2 **Termination for material breach.** Operator may terminate the master agreement for cause upon 30 days' written notice if Vendor materially breaches Sections 1.2 (independent-decision attestation), 2.2 (no-coordination representation), or 5.2 (voucher-respect requirement) and fails to cure within the notice period.

6.3 **Survival.** Sections 3 (antitrust-defensibility cooperation), 4 (audit-trail integration to the extent of records produced during the term), and 5.1 (disparate-impact reporting for the term) shall survive termination for the longer of: (i) 6 years, or (ii) the applicable antitrust statute of limitations.

## What this addendum does NOT cover

- **Pricing-coordination antitrust risk per se.** These clauses support process-evidence good-faith defenses under rule-of-reason; they do not cure per se exposure from competitor-data-pooling. Antitrust counsel review of data-input topology is mandatory.
- Indemnification, pricing, payment terms, service-level credits (separate negotiation)
- Insurance requirements (consult risk management)
- Jurisdiction-specific state-AG-investigation-cooperation requirements (consult counsel)

## How to use this template

1. **Antitrust-counsel review of Vendor's data-input topology before adoption.** This is not optional. Section 1.1 disclosure is the input to that review; if the disclosure shows the Vendor pools competitor data, the Operator's exposure may be material regardless of how well these contractual provisions are drafted.
2. Have counsel review and adapt the addendum
3. Negotiate as a Schedule to the master services agreement at the next renewal
4. Pair runtime adoption with [ADR-0011 (Vendor-Output Adapter)](../adr/0011-vendor-output-adapter-pattern.md) and the [ADR-0003 audit chain](../adr/0003-hash-chain-audit.md)
5. File the executed addendum + a copy of antitrust counsel's data-input-topology review memo with the General Counsel
