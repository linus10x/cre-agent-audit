# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No items currently in flight. Next-cycle candidate work surfaces here as it lands on `main`.

The single remaining item from the original 7 `SHIP-RECEIPT.md` deferred list — **F32 (Big-4) — Named-GC reference quotes** — is research outside engineering scope and stays open until primary-source quotes can be sourced. It is not gating the next release.

---

## [0.2.2] — 2026-05-28 — Engineering items 2 of 3 closed

**Released:** 2026-05-28 · **Tag:** `v0.2.2` (minted post-CI green on the release commit) · **PR:** post-PR-#31 follow-on commits on `main`

Closes the two engineering items remaining from the original 7 `SHIP-RECEIPT.md` deferred list. The third (F32 — named-GC reference quotes) is research outside engineering scope and remains open.

### Added

- **Fair-housing MI-threshold learned-proxy detector (ADR-0008 update; closes F11).**
  - `MutualInformationCalculator` — stdlib-only MI computation (no `scikit-learn`); quartile-binning for numeric features; result cached per feature
  - `MIThresholdDetector(reference=..., mi_threshold=0.10)` — opt-in detector; `detect_proxies(applicant_features)` returns `tuple[ProxyFinding, ...]`
  - `ProtectedClassReference` — operator-configured labeled sample; construction-time validation (≥30 samples; <100 warns)
  - `ProxyFinding` — feature_name, mi_score, threshold, protected_class_name, severity (auto-derived)
  - `InvalidReferenceError` + `MIReferenceUndersizedWarning`
  - `FairHousingPreflightGate(mi_proxy_detector=...)` — opt-in integration; emits `FHA-MI-PROXY` veto when the detector flags a feature
  - Academic anchoring: Kusner 2017, Calmon 2017, Hardt-Price-Srebro 2016, Pedreshi-Ruggieri-Turini 2008
  - SafeRent-shaped synthetic fixture (`tests/fixtures/saferent_shaped_reference.py`): 1,000-applicant deterministic dataset where `zip_code_quintile` carries MI ≈ 0.369 against voucher status
- **`audit-verify` extra (closes ADR-0012-A1).**
  - New `[project.optional-dependencies] audit-verify = ["cryptography>=42"]`
  - New `src/cre_agent_audit/governance/rfc3161_verify.py` — `verify_tsr_token` + `verify_audit_entry_token` + `TSRVerificationResult` + `TSRParseError`
  - Validates RSA signatures (PKCS1v15 + SHA-256), chains the TSA cert to operator-supplied trusted roots, checks `not_valid_after_utc` (with opt-out via `accept_expired_at_verify_time`)
  - Token-free `AuditEntry` instances (v0.2.0 default) return `verified=True` — no TSA claim to invalidate
  - Base package NEVER imports the module; Zero-Runtime-Dependencies posture preserved
  - CI installs `[dev,audit-verify]` so the new module is exercised across the Python 3.10/3.11/3.12 matrix
  - Synthetic-TSA pytest fixture in `tests/conftest.py` (deterministic, regenerated each run)

### Changed

- `FairHousingPreflightGate.__init__` accepts `mi_proxy_detector: MIThresholdDetector | None = None`. Default `None` preserves v0.2.1 behavior.
- ADR-0008 updated with the "MI-threshold learned-proxy detection (`FHA-MI-PROXY`; added v0.2.2)" subsection.
- ADR-0012 updated with the "v0.2.2 update — `rfc3161_verify` shipped under `[audit-verify]` extra" subsection.
- Package `__init__.py` re-exports the six new detector types.

### Tests

- pytest: **317 / 317 passing** (was 294; +23 across MI detector + fixture + integration + audit-verify)
- mypy `--strict`: clean across `src/ tests/`
- ruff + ruff format: clean

### Deferred to a future release

- **F32 (Big-4) — Named-GC reference quotes.** Research outside engineering scope; stays open until primary-source quotes can be sourced.

