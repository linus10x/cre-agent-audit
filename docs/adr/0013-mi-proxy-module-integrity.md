# ADR-0013 · MI Proxy — Module Integrity Verifier Chain-of-Custody

**Status:** Proposed — v0.2.1 (in flight); will become Accepted on PR #31 merge
**Date:** 2026-05-28
**Decider:** Kunjar Bhaduri
**Pairs with:** ADR-0012 (persistence / timestamps / witness anchor seams)

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

ADR-0012 closed three v0.2.1 deferred items by introducing pluggable persistence (`LedgerStore`), trusted timestamps (`TimestampSource`), and external witness anchoring (`WitnessRegister`). Each of those Protocol seams pushes part of the trust boundary outward — to the substrate (Postgres, S3, DynamoDB), to the TSA (FreeTSA, DigiCert), and to the witness log (Rekor, OpenTimestamps).

There is one trust-boundary asset that ADR-0012 explicitly does not address: **the verifier itself.**

`AuditLedger.verify_chain()` is the function that consumers, auditors, and downstream regulators rely on to attest to the integrity of the chain. If the verifier binary or its configuration is swapped — by a malicious operator, by a supply-chain attack on the package, by an undetected drift between the deployed verifier and the one approved through change management — then a compromised verifier can return false-positive `verify_chain()` across the entire audit chain. The hash-chain itself remains internally consistent; the *verifier* is the lie.

FAILURE-MODES.md § Row 7 (Verifier compromise) names this class. The detection mechanism it points at is the subject of this ADR.

The constraint that bounds every choice here is the same as ADR-0012: **the package's Zero-Runtime-Dependencies posture is load-bearing.** The default MI Proxy backend must work stdlib-only. External attestation (SLSA / in-toto / Sigstore cosign) is opt-in via `[project.optional-dependencies]` and never imported by `cre_agent_audit/__init__.py`.

## Decision

Introduce a `MIProxy` Protocol with two methods and ship a stdlib-only default backend, plus a `verify_chain` hook that fails closed when attestation fails.

### Protocol surface

```python
class MIProxy(Protocol):
    def attest(self, component_id: str) -> Attestation: ...
    def verify_attestation(self, attestation: Attestation) -> bool: ...
```

```python
@dataclass(frozen=True)
class Attestation:
    component_id: str          # e.g. "cre_agent_audit.governance.audit_chain"
    sha256_hex: str            # hash over the verifier source + relevant config
    timestamp_iso: str         # UTC ISO 8601
    signature_b64: str         # signature over (component_id, sha256_hex, timestamp_iso)
    backend_id: str            # "local-hmac" | "slsa" | "in-toto" | "sigstore-cosign"
```

The Protocol is two methods on purpose. `attest()` produces a signed assertion about *this* verifier at *this* moment. `verify_attestation()` re-validates an assertion at verify time. The two are split so that downstream backends can produce attestations out-of-band (CI build pipeline, SLSA provenance generator) and the runtime only needs the re-validation path.

### Default backend — `LocalMIProxy`

Ships in `src/cre_agent_audit/governance/mi_proxy.py`:

- Reads the verifier module's source bytes via `importlib.resources` (no `inspect.getsource` brittleness).
- Computes SHA-256 over `(source_bytes + canonical_config_bytes)`.
- Signs `(component_id, sha256_hex, timestamp_iso)` with HMAC-SHA256 using a static key loaded from the environment variable `CRE_AUDIT_MI_PROXY_KEY` (32+ bytes, base64 or hex).
- If the key is absent: emits an explicit `MIProxyKeyMissingWarning`, signs with a zeroed key, and any subsequent `verify_attestation()` against a real key fails closed. The warning is non-suppressible: the verifier refuses to silently degrade.
- Attestations are time-bounded: `verify_attestation()` rejects attestations older than `max_age_seconds` (default 86_400 — one day). Override per deployer policy.
- `backend_id="local-hmac"`.

The default is symmetric-HMAC, not asymmetric. The reason: HMAC stays stdlib; asymmetric signatures pull in `cryptography`, which violates Zero-Deps. Deployers who need asymmetric attestation use the opt-in backend.

### Opt-in backend — external attestation

A second backend (not shipped in v0.2.1, documented for the integration shape) delegates to an external attestation service:

