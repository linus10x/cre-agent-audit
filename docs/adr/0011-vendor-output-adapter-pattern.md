# ADR-0011 · Vendor-Output Adapter Pattern

**Status:** Accepted — Design Only (v0.2.0); reference implementation tracked for v0.3
**Date:** 2026-05-27
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

The Fair-Housing Pre-Flight Gate (ADR-0008), the Lease-Abstraction Provenance Chain (ADR-0007), and the Sovereign Veto (ADR-0002) as designed assume the operator controls the feature vector and the model. That assumption is incorrect for the majority of CRE-operator AI surface.

**Most CRE operators do not run in-house AI models.** They consume vendor outputs:

| Surface | Typical vendors |
|---|---|
| Tenant screening | SafeRent · RentGrow (Yardi) · TransUnion SmartMove · Real Capital Solutions · Findigs |
| Lease abstraction | Leverton (MRI Software) · V7 Lease · Reonomy · Aigen Sciences · Spacewell |
| Revenue management (pricing) | RealPage YieldStar · RealPage LRO · AppFolio Property Manager · Yardi Revenue IQ |
| AI-mediated resident communication | EliseAI · Hyly · Funnel Leasing |
| Application-fraud detection | Snappt · The Closing Docs · Plaid Identity |

The operator's AI-governance surface for these vendor-mediated workflows is the **vendor output** (score, recommendation, reason codes), **not the feature vector**. ADR-0008's `FairHousingPreflightGate` cannot run its proxy-feature checks because the operator does not see the features.

The operator still has FHA, ECOA, FCRA, and antitrust exposure on the *use* of the vendor's output. The pattern that works is an adapter that operates on the vendor-output tuple and produces the same engineering rails (Sovereign Veto, Audit Ledger, disparate-impact monitor on accept/decline outcomes) without requiring feature-level access.

## Decision

Define a `VendorScoreGate` Protocol that operates on vendor outputs without access to the feature vector. The adapter:

1. Receives `VendorOutput` (score, recommendation, reason-codes, optional vendor-provided fairness-metric output)
2. Runs operator-side disparate-impact monitoring on accept/decline outcomes at the operator's decision boundary (computable from vendor-output records alone — the four-fifths-rule selection-rate comparison does not require feature access)
3. Logs every operator decision (accept / decline / refer-to-human) with full vendor-output context to the Audit Ledger (ADR-0003)
4. Generates adverse-action notice content (FCRA / ECOA-style) preserving vendor-supplied reason codes
5. Fires Sovereign Veto (ADR-0002) on operator-side decisions that fail four-fifths-rule monitoring even when the underlying vendor score is "approved"

### Interface sketch (pseudocode — v0.2.0 ships design only)

```python
from typing import Protocol
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class VendorRecommendation(Enum):
    ACCEPT = "accept"
    REVIEW = "review"
    DECLINE = "decline"

@dataclass(frozen=True)
class VendorOutput:
    """What an operator receives from a third-party AI vendor.

    NOTE: deliberately does NOT include the feature vector — that is what the
    operator does not have access to in vendor-mediated workflows.
    """
    vendor_name: str                          # "SafeRent" · "RealPage" · etc.
    vendor_model_version: str | None          # if disclosed in contract
    request_id: str                           # vendor-side correlation ID
    score: float | None                       # vendor's score on its native scale
    score_scale_min: float | None
    score_scale_max: float | None
    recommendation: VendorRecommendation
    reason_codes: tuple[str, ...]             # vendor-provided; FCRA-style if applicable
    vendor_fairness_output: dict[str, float] | None = None  # if vendor exposes
    received_at: datetime = ...

@dataclass(frozen=True)
class ApplicantContext:
    """What the operator knows about the applicant (the protected-class
    reportable-demographics fields are tightly controlled — only what the
    operator has lawful basis to record and report under FHA/ECOA)."""
    applicant_id: str                         # operator-side ID; never vendor-side PII
    cohort_signal: str | None                 # only if lawfully reportable
    surface: str                              # which protected surface (per ADR-0008)

@dataclass(frozen=True)
class Decision:
    """The operator's decision on the vendor output."""
    applicant_id: str
    operator_decision: VendorRecommendation
    reason_codes: tuple[str, ...]             # operator-side + vendor-side, preserved
    sovereign_veto_fired: bool = False
    sovereign_veto_reason: str | None = None
    bypass_owner: str | None = None
    timestamp: datetime = ...

class VendorScoreGate(Protocol):
    """Adapter for vendor-mediated AI surfaces (tenant-screening, etc.)."""

    def evaluate(
        self,
        vendor_output: VendorOutput,
        applicant: ApplicantContext,
    ) -> Decision: ...

    def disparate_impact_window(
        self,
        surface: str,
        days: int = 90,
    ) -> dict[str, float]:  # cohort -> selection-rate ratio (vs highest cohort)
        ...

    def emit_audit_entry(self, decision: Decision) -> "AuditEntry": ...
```

