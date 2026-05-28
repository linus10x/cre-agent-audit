# CTRL-009 — Tenant PII Data Residency Partitioning

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Partition tenant data by jurisdiction at the storage layer; gate every cross-jurisdiction read with a `LegalBasis` tag and recorded purpose at write-time. |
| **Control objective** | Enforce data-residency requirements at write-time (not read-time) so violations cannot accumulate; satisfy GDPR Art. 6 + CCPA/CPRA + state tenant-data statutes. |
| **Control owner (typical)** | Chief Information Security Officer + General Counsel (joint authority per ADR-0002 RACI); Data Protection Officer (where applicable) |
| **Frequency** | Per-read (continuous) + per-cross-jurisdiction request (LegalBasis check) |
| **Type** | Preventive (blocks untagged cross-jurisdiction reads) + Detective (records every cross-jurisdiction request) |
| **Evidence of operation** | `CrossJurisdictionRequest` records on every cross-boundary read; `LegalBasis` tags on every request; logged exceptions require GC sign-off |
| **ADR** | [`docs/adr/0009-tenant-pii-residency.md`](../adr/0009-tenant-pii-data-residency.md) |
| **Implementation** | [`src/cre_agent_audit/governance/tenant_pii_residency.py`](../../src/cre_agent_audit/governance/tenant_pii_residency.py) |

## Test of design

Code review: confirm the veto fires on cross-jurisdiction reads without a `LegalBasis` tag; confirm vague-purpose detection rejects insufficient purpose strings.

## Test of operating effectiveness

Quarterly: sample 20 cross-jurisdiction requests; verify each has a LegalBasis tag and a non-vague purpose; review any GC-signed exception logs.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | MANAGE 4.3 (errors corrected) · MAP 2.3 · MEASURE 2.10 (privacy) |
| ISO/IEC 42001:2023 Annex A | A.5.34 (privacy and protection of PII) · A.5.36 (compliance) · A.18.1.4 (privacy and protection of PII) |
| COSO ICAIR component | Control Activities · Risk Assessment |
| Big-4 standard AI-controls taxonomy | Data Lineage · Third-Party |

## Limitations and compensating controls

Does not cover encryption-at-rest configuration (separate IT control); does not cover access-control to partitioned data (IAM owns that); does not satisfy GDPR Art. 17 erasure on its own; does not address Hague Convention / cross-border-discovery scenarios (see ADR-0010).

## Related

- ADR-0009 (full architectural reasoning)
- ADR-0003 (every event of this control writes to the audit chain)
- ADR-0010 (retention / privilege / discovery posture for evidence this control generates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
