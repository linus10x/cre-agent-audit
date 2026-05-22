"""Smoke tests for the 6-agent topology per ARCHITECTURE.md.

The agents themselves are stubs in v0.2; these tests verify the interfaces
load cleanly, the role names are stable, and the audit + orchestrator
agents wire against the real audit ledger.
"""

from __future__ import annotations

from cre_agent_audit.agents.audit import AuditAgent, AuditQuery
from cre_agent_audit.agents.domain_intelligence import DomainIntelligenceAgent
from cre_agent_audit.agents.monitor import MonitorAgent
from cre_agent_audit.agents.orchestrator import OrchestratorAgent
from cre_agent_audit.agents.risk import RiskAgent
from cre_agent_audit.agents.strategy import StrategyAgent
from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger


def test_six_agent_roles_have_canonical_names() -> None:
    assert DomainIntelligenceAgent.role == "domain_intelligence"
    assert StrategyAgent.role == "strategy"
    assert RiskAgent.role == "risk"
    assert AuditAgent(ledger=AuditLedger()).role == "audit"
    assert MonitorAgent.role == "monitor"
    assert OrchestratorAgent().role == "orchestrator"


def test_audit_agent_filters_ledger_by_decision_type() -> None:
    ledger = AuditLedger()
    ledger.append(
        actor_kind=ActorKind.AGENT,
        actor_id="strategy",
        decision_type="screening",
        action_payload=b"a",
        gate_verdicts={},
    )
    ledger.append(
        actor_kind=ActorKind.AGENT,
        actor_id="strategy",
        decision_type="lease_abstraction",
        action_payload=b"b",
        gate_verdicts={},
    )
    agent = AuditAgent(ledger=ledger)
    entries = agent.process(AuditQuery(decision_type="screening"))
    assert len(entries) == 1
    assert entries[0].decision_type == "screening"


def test_audit_agent_filters_by_actor_id() -> None:
    ledger = AuditLedger()
    ledger.append(
        actor_kind=ActorKind.AGENT,
        actor_id="strategy_v1",
        decision_type="screening",
        action_payload=b"a",
        gate_verdicts={},
    )
    ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="defcon",
        decision_type="transition",
        action_payload=b"b",
        gate_verdicts={},
    )
    agent = AuditAgent(ledger=ledger)
    entries = agent.process(AuditQuery(actor_id="strategy_v1"))
    assert len(entries) == 1


def test_orchestrator_accepts_all_optional_subagents() -> None:
    orchestrator = OrchestratorAgent(
        domain_intelligence=DomainIntelligenceAgent(),
        strategy=StrategyAgent(),
        risk=RiskAgent(),
        audit=AuditAgent(ledger=AuditLedger()),
        monitor=MonitorAgent(),
    )
    # v0.2 stub: process returns None.
    assert orchestrator.process({}) is None


def test_stubs_return_safe_defaults() -> None:
    assert DomainIntelligenceAgent().process(None) == []
    assert StrategyAgent().process([]) is None
    risk_result = RiskAgent().process(None)  # type: ignore[arg-type]
    assert risk_result.risk_level == "LOW"
    assert MonitorAgent().process(AuditLedger()) == ()
