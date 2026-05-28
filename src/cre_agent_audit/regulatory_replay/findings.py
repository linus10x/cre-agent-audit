"""Dataclass surface for the regulatory-incident replay framework.

`Finding`, `Severity`, `Evidence`, `Citation`, `ADRRef` are the shared
vocabulary every matter speaks. The Protocol in `replay.py` accepts
`tuple[Finding, ...]` as the expected-findings contract; the
`EvidenceBundle` in `evidence_bundle.py` serializes them to JSON.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    """Finding severity, mapped to the Big-4 audit deliverable scale."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass(frozen=True)
class Citation:
    """A primary-source citation for a regulatory anchor.

    Verbatim case identification per CLAUDE.md voice rules: case name,
    court (or agency), docket, ISO-8601 date. `url` is optional but
    encouraged for verifiability.
    """

    case_name: str
    court: str
    docket: str
    date_iso: str
    url: str | None = None


@dataclass(frozen=True)
class ADRRef:
    """Reference to an ADR by number.

    The framework's patterns are numbered ADR-0001 through ADR-NNNN.
    `__str__` formats as ``"ADR-NNNN"`` for findings reports.
    """

    number: int
    title: str

    def __str__(self) -> str:
        return f"ADR-{self.number:04d}"


@dataclass(frozen=True)
class Evidence:
    """Where in the audit chain the finding's signal lives.

    `chain_sequence_range` is a ``(start, end)`` tuple over
    ``AuditEntry.sequence`` numbers; `verdict` is the one-line
    plain-English signal.
    """

    chain_sequence_range: tuple[int, int]
    verdict: str


@dataclass(frozen=True)
class Finding:
    """One finding the replay surfaces.

    Anchored on `pattern` (which ADR caught it), `severity` (Big-4
    scale), `evidence` (where in the chain), `regulatory_anchor`
    (primary-source citation), and `remediation` (the one-paragraph
    operator action).
    """

    pattern: ADRRef
    severity: Severity
    evidence: Evidence
    regulatory_anchor: Citation
    remediation: str
