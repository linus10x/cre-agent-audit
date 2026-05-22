"""Tenant-PII Data-Residency Partitioning — ADR-0009 (CRE-native).

Tenant data is segregated by jurisdiction at the storage layer. Every read
that crosses a jurisdiction boundary requires a typed ``LegalBasis`` tag
and a specific recorded purpose. Vague purposes ("analytics", "operations")
are insufficient on their face.

Veto reason codes emitted by ``TenantPIIResidencyCheck``:

    RESIDENCY-CROSS-JURISDICTION-UNTAGGED  no LegalBasis on cross-jurisdiction read
    RESIDENCY-CONSENT-MISSING              CONSENT basis without consent_record_id
    RESIDENCY-LIA-MISSING                  LEGITIMATE_INTEREST basis without lia_document_id
    RESIDENCY-STATUTE-MISSING              LEGAL_OBLIGATION basis without statute_citation
    RESIDENCY-PURPOSE-VAGUE                purpose is generic, not specific to a use case

GC sign-off is required for any human bypass (per ADR-0009). The bypass
record format mirrors ADR-0008's ``FairHousingException``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from cre_agent_audit.governance.sovereign_veto import (
    AgentAction,
    ConstraintCheck,
    VetoResult,
)


class LegalBasis(Enum):
    """Lawful basis taxonomy aligned with GDPR Art. 6.

    CCPA/CPRA does not use the identical taxonomy but maps onto these four
    per ADR-0009.
    """

    CONSENT = "consent"
    """GDPR Art. 6(1)(a) — requires ``consent_record_id``."""

    CONTRACT = "contract"
    """GDPR Art. 6(1)(b) — lease performance is the canonical CRE example."""

    LEGITIMATE_INTEREST = "legitimate_interest"
    """GDPR Art. 6(1)(f) — requires a documented LIA (``lia_document_id``)."""

    LEGAL_OBLIGATION = "legal_obligation"
    """GDPR Art. 6(1)(c) — requires a ``statute_citation``."""


_VAGUE_PURPOSE_TERMS: frozenset[str] = frozenset(
    {
        "analytics",
        "operations",
        "reporting",
        "business intelligence",
        "ops",
        "bi",
        "general use",
        "internal use",
        "research",
    }
)
"""Single-word or short phrases that are not specific enough to satisfy ADR-0009.

The rule is: a purpose must name a specific use case (e.g., "delinquency-risk
modeling for occupancy-cost report Q3 2026"), not a generic category.
"""


@dataclass(frozen=True)
class CrossJurisdictionRequest:
    """A request to read tenant PII potentially across a jurisdiction boundary."""

    requesting_actor: str
    requesting_jurisdiction: str
    target_record_jurisdiction: str
    legal_basis: LegalBasis | None
    purpose: str
    statute_citation: str | None = None
    lia_document_id: str | None = None
    consent_record_id: str | None = None

    def __post_init__(self) -> None:
        if not self.requesting_actor.strip():
            raise ValueError("requesting_actor must be non-empty")
        if not self.requesting_jurisdiction.strip():
            raise ValueError("requesting_jurisdiction must be non-empty")
        if not self.target_record_jurisdiction.strip():
            raise ValueError("target_record_jurisdiction must be non-empty")
        if not self.purpose.strip():
            raise ValueError("purpose must be non-empty")

    @property
    def is_cross_jurisdiction(self) -> bool:
        return self.requesting_jurisdiction != self.target_record_jurisdiction


@dataclass(frozen=True)
class TenantPIIAction(AgentAction):
    """A tenant-PII read routed through the residency gate."""

    request: CrossJurisdictionRequest = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.request is None:
            raise ValueError("TenantPIIAction requires a CrossJurisdictionRequest")


@dataclass
class TenantPIIResidencyCheck(ConstraintCheck):
    """Constraint check for cross-jurisdiction tenant-PII reads per ADR-0009."""

    extra_vague_terms: frozenset[str] = field(default_factory=frozenset)
    """Operator-supplied additional vague-purpose terms (lowercase)."""

    _DEFAULT_OWNER = "legal:gc"

    def evaluate(self, action: AgentAction) -> VetoResult:
        if not isinstance(action, TenantPIIAction):
            return VetoResult.veto(
                reason_code="UNKNOWN-ACTION-CLASS",
                owner_required=self._DEFAULT_OWNER,
                detail=(
                    "TenantPIIResidencyCheck received an action that is not a "
                    "TenantPIIAction."
                ),
            )

        request = action.request

        # Intra-jurisdiction reads pass through without gate cost beyond the
        # partition check (the partition check itself is enforced at the
        # storage layer and is out of scope for this module per ADR-0009).
        if not request.is_cross_jurisdiction:
            return VetoResult.passing()

        # Cross-jurisdiction reads require a LegalBasis tag.
        if request.legal_basis is None:
            return VetoResult.veto(
                reason_code="RESIDENCY-CROSS-JURISDICTION-UNTAGGED",
                owner_required=self._DEFAULT_OWNER,
                detail=(
                    f"Cross-jurisdiction read from "
                    f"{request.requesting_jurisdiction!r} to "
                    f"{request.target_record_jurisdiction!r} without a LegalBasis. "
                    f"GDPR Art. 6 / CCPA / state tenant-data statutes all require "
                    f"an enumerated lawful basis."
                ),
            )

        # Basis-specific completeness checks.
        if request.legal_basis is LegalBasis.CONSENT and not (
            request.consent_record_id and request.consent_record_id.strip()
        ):
            return VetoResult.veto(
                reason_code="RESIDENCY-CONSENT-MISSING",
                owner_required=self._DEFAULT_OWNER,
                detail="LegalBasis.CONSENT requires a consent_record_id.",
            )

        if request.legal_basis is LegalBasis.LEGITIMATE_INTEREST and not (
            request.lia_document_id and request.lia_document_id.strip()
        ):
            return VetoResult.veto(
                reason_code="RESIDENCY-LIA-MISSING",
                owner_required=self._DEFAULT_OWNER,
                detail=(
                    "LegalBasis.LEGITIMATE_INTEREST requires a documented LIA "
                    "(lia_document_id) covering the requesting purpose."
                ),
            )

        if request.legal_basis is LegalBasis.LEGAL_OBLIGATION and not (
            request.statute_citation and request.statute_citation.strip()
        ):
            return VetoResult.veto(
                reason_code="RESIDENCY-STATUTE-MISSING",
                owner_required=self._DEFAULT_OWNER,
                detail="LegalBasis.LEGAL_OBLIGATION requires a statute_citation.",
            )

        # Purpose specificity.
        purpose_lower = request.purpose.strip().lower()
        vague_terms = _VAGUE_PURPOSE_TERMS | self.extra_vague_terms
        if purpose_lower in vague_terms:
            return VetoResult.veto(
                reason_code="RESIDENCY-PURPOSE-VAGUE",
                owner_required=self._DEFAULT_OWNER,
                detail=(
                    f"purpose {request.purpose!r} is generic. ADR-0009 requires a "
                    f"specific use case naming the report, time window, and metric."
                ),
            )

        return VetoResult.passing()
