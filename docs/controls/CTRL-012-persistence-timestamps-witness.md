# CTRL-012 — Persistence, Trusted Timestamps & External Witness Anchoring

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Three composable Protocol seams in the audit-chain layer: (1) `LedgerStore` — append-only persistence with operator-chosen substrate (Postgres + WAL, S3 + Object Lock, DynamoDB conditional writes); (2) `TimestampSource` — RFC 3161 trusted-timestamp tokens bound into the chain hash; (3) `WitnessRegister` — periodic anchoring of the chain-head digest to Sigstore Rekor + OpenTimestamps, with the receipt written back into the same chain it protects. |
| **Control objective** | Tamper-evidence beyond the trust boundary the framework can enforce alone — the chain becomes verifiable against external public records (the TSA's signing chain; the Rekor public transparency log; the Bitcoin chain via OpenTimestamps). Closes the "internally consistent but not adversarially tamper-evident" limitation of the bare audit ledger (ADR-0003 / CTRL-003). |
| **Control owner (typical)** | VP Engineering (substrate operation + seam wiring) + Chief Information Security Officer (witness-anchor cron + alerting) + Compliance (retention + substrate-WORM compliance under SEC 17a-4 / SOX 404 ITGC) |
| **Frequency** | Per-decision (continuous on every `append()` — `LedgerStore.append` + `TimestampSource.stamp`) + scheduled (witness-anchor cron; recommended weekly minimum) + event-driven (TSA outage fallback alert) |
| **Type** | Preventive (substrate-level immutability + RFC 3161 token signing) + Detective (witness-anchor cross-check + verify_chain) + Forensic (chain head provable against external public records) |
| **Evidence of operation** | Substrate WORM-compliance documentation; deployed TSA configuration + RFC 3161 token store; periodic witness-anchor receipts written back as `decision_type="witness_anchor"` chain entries; `verify_chain()` reports + signature-chain verification reports when the optional `audit-verify` extra ships. |
| **ADR** | [`docs/adr/0012-persistence-witness-timestamp-pattern.md`](../adr/0012-persistence-witness-timestamp-pattern.md) |
| **Implementation** | [`src/cre_agent_audit/governance/ledger_store.py`](../../src/cre_agent_audit/governance/ledger_store.py) + [`ledger_store_sqlite.py`](../../src/cre_agent_audit/governance/ledger_store_sqlite.py) + [`ledger_store_jsonl.py`](../../src/cre_agent_audit/governance/ledger_store_jsonl.py) + [`timestamp_source.py`](../../src/cre_agent_audit/governance/timestamp_source.py) + [`witness_anchor.py`](../../src/cre_agent_audit/governance/witness_anchor.py) + `rfc3161_codec.py` |

## Test of design

Code review: `LedgerStore` Protocol surface is append-only-by-absence (no update / delete / truncate / set methods); the in-repo backends do not expose mutation; the `RFC3161TimestampSource` has a configurable `fallback_to_local_on_failure` (default True so a TSA outage does not stall the audit pipeline; set False to fail closed); the `WitnessRegister.anchor()` helper writes the receipt back into the chain as a `decision_type="witness_anchor"` entry so tampering with the anchor record requires tampering with every entry after it.

## Test of operating effectiveness

Quarterly: pick a date in the prior period; (1) verify the substrate's WORM configuration was in effect for that date; (2) verify the RFC 3161 token for entries from that date validates against the TSA's signing certificate (requires `audit-verify` extra); (3) verify the chain-head digest for that date matches the Rekor inclusion proof and/or the OpenTimestamps Bitcoin attestation. Annual: end-to-end exercise reconstructing the chain from a public-record-only starting position.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | MEASURE 2.7 (monitoring drift) · MANAGE 2.3 (response to issues) · GOVERN 6.1 (third-party transparency) |
| ISO/IEC 42001:2023 Annex A | A.12.4.1 (event logging) · A.12.4.2 (protection of log information) · A.18.1.3 (protection of records) |
| COSO ICAIR component | Control Activities · Information & Communication · Monitoring |
| Big-4 standard AI-controls taxonomy | Tamper-Evident Records · External Attestation · Chain-of-Custody |
| Primary-source standards | RFC 3161 (TSP) · RFC 6962 (Certificate Transparency) · SEC 17a-4 (broker-dealer WORM) |

## Limitations and compensating controls

Signature-chain verification of stored RFC 3161 tokens requires the `audit-verify` extra (forthcoming in v0.2.2). The opt-in `RekorWitness` and `OpenTimestampsWitness` create dependencies on external services at anchoring time; deployers instrument the anchor cron with retry + alerting (the pattern recovers — the next cron run anchors the new head — but the deployer's monitoring catches sustained anchor failures). Multi-process write contention is the deployer's substrate problem; the Protocol assumes the deployer's substrate enforces single-writer-or-conditional-write semantics.

## Related

- ADR-0012 (full architectural reasoning + three Protocol seams)
- ADR-0003 (the chain this control extends with substrate + timestamp + witness)
- ADR-0013 (MI Proxy makes the verifier itself tamper-detecting on top of this control's tamper-evidence)
- CTRL-003 (the audit-chain control this one extends)
- CTRL-013 (MI Proxy verifier-integrity control)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
