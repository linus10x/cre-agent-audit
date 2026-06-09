# ADR-0014 · Operator-Side AI Governance for Regulated Industries (Category Claim)

**Status:** Accepted — 2026-05-28
**Decider:** Kunjar Bhaduri
**Pairs with:** ADR-0003 (audit ledger), ADR-0011 (vendor-output adapter), ADR-0012 (persistence/timestamps/witness), ADR-0013 (MI Proxy)

> **⚠ Reference pattern, not legal advice.** This ADR records a category-claim decision (positioning), not a technical decision. Regulatory characterizations are reference mappings; consult counsel for jurisdiction-specific applicability. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

The AI-governance market is fragmenting into two distinct architectural positions:

1. **Vendor-side AI governance** — solutions sold by the AI vendor *to operators using that vendor's AI*. Examples in commercial real estate: RealPage Compliance Studio, Yardi Risk, MRI Compliance, SafeRent Audit. These solutions are mature, well-funded, and well-distributed. They share one structural problem: they cannot credibly audit the vendor's own product without compromising the vendor's commercial interests. The operator buying the audit gets compliance theater, not adversarial integrity.

2. **Operator-side AI governance** — controls and audit infrastructure deployed *by the operator independently of the vendor*, instrumenting the boundary at which vendor outputs enter the operator's decision pipeline. The operator owns the chain-of-custody. The audit ledger captures every vendor decision. The patterns are vendor-agnostic by design.

The anchors of record share a common structural feature: **the operator carried the liability, not the vendor.** *In re Trans Union Rental Screening Solutions* (FTC + CFPB consent orders, October 2023, $15M civil money penalty, FCRA § 607(b) accuracy). *Louis v. SafeRent Solutions, LLC*, No. 1:22-cv-10800 (D. Mass., November 20, 2024, approximately $2.275M class settlement with a five-year score-use injunction). *U.S. v. RealPage, Inc. et al.* (filed August 23, 2024 by DOJ + 8 state attorneys general; **Sherman Act §§ 1 AND 2**; resolved by a DOJ proposed consent judgment filed Nov 24, 2025, pending Tunney Act approval; co-defendant final judgments entered, e.g., Greystar Mar 2, 2026; resolved without admission of liability, never adjudicated). In each matter, operators relying on vendor-side audit could not produce the operator-side evidence the regulators demanded.

`cre-agent-audit` is a reference implementation of operator-side AI governance for commercial real estate. `finserv-agent-audit` is the sibling for financial services. This ADR names the category claim explicitly.

## Decision

`cre-agent-audit` and `finserv-agent-audit` are reference implementations of an architectural category: **operator-side AI governance for regulated industries**. The Autonomy Ladder™ A0→A4 framework is the autonomy-level abstraction. The per-vertical pattern libraries are the artifact stacks.

The category is defined by three structural commitments:

1. **The operator owns the audit ledger.** The chain-of-custody for every AI decision lives in operator infrastructure, not vendor infrastructure. The vendor provides a score; the operator's ledger captures the input, the vendor's output, the operator's decision, the human-in-loop, and the appeal — as one hash-chained record.

2. **Patterns are vendor-agnostic by construction.** `VendorScoreGate` (ADR-0011 + v0.2.1 implementation) accepts inputs from any vendor. `SovereignVeto` (ADR-0002) overrides any vendor recommendation. `FairHousingPreflightGate` (ADR-0008) screens any vendor's input model. No pattern is coupled to any specific vendor's API or scoring function.

3. **Audit-evidence is operator-producible.** The audit-evidence bundle (`EvidenceBundle` shipping in v0.2.2 alongside the regulatory-replay framework) is something the operator produces and hands to their auditor, regulator, or counsel — without vendor involvement. The vendor is never the source of evidence about the vendor.

## Consequences

**Positive.**

- The category claim sets vendor-side incumbents up as compromised — they cannot counter-position without commercial-interest conflicts. Operators evaluating AI-governance solutions now have a clear architectural frame: did we get vendor-side audit (the vendor grading itself), or did we get operator-side audit (we own the chain)?
- Adjacent verticals (insurance, healthcare, FSI) can inherit the operator-side commitment without re-deriving the framework's structural properties.
- Each named matter the framework replays becomes evidence the category claim is the right frame. The `examples/regulatory-incidents/` directory operationalizes the claim with three runnable matters in v0.2.2.

