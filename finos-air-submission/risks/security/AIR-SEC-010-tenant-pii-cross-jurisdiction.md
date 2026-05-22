---
risk_id: AIR-SEC-010
title: "Cross-jurisdiction tenant-PII flow without a recorded legal-basis tag"
category: security
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
related_mitigations:
  - AIR-MIT-SEC-PII-01
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0009-tenant-pii-data-residency.md"
license: MIT
---

## Description

Tenant data crosses jurisdictions in CRE operations as a matter of routine. A multi-state landlord with a centralized property-management platform processes data on tenants whose residency, lease jurisdiction, employment jurisdiction, and consent jurisdiction may not overlap. An international tenant in a US-based portfolio adds GDPR exposure. A vendor processing tenant data in a different state adds CCPA / CPRA exposure. Cross-jurisdiction flows that violate residency requirements are settled-liability territory under GDPR (EU tenants), under CCPA / CPRA (California), and under an increasing list of state-level tenant-data-protection statutes.

[TODO Week 7: expand the 5 RESIDENCY-* veto reason codes (CROSS-JURISDICTION-UNTAGGED · CONSENT-MISSING · LIA-MISSING · STATUTE-MISSING · PURPOSE-VAGUE), the LegalBasis taxonomy (GDPR Art. 6 alignment), the aggregation discipline — pull from ADR-0009 body. Council bar 9.5+ before submit.]

## Related mitigations

- `AIR-MIT-SEC-PII-01` — Autonomy Ladder™ Tenant-PII Data-Residency Partitioning (preventative control)
