"""Strategy agent (stub) — composes an action recommendation from domain
observations. v0.2 ships the interface; production deployments subclass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cre_agent_audit.agents.base import Agent
from cre_agent_audit.agents.domain_intelligence import DomainObservation


@dataclass(frozen=True)
class StrategyRecommendation:
    action_kind: str  # 'lease_abstraction' | 'tenant_screening' | 'rent_optimization' | ...
    payload: dict[str, Any]
    confidence: float


class StrategyAgent(Agent[list[DomainObservation], StrategyRecommendation | None]):
    role = "strategy"

    def process(self, input_data: list[DomainObservation]) -> StrategyRecommendation | None:
        """v0.2 stub — production implementations propose action(s) for the
        orchestrator to route through risk + sovereign veto."""
        return None
