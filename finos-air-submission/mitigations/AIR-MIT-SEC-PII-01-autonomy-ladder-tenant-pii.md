---
mitigation_id: AIR-MIT-SEC-PII-01
title: "Autonomy Ladder™ Tenant-PII Data-Residency Partitioning — LegalBasis taxonomy + cross-jurisdiction veto"
control_type: preventative
mitigates_risks:
  - AIR-SEC-010
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
reference_implementation: "https://github.com/linus10x/cre-agent-audit/blob/main/src/cre_agent_audit/governance/tenant_pii_residency.py"
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0009-tenant-pii-data-residency.md"
license: MIT
---

## Summary

[TODO Week 7: full body per ADR-0009 — 5 RESIDENCY-* veto codes · LegalBasis taxonomy aligned with GDPR Art. 6 (CONSENT · CONTRACT · LEGITIMATE_INTEREST · LEGAL_OBLIGATION) · CrossJurisdictionRequest typed object · jurisdiction partition at storage layer · vague-purpose detection · GC sign-off for any bypass.]

Reference Python implementation at `src/cre_agent_audit/governance/tenant_pii_residency.py`. MIT-licensed.