- **SLSA provenance** — read `provenance.json` from a known-location artifact registry; verify against the build pipeline's signing certificate.
- **in-toto** — verify a layout against the deployed verifier binary.
- **Sigstore cosign** — verify a `cosign sign-blob` signature against the Fulcio-issued certificate, with Rekor inclusion proof.

These backends ship under the `[project.optional-dependencies] attestation` extra in a forthcoming release; the package never imports them.

### Hook into `verify_chain`

`AuditLedger.verify_chain()` accepts an optional `mi_proxy: MIProxy | None = None` parameter:

- If `mi_proxy is None`: default behavior is preserved (v0.2.0 / ADR-0012 semantics). Existing callers see no change.
- If `mi_proxy is not None`: before walking the chain, the verifier calls `mi_proxy.attest(component_id="cre_agent_audit.governance.audit_chain")` and `mi_proxy.verify_attestation(...)`. If attestation fails, raise `IntegrityVerificationError` and **refuse to return a verified result**. Fail-closed.

The hook is opt-in to preserve v0.2.0 backward compatibility. The recommended posture in deployment documentation (forthcoming ADR-0012-A2) is to wire `mi_proxy` whenever the audit chain is consumed by an external auditor or regulator.

## Consequences

**Positive.**
- Closes FAILURE-MODES.md Row 7 with a real, fail-closed detection mechanism.
- Zero-Deps badge intact. Default backend uses `hashlib`, `hmac`, `base64`, `importlib.resources` — all stdlib.
- The Protocol surface is small enough that downstream deployers wire SLSA / in-toto / cosign backends in ~80 LOC against the same interface.
- Existing `AuditLedger.verify_chain()` callers are unaffected. The hook is opt-in.

**Negative.**
- HMAC keys must be managed by the deployer. The package does not ship key-rotation tooling; that is a deployment concern. The `MIProxyKeyMissingWarning` and fail-closed-on-mismatch posture surface the problem loudly when keys are misconfigured, but the deployer owns the lifecycle.
- The default backend protects against in-process verifier swap but not against an attacker with read-access to the HMAC key. Asymmetric signatures (SLSA / cosign) close that gap; the deployer pays the dependency cost on their side, not in this package.
- The verifier's "component_id" is a string; the default backend hashes the module's source file. If the deployer monkey-patches `verify_chain` at runtime via `setattr(module, ...)`, the hash will not change. This is a documented limitation; defending against runtime monkey-patching requires a different posture (sandboxed verifier process, kernel-level integrity measurement) that is out of scope.
- Adds approximately 5ms per `verify_chain()` call with the local backend. Measured on Apple Silicon; reproducible via `tests/test_mi_proxy.py::test_attest_latency_local_backend`.

**Architectural.**
- The MI Proxy is the **second** out-of-band trust seam in the audit stack. The first is the witness anchor (ADR-0012 Seam 3), which makes the chain history tamper-evident. The MI Proxy makes the verifier itself tamper-detecting. Together they close the loop on "is the chain real and is the function reading it real."
- The Protocol-with-default-backend pattern matches ADR-0012's three seams. The same downstream-deployer story applies: small Protocol surface, stdlib reference, opt-in stronger backends.

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| Trust the verifier implicitly | Assumes a trust boundary the framework cannot enforce. The whole point of v0.2.1 is to make that boundary explicit and testable. |
| Require external attestation (SLSA / cosign) as the default | Forces an infra dependency on every adopter. Breaks Zero-Deps. A v0.2.1 deployer running on a single VM should be able to use the framework end-to-end with stdlib only. |
| Merkle tree of verifier state over time | Gives the *history* of verifier identities, not the answer to "is THIS binary the one we approved." The MI Proxy answers the question; a Merkle log of attestations is a derivative artifact and can be built on top. |
| Embed the verifier hash directly in `AuditEntry` | Couples every chain entry to a verifier-state artifact. Forces re-attestation per entry instead of per verify. Inflates the chain. The MI Proxy fires per `verify_chain()` call, which is the right cadence — verify is the action that matters. |
| Sign the chain head with an asymmetric key at append time | A different pattern (signed-log, à la Certificate Transparency). Useful, but orthogonal: it attests to the *chain*, not the *verifier*. The witness anchor in ADR-0012 covers the signed-log direction. |
| Require the deployer to wire OS-level integrity measurement (IMA, Secure Boot) | The right answer in regulated environments, but the package cannot ship it; OS-level integrity is the deployer's substrate, not the library's. The MI Proxy is the layer the library can own. |

