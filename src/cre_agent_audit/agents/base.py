"""Shared base types for the 6-agent topology per ARCHITECTURE.md.

The agents are roles, not microservices — the same process can host
multiple agents in a small deployment, separated only by the orchestrator's
routing logic. Each role has one clear responsibility.

``AuditConsumer`` is the consolidated v0.2.1 contract for agents that
read or write the audit chain. It accepts the four v0.2.1 injection seams
in one place — ``ledger`` (ADR-0012 LedgerStore + TimestampSource +
WitnessRegister live behind it), ``mi_proxy`` (ADR-0013), and
``vendor_score_gate`` (ADR-0011 update). Production deployers wire all
three through one constructor; the same consumer instance can verify
chain integrity end-to-end without reaching past the interface.

Public signatures of existing agents (``AuditAgent.process``,
``MonitorAgent.process``) are preserved verbatim. ``AuditConsumer`` adds
``verify_integrity()`` and ``record_vendor_score()`` as the consolidated
operations the four seams compose into.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from cre_agent_audit.governance.audit_chain import AuditLedger
    from cre_agent_audit.governance.mi_proxy import MIProxy
    from cre_agent_audit.governance.vendor_score_gate import (
        VendorScoreEntry,
        VendorScoreGate,
    )

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Agent(ABC, Generic[InputT, OutputT]):
    """Base agent interface — typed input, typed output, no shared state.

    Production implementations swap in their own subclass per role. The v0.2
    stubs here exist so the orchestrator can be wired against a stable
    interface and so consumers see the canonical role signatures.
    """

    role: str
    """Short identifier used by the audit ledger and the orchestrator."""

    @abstractmethod
    def process(self, input_data: InputT) -> OutputT: ...


@dataclass(frozen=True)
class AgentResult(Generic[OutputT]):
    """Wrapper for an agent's output that carries the role + outcome together."""

    role: str
    output: OutputT


class AuditConsumer:
    """Mixin for agents that read or write the audit chain.

    Captures the v0.2.1 dependency-injection contract in one place:
    ``ledger`` (required; backed by the ADR-0012 LedgerStore /
    TimestampSource / WitnessRegister seams behind it), ``mi_proxy``
    (optional; ADR-0013), ``vendor_score_gate`` (optional; ADR-0011 update).

    ``verify_integrity()`` is the consolidated read-side check —
    ``AuditLedger.verify_chain(mi_proxy=self.mi_proxy)`` with the injected
    proxy if any. ``record_vendor_score()`` delegates to the injected gate
    or raises if absent.
    """

    ledger: AuditLedger
    mi_proxy: MIProxy | None
    vendor_score_gate: VendorScoreGate | None

    def verify_integrity(self) -> None:
        """Verify the chain end-to-end, including verifier integrity if
        MI Proxy is wired. Raises ``AuditChainTamperError`` on in-chain
        inconsistency or ``IntegrityVerificationError`` on MI Proxy failure.
        """
        self.ledger.verify_chain(mi_proxy=self.mi_proxy)

    def record_vendor_score(
        self,
        *,
        vendor_id: str,
        input_hash: str,
        score: float,
        model_version: str,
    ) -> VendorScoreEntry:
        """Record a vendor-scoring event via the injected gate.

        Raises ``RuntimeError`` when no gate was injected — the consumer
        cannot silently no-op a vendor signal; the deployer either wires
        a gate or chooses not to use this convenience method.
        """
        if self.vendor_score_gate is None:
            raise RuntimeError(
                "record_vendor_score requires an injected VendorScoreGate; "
                "construct this consumer with vendor_score_gate=... or call "
                "VendorScoreGate.emit() directly"
            )
        return self.vendor_score_gate.emit(
            vendor_id=vendor_id,
            input_hash=input_hash,
            score=score,
            model_version=model_version,
        )
