# ADR-0008 · Fair-Housing Pre-Flight Gate

**Status:** Accepted · CRE-native
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

Three regulatory matters in 24 months name the operator-side AI-governance gap this pattern addresses:

- **TransUnion** — October 2023 — $15M to the FTC and CFPB on systemic accuracy failures in rental-screening reports under FCRA § 607(b). The matter named *In re Trans Union Rental Screening Solutions, Inc.* (joint FTC/CFPB consent orders).
- **SafeRent** — November 2024 — approximately $2.275M class settlement in *Louis v. SafeRent Solutions, LLC*, No. 1:22-cv-10800 (D. Mass.). The complaint named tenant-screening AI that scored applicants below threshold with no documented reason; the settlement included a five-year score-use injunction on voucher-holder applicants. **Class settlement, not adjudicated FHA liability.**
- **RealPage** — August 2024 — *U.S. v. RealPage, Inc.* filed by DOJ + 8 state AGs alleging Sherman § 1 violations from algorithmic rent-coordination. **Ongoing civil antitrust litigation** as of v0.2.0 (not a consent decree or settled liability).

The doctrinal foundation for disparate-impact under the FHA is *Texas Dept. of Housing v. Inclusive Communities Project*, 576 U.S. 519 (2015), which constitutionalized disparate-impact and articulated the burden-shifting framework HUD codified at 24 C.F.R. § 100.500.

The Colorado AI Act (SB24-205, signed May 2024; follow-on amendments tracked separately) names housing among the consequential-decision categories; tenant-screening AI is in-scope as a deployer obligation. The Colorado AI Act timeline is the next state-level regulatory checkpoint for CRE operators in the housing branch.

**This pattern materially reduces the class of failure modes the SafeRent and TransUnion matters exposed. It does not, standing alone, establish FHA compliance.**

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

The decision input is screened for features that proxy for protected class against a **configurable lexical blocklist** per jurisdiction (e.g., voucher-related feature names, source-of-income markers, criminal-history blanket-exclusion features). Zip-code-only screening is a known proxy for race; income-source granularity is a known proxy for source-of-income status; the blocklist captures known-name lexical proxies of this kind.

Veto fires if any feature name in the input matches the blocklist.

**Scope of proxy detection — explicit bound.** This pattern in v0.2.0 implements **lexical / named-feature** proxy detection. It does NOT detect:
- **Learned proxies in embedding space** (a deep model can encode protected-class information in latent features even when the named feature is excluded — see Dwork et al. 2012; Datta et al. 2017).
- **Behavioral-signal proxies** (browser fingerprints, application-session timing patterns, language patterns).
- **Geospatial-granularity proxies** finer than zip code (precinct-level, block-group-level).

Detection of those classes requires upstream training-time controls (differential privacy on training data, adversarial debiasing, counterfactual-fairness audits — Kusner et al. 2017) and is **out of scope for v0.2.0**. The MI-threshold (mutual-information against historical protected-class outcomes) approach is tracked as a v0.3 implementation candidate. See [`docs/LIMITATIONS.md`](../../docs/LIMITATIONS.md).

**2. Voucher-status non-discrimination — `FHA-VOUCHER`**

The decision input is screened for any feature that includes or correlates with housing-voucher participation. This is the SafeRent failure mode. Any feature that creates disparate impact on voucher-holding applicants triggers the veto. Jurisdiction-specific: in states with SOI protections (CA, NJ, DC, etc.) the rule is absolute; in states without, the disparate-impact monitor still applies.

**3. Source-of-income protection — `FHA-SOI`**

In jurisdictions with source-of-income ordinances (federal: not protected; state: CA, CT, DC, MA, MN, NJ, NY, OR, VT, WA; municipal layer beyond), any feature that introduces income source into the decision triggers the veto. The ordinance list lives in `config/compliance_rules.yaml`.

**4. Criminal-history use bans — `FHA-CRIM`**

HUD 2016 guidance plus state and municipal layers. The check enforces (a) no blanket criminal-history disqualifications, (b) individualized assessment requirement where applicable, (c) lookback-period limits where applicable, (d) conviction-only-not-arrest requirement where applicable.

**5. Disparate-impact monitor on outputs — `FHA-DISPARATE`**

