# Prior Art and Intellectual Lineage

> **Reference acknowledgement, not a complete literature review.** This document lists the prior work the cre-agent-audit patterns build on, so adopters and reviewers can place the patterns in the broader AI-governance + algorithmic-fairness + safety-critical-systems literature. See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md).

## Staged-autonomy frameworks (foundation for Pattern 4 — Autonomy Ladder™ A0→A4)

The A0→A4 ladder structure is intentionally isomorphic to staged-autonomy frameworks already familiar to engineering and regulatory audiences. **The Autonomy Ladder ladder structure is borrowed and acknowledged; the contribution of ADR-0004 is the CRE-vertical mapping of autonomy tier to specific patterns and to specific regulatory matters.**

- **SAE J3016** — *Taxonomy and Definitions for Terms Related to Driving Automation Systems for On-Road Motor Vehicles* (SAE International, 2014 / revised 2018 / revised 2021). The 0–5 ladder structure originates here. Autonomy Ladder A0→A4 is a five-tier adaptation for governed agentic AI in regulated workflows.
- **OECD AI Principles** (2019; updated 2024) — Recommendation of the Council on Artificial Intelligence (OECD/LEGAL/0449). Staged-oversight language for AI systems.
- **NIST AI Risk Management Framework 1.0** (January 2023) — MANAGE 2.3 (risk decisions documented) + MANAGE 3.1 (third-party + procurement-related risk) — maturity scaffolding for human oversight scaling with risk.
- **Shavit, Brundage, Lin, et al.** (2023) — *Practices for Governing Agentic AI Systems* (OpenAI white paper) — tier-based agent-autonomy framing.
- **Anderljung, Barnhart, Korinek, et al.** (2023) — *Frontier AI Regulation: Managing Emerging Risks to Public Safety* — staged-deployment framing.

## Assurance-case methodology (foundation for "evidence stack" language in ADR-0004)

The "assurance case" framing in ADR-0004 — "AI operating above the autonomy level its assurance case could defend" — is borrowed term-of-art from safety-critical-systems literature:

- **Kelly & Weaver** (2004) — *The Goal Structuring Notation – A Safety Argument Notation* — established the term "assurance case" for a structured argument that a system is acceptably safe for a defined context.
- **Bloomfield, Bishop, Penny** (2021) — *Assurance Cases for AI: A Survey* — survey of assurance-case methodology applied to AI systems.

This replaces the prior coinage "evidence stack" with a term that has provenance in the field.

## Algorithmic fairness and accountability (foundation for Pattern 8 — Fair-Housing Pre-Flight Gate)

The Fair-Housing Pre-Flight Gate is informed by a body of work in algorithmic fairness, accountability, and the sociotechnical critique of fairness-as-a-technical-property:

