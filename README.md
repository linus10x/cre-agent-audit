# cre-agent-audit

> Reference architecture for AI agent governance in commercial real estate operations.

> ## v0.2.0 — All 9 governance patterns landed
>
> - **ADR-0001 DEFCON state machine** · 5 states · per-state capability allowlist · transition logging
> - **ADR-0002 Sovereign Veto + bypass** · constraint-surface-specific · structured reason codes
> - **ADR-0003 Hash-chain Audit Ledger** · SHA-256 chaining · tamper-evident · correction entries
> - **ADR-0004 Autonomy Ladder™ A0→A4 promotion gate** · A2→A3 four-criterion gate · multi-failure reporting
> - **ADR-0005 Regulation Loader** · loads `config/compliance_rules.yaml` · pattern ↔ regulation lookups · schema-validated
> - **ADR-0006 Shadow Mode Rollout** · `ShadowRouter` · aggregate + cohort-specific divergence · 4-class promotion gate (7d / 30d / 60d / 90d with fair-housing zero-worse-direction rule)
> - **ADR-0007 Lease-Abstraction Provenance Chain** · 5 PROV-* veto codes · reviewer-signature SHA-256 sigil · `LeaseRepository`
> - **ADR-0008 Fair-Housing Pre-Flight Gate** · 5 ordered checks (FHA-PROXY · FHA-VOUCHER · FHA-SOI · FHA-CRIM · FHA-DISPARATE) · `DisparateImpactMonitor` with four-fifths rule · `BypassRegistry` auto-escalation
> - **ADR-0009 Tenant-PII Data-Residency Partitioning** · 5 RESIDENCY-* veto codes · GDPR Art. 6 LegalBasis taxonomy · vague-purpose detection
>
> **6-agent topology stubs** under `src/cre_agent_audit/agents/` (domain · strategy · risk · audit · orchestrator · monitor) — `AuditAgent` is functional and filters the ledger by decision_type / actor_id / sequence.
>
> **133 unit tests · 89% branch coverage · ruff and mypy strict-mode clean · all 3 examples run end-to-end with real governance behavior.**
>
> **v0.2.x patches landing post-Mon Jun 2:** per-clause-kind typed schema specializations · orchestrator wiring against the full compose order · NIST AI RMF + Treasury FS AI RMF 230-control mapping in `compliance_rules.yaml` · full FINOS AIR Governance Framework submission (18-file PR).

92% of CRE firms are piloting AI agents. 5% have hit program goals. The gap is governance.

Three settled cases anchor the discipline. **TransUnion** paid $15M to the FTC and the CFPB in October 2023 on a tenant-screening AI tool. **SafeRent** settled for $2.3M in November 2024 on an AI scoring model that treated housing-voucher status as a Fair Housing Act violation. **RealPage** agreed to binding DOJ restrictions in November 2025 on rent-pricing AI — data at least one year old, state-wide granularity only, no pricing discussions permitted at user meetings.

The **Colorado AI Act** (SB 189, signed March 14, 2026) sets a **January 1, 2027** compliance deadline for impact assessments and risk-management policies on consequential decisions, with tenant screening named explicitly. Other states are drafting against the Colorado template.