**Negative.**

- The category is wider than CRE. Concentration on CRE through v0.2.x means the meta-positioning is implicit. v0.3+ work should make it explicit via `autonomy-ladder.io` meta-positioning and cross-vertical ADR alignment.
- Naming a category invites incumbents to claim it. The defense is execution: continued framework maturity, named-matter coverage, sustained publishing cadence, and peer-reviewed publication.

**Architectural.**

- Future patterns are gated on the three structural commitments. Any pattern requiring vendor cooperation (e.g., a vendor-provided attestation that cannot be operator-verified) is rejected by the category. The MI Proxy in ADR-0013 is the canonical example: even the verifier is operator-attestable.
- The Regulatory-Incident Replay framework shipping in v0.2.2 directly operationalizes the category claim. Each named matter replays a failure shape where operator-side audit would have produced the evidence the vendor-side audit did not.

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| Frame as "AI governance" generally | Generic category with 500+ entrants. No defensible differentiation. Commodity pricing pressure. |
| Frame as "CRE-only AI governance" | Under-prices the framework's structural commitments. Does not transfer to the FSI sibling repo. Misses inter-vertical defensibility. |
| Frame as "vendor-neutral AI audit" | Implies vendor-side could be neutral. Obscures the structural conflict. |
| Frame as "regulator-friendly AI governance" | Implies regulator audience first. The framework is operator-first by design. |
| Do not claim a category | Lets competitors define the terms. Cedes positioning advantage. Accepts commodity outcomes. |

## Regulatory mapping

- **SOC 2 CC7.2** (System Monitoring) — Operator-side audit infrastructure satisfies the monitoring criterion in a way that vendor-grading-itself does not.
- **SOX 404 ITGC** — The operator-controlled audit ledger satisfies the change-management and access-control criteria the auditor exercises. Vendor-side audit fails the same exercise because the vendor is not the audited entity.
- **FFIEC IT Handbook Appendix J** — Third-party risk management. This category explicitly acknowledges the vendor as the third-party risk and instruments accordingly.
- **CFPB Circular 2022-03** — Adverse-action notice obligations under FCRA / ECOA are operator-side, not vendor-side. The framework supports the operator's documentary burden when an AI-derived adverse action is issued.
- **HUD final rule (June 2024)** restoring the Obama-era disparate-impact framework under the Fair Housing Act — operator-side audit is the evidentiary path for the three-step burden-shifting analysis.
- **Colorado SB 189** (signed March 14, 2026, effective January 1, 2027) — operator AI deployers in Colorado need operator-side records by January 2027.

## Related

- ADR-0003 — Hash-chained audit ledger (the operator-side chain-of-custody primitive)
- ADR-0011 — Vendor-output adapter (the vendor-input boundary)
- ADR-0012 — Persistence / timestamps / witness anchor (substrate-level operator commitments)
- ADR-0013 — MI Proxy (operator-attestable verifier)
- [`THESIS.md`](../../THESIS.md) — three-year project commitment grounded on this category
- [`PUBLICATIONS.md`](../../PUBLICATIONS.md) — academic publication track defending the category claim
- [`examples/regulatory-incidents/`](../../examples/regulatory-incidents/) — named-matter replays operationalizing the category
- [`docs/services/`](../../docs/services/) — productized services anchored on the category

## Implementation notes

This ADR is positioning, not code. The supporting code + content shipping alongside in v0.2.2:

- `src/cre_agent_audit/regulatory_replay/` — the framework that operationalizes the category claim (IncidentReplay Protocol + EvidenceBundle + cre-replay CLI)
- `examples/regulatory-incidents/` — three named-matter replays (TransUnion, SafeRent, RealPage-as-alleged)
- `docs/services/` — seven productized service templates (5 public-anchor + 2 private-tier)
- `THESIS.md` + `PUBLICATIONS.md` — the long-term commitment + the academic credibility track

Future ADRs (likely 0015+) build on this one. Any new pattern, any new vertical, any new product offering is measured against the three structural commitments named above.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
