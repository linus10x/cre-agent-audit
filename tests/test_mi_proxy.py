"""Tests for the MI Proxy (Module Integrity verifier chain-of-custody).

Implements the test surface named in ADR-0013 § "Implementation notes":
round-trip, tampered binary, missing key, stale attestation, verifier-hook
integration. Fail-closed posture is the load-bearing assertion.
"""

from __future__ import annotations

import base64
import secrets
import time
import warnings
from datetime import datetime, timedelta, timezone

import pytest

from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditLedger,
)
from cre_agent_audit.governance.mi_proxy import (
    Attestation,
    IntegrityVerificationError,
    LocalMIProxy,
    MIProxy,
    MIProxyKeyMissingWarning,
)

VERIFIER_COMPONENT = "cre_agent_audit.governance.audit_chain"


def _ledger_with_one_entry() -> AuditLedger:
    ledger = AuditLedger()
    ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="test_decision",
        action_payload=b"hello",
        gate_verdicts={"defcon": "allow"},
    )
    return ledger


def _fresh_key_b64() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


# --------------------------------------------------------------------------- #
# 1. Protocol conformance                                                     #
# --------------------------------------------------------------------------- #


def test_local_mi_proxy_is_a_mi_proxy() -> None:
    """LocalMIProxy conforms to the MIProxy Protocol."""
    proxy: MIProxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    assert hasattr(proxy, "attest")
    assert hasattr(proxy, "verify_attestation")


# --------------------------------------------------------------------------- #
# 2. Round-trip — attest then verify                                          #
# --------------------------------------------------------------------------- #


def test_local_mi_proxy_round_trip_succeeds() -> None:
    """A fresh attestation verifies against the same proxy."""
    proxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    attestation = proxy.attest(component_id=VERIFIER_COMPONENT)
    assert proxy.verify_attestation(attestation) is True
    assert attestation.component_id == VERIFIER_COMPONENT
    assert attestation.backend_id == "local-hmac"
    assert len(attestation.sha256_hex) == 64
    assert attestation.signature_b64
    # ISO-8601 round-trip
    parsed = datetime.fromisoformat(attestation.timestamp_iso)
    assert parsed.tzinfo is not None


# --------------------------------------------------------------------------- #
# 3. Tampered attestation — any field change fails verify                     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "field, mutated_value",
    [
        ("component_id", "cre_agent_audit.governance.different_module"),
        ("sha256_hex", "0" * 64),
        ("timestamp_iso", "2030-01-01T00:00:00+00:00"),
        ("backend_id", "spoofed-backend"),
    ],
)
def test_local_mi_proxy_rejects_tampered_attestation(
    field: str, mutated_value: str
) -> None:
    proxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    attestation = proxy.attest(component_id=VERIFIER_COMPONENT)
    tampered = Attestation(
        **{**attestation.__dict__, field: mutated_value}
    )
    assert proxy.verify_attestation(tampered) is False


def test_local_mi_proxy_rejects_swapped_signature() -> None:
    """A signature from a different key over the same payload is rejected."""
    proxy_a = LocalMIProxy(signing_key=secrets.token_bytes(32))
    proxy_b = LocalMIProxy(signing_key=secrets.token_bytes(32))
    attestation_b = proxy_b.attest(component_id=VERIFIER_COMPONENT)
    assert proxy_a.verify_attestation(attestation_b) is False


def test_local_mi_proxy_rejects_attestation_of_unknown_component() -> None:
    """attest() raises ImportError for a component that does not resolve."""
    proxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    with pytest.raises(ImportError):
        proxy.attest(component_id="cre_agent_audit.governance.does_not_exist")


# --------------------------------------------------------------------------- #
# 4. Missing key — explicit warning + fail-closed                             #
# --------------------------------------------------------------------------- #


