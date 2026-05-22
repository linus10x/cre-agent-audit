"""Typed objects for tenant-screening decisions — supports ADR-0008.

The Fair-Housing Pre-Flight Gate (ADR-0008) consumes ``ScreeningDecision``
and either passes the action through or vetoes with one of the five FHA-*
reason codes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ProtectedSurface(Enum):
    """Decision surfaces that route through the Fair-Housing Pre-Flight Gate.

    Per ADR-0008. A surface is protected if a decision on that surface has
    been subject to FHA, ECOA, or state-AI-act enforcement, or if reasonable
    counsel would identify it as protected-class-adjacent.
    """

    TENANT_SCREENING = "tenant_screening"
    RENEWAL_PRICING = "renewal_pricing"
    MARKETING_AUDIENCE_TARGETING = "marketing_audience_targeting"
    HOUSING_CREDIT_DECISION = "housing_credit_decision"
    TENANT_COMMUNICATION_PERSONALIZATION = "tenant_communication_personalization"


class Decision(Enum):
    APPROVE = "approve"
    DENY = "deny"
    REVIEW = "review"


@dataclass(frozen=True)
class ScreeningDecision:
    """AI-proposed screening decision, prior to the Fair-Housing gate.

    ``features`` is the input feature vector the model used. The gate
    inspects feature names against per-jurisdiction proxy lists, voucher
    indicators, source-of-income indicators, and criminal-history features.
    """

    decision_id: str
    applicant_id_anon: str
    surface: ProtectedSurface
    features: dict[str, float | str | bool]
    score: float
    decision: Decision
    jurisdiction: str
    model_version: str

    def __post_init__(self) -> None:
        if not self.decision_id.strip():
            raise ValueError("decision_id must be non-empty")
        if not self.applicant_id_anon.strip():
            raise ValueError("applicant_id_anon must be non-empty")
        if not self.jurisdiction.strip():
            raise ValueError("jurisdiction must be non-empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be in [0.0, 1.0]")


class AuthorityLevel(Enum):
    """Bypass authority levels per ADR-0008."""

    MANAGER = "manager"
    DIRECTOR = "director"
    GC = "gc"  # general counsel — highest authority


@dataclass(frozen=True)
class FairHousingException:
    """A durable logged exception authorizing a one-time gate bypass.

    Per ADR-0008. Cannot be edited or deleted after creation. Three bypasses
    by the same owner in a 90-day window auto-escalate to GC. Five bypasses
    on the same reason code in 90 days force the program to DEFCON-4.
    """

    exception_id: str
    decision_id: str
    veto_reason_code: str  # e.g., FHA-VOUCHER
    bypass_owner: str
    bypass_justification: str
    bypass_authority: AuthorityLevel
    timestamp: datetime
    audit_chain_sigil: str  # hash anchor on the audit chain (ADR-0003)

    def __post_init__(self) -> None:
        if not self.exception_id.strip():
            raise ValueError("exception_id must be non-empty")
        if not self.decision_id.strip():
            raise ValueError("decision_id must be non-empty")
        if not self.veto_reason_code.strip():
            raise ValueError("veto_reason_code must be non-empty")
        if not self.bypass_owner.strip():
            raise ValueError("bypass_owner must be non-empty")
        if not self.bypass_justification.strip():
            raise ValueError("bypass_justification must be non-empty")
        if not self.audit_chain_sigil.strip():
            raise ValueError("audit_chain_sigil must be non-empty")


# State-level Source-of-Income ordinance jurisdictions per ADR-0008.
# Federal SOI is not protected; the state list lives in compliance_rules.yaml
# in production. This minimal default is shipped with the gate so it works
# out of the box; operators override via compliance_rules.yaml.
DEFAULT_SOI_PROTECTED_JURISDICTIONS: frozenset[str] = frozenset(
    {"CA", "CT", "DC", "MA", "MN", "NJ", "NY", "OR", "VT", "WA"}
)


@dataclass(frozen=True)
class JurisdictionRules:
    """Per-jurisdiction toggles for the 5 Fair-Housing checks."""

    jurisdiction: str
    soi_protected: bool
    criminal_history_individualized_assessment_required: bool = True
    criminal_history_lookback_limit_years: int | None = 7
    proxy_features_blocked: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "applicant_zip_only",  # zip-only is a known race proxy
                "preferred_language",  # proxies for national origin
                "first_name_origin_score",  # proxies for protected class
            }
        )
    )
