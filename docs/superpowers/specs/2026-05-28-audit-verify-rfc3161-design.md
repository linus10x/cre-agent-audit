# Spec — `audit-verify` Extra: RFC 3161 Signature-Chain Verification · 2026-05-28

**Status:** Approved (brainstorming → design → spec) 2026-05-28
**Owner:** Kunjar Bhaduri
**Repo:** `linus10x/cre-agent-audit` (`main` at `dfd388a`)
**Version target:** `0.2.2` final (this is one of the three v0.2.2 close items)
**Closes:** ADR-0012-A1 forward-reference — *`rfc3161_verify.py` signature-chain verification under the `audit-verify` extra*
**Pairs with:** [`docs/superpowers/specs/2026-05-28-fair-housing-mi-threshold-detector-design.md`](2026-05-28-fair-housing-mi-threshold-detector-design.md) (the other v0.2.2 close item)

## Goal

Close the ADR-0012-A1 forward-reference. v0.2.1's `RFC3161TimestampSource` stores opaque-encoded TSR tokens in `AuditEntry.timestamp_token_b64`; the framework can produce these tokens but cannot independently re-verify them at audit time. Ship `rfc3161_verify.py` behind a new `[audit-verify]` optional dependency so deployers can validate stored TSR tokens against the TSA's signing chain at any future point, satisfying the FFIEC App J + SOX 404 ITGC + SEC 17a-4 audit-evidence reverification expectations.

## Non-goals