This repo is a **reference architecture, not a product**. Nine architectural decision records — six patterns inherited from [`finserv-agent-audit`](https://github.com/linus10x/finserv-agent-audit), three CRE-native. MIT-licensed. Fork it. Pressure-test it. Open an issue.

---

## What this is

A public, MIT-licensed reference implementation of nine governance patterns for AI agents operating inside commercial-real-estate workflows. Six patterns lift from the sibling [`finserv-agent-audit`](https://github.com/linus10x/finserv-agent-audit) repo — the discipline is the same across regulated industries even when the vertical vocabulary changes. Three patterns are CRE-native because they address failure modes that do not exist in financial services: lease-clause hallucination, fair-housing disparate-impact, and tenant-PII residency partitioning.

Any CRE CTO can fork this repo, read it in an afternoon, and pressure-test it against an internal AI program. Any PE operating partner can use it as a portfolio-wide governance baseline. Any vendor can prove (or disprove) their architecture against the nine patterns.

The umbrella is **Regulated-Operations AI Governance**, documented at [autonomy-ladder.io](https://autonomy-ladder.io). The discipline maturity scaffold is the **Autonomy Ladder™ A0 → A4**.

## The nine patterns

| ADR | Pattern | Source | Anchor regulation | NIST AI RMF | Treasury FS AI RMF |
|---|---|---|---|---|---|
| [0001](docs/adr/0001-defcon-state-machine.md) | DEFCON state machine | inherited ([finserv](https://github.com/linus10x/finserv-agent-audit/blob/main/docs/adr/0001-defcon-state-machine.md)) | Operational risk frameworks | GOVERN | TFRMF-LG-01..03 |
| [0002](docs/adr/0002-sovereign-veto.md) | Sovereign Veto | inherited ([finserv](https://github.com/linus10x/finserv-agent-audit/blob/main/docs/adr/0002-sovereign-veto.md)) | Three-lines-of-defense | GOVERN · MEASURE | TFRMF-DA-01..05 |
| [0003](docs/adr/0003-hash-chain-audit.md) | Hash-chain Audit Ledger | inherited ([finserv](https://github.com/linus10x/finserv-agent-audit/blob/main/docs/adr/0003-hash-chain-audit.md)) | SOC 2 CC7.2 · SEC 17a-4 | MEASURE · MANAGE | TFRMF-AT-01..09 |
| [0004](docs/adr/0004-autonomy-ladder-a0-a4.md) | Autonomy Ladder™ A0 → A4 | inherited ([finserv](https://github.com/linus10x/finserv-agent-audit/blob/main/docs/adr/0004-autonomy-ladder-a0-a4.md)) | EU AI Act Art. 14 · CO SB 26-189 | GOVERN · MAP | TFRMF-LG-08..12 |
| [0005](docs/adr/0005-eu-ai-act-mapping.md) | Regulation-to-pattern YAML mapping | inherited ([finserv](https://github.com/linus10x/finserv-agent-audit/blob/main/docs/adr/0005-eu-ai-act-mapping.md)) | self-referential | MAP | TFRMF-LG-04..05 |
| [0006](docs/adr/0006-shadow-mode-rollout.md) | Shadow Mode Rollout | inherited ([finserv](https://github.com/linus10x/finserv-agent-audit/blob/main/docs/adr/0006-shadow-mode-rollout.md)) | SR 26-2 (supersedes SR 11-7) | MAP · MANAGE | TFRMF-PR-01..07 |
| [0007](docs/adr/0007-lease-abstraction-provenance.md) | **Lease-Abstraction Provenance Chain** | **CRE-native** | SOC 2 CC7.2 · institutional lease-admin audit | MEASURE | TFRMF-DL-01..04 |
| [0008](docs/adr/0008-fair-housing-preflight-gate.md) | **Fair-Housing Pre-Flight Gate** | **CRE-native** | FHA · ECOA · CO SB 26-189 · HUD AI guidance · DOJ-RealPage | MAP · MEASURE · MANAGE | TFRMF-CF-01..09 |
| [0009](docs/adr/0009-tenant-pii-data-residency.md) | **Tenant-PII Data-Residency Partitioning** | **CRE-native** | GDPR Art. 6 · CCPA/CPRA · state tenant-data statutes | MANAGE | TFRMF-DR-01..07 |

**NIST + Treasury mapping** — every pattern carries at least one NIST AI RMF function (GOVERN / MAP / MEASURE / MANAGE) and one Treasury Financial Services AI RMF control range (Feb 19, 2026 — 230 control objectives total). The mappings live in `config/compliance_rules.yaml` and are queryable at runtime via `RegulationLoader.nist_functions_for(pattern)` and `RegulationLoader.treasury_controls_for(pattern)`. Treasury control IDs use lifecycle-phase prefixes (LG · DA · AT · PR · DL · CF · DR) — the canonical section numbering lives in the Treasury document.

Read [`ARCHITECTURE.md`](ARCHITECTURE.md) for how the patterns compose into a runtime.

## Quickstart

```bash
git clone https://github.com/linus10x/cre-agent-audit.git
cd cre-agent-audit
python -m venv .venv && source .venv/bin/activate
pip install -e .
pytest                                       # all governance modules unit-tested
python examples/01_lease_abstraction_provenance/run.py
python examples/02_tenant_screening_preflight/run.py
python examples/03_rent_optimization_sovereign_veto/run.py
```

Each example is a runnable narrative — the first writes a clause-level provenance object on a sample lease, the second routes a tenant-screening decision through the fair-housing pre-flight gate, the third demonstrates a sovereign veto firing on a rent-optimization recommendation.

## Repo layout

```
cre-agent-audit/
├── README.md
├── ARCHITECTURE.md
├── LICENSE                            # MIT
├── docs/
│   └── adr/                           # 9 architectural decision records
├── src/
│   ├── governance/                    # 9 pattern implementations
│   ├── agents/                        # 6 agent stubs (domain · strategy · risk · audit · orchestrator · monitor)
│   └── schemas/                       # 3 typed objects (lease_clause · screening_decision · pricing_recommendation)
├── examples/                          # 3 runnable demos
├── config/
│   └── compliance_rules.yaml          # pattern-to-regulation mapping
└── tests/                             # unit tests per governance module
```

## Who this is for

- **CRE-portco CTOs** running tenant-screening, lease-abstraction, or rent-optimization AI in production or in pilot
- **PE operating partners** writing checks into CRE platforms with AI inside, asking for a governance baseline
- **CRE-tech vendors** wanting to demonstrate that their architecture meets a recognized standard
- **GCs and chief risk officers** trying to translate "we use AI in tenant screening" into a defensible exception log

It is **not** for: small-portfolio operators who can keep a human in the loop on every decision (you do not need this scaffolding yet); consumer real-estate platforms (different regulatory surface); or pre-pilot AI exploration (build something first, then govern it).

## How to contribute

The repo is open because the failure modes a community catches are an order of magnitude more than the failure modes any single author catches alone.

- **Found a missing failure mode?** Open an issue with the regulatory anchor and a concrete (anonymized) example.
- **State-level fair-housing variance?** New York, California, Massachusetts, Minneapolis, Seattle each layer constraints — PRs welcome.
- **Multi-language provenance?** The lease-abstraction pattern assumes English. Multi-language extensions welcome.
- **Adversarial test corpus?** The single most-needed contribution. A community-built corpus of adversarial inputs across all nine patterns would harden v1 into v3.

PRs include passing tests and an ADR update (or a new ADR if the pattern is novel).

## License + trademark

**License:** [MIT](LICENSE) — no warranty, no liability, fork freely.

**Trademark:** *Autonomy Ladder™* is a common-law trademark of Kunjar Bhaduri, applied for USPTO registration in classes 9, 35, 41, 42 (filed via [`tmsearch.uspto.gov`](https://tmsearch.uspto.gov)). The framework is open for use under the MIT license; the name is reserved.

## Related

- [`finserv-agent-audit`](https://github.com/linus10x/finserv-agent-audit) — sibling repo · six inherited patterns for financial services
- [`finserv-agent-audit/docs/adr/private-capital/`](https://github.com/linus10x/finserv-agent-audit/tree/main/docs/adr/private-capital) — three Private Capital ADRs (buy-side adversarial gates · options-strategy governance · sovereign veto for autonomous allocators)
- [autonomy-ladder.io](https://autonomy-ladder.io) — A0 → A4 self-score for any AI program
- *AI Agents in Regulated Operations: One Discipline, Two Verticals* — LinkedIn umbrella article (link added on publish)
- *I built the CRE-Agent-Audit governance kit in one weekend. Three settled cases told me what to build.* — LinkedIn Article 2 (link added Mon Jun 2, 2026 8:00 AM CT)

---

*Authored by Kunjar Bhaduri · Dallas, TX · 2026.*
