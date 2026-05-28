"""Shared pytest fixtures.

Currently houses the ``synthetic_tsa`` fixture used by
``tests/test_rfc3161_verify.py`` (audit-verify extra). Skips cleanly when
``cryptography`` is not installed so the rest of the test suite remains
runnable in the base-dependency install.
"""

from __future__ import annotations

import pytest

try:
    import cryptography  # noqa: F401

    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False


@pytest.fixture(scope="session")
def synthetic_tsa() -> dict[str, object]:
    """Build a synthetic TSA root cert + intermediate signer + signing key.

    Used by ``tests/test_rfc3161_verify.py``. Skips cleanly when
    ``cryptography`` (the ``audit-verify`` extra) is not installed.

    Returns a dict with:
    - ``root_cert_pem``: bytes — PEM-encoded synthetic root cert
    - ``tsa_cert_pem``: bytes — PEM-encoded TSA signer cert
    - ``tsa_key``: cryptography RSA private key
    - ``tsa_cert``: cryptography Certificate object
    - ``root_cert``: cryptography Certificate object
    """
    if not _HAS_CRYPTOGRAPHY:
        pytest.skip("cryptography (audit-verify extra) not installed")

    from datetime import datetime, timedelta, timezone

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    now = datetime.now(timezone.utc)

    root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    root_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "TestTSA Root CA")])
    root_cert = (
        x509.CertificateBuilder()
        .subject_name(root_subject)
        .issuer_name(root_subject)
        .public_key(root_key.public_key())
        .serial_number(1)
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(root_key, hashes.SHA256())
    )

    tsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    tsa_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "TestTSA Signer")])
    tsa_cert = (
        x509.CertificateBuilder()
        .subject_name(tsa_subject)
        .issuer_name(root_subject)
        .public_key(tsa_key.public_key())
        .serial_number(2)
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=180))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(root_key, hashes.SHA256())
    )

    return {
        "root_cert_pem": root_cert.public_bytes(serialization.Encoding.PEM),
        "tsa_cert_pem": tsa_cert.public_bytes(serialization.Encoding.PEM),
        "tsa_key": tsa_key,
        "tsa_cert": tsa_cert,
        "root_cert": root_cert,
    }
