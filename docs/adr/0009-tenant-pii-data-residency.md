# ADR-0009 · Tenant-PII Data-Residency Partitioning

**Status:** Accepted · CRE-native
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

Tenant data crosses jurisdictions in CRE operations as a matter of routine. A multi-state landlord with a centralized property-management platform processes data on tenants whose residency, lease jurisdiction, employment jurisdiction, and consent jurisdiction may not overlap. An international tenant in a US-based portfolio adds GDPR exposure. A vendor processing tenant data in a different state adds CCPA / CPRA exposure. Cross-jurisdiction flows that violate residency requirements are settled-liability territory under GDPR (EU tenants), under CCPA / CPRA (California), and under an increasing list of state-level tenant-data-protection statutes.

The conventional approach is "we encrypt the data." Encryption is necessary and insufficient. The regulatory question is not whether the data is encrypted in transit — it is whether the data was *permitted to cross the boundary at all*, and if so, on what legal basis.

The pattern that works is **partition at the storage layer, gate every cross-jurisdiction read at the agent boundary, and tag every cross-jurisdiction flow with a legal basis recorded on the audit chain.**

## Decision

Tenant data is segregated by **jurisdiction** at the storage layer. Every tenant record carries a `jurisdiction` field at write time. Every read that crosses a jurisdiction boundary requires a `LegalBasis` tag and a recorded purpose.

### The data model

```python
class Jurisdiction(Enum):
    US_FEDERAL = "us_federal"
    US_CA = "us_ca"
    US_NY = "us_ny"
    US_TX = "us_tx"
    # ... full enumeration in compliance_rules.yaml
    EU_DE = "eu_de"
    EU_FR = "eu_fr"
    # ...
    CA_ON = "ca_on"  # Canadian Ontario, etc.

class LegalBasis(Enum):
    CONSENT = "consent"                   # GDPR Art. 6(1)(a)
    CONTRACT = "contract"                 # GDPR Art. 6(1)(b) · lease performance
    LEGITIMATE_INTEREST = "legitimate_interest"  # GDPR Art. 6(1)(f) · documented LIA required
    LEGAL_OBLIGATION = "legal_obligation" # GDPR Art. 6(1)(c) · statute citation required
    # CCPA/CPRA does not use the same taxonomy but maps onto these four

@dataclass(frozen=True)
class TenantRecord:
    tenant_id: str
    jurisdiction: Jurisdiction
    data: TenantDataPayload          # the actual PII
    consent_record: ConsentRecord | None  # required if LegalBasis.CONSENT was used to write

@dataclass(frozen=True)
class CrossJurisdictionRequest:
    requesting_actor: str
    requesting_jurisdiction: Jurisdiction
    target_record_jurisdiction: Jurisdiction
    legal_basis: LegalBasis
    purpose: str                     # specific use case · not generic
    statute_citation: str | None     # required for LEGAL_OBLIGATION
    lia_document_id: str | None      # required for LEGITIMATE_INTEREST
    consent_record_id: str | None    # required for CONSENT
```

### The residency veto

The sovereign veto (ADR-0002) fires on any of:

1. **`RESIDENCY-CROSS-JURISDICTION-UNTAGGED`** — agent attempts to read a record where `requesting_jurisdiction != target_record_jurisdiction` without a `LegalBasis` on the request.
2. **`RESIDENCY-CONSENT-MISSING`** — `LegalBasis.CONSENT` claimed but no `consent_record_id` provided or the record is not retrievable or is expired.
3. **`RESIDENCY-LIA-MISSING`** — `LegalBasis.LEGITIMATE_INTEREST` claimed but no `lia_document_id` provided, or the LIA document does not cover the requesting purpose.
4. **`RESIDENCY-STATUTE-MISSING`** — `LegalBasis.LEGAL_OBLIGATION` claimed but no `statute_citation` provided.
5. **`RESIDENCY-PURPOSE-VAGUE`** — `purpose` field is generic (e.g., "analytics", "operations") rather than specific (e.g., "delinquency-risk modeling for occupancy-cost report Q3 2026").

### GC sign-off for exceptions

Exceptions to the residency veto require GC sign-off, not just managerial. The bypass writes a logged exception structurally identical to ADR-0008's `FairHousingException` but with `bypass_authority = AuthorityLevel.GC` mandatory.

### Aggregation rule

Aggregate reads across jurisdictions (e.g., portfolio-wide delinquency-rate dashboard) require either:

- **Anonymization at the gate** — the aggregator receives only counts and ratios, never per-tenant rows. Enforced by an aggregator-mode pattern in `src/governance/tenant_pii_residency.py` that returns a `JurisdictionAggregate` object containing only counts.
- **OR**: A blanket `LegalBasis` on the aggregating actor, GC-signed, with a documented retention policy on the aggregate.

The default is anonymization. A blanket basis is a deliberate exception, logged.

## Consequences

**Positive.** Cross-jurisdiction data flows are explicit, justified, and recorded. A regulator inquiry under GDPR can be answered by a query against the audit chain ("show me every cross-jurisdiction read of EU-resident tenant data and the legal basis on each"). A CCPA consumer-rights request can be served by partition-aware queries that do not require scanning the whole platform.

**Negative.** Adds cost to every read. Mitigated by the fact that intra-jurisdiction reads (the bulk) do not invoke the gate beyond a partition-check. Cross-jurisdiction reads carry the gate cost, which is exactly the surface where the cost is justified.

**Architectural.** Storage is partitioned at the lowest layer. Agents cannot bypass by reading "the database directly" because there is no single database — there are jurisdiction-partitioned stores with the gate as the only multi-store reader.

## What this gate does NOT cover

- **Vendor-of-vendor PII flows** — if a vendor processing tenant data uses sub-processors that route data across jurisdictions, the gate cannot see inside the vendor. Vendor due diligence remains a separate control.
- **Re-identification attacks on aggregate outputs** — k-anonymity and differential privacy on aggregates are out of scope for v1. Issue placeholder.
- **Tenant-initiated cross-jurisdiction transfers** — e.g., a tenant requesting their records be sent to a new jurisdiction. Handled by a specific consent-bearing path, not the residency veto.

## Regulatory anchor

- GDPR Art. 6 (lawful basis), Art. 13-14 (transparency), Art. 30 (records of processing)
- CCPA / CPRA (Cal. Civ. Code § 1798.100 et seq.)
- State-level tenant-data-protection statutes (NY tenant data protection · CA AB-2273 analog for adults · etc.)
- EU AI Act for EU tenants where AI processing is in scope

## Implementation notes

See `src/governance/tenant_pii_residency.py` for the reference implementation, `src/schemas/` for `TenantRecord` and related typed objects, and `examples/` for the cross-jurisdiction demonstration paths.

## Related

- ADR-0002 (Sovereign Veto) — the enforcement layer
- ADR-0003 (Hash-chain Audit) — every cross-jurisdiction read and every exception is recorded
- ADR-0005 (Regulation-to-Pattern Mapping) — jurisdictional rules live in `compliance_rules.yaml`
- ADR-0008 (Fair-Housing Pre-Flight) — the gates run in sequence; residency runs first on cross-jurisdiction reads
