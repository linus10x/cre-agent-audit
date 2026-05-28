# CTRL-013 — MI Proxy (Module Integrity Verifier Chain-of-Custody)

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Before any `verify_chain()` returns a verified result, the verifier attests its own identity via the `MIProxy` Protocol. Default backend `LocalMIProxy` computes SHA-256 over the verifier's source bytes + canonical config and signs HMAC-SHA256 with a deployer-provided key (`CRE_AUDIT_MI_PROXY_KEY`, 32+ bytes). Opt-in backends delegate to SLSA provenance, in-toto attestations, or Sigstore cosign. Attestation failure raises `IntegrityVerificationError`; `verify_chain()` refuses to return — fail-closed. |
| **Control objective** | Detect verifier compromise — the trust-boundary attack the bare audit chain cannot detect. A compromised verifier returning false-positive `verify_chain()` across an otherwise-internally-consistent chain is the failure shape this control prevents. Privileged-software change-management (SOX 404 ITGC) made testable. |
| **Control owner (typical)** | Chief Information Security Officer (HMAC key lifecycle + key rotation policy + external attestation backend selection) + VP Engineering (verifier deployment + attestation wiring) + Compliance (SOX 404 ITGC change-management evidence for the verifier as privileged software) |
| **Frequency** | Per-verify (continuous — every `AuditLedger.verify_chain(mi_proxy=...)` call) + scheduled (deployer-chosen attestation refresh cadence; `max_age_seconds` default 86_400 — one day) + event-driven (key rotation; new verifier deployment) |
| **Type** | Preventive (fail-closed) + Detective (attestation mismatch reveals divergence between deployed verifier and approved one) + Forensic (attestation records establish what verifier was in effect at a given time) |
| **Evidence of operation** | HMAC key custody record (key never embedded in repo or runtime artifact); deployment-time attestation log; per-verify attestation outcomes; key-rotation log; SLSA / in-toto / cosign attestation chain when opt-in external backend wired. |
| **ADR** | [`docs/adr/0013-mi-proxy-module-integrity.md`](../adr/0013-mi-proxy-module-integrity.md) |
| **Implementation** | [`src/cre_agent_audit/governance/mi_proxy.py`](../../src/cre_agent_audit/governance/mi_proxy.py) — `MIProxy` Protocol + `Attestation` dataclass + `LocalMIProxy` HMAC default backend + `IntegrityVerificationError` + `MIProxyKeyMissingWarning` |

## Test of design

Code review: `LocalMIProxy(signing_key=)` refuses keys shorter than 32 bytes (`ValueError` on construction); `LocalMIProxy.from_env()` emits `MIProxyKeyMissingWarning` when the env var is absent and signs with a zero key so subsequent verifies against a real-keyed proxy fail closed — non-suppressible by design; `verify_attestation()` checks signature + freshness (`max_age_seconds`) + current source-hash; `AuditLedger.verify_chain(mi_proxy=...)` calls `mi_proxy.attest()` then `mi_proxy.verify_attestation()` BEFORE walking the chain and raises `IntegrityVerificationError` on failure.

## Test of operating effectiveness

Quarterly: (1) verify the deployed verifier's source hash matches the most-recent approved-change attestation in the change-management system; (2) sample `verify_chain(mi_proxy=...)` invocations from the prior period and confirm the attestation outcome matches the deployed verifier identity; (3) confirm the HMAC key has rotated per policy. Annual: key-rotation exercise + verifier-replacement exercise (deploy a new verifier; confirm the prior attestation refuses; confirm the new attestation validates).

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | GOVERN 1.5 (system integrity) · MEASURE 2.7 (drift detection) · MANAGE 2.3 (response to issues) |
| ISO/IEC 42001:2023 Annex A | A.8.4 (operational controls — integrity of operational software) · A.12.4.1 (event logging) · A.14.2 (security in development and support processes — secure deployment) |
| COSO ICAIR component | Control Environment · Control Activities · Information & Communication |
| Big-4 standard AI-controls taxonomy | Privileged-Software Change Management · Code-Integrity Attestation · Operator-Side Verifier Validation |
| Primary-source standards | RFC 6962 (Certificate Transparency — Sigstore Rekor as one external backend option) · SOX 404 ITGC (change management for privileged software) · FFIEC IT Handbook Appendix J (third-party attestation when opt-in backend used) |

## Limitations and compensating controls

The HMAC default backend protects against in-process verifier swap but not against an attacker with read-access to the HMAC key. Asymmetric signatures (SLSA / cosign + Fulcio certificate chain) close that gap; the deployer pays the dependency cost on their side, not in this package. Runtime monkey-patching of `verify_chain` via `setattr(module, ...)` is not detected by the source-hash backend — defending against runtime monkey-patching requires OS-level integrity measurement (Linux IMA, macOS Endpoint Security, Windows VBS) and is out of scope. The MI Proxy itself is part of the trust boundary; recursion stops at the operator's signing key for `LocalMIProxy` and at the attestation service's root of trust for opt-in backends — the package documents this and does not pretend to close infinite regress.

## Related

- ADR-0013 (full architectural reasoning + alternatives considered)
- ADR-0003 (the verifier this control protects)
- ADR-0012 (substrate-level tamper-evidence — this control adds verifier-level tamper-detection on top)
- CTRL-003 (the audit-chain control this one's verifier validates)
- CTRL-012 (substrate + timestamp + witness control)
- [`FAILURE-MODES.md`](../../FAILURE-MODES.md) Row 7 (Verifier compromise — the failure mode this control addresses)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
