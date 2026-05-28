# ADR-0012 · Pluggable Persistence, Trusted Timestamps, and External Witness Anchoring

**Status:** Accepted — v0.2.1 (in flight)
**Date:** 2026-05-28
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

v0.2.0 shipped the hash-chained `AuditLedger` (ADR-0003) with three named limitations bounded in [`docs/LIMITATIONS.md`](../LIMITATIONS.md):

1. **In-memory persistence only.** Reference implementation stored entries in a single `list[AuditEntry]` — adequate for unit tests and demo workflows, not for SOX 404 ITGC retention or FFIEC Audit booklet expectations.
2. **Local-clock timestamps.** `AuditEntry.timestamp = datetime.now(timezone.utc)` — no trusted-time attestation; a deployer with system-clock control can backdate.
3. **Internally consistent, not adversarially tamper-evident.** Hash-chaining alone detects modification by an honest holder of the chain head; an attacker with full ledger-host write access can regenerate the chain end-to-end and `verify_chain()` will still pass.

All three limitations were explicitly deferred to v0.2.1 in [`docs/SHIP-RECEIPT.md`](../SHIP-RECEIPT.md) (items F20 + F20 + F10 of the 5-chamber adversarial review). This ADR documents the v0.2.1 decisions that close them.

The constraint that bounds every choice in this ADR: **the package's Zero-Runtime-Dependencies posture is load-bearing.** Optional integrations live behind `extras_require`; they are never imported by `cre_agent_audit/__init__.py`.

## Decision

Three Protocol-based seams added to the audit-chain layer. Each is injectable into `AuditLedger.__init__`; each ships at least one stdlib-only reference implementation in this repository; each documents an integration shape that downstream deployers can implement against without pulling driver libraries into the package.

### Seam 1 — `LedgerStore` (persistence)

```python
class LedgerStore(Protocol):
    def append(self, entry: AuditEntry) -> None: ...
    def __iter__(self) -> Iterator[AuditEntry]: ...
    def __len__(self) -> int: ...
    def get(self, sequence: int) -> AuditEntry: ...
    def head_sequence(self) -> int: ...
    def head_self_hash(self) -> str: ...
```

The Protocol is **append-only by absence** — no `update`, `delete`, `truncate`, or `set` method appears anywhere in the surface. Production stores enforce this in their own substrate (Postgres row-level-immutability, S3 + Object Lock, DynamoDB conditional writes); the in-repo stores enforce it by not exposing mutation methods.

Three reference implementations ship in `src/cre_agent_audit/governance/`:

| Backend | Module | Use case |
|---|---|---|
| `InMemoryLedgerStore` | `ledger_store.py` | v0.2.0 behavior preserved — tests, demos, ephemeral pipelines |
| `SqliteLedgerStore` | `ledger_store_sqlite.py` | Single-node durability via stdlib `sqlite3`; one row per entry; no UPDATE codepath |
| `JsonlLedgerStore` | `ledger_store_jsonl.py` | Append-only file for highest-throughput ingestion; opt-out `fsync=False` |

Downstream deployers implementing Postgres+WAL, S3+Object Lock, DynamoDB, Kafka, or QLDB write the ~60 LOC against the `LedgerStore` Protocol. This repo does not pull psycopg, boto3, or any driver library — that would violate the Zero-Deps badge.

`AuditLedger` accepts `store: LedgerStore | None = None`; defaults to `InMemoryLedgerStore()` via `__post_init__`. v0.2.0 callers calling `AuditLedger()` get the v0.2.0 behavior unchanged.

### Seam 2 — `TimestampSource` (trusted time)

```python
class TimestampSource(Protocol):
    def stamp(self, payload_digest: bytes) -> TrustedTimestamp: ...
```

Reference implementations in `src/cre_agent_audit/governance/timestamp_source.py`:

| Source | Behavior |
|---|---|
| `LocalClockTimestampSource` | `datetime.now(timezone.utc)`; no token. Default; preserves v0.2.0 semantics. |
| `RFC3161TimestampSource` | POSTs a TSQ to a deployer-chosen TSA (FreeTSA, DigiCert, Sectigo, internal); receives a TSR; stores the opaque token base64-encoded. Fallback-to-local on TSA failure is the default (so a TSA outage cannot stall the audit pipeline); set `fallback_to_local_on_failure=False` to fail closed. |

