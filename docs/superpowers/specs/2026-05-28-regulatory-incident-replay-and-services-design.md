# Spec — Regulatory-Incident Replay Framework + Productized Services + Moat Layer · 2026-05-28

**Status:** Approved (brainstorming → design → spec) 2026-05-28
**Owner:** Kunjar Bhaduri
**Repo:** `linus10x/cre-agent-audit` (`main` at `3f3aaaf`)
**Pre-release marker:** `0.2.2.dev0` (v0.2.1 released; this work targets v0.2.2)
**Publish gate:** None. Drafts + service templates committed; revenue gates depend on Kunjar's own engagement, not on this work shipping.

## Goal

Land the single artifact most likely to convert a sophisticated CRE-tech VP, Big-4 partner, BigLaw advisor, or PE operating partner from cold visitor to qualified lead. Anchor it on a moat stack that compounds — Cornered Resource + Counter-positioning + Branding + Process Power + Network Economies (Helmer's 7 Powers, three- to five-power stack for this case).

## Non-goals

- No tag creation; v0.2.2 final tag waits on the 3 deferred v0.2.1 items.
- No publish to LinkedIn / X / HN (handled separately in Cowork).
- No commercial-software product (Postgres adapter / SaaS dashboard / hosted attestation) — that's a separate $250K+ engineering investment for v0.3+.
- No real customer engagement contracts. Service templates are public-facing scope definitions; actual engagements are still hand-sold.
- No banned-name references; no Colorado SB 24-205 as operative; no RealPage as settled.

## Moat thesis (the load-bearing rationale)

The chamber panel converged on a 5-power stack from Helmer's 7 Powers:

1. **Cornered Resource (Helmer 6)** — Kunjar's specific track-record combination. Non-replicable. Already paid-for. Underweighted in current strategy until this work makes attribution explicit.
2. **Counter-positioning (Helmer 1)** — "Operator-side AI governance for regulated industries" sets up vendor-side incumbents (RealPage Compliance, Yardi Risk, MRI Compliance) as compromised. Cannot be copied without business-model damage.
3. **Branding (Helmer 5)** — Autonomy Ladder™ + framework cadence + sustained publication. Compounds over 18–24 months.
4. **Process Power (Helmer 7)** — Framework discipline + SoT propagation + private engagement-corpus from every paid engagement. Compounds per engagement.
5. **Network Economies (Helmer 4)** — Practitioner-bench community + open-source contribution graph + cited-matter network. Compounds with community scale.

Explicitly NOT pursuing: Scale Economies (Helmer 2 — solo cap), Switching Costs (Helmer 3 — low in advisory).

The realistic moat (achievable in 3–6 months) is Authorship + Cornered Resource + Pricing-as-Moat. The durable moat (compounds over 5–10 years) is Cornered Resource + Counter-positioning + sustained Cadence + private Case-History Library. They are not in tension. The realistic moats generate the surface on which the durable moats compound.

## Council slate (15-mentor panel for this work)

Engineering + brand + strategy chambers:

| Mentor | Lens |
|---|---|
| Hamilton Helmer | 7 Powers moat framework |
| Warren Buffett | Durable competitive advantage |
| Peter Thiel | Monopoly / category-of-one |
| Marc Andreessen | Open-source as B2B trust go-to-market |
| Bill Gurley | Service-business economics |
| Clay Christensen | Jobs-to-be-done |
| David Maister | Professional service firm moats |
| Alan Weiss | Solo consulting / pricing-as-moat |
| Naval Ravikant | Specific knowledge + leverage |
| Marcos López de Prado | Academic-credibility track |
| Justin Welsh | Solopreneur audience cadence |
| Dorie Clark | Recognized-expert archive |
| Elad Gil | Category creation |
| Charity Majors | Production credibility |
| Charles Margolis (Brian Balfour) | Product-channel-market fit |

Pass = 10/10 from each, zero must-fix gaps. Capped at 3 revision passes per artifact. If 10/10 unreachable after 3 passes, surface the blocker and stop.

## Deliverables

### D1 — `docs/adr/0014-operator-side-ai-governance-category.md` (category claim)

The formal category-claim ADR. Not a code decision; a positioning decision recorded in the same form as the technical ADRs to maintain the discipline pattern. Names "operator-side AI governance for regulated industries" as the category. Cites the counter-positioning rationale (Helmer 1). Distinguishes from vendor-side incumbents (RealPage Compliance Studio, Yardi Risk, MRI Compliance) explicitly. Names the 6 chamber positions on why this category claim is defensible.

### D2 — `THESIS.md` (3-year project commitment)

Repo-root file. Public commitment document. Covers:
- The 3-year roadmap: framework maturity (v0.2 → v0.5)
- The publication track (3 peer-reviewed papers across 2026–2028)
- The publishing cadence (quarterly State of CRE-AI Governance reports + weekly content per CLAUDE.md cadence)
- The product portfolio commitment (services + intel + bench + course)
- The cornered-resource attribution (Five Pillars from CLAUDE.md — named explicitly)
- Why this is a multi-year project, not a one-shot

Voice: operator-with-leverage, first-person singular, no aspiration language. Specific dates and named deliverables.

### D3 — `PUBLICATIONS.md` (academic publication track)

Repo-root file. Names target venues:
- ACM SEMS (Symposium on Engineering & Mathematics of Security) — methods paper on FAILURE-MODES.md matrix-as-contract pattern
- FAccT (ACM Conference on Fairness, Accountability, and Transparency) — paper on operator-side mutual-information-threshold proxy detection (when v0.2.2 lands)
- Journal of Risk & Financial Management (MDPI) — paper on RFC 3161 + Sigstore Rekor + MI Proxy as triple-witness pattern for SOX 404 ITGC audit-evidence
- SAFE consortium / NIST AI RMF profile submission — CRE-vertical profile proposal

Each entry includes: target venue, draft title, status, target submission date, lead author (Kunjar Bhaduri).

### D4 — `src/cre_agent_audit/regulatory_replay/` (the harness)

Python subpackage. Six modules:

```
regulatory_replay/
├── __init__.py          # Re-exports IncidentReplay, Finding, EvidenceBundle, etc.
├── replay.py            # IncidentReplay Protocol + IncidentReplayBase + ReplayResult
├── findings.py          # Finding, Severity, Evidence, Citation dataclasses
├── evidence_bundle.py   # EvidenceBundle.assemble() + .write_zip()
├── scoring.py           # pattern-coverage score per matter; matrix vs failure-modes
└── cli.py               # `cre-replay` Click-style CLI
```

The `IncidentReplay` Protocol surface:

```python
class IncidentReplay(Protocol):
    matter_id: str                       # "01_transunion_rental_screening"
    matter_title: str                    # verbatim case identification
    primary_sources: tuple[Citation, ...]
    failure_shape: str                   # 1-paragraph plain-English failure description
    patterns_engaged: tuple[ADRRef, ...]

    def synthetic_dataset(self) -> Iterable[Any]: ...
    def run_replay(
        self,
        *,
        ledger: AuditLedger,
        gates: Mapping[str, object],
    ) -> ReplayResult: ...
    def expected_findings(self) -> tuple[Finding, ...]: ...
```

`EvidenceBundle` assembles + writes a zip per matter:

```
audit-evidence/<matter>.zip
├── audit_chain.jsonl
├── verify_chain_report.json
├── mi_proxy_attestation.json
├── findings.json
├── controls_description_table.md
└── narrative.md
```

CLI entry point in `pyproject.toml`: `cre-replay = "cre_agent_audit.regulatory_replay.cli:main"`. Commands: `list`, `run <matter_id>`, `run-all`, `verify <matter_id>`.

### D5 — `examples/regulatory-incidents/` (three matters in PR 1)

Directory structure:

```
examples/regulatory-incidents/
├── README.md                              # gallery; sets framing
├── 01_transunion_rental_screening/
│   ├── README.md                          # 300-500w narrative + primary-source citations
│   ├── replay.py                          # IncidentReplay implementation
│   ├── synthetic_data.json                # shape-faithful, no real PII
│   ├── expected_findings.json             # TDD contract
│   └── audit-evidence/                    # .gitignore'd; generated by replay
├── 02_saferent_voucher_screening/
│   └── ... (same structure)
└── 03_realpage_ongoing_litigation/
    └── ... (same structure)
```

Per-matter content discipline:

- **01_transunion** — TransUnion Rental Screening Solutions consent orders (FTC + CFPB, October 2023, $15M, FCRA § 607(b) accuracy). Synthetic 500-record dataset with shape-faithful accuracy errors. Replay engages ADR-0003 + ADR-0007 + ADR-0011 + VendorScoreGate. Expected findings: ~47 score-drift flags + 12 chain-of-custody breaks.
- **02_saferent** — Louis v. SafeRent Solutions (D. Mass., November 2024, ~$2.275M class settlement, five-year score-use injunction). Synthetic 1,000-applicant dataset with voucher-status proxies + criminal-history blanket exclusions + undocumented threshold scoring. Replay engages ADR-0008 + ADR-0002 + ADR-0003 + ADR-0011. Expected findings: ~89 VETO codes + 12 blanket-exclusion blocks.
- **03_realpage** — *U.S. v. RealPage, Inc. et al.* (M.D.N.C. Aug 23, 2024, DOJ + 8 state AGs, ongoing antitrust litigation). Framed as ALLEGED conduct throughout. Synthetic 50-decision dataset modeling coordination signals (not adjudicating). Replay engages ADR-0001 + ADR-0002 + ADR-0011 + VendorScoreGate drift detection. Findings include "consult counsel re: Sherman § 1 exposure" rather than legal conclusions.

Voice constraint applied across all three: opens with the disclaimer "This worked example is not legal advice and does not adjudicate the underlying matter. Patterns are software, not regulatory determinations."

### D6 — `docs/services/` (seven productized-service templates)

Directory structure:

```
docs/services/
├── README.md                              # gallery; how-to-engage; pricing rationale
├── 01-diagnostic-5k.md                    # $5K · 90-min interview + 20-page deliverable
├── 02-audit-40k.md                        # $40K · 4 weeks · full audit-evidence bundle
├── 03-retainer-15k-quarterly.md           # $15K/q · quarterly rerun + new-incident coverage
├── 04-workshop-25k-50k.md                 # $25K-50K · 1-day on-site or 2-day virtual
├── 05-cohort-50k-200k.md                  # $50K-200K · 8-week program · 20-40 seats
├── 06-private-intel-subscription.md       # $25K-100K/yr · gated newsletter + catalog
└── 07-practitioner-bench.md               # $10K-50K/yr · invite-only community
```

Each template follows this shape:

```markdown
# <Service name> — $<price>

**Duration:** <X>
**Deliverable:** <one sentence>
**Target buyer:** <named role + firm tier>

## What you get
- (numbered list of concrete artifacts)

## Methodology
- Anchored on the cre-agent-audit framework + Regulatory-Incident Replay
- Specific patterns engaged: ADR-NNNN, ADR-NNNN
- Each finding cites primary regulatory source

## What's NOT in the public framework
- (what this engagement adds beyond the open repo)

## What's NOT in scope
- (explicit boundaries)

## How to engage
- Email: contact@autonomy-ladder.io
- Three-question intake form

## Pricing
- Fixed-fee; 50% on engagement letter, 50% on delivery
- Travel + expenses at cost

## Disclaimer
- Patterns are software, not legal advice
- See repo-root DISCLAIMER.md
```

Services 06 and 07 are private-tier — the moat-strengthening layer. Each template's "What's NOT in the public framework" section is load-bearing: it names what the paid engagement gives buyers that the open repo does not.

### D7 — Tests

- `tests/test_regulatory_replay_framework.py` — harness conformance. Verifies:
  - `IncidentReplay` Protocol surface (every required method)
  - `EvidenceBundle.assemble()` produces all 6 files
  - `EvidenceBundle.write_zip()` produces a valid zip
  - `Finding` validates severity / evidence shape
  - `cre-replay` CLI commands run without error against a stub replay
- `tests/test_regulatory_incident_matters.py` — per-matter conformance. For each of 01_transunion, 02_saferent, 03_realpage:
  - `run_replay()` produces the exact set of findings declared in `expected_findings.json` (TDD contract)
  - Pattern-coverage scoring matches the declared `patterns_engaged`
  - Primary-source citations resolve (URL-shaped or doc-shaped, no `<TBD>`)
- Update `tests/test_doc_staleness.py` to extend `PUBLIC_DOC_PATHS` with `docs/services/` and `examples/regulatory-incidents/`.
- New test: `tests/test_service_templates.py` — regex check that every `docs/services/*.md` carries all required sections (price, duration, deliverable, target buyer, what-you-get, methodology, what's-not-in-public, what's-not-in-scope, how-to-engage, pricing, disclaimer).

### D8 — Cross-linkage

README.md additions:
- "Real-world use cases" section: link to `examples/regulatory-incidents/`
- New "Engage" section (after Author, before Community): link to `docs/services/`
- New "Thesis + publications" section near the bottom: link to `THESIS.md` + `PUBLICATIONS.md`

FAILURE-MODES.md additions:
- Each row that maps to a named matter gets a "Motivating example" cross-link to `examples/regulatory-incidents/<NN>_<slug>/`

### D9 — Private memory entry (NOT in repo)

A `feedback`-type memory entry capturing the engagement-capture discipline:

```
For every paid engagement (Diagnostic, Audit, Retainer, Workshop, Cohort), capture:
- A confidential client memo (problem + recommendation + risk assessment)
- A de-identified risk pattern for the private corpus
- Lessons learned that inform framework v.next
- A referral pathway captured before engagement ends

Never publish the corpus. It IS the moat (Maister's PSF + Helmer's Process Power).
```

Saved to: `/Users/kunjarbhaduri/.claude/projects/-Users-kunjarbhaduri-Documents-110---Kunjar-s-Resume-Repos-cre-agent-audit/memory/feedback_engagement_capture_discipline.md` + indexed in `MEMORY.md`.

## Sequencing

Single PR landing on `main`. Internal commit checkpoints:

1. **Commit 1** — ADR-0014 + THESIS.md + PUBLICATIONS.md (the moat layer; positioning before code)
2. **Commit 2** — `src/cre_agent_audit/regulatory_replay/` framework module + tests
3. **Commit 3** — Three matters in `examples/regulatory-incidents/`
4. **Commit 4** — Seven service templates in `docs/services/`
5. **Commit 5** — Cross-linkage updates to README + FAILURE-MODES.md
6. **Commit 6** — Doc-staleness test extensions + service-template lint test
7. **Commit 7** — Private memory entry

Each commit ships independently green (pytest + ruff + mypy + ruff format). Each commit passes the 5-rule SoT-propagation discipline. Each commit message names every file + the chamber-pass score for the artifacts in that commit.

Push at the end. CI green confirmation before sign-off.

## Constraints applied

- CLAUDE.md voice rules (no banned terms across any committed surface)
- Banned-names referenced indirectly per the prior session pattern
- APEX framing as "private quantitative options research program with López de Prado as named advisor" (only applicable if referenced; this work does not reference)
- Colorado SB 189 (operative); SB 24-205 stayed (not operative)
- RealPage ongoing litigation, not settled
- Tamper-detecting-within-trust-boundary-by-default framing preserved
- Disclaimer line in every regulatory-mapping surface
- Zero-deps badge protected (`pyproject.toml` `[project.dependencies] = []` unchanged)
- mypy --strict + ruff check + ruff format clean
- New CLI entry point goes in `[project.scripts]`, not as a runtime dependency

## Out-of-scope (explicit)

- No tag creation
- No publish
- No actual customer engagements
- No commercial-software layer (Postgres adapter, SaaS dashboard, hosted attestation)
- No finserv-agent-audit parity work (separate session)
- No README rewrite beyond the new section additions
- No edits to existing ADRs or `FAILURE-MODES.md` beyond cross-link additions
- No CHANGELOG cut (this work targets [Unreleased] / v0.2.2)
- No changes to the v0.2.1 release artifact (immutable)

## What "10/10 from every chamber" means for this work

Per-artifact council pass:
- ADR-0014 + THESIS.md + PUBLICATIONS.md — graded on Branding, Counter-positioning, Cornered-resource visibility, Welsh/Clark cadence credibility
- Regulatory-replay framework — graded on Majors (production credibility), López de Prado (methods rigor), Andreessen (open-source GTM)
- Three matters — graded on Christensen (jobs-to-be-done clarity), López de Prado (citation rigor), Thiel (category-of-one positioning)
- Seven service templates — graded on Maister (PSF moats), Weiss (pricing-as-moat), Buffett (durable advantage)
- Cross-linkage — graded on Balfour (channel fit), Welsh (conversion path)
- Tests + lint — graded on Majors (production discipline), Larson (named increment)

Capped at 3 revision passes per artifact. If 10/10 unreachable after 3 passes on any artifact, surface the blocker and stop.

---

## Spec self-review (inline, per the brainstorming skill)

1. **Placeholder scan:** None. Every section names what ships with concrete file paths.
2. **Internal consistency:** The seven-commit sequencing aligns with the deliverables. The chamber slate maps to specific artifacts. The constraints are inherited from CLAUDE.md without modification.
3. **Scope check:** Single implementation plan. The work is decomposable but coherent — all pieces serve the same moat thesis.
4. **Ambiguity check:** The price points in service templates are ranges (e.g., $25K–50K for workshop) because they vary by client size. This is intentional, not ambiguous — the template explains the range.

No issues to fix inline.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
