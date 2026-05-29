"""External-witness anchoring pattern — ADR-0012 § 1.4.

The hash-chained `AuditLedger` is internally consistent but not adversarially
tamper-evident on its own. Periodically anchoring `chain_head()` to an external
witness register (Rekor, OpenTimestamps, regulator-side log) converts it to
adversarially tamper-evident: the witness records what the head was at time T,
and a later forger cannot retroactively rewrite the chain without producing
a witness receipt that contradicts the public record.

Anchoring writes the receipt back to the ledger as a `decision_type="witness_anchor"`
entry. This binds the anchor into the same hash chain that's being protected —
tampering with the anchor record requires tampering with every entry after it.

Stdlib-only HTTP. No `python-rekor`, no `opentimestamps-client`. Receipts
preserve the opaque server response verbatim for later verification.
"""

from __future__ import annotations

import http.client
import json
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable
from urllib.parse import urlparse

from cre_agent_audit.governance.audit_chain import ActorKind, AuditEntry, AuditLedger


@dataclass(frozen=True)
class WitnessReceipt:
    register_name: str  # "rekor" | "opentimestamps" | "custom"
    register_url: str
    submitted_at: datetime
    receipt_blob: bytes  # opaque to the ledger; verifier consumes
    inclusion_uuid: str | None
    log_index: int | None


@runtime_checkable
class WitnessRegister(Protocol):
    """Protocol — anchors a chain-head digest to an external witness register.

    Marked ``@runtime_checkable`` (parity with the other four ADR-0011 /
    ADR-0012 / ADR-0013 Protocol seams) so deployers can validate custom
    backends with ``isinstance(my_impl, WitnessRegister)`` at injection time.
    """

    def anchor(self, chain_head_hex: str) -> WitnessReceipt: ...


@dataclass
class RekorWitness:
    """Sigstore Rekor public transparency log client.

    POSTs a `hashedrekord` entry to Rekor's REST API; receives an inclusion
    UUID + logIndex. Default endpoint is the public Sigstore instance.
    """

    rekor_url: str = "https://rekor.sigstore.dev"
    timeout_s: float = 10.0

    def anchor(self, chain_head_hex: str) -> WitnessReceipt:
        if len(chain_head_hex) != 64:
            raise ValueError("chain_head_hex must be 64 chars (SHA-256)")
        body = json.dumps(
            {
                "apiVersion": "0.0.1",
                "kind": "hashedrekord",
                "spec": {
                    "data": {
                        "hash": {"algorithm": "sha256", "value": chain_head_hex},
                    },
                    "signature": {
                        # Repo policy: anchor the digest only; no signature key
                        # required. Rekor accepts hashedrekord with a placeholder
                        # signature field for transparency-log-only use.
                        "content": "",
                        "format": "x509",
                        "publicKey": {"content": ""},
                    },
                },
            }
        ).encode("utf-8")
        resp_body, status = _post(self.rekor_url + "/api/v1/log/entries", body, self.timeout_s)
        if status not in (200, 201):
            raise RuntimeError(f"Rekor returned HTTP {status}: {resp_body!r}")
        parsed = json.loads(resp_body)
        uuid_value = parsed.get("uuid")
        log_index_value = parsed.get("logIndex")
        return WitnessReceipt(
            register_name="rekor",
            register_url=self.rekor_url,
            submitted_at=datetime.now(timezone.utc),
            receipt_blob=resp_body,
            inclusion_uuid=str(uuid_value) if uuid_value is not None else None,
            log_index=int(log_index_value) if log_index_value is not None else None,
        )


@dataclass
class OpenTimestampsWitness:
    """OpenTimestamps calendar client. Submits the digest; receives a
    pending-commitment receipt that can later be upgraded to a Bitcoin-
    attestation receipt by re-submitting the same opaque blob."""

    calendar_urls: tuple[str, ...] = (
        "https://alice.btc.calendar.opentimestamps.org",
        "https://bob.btc.calendar.opentimestamps.org",
    )
    timeout_s: float = 10.0

    def anchor(self, chain_head_hex: str) -> WitnessReceipt:
        digest = bytes.fromhex(chain_head_hex)
        last_exc: Exception | None = None
        for url in self.calendar_urls:
            try:
                resp_body, status = _post(
                    url + "/digest",
                    digest,
                    self.timeout_s,
                    content_type="application/octet-stream",
                )
                if status == 200:
                    return WitnessReceipt(
                        register_name="opentimestamps",
                        register_url=url,
                        submitted_at=datetime.now(timezone.utc),
                        receipt_blob=resp_body,
                        inclusion_uuid=None,
                        log_index=None,
                    )
                last_exc = RuntimeError(f"OTS calendar {url} returned HTTP {status}")
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
        raise RuntimeError(f"all OTS calendars failed: {last_exc!r}")


def anchor_to_witness(
    *,
    ledger: AuditLedger,
    witness: WitnessRegister,
    actor_id: str = "system:witness_anchor",
) -> AuditEntry:
    """Anchor `ledger.chain_head()` to `witness`; record the receipt as a new entry."""
    head = ledger.chain_head()
    receipt = witness.anchor(head)
    return ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id=actor_id,
        decision_type="witness_anchor",
        action_payload=receipt.receipt_blob,
        gate_verdicts={
            "witness_register": receipt.register_name,
            "witness_url": receipt.register_url,
            "chain_head_anchored": head,
            "inclusion_uuid": receipt.inclusion_uuid or "",
            "log_index": str(receipt.log_index) if receipt.log_index is not None else "",
        },
    )


def _post(
    url: str,
    body: bytes,
    timeout_s: float,
    *,
    content_type: str = "application/json",
) -> tuple[bytes, int]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported scheme {parsed.scheme!r}")
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    conn: http.client.HTTPConnection | http.client.HTTPSConnection
    if parsed.scheme == "https":
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(host, port, timeout=timeout_s, context=ctx)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=timeout_s)
    try:
        conn.request(
            "POST",
            parsed.path or "/",
            body=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        return resp.read(), resp.status
    finally:
        conn.close()
