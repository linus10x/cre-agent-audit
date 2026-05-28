# Limitations — what this stack does NOT do

> **Reference statement of limitations, not a complete enumeration.** Adopters are responsible for their own validation, controls testing, and counsel review. See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md).

The nine patterns in this repository are a useful starting point for AI-governance discipline in CRE operating companies. They are not a sufficient program on their own. This document enumerates the most material limitations so adopters can scope additional controls.

## Engineering limitations

### 1. Lexical-only proxy detection in the Fair-Housing Pre-Flight Gate (Pattern 8 / ADR-0008)

The proxy-detection check in `FairHousingPreflightGate` compares input feature names against a configurable lexical blocklist. It does NOT detect:

- **Learned proxies in embedding space.** A deep model can encode protected-class information in latent features even when the named feature is excluded (Dwork et al. 2012; Datta et al. 2017; Selbst et al. 2019 *Fairness and Abstraction in Sociotechnical Systems*).
- **Behavioral-signal proxies.** Browser fingerprints, application-session timing patterns, language patterns (Buolamwini & Gebru 2018 *Gender Shades*).
- **Geospatial-granularity proxies finer than zip code.** Census-tract-level, block-group-level, or precinct-level proxies require finer-grained detection than this gate provides.

Detection of those classes requires upstream training-time controls (differential privacy on training data, adversarial debiasing, counterfactual fairness audits — Kusner et al. 2017 *Counterfactual Fairness*) — out of scope for v0.2.0; MI-threshold detection tracked for v0.3.

### 2. Internally-consistent ledger, not adversarially tamper-evident on its own (Pattern 3 / ADR-0003)

The hash-chained Audit Ledger detects modification by an honest holder of the chain head. Adversarial integrity against an attacker with full ledger-host write access requires periodic anchoring of the chain head to an external witness register — OpenTimestamps, Sigstore Rekor, regulator log, or a notarized blockchain anchor (Haber & Stornetta 1991; RFC 6962 Certificate Transparency design rationale).

The `AuditLedger.chain_head()` method exposes the head digest for deployer-side anchoring. Reference integration of OpenTimestamps / Sigstore Rekor is a v0.3 candidate.

### 3. In-memory persistence in the reference implementation (Pattern 3 / ADR-0003)

The reference `AuditLedger` stores entries in an in-memory `list[AuditEntry]`. Production deployments need a pluggable persistence backend (Postgres + WAL with row-level-immutability constraints, append-only S3 + Object Lock, DynamoDB with conditional writes) to satisfy SOX 404 ITGC retention or FFIEC Audit booklet expectations. This is the highest-priority v0.3 follow-up.

### 4. Local-clock timestamps (Pattern 3 / ADR-0003)

`AuditEntry.timestamp` comes from `datetime.now(timezone.utc)` — local system clock. For RFC 3161 trusted timestamps (the audit-grade time-attestation standard), deployers integrate a TSA (FreeTSA, DigiCert, internal TSA). v0.3 candidate.

### 5. Four-fifths-rule monitor only (Pattern 8)

The disparate-impact check uses the standard four-fifths-rule selection-rate comparison. It does NOT engage the fairness-metric pluralism / impossibility-result literature:

- Kleinberg, Mullainathan & Raghavan (2016) *Inherent Trade-Offs in the Fair Determination of Risk Scores* — calibration vs balance for negative class vs balance for positive class are mutually inconsistent except in degenerate cases
- Chouldechova (2017) *Fair prediction with disparate impact* — the impossibility result for criminal-justice risk scores
- Kasy & Abebe (2021) *Fairness, Equality, and Power in Algorithmic Decision-Making* — the distributive-justice critique of group-fairness metrics

Adopters owning a regulator-facing fairness defense should choose their fairness metric in consultation with counsel and document the choice. The four-fifths-rule is the standard regulatory benchmark under HUD 24 C.F.R. § 100.500 and Uniform Guidelines on Employee Selection Procedures (29 C.F.R. § 1607.4(D)); adopting it is defensible-but-not-uniquely-defensible.

