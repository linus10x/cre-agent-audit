# Mapping Matrices — 9 Patterns × 4 Frameworks

> **Reference mapping, not authoritative framework interpretation.** See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md). Mappings are author-asserted; every annual repo review re-verifies them against the framework's primary-source documents.

Four side-by-side matrices showing how the nine cre-agent-audit patterns map into the AI-governance frameworks Big-4 audit firms and risk-committee teams use to scope assurance programs.

## Matrix A — Patterns × NIST AI RMF 1.0

NIST AI Risk Management Framework 1.0 (January 2023). Four core functions: GOVERN · MAP · MEASURE · MANAGE.

| # | Pattern | GOVERN | MAP | MEASURE | MANAGE |
|---|---|---|---|---|---|
| 1 | DEFCON State Machine | 1.6 (incident response) | — | — | 2.3 (risk decisions documented) |
| 2 | Sovereign Veto | 2.3 (decisions documented) | — | — | 4.1 (post-deployment monitoring) |
| 3 | Hash-Chained Audit Ledger | — | — | 2.1 (system performance monitored) | 4.3 (errors corrected) |
| 4 | Autonomy Ladder™ A0→A4 | 1.1 (accountability mechanisms) | 1.1 (context) | — | 2.3 (risk decisions documented) |
| 5 | Regulation Loader | 1.1 | 2.3 (system requirements) | 3.1 (approaches + metrics) | — |
| 6 | Shadow-Mode Rollout | — | 4.1 (mapping risks) | — | 2.4 (mechanisms for inspection) |
| 7 | Lease-Abstraction Provenance | — | — | 2.1 | 4.3 |
| 8 | Fair-Housing Pre-Flight Gate | — | 2.3 | 2.11 (fairness metrics) | 2.3 + 2.4 |
| 9 | Tenant PII Data Residency | — | 2.3 | 2.10 (privacy) | 4.3 |

## Matrix B — Patterns × ISO/IEC 42001:2023 Annex A

ISO/IEC 42001:2023 — *Information technology — Artificial intelligence — Management system*. Annex A controls.

| # | Pattern | ISO/IEC 42001:2023 Annex A controls |
|---|---|---|
| 1 | DEFCON State Machine | A.6.1.2 (risk treatment options) · A.10.1.3 (operations management) |
| 2 | Sovereign Veto | A.6.2.1 (segregation of duties) · A.9.4.1 (access to functions and information) |
| 3 | Hash-Chained Audit Ledger | A.12.4.1 (event logging) · A.12.4.2 (protection of log information) · A.12.4.3 (administrator and operator logs) |
| 4 | Autonomy Ladder™ A0→A4 | A.6.1.2 (segregation) · A.5.32 (information security in project management) |
| 5 | Regulation Loader | A.5.36 (compliance) · A.18.1.1 (identification of applicable legislation) |
| 6 | Shadow-Mode Rollout | A.14.2.1 (secure development policy) · A.14.2.8 (system security testing) |
| 7 | Lease-Abstraction Provenance | A.8.2.2 (information labelling) · A.12.4.1 (event logging) · A.18.1.3 (protection of records) |
| 8 | Fair-Housing Pre-Flight Gate | A.5.33 (protection of personal data) · A.5.34 (privacy / PII) |
| 9 | Tenant PII Data Residency | A.5.34 (privacy / PII) · A.5.36 (compliance) · A.18.1.4 (privacy / PII) |

**Note.** ISO/IEC 42001:2023 Annex A control numbering is the standard's primary-source numbering. Mappings here are author-asserted at the standard-control level; subordinate clause-level mappings (e.g., A.5.34.3) are out of scope for v0.2.0 and are tracked for v0.3.

## Matrix C — Patterns × COSO ICAIR

COSO ICAIR (Internal Control over AI Reporting) — the COSO + Deloitte 2024 overlay extending COSO's Internal Control – Integrated Framework (2013) to AI systems. Five components.