### Pairs with procurement clauses

The adapter only works if the vendor exposes the data it needs. The contractual companion is [`docs/vendor-clauses/screening.md`](../../docs/vendor-clauses/screening.md) (DPA + model-risk addendum + four-fifths-rule reporting SLA). Operators that cannot negotiate the disclosure SLA into the next vendor contract renewal are running uncovered exposure regardless of the adapter's existence.

## Consequences

**Positive.** Operators get Patterns 2 + 3 coverage on the >80% of AI surface they do not control directly. The adapter is a clean seam: vendor-side opacity stops at the adapter; the operator's downstream stack (Sovereign Veto, Audit Ledger, disparate-impact monitor) keeps working as designed. The procurement-clause companion (`docs/vendor-clauses/screening.md`) converts the pattern into procurement-side requirement that a Chief Procurement Officer can circulate without engineering involvement.

**Negative.** The adapter cannot detect proxy features the operator does not see. The four-fifths-rule monitor on the operator-side decision is necessary-but-insufficient — if the vendor's model has a learned proxy bias, the four-fifths-rule check on the operator's accept/decline ratio may pass while the vendor-side scoring is the actual discriminatory signal. The mitigation is on the contracting side (vendor-side fairness reporting SLA) plus regulatory-discovery insistence on vendor-side model documentation.

**Architectural.** The adapter is the seam between the operator's stack and the vendor's stack. In a production deployment, it is the highest-impact governance boundary because it converts an opaque third-party signal into an operator-side, audit-chain-recorded decision. The seam should be loud (heavily logged) and explicit (configured per vendor, not implicit).

## What this does NOT cover

- **Vendor-side training-time controls.** Out of operator control by definition; the operator's recourse is contractual (model-risk addendum) and regulatory-discovery (Big-4 vendor-due-diligence on the model lifecycle).
- **Vendor-internal proxy-feature usage.** The operator cannot inspect the vendor's feature engineering; the operator requires the four-fifths-rule output as contractually-disclosed signal.
- **Reference implementation.** v0.2.0 ships the design (Protocol sketch + interface contract). v0.3 ships the reference implementation, a SafeRent-shaped synthetic test example, and an integration test against a mock vendor.
- **Vendor SLA enforcement at runtime.** If the vendor fails to provide the four-fifths-rule report the contract obligates, the operator's runtime cannot synthesize the missing data — the failure becomes a contract-breach issue, not a runtime fallback.
- **PCI / HIPAA / other vertical-specific vendor frameworks.** This pattern is CRE-specific; analogous patterns exist for FSI in the sibling `finserv-agent-audit` repo.

## Regulatory anchor

- Fair Housing Act (42 U.S.C. § 3604) — operator liability for use of a vendor's output that produces disparate impact
- ECOA (15 U.S.C. § 1691) — adverse-action notice requirements apply to operator use of vendor scores
- FCRA (15 U.S.C. § 1681) — accuracy + dispute rights apply to consumer reports purchased from vendors
- *Louis v. SafeRent Solutions, LLC* — operator deployment of vendor tenant-screening AI was the operator's exposure surface
- Operator-side vendor-management standards: OCC Bulletin 2013-29 (third-party risk) · SR 11-7 (model risk for vendor-supplied models) · NIST AI RMF Manage 3.x (third-party AI risk)

## Implementation notes

v0.2.0 ships:
- This design ADR with the Protocol interface sketch
- `docs/vendor-clauses/screening.md` — drop-in contract addendum for tenant-screening vendors
- `docs/vendor-clauses/abstraction.md` — drop-in contract addendum for lease-abstraction vendors
- `docs/vendor-clauses/pricing.md` — drop-in contract addendum for revenue-management vendors

v0.3 ships (tracked):
- `src/cre_agent_audit/governance/vendor_score_gate.py` — concrete implementation
- `tests/test_vendor_score_gate.py` — full test suite with SafeRent-shaped synthetic vendor output
- `examples/04_vendor_score_gate/run.py` — runnable demo against a mock vendor

## Related

- ADR-0002 (Sovereign Veto) — adapter generates decisions the veto can fire on
- ADR-0003 (Hash-chained Audit Ledger) — adapter emits entries to this ledger
- ADR-0007 (Lease-Abstraction Provenance) — analogous pattern for vendor lease-abstraction; covered contractually via `docs/vendor-clauses/abstraction.md`
- ADR-0008 (Fair-Housing Pre-Flight Gate) — the in-house equivalent of this adapter; ADR-0011 is the vendor-mediated complement
- ADR-0010 (Retention/Privilege/Discovery) — vendor-mediated decisions create their own discovery surface
- `docs/vendor-clauses/screening.md` — the contractual companion that obligates the data the adapter needs
