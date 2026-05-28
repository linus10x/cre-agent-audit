# governance-artifacts/

Three completed, review-defensible governance-control drafts authored as contributory artifacts for the [FINOS AI Risk Initiative](https://air.finos.org/) — the financial-services industry's open-source AI risk-control catalog. Released here under MIT alongside the pattern primitives they describe.

## What is in this folder

- **`AIR-RC-004-sovereign-veto.md`** — Regulatory-Compliance control: human-only kill switch on consequential AI decisions. Maps to ADR-0002 and `src/cre_agent_audit/governance/sovereign_veto.py`.
- **`AIR-RC-007-fair-housing.md`** — Regulatory-Compliance control: Fair-Housing Pre-Flight gate for tenant-screening AI. Maps to ADR-0008 and `src/cre_agent_audit/governance/fair_housing_preflight.py`.
- **`AIR-MIT-RC-VETO-01-sovereign-veto.md`** — Mitigation drafted against AIR-RC-004.

## What the prefixes mean (for non-FINOS readers)

The FINOS AIR catalog uses a structured naming convention:

| Prefix | Meaning |
|---|---|
| `AIR-RC-NNN` | A regulatory-compliance risk in the AIR catalog (with an author's working number) |
| `AIR-OP-NNN` | An operational risk in the AIR catalog |
| `AIR-SEC-NNN` | A security risk in the AIR catalog |
| `AIR-MIT-RC-NNN-NN` | A mitigation drafted against a regulatory-compliance risk |
| `AIR-MIT-OP-NNN-NN` | A mitigation drafted against an operational risk |

The numbers in this folder are the author's internal IDs from the working-group submission package, not assigned FINOS catalog identifiers.

## What you can do with these files

- **Fork** them into your own control library
- **Cite** them in your AI risk register (with attribution to this repository's commit SHA + date)
- **Adapt** them to your jurisdictions, vendor surface, or risk-appetite framing
- **Submit a PR** here if you find a factual error or want to extend the control's evidence-of-operation guidance

## What you should NOT do with these files

- **Do not infer FINOS endorsement.** These drafts have **not been reviewed, endorsed, or accepted by FINOS or the AIR Working Group** as of v0.2.0. They are released independently under MIT.
- **Do not represent them as adopted FINOS catalog entries.** When the WG adopts a control, it carries an official FINOS-assigned ID and lives in the AIR catalog itself, not in this folder.

## What's NOT in this folder by design

The full 19-artifact submission package — including 16 additional risk and mitigation files in author-draft form — is held in **local working copies only**, pending Week-7 fill-in and the FINOS Working-Group PR + review process. The three files in this folder are the only three that are author-complete to a release-defensible standard. The remainder will be contributed through the FINOS PR + working-group review path on their own timeline.

**Historical-commit acknowledgement (transparency note).** The 16 draft files were committed to this repository's main branch *before* the public-visibility flip on 2026-05-28 and therefore exist in the repository's git history at commit `e9d2f6e` (the pre-Stage-5-removal main HEAD). They are not part of the current main tree (removed in the Stage 5 governance carve-out — see [`docs/SHIP-RECEIPT.md`](../docs/SHIP-RECEIPT.md)) and are not browsable from the default tree view. The author chose not to rewrite git history to remove the historical commit — public hashes are permanent references and rewriting history breaks downstream consumers. The draft files in that historical commit are author-draft only; they have not been reviewed, endorsed, or accepted by FINOS or the AIR Working Group at any point. Adopters who encounter the historical commit content should treat those 16 files as identical in status to any author-draft work — useful as design context, not as adopted catalog entries.

See [`docs/FINOS-SUBMISSION-CADENCE.md`](../docs/FINOS-SUBMISSION-CADENCE.md) for the Week-7 fill-in workflow and the WG-bound submission path.

## Relation to this repo's patterns

These three artifacts describe controls in the FINOS AIR format. The implementation of each control lives in this repo's `src/cre_agent_audit/governance/` subpackage, with full architectural reasoning in the corresponding ADR (`docs/adr/0002-sovereign-veto.md` for the veto, `docs/adr/0008-fair-housing-preflight-gate.md` for the fair-housing gate). The mapping into Big-4 / ISO 42001 / COSO ICAIR audit frameworks lives in [`../docs/MAPPING-MATRICES.md`](../docs/MAPPING-MATRICES.md) and the per-pattern Control Description Tables in [`../docs/controls/`](../docs/controls/).

See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md) for the full not-legal-advice, not-FINOS-endorsement, MIT-warranty-disclaimer statement.