### 6. Vendor-mediated AI gets partial coverage in v0.2.0 (Pattern 11)

Most CRE operators do not run their own tenant-screening, lease-abstraction, or pricing models. They consume vendor outputs. ADR-0011 documents the design for the `VendorScoreGate` adapter that bridges vendor outputs (score, recommendation, reason-codes) into the operator's audit ledger + sovereign-veto layer. v0.2.0 ships:

- The ADR-0011 design + interface sketch
- The `docs/vendor-clauses/{screening,abstraction,pricing}.md` procurement-side companion

v0.2.0 does NOT ship:
- Reference implementation of `VendorScoreGate` (v0.3 candidate)
- A SafeRent-shaped synthetic vendor-output test example (v0.3 candidate)
- Integration test against a mock vendor (v0.3 candidate)

Until the v0.3 implementation lands, operators that depend on vendor-mediated AI coverage should adopt the procurement-clause companion and build the adapter integration in-house following the ADR-0011 design sketch.

### 7. State-by-state regulatory coverage is partial

The compliance-rules YAML covers federal regulations + Colorado AI Act + the federal-floor source-of-income ordinance jurisdictions (CA, CT, DC, MA, MN, NJ, NY, OR, VT, WA). State-by-state mapping at the deployer-obligation level is partial — five state-mapping issues (TX, NY, CA, WA, FL) are open as v0.2.0 good-first-issues, with primary-source citation required per PR.

## Scope limitations

### 8. Engages the operator's *deployment*, not the model's *training*

Selbst et al. 2019 *Fairness and Abstraction in Sociotechnical Systems* — fairness is sociotechnical, not technical. This stack governs how AI is *deployed* by an operator inside an operating workflow. Training-time controls (training-data hygiene, model architecture choices, hyperparameter selection) are out of scope. Adopters whose AI exposure runs through vendor-supplied models have additional vendor-side training-time controls to require through procurement (see vendor-clauses).

### 9. Pre-revenue research artifact

The repository is a reference architecture published as a v0.2.0 first public release. It has not been deployed in a production environment by the author or by any named adopter. The author's prior experience operating governance programs informs the patterns, but the patterns themselves have not been battle-tested at production scale in CRE. Adopters own validation in their environments.

### 10. No production-deployment warranties

The MIT license disclaims warranty. This `LIMITATIONS.md` extends that posture to the non-software components (regulatory characterizations, control descriptions, vendor-clause templates, due-diligence checklists, deployment-cadence walkthroughs). See [`DISCLAIMER.md`](../DISCLAIMER.md) for the full statement.

## What v0.2.0 also does NOT cover (named v0.3 follow-ups)

- Implementation of MI-threshold learned-proxy detection in `fair_housing_preflight.py`
- Pluggable persistence backend for `AuditLedger`
- RFC 3161 trusted-timestamp integration
- OpenTimestamps / Sigstore Rekor witness-anchor reference integration
- `VendorScoreGate` concrete implementation (with SafeRent-shaped synthetic example)
- Full per-pattern subordinate-clause-level ISO/IEC 42001 mapping (v0.2.0 ships pattern-level mappings)
- Five state regulatory mappings (TX, NY, CA, WA, FL) — community good-first-issues
- `agents/` subpackage: five stub agent classes (`strategy`, `risk`, `monitor`, `orchestrator`, `domain_intelligence`) get reference implementations or get removed
- Docker compose for 60-second zero-pip-install demo
- LangChain + CrewAI adapter modules
- Terraform module sketch for the IdP-bypass-authority resolver integration

## What this list does NOT do

- Does not enumerate every possible adversarial input or threat model
- Does not address vertical-specific regulatory regimes outside CRE (PCI DSS, HIPAA, DORA, etc.)
- Does not replace a security-review or threat-modeling engagement

If you identify a limitation worth adding to this list, please open an issue at https://github.com/linus10x/cre-agent-audit/issues with the description and (where possible) a citation.
