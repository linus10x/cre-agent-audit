#!/usr/bin/env bash
# file_initial_issues.sh — Files the council-prioritized P0 + P1 issues to
# github.com/linus10x/cre-agent-audit. Run AFTER `git push -u origin main`.
#
# Per Memos/GitHub_Issues_Backlog_2026-05-22.md · council 9.86/10 · 5/5 affirm.

set -euo pipefail

REPO="linus10x/cre-agent-audit"

echo "=== Creating labels ==="
gh label create "v0.2.1" --repo "$REPO" --description "Patches before Mon Jun 2 / shortly after" --color "0E8A16" 2>/dev/null || true
gh label create "v0.2.x" --repo "$REPO" --description "Patches in the v0.2 cycle" --color "5319E7" 2>/dev/null || true
gh label create "v0.3" --repo "$REPO" --description "Roadmap items for the next major" --color "C5DEF5" 2>/dev/null || true
gh label create "regulatory-coverage" --repo "$REPO" --description "Adds or refines a regulatory mapping" --color "D93F0B" 2>/dev/null || true
gh label create "gtm" --repo "$REPO" --description "Brand or go-to-market enabler" --color "FBCA04" 2>/dev/null || true
gh label create "quality" --repo "$REPO" --description "Test coverage / property tests / lint" --color "BFD4F2" 2>/dev/null || true
gh label create "community-contribution" --repo "$REPO" --description "Designed for outside PRs" --color "7057FF" 2>/dev/null || true
gh label create "wontfix-candidate" --repo "$REPO" --description "Under review for wontfix" --color "808080" 2>/dev/null || true

echo "=== P0 · I-01 · NIST + Treasury FS AI RMF mapping ==="
gh issue create --repo "$REPO" \
  --title "Map all 9 patterns to NIST AI RMF functions + Treasury FS AI RMF 230 control IDs" \
  --label "enhancement,v0.2.1,gtm" \
  --body "Per Gap-Finding G-58, the credibility anchor for Private Capital buyer conversations is a published map from each governance pattern to (a) the NIST AI RMF function it satisfies (GOVERN · MAP · MEASURE · MANAGE) and (b) the specific Treasury Financial Services AI RMF control ID range (released Feb 19, 2026 — 230 control objectives total).