def test_local_mi_proxy_warns_when_key_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """No key in env → MIProxyKeyMissingWarning; attestations sign with zero key."""
    monkeypatch.delenv("CRE_AUDIT_MI_PROXY_KEY", raising=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        proxy = LocalMIProxy.from_env()
        proxy.attest(component_id=VERIFIER_COMPONENT)
    key_warnings = [w for w in caught if issubclass(w.category, MIProxyKeyMissingWarning)]
    assert key_warnings, "Expected MIProxyKeyMissingWarning when key absent"


def test_local_mi_proxy_fail_closed_against_real_key_after_missing_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An attestation signed under the zero key does not verify under a real key."""
    monkeypatch.delenv("CRE_AUDIT_MI_PROXY_KEY", raising=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        zero_key_proxy = LocalMIProxy.from_env()
        attestation = zero_key_proxy.attest(component_id=VERIFIER_COMPONENT)
    real_proxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    assert real_proxy.verify_attestation(attestation) is False


def test_local_mi_proxy_rejects_short_key() -> None:
    """Keys shorter than 32 bytes are rejected at construction."""
    with pytest.raises(ValueError):
        LocalMIProxy(signing_key=b"short")


# --------------------------------------------------------------------------- #
# 5. Stale attestation — time-bounded                                         #
# --------------------------------------------------------------------------- #


def test_local_mi_proxy_rejects_stale_attestation() -> None:
    """Attestations older than max_age_seconds fail verify."""
    key = secrets.token_bytes(32)
    proxy = LocalMIProxy(signing_key=key, max_age_seconds=60)

    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    fresh = proxy.attest(component_id=VERIFIER_COMPONENT)
    # Re-sign the stale-timestamped attestation with the same key so that
    # the signature is valid but the timestamp is out of window.
    stale = LocalMIProxy._for_test_resign(
        proxy,
        component_id=fresh.component_id,
        sha256_hex=fresh.sha256_hex,
        timestamp_iso=stale_ts,
        backend_id=fresh.backend_id,
    )
    assert proxy.verify_attestation(stale) is False


def test_local_mi_proxy_accepts_fresh_attestation_within_window() -> None:
    proxy = LocalMIProxy(signing_key=secrets.token_bytes(32), max_age_seconds=3600)
    attestation = proxy.attest(component_id=VERIFIER_COMPONENT)
    assert proxy.verify_attestation(attestation) is True


# --------------------------------------------------------------------------- #
# 6. AuditLedger.verify_chain hook — fail-closed when proxy attests false     #
# --------------------------------------------------------------------------- #


def test_verify_chain_with_mi_proxy_passes_when_attestation_valid() -> None:
    """verify_chain(mi_proxy=...) returns normally when attestation succeeds."""
    ledger = _ledger_with_one_entry()
    proxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    ledger.verify_chain(mi_proxy=proxy)  # must not raise


def test_verify_chain_without_mi_proxy_preserves_default_behavior() -> None:
    """The hook is opt-in; v0.2.0 callers see no change."""
    ledger = _ledger_with_one_entry()
    ledger.verify_chain()  # must not raise


def test_verify_chain_with_failing_mi_proxy_raises_integrity_error() -> None:
    """verify_chain refuses to return a verified result when MIProxy fails."""

    class AlwaysFailMIProxy:
        def attest(self, component_id: str) -> Attestation:
            return Attestation(
                component_id=component_id,
                sha256_hex="f" * 64,
                timestamp_iso=datetime.now(timezone.utc).isoformat(),
                signature_b64="invalid",
                backend_id="test-fail",
            )

        def verify_attestation(self, attestation: Attestation) -> bool:
            return False

    ledger = _ledger_with_one_entry()
    with pytest.raises(IntegrityVerificationError):
        ledger.verify_chain(mi_proxy=AlwaysFailMIProxy())


# --------------------------------------------------------------------------- #
# 7. Performance budget — local backend must stay cheap                       #
# --------------------------------------------------------------------------- #


def test_attest_latency_local_backend() -> None:
    """ADR-0013 commits to ~5ms per call with the local backend (10x slack)."""
    proxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    start = time.perf_counter()
    for _ in range(10):
        attestation = proxy.attest(component_id=VERIFIER_COMPONENT)
        proxy.verify_attestation(attestation)
    elapsed_ms_per_call = ((time.perf_counter() - start) * 1000) / 10
    # Allow 50ms generous ceiling for slow CI; tight budget is 5ms.
    assert elapsed_ms_per_call < 50, f"Attest+verify took {elapsed_ms_per_call:.2f}ms/call"
