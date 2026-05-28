"""Tests for witness-anchor pattern (Rekor + OpenTimestamps)."""

from __future__ import annotations

import dataclasses
import json
import threading
from collections.abc import Iterator
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger
from cre_agent_audit.governance.witness_anchor import (
    OpenTimestampsWitness,
    RekorWitness,
    WitnessReceipt,
    anchor_to_witness,
)


class _MockRekorHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        body = json.dumps(
            {
                "uuid": "deadbeef" * 8,
                "logIndex": 12345,
                "integratedTime": int(datetime.now(timezone.utc).timestamp()),
            }
        ).encode("utf-8")
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:  # noqa: ARG002
        pass


@pytest.fixture
def mock_rekor() -> Iterator[str]:
    server = HTTPServer(("127.0.0.1", 0), _MockRekorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def test_rekor_witness_returns_receipt(mock_rekor: str) -> None:
    w = RekorWitness(rekor_url=mock_rekor)
    receipt = w.anchor("a" * 64)
    assert isinstance(receipt, WitnessReceipt)
    assert receipt.register_name == "rekor"
    assert receipt.log_index == 12345


def test_rekor_witness_rejects_wrong_head_length() -> None:
    w = RekorWitness(rekor_url="http://localhost:1")
    with pytest.raises(ValueError):
        w.anchor("too-short")


def test_anchor_to_witness_writes_audit_entry(mock_rekor: str) -> None:
    ledger = AuditLedger()
    ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="t",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
    )
    anchor_entry = anchor_to_witness(ledger=ledger, witness=RekorWitness(rekor_url=mock_rekor))
    assert anchor_entry.decision_type == "witness_anchor"
    assert anchor_entry.gate_verdicts["witness_register"] == "rekor"
    assert anchor_entry.gate_verdicts["log_index"] == "12345"
    assert ledger.store is not None
    assert len(ledger.store) == 2
    ledger.verify_chain()


def test_witness_receipt_is_frozen() -> None:
    r = WitnessReceipt(
        register_name="rekor",
        register_url="http://x",
        submitted_at=datetime.now(timezone.utc),
        receipt_blob=b"",
        inclusion_uuid=None,
        log_index=None,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.register_name = "other"  # type: ignore[misc]


def test_ots_witness_raises_when_all_calendars_unreachable() -> None:
    w = OpenTimestampsWitness(
        calendar_urls=("https://invalid.example.test.invalid./",),
        timeout_s=0.5,
    )
    with pytest.raises(RuntimeError):
        w.anchor("b" * 64)
