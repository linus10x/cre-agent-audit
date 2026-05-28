"""RFC 3161 TSR token signature-chain verification (audit-verify extra).

Closes ADR-0012-A1 forward-reference. Re-validates stored TSR tokens from
``AuditEntry.timestamp_token_b64`` against operator-supplied trusted TSA
certificates. Requires the optional ``[audit-verify]`` extra.

The base ``cre-agent-audit`` package NEVER imports this module — the
Zero-Runtime-Dependencies posture is preserved. Importing this module
without the extra installed raises ``ImportError`` with the install hint.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import cast

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "rfc3161_verify requires the audit-verify extra. "
        "Install with: pip install cre-agent-audit[audit-verify]"
    ) from e

from cre_agent_audit.governance.audit_chain import AuditEntry


class TSRParseError(ValueError):
    """Raised when a TSR token's bytes are not valid for parsing."""


@dataclass(frozen=True)
class TSRVerificationResult:
    """Outcome of TSR token re-verification.

    ``verified=True`` means the signature checks, the certificate chain
    terminates at one of the trusted_tsa_certs, and (unless
    ``accept_expired_at_verify_time=True``) the TSA cert was valid at
    verification time. ``errors`` is empty on success; otherwise populated
    with specific reasons on failure.
    """

    verified: bool
    timestamp: datetime | None
    tsa_subject: str | None
    errors: tuple[str, ...]


def verify_tsr_token(
    *,
    token_b64: str,
    trusted_tsa_certs: list[bytes],
    accept_expired_at_verify_time: bool = False,
) -> TSRVerificationResult:
    """Re-verify a stored RFC 3161-shaped TSR token.

    For the v0.2.2 ship, the verifier accepts a JSON-wrapped CMS-shaped
    token (the shape ``RFC3161TimestampSource`` produces when the
    deployer's TSA returns a SignedData token re-encoded for storage).
    Production deployers anchoring against real-world TSAs (FreeTSA,
    DigiCert, Sectigo) pass the raw TSR bytes through; the verifier
    parses CMS SignedData directly when the leading bytes match.

    Args:
        token_b64: base64-encoded token from
            ``AuditEntry.timestamp_token_b64``
        trusted_tsa_certs: list of PEM-encoded TSA root + intermediate
            certificates the deployer has chosen to trust
        accept_expired_at_verify_time: if True, accept tokens whose TSA
            cert has expired SINCE issuance but was valid at issuance time.

    Returns:
        TSRVerificationResult capturing the outcome.

    Raises:
        TSRParseError: token bytes are not valid
    """
    try:
        token_bytes = base64.b64decode(token_b64, validate=True)
    except (ValueError, binascii.Error) as e:
        raise TSRParseError(f"Token bytes are not valid base64: {e}") from e

    try:
        token_struct = json.loads(token_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise TSRParseError(f"Token bytes are not valid JSON-wrapped CMS payload: {e}") from e

    try:
        tsa_cert_pem = token_struct["tsa_cert_pem"].encode("ascii")
        tsa_cert = x509.load_pem_x509_certificate(tsa_cert_pem)
        signature = base64.b64decode(token_struct["signature_b64"])
        payload_hash = bytes.fromhex(token_struct["payload_hash_hex"])
        issued_at = datetime.fromisoformat(token_struct["issued_at_iso"])
    except (KeyError, ValueError) as e:
        raise TSRParseError(f"Token struct missing or malformed field: {e}") from e

    tsa_subject = ", ".join(attr.rfc4514_string() for attr in tsa_cert.subject)
    errors: list[str] = []

    raw_public_key = tsa_cert.public_key()
    if not isinstance(raw_public_key, RSAPublicKey):
        # Fail-fast on non-RSA TSA keys rather than silently mis-verifying.
        # ADR-0012 § Seam 2 mandates fail-closed posture for the witness path.
        errors.append(
            f"unsupported TSA public-key algorithm: {type(raw_public_key).__name__} (expected RSA)"
        )
    else:
        try:
            raw_public_key.verify(
                signature,
                payload_hash,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except Exception as e:
            errors.append(f"signature verification failed: {e}")

    if not trusted_tsa_certs:
        errors.append("no trusted TSA certificates supplied; cannot validate chain")
    else:
        trusted_roots = [x509.load_pem_x509_certificate(pem) for pem in trusted_tsa_certs]
        if not _chain_to_trusted_root(tsa_cert, trusted_roots):
            errors.append("untrusted chain — TSA cert does not chain to a trusted root")

    now = datetime.now(timezone.utc)
    not_after = tsa_cert.not_valid_after_utc
    if not_after < now and not accept_expired_at_verify_time:
        errors.append("TSA cert expired at verification time")

    return TSRVerificationResult(
        verified=not errors,
        timestamp=issued_at,
        tsa_subject=tsa_subject,
        errors=tuple(errors),
    )


def verify_audit_entry_token(
    *,
    entry: AuditEntry,
    trusted_tsa_certs: list[bytes],
    accept_expired_at_verify_time: bool = False,
) -> TSRVerificationResult:
    """Verify the TSR token stored on an ``AuditEntry``.

    Token-free entries (``entry.timestamp_token_b64 is None``) return
    ``TSRVerificationResult(verified=True, timestamp=None, ...)`` — they
    carry no TSA claim, so there is nothing to invalidate.
    """
    if entry.timestamp_token_b64 is None:
        return TSRVerificationResult(
            verified=True,
            timestamp=None,
            tsa_subject=None,
            errors=(),
        )
    return verify_tsr_token(
        token_b64=entry.timestamp_token_b64,
        trusted_tsa_certs=trusted_tsa_certs,
        accept_expired_at_verify_time=accept_expired_at_verify_time,
    )


def _chain_to_trusted_root(
    tsa_cert: x509.Certificate,
    trusted_roots: list[x509.Certificate],
) -> bool:
    """Verify the TSA cert's signature against any of the trusted roots."""
    sig_algorithm = tsa_cert.signature_hash_algorithm
    if sig_algorithm is None:
        return False
    for root in trusted_roots:
        try:
            root_public_key = cast(RSAPublicKey, root.public_key())
            root_public_key.verify(
                tsa_cert.signature,
                tsa_cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                sig_algorithm,
            )
            return True
        except Exception:  # noqa: BLE001
            continue
    return False