A running statistical monitor across all decisions in a configurable window (default 90 days). For each protected cohort with reportable demographics, the monitor computes the selection rate relative to the highest-selection cohort. A ratio below 0.80 (the four-fifths rule) on any active cohort triggers the veto on every subsequent decision in that surface until the rate recovers or a logged exception is filed.

### MI-threshold learned-proxy detection — `FHA-MI-PROXY` (added v0.2.2)

Lexical-only proxy detection (check #1 above) misses a class of failure the *Louis v. SafeRent Solutions* matter named: features that carry statistical signal about voucher-holder status without naming voucher status lexically (zip-code-shaped features being the canonical example).

v0.2.2 ships `MIThresholdDetector` in [`src/cre_agent_audit/governance/mi_threshold_detector.py`](../../src/cre_agent_audit/governance/mi_threshold_detector.py). When wired into `FairHousingPreflightGate(mi_proxy_detector=...)`, the gate runs the detector immediately after check #1 (lexical proxy) and emits `FHA-MI-PROXY` for any feature whose mutual information with the protected class exceeds the configured threshold.

```python
from cre_agent_audit.governance.mi_threshold_detector import MIThresholdDetector
from tests.fixtures.saferent_shaped_reference import saferent_shaped_reference

reference = saferent_shaped_reference()  # or operator's own labeled sample
detector = MIThresholdDetector(reference=reference, mi_threshold=0.10)
gate = FairHousingPreflightGate(mi_proxy_detector=detector)
result = gate.evaluate(action)
# Features above the MI threshold produce reason_code='FHA-MI-PROXY' with the
# feature name and MI score in result.detail.
```

**Methodology.** Mutual information `I(F; Y)` is computed between each feature `F` in the operator's labeled reference and the protected-class label `Y`, normalized to `[0, 1]` by the marginal entropy of `Y`. Numeric features are quartile-binned before computation. The threshold default is `0.10` — features carrying 10% of the protected-class signal are flagged for operator review. Stdlib-only implementation (no `scikit-learn`); the Zero-Runtime-Dependencies posture is preserved.

**Academic anchoring.** The MI-threshold approach is grounded in:

- Kusner et al. 2017 — *Counterfactual Fairness* (NeurIPS)
- Calmon et al. 2017 — *Optimized Pre-Processing for Discrimination Prevention* (NeurIPS)
- Hardt-Price-Srebro 2016 — *Equality of Opportunity in Supervised Learning*
- Pedreshi-Ruggieri-Turini 2008 — *Discrimination-aware data mining* (KDD)

**Limitations.** MI signal-presence is **necessary but not sufficient** for fair-housing compliance. Adopters owning a regulator-facing fairness defense should choose their fairness metric in consultation with counsel and document the choice. The four-fifths-rule monitor (check #5) is the post-decision complement; the MI detector is the pre-decision complement. Binary protected attributes only in v0.2.2; multi-class is a v0.3+ candidate. The detector is opt-in (`mi_proxy_detector=None` is the default); operators wire it when they have a labeled reference distribution.

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
- *Texas Dept. of Housing v. Inclusive Communities Project*, 576 U.S. 519 (2015) — constitutionalized disparate-impact under the FHA
- HUD disparate-impact rule (24 C.F.R. § 100.500) — burden-shifting framework
- ECOA (15 U.S.C. § 1691)
- HUD guidance on AI in housing decisions (2024)
- Colorado AI Act (SB24-205 + follow-on amendments) — housing as consequential decision
- State-level fair-housing statutes (CA, CT, DC, MA, MN, NJ, NY, OR, VT, WA — source-of-income protections)
- TransUnion FTC/CFPB consent orders (Oct 2023) — FCRA § 607(b) accuracy
- *Louis v. SafeRent Solutions* (D. Mass., Nov 2024) — class settlement

## Implementation notes

See `src/governance/fair_housing_preflight.py` for the reference implementation, `src/schemas/screening_decision.py` for the typed objects, and `examples/02_tenant_screening_preflight/` for the runnable demo.

## Related

- ADR-0002 (Sovereign Veto) — the enforcement layer
- ADR-0003 (Hash-chain Audit) — where every veto and every exception is recorded
- ADR-0004 (Autonomy Ladder) — tenant screening is A3-bounded · cannot exceed A3 without this gate live
- ADR-0006 (Shadow Mode) — new screening models run shadow for 60 days with zero-worse-direction veto requirement
