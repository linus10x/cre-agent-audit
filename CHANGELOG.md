# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1-wip] — 2026-05-22 — Tier-B autonomous shipment (Workbook v2 · Case Study · Article 6 · FINOS AIR submission scaffold · NIST + Treasury mapping)

### Added (Tier B pass)
- `config/compliance_rules.yaml` extended to v1.1.0 with NIST AI RMF function overlay + Treasury FS AI RMF 230-control mapping on every regulation entry across all 9 patterns
- `src/cre_agent_audit/governance/regulation_loader.py` extended with `nist_functions_for(pattern)` + `treasury_controls_for(pattern)` queries; `RegulationCitation` dataclass extended with `nist_ai_rmf_function` + `treasury_fs_ai_rmf_controls` fields (backwards-compatible defaults)
- `tests/test_regulation_loader.py` extended with `TestNistAndTreasuryMapping` class — 7 new tests covering citation fields · distinct-set queries · backwards-compatible loading of v1.0 YAML
- `README.md` mapping table extended with NIST function + Treasury TFRMF-* control range columns per pattern row; cross-links to sibling `finserv-agent-audit` ADRs added on every inherited-pattern row
- `CONTRIBUTING.md` — table-stakes OSS contributor guide (regulatory-coverage PR process · adversarial test case workflow · TDD discipline · ADR additions · PR checklist · issue triage labels)
- `SECURITY.md` — GitHub Security Advisory channel · 72-hour acknowledgment SLA · 90-day disclosure window · severity rubric (Critical / High / Medium / Low) · scope and out-of-scope
- `finos-air-submission/` directory with the full 18-file submission package — 9 risk markdown files across `risks/operational/`, `risks/regulatory-and-compliance/`, `risks/security/` + 9 mitigation files crediting Autonomy Ladder™ as the named pattern source. 3 fully drafted (AIR-RC-004 Sovereign Veto · AIR-RC-007 Fair Housing · AIR-MIT-RC-VETO-01); 15 carry council-approved structured stubs ready for Week-7 Kunjar fill-in.

### Verified
- pytest: **140 / 140 passing** (up from 133; the 7 new TestNistAndTreasuryMapping tests load clean)
- pytest-cov: **89% branch coverage** (above 85% target); regulation_loader.py at 98%
- ruff: **clean** across src/ + tests/ + examples/
- mypy: **clean** in strict mode across 22 source files
- All 3 example scripts continue to exit 0

### Companion artifacts shipped outside the repo
- `Memos/Workbook_First90Days_PE_CRE_CTO_v2.md` — full 28-page workbook draft (council 9.78/10 · 5/5 affirm · WeasyPrint render pending)
- `Content/CRE-Track/_deliverables/Case_Study_Regulated_Operations_AI_v1.md` — anonymized 8-page case study source (Stage 1 content 9.78/10 + Stage 2 re-ID 10.0/10 universal · APPROVED for publish)
- `Content/CRE-Track/Article_Phase6_Case_Study_Anchor_v1.md` — ~1,150-word Article 6 RECAST (council 9.78/10 · 5/5 affirm)
- `Memos/Private_Capital_ADR_Merge_Prep_2026-05-22.md` — bash sequence + PR body for the 3 Private Capital ADRs upstream merge

## [0.2.0] — 2026-05-22 — Python source layer COMPLETE (9 of 9 governance patterns + 6 agent stubs)

### Added (third pass — 2026-05-22 PM)
- `src/cre_agent_audit/governance/shadow_mode.py` — `ShadowRouter` per ADR-0006 with aggregate divergence rate · veto-direction classification (SHADOW_MORE_CONSERVATIVE / SHADOW_MORE_AGGRESSIVE / EQUIVALENT) · cohort-specific divergence · 4-class promotion-gate matrix (INFORMATIONAL 7d · MATERIAL_LEASE 30d · FAIR_HOUSING 60d + zero-worse-direction-per-cohort · RENT_OPTIMIZATION 90d)
- `src/cre_agent_audit/governance/regulation_loader.py` — `RegulationLoader` per ADR-0005 reading `config/compliance_rules.yaml` with `RegulationCitation` typed lookups + reverse lookup (patterns satisfying a regulation) + schema validation (`InvalidComplianceRulesError`)
- `src/cre_agent_audit/governance/tenant_pii_partition.py` — `TenantPIIResidencyCheck` per ADR-0009 with all 5 RESIDENCY-* veto codes (CROSS-JURISDICTION-UNTAGGED · CONSENT-MISSING · LIA-MISSING · STATUTE-MISSING · PURPOSE-VAGUE) + `CrossJurisdictionRequest` typed object + `LegalBasis` enum (GDPR Art. 6 taxonomy)
- `src/cre_agent_audit/agents/` — 6 agent stubs per ARCHITECTURE.md topology: `DomainIntelligenceAgent` · `StrategyAgent` · `RiskAgent` · `AuditAgent` (functional — filters ledger by decision_type / actor_id / sequence) · `OrchestratorAgent` · `MonitorAgent`. Shared `Agent[InputT, OutputT]` ABC in `agents/base.py`.
- `tests/test_shadow_mode.py` — 16 unit tests
- `tests/test_regulation_loader.py` — 12 unit tests (including malformed-YAML validation)
- `tests/test_tenant_pii_partition.py` — 15 unit tests
- `tests/test_agents.py` — 5 smoke tests for the agent topology + AuditAgent filter behavior

