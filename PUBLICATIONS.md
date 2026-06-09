# PUBLICATIONS — Academic Publication Track

**Status:** Public commitment · maintained by Kunjar Bhaduri · last refreshed 2026-05-28

This document records the academic publication targets for the `cre-agent-audit` and `finserv-agent-audit` projects. An explicit publication track makes the framework defensible against academic-credibility competitors (researchers at the Bailey-Borghesi, Stuart Russell, Solon Barocas, Margaret Mitchell, Timnit Gebru level) and signals to potential adopters that the methodology is going through peer review.

## Why publication matters here

Risk committees at Tier-1 banks, top-10 health insurance carriers, and Big-4 partner deliverables cite *peer-reviewed methodology*. A framework with zero peer-reviewed citations reads as practitioner commentary regardless of its technical merit. A framework with two or three peer-reviewed publications survives Daubert-grade scrutiny and Big-4 methods review.

## Target venues

| Venue | Why this venue | Submission shape |
|---|---|---|
| **ACM SEMS** (Symposium on Engineering and Mathematics of Security) | Methods + matrix-as-contract pattern fit the engineering-meets-security focus. | Short paper, 8–10 pages |
| **ACM FAccT** (Conference on Fairness, Accountability, and Transparency) | Operator-side mutual-information-threshold proxy detection + the fair-housing pre-flight gate match FAccT's policy-AI-fairness intersection. | Full paper, 12–15 pages |
| **Journal of Risk & Financial Management** (MDPI, peer-reviewed open access) | Triple-witness (RFC 3161 + Sigstore Rekor + MI Proxy) as audit-evidence pattern for SOX 404 ITGC; cross-vertical (CRE + FSI). | Full journal article |
| **SAFE consortium / NIST AI RMF profile** | CRE-vertical profile proposal — the framework as a worked example of a vertical-specific NIST AI RMF profile. | NIST community comment + workshop submission |

## Drafts in flight

### Draft 1 — `FAILURE-MODES.md` matrix-as-contract pattern (ACM SEMS target)

**Working title:** "Doc/Code Parity as a Build-Time Invariant: A Pattern for Audit-Framework Maintainability"

**Status:** Outline drafted. Pulls from the `FAILURE-MODES.md` matrix shipped in v0.2.1, the companion `tests/test_failure_modes_matrix.py` drift test, and the `tests/test_doc_staleness.py` pattern.

**Submission target:** Q1 2027

**Lead author:** Kunjar Bhaduri

### Draft 2 — Operator-side MI-threshold proxy detection (ACM FAccT target)

**Working title:** "Operator-Side Mutual-Information Proxy Detection for Fair-Housing AI Decision Stacks"

**Status:** Implementation shipped in v0.2.2 (2026-05-28) — `MIThresholdDetector` + `MutualInformationCalculator` in `src/cre_agent_audit/governance/mi_threshold_detector.py`; SafeRent-shaped synthetic reference at `tests/fixtures/saferent_shaped_reference.py`; `FHA-MI-PROXY` veto code wired into `fair_housing_preflight.py`. Outline ready to draft.

**Submission target:** Q3 2027

**Lead author:** Kunjar Bhaduri

### Draft 3 — Triple-witness pattern for audit-evidence (Journal of Risk & Financial Management target)

**Working title:** "Triple-Witness Audit-Evidence for SOX 404 ITGC: RFC 3161 + Sigstore Rekor + Module-Integrity Proxy"

**Status:** Outline drafted. Pulls from ADR-0012 (persistence/timestamps/witness) and ADR-0013 (MI Proxy) in v0.2.1.

**Submission target:** Q4 2027

**Lead author:** Kunjar Bhaduri

### Draft 4 — NIST AI RMF CRE-vertical profile (SAFE consortium / NIST community)

**Working title:** "A Commercial Real-Estate Profile for the NIST AI Risk Management Framework"

**Status:** Outline pending. Depends on v0.3.0 state-by-state regulatory mappings.

**Submission target:** Q1 2028

**Lead author:** Kunjar Bhaduri

## Citation discipline

Every publication cites the framework version (with DOI) used as the methodological basis:

- `cre-agent-audit` v0.2.1: DOI [10.5281/zenodo.20434575](https://doi.org/10.5281/zenodo.20434575)
- Future releases will have their own DOIs.

Cross-references to settled matters use verbatim primary-source citations:

- Case name, court (or agency), docket, ISO-8601 date, dollar amount where on the record
- *U.S. v. RealPage, Inc. et al.* (filed August 23, 2024; Sherman Act §§ 1 and 2) — **resolved by a DOJ proposed consent judgment (filed Nov 24, 2025, pending Tunney Act approval), without admission of liability**, never described as adjudicated

## How citations help the moat

Each peer-reviewed publication produces:

1. **An academic citation surface** — every future paper citing the work compounds the framework's authority (Helmer Power 5, Branding).
2. **A defensibility anchor** — Big-4 methods review and BigLaw Daubert challenges become survivable.
3. **A speaking-circuit credential** — peer-reviewed work qualifies for tier-1 conference invitations. Speaking engagements are direct revenue (per `THESIS.md` § Productization, $10K–$25K per talk × 6–12/yr) and indirect credibility (each talk seeds the audience for the next productized-service buyer).
4. **An audience-expansion signal** — academic readers become inbound for the productized-service portfolio (`docs/services/`).
5. **A case-history compounding signal** — every peer-reviewed publication is a public anchor that references the (private) case-history library built from paid engagements. Maister's professional-service-firm moat: "we have N prior matters on this exact surface" reads with peer-reviewed credibility, not as practitioner anecdote.

## Cadence integration

The peer-review track is annual; the publishing cadence is weekly + quarterly. They interlock. Each weekly LinkedIn post and each X thread compounds the audience that reads the quarterly *State of CRE-AI Governance* report; the quarterly report cites the most recent peer-reviewed paper; the peer-reviewed paper anchors the framework version that's three months old by submission and stable. The result: no month without a public artifact, no quarter without a published report, no year without a peer-reviewed submission.

## Verifiability

When a draft ships, this document updates the status field from "outline" → "submitted" → "accepted" → "published" with the venue link. Reviewers and adopters can verify the trajectory at any time.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
