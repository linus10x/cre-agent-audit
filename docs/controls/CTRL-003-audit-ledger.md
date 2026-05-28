# CTRL-003 — Internally-Consistent Hash-Chained Audit Ledger

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Append every consequential decision (executed + vetoed) to an SHA-256-linked ledger; expose chain-head digest for external witness anchoring. |
| **Control objective** | Decision-trail recoverability for regulator, audit, litigation, and operating-partner inquiry; forward integrity within a deployment. |
| **Control owner (typical)** | VP Engineering (ledger operation) + Chief Information Security Officer (witness-anchor cadence) + General Counsel (retention + privilege per ADR-0010) |
| **Frequency** | Per-decision (continuous append) + periodic (chain-head digest publication to external witness, recommended weekly) |
| **Type** | Detective (records what happened) + Forensic (chain integrity supports post-incident reconstruction) |
| **Evidence of operation** | The ledger itself; the witness-anchor publication record (OpenTimestamps / Sigstore Rekor / regulator log); periodic `verify_chain()` reports |
| **ADR** | [`docs/adr/0003-audit-ledger.md`](../adr/0003-hash-chain-audit.md) |
| **Implementation** | [`src/cre_agent_audit/governance/audit_chain.py`](../../src/cre_agent_audit/governance/audit_chain.py) |

## Test of design

Code review: `verify_chain()` detects both self_hash and prior_hash inconsistencies; chain_head() returns the genesis sentinel for empty ledger.

## Test of operating effectiveness

Quarterly: produce the chain-head digest for a randomly-selected date in the prior period; verify it matches the witness-anchor publication for that date.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | MEASURE 2.1 (system performance + impact monitored) · MANAGE 4.3 (errors corrected) |
| ISO/IEC 42001:2023 Annex A | A.12.4.1 (event logging) · A.12.4.2 (protection of log information) · A.12.4.3 (administrator and operator logs) |
| COSO ICAIR component | Information & Communication · Monitoring |
| Big-4 standard AI-controls taxonomy | Operational Monitoring · Data Lineage |

## Limitations and compensating controls

Internally-consistent, NOT adversarially tamper-evident on its own — requires external witness anchor (see ADR-0003 Audit Evidence Properties); in-memory persistence in reference implementation (production needs pluggable backend); local-clock timestamps (RFC 3161 TSA recommended).

## Related

- ADR-0003 (full architectural reasoning)
- ADR-0003 (every event of this control writes to the audit chain)
- ADR-0010 (retention / privilege / discovery posture for evidence this control generates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
