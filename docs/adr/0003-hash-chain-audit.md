# ADR-0003 · Hash-chain Audit Ledger

**Status:** Accepted · inherited from finserv-agent-audit
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

## Context

A regulator inquiring about a CRE-AI decision twelve months after the fact needs an answer that does not depend on whether the agent code, the prompt, the model weights, or the operator's intentions have changed in the interim. The answer must be a record that was true when the decision was made and cannot have been tampered with since.

Standard application logging is insufficient. Logs are mutable. Logs are deletable. Logs are reconstructable in ways that survive scrutiny by an adversarial third party. A board committee asking "show me every decision the agent made on this property over the last quarter" needs a stronger guarantee than "trust the log file."

## Decision

Adopt a **hash-chain audit ledger** — every decision event is appended to a chain in which each entry contains the SHA-256 hash of the previous entry. Tampering with any entry invalidates every entry that follows. Periodic anchor checkpoints write the chain head to an external durable system.

```python
@dataclass(frozen=True)
class AuditEntry:
    sequence: int                       # monotonically increasing
    timestamp: datetime
    actor_kind: ActorKind               # AGENT | HUMAN | SYSTEM
    actor_id: str
    decision_type: str                  # screening · pricing · abstraction · transition · ...
    action_payload: bytes               # the decision itself, structured
    gate_verdicts: dict[str, str]       # which gates ran, what they returned
    prior_hash: str                     # sha256(prior entry)
    self_hash: str                      # sha256(this entry minus self_hash)
```

The ledger is append-only. Reads are by sequence number, by actor, by decision type, by time window, or by cross-referenced entity (property ID, tenant ID, lease ID). The ledger does **not** support deletion or in-place edits. A correction is a new entry that references the prior entry's sequence with `decision_type = "correction"`.

Anchor checkpoints are external. Every 1,000 entries or 24 hours (whichever comes first) the current chain head hash is written to a separate durable system — in the reference repo this is a configurable backend (filesystem · S3 · DynamoDB · Postgres with row-level immutability via constraints).

## Consequences

**Positive.** Tamper-evident by construction. A single corrupted byte invalidates the chain from that point forward, and the corruption is detectable at any later audit. Regulator-reconstructable decision history is a one-query operation. Disputes between operator and counterparty can be resolved by reading the ledger, not by re-litigating intent.

**Negative.** Storage cost grows linearly with decision volume. At realistic CRE-portfolio decision rates (hundreds of thousands per quarter at a mid-size operator) the chain grows to gigabytes per year — manageable but non-zero. Rotation policy: chains are partitioned by quarter, anchor checkpoints carry the prior partition's terminal hash, and historical partitions can be cold-stored.

**Architectural.** Every gate verdict — DEFCON, Domain pre-flight, Sovereign Veto, Autonomy Ladder, Shadow Mode router — is captured on every entry. A veto'd action is a ledger entry as full as an executed action. The ledger is the record of what was *considered*, not just what was *done*.

## Regulatory anchor

- SOC 2 Trust Services Criteria CC7.2 (system monitoring)
- SEC 17a-4 (broker-dealer record retention — analog for institutional-investor-owned CRE)
- NIST AI RMF Govern function (GOVERN 1.1 — accountability mechanisms documented)
- Evidence-preservation best practice in litigation-prone domains

## CRE-specific notes

Lease abstraction generates the highest-volume decision class in this repo (one entry per extracted clause). The ledger schema includes a `material` boolean to support material-only audit queries — a litigation-defensible separation between every clause extracted and every clause that mattered.

## Related

- All other ADRs — every pattern writes to this ledger
- ADR-0001 (DEFCON) — every state transition writes an entry
- ADR-0002 (Sovereign Veto) — every veto writes an entry
