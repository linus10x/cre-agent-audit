# Roadmap

## v0.2.0 — Foundation (released 2026-06-02)

- 9 governance patterns (ADR-0001 through ADR-0009) with bounded claims and primary-source-verified regulatory citations
- 2 design ADRs added from adversarial-review fold-in: ADR-0010 (Audit-Chain Retention/Privilege/Discovery Posture), ADR-0011 (Vendor-Output Adapter Pattern, design only)
- Zero runtime dependencies (stdlib only; YAML is author-time only via `scripts/build_compliance_json.py`)
- 142 unit tests · 89% branch coverage · ruff + `mypy --strict` clean
- Three runnable worked examples
- 9 per-pattern Control Description Tables (`docs/controls/CTRL-001..009.md`)
- Four-framework mapping matrix (`docs/MAPPING-MATRICES.md` — NIST AI RMF × ISO 42001 × COSO ICAIR × Big-4 standard taxonomy)
- Drop-in vendor-clause templates for screening, abstraction, pricing
- PE due-diligence 10-question checklist
- 90-day deployment cadence walkthrough (`examples/FIRST_90_DAYS.md`)
- Three FINOS-format contributory control drafts (`governance-artifacts/`) with explicit non-endorsement provenance
- DISCLAIMER.md, LIMITATIONS.md, PRIOR-ART.md
- Sibling cross-link to `linus10x/finserv-agent-audit`

## v0.2.1 — Adversarial-review follow-ups (released 2026-05-28; tag `v0.2.1`; DOI [10.5281/zenodo.20434575](https://doi.org/10.5281/zenodo.20434575))

The 5-chamber adversarial review (PE op-partner, Big-4 AI-audit partner, AI-governance attorney, CRE-vertical CTO, algorithmic-fairness academic) surfaced 33 findings; 26 folded into v0.2.0; 7 deferred to v0.2.1. PR #31 merged 2026-05-28 closed 4 of the 7 plus 2 added during PR 3 (ADR-0013 MI Proxy + the consolidated `AuditConsumer`). 3 items remain for v0.2.2.

### Landed in `v0.2.1`

- ✅ **Pluggable persistence backend** for `AuditLedger` — `LedgerStore` Protocol + `InMemoryLedgerStore` / `SqliteLedgerStore` / `JsonlLedgerStore` (ADR-0012 § Seam 1)
- ✅ **RFC 3161 trusted-timestamp integration** — `TimestampSource` Protocol + `LocalClockTimestampSource` / `RFC3161TimestampSource` + stdlib DER ASN.1 codec (ADR-0012 § Seam 2)
- ✅ **OpenTimestamps / Sigstore Rekor witness-anchor reference integration** — `WitnessRegister` Protocol + `RekorWitness` / `OpenTimestampsWitness` + `anchor_to_witness()` (ADR-0012 § Seam 3)
- ✅ **`VendorScoreGate` concrete implementation** — Protocol + `InMemoryVendorScoreGate` default + score-drift detection with fail-closed default (ADR-0011 update; FAILURE-MODES.md Row 8)
- ✅ **Full negative-results / failure-mode appendix** — repo-root `FAILURE-MODES.md` matrix across 8 classes + drift-detection test enforcing doc/code parity
- ✅ **(added in PR 3) ADR-0013 — MI Proxy** — out-of-band verifier chain-of-custody; `LocalMIProxy` HMAC default; `AuditLedger.verify_chain(mi_proxy=...)` fail-closed hook
- ✅ **(added in PR 3) Consolidated `AuditConsumer` base** — the three ADR-0012 seams + MI Proxy + VendorScoreGate inject through one interface

## v0.2.2 — In flight on `main` as `0.2.2.dev0` (target: 2026-Q3)

The 3 items deferred from the original 7 `SHIP-RECEIPT.md` v0.2.1 follow-up list:

- **MI-threshold learned-proxy detection** in `fair_housing_preflight.py` (mutual-information based; ADR-0008 update) + SafeRent-shaped synthetic fixture. **Distinct from the Module Integrity Proxy that shipped under ADR-0013.**
- **`audit-verify` extra wiring** — `rfc3161_verify.py` signature-chain validation behind `pyca/cryptography`
- **Named-GC reference quotes**

## v0.3.0 — Production-deployment hardening (target: 2026-Q4)

- **Full ISO/IEC 42001:2023 + COSO ICAIR overlay** at per-pattern subcategory cell-level (v0.2.0 ships a condensed single-doc matrix; v0.3 ships full per-pattern mapping)
- **Five state regulatory mappings** (TX, NY, CA, WA, FL) tracked as community good-first-issues; primary-source citation required per PR
- **`agents/` subpackage cleanup** — v0.2.1 consolidated the two real audit-chain consumers (`audit`, `monitor`) behind the `AuditConsumer` base. v0.3 prunes the unused domain stubs (`strategy`, `risk`, `domain_intelligence`) and promotes `orchestrator` to a functional implementation (likely under ADR-0014).
- **LangChain + CrewAI adapters** for agent-orchestration framework users
- **Async pattern variants** for high-volume decision surfaces
- **Docker compose for 60-sec zero-pip-install demo**
- **`governance-as-a-service` HTTP wrapper** for polyglot consumers (Go, Java, .NET shops)
- **Terraform module sketch** for the IdP-bypass-authority resolver integration (Okta + Azure AD reference)

## v0.4.0 — Public distribution + ecosystem (target: 2027-Q1)

- **PyPI publication** with full release-pipeline integration
- **FINOS AIR Working Group submission** — full 19-artifact submission package, on-WG-track (post Week-7 fill-in completing on the `finos-submission-wip` private branch)
- **Mermaid sequence diagrams** for all 9 patterns
- **Lease-abstraction litigation-discovery worked example** under `examples/04_lease_provenance_discovery/`

## Community Requests (un-prioritized)

- Adapters for additional agent-orchestration frameworks (AutoGen, AG2, Semantic Kernel)
- DORA Article 23/24 (digital-operational-resilience) mapping
- AWS Lambda + Azure Functions deployment recipes
- Insurance vertical variant — fork to `linus10x/insurance-agent-audit`
- Healthcare vertical variant — fork to `linus10x/health-agent-audit`
- Multi-language lease-abstraction provenance (current English-only)
- AI fraud-detection on rental applications (synthetic-ID + stolen-voucher class)

## Contribution path

PRs are most welcome for state regulatory mappings, primary-source citation corrections, vendor-clause template additions, and ADR boundary clarifications. See [`CONTRIBUTING.md`](CONTRIBUTING.md). Good-first-issues are labeled `good first issue` on GitHub.
