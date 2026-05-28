# Limitations — what this stack does NOT do

> **Reference statement of limitations, not a complete enumeration.** Adopters are responsible for their own validation, controls testing, and counsel review. See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md).

The nine patterns in this repository are a useful starting point for AI-governance discipline in CRE operating companies. They are not a sufficient program on their own. This document enumerates the most material limitations so adopters can scope additional controls.

## Engineering limitations

### 1. Lexical-only proxy detection in the Fair-Housing Pre-Flight Gate (Pattern 8 / ADR-0008)

The proxy-detection check in `FairHousingPreflightGate` compares input feature names against a configurable lexical blocklist. It does NOT detect:

- **Learned proxies in embedding space.** A deep model can encode protected-class information in latent features even when the named feature is excluded (Dwork et al. 2012; Datta et al. 2017; Selbst et al. 2019 *Fairness and Abstraction in Sociotechnical Systems*).
- **Behavioral-signal proxies.** Browser fingerprints, application-session timing patterns, language patterns (Buolamwini & Gebru 2018 *Gender Shades*).
- **Geospatial-granularity proxies finer than zip code.** Census-tract-level, block-group-level, or precinct-level proxies require finer-grained detection than this gate provides.

Detection of those classes requires upstream training-time controls (differential privacy on training data, adversarial debiasing, counterfactual fairness audits — Kusner et al. 2017 *Counterfactual Fairness*) — out of scope for v0.2.0. The mutual-information-threshold learned-proxy detector for Pattern 8 is tracked as a v0.2.1 deliverable (not yet landed).

### 2. Tamper-detection within the trust boundary by default; tamper-evidence requires the witness pattern (Pattern 3 / ADR-0003 + ADR-0012 + ADR-0013)

The hash-chained Audit Ledger detects modification by an honest holder of the chain head. Adversarial integrity against an attacker with full ledger-host write access requires anchoring the chain head to an external witness register.

v0.2.1 ships the witness-anchor pattern (ADR-0012 § Seam 3 — `RekorWitness` for Sigstore, `OpenTimestampsWitness`, and `anchor_to_witness()` that binds the receipt back into the same chain). Scheduling the anchor cron is the deployer's responsibility. v0.2.1 also ships the MI Proxy (ADR-0013) so the verifier itself is tamper-detecting: `AuditLedger.verify_chain(mi_proxy=...)` fails closed via `IntegrityVerificationError` when the verifier's own attestation does not check.

Out-of-band external attestation backends (SLSA / in-toto / Sigstore cosign) are tracked behind the future `[attestation]` extra.

### 3. Pluggable persistence shipped in v0.2.1; production substrate is the deployer's choice (Pattern 3 / ADR-0003 + ADR-0012)

v0.2.0's reference `AuditLedger` stored entries in an in-memory `list[AuditEntry]`. v0.2.1 introduces the `LedgerStore` Protocol (ADR-0012 § Seam 1) with three stdlib reference backends (`InMemoryLedgerStore`, `SqliteLedgerStore`, `JsonlLedgerStore`). Production deployments wire their own backend against the Protocol — Postgres + WAL with row-level-immutability constraints, append-only S3 + Object Lock, or DynamoDB with conditional writes — to satisfy SOX 404 ITGC retention or FFIEC Audit booklet expectations. The package does not pull driver libraries; the Zero-Deps badge is intact.

### 4. RFC 3161 trusted timestamps shipped in v0.2.1; signature-chain verification on the v0.2.1 follow-up backlog (Pattern 3 / ADR-0003 + ADR-0012)

v0.2.0 used `datetime.now(timezone.utc)` for `AuditEntry.timestamp` — local system clock. v0.2.1 introduces the `TimestampSource` Protocol (ADR-0012 § Seam 2) with `LocalClockTimestampSource` (default) and `RFC3161TimestampSource` (stdlib `http.client` + hand-rolled DER ASN.1 codec). The TSR token is opaque-stored verbatim so any RFC 3161-aware verifier can validate the TSA chain later.

Signature-chain re-verification of stored TSR tokens (`rfc3161_verify.py` behind the `audit-verify` extra, using `pyca/cryptography`) is the remaining v0.2.1 deliverable on this seam.

### 5. Four-fifths-rule monitor only (Pattern 8)

The disparate-impact check uses the standard four-fifths-rule selection-rate comparison. It does NOT engage the fairness-metric pluralism / impossibility-result literature:

- Kleinberg, Mullainathan & Raghavan (2016) *Inherent Trade-Offs in the Fair Determination of Risk Scores* — calibration vs balance for negative class vs balance for positive class are mutually inconsistent except in degenerate cases
- Chouldechova (2017) *Fair prediction with disparate impact* — the impossibility result for criminal-justice risk scores
- Kasy & Abebe (2021) *Fairness, Equality, and Power in Algorithmic Decision-Making* — the distributive-justice critique of group-fairness metrics

Adopters owning a regulator-facing fairness defense should choose their fairness metric in consultation with counsel and document the choice. The four-fifths-rule is the standard regulatory benchmark under HUD 24 C.F.R. § 100.500 and Uniform Guidelines on Employee Selection Procedures (29 C.F.R. § 1607.4(D)); adopting it is defensible-but-not-uniquely-defensible.

