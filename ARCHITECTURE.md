# Architecture — cre-agent-audit

How the nine governance patterns compose into a runtime for CRE AI agents.

---

## The compose order matters

The patterns are not a menu. They are a stack. An agent action that touches a regulated decision flows through every layer below before any state mutates anywhere downstream.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Agent proposes action (lease clause · screening decision · price)  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
            ┌──────────────────▼──────────────────┐
            │  DEFCON state check (ADR-0001)      │
            │  Is the system in a state that      │
            │  permits this class of action?      │
            └──────────────────┬──────────────────┘
                               │  pass
            ┌──────────────────▼──────────────────┐
            │  Domain pre-flight (ADR-0007/8/9)   │
            │  · Lease clause carries Provenance? │
            │  · Screening decision passes FHA?   │
            │  · PII flow tagged for residency?   │
            └──────────────────┬──────────────────┘
                               │  pass
            ┌──────────────────▼──────────────────┐
            │  Sovereign Veto check (ADR-0002)    │
            │  Non-overridable boundary check.    │
            │  No agent override. No human bypass │
            │  without logged exception.          │
            └──────────────────┬──────────────────┘
                               │  pass
            ┌──────────────────▼──────────────────┐
            │  Autonomy Ladder gate (ADR-0004)    │
            │  Is the agent at the autonomy tier  │
            │  authorized for this decision?      │
            └──────────────────┬──────────────────┘
                               │  pass
            ┌──────────────────▼──────────────────┐
            │  Shadow Mode router (ADR-0006)      │
            │  New capability? Route silent.      │
            │  Promoted capability? Route live.   │
            └──────────────────┬──────────────────┘
                               │
            ┌──────────────────▼──────────────────┐
            │  Hash-chain Audit write (ADR-0003)  │
            │  Append decision + every gate's     │
            │  verdict to the audit ledger.       │
            │  Immutable. Regulator-reconstructable│
            └──────────────────┬──────────────────┘
                               │
                       ACTION EXECUTES
```

The compose order is deliberate. DEFCON first because an unsafe operating state should kill the action before any expensive check runs. Domain pre-flight before sovereign veto because the domain check has the specific knowledge to construct the right veto condition. Shadow mode after veto because a vetoed decision is also worth observing in shadow for the regulatory record. Audit write last so the ledger captures every gate's verdict, not just the action.

## The agent topology (6 roles)

The repo ships six agent stubs that mirror the finserv-agent-audit topology. They are roles, not microservices — the same process can host multiple agents in a small deployment, separated by orchestrator routing.

| Agent | Responsibility |
|---|---|
| `domain_intelligence` | Reads the underlying domain — lease text, tenant application, market rent — and surfaces structured observations |
| `strategy` | Composes an action recommendation from domain observations |
| `risk` | Evaluates the recommendation against policy limits and known failure modes |
| `audit` | Reconstructs prior decisions for regulators, LPs, or internal review |
| `orchestrator` | Routes work between the other five agents according to the compose order above |
| `monitor` | Observes the audit ledger for anomalies and emits alerts |

Tested against a 6-agent topology because that is what scales from a 5-property portfolio to a 5,000-property portfolio without architectural rework. Three agents are too few (no separation of concerns); nine are too many (orchestration overhead dominates).

## The three CRE-native patterns in detail

Each is the subject of a heavy ADR. Read them in order — they share assumptions.

### Lease-Abstraction Provenance Chain (ADR-0007)

Every clause an AI extracts from a lease carries a typed `Provenance` object:

```python
@dataclass(frozen=True)
class Provenance:
    document_hash: str           # sha256 of the source PDF
    page: int                    # 1-indexed
    paragraph: tuple[int, int]   # (start_paragraph, end_paragraph)
    extraction_confidence: float # 0.0 – 1.0
    model_version: str           # e.g., "claude-opus-4-7"
    reviewer_signature: Signature | None  # optional, recommended for material clauses
    timestamp: datetime
