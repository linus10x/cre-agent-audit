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

---

*Read the ADRs for the full reasoning behind each pattern. The ADRs are the discipline; the code is the implementation.*
