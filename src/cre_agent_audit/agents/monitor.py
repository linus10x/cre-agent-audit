"""Monitor agent (stub) — observes the audit ledger for anomalies and emits
structured alerts. Read-only with respect to the ledger.
"""

from __future__ import annotations

from dataclasses import dataclass

from cre_agent_audit.agents.base import Agent
from cre_agent_audit.governance.audit_chain import AuditLedger


@dataclass(frozen=True)
class MonitorAlert:
    severity: str  # 'INFO' | 'WARNING' | 'CRITICAL'
    code: str
    message: str


class MonitorAgent(Agent[AuditLedger, tuple[MonitorAlert, ...]]):
    role = "monitor"

    def process(self, input_data: AuditLedger) -> tuple[MonitorAlert, ...]:
        """v0.2 stub — production implementations scan the ledger for
        statistical anomalies (veto-rate spikes, cohort-specific divergence,
        shadow-mode time-in-state limits) and emit alerts."""
        return ()
