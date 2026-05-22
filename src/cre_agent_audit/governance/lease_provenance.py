"""Lease-Abstraction Provenance Chain — ADR-0007 (CRE-native).

Every clause an AI extracts from a lease carries a typed Provenance object.
A clause missing any component of provenance — or carrying low confidence
on a material clause, or carrying an unknown document hash, or carrying a
stale model version — is vetoed at the agent boundary by the sovereign
veto (ADR-0002). The clause does not reach the system of record.

This module implements the five veto reason codes named in ADR-0007:

    PROV-INCOMPLETE-MATERIAL       material clause missing required field
    PROV-INCOMPLETE-SIGNIFICANT    significant clause missing required field
    PROV-LOW-CONFIDENCE-MATERIAL   material clause confidence below threshold
    PROV-HASH-MISMATCH             document_hash not in lease repository
    PROV-STALE-MODEL               model_version below minimum for criticality
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime

from cre_agent_audit.governance.sovereign_veto import (
    AgentAction,
    ConstraintCheck,
    VetoResult,
)
from cre_agent_audit.schemas.lease_clause import (
    ClauseCriticality,
    ExtractedClause,
)


def compute_reviewer_sigil(reviewer_id: str, clause_text: str, reviewed_at: datetime) -> str:
    """Return the SHA-256 sigil binding a reviewer to a specific clause + time.

    The sigil makes a reviewer signature non-forgeable: any change to the
    clause text or the timestamp produces a different sigil. The lease
    administrator's identity provider signs the (reviewer_id, sigil) pair.
    """
    payload = f"{reviewer_id}|{clause_text}|{reviewed_at.isoformat()}".encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class LeaseClauseAction(AgentAction):
    """A lease-abstraction action proposing one ExtractedClause for the SoR.

    Sovereign-veto dispatch reads ``action_class`` (always
    ``"lease_abstraction"``); the rest is consumed by ``LeaseProvenanceCheck``.
    """

    clause: ExtractedClause = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.clause is None:
            raise ValueError("LeaseClauseAction requires a clause")


@dataclass(frozen=True)
class LeaseRepository:
    """The set of document hashes the lease-admin team has on file.

    Provenance hash-mismatch fires when an AI-extracted clause carries a
    document_hash that is not in this repository. In production this is
    backed by the lease-storage system; in v0.2 it's an in-memory set.
    """

    known_hashes: frozenset[str] = field(default_factory=frozenset)

    def has(self, document_hash: str) -> bool:
        return document_hash in self.known_hashes


@dataclass
class LeaseProvenanceCheck(ConstraintCheck):
    """Sovereign-veto constraint check for lease-abstraction actions.

    Implements the five PROV-* veto reason codes from ADR-0007. The check
    is constraint-surface-specific and registered against
    ``"lease_abstraction"`` on a ``SovereignVeto`` instance.
    """

    repository: LeaseRepository = field(default_factory=LeaseRepository)
    """Document hashes the lease-admin team has on file."""

    material_min_confidence: float = 0.85
    """Configurable per portfolio. Default per ADR-0007."""

    min_model_version_material: str | None = None
    """Lex-comparable model version. ``None`` disables the check."""

    allowed_model_versions: frozenset[str] = field(default_factory=frozenset)
    """Optional explicit allowlist. ``None``/empty disables the check (the model is allowed)."""

    _DEFAULT_OWNER = "ops:lease_admin_lead"

    def evaluate(self, action: AgentAction) -> VetoResult:
        if not isinstance(action, LeaseClauseAction):
            return VetoResult.veto(
                reason_code="UNKNOWN-ACTION-CLASS",
                owner_required=self._DEFAULT_OWNER,
                detail=(
                    "LeaseProvenanceCheck received an action that is not a "
                    "LeaseClauseAction."
                ),
            )

        clause = action.clause
        provenance = clause.provenance

        # 1. Hash mismatch (fires first because it invalidates everything downstream).
        if not self.repository.has(provenance.document_hash):
            return VetoResult.veto(
                reason_code="PROV-HASH-MISMATCH",
                owner_required=self._DEFAULT_OWNER,
                detail=(
                    f"document_hash {provenance.document_hash[:12]}... not in "
                    "lease repository. The extraction may reference a hallucinated "
                    "document or an out-of-band source."
                ),
            )

        # 2. Stale model version (per criticality).
        if (
            clause.criticality is ClauseCriticality.MATERIAL
            and self.min_model_version_material is not None
            and self.allowed_model_versions
            and provenance.model_version not in self.allowed_model_versions
        ):
            return VetoResult.veto(
                reason_code="PROV-STALE-MODEL",
                owner_required=self._DEFAULT_OWNER,
                detail=(
                    f"model_version {provenance.model_version!r} is not in the "
                    f"allowlist {sorted(self.allowed_model_versions)!r} for "
                    f"{clause.criticality.value} clauses."
                ),
            )

        # 3. Criticality-specific completeness.
        if clause.criticality is ClauseCriticality.MATERIAL:
            if provenance.reviewer_signature is None:
                return VetoResult.veto(
                    reason_code="PROV-INCOMPLETE-MATERIAL",
                    owner_required=self._DEFAULT_OWNER,
                    detail=(
                        "Material clauses require a ReviewerSignature. The lease-"
                        "admin team retains responsibility for material clauses."
                    ),
                )
            if provenance.extraction_confidence < self.material_min_confidence:
                return VetoResult.veto(
                    reason_code="PROV-LOW-CONFIDENCE-MATERIAL",
                    owner_required=self._DEFAULT_OWNER,
                    detail=(
                        f"Material clause extracted with confidence "
                        f"{provenance.extraction_confidence:.2f} < "
                        f"threshold {self.material_min_confidence:.2f}."
                    ),
                )

        if (
            clause.criticality is ClauseCriticality.SIGNIFICANT
            and provenance.extraction_confidence <= 0.0
        ):
            return VetoResult.veto(
                reason_code="PROV-INCOMPLETE-SIGNIFICANT",
                owner_required=self._DEFAULT_OWNER,
                detail=(
                    "Significant clause carries zero extraction confidence; "
                    "the model emitted the clause without a confidence "
                    "signal. Re-extract or escalate."
                ),
            )

        # ROUTINE clauses pass through with valid hash + paragraph + confidence > 0.
        return VetoResult.passing()
