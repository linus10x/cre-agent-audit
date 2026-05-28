# Diagnostic — $5K

**Duration:** 90-minute interview + 5 business days for the deliverable

**Deliverable:** A 20-page written assessment naming where your AI-governance posture exposes you to a SafeRent-shaped, TransUnion-shaped, or RealPage-shaped failure mode — anchored on three named regulatory matters and the operator-side patterns from the published framework.

**Target buyer:** CRE technology VP · PE deal team scoping a portfolio AI-readiness review · Big-4 partner evaluating client engagement scope · in-house counsel preparing for a CFPB / FTC / state-AG inquiry

## What you get

1. **90-minute interview** — structured conversation walking your AI surface (tenant-screening, lease-abstraction, pricing / revenue management, vendor-mediated decisions, in-house models)
2. **20-page assessment document** — `cre-agent-audit` framework patterns mapped to your declared surface, with named exposure points
3. **Three-matter posture comparison** — your stack measured against the TransUnion, SafeRent, and RealPage (alleged) failure shapes from `examples/regulatory-incidents/`
4. **Specific remediation priorities** — ranked by exposure severity, sized by effort
5. **Optional referral path** — to BigLaw / Big-4 / engineering implementers if the diagnostic surfaces work outside operator-side audit scope

## Methodology

- Anchored on `cre-agent-audit` v0.2.1+ (DOI [10.5281/zenodo.20434575](https://doi.org/10.5281/zenodo.20434575))
- Patterns engaged depend on your declared surface; typically ADR-0001 (DEFCON) · ADR-0002 (Sovereign Veto) · ADR-0003 (audit ledger) · ADR-0008 (Fair-Housing Pre-Flight) · ADR-0011 (Vendor-Output Adapter) · ADR-0012 (persistence / timestamps / witness anchor) · ADR-0013 (MI Proxy)
- Each finding cites a primary-source regulatory anchor
- Methodology is the Regulatory-Incident Replay framework (`src/cre_agent_audit/regulatory_replay/`)

## What's NOT in the public framework

- **Operator-specific exposure mapping.** The public framework names the patterns; this engagement names which patterns expose your specific stack — and where you would be exposed to a SafeRent-shaped or TransUnion-shaped failure mode if a regulator inquiry landed tomorrow. The exposure map is not in the public docs.
- **Confidential risk-rank.** The 20-page deliverable ranks the exposure points by severity for your stack — a confidential prioritization the framework cannot publish (each ranking depends on your specific declared surface).
- **De-identified pattern library reference.** Where applicable, the engagement references de-identified patterns from the private case-history corpus that informs framework v.next.

## What's NOT in scope

- Code implementation or framework deployment in your stack
- Legal opinion on whether your specific conduct violates any statute
- Vendor due-diligence against specific tenant-screening, lease-abstraction, or pricing vendors
- Penetration testing or red-team adversarial review
- Audit-evidence bundle production against your live data (that's the Audit engagement at $40K)

## How to engage

- Email `contact@autonomy-ladder.io` with `[Diagnostic]` in the subject
- Intake: (1) firm name + role; (2) specific AI-governance pain point; (3) internal sponsor / approver
- Engagement letter issued within 2 business days of intake acceptance
- 90-minute interview scheduled within 2 weeks of engagement-letter signature
- Deliverable within 5 business days of the interview

## Pricing

- **$5,000 fixed-fee.** 50% on engagement-letter signature; 50% on deliverable handoff.
- Travel + expenses passed through at cost (typical $0–$500 for video-conference engagements)
- No discount tier. The Diagnostic price is the gating mechanism; sub-$5K work is declined as a matter of standing rule.

## Disclaimer

Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment. This engagement produces audit-governance recommendations grounded in the published framework; it does not constitute legal counsel and does not adjudicate any specific regulatory matter. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
