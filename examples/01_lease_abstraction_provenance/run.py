"""Example 01 — Lease Abstraction Provenance Chain.

Demonstrates the full ADR-0007 boundary stack: DEFCON → Sovereign Veto →
LeaseProvenanceCheck → Audit Ledger. Three cases:
- A material clause with full provenance + reviewer signature → PASS
- A material clause missing the reviewer signature → VETO PROV-INCOMPLETE-MATERIAL
- A material clause referencing an unknown document_hash → VETO PROV-HASH-MISMATCH

Run:
    python examples/01_lease_abstraction_provenance/run.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.governance.defcon import Capability, DefconController, DefconState
from cre_agent_audit.governance.lease_provenance import (
    LeaseClauseAction,
    LeaseProvenanceCheck,
    LeaseRepository,
    compute_reviewer_sigil,
)
from cre_agent_audit.governance.sovereign_veto import SovereignVeto
from cre_agent_audit.schemas.lease_clause import (
    ClauseCriticality,
    ExtractedClause,
    Provenance,
    ReviewerSignature,
)

KNOWN_DOC_HASH = "a" * 64
UNKNOWN_DOC_HASH = "b" * 64
NOW = datetime(2026, 5, 22, 12, 0, 0, tzinfo=timezone.utc)


def signature(reviewer_id: str, clause_text: str) -> ReviewerSignature:
    return ReviewerSignature(
        reviewer_id=reviewer_id,
        reviewed_at=NOW,
        sigil=compute_reviewer_sigil(reviewer_id, clause_text, NOW),
    )


def make_clause(
    *,
    text: str,
    criticality: ClauseCriticality,
    doc_hash: str = KNOWN_DOC_HASH,
    confidence: float = 0.94,
    reviewer: ReviewerSignature | None = None,
) -> ExtractedClause:
    return ExtractedClause(
        clause_id=f"clause-{text[:6]}",
        text=text,
        criticality=criticality,
        schema={"raw_text": text},
        provenance=Provenance(
            document_hash=doc_hash,
            page=4,
            paragraph=(2, 3),
            extraction_confidence=confidence,
            model_version="claude-opus-4-7",
            extracted_at=NOW,
            reviewer_signature=reviewer,
        ),
    )


def main() -> int:
    print("Example 01 — Lease Abstraction Provenance Chain")
    print("=" * 60)

    defcon = DefconController(initial_state=DefconState.NORMAL)
    ledger = AuditLedger()
    repository = LeaseRepository(known_hashes=frozenset({KNOWN_DOC_HASH}))
    check = LeaseProvenanceCheck(repository=repository)
    veto = SovereignVeto(ledger=ledger).register("lease_abstraction", check)

    if not defcon.is_allowed(Capability.LEASE_ABSTRACTION):
        print(f"DEFCON state {defcon.state.name} blocks LEASE_ABSTRACTION.")
        return 1

    cases = [
        (
            "Material clause with full provenance + reviewer signature",
            make_clause(
                text="Base rent: $42.50/sqft, escalating 3% annually.",
                criticality=ClauseCriticality.MATERIAL,
                reviewer=signature("reviewer:alice", "Base rent: $42.50/sqft, escalating 3% annually."),
            ),
        ),
        (
            "Material clause MISSING reviewer signature",
            make_clause(
                text="Tenant may terminate on 6 months' notice after year 5.",
                criticality=ClauseCriticality.MATERIAL,
                reviewer=None,
            ),
        ),
        (
            "Material clause referencing UNKNOWN document hash",
            make_clause(
                text="Co-tenancy clause: anchor vacancy triggers rent abatement.",
                criticality=ClauseCriticality.MATERIAL,
                doc_hash=UNKNOWN_DOC_HASH,
                reviewer=signature("reviewer:bob", "Co-tenancy clause: anchor vacancy triggers rent abatement."),
            ),
        ),
        (
            "Routine clause (boilerplate) with full provenance",
            make_clause(
                text="Notices shall be deemed received three business days after mailing.",
                criticality=ClauseCriticality.ROUTINE,
                reviewer=None,
            ),
        ),
    ]

    for label, clause in cases:
        action = LeaseClauseAction(action_class="lease_abstraction", clause=clause)
        result = veto.check(action)
        suffix = f" reason: {result.reason_code}" if result.reason_code else ""
        print(f"{label}")
        print(f"  → {result.verdict.value}{suffix}")

    print(f"\nTotal audit entries: {len(ledger.entries)} (every clause decision recorded)")
    ledger.verify_chain()
    print("Audit chain verified intact ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
