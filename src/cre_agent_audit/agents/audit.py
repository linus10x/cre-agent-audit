"""Audit agent (stub) — reconstructs prior decisions for regulators, LPs,
and internal review by reading the hash-chain audit ledger (ADR-0003).
"""

from __future__ import annotations

from dataclasses import dataclass

from cre_agent_audit.agents.base import Agent
from cre_agent_audit.governance.audit_chain import AuditEntry, AuditLedger


@dataclass(frozen=True)
class AuditQuery:
    """A regulator-facing audit query — by time window, decision type, actor, etc."""

    decision_type: str | None = None
    actor_id: str | None = None
    since_sequence: int | None = None


class AuditAgent(Agent[AuditQuery, tuple[AuditEntry, ...]]):
    role = "audit"

    def __init__(self, ledger: AuditLedger) -> None:
        self.ledger = ledger

    def process(self, input_data: AuditQuery) -> tuple[AuditEntry, ...]:
        """Filter ledger entries against the query. v0.2 implementation is
        complete enough to support regulator-facing queries by decision_type
        and actor_id within a sequence range."""
        entries = list(self.ledger.entries)
        if input_data.since_sequence is not None:
            entries = [e for e in entries if e.sequence >= input_data.since_sequence]
        if input_data.decision_type is not None:
            entries = [e for e in entries if e.decision_type == input_data.decision_type]
        if input_data.actor_id is not None:
            entries = [e for e in entries if e.actor_id == input_data.actor_id]
        return tuple(entries)
