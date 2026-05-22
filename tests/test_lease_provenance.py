"""Tests for Lease-Abstraction Provenance Chain — ADR-0007."""

from __future__ import annotations

from datetime import datetime, timezone

from cre_agent_audit.governance.lease_provenance import (
    LeaseClauseAction,
    LeaseProvenanceCheck,
    LeaseRepository,
    compute_reviewer_sigil,
)
from cre_agent_audit.governance.sovereign_veto import VetoVerdict
from cre_agent_audit.schemas.lease_clause import (
    ClauseCriticality,
    ExtractedClause,
    Provenance,
    ReviewerSignature,
)

_DOC_HASH = "a" * 64  # 64-char hex sha256


def _now() -> datetime:
    return datetime(2026, 5, 22, 12, 0, 0, tzinfo=timezone.utc)


def _signature(reviewer_id: str, clause_text: str) -> ReviewerSignature:
    reviewed_at = _now()
    return ReviewerSignature(
        reviewer_id=reviewer_id,
        reviewed_at=reviewed_at,
        sigil=compute_reviewer_sigil(reviewer_id, clause_text, reviewed_at),
        notes=None,
    )


def _provenance(
    *,
    document_hash: str = _DOC_HASH,
    confidence: float = 0.92,
    model_version: str = "claude-opus-4-7",
    reviewer: ReviewerSignature | None = None,
) -> Provenance:
    return Provenance(
        document_hash=document_hash,
        page=4,
        paragraph=(2, 3),
        extraction_confidence=confidence,
        model_version=model_version,
        extracted_at=_now(),
        reviewer_signature=reviewer,
        bounding_box=None,
    )


def _clause(
    *,
    criticality: ClauseCriticality,
    provenance: Provenance,
    text: str = "Base rent: $42.50/sqft, escalating 3% annually.",
) -> ExtractedClause:
    return ExtractedClause(
        clause_id="clause-001",
        text=text,
        criticality=criticality,
        schema={"rent_amount": 42.50, "escalation_rate": 0.03},
        provenance=provenance,
    )


def _action(clause: ExtractedClause) -> LeaseClauseAction:
    return LeaseClauseAction(action_class="lease_abstraction", clause=clause)


class TestMaterialClauseRequiresAllFields:
    def test_material_with_full_provenance_passes(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(repository=repo)
        clause = _clause(
            criticality=ClauseCriticality.MATERIAL,
            provenance=_provenance(reviewer=_signature("reviewer:alice", "x")),
            text="x",
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.PASS

    def test_material_missing_reviewer_signature_vetoes(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(repository=repo)
        clause = _clause(
            criticality=ClauseCriticality.MATERIAL,
            provenance=_provenance(reviewer=None),
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "PROV-INCOMPLETE-MATERIAL"

    def test_low_confidence_material_vetoes(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(repository=repo)
        clause = _clause(
            criticality=ClauseCriticality.MATERIAL,
            provenance=_provenance(
                confidence=0.81, reviewer=_signature("reviewer:alice", "x")
            ),
            text="x",
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "PROV-LOW-CONFIDENCE-MATERIAL"

    def test_low_confidence_material_threshold_is_configurable(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(repository=repo, material_min_confidence=0.70)
        clause = _clause(
            criticality=ClauseCriticality.MATERIAL,
            provenance=_provenance(
                confidence=0.72, reviewer=_signature("reviewer:alice", "x")
            ),
            text="x",
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.PASS


class TestSignificantClause:
    def test_significant_with_full_provenance_passes_without_signature(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(repository=repo)
        clause = _clause(
            criticality=ClauseCriticality.SIGNIFICANT,
            provenance=_provenance(reviewer=None),
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.PASS

    def test_significant_missing_confidence_zero_vetoes(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(repository=repo)
        clause = _clause(
            criticality=ClauseCriticality.SIGNIFICANT,
            provenance=_provenance(confidence=0.0),
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "PROV-INCOMPLETE-SIGNIFICANT"


class TestRoutineClause:
    def test_routine_with_full_provenance_passes(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(repository=repo)
        clause = _clause(
            criticality=ClauseCriticality.ROUTINE,
            provenance=_provenance(),
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.PASS


class TestHashMismatch:
    def test_unknown_document_hash_vetoes(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(repository=repo)
        clause = _clause(
            criticality=ClauseCriticality.MATERIAL,
            provenance=_provenance(
                document_hash="b" * 64,
                reviewer=_signature("reviewer:alice", "x"),
            ),
            text="x",
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "PROV-HASH-MISMATCH"


class TestStaleModel:
    def test_stale_model_for_material_vetoes(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(
            repository=repo,
            min_model_version_material="claude-opus-4-6",
            allowed_model_versions={"claude-opus-4-6", "claude-opus-4-7"},
        )
        clause = _clause(
            criticality=ClauseCriticality.MATERIAL,
            provenance=_provenance(
                model_version="claude-opus-4-5",  # below min
                reviewer=_signature("reviewer:alice", "x"),
            ),
            text="x",
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "PROV-STALE-MODEL"

    def test_model_at_or_above_min_passes(self) -> None:
        repo = LeaseRepository(known_hashes={_DOC_HASH})
        check = LeaseProvenanceCheck(
            repository=repo,
            min_model_version_material="claude-opus-4-6",
            allowed_model_versions={"claude-opus-4-6", "claude-opus-4-7"},
        )
        clause = _clause(
            criticality=ClauseCriticality.MATERIAL,
            provenance=_provenance(
                model_version="claude-opus-4-7",
                reviewer=_signature("reviewer:alice", "x"),
            ),
            text="x",
        )
        result = check.evaluate(_action(clause))
        assert result.verdict is VetoVerdict.PASS


class TestReviewerSigil:
    def test_reviewer_sigil_is_deterministic(self) -> None:
        ts = _now()
        sigil_a = compute_reviewer_sigil("reviewer:alice", "Base rent: $42.50", ts)
        sigil_b = compute_reviewer_sigil("reviewer:alice", "Base rent: $42.50", ts)
        assert sigil_a == sigil_b

    def test_reviewer_sigil_changes_on_text_change(self) -> None:
        ts = _now()
        sigil_a = compute_reviewer_sigil("reviewer:alice", "Base rent: $42.50", ts)
        sigil_b = compute_reviewer_sigil("reviewer:alice", "Base rent: $99.99", ts)
        assert sigil_a != sigil_b


class TestActionShape:
    def test_action_class_is_lease_abstraction(self) -> None:
        clause = _clause(
            criticality=ClauseCriticality.ROUTINE,
            provenance=_provenance(),
        )
        action = _action(clause)
        assert action.action_class == "lease_abstraction"