## What this does NOT cover

- **Asymmetric default.** The default backend is HMAC. Deployers who require non-repudiation (asymmetric verification by a third party) wire the opt-in backend.
- **Key rotation.** The deployer owns the HMAC key lifecycle. The package only requires that the key be present and at least 32 bytes; it does not rotate, escrow, or manage keys.
- **Runtime monkey-patching defense.** A deployer with code-execution privilege on the verifier host can replace `verify_chain` at runtime in ways the source-hash backend does not detect. Defending against this requires OS-level integrity measurement (Linux IMA, macOS Endpoint Security, Windows VBS) — out of scope for the package.
- **Verifier-of-the-verifier.** The MI Proxy attests to the verifier. The MI Proxy itself is part of the trust boundary. Recursion stops at the operator's signing key for the local backend, and at the attestation service's root of trust for the opt-in backends. The package documents this and does not pretend to close infinite regress.
- **Integration with the witness anchor.** A future ADR-0013-A1 may write the MI Proxy attestation result as a `decision_type="verifier_attestation"` entry in the audit chain, binding the verifier's identity into the chain it verifies. Out of scope for the v0.2.1 deliverable.

## Regulatory mapping

- **SOC 2 CC7.2** — *System Monitoring*. The verifier is a privileged component in the audit-trail pipeline; its integrity is a CC7.2 expectation. The MI Proxy is the detection mechanism for that expectation.
- **SOX 404 ITGC** — *Change Management*. The verifier is privileged software; changes to it must go through approved change. The MI Proxy fails closed when the deployed verifier diverges from the attested one — that is the technical control behind the change-management policy.
- **FFIEC IT Handbook App J** — *Third-Party Risk*. When the opt-in backend delegates to an external attestation service (SLSA, cosign + Fulcio), the third-party-attestation expectations of App J apply to that service. The package documents the integration; the deployer owns the third-party risk assessment.
- **ISO/IEC 42001:2023** — *AI Management System*. § 8.4 (Operational Controls) expects integrity controls on the AI system's operational software. The verifier qualifies; the MI Proxy is the integrity control.
- **EU AI Act (2024/1689) Annex IV § 1(g)** — record-keeping for third-party components. The opt-in backend's attestation chain is the record.
- **RFC 6962** — *Certificate Transparency*. The opt-in Sigstore backend uses Rekor, which is a CT-style log. The trust model is the same: an external append-only log records what was attested at time T; later attempts to claim a different attestation contradict the log.

## Failure modes addressed

See [`FAILURE-MODES.md`](../../FAILURE-MODES.md) Row 7 ("Verifier compromise"). This ADR is the named tracking record that resolves the deferred marker on that row.

## Related

- ADR-0003 — Internally-consistent hash-chained audit ledger (the verifier this ADR protects)
- ADR-0012 — Persistence / timestamps / witness anchor seams (companion ADR; same Protocol-with-stdlib-default pattern)
- FAILURE-MODES.md — Row 7 (Verifier compromise) is what this ADR closes

## Implementation notes

v0.2.1 ships:
- `src/cre_agent_audit/governance/mi_proxy.py` — `MIProxy` Protocol + `Attestation` dataclass + `LocalMIProxy` default backend + `IntegrityVerificationError` + `MIProxyKeyMissingWarning`
- Hook in `src/cre_agent_audit/governance/audit_chain.py` — `verify_chain(mi_proxy=None)` parameter; fail-closed when attestation fails
- `tests/test_mi_proxy.py` — round-trip, tampered binary, missing key, stale attestation, verifier-hook integration

v0.2.1 tracked for completion (deferred to subsequent ADRs):
- ADR-0013-A1 — External attestation backends (SLSA / in-toto / Sigstore cosign) behind `[attestation]` extra
- ADR-0013-A2 — `decision_type="verifier_attestation"` chain entry binding MI Proxy result into the chain
- ADR-0012-A2 — Deployment guidance for when to wire MI Proxy (regulated-substrate consumers, auditor-facing verifiers)

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
