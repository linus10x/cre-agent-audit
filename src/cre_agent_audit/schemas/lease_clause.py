"""Typed objects for lease-clause extraction — supports ADR-0007.

The `Provenance` object is the single typed gate between an AI extraction
and the system-of-record write. Without complete `Provenance`, the sovereign
veto fires and the clause never reaches the SoR.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class ClauseCriticality(Enum):
    """Three-tier criticality scaffold per ADR-0007."""

    MATERIAL = "material"
    """Rent schedule · break · options · jurisdiction · outgoings · co-tenancy."""

    SIGNIFICANT = "significant"
    """Use · permitted alterations · insurance · assignment."""

    ROUTINE = "routine"
    """Notice provisions · definitions · boilerplate."""


@dataclass(frozen=True)
class BoundingBox:
    """Pixel coordinates for visual highlighting in lease-review UI.

    Coordinates are expressed in PDF user units (1/72 inch). Origin is the
    bottom-left of the page (PDF convention, not screen convention).
    """

    page_width: float
    page_height: float
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("BoundingBox width and height must be positive")
        if self.x < 0 or self.y < 0:
            raise ValueError("BoundingBox x and y must be non-negative")


@dataclass(frozen=True)
class ReviewerSignature:
    """Human reviewer signature on a material clause.

    The ``sigil`` is the canonical proof the named reviewer signed off on
    this specific clause text at this specific time. Computing it lives in
    `lease_provenance.compute_reviewer_sigil`.
    """

    reviewer_id: str
    reviewed_at: datetime
    sigil: str
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.reviewer_id.strip():
            raise ValueError("reviewer_id must be non-empty")
        if not self.sigil.strip():
            raise ValueError("sigil must be non-empty")


@dataclass(frozen=True)
class Provenance:
    """Typed provenance for one AI-extracted clause.

    ``Provenance`` is the load-bearing structure for ADR-0007. Any missing
    component on a clause flagged ``MATERIAL`` triggers
    ``PROV-INCOMPLETE-MATERIAL`` at the sovereign-veto layer.
    """

    document_hash: str
    page: int
    paragraph: tuple[int, int]
    extraction_confidence: float
    model_version: str
    extracted_at: datetime
    reviewer_signature: ReviewerSignature | None = None
    bounding_box: BoundingBox | None = None

    def __post_init__(self) -> None:
        if not self.document_hash.strip():
            raise ValueError("document_hash must be non-empty")
        if self.page < 1:
            raise ValueError("page is 1-indexed; got " + str(self.page))
        start, end = self.paragraph
        if start < 0 or end < start:
            raise ValueError("paragraph must be (start, end) with start>=0 and end>=start")
        if not 0.0 <= self.extraction_confidence <= 1.0:
            raise ValueError("extraction_confidence must be in [0.0, 1.0]")
        if not self.model_version.strip():
            raise ValueError("model_version must be non-empty")


# ClauseSchema is intentionally a permissive ``dict`` in v0.2 — the typed
# per-clause-kind slot schemas (rent_amount, escalation_rate, break_date,
# co_tenancy_conditions, ...) ship in v0.2.x patches as concrete dataclasses
# alongside the lease-clause inventory tooling.
ClauseSchema = dict[str, Any]


@dataclass(frozen=True)
class ExtractedClause:
    """One AI-extracted clause with full provenance."""

    clause_id: str
    text: str
    criticality: ClauseCriticality
    schema: ClauseSchema
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.clause_id.strip():
            raise ValueError("clause_id must be non-empty")
        if not self.text.strip():
            raise ValueError("text must be non-empty")
