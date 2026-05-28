"""Monitor agent — observes the audit ledger for anomalies and emits
structured alerts. Read-only with respect to the ledger.

v0.2.1 update: extends ``AuditConsumer`` so the v0.2.1 seams (MI Proxy,
VendorScoreGate) are injectable through one constructor. ``process``
signature is unchanged: ``process(ledger)`` still returns
``tuple[MonitorAlert, ...]``. The ``ledger`` constructor argument is
optional and defaults to a fresh ``AuditLedger()`` so v0.2.0 callers
that invoke ``MonitorAgent()`` continue to work unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

from cre_agent_audit.agents.base import Agent, AuditConsumer
from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.governance.mi_proxy import MIProxy
from cre_agent_audit.governance.vendor_score_gate import VendorScoreGate


@dataclass(frozen=True)
class MonitorAlert:
    severity: str  # 'INFO' | 'WARNING' | 'CRITICAL'
    code: str
    message: str


class MonitorAgent(Agent[AuditLedger, tuple[MonitorAlert, ...]], AuditConsumer):
    role = "monitor"

    def __init__(
        self,
        ledger: AuditLedger | None = None,
        *,
        mi_proxy: MIProxy | None = None,
        vendor_score_gate: VendorScoreGate | None = None,
    ) -> None:
        self.ledger = ledger if ledger is not None else AuditLedger()
        self.mi_proxy = mi_proxy
        self.vendor_score_gate = vendor_score_gate

    def process(self, input_data: AuditLedger) -> tuple[MonitorAlert, ...]:
        """v0.2 stub — production implementations scan the ledger for
        statistical anomalies (veto-rate spikes, cohort-specific divergence,
        shadow-mode time-in-state limits) and emit alerts."""
        return ()
