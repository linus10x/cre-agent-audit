# ADR-0008 · Fair-Housing Pre-Flight Gate

**Status:** Accepted · CRE-native
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

## Context

Algorithmic discrimination in tenant screening is no longer hypothetical. Three settled cases anchor the discipline:

- **TransUnion** — October 2023 — $15M to the FTC and the CFPB. A tenant-screening AI tool that landed on the wrong side of consumer-reporting law.
- **SafeRent** — November 20, 2024 — $2.3M. An AI scoring model that treated housing-voucher status as a negative signal in violation of the Fair Housing Act.
- **RealPage** — November 24, 2025 — DOJ-imposed binding restrictions on rent-pricing AI (data ≥1 yr old · state-wide granularity only · no pricing discussions at user meetings).

The Colorado AI Act (SB 189, signed March 14, 2026) sets a January 1, 2027 compliance deadline for impact assessments and risk-management policies on consequential decisions, with tenant screening named explicitly.

The conventional response to algorithmic discrimination is "human in the loop." At CRE-portfolio scale the conventional response is theatre. A tenant-screening agent runs hundreds of thousands of decisions per quarter at a mid-size portfolio. Human review at that volume is either a bottleneck (most decisions wait) or a stamp (most decisions are rubber-stamped without meaningful review).

The pattern that works at scale is **hard-coded constraint check at the agent boundary**, with a structured bypass path that is itself auditable.

## Decision

Every agent action that touches a **protected decision surface** routes through the Fair-Housing Pre-Flight Gate before execution. The gate runs an ordered sequence of checks. Each check that fires raises a sovereign veto (ADR-0002) with a specific reason code.

### Protected surfaces

```python
PROTECTED_SURFACES = {
    "tenant_screening",
    "renewal_pricing",
    "marketing_audience_targeting",
    "housing_credit_decision",
    "tenant_communication_personalization",
}
```

A surface is protected if a decision on that surface has been the subject of an FHA, ECOA, or state-AI-act enforcement action, or if a reasonable counsel would identify it as protected-class-adjacent. The list is in `config/compliance_rules.yaml` and updated by PR with regulatory citation.

### The check sequence

The gate runs five ordered checks. Each is implemented as a separate function for testability and selective enable/disable per jurisdiction.

**1. Protected-class proxy detection — `FHA-PROXY`**

The decision input is screened for features that proxy for protected class. Zip-code-only screening is a known proxy for race. Income-source granularity is a known proxy for source-of-income status. A configurable list of features per jurisdiction, with a per-feature mutual-information threshold against historical decisions' protected-class outcomes (where reportable demographics are available).

Veto fires if any feature in the input crosses the threshold.

**2. Voucher-status non-discrimination — `FHA-VOUCHER`**

The decision input is screened for any feature that includes or correlates with housing-voucher participation. This is the SafeRent failure mode. Any feature that creates disparate impact on voucher-holding applicants triggers the veto. Jurisdiction-specific: in states with SOI protections (CA, NJ, DC, etc.) the rule is absolute; in states without, the disparate-impact monitor still applies.

**3. Source-of-income protection — `FHA-SOI`**

In jurisdictions with source-of-income ordinances (federal: not protected; state: CA, CT, DC, MA, MN, NJ, NY, OR, VT, WA; municipal layer beyond), any feature that introduces income source into the decision triggers the veto. The ordinance list lives in `config/compliance_rules.yaml`.

**4. Criminal-history use bans — `FHA-CRIM`**

HUD 2016 guidance plus state and municipal layers. The check enforces (a) no blanket criminal-history disqualifications, (b) individualized assessment requirement where applicable, (c) lookback-period limits where applicable, (d) conviction-only-not-arrest requirement where applicable.

**5. Disparate-impact monitor on outputs — `FHA-DISPARATE`**

A running statistical monitor across all decisions in a configurable window (default 90 days). For each protected cohort with reportable demographics, the monitor computes the selection rate relative to the highest-selection cohort. A ratio below 0.80 (the four-fifths rule) on any active cohort triggers the veto on every subsequent decision in that surface until the rate recovers or a logged exception is filed.

### Human bypass path

A human can override any single veto for any single decision. The bypass writes a logged exception with:

```python
@dataclass(frozen=True)
class FairHousingException:
    exception_id: str
    decision_id: str
    veto_reason_code: str        # e.g., FHA-VOUCHER
    bypass_owner: str            # named human · identity-provider-verified
    bypass_justification: str    # free text · regulatory or factual basis
    bypass_authority: AuthorityLevel  # MANAGER | DIRECTOR | GC
    timestamp: datetime
    audit_chain_sigil: str       # hash anchor on the audit chain
```

The exception is durable. It cannot be edited or deleted. Three bypasses by the same owner in a 90-day window auto-escalate to the GC. Five bypasses on the same reason code in a 90-day window force the program to DEFCON-4 (ADR-0001) until the gate is re-tuned or the underlying input feature is removed.

## Consequences

**Positive.** The four named failure modes (TransUnion, SafeRent, RealPage, and the Colorado AI Act trigger) are blocked at the agent boundary by construction, not by hope. The exception log becomes the board-level governance artifact. Regulators inquiring about a screening decision can reconstruct the gate verdicts on every decision in the audit chain. Disparate impact is measured and acted on, not assumed away.

**Negative.** Throughput is bounded by the gate's compute cost. The cost is well-bounded — checks 1-4 are O(features), check 5 is O(decisions in window) with caching. The cost is measured in milliseconds per decision; the cost of a settled case is measured in millions.

**Calibration risk.** An over-tight gate produces a flood of exceptions that overwhelm the GC. An under-tight gate produces settled liability. Calibration is portfolio-specific and is the work of the program, not the framework. The gate ships with reasonable defaults and a calibration playbook in `docs/`.

## What this gate does NOT cover

- **State and municipal SOI ordinances beyond the federal list and Colorado** — these are PRs from the community.
- **Marketing audience targeting on multi-language properties** — language preference can proxy for national origin in ways the current proxy detector does not catch reliably.
- **Algorithmic disparate impact on outputs across multi-jurisdiction portfolios** — the four-fifths rule applied jurisdiction-by-jurisdiction can miss aggregate effects.

These are issue placeholders, not architectural failures. The repo is open for the community to harden them.

## Regulatory anchor

- Fair Housing Act (42 U.S.C. § 3604)
- ECOA (15 U.S.C. § 1691)
- HUD AI guidance (2024 HUD memorandum on AI and Fair Housing)
- Colorado AI Act SB 189 (effective 2027-01-01)
- State-level fair-housing statutes
- Disparate-impact framework under FHA (HUD 24 C.F.R. § 100.500)

## Implementation notes

See `src/governance/fair_housing_preflight.py` for the reference implementation, `src/schemas/screening_decision.py` for the typed objects, and `examples/02_tenant_screening_preflight/` for the runnable demo.

## Related

- ADR-0002 (Sovereign Veto) — the enforcement layer
- ADR-0003 (Hash-chain Audit) — where every veto and every exception is recorded
- ADR-0004 (Autonomy Ladder) — tenant screening is A3-bounded · cannot exceed A3 without this gate live
- ADR-0006 (Shadow Mode) — new screening models run shadow for 60 days with zero-worse-direction veto requirement