### Verified (third pass)
- pytest: **133 / 133 passing** (up from 85)
- pytest-cov: **89% branch coverage** (above 85% target)
- ruff: **clean** across 22 source files
- mypy: **clean** in strict mode across 22 source files
- All 3 example scripts exit 0

### Status — 9 of 9 governance patterns landed
- ADR-0001 DEFCON state machine ✓
- ADR-0002 Sovereign Veto + bypass ✓
- ADR-0003 Hash-chain Audit Ledger ✓
- ADR-0004 Autonomy Ladder™ A0→A4 + promotion gate ✓
- ADR-0005 Regulation Loader (compliance_rules.yaml) ✓
- ADR-0006 Shadow Mode Rollout + promotion-gate matrix ✓
- ADR-0007 Lease-Abstraction Provenance Chain ✓
- ADR-0008 Fair-Housing Pre-Flight Gate (5 ordered checks + DisparateImpactMonitor + BypassRegistry) ✓
- ADR-0009 Tenant-PII Data-Residency Partitioning ✓

### Pending for v0.2.x patches (post-Mon Jun 2 public ship)
- Per-clause-kind typed schemas (`ClauseSchema` slot specializations for rent_amount · escalation_rate · break_date · co_tenancy · options_to_renew · jurisdiction · outgoings)
- Agent stub production realizations (orchestrator wiring against the full compose order)
- compliance_rules.yaml extension with NIST AI RMF function mapping + Treasury FS AI RMF 230-control mapping per Gap-Finding G-58
- Full FINOS AIR submission (18 markdown files per `Memos/FINOS_AIR_Submission_Outline_v0_2026-05-22.md`) — Week 8 ship

## [0.2.0-wip] — 2026-05-22 — Python source layer (in progress · 6 of 10 modules landed)

### Added (second pass — 2026-05-22 PM)
- `src/cre_agent_audit/schemas/lease_clause.py` — typed `Provenance`, `ReviewerSignature`, `BoundingBox`, `ExtractedClause`, `ClauseCriticality` enum (3 tiers) per ADR-0007
- `src/cre_agent_audit/schemas/screening_decision.py` — typed `ScreeningDecision`, `FairHousingException`, `JurisdictionRules`, `ProtectedSurface` + `Decision` + `AuthorityLevel` enums, default SOI-protected jurisdiction set per ADR-0008
- `src/cre_agent_audit/governance/lease_provenance.py` — `LeaseProvenanceCheck` per ADR-0007 with all 5 veto codes (PROV-INCOMPLETE-MATERIAL · PROV-INCOMPLETE-SIGNIFICANT · PROV-LOW-CONFIDENCE-MATERIAL · PROV-HASH-MISMATCH · PROV-STALE-MODEL) + `LeaseRepository` + `compute_reviewer_sigil` SHA-256 binding
- `src/cre_agent_audit/governance/fair_housing_gate.py` — `FairHousingPreflightGate` per ADR-0008 with all 5 ordered checks (FHA-PROXY · FHA-VOUCHER · FHA-SOI · FHA-CRIM · FHA-DISPARATE) + `DisparateImpactMonitor` (four-fifths-rule) + `BypassRegistry` (3-bypasses-same-owner-90d → GC, 5-bypasses-same-reason-90d → DEFCON-4)
- `tests/test_lease_provenance.py` — 13 unit tests
- `tests/test_fair_housing_gate.py` — 17 unit tests
- Full realization of `examples/01_lease_abstraction_provenance/run.py` and `examples/02_tenant_screening_preflight/run.py` against the live `LeaseProvenanceCheck` and `FairHousingPreflightGate` implementations (replaced stubs from the morning shipment)

### Verified (second pass)
- pytest: 85 / 85 passing (up from 55)
- pytest-cov: 87% branch coverage (above 85% target)
- ruff: clean
- mypy: clean (strict mode, 12 source files)
- All 3 example scripts exit 0 with real governance behavior demonstrated

## [0.2.0-wip] — 2026-05-22 — Python source layer (in progress · 4 of 10 modules)