The TSQ/TSR codec is hand-rolled in `rfc3161_codec.py` against the DER ASN.1 subset RFC 3161 actually uses (OID, INTEGER, OCTET STRING, NULL, BOOLEAN, SEQUENCE, GeneralizedTime). No `cryptography`, no `asn1crypto`. Signature-chain verification (necessary to re-validate a stored token years later) belongs to the optional `audit-verify` extra (pyca/cryptography) which ships in a separate `rfc3161_verify.py` module — not yet wired in v0.2.1.

`AuditEntry` gains an optional `timestamp_token_b64: str | None = None` field. The token is included in `canonical_bytes_for_hashing` ONLY when present, so v0.2.0 ledgers (token-free) remain hash-stable under v0.2.1 `verify_chain()`. Mixing local-clock and TSA-stamped entries in the same ledger is supported and audit-honest — the per-entry mode is recorded by the presence/absence of the field.

`AuditLedger` accepts `timestamp_source: TimestampSource | None = None`; defaults to `LocalClockTimestampSource()`.

### Seam 3 — `WitnessRegister` (external anchoring)

```python
class WitnessRegister(Protocol):
    def anchor(self, chain_head_hex: str) -> WitnessReceipt: ...
```

Reference implementations in `src/cre_agent_audit/governance/witness_anchor.py`:

| Register | Behavior |
|---|---|
| `RekorWitness` | POSTs a `hashedrekord` entry to Sigstore Rekor's public transparency log; receives an inclusion UUID + logIndex. Default endpoint is the public Sigstore instance; deployers can point to a private Rekor for air-gapped use. |
| `OpenTimestampsWitness` | Submits the chain head digest to the OpenTimestamps calendar API; receives a pending-commitment receipt that can later be upgraded to a Bitcoin attestation by re-submitting the opaque blob. Multiple calendar URLs supported for redundancy. |

The `anchor_to_witness(ledger, witness)` helper writes the receipt back to the ledger as a `decision_type="witness_anchor"` entry. This binds the anchor into the same hash chain it protects: tampering with the anchor record requires tampering with every entry after it. Scheduling is the deployer's responsibility — cron, Kubernetes CronJob, AWS EventBridge — not the package's. The package ships the function; the deployer schedules it.

## Consequences

**Positive.**
- Three of seven v0.2.1 deferred items closed; all three close behind clean Protocols with backward-compat defaults.
- Zero-Deps badge intact. `pyproject.toml` `[project.dependencies]` remains `[]`. Optional `[project.optional-dependencies] audit-verify` is documented but not required for the core audit semantics.
- Stdlib-only network code in `timestamp_source.py` and `witness_anchor.py` (`http.client` + `ssl`). No `requests`, no `urllib3`.
- v0.2.0 ledgers and v0.2.0 callers continue to work unchanged. Hash semantics are stable across versions for token-free entries.

**Negative.**
- DER ASN.1 codec is hand-rolled. The RFC 3161 subset is small (TSQ + GeneralizedTime extraction), but the maintenance burden is real. The optional `audit-verify` extra delegates full DER work to `pyca/cryptography`; the in-repo codec is the "build the request, parse the timestamp" path and is sufficient for 80% of audit value.
- Mid-flight migration from `LocalClockTimestampSource` to `RFC3161TimestampSource` produces a heterogeneous ledger (some entries with tokens, some without). This is intentional — the per-entry `timestamp_token_b64` field documents which mode produced each entry — but deployers should document the migration cutover in their own ops runbooks.
- `RekorWitness` and `OpenTimestampsWitness` create hard dependencies on external services at anchoring time. Deployers must instrument the anchor cron with retry + alerting. The pattern recovers (next cron run anchors the new head); the audit is not blocked.

**Architectural.**
- The three seams are independent. A deployer can adopt `SqliteLedgerStore` without `RFC3161TimestampSource` or vice versa. The seams compose without coordination.
- The `anchor_to_witness` helper's design — anchor receipt becomes a regular ledger entry — was the load-bearing decision. Alternatives considered: separate `witness_log` table (rejected; coordination problem between two logs), out-of-band PKCS#7 detached signature (rejected; verifier needs both the signature and the chain).

## What this does NOT cover

