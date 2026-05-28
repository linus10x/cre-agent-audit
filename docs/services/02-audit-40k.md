# Audit — $40K

**Duration:** 4 weeks

**Deliverable:** A complete audit-evidence bundle on the operator's actual AI surface — chain export, verify report, MI Proxy attestation, findings, controls description table, executive narrative — produced from the operator's live data using the Regulatory-Incident Replay harness applied to the operator's vendor stack.

**Target buyer:** Top-50 multifamily operating company · Big-4 client engagement (where the partner needs operator-side audit-evidence to support their deliverable) · publicly-traded REIT preparing for SOX 404 ITGC review · operating company responding to a regulator inquiry

## What you get

1. **Engagement-letter scope definition** — explicit listing of which AI surfaces (tenant-screening, lease-abstraction, pricing, vendor-mediated) are in scope and the time-window covered
2. **Audit-evidence bundle** — six-file zip per surface (audit_chain.jsonl + verify_chain_report.json + mi_proxy_attestation.json + findings.json + controls_description_table.md + narrative.md) per the `EvidenceBundle` shape shipped in v0.2.2
3. **20–30 page audit-engagement report** — executive summary, methodology, findings by surface, remediation roadmap, primary-source citations
4. **Controls description table** — per-finding mapping to existing CTRL-NNN docs + recommended new controls
5. **MI Proxy attestation** — out-of-band verifier integrity attestation (ADR-0013) wired during engagement
6. **Engagement-close briefing** — 90-minute readout with the operator's CTO / CAIO / Chief Risk Officer + audit committee point of contact
7. **Confidential client memo** filed in the private engagement corpus (Maister PSF discipline — see `feedback_engagement_capture_discipline` memory)

## Methodology

- Anchored on `cre-agent-audit` v0.2.1+ (DOI [10.5281/zenodo.20434575](https://doi.org/10.5281/zenodo.20434575))
- The Regulatory-Incident Replay harness (`src/cre_agent_audit/regulatory_replay/`) is run against the operator's actual decision pipeline, not just synthetic data
- Patterns engaged depend on scope; typical full-stack audit engages ADR-0001 through ADR-0013
- `verify_chain(mi_proxy=...)` runs with a deployer-attested MI Proxy backing the verifier
- Each finding cites a primary-source regulatory anchor (FCRA, FHA, ECOA, CFPB Circular 2022-03, HUD June 2024 final rule, Colorado SB 189, etc.)

## What's NOT in the public framework

- **Operator-specific evidence bundle on live data.** The public framework produces the bundle shape; this engagement produces the bundle with your data. The bundle is the audit-evidence Big-4 partners hand to clients and BigLaw counsel files as supporting documentation.
- **MI Proxy attestation tied to your specific verifier deployment.** The public framework defines the seam; this engagement wires it.
- **Engagement-letter scope contract.** The 4-week engagement carries a defined scope, a defined deliverable, and a defined turn-around — none of which the open framework can pre-commit to.
- **Audit-committee readout slot.** A 90-minute live briefing for the operator's audit committee / risk committee, prepared and delivered by Kunjar Bhaduri personally.

## What's NOT in scope

- Code implementation in the operator's stack beyond the audit instrumentation
- Legal opinion or counsel
- Vendor contract renegotiation (vendor-clause templates ship publicly; vendor selection is out of scope)
- Indemnification or warranty for the operator's downstream decisions
- Continuous monitoring beyond the 4-week window (that's the Retainer at $15K/q)
- Penetration testing or adversarial red-team review

## How to engage

- Email `contact@autonomy-ladder.io` with `[Audit]` in the subject
- Intake: (1) firm name + role; (2) AI surface(s) in scope; (3) time-window; (4) internal sponsor; (5) regulator-inquiry context (if any)
- Engagement letter within 5 business days
- 4-week engagement initiated within 4 weeks of engagement-letter signature
- Audit-evidence bundle and engagement report delivered at week 4
- Engagement-close briefing within 2 weeks of deliverable handoff

## Pricing

- **$40,000 fixed-fee.** 50% on engagement-letter signature; 50% on deliverable handoff.
- Travel + expenses passed through at cost (typical $1,000–$5,000 for on-site engagements)
- Scope expansion priced at $5,000 per additional AI surface beyond the engagement-letter scope
- No discount tier

## Disclaimer

Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment. This engagement produces audit artifacts and governance recommendations grounded in the published framework; it does not constitute legal counsel and does not adjudicate any specific regulatory matter. The audit-evidence bundle is documentation, not adjudication — the operator and their counsel determine how the evidence is used. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
