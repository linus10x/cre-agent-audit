# CTRL-007 — Lease-Abstraction Provenance Chain

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Require every AI-extracted lease clause to carry a typed `Provenance` object (document hash · page · paragraph · OCR + extraction confidence · model version · reviewer signature for material clauses). |
| **Control objective** | Litigation-discovery defensibility for AI-extracted lease terms; close the 'how was this clause extracted' question by construction. |
| **Control owner (typical)** | VP Engineering (provenance generation) + Lease Administration lead (reviewer signatures on material clauses) + General Counsel (annual review of veto thresholds) |
| **Frequency** | Per-clause (continuous as leases are abstracted) |
| **Type** | Preventive (blocks system-of-record write on missing provenance) + Detective (records every veto'd clause) |
| **Evidence of operation** | `Provenance` objects on every extracted clause; reviewer signatures on material clauses; veto'd clauses logged to audit chain with full provenance |
| **ADR** | [`docs/adr/0007-lease-provenance.md`](../adr/0007-*.md) |
| **Implementation** | [`src/cre_agent_audit/governance/lease_provenance.py`](../../src/cre_agent_audit/governance/lease_provenance.py) |

## Test of design

Code review: confirm the typed `ExtractedClause` carries `Provenance` and that the veto fires on incomplete or low-confidence material clauses.

## Test of operating effectiveness

Quarterly: sample 20 material-clause abstractions; verify each has a reviewer signature; verify hash-mismatch + stale-model + low-confidence vetoes fired in the period and were resolved.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | MEASURE 2.1 (system performance monitored) · MANAGE 4.3 (errors corrected) |
| ISO/IEC 42001:2023 Annex A | A.8.2.2 (information labelling) · A.12.4.1 (event logging) · A.18.1.3 (protection of records) |
| COSO ICAIR component | Control Activities · Monitoring |
| Big-4 standard AI-controls taxonomy | Data Lineage · Model Validation |

## Limitations and compensating controls

Requires vendor pipelines to expose clause-level provenance (most vendor pipelines do not natively — see `docs/vendor-clauses/abstraction.md` for contractual SLA template); English only in v0.2.0; OCR confidence is vendor-supplied (operator cannot validate it independently).

## Related

- ADR-0007 (full architectural reasoning)
- ADR-0003 (every event of this control writes to the audit chain)
- ADR-0010 (retention / privilege / discovery posture for evidence this control generates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