- **Signature-chain verification of stored RFC 3161 tokens.** Implemented in `rfc3161_verify.py` behind the `audit-verify` extra (NOT yet wired in v0.2.1). The opaque token is preserved verbatim so a downstream verifier (any RFC 3161-aware tool) can validate the TSA chain at any time.
- **Production-grade `LedgerStore` backends for Postgres / S3 / DynamoDB.** The Protocol is the contract; deployers implement against it. This ADR documents the integration shape and the conditional-write idiom per backend. Repo does not pull driver libraries.
- **Anchor scheduling and retry.** Deployers wire the anchor cron in their own infrastructure (Kubernetes CronJob, AWS EventBridge, GitHub Actions schedule). The pattern is idempotent against repeated submission of the same head — multiple anchor entries with the same `chain_head_anchored` value are valid and audit-honest.
- **Migration tooling from v0.2.0 in-memory ledgers to v0.2.1 backends.** Out of scope — adopters running v0.2.0 in production are out-of-band per the LIMITATIONS.md "pre-revenue research artifact" framing. v0.2.1 callers starting fresh do not need migration tooling.
- **MI-threshold learned-proxy detection** (Fair-Housing Gate, ADR-0008) — separate v0.2.1 work item.
- **`VendorScoreGate` concrete implementation** (ADR-0011) — separate v0.2.1 work item.

## Regulatory anchor

- **SOC 2 Type 2** — CC6.1 (Logical and Physical Access Controls) and CC7.2 (System Monitoring) expect audit trails to be tamper-evident and retained per the deployer's policy. The Protocol-based persistence design supports the deployer's choice of substrate; the witness anchor supports the tamper-evidence claim against an adversarial trust boundary.
- **SOX 404 ITGC** — audit-trail integrity is a documented expectation; the SQLite + JSONL reference implementations are the entry point; production deployers extend with their substrate's WAL / Object Lock / conditional writes.
- **FFIEC Audit Booklet** — IT Audit § "Audit Trail" expects time-attested, retention-policied, integrity-protected records. RFC 3161 trusted timestamps + external witness anchoring directly address two of three.
- **RFC 3161** — *Internet X.509 Public Key Infrastructure Time-Stamp Protocol (TSP)*. The TSA produces a signed time attestation that can be verified at any future point against the TSA's signing chain.
- **RFC 6962** — *Certificate Transparency*. The design rationale for external-witness-as-tamper-evidence is the same: the witness records what existed at time T, and a later attempt to rewrite history must contradict the public record.

## Related

- ADR-0003 (Hash-Chained Audit Ledger) — the original pattern this ADR extends
- ADR-0008 (Fair-Housing Pre-Flight Gate) — separate v0.2.1 hardening (MI-threshold proxy detection)
- ADR-0010 (Audit-Chain Retention, Privilege & Discovery Posture) — the retention policy that the LedgerStore Protocol implements
- ADR-0011 (Vendor-Output Adapter Pattern) — separate v0.2.1 hardening (VendorScoreGate concrete implementation)
- `docs/LIMITATIONS.md` § 2, § 3, § 4 — bounded claims for v0.2.0 that this ADR closes

## Implementation notes

v0.2.1 ships:
- `src/cre_agent_audit/governance/ledger_store.py` — Protocol + `InMemoryLedgerStore`
- `src/cre_agent_audit/governance/ledger_store_sqlite.py` — stdlib `sqlite3` backend
- `src/cre_agent_audit/governance/ledger_store_jsonl.py` — append-only JSONL backend
- `src/cre_agent_audit/governance/timestamp_source.py` — Protocol + `LocalClockTimestampSource` + `RFC3161TimestampSource`
- `src/cre_agent_audit/governance/rfc3161_codec.py` — minimal DER ASN.1 codec
- `src/cre_agent_audit/governance/witness_anchor.py` — `RekorWitness`, `OpenTimestampsWitness`, `anchor_to_witness()`
- Test files round-tripping each backend; mock HTTP server for Rekor; OTS unreachable-calendar failure path

v0.2.1 tracked for completion (separate ADRs / commits):
- ADR-0012-A1 (forthcoming) — `rfc3161_verify.py` signature-chain verification under the `audit-verify` extra
- MI-threshold proxy detector (Fair-Housing Gate; ADR-0008 update)
- `VendorScoreGate` concrete implementation (ADR-0011 update)
- Agent topology pruning (ADR-0013, forthcoming)
- `docs/FAILURE-MODES.md` per-pattern negative-results appendix
