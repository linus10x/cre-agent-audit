"""Regulatory-incident replay framework (ADR-0014).

Adversarial-audit harness: replays the failure shape of named settled
matters against the cre-agent-audit framework, producing an audit-
evidence bundle showing which patterns would have caught the failure.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

from cre_agent_audit.regulatory_replay.evidence_bundle import EvidenceBundle
from cre_agent_audit.regulatory_replay.findings import (
    ADRRef,
    Citation,
    Evidence,
    Finding,
    Severity,
)
from cre_agent_audit.regulatory_replay.replay import (
    IncidentReplay,
    IncidentReplayBase,
    ReplayResult,
)
from cre_agent_audit.regulatory_replay.scoring import pattern_coverage_score

__all__ = [
    "ADRRef",
    "Citation",
    "Evidence",
    "EvidenceBundle",
    "Finding",
    "IncidentReplay",
    "IncidentReplayBase",
    "ReplayResult",
    "Severity",
    "pattern_coverage_score",
]
