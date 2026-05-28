# ADR-0007 · Lease-Abstraction Provenance Chain

**Status:** Accepted · CRE-native
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

When a lease clause becomes contested in litigation, the question is: how was it extracted, what was the model's confidence, and who validated it? This pattern produces that audit trail by construction — **provided the lease-abstraction pipeline (typically a third-party vendor: Leverton/MRI AI, V7 Lease, Reonomy) exposes the clause-level provenance object.** For vendor-shipped outputs that do not expose provenance natively, the operator's procurement-side power is the answer; see [`docs/vendor-clauses/abstraction.md`](../../docs/vendor-clauses/abstraction.md) for the contractual SLA template that obligates clause-level provenance disclosure.

AI lease abstraction is the highest-ROI CRE-AI use case. Leading firms report 10× deal-execution improvement. The number is real. The risk underneath is also real, and most operators are not pricing it.

The risk is hallucination at the clause level. An AI that misses a break clause does not produce a 1% accuracy drop visible on a metrics dashboard. It produces a missed renewal trigger that costs a portfolio more than the entire AI program saved. An AI that transposes a rent escalation produces a financial statement that ties to the wrong number. An AI that confabulates a co-tenancy clause produces a tenant-relations dispute that lands in litigation.

Lease abstraction in production runs at clause volumes (hundreds of clauses per lease, thousands of leases per portfolio per quarter) that exceed human review capacity. The pattern that works at scale is **structural traceability, not post-hoc review**.

## Decision

Every clause an AI extracts from a lease carries a typed **`Provenance`** object. A clause that is missing any component of the provenance object cannot be written to the system of record. The sovereign veto (ADR-0002) is the enforcement mechanism.

### The Provenance object

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ClauseCriticality(Enum):
    MATERIAL = "material"        # rent schedule · break · options · jurisdiction · outgoings · co-tenancy
    SIGNIFICANT = "significant"  # use · permitted alterations · insurance · assignment
    ROUTINE = "routine"          # notice provisions · definitions · boilerplate

@dataclass(frozen=True)
class Provenance:
    document_hash: str           # sha256 of source PDF · ties the clause to a specific document version
    page: int                    # 1-indexed page number
    paragraph: tuple[int, int]   # (start, end) paragraph index on the page
    extraction_confidence: float # 0.0 – 1.0 · model-reported confidence
    model_version: str           # e.g., "claude-opus-4-7"
    extracted_at: datetime
    reviewer_signature: ReviewerSignature | None
    bounding_box: BoundingBox | None  # pixel coordinates for visual highlighting in UI

@dataclass(frozen=True)
class ExtractedClause:
    clause_id: str
    text: str
    criticality: ClauseCriticality
    schema: ClauseSchema         # typed slots — rent_amount · escalation_rate · break_date · ...
    provenance: Provenance
```

### The provenance veto

The sovereign veto fires under any of:

1. **`PROV-INCOMPLETE-MATERIAL`** — clause flagged `MATERIAL` is missing any of: document_hash, page, paragraph, extraction_confidence, or reviewer_signature.
2. **`PROV-INCOMPLETE-SIGNIFICANT`** — clause flagged `SIGNIFICANT` is missing document_hash, page, paragraph, or extraction_confidence. Reviewer signature is recommended but not required.
3. **`PROV-LOW-CONFIDENCE-MATERIAL`** — clause flagged `MATERIAL` has extraction_confidence below 0.85 (configurable per portfolio).
4. **`PROV-HASH-MISMATCH`** — document_hash does not match any document currently in the lease repository.
5. **`PROV-STALE-MODEL`** — model_version is below the minimum version configured for clauses of this criticality.

Vetoed clauses are logged to the audit chain (ADR-0003) with full Provenance for diagnostic review. The clause is not written to the system of record. A human reviewer (typically a lease administrator) is notified.

### Material clauses require human reviewer signature

For `MATERIAL` clauses the `reviewer_signature` field is required. Without it, the veto fires. The signature is itself a hash-chain entry:

```python
@dataclass(frozen=True)
class ReviewerSignature:
    reviewer_id: str             # named human · tied to identity provider
    reviewed_at: datetime
    sigil: str                   # sha256(reviewer_id + clause_text + reviewed_at)
    notes: str | None
```

The lease-administration team retains responsibility for material clauses. The AI proposes; the reviewer signs. Throughput at production scale is preserved because routine and significant clauses (the bulk of any lease) flow through without signature requirement.

## Consequences

**Positive.** Hallucinated material clauses cannot reach the system of record. A reviewer's signature is recorded immutably. A regulator, an LP, or a litigation discovery can reconstruct the provenance of any clause from the audit chain back to the source document, page, paragraph, and model version. The cost of "we don't know how this clause got into the system" goes to zero.

**Negative.** Throughput on material clauses is bounded by reviewer capacity. This is the right answer. The alternative — unsigned material clauses written autonomously — is a settled liability waiting for a trigger.

**Architectural.** The Provenance object is the single typed gate between extraction and system-of-record write. There is no other path. The agent's reasoning is not the path of record; the typed object is.

## Failure modes this prevents

- **Confabulated dates** — clause text references a date the source document does not contain. Caught by `PROV-HASH-MISMATCH` if the model invented the date; caught by reviewer signature requirement if the date is on the document but transcribed wrong.
- **Transposed rent escalations** — model swaps base rent and escalation amount. Caught by reviewer signature requirement on `MATERIAL`.
- **Missed conditional clauses** — agent extracts only the affirmative path of a conditional, missing the carve-out. Caught by structural validation in the typed `ClauseSchema` (e.g., a `break_clause` schema with `conditions` slot that cannot be omitted).
- **Stale model regressions** — an old model version producing degraded output. Caught by `PROV-STALE-MODEL`.

## Regulatory anchor

- SOC 2 Trust Services Criteria CC7.2 (system monitoring · evidence preservation)
- Institutional lease-administration audit standards (industry-specific; varies by REIT, fund, family office)
- General fiduciary duty in lease administration

## Implementation notes

See `src/governance/lease_provenance.py` for the reference implementation, `src/schemas/lease_clause.py` for the typed objects, and `examples/01_lease_abstraction_provenance/` for the runnable demo.

## Related

- ADR-0002 (Sovereign Veto) — the enforcement layer
- ADR-0003 (Hash-chain Audit) — where the Provenance object is recorded
- ADR-0006 (Shadow Mode) — new extraction models run shadow for 30 days before promotion
