"""Tests for rfc3161_verify (audit-verify extra).

Skips the entire module when ``cryptography`` is not installed.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any

import pytest

cryptography = pytest.importorskip("cryptography")

from cre_agent_audit.governance.rfc3161_verify import (  # noqa: E402
    TSRParseError,
    TSRVerificationResult,
    verify_audit_entry_token,
    verify_tsr_token,
)


def _build_signed_tsr(synthetic_tsa: dict[str, Any]) -> bytes:
    """Build a JSON-wrapped CMS-shaped signed token for testing."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    payload = b"test payload for rfc3161 verify"
    digest = hashes.Hash(hashes.SHA256())
    digest.update(payload)
    payload_hash = digest.finalize()

    signature = synthetic_tsa["tsa_key"].sign(
        payload_hash,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    token_struct = {
        "tsa_cert_pem": synthetic_tsa["tsa_cert_pem"].decode("ascii"),
        "signature_b64": base64.b64encode(signature).decode("ascii"),
        "payload_hash_hex": payload_hash.hex(),
        "issued_at_iso": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(token_struct).encode("utf-8")


def test_verify_round_trip_succeeds(
    synthetic_tsa: dict[str, Any],
) -> None:
    token = _build_signed_tsr(synthetic_tsa)
    token_b64 = base64.b64encode(token).decode("ascii")
    result = verify_tsr_token(
        token_b64=token_b64,
        trusted_tsa_certs=[synthetic_tsa["root_cert_pem"]],
    )
    assert result.verified, f"expected verified; errors={result.errors}"
    assert result.tsa_subject is not None
    assert "TestTSA Signer" in result.tsa_subject
    assert result.errors == ()
    assert isinstance(result, TSRVerificationResult)


def test_verify_tamper_detection(synthetic_tsa: dict[str, Any]) -> None:
    """Mutating the signature → verifier surfaces a signature error."""
    token = _build_signed_tsr(synthetic_tsa)
    struct = json.loads(token)
    sig = base64.b64decode(struct["signature_b64"])
    mutated = bytes([(sig[0] ^ 0xFF), *sig[1:]])
    struct["signature_b64"] = base64.b64encode(mutated).decode("ascii")
    mutated_token = json.dumps(struct).encode("utf-8")

    token_b64 = base64.b64encode(mutated_token).decode("ascii")
    result = verify_tsr_token(
        token_b64=token_b64,
        trusted_tsa_certs=[synthetic_tsa["root_cert_pem"]],
    )
    assert not result.verified
    assert any("signature" in e.lower() for e in result.errors)


def test_verify_untrusted_chain_fails(
    synthetic_tsa: dict[str, Any],
) -> None:
    """Empty trusted certs → chain validation fails."""
    token = _build_signed_tsr(synthetic_tsa)
    token_b64 = base64.b64encode(token).decode("ascii")
    result = verify_tsr_token(
        token_b64=token_b64,
        trusted_tsa_certs=[],
    )
    assert not result.verified
    assert any("trusted" in e.lower() or "chain" in e.lower() for e in result.errors)


def test_verify_garbage_bytes_raises_parse_error() -> None:
    with pytest.raises(TSRParseError):
        verify_tsr_token(
            token_b64=base64.b64encode(b"not a real token").decode("ascii"),
            trusted_tsa_certs=[],
        )


def test_verify_non_rsa_tsa_key_surfaces_explicit_error(
    synthetic_tsa: dict[str, Any],
) -> None:
    """A non-RSA TSA certificate must NOT silently pass verification.

    Builds a token whose ``tsa_cert_pem`` field points at an EC (not RSA)
    certificate. The verifier must surface an explicit "unsupported TSA
    public-key algorithm" error rather than silently mis-verifying.
    """
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    ec_key = ec.generate_private_key(ec.SECP256R1())
    builder = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "EC-TSA")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "EC-TSA")]))
        .public_key(ec_key.public_key())
        .serial_number(1)
        .not_valid_before(datetime(2026, 1, 1, tzinfo=timezone.utc))
        .not_valid_after(datetime(2027, 1, 1, tzinfo=timezone.utc))
    )
    ec_cert = builder.sign(ec_key, hashes.SHA256())
    ec_pem = ec_cert.public_bytes(serialization.Encoding.PEM)

    token_struct = {
        "tsa_cert_pem": ec_pem.decode("ascii"),
        "signature_b64": base64.b64encode(b"\x00" * 64).decode("ascii"),
        "payload_hash_hex": ("aa" * 32),
        "issued_at_iso": datetime(2026, 5, 28, tzinfo=timezone.utc).isoformat(),
    }
    token_b64 = base64.b64encode(json.dumps(token_struct).encode("utf-8")).decode("ascii")

    result = verify_tsr_token(
        token_b64=token_b64,
        trusted_tsa_certs=[synthetic_tsa["root_cert_pem"]],
    )
    assert result.verified is False
    assert any("unsupported TSA public-key algorithm" in e for e in result.errors)


def test_verify_audit_entry_token_with_none_returns_verified() -> None:
    """Token-free AuditEntry (v0.2.0 default) is not invalidated."""
    from cre_agent_audit.governance.audit_chain import (
        ActorKind,
        AuditLedger,
    )

    ledger = AuditLedger()
    ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
    )
    entry = ledger.entries[0]
    result = verify_audit_entry_token(
        entry=entry,
        trusted_tsa_certs=[],
    )
    assert result.verified
    assert result.timestamp is None
    assert result.tsa_subject is None
    assert result.errors == ()
