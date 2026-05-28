"""Audit agent — reconstructs prior decisions for regulators, LPs, and
internal review by reading the hash-chain audit ledger (ADR-0003).

v0.2.1 update: extends ``AuditConsumer`` so the v0.2.1 seams (MI Proxy,
VendorScoreGate) are injectable through one constructor. The ``process``
filter signature is unchanged from v0.2.0.
"""

from __future__ import annotations

from dataclasses import dataclass

from cre_agent_audit.agents.base import Agent, AuditConsumer
from cre_agent_audit.governance.audit_chain import AuditEntry, AuditLedger
from cre_agent_audit.governance.mi_proxy import MIProxy
from cre_agent_audit.governance.vendor_score_gate import VendorScoreGate


@dataclass(frozen=True)
class AuditQuery:
    """A regulator-facing audit query — by time window, decision type, actor, etc."""

    decision_type: str | None = None
    actor_id: str | None = None
    since_sequence: int | None = None


class AuditAgent(Agent[AuditQuery, tuple[AuditEntry, ...]], AuditConsumer):
    role = "audit"

    def __init__(
        self,
        ledger: AuditLedger,
        *,
        mi_proxy: MIProxy | None = None,
        vendor_score_gate: VendorScoreGate | None = None,
    ) -> None:
        self.ledger = ledger
        self.mi_proxy = mi_proxy
        self.vendor_score_gate = vendor_score_gate

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
