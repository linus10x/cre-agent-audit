"""DEFCON state machine — ADR-0001.

Five named operating states with per-state capability allowlists and logged
transitions. The DEFCON controller is the first check in the compose order
(see ARCHITECTURE.md). Unsafe-state actions are killed before any downstream
cost is incurred.

State semantics (per ADR-0001):

    DEFCON-5 NORMAL       All capabilities active. Standard audit.
    DEFCON-4 HEIGHTENED   Material-clause writes require human co-sign.
                          Other capabilities active.
    DEFCON-3 RESTRICTED   Tenant-screening + rent-optimization paused.
                          Lease abstraction continues with mandatory signature.
    DEFCON-2 CONTAINMENT  All writes paused. Agents read-only.
                          Audit ledger continues writing.
    DEFCON-1 SHUTDOWN     Agents offline. Audit ledger continues writing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum


class DefconState(Enum):
    """Five DEFCON levels. ``level`` mirrors the ADR-0001 numeric naming."""

    NORMAL = 5
    HEIGHTENED = 4
    RESTRICTED = 3
    CONTAINMENT = 2
    SHUTDOWN = 1

    @property
    def level(self) -> int:
        return int(self.value)


class Capability(Enum):
    """Agent capabilities checked against the DEFCON allowlist.

    The set is intentionally minimal in v0.2 and grows as additional governance
    modules surface new gated capabilities. Each capability is tagged in the
    allowlist matrix below.
    """

    # Read-only capabilities (allowed across all states except SHUTDOWN).
    LEASE_ABSTRACTION_READ = "lease_abstraction_read"
    RENT_COMP_INGEST = "rent_comp_ingest"

    # Mixed read/write capabilities.
    LEASE_ABSTRACTION = "lease_abstraction"  # extraction with reviewer signature path
    LEASE_MATERIAL_WRITE = "lease_material_write"  # material-clause write to SoR
    TENANT_SCREENING = "tenant_screening"
    RENT_OPTIMIZATION = "rent_optimization"

    # The audit ledger never stops. Required for the DEFCON guarantee in ADR-0003.
    AUDIT_WRITE = "audit_write"


@dataclass(frozen=True)
class CapabilityRule:
    allowed: bool
    requires_cosign: bool = False


# Per-state allowlist matrix. Codified directly from ADR-0001's state semantics.
# Capability rules default to (allowed=True, requires_cosign=False) when omitted.
_ALLOWLIST: dict[DefconState, dict[Capability, CapabilityRule]] = {
    DefconState.NORMAL: {capability: CapabilityRule(allowed=True) for capability in Capability},
    DefconState.HEIGHTENED: {
        **{capability: CapabilityRule(allowed=True) for capability in Capability},
        Capability.LEASE_MATERIAL_WRITE: CapabilityRule(allowed=True, requires_cosign=True),
    },
    DefconState.RESTRICTED: {
        Capability.LEASE_ABSTRACTION_READ: CapabilityRule(allowed=True),
        Capability.RENT_COMP_INGEST: CapabilityRule(allowed=True),
        Capability.LEASE_ABSTRACTION: CapabilityRule(allowed=True, requires_cosign=True),
        Capability.LEASE_MATERIAL_WRITE: CapabilityRule(allowed=True, requires_cosign=True),
        Capability.TENANT_SCREENING: CapabilityRule(allowed=False),
        Capability.RENT_OPTIMIZATION: CapabilityRule(allowed=False),
        Capability.AUDIT_WRITE: CapabilityRule(allowed=True),
    },
    DefconState.CONTAINMENT: {
        Capability.LEASE_ABSTRACTION_READ: CapabilityRule(allowed=True),
        Capability.RENT_COMP_INGEST: CapabilityRule(allowed=True),
        Capability.LEASE_ABSTRACTION: CapabilityRule(allowed=False),
        Capability.LEASE_MATERIAL_WRITE: CapabilityRule(allowed=False),
        Capability.TENANT_SCREENING: CapabilityRule(allowed=False),
        Capability.RENT_OPTIMIZATION: CapabilityRule(allowed=False),
        Capability.AUDIT_WRITE: CapabilityRule(allowed=True),
    },
    DefconState.SHUTDOWN: {capability: CapabilityRule(allowed=False) for capability in Capability}
    | {Capability.AUDIT_WRITE: CapabilityRule(allowed=True)},
}


@dataclass(frozen=True)
class DefconTransition:
    """One immutable transition record. Written to the audit ledger (ADR-0003)."""

    prior_state: DefconState
    new_state: DefconState
    actor: str
    reason: str
    timestamp: datetime
    estimated_duration: timedelta | None = None


@dataclass
class DefconController:
    """Single owner of the global DEFCON state.

    The controller is intentionally a plain dataclass without external dependencies.
    The audit-ledger hook in production is injected via the orchestrator (ADR-0001
    composes with ADR-0003 at the system boundary, not inside this module).
    """

    initial_state: DefconState = DefconState.NORMAL
    _history: list[DefconTransition] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        # Mutable state begins at the initial value; transitions update it.
        self._state: DefconState = self.initial_state

    @property
    def state(self) -> DefconState:
        return self._state

    @property
    def history(self) -> tuple[DefconTransition, ...]:
        return tuple(self._history)

    def is_allowed(self, capability: Capability) -> bool:
        rule = _ALLOWLIST[self._state].get(capability)
        if rule is None:
            # Conservative default: a capability not listed at this state is denied.
            return False
        return rule.allowed

    def requires_cosign(self, capability: Capability) -> bool:
        rule = _ALLOWLIST[self._state].get(capability)
        if rule is None or not rule.allowed:
            return False
        return rule.requires_cosign

    def transition_to(
        self,
        new_state: DefconState,
        *,
        actor: str,
        reason: str,
        estimated_duration: timedelta | None = None,
        now: datetime | None = None,
    ) -> DefconTransition:
        """Move the controller to ``new_state`` and record the transition.

        Every transition is logged. Idempotent transitions (no-op stays at same state)
        are still recorded — they carry operator intent. ADR-0001 is silent on the
        idempotency case; the convention here is "record everything, the ledger
        decides what to surface."
        """
        if not actor.strip():
            raise ValueError("actor must be non-empty")
        if not reason.strip():
            raise ValueError("reason must be non-empty")

        transition = DefconTransition(
            prior_state=self._state,
            new_state=new_state,
            actor=actor,
            reason=reason,
            timestamp=now or datetime.now(timezone.utc),
            estimated_duration=estimated_duration,
        )
        self._history.append(transition)
        self._state = new_state
        return transition
