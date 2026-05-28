# FAILURE-MODES.md — Adversarial, partition, and corruption matrix

**Status:** v0.2.1 (in flight) · companion to ADR-0012 (storage/timestamp/witness seams) and ADR-0013 (MI Proxy verifier chain-of-custody).
**Last reviewed:** 2026-05-28.

> **Patterns are software, not legal advice.** Regulatory citations below are reference mappings; consult counsel for applicability to your control environment. See repo-root [`DISCLAIMER.md`](DISCLAIMER.md).

## How to read this document

The audit chain in this package is **tamper-detecting within its trust boundary by default**. Tamper-*evidence* against an attacker who controls the ledger host requires an external witness — RFC 3161 trusted timestamps (ADR-0012 Seam 2) and/or Sigstore Rekor + OpenTimestamps anchoring (ADR-0012 Seam 3). The matrix below names, per failure-mode class, what gets detected by which mechanism and what the recovery action looks like.

Each detection mechanism resolves to either:
- a fully-qualified callable in this codebase, rendered in the matrix below as `(F)` followed by the dotted Python path — these are enforced by the companion test [`tests/test_failure_modes_matrix.py`](tests/test_failure_modes_matrix.py), or
- an explicit `NOT YET IMPLEMENTED · tracking: ADR-XXXX (or #issue)` marker — the test accepts these and fails the build if either the marker disappears or the named callable goes missing.

The classes are ordered from "in-trust-boundary" (rows 1–3) to "across-trust-boundary" (rows 4–8). The first three are addressable today; the last five are why ADR-0012 and ADR-0013 exist.

---

## Matrix

| # | Class | Example | Detection | Recovery | Regulatory mapping |
|---|---|---|---|---|---|
| 1 | **Storage drift** | Local JSONL truncated; SQLite row UPDATEd out-of-band; S3 object overwritten; EFS rename race | Hash-chain verify-on-read · `(F) cre_agent_audit.governance.audit_chain.AuditLedger.verify_chain` | Reconstruct from external witness anchor if enabled (`(F) cre_agent_audit.governance.witness_anchor.anchor_to_witness`); otherwise quarantine the affected range and surface to operator | SOC 2 CC7.2 (system monitoring); SOX 404 ITGC (audit-trail integrity); FFIEC IT Handbook App J (third-party storage) |
| 2 | **Sequence gap / partition (split-brain)** | Two processes write the same backend concurrently; sequence numbers skip or repeat; one writer wins, the other's entries are lost | Monotonic sequence invariant inside chain verify · `(F) cre_agent_audit.governance.audit_chain.AuditLedger.verify_chain` (rejects non-contiguous `sequence`); plus backend-level conditional write (Postgres unique constraint, DynamoDB conditional write, S3 Object Lock + Versioning) per ADR-0012 § Seam 1 integration shape | Reject the second writer at the backend layer; manual reconcile from the witness anchor or from operator review of the gap | SOC 2 CC7.2; SOX 404 ITGC change management; FFIEC App J § "Concurrency" |
| 3 | **Adversarial replay (in-trust-boundary)** | A previously-appended chain segment is re-inserted later in the same ledger | Sequence monotonicity invariant · `(F) cre_agent_audit.governance.audit_chain.AuditLedger.verify_chain` (re-inserted entries fail prior-hash + sequence checks); within a tamper-evident witness boundary, sequence + timestamp window cross-check is `NOT YET IMPLEMENTED · tracking: ADR-0012-A1 (rfc3161_verify extra)` | Reject the replayed segment at verify time; do not auto-resolve | SOC 2 CC7.2; RFC 3161 (signed timestamps make replay across the witness boundary detectable) |
| 4 | **Timestamp tampering** | System clock skew at append; monotonic counter rewind; deployer with `CAP_SYS_TIME` backdates entries | Within trust boundary: timestamps in chain order are non-decreasing (deployer policy, enforced at append by the `TimestampSource`); across trust boundary: RFC 3161 token verification disagrees with claimed time · `NOT YET IMPLEMENTED · tracking: ADR-0012-A1 (audit-verify extra wires rfc3161_verify.py)` | Quarantine the affected chain segment; flag for review; do not auto-rewrite | RFC 3161 (TSA-signed time); SOC 2 CC7.2; SOX 404 ITGC (time integrity for change records) |
| 5 | **Witness disagreement** | Rekor returns a different inclusion proof than the receipt on file; OpenTimestamps calendar drops the commitment; multiple anchors disagree | Cross-check witness receipts on verify · `NOT YET IMPLEMENTED · tracking: ADR-0012-A1 (witness re-verification on read)`. Today: the `anchor_to_witness` helper writes the receipt back to the ledger as a `decision_type="witness_anchor"` entry; mismatch between two anchor entries with the same `chain_head_anchored` is detectable by operator inspection but not yet by automated verify | Escalate; do not auto-resolve. Operator decides which witness to trust based on substrate posture. | RFC 6962 (Certificate Transparency model); SOC 2 CC7.2 |
| 6 | **Backend permission revocation** | IAM/EFS permissions removed mid-write; SQLite file becomes read-only; S3 bucket policy revokes `PutObject` | Backend `append()` raises a structured exception · `(F) cre_agent_audit.governance.audit_chain.AuditLedger.append` (propagates the `LedgerStore.append` failure); deployers wire alerting in the operational substrate | Fail-closed: refuse to continue the operation that needed the audit entry; surface to operator. The audit chain prefers a missing operation over a missing audit record. | SOC 2 CC7.2 (continuous monitoring); FFIEC App J § "Vendor incident response"; SOX 404 ITGC |
| 7 | **Verifier compromise (Module Integrity)** | The verifier binary or config is swapped for one that returns false-positive `verify_chain()`; the trust boundary is shifted under the operator's feet | Out-of-band MI Proxy attestation on each verify · `(F) cre_agent_audit.governance.mi_proxy.LocalMIProxy.verify_attestation` (ADR-0013); default backend hashes the verifier source + canonical config and signs HMAC-SHA256 with a deployer key; `AuditLedger.verify_chain(mi_proxy=...)` is the opt-in hook | Quarantine the verifier and switch to a backup attested verifier; refuse to return a verified result while attestation fails (fail-closed; raises `IntegrityVerificationError`) | SOC 2 CC7.2 (system monitoring of integrity); SOX 404 ITGC change management (the verifier is privileged software); FFIEC App J (external attestation when out-of-band backend is used); RFC 6962 (Rekor as one external backend option) |
| 8 | **Vendor AI scoring drift** | A third-party scorer silently changes its model; same input produces a different score; vendor patches without changelog | Score-drift emission diff against the audit chain · `(F) cre_agent_audit.governance.vendor_score_gate.InMemoryVendorScoreGate.emit` (ADR-0011 update; v0.2.1); same `input_hash` + same `model_version` + different `score` surfaces as a flagged `decision_type="vendor_score_drift"` chain entry; default posture raises `VendorScoreDriftDetected` so the pipeline halts rather than silently absorbing the change | Flag in audit chain; trigger vendor-review playbook; operator decides whether to quarantine the vendor's signal; `raise_on_drift=False` available for shadow-mode rollouts | FFIEC IT Handbook App J § "Third-party model risk"; SOC 2 CC7.2; ISO/IEC 42001:2023 (AI management system, third-party model controls); EU AI Act (2024/1689) Annex IV § 1(g) (third-party component records) |

