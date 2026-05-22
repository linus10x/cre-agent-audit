"""Sovereign Veto — ADR-0002.

A non-overridable check that runs at the agent boundary before any action
that crosses a constraint surface the agent does not have authority to clear.

The veto is constraint-surface-specific (tenant screening goes to the Fair
Housing gate, lease abstraction goes to the Provenance Chain, rent
optimization goes to the antitrust-coordination check). This module is the
dispatch layer; the surface-specific checks live in their own modules and
register themselves here via ``register(action_class, check)``.

Bypass requires a named human owner plus a regulatory basis. The bypass
entry is logged immutably; the original veto entry is NEVER removed.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger


class VetoVerdict(Enum):
    PASS = "PASS"
    VETO = "VETO"


@dataclass(frozen=True)
class VetoResult:
    """Structured outcome of a sovereign-veto check.

    Vetoes are not "no." Vetoes are named reason codes (e.g., FHA-VOUCHER,
    PROV-INCOMPLETE-MATERIAL, RESIDENCY-CROSS-JURISDICTION-UNTAGGED). The
    code is the regulator-readable explanation.
    """

    verdict: VetoVerdict
    reason_code: str | None = None
    owner_required: str | None = None
    detail: str | None = None

    @classmethod
    def passing(cls) -> VetoResult:
        return cls(verdict=VetoVerdict.PASS)

    @classmethod
    def veto(
        cls,
        *,
        reason_code: str,
        owner_required: str,
        detail: str | None = None,
    ) -> VetoResult:
        if not reason_code.strip():
            raise ValueError("reason_code must be non-empty for a VETO result")
        if not owner_required.strip():
            raise ValueError("owner_required must be non-empty for a VETO result")
        return cls(
            verdict=VetoVerdict.VETO,
            reason_code=reason_code,
            owner_required=owner_required,
            detail=detail,
        )


@dataclass(frozen=True)
class AgentAction:
    """Base class for actions submitted to the sovereign veto.

    Concrete callers supply their domain-specific subclasses (lease clause,
    tenant screening decision, pricing recommendation). The veto dispatch
    only requires ``action_class`` — domain checks read the rest.
    """

    action_class: str

    def as_payload(self) -> dict[str, object]:
        """Return a JSON-serializable representation for the audit ledger.

        Subclasses with non-serializable fields should override. Default
        behaviour walks the dataclass ``__dict__`` and stringifies values
        that are not natively JSON-friendly.
        """
        result: dict[str, object] = {}
        for key, value in self.__dict__.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                result[key] = value
            elif isinstance(value, dict):
                # Best-effort: cast non-string keys to str and re-serialize values.
                result[key] = {str(k): _stringify(v) for k, v in value.items()}
            else:
                result[key] = _stringify(value)
        return result


def _stringify(value: object) -> object:
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_stringify(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _stringify(v) for k, v in value.items()}
    return str(value)


class ConstraintCheck(ABC):
    """Interface implemented by every domain-specific veto check.

    The Fair Housing Pre-Flight Gate (ADR-0008), Lease Provenance check
    (ADR-0007), Tenant PII residency check (ADR-0009), and an antitrust
    coordination check all subclass ``ConstraintCheck`` and register
    themselves with a ``SovereignVeto`` instance at startup.
    """

    @abstractmethod
    def evaluate(self, action: AgentAction) -> VetoResult: ...


@dataclass(frozen=True)
class SovereignBypass:
    """A human-authorized override of a veto, with logged owner and basis.

    The bypass authorizes a SINGLE decision. It cannot be a standing waiver.
    Owner and regulatory_basis are required and validated at construction.
    """

    veto_reason_code: str
    owner: str
    regulatory_basis: str
    justification: str

    def __post_init__(self) -> None:
        if not self.veto_reason_code.strip():
            raise ValueError("veto_reason_code must be non-empty")
        if not self.owner.strip():
            raise ValueError("owner must be non-empty")
        if not self.regulatory_basis.strip():
            raise ValueError("regulatory_basis must be non-empty")
        if not self.justification.strip():
            raise ValueError("justification must be non-empty")


@dataclass
class SovereignVeto:
    """Dispatch layer for constraint-surface-specific checks.

    A SovereignVeto instance carries a registry of ``action_class`` →
    ``ConstraintCheck``. Calls to ``check(action)`` dispatch to the
    registered surface, evaluate the check, log the verdict to the audit
    ledger (if one is wired), and return a structured ``VetoResult``.

    Calls for an unregistered ``action_class`` are conservatively vetoed
    with ``UNKNOWN-ACTION-CLASS`` — the framework refuses to let an agent
    sneak past the veto by inventing a new action class.
    """

    ledger: AuditLedger | None = None
    _registry: dict[str, ConstraintCheck] = field(default_factory=dict, init=False, repr=False)

    def register(self, action_class: str, check: ConstraintCheck) -> SovereignVeto:
        if not action_class.strip():
            raise ValueError("action_class must be non-empty")
        self._registry[action_class] = check
        return self

    def check(self, action: AgentAction) -> VetoResult:
        constraint_check = self._registry.get(action.action_class)
        if constraint_check is None:
            result = VetoResult(
                verdict=VetoVerdict.VETO,
                reason_code="UNKNOWN-ACTION-CLASS",
                owner_required="ops:on_call_compliance",
                detail=(
                    f"No constraint check registered for action_class "
                    f"{action.action_class!r}. The veto fails closed by default."
                ),
            )
        else:
            result = constraint_check.evaluate(action)

        self._record_decision(action=action, result=result)
        return result

    def record_bypass(self, bypass: SovereignBypass) -> None:
        """Write a bypass entry to the audit ledger.

        The original veto entry remains untouched. The bypass is a *new*
        entry — that ADR-0003 invariant is the whole point of the ledger
        being append-only.
        """
        if self.ledger is None:
            return

        gate_verdicts = {
            "veto_reason_code": bypass.veto_reason_code,
            "regulatory_basis": bypass.regulatory_basis,
            "justification": bypass.justification,
        }
        payload = json.dumps(
            {
                "veto_reason_code": bypass.veto_reason_code,
                "owner": bypass.owner,
                "regulatory_basis": bypass.regulatory_basis,
                "justification": bypass.justification,
            },
            sort_keys=True,
        ).encode("utf-8")
        self.ledger.append(
            actor_kind=ActorKind.HUMAN,
            actor_id=bypass.owner,
            decision_type="sovereign_bypass",
            action_payload=payload,
            gate_verdicts=gate_verdicts,
        )

    def _record_decision(self, *, action: AgentAction, result: VetoResult) -> None:
        if self.ledger is None:
            return

        gate_verdicts: dict[str, str] = {"verdict": result.verdict.value}
        if result.reason_code:
            gate_verdicts["reason_code"] = result.reason_code
        if result.owner_required:
            gate_verdicts["owner_required"] = result.owner_required

        payload = json.dumps(
            {
                "action_class": action.action_class,
                "action": action.as_payload(),
                "detail": result.detail,
            },
            sort_keys=True,
            default=_stringify,
        ).encode("utf-8")

        self.ledger.append(
            actor_kind=ActorKind.SYSTEM,
            actor_id="sovereign_veto",
            decision_type="sovereign_veto",
            action_payload=payload,
            gate_verdicts=gate_verdicts,
        )
