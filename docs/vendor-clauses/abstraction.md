# Vendor clause — Lease-abstraction AI

> **Reference contract addendum, not legal advice.** Adapt to your jurisdictions and risk appetite in consultation with counsel. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

Drop-in contract language for the operator's next vendor contract renewal or change-order with a lease-abstraction AI vendor (Leverton / MRI Software AI, V7 Lease, Reonomy, Aigen Sciences, Spacewell, or equivalent). The clauses below pair with [ADR-0007 (Lease-Abstraction Provenance Chain)](../adr/0007-lease-abstraction-provenance.md); the provenance pattern only works if the vendor exposes the clause-level provenance object this addendum obligates.

## Section 1 — Clause-level provenance disclosure

1.1 **Provenance object required.** For every clause extracted from a lease by Vendor's AI, Vendor shall provide Operator a structured Provenance Object containing at minimum:

| Field | Type | Required |
|---|---|---|
| `document_hash` | SHA-256 hex string of the source PDF | Yes |
| `source_page` | 1-indexed page number | Yes |
| `source_paragraph_range` | `(start, end)` paragraph index on the page | Yes |
| `ocr_confidence` | float 0.0–1.0 | Yes |
| `extraction_confidence` | float 0.0–1.0 (model-reported) | Yes |
| `model_version` | Vendor's versioned model identifier | Yes |
| `extracted_at` | ISO 8601 UTC timestamp | Yes |
| `reviewer_signature` | structured object (see 1.2) for material clauses; null for routine | Conditional |
| `bounding_box` | pixel coordinates for visual highlighting | Optional |

1.2 **Reviewer signature for material clauses.** For clauses Vendor's pipeline categorizes as `material` (or analogous category — rent schedule, break clause, options, jurisdiction, outgoings, co-tenancy), the Provenance Object shall include a `reviewer_signature` field containing: (i) reviewer identifier tied to an identity provider, (ii) timestamp of review, (iii) SHA-256 sigil of `reviewer_id + clause_text + reviewed_at`, (iv) any reviewer notes.

1.3 **No clause without provenance.** Vendor shall not deliver to Operator any extracted clause that lacks a complete Provenance Object. If Vendor's pipeline produces a clause for which provenance cannot be generated (low-confidence OCR, source-document corruption, model-failure), Vendor shall return a structured error to Operator; Operator's downstream system shall not receive the clause text.

## Section 2 — Material-clause-quality SLA

2.1 **Confidence threshold.** Vendor shall not deliver `material` clauses with `extraction_confidence` below 0.85 (or such other threshold mutually agreed in Schedule [N] per portfolio).

2.2 **Reviewer signature SLA.** Vendor shall deliver `material` clauses only with a `reviewer_signature` present; clauses below 0.85 confidence shall be routed for human review prior to delivery, with the resulting reviewer signature satisfying this requirement.

2.3 **Hash-mismatch protection.** Vendor shall maintain integrity of the source-document hash from intake through extraction and shall reject delivery of any clause whose `document_hash` does not match a document currently in Vendor's intake repository.

2.4 **Stale-model protection.** Vendor shall maintain a published minimum model version per clause criticality; clauses extracted by below-minimum model versions shall not be delivered. The minimum version shall be updated no less than annually based on Vendor's internal model-quality monitoring.

## Section 3 — Litigation-discovery support

3.1 **Provenance preservation.** Vendor shall preserve the Provenance Object for each extracted clause for the longer of: (i) the duration of the master agreement plus 6 years, or (ii) the applicable lease-litigation statute of limitations for the jurisdiction(s) covered by Operator's portfolio.

3.2 **Discovery response.** In the event of litigation, regulatory inquiry, or formal lease-dispute proceeding involving an extracted clause, Vendor shall produce within 10 business days of Operator's request: (i) the complete Provenance Object for the clause in question, (ii) Vendor's internal extraction-pipeline logs for the extraction event, (iii) any reviewer audit trail for the reviewer signature.

3.3 **Expert witness availability.** Vendor shall, at Operator's reasonable cost, make available a qualified Vendor representative to provide deposition or trial testimony explaining Vendor's extraction methodology, model versioning, and confidence calibration.

## Section 4 — Model documentation

4.1 **Model Card.** Vendor shall provide Operator with a Model Card (Mitchell et al. 2019 format) for each model version used in extraction services. The Model Card shall be updated within 30 days of any material model change.

4.2 **Training-data provenance.** Vendor shall represent that its training data was lawfully obtained and shall maintain records sufficient to defend that representation in the event of an IP, copyright, or trade-secret claim by a third party.

## Section 5 — Term, Termination, and Survival

5.1 **Term.** This addendum shall be coterminous with the master services agreement.

5.2 **Survival.** Sections 3.1 (provenance preservation), 3.2 (discovery response), and 3.3 (expert availability) shall survive termination for the period stated in 3.1.

## What this addendum does NOT cover

- Multi-language extraction (Vendor may charge separately; specify in Schedule)
- Custom clause-type extraction beyond Vendor's standard taxonomy (statement of work)
- Indemnification, pricing, service-level credits, insurance (separate negotiation)
- Lease-specific data-residency requirements (consult counsel for jurisdiction-specific posture; some jurisdictions impose lease-data-localization requirements)

## How to use this template

1. Have counsel review and adapt to the Operator's lease-administration risk-appetite
2. Negotiate as a Schedule to the master services agreement at the next renewal
3. Pair runtime adoption with [ADR-0007 (Lease Provenance)](../adr/0007-lease-abstraction-provenance.md)
4. If the Vendor refuses Section 3 (litigation-discovery support), escalate to General Counsel — the absence of discovery cooperation is a material risk for any operator whose lease portfolio is the subject of recurring lease-dispute proceedings
