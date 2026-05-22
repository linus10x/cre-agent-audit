"""Domain Intelligence agent (stub) — reads underlying domain (lease text,
tenant application, market rent) and surfaces structured observations.

v0.2 ships the role + interface; production deployments subclass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cre_agent_audit.agents.base import Agent


@dataclass(frozen=True)
class DomainObservation:
    """One structured observation surfaced from raw domain data."""

    observation_kind: str  # 'lease_clause' | 'tenant_signal' | 'market_rent' | ...
    payload: dict[str, Any]
    source_hash: str  # ties the observation to a reproducible source


class DomainIntelligenceAgent(Agent[Any, list[DomainObservation]]):
    role = "domain_intelligence"

    def process(self, input_data: Any) -> list[DomainObservation]:
        """v0.2 stub — production implementations parse the input and return
        a list of structured observations. The stub returns an empty list."""
        return []