### 6. Vendor-mediated AI captured via `VendorScoreGate` in v0.2.1 (Pattern 11 / ADR-0011 + FAILURE-MODES.md Row 8)

Most CRE operators do not run their own tenant-screening, lease-abstraction, or pricing models. They consume vendor outputs. ADR-0011 documents the design for the `VendorScoreGate` adapter; v0.2.1 ships the concrete implementation:

- The ADR-0011 design + interface sketch (v0.2.0)
- The `docs/vendor-clauses/{screening,abstraction,pricing}.md` procurement-side companion (v0.2.0)
- The `VendorScoreGate` Protocol + `InMemoryVendorScoreGate` default backend (v0.2.1) — emits every vendor-scoring event to the audit chain with full provenance (`vendor_id`, `input_hash`, `score`, `model_version`)
- Score-drift detection (v0.2.1) — same `input_hash` + same `model_version` + different `score` surfaces as a flagged `decision_type="vendor_score_drift"` chain entry; default posture raises `VendorScoreDriftDetected` so the pipeline halts rather than silently absorbing the change (`raise_on_drift=False` available for shadow-mode rollouts)

A SafeRent-shaped synthetic vendor-output fixture is the remaining v0.2.1 deliverable on this seam — currently tracked as a follow-up alongside the fair-housing MI-threshold detector.

### 7. State-by-state regulatory coverage is partial

The compliance-rules YAML covers federal regulations + Colorado AI Act + the federal-floor source-of-income ordinance jurisdictions (CA, CT, DC, MA, MN, NJ, NY, OR, VT, WA). State-by-state mapping at the deployer-obligation level is partial — five state-mapping issues (TX, NY, CA, WA, FL) are open as v0.2.0 good-first-issues, with primary-source citation required per PR.

## Scope limitations

### 8. Engages the operator's *deployment*, not the model's *training*

Selbst et al. 2019 *Fairness and Abstraction in Sociotechnical Systems* — fairness is sociotechnical, not technical. This stack governs how AI is *deployed* by an operator inside an operating workflow. Training-time controls (training-data hygiene, model architecture choices, hyperparameter selection) are out of scope. Adopters whose AI exposure runs through vendor-supplied models have additional vendor-side training-time controls to require through procurement (see vendor-clauses).

### 9. Pre-revenue research artifact

The repository is a reference architecture published as a v0.2.0 first public release. It has not been deployed in a production environment by the author or by any named adopter. The author's prior experience operating governance programs informs the patterns, but the patterns themselves have not been battle-tested at production scale in CRE. Adopters own validation in their environments.

### 10. No production-deployment warranties

The MIT license disclaims warranty. This `LIMITATIONS.md` extends that posture to the non-software components (regulatory characterizations, control descriptions, vendor-clause templates, due-diligence checklists, deployment-cadence walkthroughs). See [`DISCLAIMER.md`](../DISCLAIMER.md) for the full statement.

## Follow-up backlog

### v0.2.1 in flight on `main` as `0.2.1.dev2` — 4 of 7 deferred items landed

- ✅ Pluggable persistence backend for `AuditLedger` — shipped (ADR-0012 § Seam 1)
- ✅ RFC 3161 trusted-timestamp integration — shipped (ADR-0012 § Seam 2)
- ✅ OpenTimestamps / Sigstore Rekor witness-anchor reference integration — shipped (ADR-0012 § Seam 3)
- ✅ `VendorScoreGate` concrete implementation — shipped (ADR-0011 update)
- ✅ Full failure-modes appendix — shipped (`FAILURE-MODES.md` matrix + drift-detection test)
- ✅ (added in PR 3) ADR-0013 MI Proxy — shipped (verifier chain-of-custody)
- ✅ (added in PR 3) Consolidated `AuditConsumer` base — shipped

### v0.2.1 still gates the final tag

- MI-threshold learned-proxy detection in `fair_housing_preflight.py` (mutual-information based; ADR-0008 update) + SafeRent-shaped synthetic fixture. Distinct from the Module Integrity Proxy that shipped under ADR-0013.
- `audit-verify` extra wiring (`rfc3161_verify.py` signature-chain validation behind `pyca/cryptography`)
- Named-GC reference quotes

### v0.3 follow-ups

- Full per-pattern subordinate-clause-level ISO/IEC 42001 mapping (v0.2.0 ships pattern-level mappings)
- Five state regulatory mappings (TX, NY, CA, WA, FL) — community good-first-issues
- `agents/` subpackage: prune the unused stubs (`strategy`, `risk`, `domain_intelligence`) and promote `orchestrator` to a functional implementation. The `AuditConsumer` base shipped in v0.2.1 already consolidated the seams for `audit` and `monitor`.
- Docker compose for 60-second zero-pip-install demo
- LangChain + CrewAI adapter modules
- Terraform module sketch for the IdP-bypass-authority resolver integration
- External-attestation backends for the MI Proxy (SLSA / in-toto / Sigstore cosign) behind the `[attestation]` extra

## What this list does NOT do

- Does not enumerate every possible adversarial input or threat model
- Does not address vertical-specific regulatory regimes outside CRE (PCI DSS, HIPAA, DORA, etc.)
- Does not replace a security-review or threat-modeling engagement

If you identify a limitation worth adding to this list, please open an issue at https://github.com/linus10x/cre-agent-audit/issues with the description and (where possible) a citation.
