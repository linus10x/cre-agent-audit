"""IncidentReplay Protocol + IncidentReplayBase + ReplayResult.

A subclass of ``IncidentReplayBase`` implements one named regulatory
matter. The base provides the dataclass attributes; subclasses override
the three callables. ``ReplayResult`` is the returned value,
JSON-serializable for the evidence bundle.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.regulatory_replay.findings import (
    ADRRef,
    Citation,
    Finding,
)


@runtime_checkable
class IncidentReplay(Protocol):
    """The Protocol surface every matter implements.

    Five class attributes describe the matter; three methods produce
    the runnable artifacts. ``IncidentReplayBase`` provides default
    implementations of the class attributes; subclasses override.
    """

    matter_id: str
    matter_title: str
    primary_sources: tuple[Citation, ...]
    failure_shape: str
    patterns_engaged: tuple[ADRRef, ...]

    def synthetic_dataset(self) -> Iterable[Any]: ...

    def run_replay(
        self,
        *,
        ledger: AuditLedger,
        gates: Mapping[str, object],
    ) -> ReplayResult: ...

    def expected_findings(self) -> tuple[Finding, ...]: ...


class IncidentReplayBase:
    """Base class for matter implementations.

    Subclasses define the five class attributes and the three methods.
    The base does not enforce abstractness via ABC because ``Protocol``
    ``runtime_checkable`` already gives us the shape check we need.
    """

    matter_id: str = ""
    matter_title: str = ""
    primary_sources: tuple[Citation, ...] = ()
    failure_shape: str = ""
    patterns_engaged: tuple[ADRRef, ...] = ()

    def synthetic_dataset(self) -> Iterable[Any]:
        raise NotImplementedError

    def run_replay(
        self,
        *,
        ledger: AuditLedger,
        gates: Mapping[str, object],
    ) -> ReplayResult:
        raise NotImplementedError

    def expected_findings(self) -> tuple[Finding, ...]:
        raise NotImplementedError


@dataclass(frozen=True)
class ReplayResult:
    """The output of a single matter replay.

    Serializable to JSON via ``to_dict()`` for the evidence bundle.
    """

    matter_id: str
    findings_produced: tuple[Finding, ...]
    chain_entries_written: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "chain_entries_written": self.chain_entries_written,
            "findings_produced": [
                {
                    "pattern": str(f.pattern),
                    "pattern_title": f.pattern.title,
                    "severity": f.severity.value,
                    "evidence": {
                        "chain_sequence_range": list(f.evidence.chain_sequence_range),
                        "verdict": f.evidence.verdict,
                    },
                    "regulatory_anchor": {
                        "case_name": f.regulatory_anchor.case_name,
                        "court": f.regulatory_anchor.court,
                        "docket": f.regulatory_anchor.docket,
                        "date_iso": f.regulatory_anchor.date_iso,
                        "url": f.regulatory_anchor.url,
                    },
                    "remediation": f.remediation,
                }
                for f in self.findings_produced
            ],
        }