| # | Pattern | COSO ICAIR Component |
|---|---|---|
| 1 | DEFCON State Machine | Risk Assessment · Monitoring |
| 2 | Sovereign Veto | Control Activities · Information & Communication |
| 3 | Hash-Chained Audit Ledger | Information & Communication · Monitoring |
| 4 | Autonomy Ladder™ A0→A4 | Control Environment · Risk Assessment |
| 5 | Regulation Loader | Information & Communication · Monitoring |
| 6 | Shadow-Mode Rollout | Risk Assessment · Control Activities |
| 7 | Lease-Abstraction Provenance | Control Activities · Monitoring |
| 8 | Fair-Housing Pre-Flight Gate | Control Activities · Monitoring |
| 9 | Tenant PII Data Residency | Control Activities · Risk Assessment |

## Matrix D — Patterns × Big-4 Standard AI-Controls Taxonomy

Composite taxonomy from PwC's Responsible AI Toolkit, Deloitte's Trustworthy AI Framework, EY's Trusted AI Framework, and KPMG's AI Assurance Framework as of 2026. Seven canonical buckets.

| # | Pattern | Lifecycle Governance | Data Lineage | Model Validation | Operational Monitoring | Human Oversight | Third-Party | Incident Response |
|---|---|---|---|---|---|---|---|---|
| 1 | DEFCON State Machine | | | | ✅ | | | ✅ |
| 2 | Sovereign Veto | | | | | ✅ | | ✅ |
| 3 | Hash-Chained Audit Ledger | | ✅ | | ✅ | | | |
| 4 | Autonomy Ladder™ | ✅ | | | | ✅ | | |
| 5 | Regulation Loader | ✅ | | | ✅ | | | |
| 6 | Shadow-Mode Rollout | ✅ | | ✅ | | | | |
| 7 | Lease-Abstraction Provenance | | ✅ | ✅ | | | | |
| 8 | Fair-Housing Pre-Flight Gate | | | | ✅ | ✅ | | |
| 9 | Tenant PII Data Residency | | ✅ | | | | ✅ | |

**Layered policy ADRs (no separate pattern primitive):**
- **ADR-0010 — Audit-Chain Retention, Privilege & Discovery Posture** — maps to: Lifecycle Governance · Incident Response · (legal-process surface beyond the canonical taxonomy)
- **ADR-0011 — Vendor-Output Adapter Pattern** — maps to: Third-Party · Operational Monitoring · Human Oversight

## How to use this matrix in an assurance program

For a Big-4 senior manager scoping an AI-assurance engagement at a CRE operator that has adopted these patterns:

1. **For an ISO 42001 conformance audit**, use Matrix B to populate the AIMS audit program; each pattern is a control with named ISO Annex A control IDs.
2. **For a NIST AI RMF readiness assessment**, use Matrix A; the four-function coverage is visible at a glance.
3. **For a COSO ICAIR overlay engagement**, use Matrix C; the five-component coverage map provides the integrated-control-framework view your client's CFO will recognize.
4. **For a "what does this repo do vs what does Credo AI do" comparative**, Matrix D maps to the standard AI-controls vocabulary your peers' frameworks use.

The per-pattern Control Description Tables in [`docs/controls/`](controls/) provide the Activity / Objective / Owner / Frequency / Type / Evidence / Test of Design / Test of Operating Effectiveness pack your senior managers need for workpaper population.

## What this matrix does NOT do

- Does not assert that adopting all nine patterns clears any specific framework certification (ISO 42001 conformance requires a management-system audit beyond control inventory; NIST AI RMF is a framework, not a certification).
- Does not address vertical-specific frameworks (PCI DSS for payment data; HIPAA for healthcare; DORA for EU financial services — those require separate mapping work).
- Does not cover the policy + governance + organizational-design layer that surrounds the controls (operator + counsel + audit own that).
- Subordinate clause-level ISO 42001 mappings (A.X.Y.Z) are out of scope for v0.2.0; tracked for v0.3.

## Annual review cadence

The mappings in this document are author-asserted at v0.2.0 release. Annual review is required to verify:

1. Framework versions are current (NIST AI RMF Profile updates · ISO 42001 amendments · COSO ICAIR revisions · Big-4 framework refreshes)
2. Mapping accuracy holds (a framework revision may add controls that change a pattern's mapping)
3. New patterns added to the repo are mapped before release

Annual review evidence is recorded in the equivalent of `docs/SESSION-AUDIT.md` Stage 2c "Verified facts ledger" — primary-source URLs + accessed-date + mapping-change deltas.
