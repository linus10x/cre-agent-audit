# cre-agent-audit

> Nine MIT-licensed governance patterns for AI in commercial real estate operations. Durable artifacts, not slideware.

[![CI](https://github.com/linus10x/cre-agent-audit/actions/workflows/test.yml/badge.svg)](https://github.com/linus10x/cre-agent-audit/actions/workflows/test.yml)
[![Coverage 89%](https://img.shields.io/badge/coverage-89%25-brightgreen)](https://github.com/linus10x/cre-agent-audit/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Zero Dependencies](https://img.shields.io/badge/runtime%20deps-0-brightgreen)](pyproject.toml)
[![v0.2.0](https://img.shields.io/badge/release-v0.2.0-blue)](https://github.com/linus10x/cre-agent-audit/releases/tag/v0.2.0)
[![v0.2.1.dev2 in flight](https://img.shields.io/badge/in--flight-v0.2.1.dev2-orange)](CHANGELOG.md)
[![Autonomy Ladder™ family](https://img.shields.io/badge/family-Autonomy%20Ladder%E2%84%A2-purple)](https://autonomy-ladder.io)
<!-- DOI badge added in v0.2.0 via Zenodo (Stage 12) -->

## The five anchors

- **$750M wealth-platform anchor account rescue** at a top-3 wealth-platform vendor (deal architecture + delivery)
- **12-day ransomware crisis** rebuilt on Azure in 50 days — SOC 2 Type 2 + ISO 27001 in the same window
- **$7M → $140M P&L growth** over an 18-year arc — JPMorgan Chase Partner of the Year 2007 · 2009 · 2010
- **Autonomy Ladder™ governance framework** — author of A0→A4 (this repo + [sibling for FSI](https://github.com/linus10x/finserv-agent-audit) + [autonomy-ladder.io](https://autonomy-ladder.io))
- **Operated through PE-acquisition-to-divestiture** at a regulated-industry technology platform — full hold-period operating cadence

These anchor the framing. The patterns below are the artifact.

---

## Lede

The U.S. Department of Justice filed *U.S. v. RealPage, Inc.* in August 2024 — DOJ plus eight state attorneys general, civil antitrust under Sherman § 1, alleging algorithmic rent-coordination across commercial real estate operating companies. The case is ongoing. The *Louis v. SafeRent Solutions, LLC* class settlement (No. 1:22-cv-10800, D. Mass., approximately $2.275M, November 2024) named tenant-screening AI that scored applicants below threshold with no documented reason; the settlement included a five-year score-use injunction on voucher-holder applicants. The Trans Union Rental Screening Solutions joint FTC/CFPB consent orders (October 2023, $15M) named systemic accuracy failures in its rental-screening reports under FCRA § 607(b).

Each matter named the same operator-side gap: no audit trail of the model decision. No human-in-loop documentation. No way to prove the system stayed bounded.

**cre-agent-audit** is the artifact stack that addresses that gap. Nine MIT-licensed governance patterns for AI-enabled CRE workflows — written for the operators who own tenant-screening, lease abstraction, pricing, underwriting, vendor-data flow, and lease-renewal decisions. Production Python. Nine architectural decision records (ADRs) with primary-source regulatory citations. Three runnable worked examples. Companion to [`finserv-agent-audit`](https://github.com/linus10x/finserv-agent-audit) for financial services.

The Colorado AI Act timeline is the next state-level regulatory checkpoint for CRE operators in the housing branch.

> **⚠ Notice.** This repository is a reference architecture, not legal, regulatory, audit, or fairness-testing advice. Regulatory characterizations are summaries; readers must consult qualified counsel for jurisdiction-specific compliance. No attorney-client relationship is formed by use of this repository. See [`DISCLAIMER.md`](DISCLAIMER.md).

---

## Table of contents

- [At a glance](#at-a-glance)
- [Why this exists](#why-this-exists)
- [Quick start](#quick-start)
- [Architecture overview](#architecture-overview)
- [Deployment economics](#deployment-economics)
- [Patterns included](#patterns-included)
- [Real-world use cases](#real-world-use-cases)
- [How it compares](#how-it-compares)
- [Who this is for](#who-this-is-for)
- [Repo layout](#repo-layout)
- [Related: the Autonomy Ladder™ family](#related-the-autonomy-ladder-family)
- [Governance artifacts (FINOS-format contributory)](#governance-artifacts-finos-format-contributory)
- [Vendor clauses](#vendor-clauses)
- [Roadmap](#roadmap)
- [Author](#author)
- [Community](#community)
- [Acknowledgements](#acknowledgements)
- [Citation](#citation)
- [Related work + intellectual lineage](#related-work--intellectual-lineage)
- [Failure modes](#failure-modes)
- [Limitations and what this stack does NOT do](#limitations-and-what-this-stack-does-not-do)
- [License + trademark](#license--trademark)

## At a glance

| | |
|---|---|
| Patterns | 9 core (ADR-0001 → ADR-0009) + 4 hardening (ADR-0010 retention; ADR-0011 vendor adapter; ADR-0012 persistence / timestamps / witness anchor; ADR-0013 MI Proxy) |
| Tests | 234 passing (was 142 at v0.2.0; +92 across PR 1+2 and PR 3) |
| Branch coverage | 87% (above 85% gate) |
| Runtime dependencies | 0 (stdlib only) |
| Python | 3.10, 3.11, 3.12 (CI matrix) |
| License | MIT |
| Type-checked | `mypy --strict` clean |
| Linted | `ruff` clean |
| Sibling | [`linus10x/finserv-agent-audit`](https://github.com/linus10x/finserv-agent-audit) (financial services) |

## Why this exists

Three regulatory matters in 24 months changed what *reasonable AI governance* means for commercial real estate operating companies. The plaintiffs and the consent orders named the same evidentiary gap — no documented decision trail, no human-in-loop record, no documented record of bounded operation. The patterns below are extracted from production work in regulated industries — financial services, wealth platforms, and now CRE — and they survive risk-committee scrutiny because they were designed for it.

Most operator AI surface is vendor-mediated. Tenant-screening models come from SafeRent, RentGrow, TransUnion SmartMove. Revenue-management models come from RealPage, AppFolio, Yardi Revenue IQ. Lease-abstraction models come from Leverton/MRI, V7 Lease, Reonomy. For those surfaces, the patterns in this repo translate to **procurement-clause power** as much as engineering rails — see [`docs/vendor-clauses/`](docs/vendor-clauses/) for the contractual companion to the code.

## Quick start

```bash
git clone https://github.com/linus10x/cre-agent-audit.git
cd cre-agent-audit
pip install -e ".[dev]"
make verify                                           # ruff + mypy + pytest + JSON-sync + wheel-build
python examples/02_tenant_screening_preflight/run.py  # demonstrates FHA-PROXY/VOUCHER/SOI/CRIM/DISPARATE
```

Sample output (abridged) — example 02:

```
→ PASS:  applicant_id=A-001  credit=720 income_x_rent=3.5  → ALLOW
→ PASS:  applicant_id=A-002  credit=680 income_x_rent=2.8  → REVIEW
→ VETO reason: FHA-VOUCHER  (voucher-status proxy detected)
→ VETO reason: FHA-CRIM     (blanket criminal-history exclusion attempted)
Total audit entries: 7 (every decision recorded)
Audit chain verified intact ✓
```

The example demonstrates the Fair-Housing Pre-Flight Gate (Pattern 8) firing, the Sovereign Veto (Pattern 2) rejecting, the hash-chained Audit Ledger (Pattern 3) recording every decision, and the human-review handoff. Cold-clone to verified-output target: under 60 seconds.

Full reproduction guide: [`docs/REPRODUCE.md`](docs/REPRODUCE.md).

## Architecture overview

Three subpackages under `src/cre_agent_audit/`:

- `governance/` — nine pattern primitives (DEFCON, Sovereign Veto, Audit Ledger, Autonomy Ladder, Regulation Loader, Shadow Router, Lease Provenance, Fair-Housing Preflight, Tenant PII Residency)
- `agents/` — six agent base classes (one functional, five v0.3 stubs)
- `schemas/` — typed decision objects (lease clause, screening decision)

Patterns compose into a runtime via the orchestrator (see [`ARCHITECTURE.md`](ARCHITECTURE.md)). Every decision routes through DEFCON state filter → domain pre-flight → Sovereign Veto → Audit Ledger. Veto'd decisions write to the ledger as fully as executed ones.

## Deployment economics

For an interim CTO or fractional CAIO scoping adoption:

| Item | Estimate |
|---|---|
| Engineering hours to integrate per pattern | 0.5–3 dev-days |
| Ongoing CPU / memory cost | Negligible (stdlib only; ledger size grows linearly with decision volume) |
| Exception-review headcount | 0.1–0.3 FTE compliance reviewer per A2+ workflow at portfolio scale |
| What it offsets | The runtime-gate + audit-primitive layer of a commercial AI-governance platform subscription (typical tier: $120K–$280K/yr) for the patterns this repo covers — does NOT replace policy authoring, vendor-risk workflow, or board-reporting modules those platforms also provide; complementary, not competitive (see Section 11). Also offsets ~40 hours/month manual GC review of decision logs. |
| Hardest integration item | Wiring Sovereign-Veto authority resolver to your IdP (Okta, Azure AD) — 4–6 months at most enterprises |
| Cold-clone-to-running examples | < 60 seconds |

The 90-day deployment cadence is in [`examples/FIRST_90_DAYS.md`](examples/FIRST_90_DAYS.md).

## Patterns included

| # | Pattern | File | Regulation anchor | Control doc |
|---|---|---|---|---|
| 1 | DEFCON State Machine | `src/cre_agent_audit/governance/defcon.py` | EU AI Act Art. 9, 15 · NIST AI RMF GOVERN | [CTRL-001](docs/controls/CTRL-001-defcon.md) |
| 2 | Sovereign Veto | `src/cre_agent_audit/governance/sovereign_veto.py` | EU AI Act Art. 14 · FHA · three-lines-of-defense | [CTRL-002](docs/controls/CTRL-002-sovereign-veto.md) |
| 3 | Hash-Chained Audit Ledger | `src/cre_agent_audit/governance/audit_chain.py` | EU AI Act Art. 12 · SOC 2 CC7.2 · SEC 17a-4 | [CTRL-003](docs/controls/CTRL-003-audit-ledger.md) |
| 4 | Autonomy Ladder™ A0→A4 | `src/cre_agent_audit/governance/autonomy_ladder.py` | EU AI Act Art. 14 · CO AI Act | [CTRL-004](docs/controls/CTRL-004-autonomy-ladder.md) |
| 5 | Regulation Loader (pattern↔reg map) | `src/cre_agent_audit/governance/regulation_loader.py` | self-referential (governs all others) | [CTRL-005](docs/controls/CTRL-005-regulation-loader.md) |
| 6 | Shadow-Mode Rollout | `src/cre_agent_audit/governance/shadow_mode.py` | SR 11-7 (model risk) · EU AI Act Art. 15 | [CTRL-006](docs/controls/CTRL-006-shadow-mode.md) |
| 7 | Lease-Abstraction Provenance | `src/cre_agent_audit/governance/lease_provenance.py` | Litigation discovery defensibility · SOC 2 CC7.2 | [CTRL-007](docs/controls/CTRL-007-lease-provenance.md) |
| 8 | Fair-Housing Pre-Flight Gate | `src/cre_agent_audit/governance/fair_housing_preflight.py` | Fair Housing Act § 3604 · ICP v Texas (576 U.S. 519) · ECOA · CO AI Act | [CTRL-008](docs/controls/CTRL-008-fair-housing-preflight.md) |
| 9 | Tenant PII Data Residency | `src/cre_agent_audit/governance/tenant_pii_residency.py` | GDPR Art. 6 · CCPA/CPRA · state tenant-data statutes | [CTRL-009](docs/controls/CTRL-009-tenant-pii-residency.md) |

Two ADRs added in v0.2.0 from adversarial-review fold-in (design + policy layer):

- [ADR-0010 — Audit-Chain Retention, Privilege & Discovery Posture](docs/adr/0010-audit-chain-retention-privilege-discovery.md) — layered on top of Patterns 2, 3, 7, 8, 9
- [ADR-0011 — Vendor-Output Adapter Pattern](docs/adr/0011-vendor-output-adapter-pattern.md) — design baseline; concrete `VendorScoreGate` implementation lands in v0.2.1.dev2

Two more ADRs added in v0.2.1 (in flight, on `main`):

- [ADR-0012 — Persistence, Trusted Timestamps, External Witness Anchoring](docs/adr/0012-persistence-witness-timestamp-pattern.md) — three Protocol seams: `LedgerStore` (stdlib `InMemory` / `Sqlite` / `Jsonl` defaults), `TimestampSource` (`LocalClock` / `RFC3161`), `WitnessRegister` (`Rekor` / `OpenTimestamps`).
- [ADR-0013 — MI Proxy (Module Integrity verifier chain-of-custody)](docs/adr/0013-mi-proxy-module-integrity.md) — out-of-band attestation of the verifier itself; `LocalMIProxy` HMAC default backend; `AuditLedger.verify_chain(mi_proxy=...)` is the opt-in fail-closed hook.

For the four-framework mapping (NIST AI RMF × ISO/IEC 42001 × COSO ICAIR × Big-4 taxonomy) see [`docs/MAPPING-MATRICES.md`](docs/MAPPING-MATRICES.md).

## Real-world use cases

**1. Tenant-screening fair-housing audit (multifamily).** The SafeRent matter named tenant-screening AI that scored voucher-holder applicants below threshold with no documented reason. The Fair-Housing Pre-Flight Gate (Pattern 8) flags protected-class proxy features against a configurable blocklist before model evaluation; the Audit Ledger (Pattern 3) records every decision with cohort statistics. The artifact stack materially reduces the class of failure modes the SafeRent matter exposed — it does not, standing alone, establish FHA compliance.

**2. Lease-abstraction discovery defense (office + industrial).** When a lease term is contested in litigation, courts ask: how was that clause extracted, what was the model's confidence, and who validated it? Lease-Abstraction Provenance (Pattern 7) tags every clause with source-document hash, OCR confidence, and extraction confidence. Discovery becomes a forensic exercise instead of a credibility one — *if* the lease-abstraction pipeline (typically a third-party vendor) exposes the clause-level provenance object. For vendor-shipped outputs that do not expose provenance, see [`docs/vendor-clauses/abstraction.md`](docs/vendor-clauses/abstraction.md) for the contractual SLA template that obligates provenance disclosure.

**3. Pricing-model good-faith documentation (multifamily + industrial).** The *U.S. v. RealPage* matter is ongoing civil antitrust litigation alleging algorithmic rent-coordination. Pattern 3 (Audit Ledger) + Pattern 4 (Autonomy Ladder A2 with sampled per-cycle audit) produce **process evidence relevant to good-faith defenses under § 1 rule-of-reason analysis**. They **do not cure per se exposure from data-pooling** — antitrust counsel must independently assess data-input topology; software governance does not substitute for input-side antitrust review.

**4. AI-mediated resident communication (chatbots, leasing agents).** Most large multifamily operators run vendor chatbots (EliseAI, Hyly, Funnel Leasing) on resident communication. These surfaces touch TCPA, Reg-Z disclosure, and fair-housing-steering risk simultaneously. Pattern 8's protected-surface list already names `tenant_communication_personalization`; the Audit Ledger captures every interaction; the Sovereign Veto fires on protected-class-adjacent topics. ADR-0011 (Vendor-Output Adapter, design) covers the vendor-mediated case.

## How it compares

| | cre-agent-audit | finserv-agent-audit | NIST AI RMF Playbook | OWASP LLM Top 10 |
|---|---|---|---|---|
| Target | CRE operating cos | FSI regulated systems | Universal | Security awareness |
| Form | MIT reference architecture | MIT reference architecture | Government playbook | Threat list |
| Runnable patterns | ✅ 9 patterns + 142 tests | ✅ 6 patterns | Conceptual guidance | Conceptual guidance |
| Kill switch | ✅ Sovereign Veto | ✅ | ❌ | ❌ |
| Audit trail | ✅ Hash-chained | ✅ Hash-chained | Recommended | ❌ |
| Decision-class autonomy | ✅ A0→A4 | ✅ A0→A4 | Recommended | ❌ |
| Regulation mapping | ✅ EU AI Act · FHA · CO AI Act · NIST + Treasury | ✅ EU AI Act · MiFID II · SEC · NIST + Treasury | ✅ NIST only | ❌ |
| Zero runtime deps | ✅ stdlib only | ✅ stdlib only | N/A | N/A |
| Python typed (mypy --strict) | ✅ | ✅ | N/A | N/A |

**Commercial AI-governance platforms** — Credo AI, Holistic AI, Fairly AI, Monitaur, IBM watsonx.governance, Microsoft Purview AI Hub — are a different category. They are managed services with subscriptions in the $50K–$300K/yr range, opinionated workflow tooling, vendor-managed control evidence storage, and ongoing policy-as-code maintained by the vendor. cre-agent-audit is a **reference architecture you fork into your own stack**. It is complementary, not competitive: many adopters use a commercial platform for policy + reporting and cre-agent-audit's patterns for the runtime gates and audit primitives the platform integrates with.

## Who this is for

- **CRE operating companies** (multifamily, office, industrial) running AI in tenant-screening, leasing, pricing, underwriting, or vendor-data workflows
- **Risk and compliance leaders** at CRE operating companies preparing for the next state regulatory checkpoint in the AI consequential-decision branch
- **PE operating partners** with CRE portfolio exposure scoping AI-governance posture across portfolio companies — see [`docs/PE_DUE_DILIGENCE.md`](docs/PE_DUE_DILIGENCE.md)
- **Audit firms** mapping AI-governance controls into assurance frameworks for CRE clients — see [`docs/controls/`](docs/controls/) + [`docs/MAPPING-MATRICES.md`](docs/MAPPING-MATRICES.md)
- **CTOs and Chief AI Officers** at CRE operating companies establishing governance frameworks before regulators ask for them

## Repo layout

```
cre-agent-audit/
├── README.md · ARCHITECTURE.md · LICENSE · DISCLAIMER.md
├── CITATION.cff · CODE_OF_CONDUCT.md · CONTRIBUTING.md · SECURITY.md · ROADMAP.md
├── Makefile                              # `make verify` runs full gate
├── pyproject.toml                        # zero runtime deps
├── docs/
│   ├── adr/                              # 11 architectural decision records (0001-0011)
│   ├── controls/                         # 9 per-pattern Control Description Tables (CTRL-001..009)
│   ├── vendor-clauses/                   # drop-in contract addenda for vendor-mediated AI
│   ├── MAPPING-MATRICES.md               # NIST × ISO 42001 × COSO ICAIR × Big-4 taxonomy
│   ├── LIMITATIONS.md                    # what this stack does NOT do
│   ├── PRIOR-ART.md                      # intellectual lineage + academic citations
│   ├── PE_DUE_DILIGENCE.md               # 10-question checklist for PE operating partners
│   └── REPRODUCE.md                      # cold-clone to all-green in 5 commands
├── src/cre_agent_audit/                  # src-layout namespace package, py.typed
│   ├── governance/                       # 9 pattern implementations
│   ├── agents/                           # 6 agent classes (1 functional + 5 v0.3 stubs)
│   └── schemas/                          # typed decision objects
├── examples/                             # 3 runnable demos + FIRST_90_DAYS.md
├── config/
│   ├── compliance_rules.yaml             # author-time source of truth
│   └── compliance_rules.json             # runtime artifact (generated; CI-verified in sync)
├── governance-artifacts/                 # 3 FINOS-format contributory control drafts
├── scripts/build_compliance_json.py      # author-time YAML → JSON converter
└── tests/                                # 142 unit tests · 89% branch coverage
```

## Related: the Autonomy Ladder™ family

`cre-agent-audit` is the commercial-real-estate half of an MIT-licensed pattern family for governing AI in regulated industries. The financial-services half is here:

**[`linus10x/finserv-agent-audit`](https://github.com/linus10x/finserv-agent-audit)** — Six governance patterns for AI in regulated financial services. Anchored to SR 11-7 (model risk), MiFID II, SEC record-retention, NIST AI RMF, and Treasury FS AI RMF. Already at v1.0.0.

| Pattern | finserv-agent-audit | cre-agent-audit |
|---|---|---|
| DEFCON state machine | ✅ | ✅ |
| Sovereign Veto | ✅ | ✅ |
| Hash-chained Audit Ledger | ✅ | ✅ |
| Autonomy Ladder A0→A4 | ✅ | ✅ |
| Regulation Mapping | ✅ MiFID II · SEC · SR 11-7 | ✅ FHA · CO AI Act · EU AI Act |
| Shadow-Mode Rollout | ✅ | ✅ |
| Lease-Abstraction Provenance | — | ✅ CRE-specific |
| Fair-Housing Pre-Flight Gate | — | ✅ CRE-specific |
| Tenant PII Data Residency | — | ✅ CRE-specific |

Both repos: MIT, zero runtime dependencies, primary-source regulatory citations, `mypy --strict` clean, ≥85% branch coverage.

The umbrella discipline — **Regulated-Operations AI Governance** — is documented at [autonomy-ladder.io](https://autonomy-ladder.io). One framework, two named verticals, one author.

## Governance artifacts (FINOS-format contributory)

The [FINOS AI Risk Initiative](https://air.finos.org/) is the financial-services industry's open-source AI risk-control catalog. Three control drafts in [`governance-artifacts/`](governance-artifacts/) are written in the FINOS AIR artifact format and released here under MIT — fork them into your own control library, cite them in your AI risk register, adapt them to your jurisdictions. Each draft maps to a pattern in this repo.

**Important.** These three drafts have **not been reviewed, endorsed, or accepted by FINOS or the AIR Working Group** as of v0.2.0. They are released independently. The full 19-artifact submission package (with 16 additional risk and mitigation files in author-draft form) is under separate working-group-bound development on a private branch and is not in this folder by design.

## Vendor clauses

Most CRE operators do not run their own tenant-screening, lease-abstraction, or pricing models. They buy from SafeRent, Yardi/RentCafe, RentGrow, Leverton/MRI, V7, RealPage, AppFolio, Yardi Revenue IQ. For vendor-mediated AI surfaces, [`docs/vendor-clauses/`](docs/vendor-clauses/) holds drop-in contract addenda mapping the patterns to procurement-clause language:

- [`screening.md`](docs/vendor-clauses/screening.md) — DPA + model-risk addendum + four-fifths-rule reporting SLA
- [`abstraction.md`](docs/vendor-clauses/abstraction.md) — lease-vendor SLA + clause-level provenance-disclosure requirement
- [`pricing.md`](docs/vendor-clauses/pricing.md) — independent-decision contract clause + data-input-topology disclosure

## Roadmap

See [`ROADMAP.md`](ROADMAP.md). Highlights for v0.3: pluggable persistence backend for the audit ledger, RFC 3161 trusted-timestamp integration, OpenTimestamps / Sigstore Rekor witness-anchor reference implementation, VendorScoreGate concrete implementation, MI-threshold learned-proxy detection in the Fair-Housing gate, five-state regulatory-mapping community contributions (TX/NY/CA/WA/FL).

## Author

**Kunjar Bhaduri** — 25-year financial-services and technology executive. Rescued a $750M multi-year wealth-management platform anchor account at a top-3 wealth-platform vendor. Rebuilt production infrastructure on Azure during a 12-day ransomware attack with no DR available — SOC 2 Type 2 and ISO 27001 cleared in the same 50-day window. Three-time JPMorgan Chase Partner of the Year (2007 · 2009 · 2010). Operated through a PE-acquisition-to-divestiture arc at a regulated-industry technology platform.

These patterns translate financial-services AI-governance discipline to CRE failure modes documented in the three named regulatory matters. The cross-domain pattern (FSI governance → CRE adoption) is intentional; CRE operators face the same audit-trail, human-in-loop, and proof-of-bounded-operation expectations that FSI institutions resolved over the last decade.

[LinkedIn](https://linkedin.com/in/kunjarbhaduri) · [NTCI Portfolio](https://github.com/linus10x)

## Community

- **Issues:** https://github.com/linus10x/cre-agent-audit/issues
- **Discussions:** https://github.com/linus10x/cre-agent-audit/discussions
- **Good first issues:** https://github.com/linus10x/cre-agent-audit/labels/good%20first%20issue — five state regulatory-mapping issues are open; community PRs welcome with primary-source citations
- **Sponsor:** https://github.com/sponsors/linus10x

## Acknowledgements

- [NIST AI Risk Management Framework 1.0](https://www.nist.gov/itl/ai-risk-management-framework) — function categories used in every pattern mapping
- [Treasury Financial Services AI Risk Management Framework](https://home.treasury.gov/) — 230 control objectives, Feb 2026
- [FINOS AI Risk Initiative](https://air.finos.org/) — artifact format the `governance-artifacts/` folder targets
- [Marcos López de Prado](https://www.quantresearch.org/) — named advisor on adjacent work on a private quantitative options research program; methodological discipline applied here
- [Solon Barocas, Moritz Hardt, Arvind Narayanan](https://fairmlbook.org/) — *Fairness and Machine Learning* foundational text
- Andrew Selbst, Danah Boyd, Sorelle Friedler, Suresh Venkatasubramanian, Janet Vertesi — *Fairness and Abstraction in Sociotechnical Systems* (FAT* 2019)
- Margaret Mitchell, Simone Wu, Andrew Zaldivar et al. — *Model Cards for Model Reporting* (FAT* 2019)
- Timnit Gebru, Jamie Morgenstern, Briana Vecchione et al. — *Datasheets for Datasets* (CACM 2021)
- Inioluwa Deborah Raji et al. — *Closing the AI Accountability Gap: Defining an End-to-End Framework for Internal Algorithmic Auditing* (FAT* 2020)

## Citation

If you cite this work in research or in adoption-decision memos, use the metadata in [`CITATION.cff`](CITATION.cff). Zenodo DOI is minted at every tagged release; the badge above will resolve.

```bibtex
@software{bhaduri_cre_agent_audit_2026,
  author       = {Bhaduri, Kunjar},
  title        = {{cre-agent-audit: Governance Patterns for AI in
                   Commercial Real Estate Operations}},
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v0.2.0},
  url          = {https://github.com/linus10x/cre-agent-audit}
}
```

## Related work + intellectual lineage

These patterns build on prior work. The Autonomy Ladder A0→A4 ladder structure is intentionally isomorphic to existing staged-autonomy frameworks (SAE J3016 driving-automation taxonomy; OECD AI Principles staged-oversight language; NIST AI RMF MANAGE 2.3 maturity scaffolding; Shavit et al. 2023 *Practices for Governing Agentic AI Systems*; Anderljung et al. 2023 *Frontier AI Regulation*). What this work contributes is the **CRE-vertical mapping of autonomy tier to specific patterns and to specific regulatory matters** — the ladder is borrowed scaffolding, the per-tier-per-pattern + per-tier-per-matter mapping is the novel contribution. Doctrinal foundation for the Fair-Housing Pre-Flight Gate is *Texas Dept. of Housing v. Inclusive Communities Project*, 576 U.S. 519 (2015), which constitutionalized disparate-impact under the FHA. Full lineage in [`docs/PRIOR-ART.md`](docs/PRIOR-ART.md).

## Failure modes

[`FAILURE-MODES.md`](FAILURE-MODES.md) is the repo-root matrix of 8 adversarial / partition / corruption failure-mode classes: storage drift, sequence gap / split-brain, adversarial replay in-trust-boundary, timestamp tampering, witness disagreement, backend permission revocation, **verifier compromise** (the Module Integrity Proxy in ADR-0013), and **vendor AI scoring drift** (the VendorScoreGate). Each row names the detection mechanism (resolved to a real callable in the codebase or marked `NOT YET IMPLEMENTED · tracking: ADR-XXXX`) and the recovery action. A companion test ([`tests/test_failure_modes_matrix.py`](tests/test_failure_modes_matrix.py)) enforces doc/code parity — the build fails on drift.

The audit chain is **tamper-detecting within its trust boundary by default**. Tamper-*evidence* against an attacker who controls the ledger host requires the external witness pattern shipped in v0.2.1 (RFC 3161 trusted timestamps via `TimestampSource` + Sigstore Rekor / OpenTimestamps via `WitnessRegister`, per [`docs/adr/0012-persistence-witness-timestamp-pattern.md`](docs/adr/0012-persistence-witness-timestamp-pattern.md)). Tamper-detection of the *verifier itself* requires the MI Proxy hook shipped in v0.2.1.dev2 ([`docs/adr/0013-mi-proxy-module-integrity.md`](docs/adr/0013-mi-proxy-module-integrity.md)) — out-of-band SHA-256 + HMAC attestation by default, opt-in SLSA / in-toto / Sigstore cosign.

## Limitations and what this stack does NOT do

- **Lexical-only proxy detection.** The Fair-Housing Pre-Flight Gate (Pattern 8) checks for named-feature proxies against a configurable blocklist. It does NOT detect learned proxies in embedding space, behavioral-signal proxies (browser fingerprints, language patterns), or geospatial-granularity proxies. The MI-threshold learned-proxy detector (mutual-information based, ADR-0008 update) is a tracked v0.2.1 deliverable — not yet landed.
- **Internally-consistent ledger by default; adversarial tamper-evidence requires the witness pattern.** The hash-chained Audit Ledger (Pattern 3) detects modification by an honest holder of the chain head. Adversarial integrity against an attacker with full ledger-host write access requires anchoring the chain head to an external witness register. v0.2.1 ships `RekorWitness` (Sigstore), `OpenTimestampsWitness`, and the `anchor_to_witness()` helper that binds the receipt back into the chain (ADR-0012 Seam 3). Scheduling the anchor is the deployer's responsibility.
- **Four-fifths-rule monitor only.** The disparate-impact check is the standard four-fifths-rule selection-rate comparison. It does not engage the fairness-metric pluralism / impossibility-result literature (Kleinberg/Mullainathan/Raghavan 2016; Chouldechova 2017) — adopters owning a regulator-facing fairness defense should choose their fairness metric in consultation with counsel and document the choice.
- **Vendor-mediated AI scoring captured via `VendorScoreGate` in v0.2.1.dev2.** The Protocol + `InMemoryVendorScoreGate` default backend ship now (ADR-0011 update; FAILURE-MODES.md Row 8); score-drift on `(vendor_id, input_hash, model_version)` surfaces as a flagged chain entry and, by default, raises to halt the pipeline. Vendor-clauses remain the procurement-side companion.
- **Five state regulatory mappings ship in v0.2.0.** TX, NY, CA, WA, FL state mappings tracked as community-contribution good-first-issues — primary-source citation required per PR.
- **Engages the operator's deployment, not the model's training.** Selbst et al. 2019 *Fairness and Abstraction in Sociotechnical Systems* — fairness is sociotechnical, not technical. This stack governs how AI is *deployed* by an operator. Training-time controls are out of scope.
- **Pre-revenue research artifact; no production-deployment warranties.** Adopters own validation. See [`DISCLAIMER.md`](DISCLAIMER.md) and [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) for the full statement.

## License + trademark

**License:** [MIT](LICENSE) — fork freely; no warranty.

**Trademark:** *Autonomy Ladder™* is a common-law trademark of Kunjar Bhaduri. USPTO registration is planned in classes 9, 35, 41, 42. The framework is open for use under the MIT license; the name is reserved during the registration period.

---

*Authored by Kunjar Bhaduri · Dallas, TX · 2026.*
