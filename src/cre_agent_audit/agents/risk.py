"""Risk agent (stub) — evaluates a strategy recommendation against policy
limits and known failure modes before the sovereign veto runs.
"""

from __future__ import annotations

from dataclasses import dataclass

from cre_agent_audit.agents.base import Agent
from cre_agent_audit.agents.strategy import StrategyRecommendation


@dataclass(frozen=True)
class RiskAssessment:
    risk_level: str  # 'LOW' | 'MEDIUM' | 'HIGH' | 'BLOCKED'
    notes: tuple[str, ...]


class RiskAgent(Agent[StrategyRecommendation, RiskAssessment]):
    role = "risk"

    def process(self, input_data: StrategyRecommendation) -> RiskAssessment:
        """v0.2 stub. Production implementations evaluate against policy
        limits + known failure modes catalog (e.g., the M-1..M-278 mistakes
        catalog in the sibling private repository)."""
        return RiskAssessment(risk_level="LOW", notes=())
