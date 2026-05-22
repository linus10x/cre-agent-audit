"""Shared base types for the 6-agent topology per ARCHITECTURE.md.

The agents are roles, not microservices — the same process can host multiple
agents in a small deployment, separated only by the orchestrator's routing
logic. Each role has one clear responsibility.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

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