Today \`config/compliance_rules.yaml\` carries jurisdiction + statute + clause per pattern but does not surface NIST function or Treasury FS AI RMF control IDs as queryable fields.

**Scope of work:**
1. Extend the YAML schema to add \`nist_ai_rmf_function\` (GOVERN / MAP / MEASURE / MANAGE) and \`treasury_fs_ai_rmf_controls\` (list of control IDs) under each regulation entry.
2. Populate the mapping for all 9 patterns (ADR-0001 through ADR-0009).
3. Add a \`Mapping\` section to the README that renders the table.
4. Add a \`RegulationLoader.nist_functions_for(pattern)\` + \`RegulationLoader.treasury_controls_for(pattern)\` lookup convenience.
5. Update the README's existing 9-pattern table to add NIST function + Treasury control range columns.

**Acceptance:**
- \`compliance_rules.yaml\` validates against the existing \`InvalidComplianceRulesError\` checks
- Every pattern has at least one NIST function + at least one Treasury control range entry
- README renders correctly with the new columns
- Test coverage on \`regulation_loader.py\` remains 100%

Priority: P0 (v0.2.1). NAV score 24/27. Council 9.86/10 · 5/5 affirm."

echo "=== P0 · I-02 · CONTRIBUTING.md + SECURITY.md ==="
gh issue create --repo "$REPO" \
  --title "Add CONTRIBUTING.md and SECURITY.md for the Mon Jun 2 public flip" \
  --label "documentation,v0.2.1" \
  --body "Table stakes before flipping the repo from private to public. A recruiter or buyer who lands on the repo for the first time should see (a) clear contribution guidelines and (b) a security-disclosure policy.

**\`CONTRIBUTING.md\` minimal content:**
1. How to file a regulatory-coverage PR (statute citation + test required)
2. How to file an adversarial test case (issue first, PR with passing test second)
3. Code style (ruff + mypy strict + DCO sign-off on commits)
4. ADR additions process (one PR per ADR proposal; council bar 9.5+ before merge)
5. Test discipline (TDD, RED-GREEN-REFACTOR, 85%+ coverage on new modules)

**\`SECURITY.md\` minimal content:**
1. Supported versions (v0.2.x · main)
2. Reporting channel: GitHub security advisory (private)
3. Response SLA: acknowledge within 72 hours, triage within 1 week
4. Disclosure timeline: 90 days from acknowledgment unless agreed otherwise
5. Out of scope: third-party integrations (e.g., named PMS/IWMS adapters)

**Acceptance:**
- Both files committed to repo root
- GitHub 'Community Standards' health-check shows both as ✓

Priority: P0 (v0.2.1). NAV score 25/27. Council 9.86/10."

echo "=== P0 · I-03 · Cross-link to sibling finserv-agent-audit ==="
gh issue create --repo "$REPO" \
  --title "Cross-link README to sibling finserv-agent-audit repo" \
  --label "documentation,v0.2.1" \
  --body "The Autonomy Ladder™ brand operates two MIT-licensed reference repos — \`finserv-agent-audit\` (Financial Services + Private Capital) and \`cre-agent-audit\` (Commercial Real Estate). The README's 'Related' section already lists both but the 'Six patterns inherited from finserv-agent-audit' framing in the Patterns table should link each inherited pattern (ADR-0001 through ADR-0006) to the corresponding sibling ADR.

**Acceptance:**
- Each inherited-pattern row in the 9-pattern table links to the sibling repo's ADR
- The 'Related' section ends with a link to \`finserv-agent-audit/docs/adr/private-capital/\` once that subdirectory is merged upstream

Priority: P0. Composite 23/27."

echo "=== P0 · I-04 · Pin Article 2 LinkedIn URL ==="
gh issue create --repo "$REPO" \
  --title "Pin Article 2 LinkedIn URL in README Related section after Jun 2 publish" \
  --label "documentation,v0.2.1,gtm" \
  --body "Article 2 (*I built the CRE-Agent-Audit governance kit in one weekend. Three settled cases told me what to build.*) publishes Mon Jun 2, 2026 at 8:00 AM CT on LinkedIn. After publish, capture the post URL and add it to the README's 'Related' section as the first entry.

**Acceptance:**
- Article 2 LinkedIn URL added to README Related section
- Commit message references Article 2 publish date

Priority: P0. Composite 23/27."

echo "=== P1 · I-05 · FINOS AIR submission ==="
gh issue create --repo "$REPO" \
  --title "Submit Autonomy Ladder™ patterns to FINOS AI Governance Framework (18-file PR)" \
  --label "enhancement,v0.2.1,gtm" \
  --body "Per Brand Unbeatable Supplement Move 1 (council 9.74/10), submit all 9 governance patterns to the FINOS AI Risk Governance Framework taxonomy at \`github.com/finos/ai-governance-framework\`. Earn industry-consortium co-branding (Citi · Goldman Sachs · Morgan Stanley · JPMorgan Chase · BNY Mellon · Barclays · Microsoft are FINOS members).

**Scope:** 9 risk markdown files + 9 mitigation markdown files = 18-file PR. Outline at \`Memos/FINOS_AIR_Submission_Outline_v0_2026-05-22.md\` in the parent project.

Taxonomy mapping (per outline):
- 4 entries under \`risks/operational/\` (DEFCON · Audit Chain · Shadow Mode · Lease Provenance)
- 4 entries under \`risks/regulatory-and-compliance/\` (Sovereign Veto · Autonomy Ladder · Regulation Mapping · Fair Housing)
- 1 entry under \`risks/security/\` (Tenant PII Residency)
- 9 corresponding mitigation entries crediting Autonomy Ladder™

**Acceptance:**
- PR opened against \`finos/ai-governance-framework\` with DCO-signed commits
- All 18 markdown files conform to the templates in \`templates-for-ri-md/\`
- PR description links to autonomy-ladder.io and this repo

Priority: P1. Composite 19/27."

echo "=== P1 · I-06 · Per-clause-kind typed schemas ==="
gh issue create --repo "$REPO" \
  --title "Per-clause-kind typed schemas (rent_amount · escalation_rate · break_date · co_tenancy · options_to_renew · jurisdiction · outgoings)" \
  --label "enhancement,v0.2.1" \
  --body "ADR-0007 names seven material clause kinds. \`src/schemas/lease_clause.py\` ships \`ClauseSchema = dict[str, Any]\` in v0.2 with a docstring acknowledging the v0.2.x patch.

Each clause kind needs its own typed slot structure so the lease provenance check can validate clause-internal completeness (e.g., a \`break_clause\` schema without \`conditions\` is itself a veto candidate).

**Scope:**
1. Add \`RentScheduleSlots\`, \`BreakClauseSlots\`, \`OptionsToRenewSlots\`, etc. as frozen dataclasses
2. Extend \`ExtractedClause.schema\` to be a union of these typed slot structures, dispatched by \`criticality + clause_kind\`
3. Add structural validation hooks in \`LeaseProvenanceCheck\` for missing slot fields per kind
4. New veto reason code: \`PROV-INCOMPLETE-SLOT\` for kind-specific missing slots

Priority: P1. Composite 16/27."

echo "=== P1 · I-07 · Orchestrator wiring ==="
gh issue create --repo "$REPO" \
  --title "Wire OrchestratorAgent against the full compose order end-to-end" \
  --label "enhancement,v0.2.1" \
  --body "\`OrchestratorAgent.process()\` returns \`None\` in v0.2. The full compose order per ARCHITECTURE.md is documented but unwired:

\`\`\`
DEFCON → Domain pre-flight → Sovereign Veto → Autonomy Ladder gate → Shadow Mode → Audit write → ACTION
\`\`\`

**Scope:**
1. Implement the full pipeline in \`OrchestratorAgent.process\`
2. Add one orchestrator-driven end-to-end example to \`examples/\`
3. Add integration tests covering the compose-order short-circuit behaviors (DEFCON denies → skip everything; Sovereign Veto vetoes → audit-write + halt)
4. Add a sequence diagram to ARCHITECTURE.md showing the compose order

Priority: P1. Composite 16/27."

echo "=== P1 · I-08 · Adversarial test corpus ==="
gh issue create --repo "$REPO" \
  --title "Build a community-curated adversarial test corpus across all 9 patterns" \
  --label "good first issue,help wanted,enhancement,v0.2.x" \
  --body "ADR-0007 and ARCHITECTURE.md both name the adversarial test corpus as 'the single most-needed contribution.' A community-built corpus of adversarial inputs that exercises every veto reason code across all 9 patterns hardens v0.2 into v0.3.

**How to contribute (per CONTRIBUTING.md):**
1. Pick one veto reason code (e.g., FHA-VOUCHER, PROV-HASH-MISMATCH, RESIDENCY-CROSS-JURISDICTION-UNTAGGED)
2. Construct an adversarial input that exercises an edge case
3. Add it to \`tests/adversarial_corpus/<reason_code>.py\`
4. PR with the new test passing

**Acceptance for issue close:**
- At least 3 adversarial cases per reason code (≈45 cases total)
- All cases live in \`tests/adversarial_corpus/\`
- CI runs the corpus as a separate test selection (\`pytest tests/adversarial_corpus/\`)

Priority: P1. Composite 19/27. Community contribution magnet."

echo "=== P1 · I-09 · State-by-state SOI ordinance mapping ==="
gh issue create --repo "$REPO" \
  --title "Add per-state Source-of-Income ordinance mappings (NY · CA · MA · MN · Minneapolis · Seattle)" \
  --label "good first issue,regulatory-coverage,v0.2.x" \
  --body "ADR-0008's \`FHA-SOI\` check uses a federal-level default + Colorado as the only state. State-level SOI ordinances exist in NY · CA · CT · DC · MA · MN · NJ · NY · OR · VT · WA plus municipal layers (NYC · SF · Seattle · Minneapolis · Portland · etc.).

**How to contribute:**
1. Pick one jurisdiction
2. Cite the specific statute or ordinance (with section number)
3. Add a \`JurisdictionRules\` entry to the default registry with the SOI protections + criminal-history lookback + proxy-feature list for that jurisdiction
4. Add tests covering the new jurisdiction's specific rules
5. PR with regulatory citation in the description

**Acceptance for issue close:**
- At least 8 state-level + 4 municipal-level jurisdictions mapped
- Each entry has at least one passing test demonstrating its specific rule
- \`compliance_rules.yaml\` reflects every added jurisdiction

Priority: P1. Composite 17/27."

echo "=== P1 · I-16 · Diagnostic SOW template ==="
gh issue create --repo "$REPO" \
  --title "Add Diagnostic SOW template under docs/templates/ for the \$5K Diagnostic SKU" \
  --label "documentation,enhancement,v0.2.1,gtm" \
  --body "\$5K Diagnostic SKU support. Operators who fork the repo and want to deliver Diagnostics on the Autonomy Ladder™ framework need a starting template.

**Scope:**
1. Create \`docs/templates/diagnostic_sow.md\` with the 22-question intake structure
2. Create \`docs/templates/diagnostic_output_redyellowgreen.md\` for the 8-page report structure
3. Link from README under a new 'Practitioner Resources' section

Priority: P1 (council promoted from P2 by Adler). Composite 17/27."

echo
echo "=== Done. Now go to https://github.com/$REPO/issues to verify all 9 issues filed. ==="
echo
echo "P2 issues are queued in Memos/GitHub_Issues_Backlog_2026-05-22.md and"
echo "should be filed in batch next session once Kunjar adds the first PR comments."
