"""Trusted timestamp Protocol + reference impls — ADR-0012 § 1.3.

By default, `AuditEntry.timestamp` is the local system clock. For audit-grade
attestation under SOC 2 / SOX 404 / FFIEC discovery, deployers can inject an
`RFC3161TimestampSource` (this module) that obtains a signed timestamp from
a trusted Timestamp Authority and stores the opaque token alongside the
timestamp. The token can later be re-verified against the TSA's signing chain.

Stdlib-only network code. No `requests`, no `urllib3`. RFC 3161 codec in
`rfc3161_codec.py`. Verification (requires `pyca/cryptography`) is gated
behind the `audit-verify` extra in `rfc3161_verify.py`.
"""

from __future__ import annotations

import http.client
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable
from urllib.parse import ParseResult, urlparse


@dataclass(frozen=True)
class TrustedTimestamp:
    """A timestamp + optional TSA attestation."""

    asserted_at: datetime
    tsa_url: str | None
    tsr_token_b64: str | None
    hash_algorithm: str = "sha256"


@runtime_checkable
class TimestampSource(Protocol):
    """Protocol — returns a `TrustedTimestamp` for a payload digest.

    Marked ``@runtime_checkable`` (parity with the other four ADR-0011 /
    ADR-0012 / ADR-0013 Protocol seams) so deployers can validate custom
    backends with ``isinstance(my_impl, TimestampSource)`` at injection time.
    """

    def stamp(self, payload_digest: bytes) -> TrustedTimestamp: ...


class LocalClockTimestampSource:
    """Default — uses `datetime.now(timezone.utc)`; no attestation."""

    def stamp(self, payload_digest: bytes) -> TrustedTimestamp:
        return TrustedTimestamp(
            asserted_at=datetime.now(timezone.utc),
            tsa_url=None,
            tsr_token_b64=None,
        )


@dataclass
class RFC3161TimestampSource:
    """RFC 3161 client — sends a TSQ, receives a TSR, parses the GenTime.

    On TSA failure, falls back to local clock by default (so a TSA outage
    cannot stall the audit pipeline). The fallback fires the `on_fallback`
    callback so the deployer can alert. Set `fallback_to_local_on_failure=False`
    to fail-closed instead.
    """

    tsa_url: str  # e.g., "https://freetsa.org/tsr"
    timeout_s: float = 5.0
    fallback_to_local_on_failure: bool = True
    on_fallback: Callable[[Exception], None] | None = None

    def stamp(self, payload_digest: bytes) -> TrustedTimestamp:
        # Validate scheme up front so callers see a clear error even when the
        # URL is wrong by configuration (not by network outage).
        url = urlparse(self.tsa_url)
        if url.scheme not in ("http", "https"):
            raise ValueError(f"tsa_url must be http or https; got {url.scheme!r}")

        from cre_agent_audit.governance.rfc3161_codec import (
            build_timestamp_request,
            parse_timestamp_response,
        )

        tsq = build_timestamp_request(payload_digest)
        try:
            tsr_bytes = self._post(tsq, url)
            asserted_at = parse_timestamp_response(tsr_bytes)
            import base64

            return TrustedTimestamp(
                asserted_at=asserted_at,
                tsa_url=self.tsa_url,
                tsr_token_b64=base64.b64encode(tsr_bytes).decode("ascii"),
            )
        except Exception as exc:
            if self.fallback_to_local_on_failure:
                if self.on_fallback is not None:
                    self.on_fallback(exc)
                return LocalClockTimestampSource().stamp(payload_digest)
            raise

    def _post(self, tsq_bytes: bytes, url: ParseResult) -> bytes:
        host = url.hostname or ""
        port = url.port or (443 if url.scheme == "https" else 80)
        conn: http.client.HTTPConnection | http.client.HTTPSConnection
        if url.scheme == "https":
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection(host, port, timeout=self.timeout_s, context=ctx)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=self.timeout_s)
        try:
            conn.request(
                "POST",
                url.path or "/",
                body=tsq_bytes,
                headers={
                    "Content-Type": "application/timestamp-query",
                    "Content-Length": str(len(tsq_bytes)),
                },
            )
            resp = conn.getresponse()
            if resp.status != 200:
                raise RuntimeError(f"TSA returned HTTP {resp.status}")
            return resp.read()
        finally:
            conn.close()