---

## [0.2.1] — 2026-05-28 — Adversarial-review follow-ups (4 of 7 closed)

**Released:** 2026-05-28 · **Tag:** `v0.2.1` at sha `680239a` · **DOI:** [10.5281/zenodo.20434575](https://doi.org/10.5281/zenodo.20434575) · **PR:** [#31](https://github.com/linus10x/cre-agent-audit/pull/31) (PR 1 + 2 + 3 on `feat/audit-system-hardening`)

Closed 4 of the original 7 `docs/SHIP-RECEIPT.md` deferred items plus 2 added during PR 3 (ADR-0013 MI Proxy and the consolidated `AuditConsumer`). 3 items remain for v0.2.2; see `[Unreleased]` above.

Build-time historical note: PR 3 bumped the in-flight marker to `0.2.1.dev2`; the published `v0.2.1` wheel built from sha `680239a` self-identifies as `0.2.1.dev2`. Public tag hashes are immutable per repo policy; the cosmetic drift is a one-time historical quirk preserved rather than rewritten.

### Added

- **Pluggable persistence via `LedgerStore` Protocol** (ADR-0012 § Seam 1).
  - `InMemoryLedgerStore` — v0.2.0 behavior preserved as the default backend.
  - `SqliteLedgerStore` — stdlib `sqlite3` backend; one row per `AuditEntry`; no UPDATE codepath; table name validated to prevent injection.
  - `JsonlLedgerStore` — append-only JSONL file; `fsync=True` default for durability.
  - Production deployers wire Postgres+WAL / S3+Object Lock / DynamoDB conditional writes against the Protocol; ADR-0012 documents the integration shape. Driver libraries stay out of the package — the Zero-Deps badge is intact.
- **Trusted timestamps via `TimestampSource` Protocol** (ADR-0012 § Seam 2).
  - `LocalClockTimestampSource` — `datetime.now(timezone.utc)`; no token; preserves v0.2.0 semantics.
  - `RFC3161TimestampSource` — stdlib `http.client` + `ssl` TSA client; fallback-to-local on TSA failure (so a TSA outage cannot stall the audit pipeline); `on_fallback` callback for deployer alerting; set `fallback_to_local_on_failure=False` to fail closed.
  - Hand-rolled `rfc3161_codec.py` covers the DER ASN.1 subset RFC 3161 actually uses (TSQ builder + GeneralizedTime extraction). Signature-chain verification deferred to `rfc3161_verify.py` behind the (forthcoming) `audit-verify` extra.
- **`AuditEntry.timestamp_token_b64`** — optional field; bound into `canonical_bytes_for_hashing` ONLY when present, so v0.2.0 token-free ledgers remain hash-stable under v0.2.1 `verify_chain()`. Mixed-mode ledgers (some entries with tokens, some without) are supported and audit-honest.
- **External witness anchoring via `WitnessRegister` Protocol** (ADR-0012 § Seam 3).
  - `RekorWitness` — Sigstore Rekor public transparency log client; submits `hashedrekord` entries; receives inclusion UUID + logIndex.
  - `OpenTimestampsWitness` — OTS calendar API client with multi-calendar redundancy; pending-commitment receipt upgradable to Bitcoin attestation.
  - `anchor_to_witness(ledger, witness)` writes the receipt back to the ledger as a `decision_type="witness_anchor"` entry — binding the anchor record into the same hash chain it protects.
- **`docs/adr/0012-persistence-witness-timestamp-pattern.md`** documenting the three Protocol seams, the integration shape per non-stdlib backend, and the regulatory mapping (SOC 2 CC6.1 / CC7.2, SOX 404 ITGC, FFIEC Audit Booklet, RFC 3161, RFC 6962).
- **`FAILURE-MODES.md`** (repo root, new) — adversarial / partition / corruption matrix across 8 failure-mode classes with detection mechanism + recovery action + regulatory mapping per row. Companion test `tests/test_failure_modes_matrix.py` enforces doc/code parity: every `(F)` callable reference in the matrix must resolve, every `NOT YET IMPLEMENTED` row must carry a tracking marker. Build fails on drift.
- **MI Proxy — Module Integrity verifier chain-of-custody** (ADR-0013, new).
  - `MIProxy` Protocol with `attest` + `verify_attestation`; default backend `LocalMIProxy` is stdlib-only (SHA-256 over verifier source + canonical config; HMAC-SHA256 signature with a deployer-provided 32+ byte key via `CRE_AUDIT_MI_PROXY_KEY`).
  - Time-bounded attestations (`max_age_seconds`, default 86_400).
  - `LocalMIProxy.from_env()` emits `MIProxyKeyMissingWarning` when the key env var is absent and signs with a zero key — fail-closed at verify time against any real-keyed proxy. Non-suppressible by design.
  - `AuditLedger.verify_chain(mi_proxy=...)` is the opt-in hook; raises `IntegrityVerificationError` when attestation fails and refuses to return a verified result. v0.2.0 callers (`verify_chain()` with no kwarg) see no change.
  - Opt-in external-attestation backends (SLSA / in-toto / Sigstore cosign) documented in ADR-0013; will ship under the `[attestation]` extra in a forthcoming release.
- **`VendorScoreGate` — third-party AI scoring with audit-chain emit** (ADR-0011 update; closes FAILURE-MODES.md § Row 8).
  - Protocol surface: `emit(vendor_id, input_hash, score, model_version)` + `history_for(vendor_id, input_hash)`.
  - `InMemoryVendorScoreGate` default backend writes through to a caller-provided `AuditLedger`. Two chain decision types: `vendor_score_emit` (normal path) and `vendor_score_drift` (flagged when same `(vendor_id, input_hash, model_version)` returns a different score).
  - Score-drift posture (default `raise_on_drift=True`): the flagged chain entry hits the ledger BEFORE `VendorScoreDriftDetected` propagates, so drift is auditable even when the caller swallows the exception. `raise_on_drift=False` available for shadow-mode rollouts.
  - Score-range and field validation at the gate boundary (score finite + in `[0.0, 1.0]`, non-empty string fields).
  - A new `model_version` is not drift (vendor patch with version bump is the legitimate path); same `model_version` + score change IS drift (the silent vendor-patch failure FAILURE-MODES.md Row 8 names).
- **Consolidated `AuditConsumer` base for agents that touch the chain** (`src/cre_agent_audit/agents/base.py`).
  - Captures the v0.2.1 dependency-injection contract in one place: `ledger` + `mi_proxy` + `vendor_score_gate`.
  - `verify_integrity()` — wraps `AuditLedger.verify_chain(mi_proxy=self.mi_proxy)`; fail-closed.
  - `record_vendor_score(...)` — delegates to the injected gate; raises `RuntimeError` when no gate wired (no silent no-op on a vendor signal).
  - `AuditAgent` and `MonitorAgent` extend the base; both accept the three seams through one constructor. Public method signatures preserved (`process` returns the same types as v0.2.0; `MonitorAgent()` no-arg call still works).

### Changed

- `AuditLedger.__init__` accepts `store: LedgerStore | None = None` and `timestamp_source: TimestampSource | None = None`. Both default to the v0.2.0 reference implementations via `__post_init__`. **Existing `AuditLedger()` callers see no behavior change.**
- `AuditLedger.verify_chain` gains an optional `mi_proxy: MIProxy | None = None` keyword argument; when supplied, attestation runs before the chain walk and `IntegrityVerificationError` is raised on failure. **`verify_chain()` without the kwarg is unchanged from v0.2.0 / PR 1+2.**
- `AuditAgent` constructor: `AuditAgent(ledger)` → `AuditAgent(ledger, *, mi_proxy=None, vendor_score_gate=None)`. v0.2.0 callers see no change.
- `MonitorAgent` constructor: `MonitorAgent()` → `MonitorAgent(ledger=None, *, mi_proxy=None, vendor_score_gate=None)`. v0.2.0 no-arg callers see no change.
- Public API surface (`__init__.py`) re-exports `LedgerStore`, `InMemoryLedgerStore`, `SqliteLedgerStore`, `JsonlLedgerStore`, `Attestation`, `IntegrityVerificationError`, `LocalMIProxy`, `MIProxy`, `MIProxyKeyMissingWarning`, `InMemoryVendorScoreGate`, `VendorScoreDriftDetected`, `VendorScoreEntry`, `VendorScoreGate` from the package root.

### Tests

- pytest: **234 / 234 passing** (was 142 at v0.2.0; was 185 at the end of PR 1+2; +49 new tests across this session — 5 failure-modes matrix, 17 MI Proxy, 14 VendorScoreGate, 13 AuditConsumer integration).
- mypy `--strict`: clean.
- ruff + ruff format: clean.

### Deferred to v0.2.2

The 3 remaining items from the original 7 `SHIP-RECEIPT.md` deferred list move forward as the v0.2.2 candidate scope (see `[Unreleased]` block above): the fair-housing MI-threshold detector, named-GC reference quotes, and the `audit-verify` extra wiring.

The agent topology pruning previously forward-referenced as "(ADR-0013, forthcoming)" in PR 1+2's `[Unreleased]` block is **superseded by v0.2.1's ADR-0013 (MI Proxy)**; the topology decision moves to a future ADR (likely ADR-0014). The consolidation of `AuditAgent` + `MonitorAgent` behind `AuditConsumer` is what landed in this v0.2.1 release in its place.

---

## [0.2.0] — 2026-06-02 — First public release · Foundation

**First public release of cre-agent-audit.** Nine governance patterns for AI-enabled commercial real estate workflows. Built to a single design philosophy: durable artifacts, not slideware.

### Design philosophy

Every pattern produces an artifact — code, ADR, audit-ledger entry, veto-config, control-description table, vendor-clause template — that survives outside the engagement that created it. Patterns are MIT-licensed, zero-runtime-dependency, and mapped to primary-source regulatory citations. The repo is meant to compound: fork it, ship it inside your stack, copy patterns into your own audit framework. The patterns are non-proprietary; the implementation is yours.

### Settled-liability anchors (primary-source verified)

The patterns are designed against three regulatory matters in the CRE-AI surface:
- *In re Trans Union Rental Screening Solutions* — FTC/CFPB consent orders, October 2023, $15M — FCRA § 607(b) accuracy
- *Louis v. SafeRent Solutions, LLC*, No. 1:22-cv-10800 (D. Mass.) — November 2024 — approximately $2.275M class settlement; five-year score-use injunction on voucher-holder applicants
- *U.S. v. RealPage, Inc.* (M.D.N.C., filed August 23, 2024 by DOJ + 8 state AGs) — ongoing civil antitrust litigation alleging algorithmic rent-coordination

Doctrinal foundation: *Texas Dept. of Housing v. Inclusive Communities Project*, 576 U.S. 519 (2015).

### Patterns

- **ADR-0001 — DEFCON State Machine** · 5 states · per-state capability allowlist · transition logging
- **ADR-0002 — Sovereign Veto** · constraint-surface-specific · structured reason codes · explicit sovereign RACI
- **ADR-0003 — Internally-Consistent Hash-Chained Audit Ledger** · SHA-256 chaining · `chain_head()` digest exposed for external witness anchoring (OpenTimestamps / Sigstore Rekor) · Audit Evidence Properties documented for SOC 2 / SOX 404 / FFIEC framing
- **ADR-0004 — Autonomy Ladder™ A0 → A4** · five-tier promotion gate · Prior Art subsection citing SAE J3016 + OECD + NIST + Shavit + Anderljung + Kelly/Weaver assurance-case methodology
- **ADR-0005 — Regulation Loader** · loads `config/compliance_rules.json` (runtime) generated from `compliance_rules.yaml` (author-time) · pattern↔regulation queries
- **ADR-0006 — Shadow-Mode Rollout** · parallel dry-run before live promotion · SR 11-7 alignment
- **ADR-0007 — Lease-Abstraction Provenance Chain** · clause-level provenance + OCR confidence + reviewer signature
- **ADR-0008 — Fair-Housing Pre-Flight Gate** · 5 ordered checks (FHA-PROXY/VOUCHER/SOI/CRIM/DISPARATE) · lexical-only proxy detection bound · ICP v Texas cited · BypassRegistry auto-escalation
- **ADR-0009 — Tenant-PII Data-Residency Partitioning** · 5 RESIDENCY-* veto codes · GDPR Art. 6 LegalBasis taxonomy
- **ADR-0010** (NEW) — Audit-Chain Retention, Privilege & Discovery Posture · SOL-synchronized retention · attorney-client privilege routing · litigation-hold integration
- **ADR-0011** (NEW) — Vendor-Output Adapter Pattern (design baseline; concrete `VendorScoreGate` implementation ships in v0.2.1) · `VendorScoreGate` Protocol for vendor-mediated AI surfaces

### Adversarial pressure-test fold-in

This release reflects a 5-chamber adversarial review by personas representing a PE operating partner, a Big-4 AI-audit partner, an AI-governance attorney, a CRE-vertical CTO, and an algorithmic-fairness academic. 33 findings surfaced; 26 folded into v0.2.0; 7 explicitly deferred to v0.2.1 (named in `docs/SHIP-RECEIPT.md`).

### Added in v0.2.0

- **Zero runtime dependencies.** `pyyaml` moved to dev-only via `scripts/build_compliance_json.py` (CI verifies JSON stays in sync with YAML).
- **Two file renames** for canonical pattern vocabulary: `fair_housing_gate.py` → `fair_housing_preflight.py`; `tenant_pii_partition.py` → `tenant_pii_residency.py`.
- **Tamper-evident reframing** in ADR-0003 + `audit_chain.py` module docstring — "internally-consistent hash-chained ledger; tamper-evident when anchored to an external witness."
- **Explicit public API surface** via `src/cre_agent_audit/__init__.py` `__all__` (40+ named exports organized by pattern).
- **Designating the Sovereign RACI** subsection in ADR-0002 — model RACI per surface (CCO+GC for screening; CRO+GC+Audit Cmte for pricing; etc.).
- **9 per-pattern Control Description Tables** at `docs/controls/CTRL-001..009.md` — Activity / Objective / Owner / Frequency / Type / Evidence / Test of Design / Test of Operating Effectiveness.
- **Four-framework mapping matrix** at `docs/MAPPING-MATRICES.md` — NIST AI RMF × ISO/IEC 42001 × COSO ICAIR × Big-4 standard taxonomy.
- **Drop-in vendor-clause templates** at `docs/vendor-clauses/{screening,abstraction,pricing}.md`.
- **PE due-diligence 10-question checklist** at `docs/PE_DUE_DILIGENCE.md`.
- **Limitations document** at `docs/LIMITATIONS.md` — explicit "what this stack does NOT do."
- **Prior-art document** at `docs/PRIOR-ART.md` — intellectual lineage (SAE J3016, OECD, NIST, Shavit, Anderljung, Barocas/Hardt/Narayanan, Selbst, Mitchell, Gebru, Raji, ICP v Texas).
- **90-day deployment cadence walkthrough** at `examples/FIRST_90_DAYS.md` — reframed as engineering rails feeding the GC's privileged risk assessment, not a discoverable audit-baseline.
- **3 cleaned-up FINOS-format contributory control drafts** at `governance-artifacts/` with explicit non-endorsement provenance headers (AIR-RC-004, AIR-RC-007, AIR-MIT-RC-VETO-01).
- **DISCLAIMER.md** at repo root + reference-pattern-not-legal-advice header on every ADR.
- **`Makefile`** with `verify` target + **`docs/REPRODUCE.md`** for one-command cold-clone reproduction.
- **Sibling-parity files**: `CITATION.cff`, `CODE_OF_CONDUCT.md`, `ROADMAP.md`, `.pre-commit-config.yaml`, `.github/CODEOWNERS`, `FUNDING.yml`, `dependabot.yml`, `ISSUE_TEMPLATE/pattern_request.yml`, `PULL_REQUEST_TEMPLATE.md`.

### Verified

- pytest: **142 / 142 passing** · pytest-cov: **89% branch coverage** (above 85% gate)
- ruff: **clean** · ruff format: **clean** · mypy `--strict`: **clean** across 33 source files
- All 3 example scripts continue to exit 0
- Cold-clone `make verify` runs under 60 seconds
- gitleaks: **clean** · markdownlint: **clean**

### Sibling

Maps 1:1 with [`linus10x/finserv-agent-audit`](https://github.com/linus10x/finserv-agent-audit) for financial-services workflows.

### Stage 2c primary-source fact-check corrections

- YAML `DOJ-RealPage Restrictions (consent decree Nov 24, 2025)` → corrected to *U.S. v. RealPage* ongoing Sherman § 1 litigation (filed Aug 23, 2024). Wikipedia + DOJ ATR primary-source verified.
- TransUnion framing aligned to *In re Trans Union Rental Screening Solutions* + FCRA § 607(b) accuracy basis.
- SafeRent framing aligned to *Louis v. SafeRent Solutions, LLC*, No. 1:22-cv-10800 (D. Mass.) class settlement (not adjudicated FHA liability).
- Colorado AI Act framing aligned to SB24-205 (primary-source verified via leg.colorado.gov) + hedged on follow-on SB 26-189 amendments.

---

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
- `src/cre_agent_audit/governance/tenant_pii_residency.py` — `TenantPIIResidencyCheck` per ADR-0009 with all 5 RESIDENCY-* veto codes (CROSS-JURISDICTION-UNTAGGED · CONSENT-MISSING · LIA-MISSING · STATUTE-MISSING · PURPOSE-VAGUE) + `CrossJurisdictionRequest` typed object + `LegalBasis` enum (GDPR Art. 6 taxonomy)
- `src/cre_agent_audit/agents/` — 6 agent stubs per ARCHITECTURE.md topology: `DomainIntelligenceAgent` · `StrategyAgent` · `RiskAgent` · `AuditAgent` (functional — filters ledger by decision_type / actor_id / sequence) · `OrchestratorAgent` · `MonitorAgent`. Shared `Agent[InputT, OutputT]` ABC in `agents/base.py`.
- `tests/test_shadow_mode.py` — 16 unit tests
- `tests/test_regulation_loader.py` — 12 unit tests (including malformed-YAML validation)
- `tests/test_tenant_pii_residency.py` — 15 unit tests
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
- `src/cre_agent_audit/governance/fair_housing_preflight.py` — `FairHousingPreflightGate` per ADR-0008 with all 5 ordered checks (FHA-PROXY · FHA-VOUCHER · FHA-SOI · FHA-CRIM · FHA-DISPARATE) + `DisparateImpactMonitor` (four-fifths-rule) + `BypassRegistry` (3-bypasses-same-owner-90d → GC, 5-bypasses-same-reason-90d → DEFCON-4)
- `tests/test_lease_provenance.py` — 13 unit tests
- `tests/test_fair_housing_preflight.py` — 17 unit tests
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
- `src/cre_agent_audit/governance/fair_housing_preflight.py` (ADR-0008 — heaviest module, 5 ordered checks + auto-escalation + disparate-impact monitor)
- `src/cre_agent_audit/governance/tenant_pii_residency.py` (ADR-0009)
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