```

The sovereign veto fires if any field is missing on a clause flagged `MATERIAL` (rent schedule, break clauses, outgoings provisions, options to renew, jurisdiction). The agent cannot write to the system of record. The veto is logged with reason code `PROV-INCOMPLETE-MATERIAL`.

### Fair-Housing Pre-Flight Gate (ADR-0008)

Every agent action that touches one of the protected-decision surfaces routes through the gate:

```python
PROTECTED_SURFACES = {
    "tenant_screening",
    "renewal_pricing",
    "marketing_audience_targeting",
    "housing_credit_decision",
    "tenant_communication_personalization",
}
```

The gate runs an ordered sequence of checks. Each check that fires raises a veto with a specific reason code:

1. **Protected-class proxy detection** — input features correlated with race, religion, national origin, sex, familial status, disability above a configurable threshold trigger `FHA-PROXY`.
2. **Voucher-status non-discrimination** — any feature that includes voucher participation in a way that creates disparate impact triggers `FHA-VOUCHER` (the SafeRent failure mode).
3. **Source-of-income protection** — jurisdictions with SOI ordinances (added per the compliance_rules.yaml) trigger `FHA-SOI` if income source enters the decision.
4. **Criminal-history use bans** — jurisdiction-specific (HUD 2016 guidance plus state and municipal layers) trigger `FHA-CRIM`.
5. **Disparate-impact monitor on outputs** — running statistics on decisions across protected cohorts trigger `FHA-DISPARATE` when the four-fifths rule is breached for any active cohort.

A human can bypass any single check, but the bypass writes a logged exception with named owner and regulatory basis. The bypass cannot remove the audit-chain entry. Three bypasses in a 90-day window auto-escalate to the GC.

### Tenant-PII Data-Residency Partitioning (ADR-0009)

Tenant data is segregated by jurisdiction at the storage layer. Every record carries a `jurisdiction` field. Every cross-jurisdiction read requires a `LegalBasis` tag:

```python
class LegalBasis(Enum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGITIMATE_INTEREST = "legitimate_interest"
    LEGAL_OBLIGATION = "legal_obligation"
```

The veto fires if an agent attempts to read across a jurisdiction boundary without a `LegalBasis` on the request and a recorded purpose. The veto reason code is `RESIDENCY-CROSS-JURISDICTION-UNTAGGED`. Logged exceptions require GC sign-off.

## What is intentionally not in this v1

These are not weaknesses — they are scope choices. The repo opens these as issues for community contribution.

- **State-by-state SOI ordinance mapping** — federal floor plus Colorado is shipped; New York, California, Massachusetts, Minneapolis, Seattle ordinances are issue placeholders.
- **Multi-language lease provenance** — English only.
- **Adversarial test corpus** — examples demonstrate the patterns; they do not stress them.
- **Real-time decision routing** — all examples are batch-oriented for clarity.
- **Integration with named PMS / IWMS systems** — the patterns are vendor-neutral by design.

## Zero runtime dependencies

The package is `stdlib`-only at runtime. The human-edited source of truth for the regulation→pattern mapping is YAML (`config/compliance_rules.yaml`); `scripts/build_compliance_json.py` emits the checked-in JSON artifact (`config/compliance_rules.json`) that the runtime `RegulationLoader` reads. PyYAML is a dev-only dependency used by the build script and by YAML authors; CI verifies the JSON stays in sync with the YAML on every PR. This pattern preserves human-author ergonomics on the editing surface and zero-runtime-dependency posture on the install surface.

## Module-name canonical vocabulary (v0.2.0 renames)

Source-file names match canonical pattern names used in ADRs, the compliance YAML, and FINOS AIR-format submission files:

- `governance/fair_housing_preflight.py` (was `fair_housing_gate.py`) — matches ADR-0008 title and `FairHousingPreflightGate` class
- `governance/tenant_pii_residency.py` (was `tenant_pii_partition.py`) — matches ADR-0009 policy-language vocabulary

## Layered policy ADRs (v0.2.0 additions)

Two ADRs added in v0.2.0 from adversarial-review fold-in — no separate runtime primitives; they are design + policy layers on top of the nine pattern primitives:

- **ADR-0010 — Audit-Chain Retention, Privilege & Discovery Posture** — layered on top of Patterns 2, 3, 7, 8, 9. Documents retention schedules synchronized to relevant statutes of limitations (FHA, ECOA, SEC 17a-4), attorney-client privilege routing on bypass-justification fields, work-product framing for disparate-impact monitor outputs, and litigation-hold integration with the audit chain.
- **ADR-0011 — Vendor-Output Adapter Pattern** (design in v0.2.0; concrete `VendorScoreGate` shipped in v0.2.1) — the `VendorScoreGate` Protocol + `InMemoryVendorScoreGate` default backend for vendor-mediated AI surfaces. Most operators do not run in-house screening / abstraction / pricing models; they receive (score, recommendation, reason-codes) tuples from vendors. The adapter bridges those outputs into the operator's audit ledger and sovereign-veto layer without requiring feature-level access. Score-drift on the same `(vendor_id, input_hash, model_version)` key surfaces as a flagged chain entry and, by default, raises `VendorScoreDriftDetected` to halt the pipeline.

## Audit-evidence framing

ADR-0003 reframes the audit ledger as **internally-consistent** (not adversarially tamper-evident on its own). The `AuditLedger.chain_head()` method exposes the chain-head SHA-256 digest for deployer-side anchoring. Without that anchor, an attacker with full ledger-host write access can regenerate the chain end-to-end.

v0.2.1 ships the reference witness-anchor implementations (ADR-0012 § Seam 3): `RekorWitness` (Sigstore public transparency log), `OpenTimestampsWitness` (OTS calendar API with multi-calendar redundancy), and `anchor_to_witness()` which writes the receipt back into the same hash chain it protects. v0.2.1 also ships the MI Proxy (ADR-0013) so `AuditLedger.verify_chain(mi_proxy=...)` fails closed when the verifier's own integrity attestation does not check — closing the verifier-compromise gap named in `FAILURE-MODES.md` Row 7.

## Big-4 audit overlay

The patterns map into Big-4 AI-assurance frameworks via:

- `docs/controls/CTRL-001..009.md` — per-pattern Control Description Tables (Activity / Objective / Owner / Frequency / Type / Evidence of Operation / Test of Design / Test of Operating Effectiveness)
- `docs/MAPPING-MATRICES.md` — four-framework overlay (NIST AI RMF × ISO/IEC 42001:2023 × COSO ICAIR × Big-4 standard taxonomy of AI controls)
- `config/compliance_rules.yaml` extended with `iso_42001_controls`, `coso_icair_component`, `big4_taxonomy_bucket` fields on every pattern entry (v0.2.0 ships a representative subset; full per-pattern mapping is a v0.3 candidate)

## Procurement-clause companion (for vendor-mediated AI)

Most CRE-operator AI surface is vendor-mediated. The patterns translate to procurement-clause power via `docs/vendor-clauses/{screening,abstraction,pricing}.md` — drop-in contract addenda for tenant-screening vendors (DPA + model-risk addendum + four-fifths-rule reporting SLA), lease-abstraction vendors (clause-level provenance-disclosure SLA), and revenue-management vendors (independent-decision contract clause + data-input-topology disclosure).

---

*Read the ADRs for the full reasoning behind each pattern. The ADRs are the discipline; the code is the implementation.*