## Defaults

| Posture | Default behavior |
|---|---|
| Verifier sees a hash-chain mismatch | Raise `AuditChainTamperError`; refuse to return a verified result |
| Verifier cannot attest its own binary (MI Proxy fail) | Raise `IntegrityVerificationError`; refuse to return a verified result |
| Vendor score gate sees drift | Record a flagged chain entry; let the caller decide whether to proceed |
| Backend `append` raises | Propagate the exception; the audit chain prefers a missing operation over a missing audit record |
| Timestamp source raises | Fallback-to-local-clock is the default for `RFC3161TimestampSource`; set `fallback_to_local_on_failure=False` to fail closed |
| Witness anchor `anchor()` raises | The pattern recovers on the next cron run; the audit is not blocked; deployer instruments alerting |

The framework is **fail-closed for verify-side checks** and **best-effort with explicit fallback for append-side dependencies on external services**. This is intentional: a missing or untrusted verify result is a hard error; a missing trusted-timestamp token on a single entry is a documented, recoverable degradation.

## What this document is NOT

- **Not a threat model for the trust boundary itself.** This matrix describes failures within and across the boundary; the boundary's perimeter (who can `kubectl exec`, who holds the signing key, who can SSH to the ledger host) is the deployer's threat model, not this document's.
- **Not legal advice.** Regulatory citations are reference mappings to help the deployer point counsel and auditors at relevant clauses; applicability is a deployer-and-counsel determination.
- **Not a substitute for vendor due diligence.** Row 8 (vendor scoring drift) detects emission diff; it does not validate the vendor's underlying model, training data, or fair-lending posture.
- **Not a substitute for the operational runbook.** Recovery actions are framework defaults; the deployer's incident-response procedure is where the actual response lives.
- **Not exhaustive.** The matrix names 8 classes the framework addresses. Threat surfaces outside these (DoS against the TSA, regulator subpoena for the signing key, insider revocation of the audit role) are deployer responsibilities by design.

## Related

- ADR-0003 — Internally-consistent hash-chained audit ledger
- ADR-0010 — Audit-chain retention, privilege, and discovery posture
- ADR-0011 — Vendor-output adapter pattern (precursor to the VendorScoreGate in Row 8)
- ADR-0012 — Persistence + timestamp + witness anchor (the three Protocol seams)
- ADR-0013 — MI Proxy (Module Integrity verifier chain-of-custody)
- ADR-0014 — Operator-side AI governance for regulated industries (the category claim that the regulatory-incident replays in `examples/regulatory-incidents/` operationalize)
- `docs/LIMITATIONS.md` — bounded claims for the v0.2.0 baseline this matrix extends

## Motivating named matters

The failure-mode classes above map to the runnable replays under [`examples/regulatory-incidents/`](examples/regulatory-incidents/):

- **Row 8 — Vendor AI scoring drift** maps to [`01_transunion_rental_screening/`](examples/regulatory-incidents/01_transunion_rental_screening/) (FCRA accuracy failures + VendorScoreGate drift signals)
- **Rows 1 + 2 — Storage drift + sequence gap** map to [`02_saferent_voucher_screening/`](examples/regulatory-incidents/02_saferent_voucher_screening/) where the operator could not produce chain-of-custody for the voucher-cohort decisions
- **Row 7 — Verifier compromise** is the conceptual motivator for the MI Proxy hook the replays exercise; [`03_realpage_ongoing_litigation/`](examples/regulatory-incidents/03_realpage_ongoing_litigation/) (framed as ALLEGED conduct) surfaces cohort-coordination signals that an operator-attested verifier would have made operator-visible at decision time

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