### Added
- `pyproject.toml` with `[project.optional-dependencies] dev`, ruff + mypy + pytest-cov configuration; supports `pip install -e .` and `pip install -e ".[dev]"`
- `src/cre_agent_audit/` namespaced package with `py.typed` marker for downstream type-checkers
- `src/cre_agent_audit/governance/defcon.py` — DEFCON state machine per ADR-0001 (5 states · per-state capability allowlist · transition logging · validation)
- `src/cre_agent_audit/governance/audit_chain.py` — hash-chain audit ledger per ADR-0003 (SHA-256 chaining · canonical serialization · tamper detection · correction entries · genesis sentinel)
- `src/cre_agent_audit/governance/sovereign_veto.py` — sovereign-veto dispatch per ADR-0002 (constraint-surface registration · structured `VetoResult` · `SovereignBypass` with named owner + regulatory basis · audit ledger integration)
- `src/cre_agent_audit/governance/autonomy_ladder.py` — Autonomy Ladder™ A0→A4 per ADR-0004 (5 tiers · A2→A3 promotion gate evaluator · multi-failure reporting · `PromotionGateNotMet` raise path)
- `tests/test_defcon.py` — 15 unit tests
- `tests/test_audit_chain.py` — 13 unit tests
- `tests/test_sovereign_veto.py` — 13 unit tests
- `tests/test_autonomy_ladder.py` — 14 unit tests
- `examples/01_lease_abstraction_provenance/run.py` — stub demonstration of boundary gates around a lease-abstraction action (placeholder pending ADR-0007 implementation)
- `examples/02_tenant_screening_preflight/run.py` — partial demonstration including the SafeRent voucher veto (placeholder pending full ADR-0008 5-check gate)
- `examples/03_rent_optimization_sovereign_veto/run.py` — fully realized DOJ-RealPage antitrust check with state-granularity + data-age + coordination veto codes

### Verified
- pytest: 55 / 55 passing
- pytest-cov: 91% branch coverage on src/
- ruff: clean
- mypy: clean (strict mode)

### Pending for v0.2.x (target full ship: Mon June 2, 2026)
- `src/cre_agent_audit/governance/shadow_mode.py` (ADR-0006)
- `src/cre_agent_audit/governance/regulation_loader.py` (ADR-0005 — load `compliance_rules.yaml` + Treasury FS AI RMF 230-control mapping per v3.1 Amendment)
- `src/cre_agent_audit/governance/lease_provenance.py` (ADR-0007)
- `src/cre_agent_audit/governance/fair_housing_gate.py` (ADR-0008 — heaviest module, 5 ordered checks + auto-escalation + disparate-impact monitor)
- `src/cre_agent_audit/governance/tenant_pii_partition.py` (ADR-0009)
- 6 agent stubs under `src/cre_agent_audit/agents/`
- 3 typed schemas under `src/cre_agent_audit/schemas/` (lease_clause · screening_decision · pricing_recommendation)
- Full realization of examples 01 + 02

## [Unreleased]

## [0.1.0] — 2026-05-22 — Architectural backbone

### Added
- `README.md` — repository overview, three settled cases anchor (TransUnion · SafeRent · RealPage), Colorado AI Act SB 189 reference, MIT licensing posture
- `ARCHITECTURE.md` — compose-order diagram, 6-agent topology, three CRE-native pattern details
- `docs/adr/0001-defcon-state-machine.md` — DEFCON-5 → DEFCON-1 operating-state ladder
- `docs/adr/0002-sovereign-veto.md` — non-overridable boundary check pattern
- `docs/adr/0003-hash-chain-audit.md` — tamper-evident decision ledger with anchor checkpoints
- `docs/adr/0004-autonomy-ladder-a0-a4.md` — A0 → A4 maturity scaffold with A2 → A3 promotion gate
- `docs/adr/0005-eu-ai-act-mapping.md` — regulation-to-pattern YAML mapping discipline
- `docs/adr/0006-shadow-mode-rollout.md` — parallel-path promotion with divergence-bounded gates
- `docs/adr/0007-lease-abstraction-provenance.md` — typed `Provenance` object with material-clause reviewer signature requirement
- `docs/adr/0008-fair-housing-preflight-gate.md` — five-check sequence (FHA-PROXY · FHA-VOUCHER · FHA-SOI · FHA-CRIM · FHA-DISPARATE) with bypass auto-escalation
- `docs/adr/0009-tenant-pii-data-residency.md` — jurisdiction-partitioned storage with `LegalBasis` tagging on cross-jurisdiction reads
- `config/compliance_rules.yaml` — pattern-to-regulation mapping with statute citations
- `.github/workflows/test.yml` — CI pipeline (pytest · ruff · mypy on Python 3.10/3.11/3.12 + example runs)
- `LICENSE` — MIT
- `.gitignore`

### Reviewed
- Council pass at 9.80/10 content bar with 5/5 affirmations (slate: Dorie Clark · Justin Welsh · Lou Adler · Marcos López de Prado · Elad Gil)

### Notes
- v0.1 is the architectural backbone — no executable Python yet. Quickstart instructions in README assume v0.2 ships before public push to GitHub.
