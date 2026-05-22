"""Orchestrator agent (stub) — routes work between the other five agents per
the compose order documented in ARCHITECTURE.md:

    DEFCON → Domain pre-flight → Sovereign Veto → Autonomy Ladder → Shadow Mode
    → Hash-chain Audit write → ACTION

v0.2 ships the role + a minimal route() that demonstrates the compose order
end-to-end. Production implementations swap in their own subclass with the
specific agent wiring for the deployment.
"""

from __future__ import annotations

from dataclasses import dataclass

from cre_agent_audit.agents.audit import AuditAgent
from cre_agent_audit.agents.base import Agent
from cre_agent_audit.agents.domain_intelligence import DomainIntelligenceAgent
from cre_agent_audit.agents.monitor import MonitorAgent
from cre_agent_audit.agents.risk import RiskAgent
from cre_agent_audit.agents.strategy import StrategyAgent
from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.governance.defcon import DefconController
from cre_agent_audit.governance.sovereign_veto import SovereignVeto


@dataclass
class OrchestratorAgent(Agent[object, object]):
    """Composes the 5 other roles into one decision pipeline."""

    role: str = "orchestrator"
    domain_intelligence: DomainIntelligenceAgent | None = None
    strategy: StrategyAgent | None = None
    risk: RiskAgent | None = None
    audit: AuditAgent | None = None
    monitor: MonitorAgent | None = None
    defcon: DefconController | None = None
    sovereign_veto: SovereignVeto | None = None
    ledger: AuditLedger | None = None

    def process(self, input_data: object) -> object:
        """v0.2 stub — returns None. Production implementations wire the full
        compose order: domain_intelligence.process → strategy.process →
        risk.process → defcon.is_allowed → sovereign_veto.check → ledger
        write → return outcome."""
        return None
