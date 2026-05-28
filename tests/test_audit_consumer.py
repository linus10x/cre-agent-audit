"""Tests for the consolidated AuditConsumer base — ADR-0012 + ADR-0013 seams
injected through one interface, used by AuditAgent and MonitorAgent.
"""

from __future__ import annotations

import hashlib
import secrets

import pytest

from cre_agent_audit.agents.audit import AuditAgent, AuditQuery
from cre_agent_audit.agents.base import AuditConsumer
from cre_agent_audit.agents.monitor import MonitorAgent
from cre_agent_audit.agents.orchestrator import OrchestratorAgent
from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger
from cre_agent_audit.governance.mi_proxy import (
    IntegrityVerificationError,
    LocalMIProxy,
)
from cre_agent_audit.governance.vendor_score_gate import (
    InMemoryVendorScoreGate,
    VendorScoreDriftDetected,
)

# --------------------------------------------------------------------------- #
# 1. AuditConsumer base — required surface                                    #
# --------------------------------------------------------------------------- #


def test_audit_agent_is_an_audit_consumer() -> None:
    agent = AuditAgent(ledger=AuditLedger())
    assert isinstance(agent, AuditConsumer)


def test_monitor_agent_is_an_audit_consumer() -> None:
    assert isinstance(MonitorAgent(ledger=AuditLedger()), AuditConsumer)


# --------------------------------------------------------------------------- #
# 2. Injection of the v0.2.1 seams                                            #
# --------------------------------------------------------------------------- #


def test_audit_consumer_accepts_mi_proxy_injection() -> None:
    proxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    agent = AuditAgent(ledger=AuditLedger(), mi_proxy=proxy)
    assert agent.mi_proxy is proxy


def test_audit_consumer_accepts_vendor_score_gate_injection() -> None:
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger)
    agent = MonitorAgent(ledger=ledger, vendor_score_gate=gate)
    assert agent.vendor_score_gate is gate


# --------------------------------------------------------------------------- #
# 3. verify_integrity — convenience that wraps verify_chain(mi_proxy=...)     #
# --------------------------------------------------------------------------- #


def test_verify_integrity_passes_when_proxy_absent() -> None:
    ledger = AuditLedger()
    ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
    )
    AuditAgent(ledger=ledger).verify_integrity()  # must not raise


def test_verify_integrity_uses_injected_mi_proxy() -> None:
    ledger = AuditLedger()
    ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
    )
    proxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    agent = AuditAgent(ledger=ledger, mi_proxy=proxy)
    agent.verify_integrity()  # must not raise — proxy attestation valid


def test_verify_integrity_fails_closed_with_bad_proxy() -> None:
    from datetime import datetime, timezone

    from cre_agent_audit.governance.mi_proxy import Attestation

    class AlwaysFailMIProxy:
        def attest(self, component_id: str) -> Attestation:
            return Attestation(
                component_id=component_id,
                sha256_hex="f" * 64,
                timestamp_iso=datetime.now(timezone.utc).isoformat(),
                signature_b64="x",
                backend_id="x",
            )

        def verify_attestation(self, attestation: Attestation) -> bool:
            return False

    ledger = AuditLedger()
    agent = AuditAgent(ledger=ledger, mi_proxy=AlwaysFailMIProxy())
    with pytest.raises(IntegrityVerificationError):
        agent.verify_integrity()


# --------------------------------------------------------------------------- #
# 4. record_vendor_score — delegates to the injected gate                     #
# --------------------------------------------------------------------------- #


def test_record_vendor_score_delegates_to_gate() -> None:
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger)
    agent = MonitorAgent(ledger=ledger, vendor_score_gate=gate)
    entry = agent.record_vendor_score(
        vendor_id="acme",
        input_hash=hashlib.sha256(b"x").hexdigest(),
        score=0.5,
        model_version="v1",
    )
    assert entry.vendor_id == "acme"
    assert len(ledger.entries) == 1


def test_record_vendor_score_without_gate_raises() -> None:
    agent = MonitorAgent(ledger=AuditLedger())  # no gate
    with pytest.raises(RuntimeError):
        agent.record_vendor_score(
            vendor_id="acme",
            input_hash=hashlib.sha256(b"x").hexdigest(),
            score=0.5,
            model_version="v1",
        )


def test_record_vendor_score_propagates_drift() -> None:
    ledger = AuditLedger()
    gate = InMemoryVendorScoreGate(ledger=ledger)
    agent = MonitorAgent(ledger=ledger, vendor_score_gate=gate)
    input_hash = hashlib.sha256(b"x").hexdigest()
    agent.record_vendor_score(
        vendor_id="acme",
        input_hash=input_hash,
        score=0.5,
        model_version="v1",
    )
    with pytest.raises(VendorScoreDriftDetected):
        agent.record_vendor_score(
            vendor_id="acme",
            input_hash=input_hash,
            score=0.8,
            model_version="v1",
        )


# --------------------------------------------------------------------------- #
# 5. Public-signature backward compatibility                                  #
# --------------------------------------------------------------------------- #


def test_audit_agent_filter_signature_preserved() -> None:
    """AuditAgent.process(AuditQuery(...)) must still return tuple[AuditEntry, ...]."""
    ledger = AuditLedger()
    ledger.append(
        actor_kind=ActorKind.AGENT,
        actor_id="strategy",
        decision_type="screening",
        action_payload=b"a",
        gate_verdicts={},
    )
    agent = AuditAgent(ledger=ledger)
    result = agent.process(AuditQuery(decision_type="screening"))
    assert isinstance(result, tuple)
    assert len(result) == 1


def test_monitor_agent_process_signature_preserved() -> None:
    """MonitorAgent.process(ledger) must still return tuple[MonitorAlert, ...]."""
    agent = MonitorAgent(ledger=AuditLedger())
    result = agent.process(AuditLedger())
    assert isinstance(result, tuple)


def test_orchestrator_accepts_audit_and_monitor_with_seams() -> None:
    """Orchestrator wires injected consumers with their v0.2.1 seams."""
    ledger = AuditLedger()
    proxy = LocalMIProxy(signing_key=secrets.token_bytes(32))
    gate = InMemoryVendorScoreGate(ledger=ledger)
    orch = OrchestratorAgent(
        audit=AuditAgent(ledger=ledger, mi_proxy=proxy),
        monitor=MonitorAgent(ledger=ledger, vendor_score_gate=gate),
        ledger=ledger,
    )
    assert orch.process({}) is None  # v0.2 stub preserved