- Not a re-implementation of `cryptography`'s X.509 chain validation (we use the library)
- Not a TSA client (that's `RFC3161TimestampSource` from v0.2.1)
- Not a TSR-builder (that's `rfc3161_codec.py` from v0.2.1)
- Not a CRL/OCSP revocation checker (defer; the deployer's environment policy chooses)
- Not coupled to any specific TSA (operator brings their trusted-root bundle)

## Why a separate extra

`pyca/cryptography` is a substantial dependency (compiled, OpenSSL-linked, ~10MB install). The framework's Zero-Runtime-Dependencies posture is load-bearing for the rest of the audit-chain code — operators who never need TSR re-verification should not be forced to install `cryptography`. The optional-extras pattern keeps the base install clean while opting deployers who DO need verification into the heavy dependency on their own terms.

## Voice + framing constraints (CLAUDE.md)

- Operator-with-leverage register; "the operator chooses what's trusted" framing
- Primary-source standards citations (RFC 3161 verbatim section references; X.509 / RFC 5280)
- Disclaimer line on every regulatory-adjacent file
- No banned terms; no banned names
- Honesty: "Verification at time T-future is contingent on the TSA's signing certificate validity at time T-past — historical-trust mode opt-in"

## Architecture

### New module: `src/cre_agent_audit/governance/rfc3161_verify.py`

Behind the `[audit-verify]` extra. Module-level `from cryptography import ...` — if extra not installed, importing the module raises an explicit `ImportError` with the install hint.

Four types:

```python
@dataclass(frozen=True)
class TSRVerificationResult:
    """Outcome of TSR token re-verification.

    `verified=True` means the signature checks, the certificate chain
    terminates at one of the trusted_tsa_certs, and (unless
    accept_expired_at_verify_time=True) the TSA cert was valid at
    verification time. `errors` is empty on success, populated with
    specific reasons on failure.
    """
    verified: bool
    timestamp: Optional[datetime]    # TSA-attested time; None if parse failed
    tsa_subject: Optional[str]       # TSA cert subject DN
    errors: tuple[str, ...]
```

```python
class TSRParseError(ValueError): ...
```

```python
def verify_tsr_token(
    *,
    token_b64: str,
    trusted_tsa_certs: list[bytes],
    accept_expired_at_verify_time: bool = False,
) -> TSRVerificationResult:
    """Re-verify a stored RFC 3161 TSR token.

    Args:
        token_b64: base64-encoded TSR token from AuditEntry.timestamp_token_b64
        trusted_tsa_certs: list of DER- or PEM-encoded TSA root + intermediate
            certificates the deployer has chosen to trust
        accept_expired_at_verify_time: if True, accept tokens whose TSA cert
            has expired SINCE the token was issued but was valid at issuance.
            Honors the "valid at issuance is sufficient" deployer policy.

    Returns:
        TSRVerificationResult capturing the outcome.

    Raises:
        TSRParseError: token bytes are not valid DER ASN.1
    """
```

```python
def verify_audit_entry_token(
    *,
    entry: AuditEntry,
    trusted_tsa_certs: list[bytes],
    accept_expired_at_verify_time: bool = False,
) -> TSRVerificationResult:
    """Convenience wrapper: verify the TSR stored in an AuditEntry.

    Returns TSRVerificationResult(verified=True) for entries whose
    timestamp_token_b64 is None — token-free entries are not invalidated
    by their lack of a token (v0.2.0 token-free ledgers continue to work).
    """
```

### `pyproject.toml` change

```toml
[project.optional-dependencies]
audit-verify = ["cryptography>=42"]
```

The existing `[project.optional-dependencies] dev` keeps its current shape; CI's existing `pip install -e ".[dev]"` is extended to `pip install -e ".[dev,audit-verify]"` so the test suite covers the new module.

### Modified ADR: `docs/adr/0012-persistence-witness-timestamp-pattern.md`

The "Implementation notes" footer ADR-0012-A1 forward-reference is updated to point at the now-shipped `rfc3161_verify.py`. A new "Verification" subsection documents the verification flow.

### Tests

`tests/test_rfc3161_verify.py`:

- Skip the entire module if `cryptography` not importable
- `conftest.py`-generated test fixture: build a synthetic TSA root cert + intermediate cert + sign a TSR with the intermediate at test-runtime using `cryptography` (no committed binaries — fixture regenerates each run)
- Round-trip: TSQ → TSA-signed TSR → `verify_tsr_token()` returns `verified=True`
- Tamper detection: mutate one byte of the signed TSR → `verify_tsr_token()` returns `verified=False` with "signature" in errors
- Untrusted chain: verify with empty `trusted_tsa_certs` → `verified=False`
- Expired-cert handling: generate TSA cert with expired `not_after`; verify with `accept_expired_at_verify_time=False` → fails; with `True` → succeeds
- `verify_audit_entry_token` with `timestamp_token_b64=None` → `verified=True` (token-free entries valid)
- Parse error: garbage bytes → `TSRParseError`

`tests/conftest.py` is updated with a `_synthetic_tsa()` helper that runs at import time only if `cryptography` is present.

### Modified CI

`.github/workflows/test.yml` extends the `pip install -e ".[dev]"` step to `pip install -e ".[dev,audit-verify]"` so the new test module runs in CI.

## Data flow

```
At audit-evidence verification time (deployer code, audit-verify extra installed):
    from cre_agent_audit.governance.rfc3161_verify import verify_audit_entry_token

    trusted_certs = load_my_trusted_tsa_bundle()  # deployer's choice

    for entry in ledger.entries:
        result = verify_audit_entry_token(
            entry=entry,
            trusted_tsa_certs=trusted_certs,
        )
        if not result.verified:
            # Surface this through the operator's audit-evidence pipeline
            log_verification_failure(entry, result.errors)
```

## Error handling

- Token b64 not valid base64 → `TSRParseError`
- Token bytes not valid DER → `TSRParseError`
- Empty `trusted_tsa_certs` list → `TSRVerificationResult(verified=False, errors=["no trusted TSA certificates supplied"])`
- Signature mismatch → `TSRVerificationResult(verified=False, errors=["signature mismatch"])`
- Chain doesn't terminate at a trusted root → `TSRVerificationResult(verified=False, errors=["untrusted chain"])`
- TSA cert expired (and `accept_expired_at_verify_time=False`) → `verified=False, errors=["TSA cert expired"]`
- Multiple errors → all errors returned in the result, not just the first

## Import-time discipline

```python
# rfc3161_verify.py top of file:
try:
    from cryptography import x509  # noqa: F401
    from cryptography.hazmat.primitives import hashes, serialization  # noqa: F401
except ImportError as e:
    raise ImportError(
        "rfc3161_verify requires the audit-verify extra. "
        "Install with: pip install cre-agent-audit[audit-verify]"
    ) from e
```

The base package's `__init__.py` does NOT import `rfc3161_verify`. The Zero-Runtime-Deps badge is intact. The module is `from cre_agent_audit.governance.rfc3161_verify import verify_tsr_token` — opt-in.

## Constraints applied

- The base package never imports `rfc3161_verify.py` (Zero-Deps preserved)
- New optional dependency is `cryptography>=42` only (no transitive surprises)
- mypy --strict clean (with `cryptography` stubs from pyca's package)
- ruff check + ruff format --check clean
- SoT propagation: ADR-0012 update first, then README + ROADMAP + LIMITATIONS + SHIP-RECEIPT + CHANGELOG follow
- Banned-term + banned-name greps zero hits
- TDD: tests first
- Disclaimer line

## Out-of-scope (explicit)

- CRL / OCSP revocation checking (deferred; deployer's environment policy)
- Multiple-TSA cross-validation (one TSA per token; multi-TSA is v0.3+ candidate)
- TSR archival format conversion (TSR-to-CMS-SignedData etc.; downstream tooling problem)
- Bulk verification CLI (deployer integrates into their own audit pipeline; we ship the function)
- Performance benchmarking beyond a single test confirming sub-second verify on a single token

## Verification of completion

The v0.2.2 close on this item completes when:
1. All tests pass (existing 294 + new ~10 — tests skip if `cryptography` not installed, run when CI installs `[audit-verify]`)
2. ruff + ruff format --check + mypy --strict clean
3. ADR-0012 updated; the staleness test still passes against the new claims
4. README + ROADMAP + LIMITATIONS + SHIP-RECEIPT + CHANGELOG updated; staleness test passes
5. CI workflow updated to install `[audit-verify]`; CI green on the changes
6. Council pass: 10/10 from the engineering slate + López de Prado (RFC 3161 + X.509 standards rigor)

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