- **Barocas, Hardt & Narayanan** (2019, ongoing) — *Fairness and Machine Learning* (https://fairmlbook.org) — foundational text for fairness in ML.
- **Selbst, boyd, Friedler, Venkatasubramanian, Vertesi** (2019) — *Fairness and Abstraction in Sociotechnical Systems* (FAT* 2019) — the five "traps" of treating fairness as a technical property; foundational critique that informs ADR-0008's "this gate governs deployment, not training" framing.
- **Mitchell, Wu, Zaldivar, Barnes, Vasserman, Hutchinson, Spitzer, Raji, Gebru** (2019) — *Model Cards for Model Reporting* (FAT* 2019) — the model-card format referenced in `docs/vendor-clauses/screening.md` Section 2.1.
- **Gebru, Morgenstern, Vecchione, Vaughan, Wallach, Iii, Crawford** (2021) — *Datasheets for Datasets* (CACM 64(12)) — datasheet format for training data; informs ADR-0007's provenance approach to lease-extraction training data.
- **Raji, Smart, White, Mitchell, Gebru, Hutchinson, Smith-Loud, Theron, Barnes** (2020) — *Closing the AI Accountability Gap: Defining an End-to-End Framework for Internal Algorithmic Auditing* (FAT* 2020) — informs the audit-program scaffolding in `docs/controls/`.

### Fairness-impossibility results (foundation for `docs/LIMITATIONS.md` Section 5)

- **Kleinberg, Mullainathan & Raghavan** (2016) — *Inherent Trade-Offs in the Fair Determination of Risk Scores* — established that calibration vs balance-for-negative-class vs balance-for-positive-class are mutually inconsistent except in degenerate cases.
- **Chouldechova** (2017) — *Fair prediction with disparate impact: A study of bias in recidivism prediction instruments* — the parallel impossibility result for criminal-justice risk scores.
- **Kasy & Abebe** (2021) — *Fairness, Equality, and Power in Algorithmic Decision-Making* (FAccT 2021) — distributive-justice critique of group-fairness metrics.

### Counterfactual fairness (foundation for v0.3 MI-threshold learned-proxy detection)

- **Kusner, Loftus, Russell, Silva** (2017) — *Counterfactual Fairness* — counterfactual definition of fairness; informs the v0.3 learned-proxy detection roadmap.

## Tamper-evidence and external witness anchoring (foundation for Pattern 3 — Audit Ledger)

The hash-chain construction is standard; the witness-anchor framing follows established literature:

- **Haber & Stornetta** (1991) — *How to Time-Stamp a Digital Document* — established the witness-anchor pattern for digital-timestamping integrity.
- **Laurie, Langley, Käsper** (2013) — *RFC 6962: Certificate Transparency* — design rationale for append-only logs with external witness verification.
- **OpenTimestamps** (Todd, 2016 onwards) — open-source Bitcoin-anchored timestamping.
- **Sigstore Rekor** (Linux Foundation, 2021 onwards) — append-only transparency log for software-supply-chain signatures; analogous architecture for audit-chain anchoring.

## Doctrinal foundation (Fair-Housing Pre-Flight Gate)

- ***Texas Department of Housing v. Inclusive Communities Project, Inc.***, 576 U.S. 519 (2015) — constitutionalized disparate-impact under the Fair Housing Act; articulated the burden-shifting framework HUD codified at 24 C.F.R. § 100.500.
- **Fair Housing Act**, 42 U.S.C. § 3601 et seq. — substantive anti-discrimination statute.
- **Equal Credit Opportunity Act**, 15 U.S.C. § 1691 et seq. — adverse-action notice requirements for credit and housing-credit decisions.
- **Fair Credit Reporting Act**, 15 U.S.C. § 1681 et seq. — accuracy + dispute rights for consumer reports; foundation for the TransUnion 2023 FTC/CFPB enforcement that anchors ADR-0008's Context section.
- **HUD Disparate Impact Rule**, 24 C.F.R. § 100.500 — disparate-impact burden-shifting framework.
- **Uniform Guidelines on Employee Selection Procedures**, 29 C.F.R. § 1607.4(D) — four-fifths-rule formalization (employment context; analogous reasoning applied in housing context).

## Standards-and-frameworks foundation (Big-4 audit overlay; see `docs/MAPPING-MATRICES.md`)

- **NIST AI Risk Management Framework 1.0** (NIST AI 100-1, January 2023)
- **NIST AI RMF Generative AI Profile** (NIST AI 600-1, July 2024)
- **ISO/IEC 42001:2023** — *Information technology — Artificial intelligence — Management system*
- **ISO/IEC 23894:2023** — *Information technology — Artificial intelligence — Guidance on risk management*
- **COSO ICAIR** (COSO + Deloitte, 2024) — Internal Control over AI Reporting overlay
- **Treasury FS AI RMF** (U.S. Department of the Treasury, February 2026) — 230 control objectives for financial-services AI
- **FINOS AI Risk Initiative** — open-source industry catalog of AI risks and mitigations; the format `governance-artifacts/AIR-*.md` targets
- **SR 11-7** (Federal Reserve, 2011) — *Guidance on Model Risk Management* — foundation for Pattern 6 Shadow-Mode Rollout
- **OCC Bulletin 2013-29** (OCC, 2013) — third-party risk management; informs vendor-side controls in ADR-0011

## Privilege and discovery doctrine (foundation for ADR-0010)

- **Federal Rules of Civil Procedure**: Rule 26(b)(3) (work-product); Rule 502 (privilege waiver); Rule 37(e) (lost ESI)
- **Federal Rules of Evidence**: 501 (privilege); 801(d)(2) (party admissions)
- ***Upjohn Co. v. United States***, 449 U.S. 383 (1981) — attorney-client privilege scope in corporate context
- ***Hickman v. Taylor***, 329 U.S. 495 (1947) — origin of the work-product doctrine

## Antitrust (foundation for ADR-0008 + `docs/vendor-clauses/pricing.md`)

- ***U.S. v. RealPage, Inc.***, M.D.N.C. (filed Aug 23, 2024) — DOJ + 8 state AGs civil antitrust litigation alleging Sherman § 1 violations via algorithmic rent-coordination; ongoing as of v0.2.0.
- **Sherman Act § 1**, 15 U.S.C. § 1 — substantive antitrust statute.
- **Per se vs rule-of-reason analysis** — doctrinal framing referenced in vendor-clauses/pricing.md regarding the limits of process-evidence good-faith defenses.

## Regulatory matters (foundation for the README lede and ADR-0008 Context section)

- ***In re Trans Union Rental Screening Solutions, Inc.***, FTC + CFPB joint consent orders (October 2023, $15M) — FCRA § 607(b) accuracy in rental-screening reports.
- ***Louis v. SafeRent Solutions, LLC***, No. 1:22-cv-10800 (D. Mass., class settlement approximately $2.275M, November 2024; settlement included five-year score-use injunction on voucher-holder applicants) — tenant-screening AI scores below threshold with no documented reason.
- **Colorado AI Act** (SB24-205, signed May 17, 2024; effective February 1, 2026; follow-on amendments tracked separately) — housing as consequential decision; deployer obligations.

## What this lineage does NOT cover

- Vertical-specific regulatory regimes outside CRE (PCI DSS, HIPAA, DORA, etc.)
- Pre-2015 algorithmic fairness literature (the field's foundational papers are largely 2015-onwards; earlier work on statistical discrimination is referenced via Barocas/Hardt/Narayanan)
- Non-US legal frameworks (EU AI Act is cited in compliance YAML; GDPR is cited in ADR-0009; broader international frameworks out of scope for this lineage doc)
- Internal Anthropic / OpenAI / DeepMind / etc. governance work that is not publicly published

## Annual review

This document is reviewed annually. The patterns + frameworks + doctrinal foundations move; the lineage must move with them. Each annual review records the field updates that informed any pattern revisions in the equivalent of `docs/SESSION-AUDIT.md` Verified Facts Ledger style.

If you identify prior work the patterns build on that is not cited here, please open a PR with the citation + the pattern(s) it informs.
