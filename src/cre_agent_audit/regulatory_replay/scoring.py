"""Pattern-coverage scoring per matter.

For each matter, compare declared ``patterns_engaged`` against patterns
actually surfaced in ``findings_produced``. Returns a 0.0-to-1.0 score.
Used by the CLI to flag matter drift — replay outputs that no longer
match the declared coverage.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

from cre_agent_audit.regulatory_replay.replay import (
    IncidentReplayBase,
    ReplayResult,
)


def pattern_coverage_score(matter: IncidentReplayBase, result: ReplayResult) -> float:
    """Fraction of declared patterns that produced at least one finding."""
    declared = {adr.number for adr in matter.patterns_engaged}
    if not declared:
        return 0.0
    fired = {f.pattern.number for f in result.findings_produced}
    overlap = declared & fired
    return len(overlap) / len(declared)
