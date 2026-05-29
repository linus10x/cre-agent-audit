# Audit System Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the entire cre-agent-audit ecosystem — (A) the V3 Truth-Seeker audit prompt in `creaudit.md`, (B) the v0.2.0 OSS repo it audits, and (C) the recursion loop that connects audit → fix-session → re-audit closure — so the same audit can be re-run after remediation and verify closure mechanically.

**Architecture:** Three independent tracks. Track A edits a single 60KB prompt file. Track B refactors `AuditLedger` behind a `LedgerStore` Protocol, adds MI-threshold proxy detection, RFC 3161 trusted timestamps, OpenTimestamps/Sigstore Rekor witness anchoring, a concrete `VendorScoreGate`, prunes three speculative agent stubs and completes orchestrator + monitor, then ships per-pattern failure-modes appendix + ISO 42001 sub-clause expansion + 5 state regulatory mappings + LangChain/CrewAI adapters. Track C operationalizes the recursion loop with a machine-verifiable acceptance-criterion grammar, a `render_findings_db.py` extractor, a `verify_acceptance_criterion.sh` runner, and a CI smoke check.

**Tech Stack:** Python 3.10+, stdlib-only runtime (no new runtime deps; load-bearing for the project's Zero-Dependencies badge), pytest, mypy `--strict`, ruff. Markdown for prose artifacts.

**Context for why this work:** v0.2.0 shipped 2026-05-28 with 142 tests + 89% branch coverage; a 5-chamber adversarial review surfaced 33 findings — 26 folded into v0.2.0 and **7 explicitly deferred to v0.2.1** (named in `docs/SHIP-RECEIPT.md`). The V3 Truth-Seeker prompt in `creaudit.md` targets a `v0.3.0 expected state` that does not exist yet, has stale failure-mode probes (RealPage as consent decree was already fixed), and asserts recursion-safety without giving an operationalizable acceptance-criterion grammar. This plan folds all 7 deferred items + selected v0.3.0 roadmap items, tightens the prompt against the actual `v0.2.0` baseline, and turns the prompt's "recursion-safe re-audit" claim into a runnable protocol.

**Hard constraints:**
- Zero runtime dependencies on the `cre_agent_audit` package. Optional integrations go in `pyproject.toml` `[project.optional-dependencies]`.
- MIT licensed; `mypy --strict` clean; `ruff check` clean; pytest ≥85% branch coverage on every commit.
- Every new pattern needs: source module, unit-test file, ADR (or updated ADR), CHANGELOG entry, control-description-table update, LIMITATIONS.md scope update.
- creaudit.md remains a **single file** droppable into a fresh LLM session with web/git access — no MCP, no sidecars.

---

## File Structure

### Track A — Prompt hardening (1 file modified)
- `creaudit.md` — edits at lines 4, 66, 69, 87, 91, 104, 106, 108, 145, 154, 264, 411–448, 454, 491, 567, 610, 622

### Track B — Repo hardening

**Source (new — 14 files):**
- `src/cre_agent_audit/governance/mi_proxy_detector.py` — stdlib mutual-information learned-proxy detector
- `src/cre_agent_audit/governance/ledger_store.py` — `LedgerStore` Protocol + `InMemoryLedgerStore`
- `src/cre_agent_audit/governance/ledger_store_sqlite.py` — stdlib `sqlite3` backend
- `src/cre_agent_audit/governance/ledger_store_jsonl.py` — append-only JSONL backend
- `src/cre_agent_audit/governance/timestamp_source.py` — `TimestampSource` Protocol + `LocalClockTimestampSource` + `RFC3161TimestampSource`
- `src/cre_agent_audit/governance/rfc3161_codec.py` — minimal DER ASN.1 codec for RFC 3161 TSQ/TSR
- `src/cre_agent_audit/governance/witness_anchor.py` — `RekorWitness`, `OpenTimestampsWitness`, `anchor_to_witness()`
- `src/cre_agent_audit/governance/vendor_score_gate.py` — concrete `VendorScoreGate` per ADR-0011
- `src/cre_agent_audit/governance/monitor_alerts.py` — alert codes + scanners for monitor agent
- `src/cre_agent_audit/schemas/vendor_output.py` — `VendorOutput`, `ApplicantContext`, `Decision`, `VendorRecommendation`
- `src/cre_agent_audit/adapters/__init__.py` — empty marker
- `src/cre_agent_audit/adapters/langchain_adapter.py` — `TYPE_CHECKING`-guarded LangChain adapter
- `src/cre_agent_audit/adapters/crewai_adapter.py` — `TYPE_CHECKING`-guarded CrewAI adapter
- `src/cre_agent_audit/governance/rfc3161_verify.py` — optional verification (requires `audit-verify` extra)

**Source (modified):**
- `src/cre_agent_audit/governance/audit_chain.py` — swap `_entries: list[AuditEntry]` for `_store: LedgerStore`; add `timestamp_source` parameter; thread `TrustedTimestamp` into entries
- `src/cre_agent_audit/governance/fair_housing_preflight.py` — add optional `mi_proxy_detector` field + `FHA-MI-PROXY` check between FHA-PROXY and FHA-VOUCHER
- `src/cre_agent_audit/agents/orchestrator.py` — replace stub with functional compose-order implementation
- `src/cre_agent_audit/agents/monitor.py` — replace stub with anomaly scanner
- `src/cre_agent_audit/__init__.py` — export new public names

**Source (deleted with deprecation cycle):**
- `src/cre_agent_audit/agents/strategy.py`
- `src/cre_agent_audit/agents/risk.py`
- `src/cre_agent_audit/agents/domain_intelligence.py`

**Tests (new — 12 files + fixtures):**
- `tests/test_mi_proxy_detector.py`
- `tests/test_ledger_store_inmemory.py`
- `tests/test_ledger_store_sqlite.py`
- `tests/test_ledger_store_jsonl.py`
- `tests/test_timestamp_source.py`
- `tests/test_rfc3161_codec.py`
- `tests/test_witness_anchor.py`
- `tests/test_vendor_score_gate.py`
- `tests/test_orchestrator.py`
- `tests/test_monitor.py`
- `tests/failure_modes/test_pattern_*.py` (9 files)
- `tests/fixtures/saferent_synthetic.py`, `tests/fixtures/rfc3161_tsr_sample.der`

**Docs (new — 5 files):**
- `docs/FAILURE-MODES.md`
- `docs/adr/0012-persistence-witness-timestamp-pattern.md`
- `docs/adr/0013-agent-topology-pruning.md`
- `docs/iso-42001-clauses.md`
- `docs/state-coverage.md`

**Docs (modified):**
- `docs/adr/0003-hash-chain-audit.md`, `docs/adr/0008-fair-housing-preflight-gate.md`, `docs/adr/0011-vendor-output-adapter-pattern.md`
- `docs/LIMITATIONS.md`, `docs/MAPPING-MATRICES.md`, `docs/controls/CTRL-003.md`, `CTRL-008.md`, `CTRL-011.md`
- `ROADMAP.md`, `CHANGELOG.md`, `README.md`, `ARCHITECTURE.md`

**Config (modified):** `config/compliance_rules.yaml`, `config/compliance_rules.json`, `pyproject.toml`

**Examples (new):** `examples/04_vendor_score_gate/run.py` + README, `examples/05_witness_anchor/run.py`

### Track C — Recursion loop (4 files new, 1 workflow)
- `scripts/render_findings_db.py` — extracts YAML findings_db block from audit report
- `scripts/verify_acceptance_criterion.py` — executes one acceptance-criterion predicate, returns exit code
- `docs/AUDIT-RECURSION.md` — full protocol doc
- `tests/test_acceptance_criterion_parser.py` — unit tests for criterion grammar
- `.github/workflows/audit-recursion-smoke.yml` — CI smoke that exercises a dry-run finding → fix → close cycle

---

## Sequencing and Commit Boundaries

Tracks A and C can run fully parallel to Track B. Inside Track B, **PR 1 (storage foundation) must land first**; the rest parallelizes.

- **PR 1 — Storage foundation** (Track B tasks B1–B4): `LedgerStore` Protocol, in-memory + SQLite + JSONL backends, `AuditLedger` refactor.
- **PR 2 — Trusted timestamps + witness anchor** (B5–B10): `TimestampSource`, `rfc3161_codec`, `RFC3161TimestampSource`, `witness_anchor`. Depends on PR 1.
- **PR 3 — MI proxy detector** (B11–B12): independent; parallelizable.
- **PR 4 — VendorScoreGate** (B13–B16): independent; parallelizable.
- **PR 5 — Agent topology cleanup** (B17–B19): independent; parallelizable.
- **PR 6 — Failure-modes appendix** (B22–B23): depends on PR 1–5.
- **PR 7 — Prompt hardening** (Track A entire): independent; parallel from day one.
- **PR 8 — Recursion loop** (Track C entire): independent from B; benefits from PR 7 landing first but does not block.
- **PR 9 — v0.3.0 items** (B24–B29): sequence after `v0.2.1` tag.

Tag **`v0.2.1`** after PR 1–6 + 7–8 land. Tag **`v0.3.0`** after PR 9.

---

# Track A — V3 Truth-Seeker Prompt Hardening

Edits the single file `creaudit.md`. All steps are read-edit-verify; no test code. Verification is `grep` for the expected substring and a manual re-read of the section.

---

### Task A1: Version-state alignment — repo-state mismatch

**Files:**
- Modify: `creaudit.md:87, 104, 106, 145, 264, 487`

- [ ] **Step 1: Read current lines 85-110 to confirm the expected-state block**

Run: `sed -n '85,110p' creaudit.md`
Expected output: lines starting with `# Context — repository under audit (v0.3.0 expected state)` and the 10-row patterns table.

- [ ] **Step 2: Replace the v0.3.0 expected-state heading with the v0.2.0 actual-state heading**

Edit `creaudit.md`:
- old_string: `# Context — repository under audit (v0.3.0 expected state)`
- new_string: `# Context — repository under audit (v0.2.0 actual state; v0.3.0 roadmap items called out per-row)`

- [ ] **Step 3: Correct Pattern 10's row in the patterns table**

Edit `creaudit.md`:
- old_string: `| 10 | Third-Party AI Governance Wrapper | docs/vendor_ai_governance.md | NEW in v0.3.0 |`
- new_string: `| 10 | Vendor-Output Adapter (design only in v0.2.0) | docs/adr/0011-vendor-output-adapter-pattern.md | DESIGN ADR shipped in v0.2.0; impl deferred to v0.3 per CHANGELOG |`

- [ ] **Step 4: Correct the "Plus" line for ADR-0010 + ADR-0011**

Edit `creaudit.md`:
- old_string: `**Plus:** ADR-0010 (discovery posture) — NEW in v0.3.0`
- new_string: `**Plus:** ADR-0010 (Audit-Chain Retention, Privilege & Discovery Posture) — shipped v0.2.0; ADR-0011 (Vendor-Output Adapter) shipped design-only v0.2.0`

- [ ] **Step 5: Replace the Python version claim**

Edit `creaudit.md`:
- old_string: `**Stack:** Python 3.12+ and 3.13. Zero runtime dependencies (badge must hold). MIT license. mypy strict, ruff, pytest with coverage ≥85% expected.`
- new_string: `**Stack:** Python 3.10+ (verify against `pyproject.toml` `requires-python`). Zero runtime dependencies — verify by parsing `pyproject.toml` `[project.dependencies]` is an empty list. MIT license. mypy strict, ruff, pytest with coverage ≥85% (v0.2.0 ships 89% / 142 tests — confirm via `.coverage` or CI badge).`

- [ ] **Step 6: Correct the release-tag completeness criterion**

Edit `creaudit.md`:
- old_string: `- [ ] 5+ good-first-issues seeded · 1+ Discussion thread · v0.3.0 release tagged · social card uploaded · Zenodo DOI minted and in CITATION.cff`
- new_string: `- [ ] 5+ good-first-issues seeded · 1+ Discussion thread · v0.2.0 release tagged (current state — verify via `git tag -l`; v0.3.0 NOT required for ship) · social card uploaded · Zenodo DOI minted and in CITATION.cff`

- [ ] **Step 7: Verify with grep**

Run: `grep -nE 'v0\.3\.0 expected state|NEW in v0\.3\.0' creaudit.md`
Expected: zero matches.

Run: `grep -nE 'Python 3\.12\+ and 3\.13' creaudit.md`
Expected: zero matches.

- [ ] **Step 8: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): align V3 prompt with v0.2.0 actual state"
```

---

### Task A2: Failure-mode probe pruning + freshening

**Files:**
- Modify: `creaudit.md:411-448`

- [ ] **Step 1: Read the current probe block**

Run: `sed -n '411,448p' creaudit.md`
Expected: P0/P1/P2/P3 probe lists.

- [ ] **Step 2: Downgrade the stale RealPage P0 probe**

Edit `creaudit.md`:
- old_string: `- RealPage referenced as "settled" / "consent decree" / "final judgment" — it is ongoing litigation`
- new_string: `- RealPage referenced as "settled" / "consent decree" / "final judgment" — it is ongoing litigation. NOTE: this was remediated pre-v0.2.0 per `docs/SHIP-RECEIPT.md` Stage 17 fix log; verify against current `README.md` + `CHANGELOG.md` before scoring as P0. If references survive only in `docs/SHIP-RECEIPT.md` itself as historical record, downgrade to P3.`

- [ ] **Step 3: Downgrade the stale Colorado SB 24-205 P0 probe**

Edit `creaudit.md`:
- old_string: `- Colorado SB 24-205 referenced as operative — it was stayed April 27, 2026; SB 189 is operative`
- new_string: `- Colorado SB 24-205 referenced as operative without stayed-status callout — verify against `config/compliance_rules.yaml` + `docs/adr/0005-eu-ai-act-mapping.md`. NOTE: v0.2.0 ships hedged framing per Stage 2c primary-source verification; if YAML/ADRs already reference SB24-205 with "stayed" callout AND SB 26-189 as follow-on, no finding.`

- [ ] **Step 4: Convert the Pattern 10 P1 probe to expected-state framing**

Edit `creaudit.md`:
- old_string: `- Pattern 10 (vendor wrapper) is docs-only, no actual wrapper code`
- new_string: `- Pattern 10 (vendor wrapper) is docs-only — expected in v0.2.0 per CHANGELOG and ROADMAP. Finding ONLY if `README.md` or any launch post implies an implementation exists. Verify against `src/cre_agent_audit/governance/` directory listing.`

- [ ] **Step 5: Insert the new adversarial probe block after line 435**

Edit `creaudit.md` — locate the existing P1 block (the one starting `P1 probes (significant overclaims or omissions):`) and append the following bullets at its end (before the P2 block):

- old_string: `- "Artifact that closes the gap" reads as party admission

P2 probes (cosmetic / minor):`
- new_string: `- "Artifact that closes the gap" reads as party admission
- Embedding-space proxy attack: does `src/cre_agent_audit/governance/fair_housing_preflight.py` rely solely on lexical token matching? Probe: `grep -nE 'embedding|cosine|vector' src/cre_agent_audit/governance/fair_housing_preflight.py`. Absent = P1, unless `docs/LIMITATIONS.md` names this and `tests/failure_modes/test_pattern_8.py` codifies the escape input.
- Ledger-rewrite attack: `audit_chain.py` exposes `chain_head()` — does any test cover the case where an attacker with full DB write access rewrites every entry including the head? Probe: `grep -rnE 'rewrite|tamper|attack' tests/`. Absence with no `docs/FAILURE-MODES.md` callout = P1.
- Vendor-output gaming: ADR-0011 — does it address vendor returning pre-laundered outputs (vendor scrubs adverse-action reason codes before surfacing to wrapper)? Probe: `grep -nE 'laundered|scrub|pre-cleaned' docs/adr/0011-*.md`. Absence = P1.
- Regulation-loader supply-chain: `compliance_rules.json` is generated from YAML — does CI verify the JSON in main matches a fresh build from YAML? Probe: read `.github/workflows/test.yml` for a JSON-sync step. Absence = P1.
- ADR vs code drift: every ADR claim must map to a test. Probe: for each ADR-NNNN, `grep -lE '<pattern_module_name>' tests/`. ADRs with zero test coverage = P1 each.
- Disclaimer placement drift: README lede contains a "five anchors" / credentials block. Probe: extract line number of first H2 (`grep -n '^## ' README.md | head -1`) and first "not legal advice" string (`grep -n 'not legal advice' README.md | head -1`). If disclaimer line > first-H2 line, P0.
- Zero-deps badge truthfulness: probe `pyproject.toml` `[project.dependencies]` is `[]` AND `requirements.txt` is absent OR empty AND every `from <thirdparty>` import in `src/` is guarded by `TYPE_CHECKING`. Any violation = P0.
- TypeStrict claim truthfulness: run `python -c "import subprocess; print(subprocess.run(['mypy', '--strict', 'src'], capture_output=True, text=True).returncode)"`. Non-zero = P0 finding against `README.md` mypy-strict badge.
- Coverage badge truthfulness: README badge claims a percentage; run `pytest --cov=src/cre_agent_audit --cov-report=term-missing`. Resulting coverage below badge minus 1% = P1.

P2 probes (cosmetic / minor):`

- [ ] **Step 6: Verify the probe block compiles structurally**

Run: `awk '/^# Failure-mode probes/,/^# Coverage matrix/' creaudit.md | grep -cE '^- '`
Expected: ≥ 25 bullets (was ≥ 18 before).

- [ ] **Step 7: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): prune stale probes; add 8 fresh adversarial probes"
```

---

### Task A3: Coverage matrix automation hooks

**Files:**
- Modify: `creaudit.md:450-458`

- [ ] **Step 1: Read the coverage-matrix block**

Run: `sed -n '450,460p' creaudit.md`
Expected: the existing `| File / Artifact | Read? | Lines / Sections audited | Per-chamber findings count | Status |` row.

- [ ] **Step 2: Replace the header with the verifiable header**

Edit `creaudit.md`:
- old_string: `| File / Artifact | Read? | Lines / Sections audited | Per-chamber findings count | Status |
|---|---|---|---|---|
| README.md | Y/N | e.g., "1-487 (all)" | e.g., "Researcher: 3, Attorney: 5, ..." | CHECKED / NOT-CHECKED / CANNOT-VERIFY |`
- new_string: `| File / Artifact | Read? | wc -l output | Lines audited | sha256 (first 12) | Per-chamber findings count | Status |
|---|---|---|---|---|---|---|
| README.md | Y/N | e.g., "487" (from `wc -l README.md`) | e.g., "1-487 (all)" | e.g., "a1b2c3d4e5f6" (from `shasum -a 256 README.md` first 12 chars) | e.g., "Researcher: 3, Attorney: 5, ..." | CHECKED / NOT-CHECKED / CANNOT-VERIFY |

Every row's `wc -l output` must be the actual file line count obtained via `wc -l <file>`. Every `Lines audited` range must be a subset of `[1, wc -l]`. Every `sha256` must be the actual digest computed against the cloned working tree at audit start (`git rev-parse HEAD` recorded once at the top of the matrix). Rows where these three columns are not present are forbidden — mark `CANNOT-VERIFY` and explain why in the Status cell.`

- [ ] **Step 3: Verify**

Run: `grep -c 'wc -l output' creaudit.md`
Expected: ≥1.

- [ ] **Step 4: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): coverage matrix requires wc -l + sha256 per row"
```

---

### Task A4: Acceptance-criterion grammar section

**Files:**
- Modify: `creaudit.md` — insert new section before Step 14 (line ~491)

- [ ] **Step 1: Locate the insertion point**

Run: `grep -n '^\*\*Step 14' creaudit.md`
Expected: one match around line 492.

- [ ] **Step 2: Insert the acceptance-criterion grammar section**

Edit `creaudit.md`:
- old_string: `**Step 14 — Findings table (claude-code-cli-consumable).**`
- new_string: `**Step 13.5 — Acceptance-criterion grammar (mandatory).**

Every finding's `Acceptance Criterion` field must be one of these machine-verifiable predicate forms. Free-text criteria are invalid and force the finding to `CANNOT-VERIFY`.

- `REGEX_PRESENT(file, "<regex>")` — file matches regex at least once
- `REGEX_ABSENT(file, "<regex>")` — file matches regex zero times
- `FILE_EXISTS(path)` — path exists in working tree
- `FILE_ABSENT(path)` — path does not exist in working tree
- `LINE_RANGE_DIFF(file, L1-L2, "<expected substring>")` — `file[L1:L2]` contains the substring
- `TEST_PASSES(test_id)` — `pytest -k <test_id>` exits 0
- `SHELL_EXIT_ZERO("<command>")` — command returns 0
- `SHA256_MATCH(file, "<digest>")` — file's SHA-256 matches the digest
- `COVERAGE_AT_LEAST(file, <pct>)` — `pytest --cov=<file>` reports ≥ pct

Compound predicates allowed with `AND` / `OR`. Example:

    REGEX_ABSENT(README.md, "consent decree") AND
    REGEX_PRESENT(README.md, "ongoing.*litigation")

Findings whose closure cannot be expressed in this grammar must be split into smaller findings until each component is verifiable, OR marked `severity: P3` and routed to the "style/voice polish" backlog (which does not gate ship).

**Step 14 — Findings table (claude-code-cli-consumable).**`

- [ ] **Step 3: Verify**

Run: `grep -c 'Acceptance-criterion grammar' creaudit.md`
Expected: ≥1.

- [ ] **Step 4: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): add machine-verifiable acceptance-criterion grammar"
```

---

### Task A5: Anti-confirmation-bias self-scoring rules

**Files:**
- Modify: `creaudit.md` — extend the 10-rule block (lines 46-68)

- [ ] **Step 1: Locate the end of rule 10**

Run: `grep -n 'Recursion safety' creaudit.md`
Expected: line ~68.

- [ ] **Step 2: Append rules 11 and 12**

Edit `creaudit.md`:
- old_string: `10. **Recursion safety.** The audit must be re-runnable after remediation. Findings must be specific enough that a follow-up audit can verify each one was addressed.`
- new_string: `10. **Recursion safety.** The audit must be re-runnable after remediation. Findings must be specific enough that a follow-up audit can verify each one was addressed. Every finding's `Acceptance Criterion` must conform to the grammar in Step 13.5.

11. **Bias-protocol self-scoring.** After producing each adversarial prelude, count the words. If under 200, the dimension restarts. Log the count in Appendix D as `D<n>_prelude_wordcount=<N>`. The symmetric-findings ratio per dimension must satisfy `0.8 ≤ strengths/weaknesses ≤ 1.25` — log as `D<n>_symmetry=<ratio>`. Any dimension outside this band restarts with a re-balanced finding list.

12. **Hostile-prior receipt.** After Step 10 (confirmation-bias self-check), list at least three sentences from your own report that the author would find uncomfortable to read. If you cannot, the audit fails the bias-protocol gate and the report must be regenerated from a stronger hostile prior.`

- [ ] **Step 3: Verify**

Run: `grep -cE '^11\. \*\*Bias-protocol|^12\. \*\*Hostile-prior' creaudit.md`
Expected: 2.

- [ ] **Step 4: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): add self-scoring + hostile-prior receipt rules 11-12"
```

---

### Task A6: Chamber-voice-divergence enforcement

**Files:**
- Modify: `creaudit.md` — extend rule 9 (line 66)

- [ ] **Step 1: Locate rule 9**

Run: `grep -n 'No homogenization' creaudit.md`
Expected: line ~66.

- [ ] **Step 2: Extend rule 9 with the verbatim-overlap check**

Edit `creaudit.md`:
- old_string: `9. **No homogenization.** The HN Skeptic writes like patio11 — terse, technical, named-failure-mode-driven. The Attorney writes like a Wachtell memo — formal, exposure-quantified, precedent-cited. The Researcher writes like a peer review — methodologically scrupulous, citation-demanding. Do not merge their voices.`
- new_string: `9. **No homogenization.** The HN Skeptic writes like patio11 — terse, technical, named-failure-mode-driven. The Attorney writes like a Wachtell memo — formal, exposure-quantified, precedent-cited. The Researcher writes like a peer review — methodologically scrupulous, citation-demanding. Do not merge their voices. Concretely: after writing the findings, run a self-diff. For every dimension, compare each chamber's finding-text against every other chamber's finding-text. If any pairwise verbatim-overlap exceeds 50% of token count, both chambers restart that dimension. Log overlap ratios per dimension in Appendix D as `D<n>_voice_overlap_max=<ratio>`. The threshold is strict — chambers may concur on a finding's existence while still expressing it in their own voice; identical sentences are a homogenization signal, not a concurrence signal.`

- [ ] **Step 3: Verify**

Run: `grep -c 'pairwise verbatim-overlap' creaudit.md`
Expected: 1.

- [ ] **Step 4: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): enforce chamber-voice-divergence via verbatim-overlap check"
```

---

### Task A7: 160-cell scoring matrix skeleton

**Files:**
- Modify: `creaudit.md:567`

- [ ] **Step 1: Locate the placeholder**

Run: `grep -n '## Scoring matrix' creaudit.md`
Expected: line ~566.

- [ ] **Step 2: Replace the placeholder with the literal skeleton**

Edit `creaudit.md`:
- old_string: `## Scoring matrix (16 perspectives × 10 dimensions = 160 cells)
[16-column × 10-row table]`
- new_string: `## Scoring matrix (16 perspectives × 10 dimensions = 160 cells)

Every cell must contain `<score 1-10>/<finding-ID anchor or "no-finding">`. A cell with `_` or empty content is itself a finding. Chambers: Res=Researcher, CTO=REIT/CRE-CTO, Big4=Big-4 Audit, Atty=Attorney, Brand=Brand-Positioning, HN=HN-Skeptic, Acq=Hostile-Acquirer, Plf=Plaintiff. Lenses: P=Practitioner, A=Auditor.

| Dim | Res-P | Res-A | CTO-P | CTO-A | Big4-P | Big4-A | Atty-P | Atty-A | Brand-P | Brand-A | HN-P | HN-A | Acq-P | Acq-A | Plf-P | Plf-A |
|-----|-------|-------|-------|-------|--------|--------|--------|--------|---------|---------|------|------|-------|-------|-------|-------|
| D1 Completeness | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |
| D2 Uniqueness | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |
| D3 Differentiation | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |
| D4 Sophistication | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |
| D5 Brand-Asset | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |
| D6 Code Quality | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |
| D7 Reg-Citation | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |
| D8 Disclaimer | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |
| D9 Adoptability | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |
| D10 Sign-off | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ | _/_ |

Every `_` must be replaced; every finding-ID anchor must point to a row in the Findings table (Section `Findings table (claude-code-cli-consumable)`).`

- [ ] **Step 3: Verify**

Run: `awk '/^## Scoring matrix/,/^## /' creaudit.md | grep -c '^| D'`
Expected: ≥10 rows.

- [ ] **Step 4: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): embed literal 160-cell matrix skeleton"
```

---

### Task A8: Fix-session kickoff prompt template

**Files:**
- Modify: `creaudit.md:610`

- [ ] **Step 1: Locate the placeholder**

Run: `grep -n '## Fix-session kickoff prompt' creaudit.md`
Expected: line ~609.

- [ ] **Step 2: Replace the placeholder with the literal kickoff prompt**

Edit `creaudit.md`:
- old_string: `## Fix-session kickoff prompt
[A self-contained Claude Code CLI prompt that the user pastes into a new session. It references this audit report by URL or path, instructs the next session to iterate through findings table row-by-row, applies fixes, and produces a closure-evidence log per finding.]`
- new_string: `## Fix-session kickoff prompt

Embed the following verbatim. The user pastes the block (between the BEGIN/END markers) into a fresh Claude Code CLI session at the repo root.

\`\`\`
===== FIX-SESSION KICKOFF (paste into Claude Code CLI at repo root) =====

You are operating against the cre-agent-audit working tree at $(pwd). The
audit report you are remediating is at docs/AUDIT-FINDINGS-<ISO-DATE>.md and
contains a YAML findings block under the heading
"## findings_db (machine-readable)".

Procedure (loop until findings_db is empty of open items):

1. Parse the findings_db YAML. Select the next finding where
   closure_status == "open", ordered by severity (P0 -> P3) then by id.

2. Read finding.file at finding.lines. Read any related test files.

3. Apply the minimal edit that satisfies finding.acceptance_criterion.
   Do not refactor adjacent code. Do not introduce new runtime dependencies
   (the Zero-Deps badge is load-bearing).

4. Run the acceptance criterion as a shell verification using
   scripts/verify_acceptance_criterion.py:
     python scripts/verify_acceptance_criterion.py "<criterion>"

   The script returns exit 0 on pass, non-zero on fail. Predicate map:
     REGEX_PRESENT    -> grep -Ec '<regex>' <file>  (expect >=1)
     REGEX_ABSENT     -> grep -Ec '<regex>' <file>  (expect 0)
     FILE_EXISTS      -> test -e <path>
     FILE_ABSENT      -> ! test -e <path>
     LINE_RANGE_DIFF  -> sed -n 'L1,L2p' <file> | grep -F '<sub>'
     TEST_PASSES      -> pytest -k <test_id> -q
     SHELL_EXIT_ZERO  -> run as given
     SHA256_MATCH     -> shasum -a 256 <file> begins with <digest>
     COVERAGE_AT_LEAST-> pytest --cov=<file> --cov-fail-under=<pct>

5. If verification fails, revert and either (a) refine the edit or
   (b) mark finding.closure_status = "blocked" with a one-line reason.

6. If verification passes, append to docs/CLOSURE-EVIDENCE-<DATE>.log:
     finding_id | <id>
     verification | <exact command run>
     command_exit | <code>
     command_stdout_first_line | <line>
     commit_sha | <git rev-parse HEAD>
     closure_date | <ISO-8601>

7. Stage + commit with message: "fix(<finding.id>): <one-line>".
   Update findings_db YAML: closure_status = "closed",
   closure_evidence = "<commit_sha>:<verification_command>",
   closure_date = "<ISO-8601>".

8. After every 5 closures OR all P0/P1 closures, regenerate the
   findings_db block by running:
     python scripts/render_findings_db.py docs/AUDIT-FINDINGS-<DATE>.md

Recursion-safe re-audit trigger condition: when all P0 and P1 findings
show closure_status == "closed" AND CI is green on HEAD, emit this exact
string to stdout and halt:

  RE-AUDIT-READY: <commit_sha> <ISO-8601>
  Paste the original V3 truth-seeker prompt into a fresh session with the
  closure-verification appendix at docs/CLOSURE-EVIDENCE-<DATE>.log inlined;
  run re-audit-closure protocol (Appendix C of the original audit report).

Refusals:
  - Do not modify acceptance_criterion to make a finding easier to close.
    Closure is verification, not negotiation.
  - Do not skip findings. If blocked, log and move on; do not delete.
  - Do not amend prior commits. Each closure is its own commit.
  - Do not introduce a runtime dependency. If a fix appears to require one,
    mark the finding "blocked: requires runtime dep" and surface to the user.

===== END FIX-SESSION KICKOFF =====
\`\`\``

- [ ] **Step 3: Verify**

Run: `grep -c 'FIX-SESSION KICKOFF' creaudit.md`
Expected: 2 (BEGIN + END markers).

- [ ] **Step 4: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): embed literal fix-session kickoff prompt"
```

---

### Task A9: Re-audit closure protocol (Appendix C)

**Files:**
- Modify: `creaudit.md:622`

- [ ] **Step 1: Locate Appendix C**

Run: `grep -n 'Appendix C' creaudit.md`
Expected: line ~621.

- [ ] **Step 2: Replace the placeholder with the operationalized protocol**

Edit `creaudit.md`:
- old_string: `## Appendix C — Recursion-safe re-audit protocol
[How to re-run this audit after remediation: same prompt, same chambers, same dimensions, validate that each finding's acceptance criterion is met]`
- new_string: `## Appendix C — Recursion-safe re-audit protocol

The re-audit session re-runs the same V3 prompt unmodified, with one additional input: the prior findings_db YAML pasted verbatim under the heading `# Prior-cycle findings (closure-verification input)`. The re-audit produces a closure-verification table as Section 0 BEFORE any new scoring.

### Section 0 — Closure-verification table (required first output)

| Finding ID | Severity | Acceptance Criterion | Verification Method | Verification Command | Exit Code | Closure Status | Re-audit Note |
|------------|----------|----------------------|---------------------|----------------------|-----------|----------------|---------------|
| F-001 | P0 | REGEX_ABSENT(README.md, "consent decree") | grep -Ec | `grep -Ec 'consent decree' README.md` | 0 | VERIFIED-CLOSED | none |
| F-002 | P0 | LINE_RANGE_DIFF(docs/cases_of_record.md, 47-52, "ongoing litigation") | sed+grep | `sed -n '47,52p' docs/cases_of_record.md \| grep -F 'ongoing litigation'` | 0 | VERIFIED-CLOSED | line shifted to 51-56 — acceptable |
| F-003 | P1 | TEST_PASSES(test_audit_chain_rewrite) | pytest | `pytest -k test_audit_chain_rewrite -q` | 0 | VERIFIED-CLOSED | new test added |
| F-007 | P1 | FILE_EXISTS(docs/embedding_proxy_limitations.md) | test -e | `test -e docs/embedding_proxy_limitations.md` | 1 | REOPENED | file absent — reopened as F-007R |

Closure-status enum:

- `VERIFIED-CLOSED` — predicate executed; exit 0; finding closed.
- `REOPENED` — predicate executed; non-zero exit; finding re-enters the open list with a new ID `<orig>R`.
- `REGRESSED` — the predicate previously passed (per closure-evidence log) and now fails. This is itself a fresh P0 finding in the new cycle and the re-audit's overall verdict is auto-downgraded one tier (SHIP -> HARDEN-P1, HARDEN-P1 -> HARDEN-P0, HARDEN-P0 -> DELAY).
- `BLOCKED-EXTERNAL` — predicate cannot be executed (e.g., network unavailable for an HTTP-based check). Re-audit notes the block and does NOT count it toward closure.

After Section 0, the re-audit produces:

  RE-AUDIT-VERDICT: <closed>/<total> closed, <reopened> reopened, <regressed> regressed

Then proceeds to the full 8-chamber re-scoring per Steps 3-13 of the original protocol. The full re-scoring is required even when 100% closure is verified, because new findings can emerge between cycles.

### Execution requirements

- The re-audit MUST run every Acceptance Criterion as a shell predicate. Re-audits that only re-read the closure-evidence log without re-executing predicates are invalid (this is the recursion-safety hard rule).
- The re-audit MUST diff the working-tree SHA against the prior-cycle SHA recorded in the findings_db `repo_sha` field. A SHA mismatch is expected (fixes were committed); a SHA match means no fixes landed and the re-audit halts with `NO-FIXES-DETECTED`.
- The re-audit MUST regenerate the Coverage Matrix from the current working tree. Files added since the prior cycle get fresh rows; files removed get a `DELETED` status row.`

- [ ] **Step 3: Verify**

Run: `grep -c 'Closure-status enum' creaudit.md`
Expected: 1.

Run: `grep -c 'RE-AUDIT-VERDICT' creaudit.md`
Expected: 1.

- [ ] **Step 4: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): operationalize Appendix C re-audit closure protocol"
```

---

### Task A10: Findings database YAML schema

**Files:**
- Modify: `creaudit.md` — insert new section before the findings table at line ~582

- [ ] **Step 1: Locate the findings-table section**

Run: `grep -n '## Findings table' creaudit.md`
Expected: line ~582.

- [ ] **Step 2: Insert the findings_db schema section before the findings table**

Edit `creaudit.md`:
- old_string: `## Findings table (claude-code-cli-consumable)`
- new_string: `## findings_db (machine-readable)

The audit report MUST include this YAML block. The fix-session kickoff prompt and the re-audit closure protocol both consume this block by name. The human-readable findings table (next section) is rendered FROM this block — they must not drift.

\`\`\`yaml
findings_db:
  schema_version: 1
  audit_cycle: "v3-<ISO-DATE>"
  repo_sha: "<git rev-parse HEAD at audit start>"
  prompt_sha: "<sha256 of creaudit.md content at audit start, first 12 chars>"
  findings:
    - id: F-001
      severity: P0                    # P0 | P1 | P2 | P3
      file: README.md
      lines: "23-25"                  # string; ranges or comma-list
      claim: "Five-anchors credentials block precedes disclaimer block"
      evidence_url: "https://github.com/linus10x/cre-agent-audit/blob/<sha>/README.md#L23"
      recommendation: "Move disclaimer above 'Five anchors' H2."
      acceptance_criterion: 'REGEX_PRESENT(README.md, "^> .*not legal advice") AND LINE_RANGE_DIFF(README.md, 1-20, "not legal advice")'
      estimated_fix_time_min: 5
      chamber_consensus: "8/8"        # N/8 chambers concur
      closure_status: open            # open | closed | blocked | reopened
      closure_evidence: null          # "<commit_sha>:<verification_command>" once closed
      closure_date: null              # ISO-8601 or null
      reaudit_status: null            # VERIFIED-CLOSED | REOPENED | REGRESSED | BLOCKED-EXTERNAL (re-audit fills)
\`\`\`

Required invariants:
- Every entry in `findings` has all fields present (use `null` for unfilled).
- `acceptance_criterion` MUST parse against the grammar in Step 13.5. Free-text criteria fail validation.
- `id` is `F-NNN` with zero-padded 3-digit suffix.
- `evidence_url` MUST resolve (HTTP 200 or git-blob path that exists).
- `chamber_consensus` is `N/8` where N is the count of chambers that named the finding (any of the 16 P/A lenses count as their chamber once).

## Findings table (claude-code-cli-consumable)`

- [ ] **Step 3: Verify**

Run: `grep -c 'findings_db (machine-readable)' creaudit.md`
Expected: 1.

Run: `grep -c '^findings_db:' creaudit.md`
Expected: ≥1.

- [ ] **Step 4: Commit**

```bash
git add creaudit.md
git commit -m "docs(audit-prompt): add machine-readable findings_db YAML schema"
```

---

### Task A11: Self-review of Track A edits

- [ ] **Step 1: Re-read the modified prompt end-to-end**

Run: `wc -l creaudit.md`
Expected: line count grew from 990 to ~1100-1150 (10 sections expanded).

- [ ] **Step 2: Grep for stale v0.3.0 references**

Run: `grep -nE 'v0\.3\.0 expected|NEW in v0\.3\.0|Python 3\.12\+ and 3\.13|content-blind audit\.$' creaudit.md | grep -v '^.*\b\(v0\.3\.0 roadmap\|v0\.3 candidate\|v0\.3 per CHANGELOG\)\b'`
Expected: zero matches (the prune is complete).

- [ ] **Step 3: Grep that all new sections are present**

Run: `grep -cE '^## (findings_db \(machine|Fix-session kickoff|Appendix C — Recursion-safe re-audit)' creaudit.md`
Expected: 3.

Run: `grep -cE '^11\. \*\*Bias-protocol|^12\. \*\*Hostile-prior|Step 13\.5 — Acceptance-criterion grammar' creaudit.md`
Expected: 3.

- [ ] **Step 4: Confirm no duplicate sections introduced**

Run: `grep -cE '^## Findings table' creaudit.md`
Expected: 1.

- [ ] **Step 5: Commit a no-op tracking commit if any small drift discovered, otherwise skip**

(Conditional — if all greps pass, no commit needed.)

---

# Track B — Repo Hardening

Folds the 7 v0.2.1 deferred items + 5 v0.3.0 roadmap items. Bumps to `v0.2.1` after tasks B1–B23, then to `v0.3.0` after B24–B29.

---

### Task B1: `LedgerStore` Protocol + `InMemoryLedgerStore`

**Files:**
- Create: `src/cre_agent_audit/governance/ledger_store.py`
- Test: `tests/test_ledger_store_inmemory.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ledger_store_inmemory.py`:

```python
"""Tests for the in-memory reference LedgerStore."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)
from cre_agent_audit.governance.ledger_store import (
    InMemoryLedgerStore,
    LedgerStore,
)


def _make_entry(seq: int, prior: str = GENESIS_PRIOR_HASH) -> AuditEntry:
    return AuditEntry(
        sequence=seq,
        timestamp=datetime(2026, 5, 28, tzinfo=timezone.utc),
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
        prior_hash=prior,
        self_hash="a" * 64,
    )


def test_empty_store_head_returns_genesis() -> None:
    store: LedgerStore = InMemoryLedgerStore()
    assert store.head_self_hash() == GENESIS_PRIOR_HASH
    assert store.head_sequence() == -1
    assert len(store) == 0


def test_append_then_get() -> None:
    store: LedgerStore = InMemoryLedgerStore()
    e0 = _make_entry(0)
    store.append(e0)
    assert len(store) == 1
    assert store.get(0) == e0
    assert store.head_sequence() == 0


def test_iter_returns_entries_in_order() -> None:
    store: LedgerStore = InMemoryLedgerStore()
    for i in range(3):
        store.append(_make_entry(i))
    assert [e.sequence for e in store] == [0, 1, 2]


def test_get_out_of_range_raises() -> None:
    store: LedgerStore = InMemoryLedgerStore()
    store.append(_make_entry(0))
    with pytest.raises(IndexError):
        store.get(5)


def test_protocol_conformance_via_isinstance_check() -> None:
    # Protocol classes from typing are runtime-checkable only when decorated;
    # this test simply asserts the method set exists, since we're a structural
    # type. The real "conformance" is mypy --strict in CI.
    store = InMemoryLedgerStore()
    for method in ("append", "__iter__", "__len__", "get", "head_sequence", "head_self_hash"):
        assert hasattr(store, method)
```

- [ ] **Step 2: Run tests — expect import-level failures**

Run: `pytest tests/test_ledger_store_inmemory.py -v`
Expected: `ModuleNotFoundError: No module named 'cre_agent_audit.governance.ledger_store'`.

- [ ] **Step 3: Write the minimal implementation**

Create `src/cre_agent_audit/governance/ledger_store.py`:

```python
"""Pluggable persistence layer for the audit ledger — ADR-0012.

The original `AuditLedger` stored entries in a single in-memory list. v0.2.1
factors storage behind a Protocol so deployers can plug in SQLite (this repo),
JSONL (this repo), or downstream backends (Postgres+WAL, S3+Object Lock,
DynamoDB conditional writes) without touching `AuditLedger` or hash semantics.

This module ships the Protocol + the in-memory reference implementation.
Backends live in `ledger_store_sqlite.py` and `ledger_store_jsonl.py`.
"""

from __future__ import annotations

from typing import Iterator, Protocol

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    AuditEntry,
)


class LedgerStore(Protocol):
    """Storage Protocol for `AuditLedger`. Append-only; never mutates."""

    def append(self, entry: AuditEntry) -> None: ...
    def __iter__(self) -> Iterator[AuditEntry]: ...
    def __len__(self) -> int: ...
    def get(self, sequence: int) -> AuditEntry: ...
    def head_sequence(self) -> int: ...
    def head_self_hash(self) -> str: ...


class InMemoryLedgerStore:
    """Reference in-memory store — preserves v0.2.0 behavior."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def __iter__(self) -> Iterator[AuditEntry]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, sequence: int) -> AuditEntry:
        if sequence < 0 or sequence >= len(self._entries):
            raise IndexError(f"sequence {sequence} out of range [0, {len(self._entries)})")
        return self._entries[sequence]

    def head_sequence(self) -> int:
        return len(self._entries) - 1

    def head_self_hash(self) -> str:
        if not self._entries:
            return GENESIS_PRIOR_HASH
        return self._entries[-1].self_hash
```

- [ ] **Step 4: Run tests — expect green**

Run: `pytest tests/test_ledger_store_inmemory.py -v`
Expected: 5 passed.

- [ ] **Step 5: mypy + ruff**

Run: `mypy --strict src/cre_agent_audit/governance/ledger_store.py`
Expected: `Success: no issues found in 1 source file`.

Run: `ruff check src/cre_agent_audit/governance/ledger_store.py tests/test_ledger_store_inmemory.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add src/cre_agent_audit/governance/ledger_store.py tests/test_ledger_store_inmemory.py
git commit -m "feat(audit-chain): add LedgerStore Protocol + InMemoryLedgerStore"
```

---

### Task B2: `SqliteLedgerStore`

**Files:**
- Create: `src/cre_agent_audit/governance/ledger_store_sqlite.py`
- Test: `tests/test_ledger_store_sqlite.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ledger_store_sqlite.py`:

```python
"""Tests for the SQLite-backed LedgerStore."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)
from cre_agent_audit.governance.ledger_store_sqlite import SqliteLedgerStore


def _entry(seq: int, prior: str = GENESIS_PRIOR_HASH) -> AuditEntry:
    return AuditEntry(
        sequence=seq,
        timestamp=datetime(2026, 5, 28, 12, 34, 56, tzinfo=timezone.utc),
        actor_kind=ActorKind.AGENT,
        actor_id="agent:test",
        decision_type="screening_decision",
        action_payload=b"\x01\x02\x03",
        gate_verdicts={"fair_housing": "PASS", "defcon": "PASS"},
        prior_hash=prior,
        self_hash="abc" * 21 + "d",  # 64 chars
    )


def test_empty_db_returns_genesis(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    assert store.head_self_hash() == GENESIS_PRIOR_HASH
    assert store.head_sequence() == -1
    assert len(store) == 0


def test_append_round_trip(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    e = _entry(0)
    store.append(e)
    assert len(store) == 1
    assert store.get(0) == e
    assert store.head_self_hash() == e.self_hash


def test_persists_across_reopen(tmp_path: Path) -> None:
    db = tmp_path / "ledger.db"
    store_a = SqliteLedgerStore(db)
    store_a.append(_entry(0))
    store_a.append(_entry(1, prior="abc" * 21 + "d"))
    del store_a

    store_b = SqliteLedgerStore(db)
    assert len(store_b) == 2
    assert [e.sequence for e in store_b] == [0, 1]


def test_iter_preserves_order_with_many_entries(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    for i in range(50):
        store.append(_entry(i))
    seqs = [e.sequence for e in store]
    assert seqs == list(range(50))


def test_no_update_path(tmp_path: Path) -> None:
    """The Protocol does not expose UPDATE; verify there is no method to mutate."""
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    for forbidden in ("update", "delete", "truncate", "set"):
        assert not hasattr(store, forbidden), f"SqliteLedgerStore must not expose {forbidden}"


def test_get_out_of_range_raises(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db")
    store.append(_entry(0))
    with pytest.raises(IndexError):
        store.get(99)


def test_custom_table_name(tmp_path: Path) -> None:
    store = SqliteLedgerStore(tmp_path / "ledger.db", table="custom_audit")
    store.append(_entry(0))
    assert len(store) == 1
```

- [ ] **Step 2: Run tests — expect import-level failures**

Run: `pytest tests/test_ledger_store_sqlite.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write the implementation**

Create `src/cre_agent_audit/governance/ledger_store_sqlite.py`:

```python
"""SQLite-backed LedgerStore — ADR-0012 § Persistence backends.

Uses stdlib `sqlite3`. Single-table schema; no UPDATE / DELETE codepath
(append-only is enforced by absence of methods, not by triggers — the
LedgerStore Protocol intentionally exposes no mutation surface).

For production deployments needing Postgres+WAL, S3+Object Lock, or
DynamoDB conditional writes: write a sibling backend in your codebase
implementing the `LedgerStore` Protocol. ADR-0012 documents the
integration shape; the repo does not pull driver libraries.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterator

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)


class SqliteLedgerStore:
    """sqlite3-backed `LedgerStore`. One row per `AuditEntry`."""

    def __init__(self, db_path: Path | str, *, table: str = "audit_chain") -> None:
        if not table.replace("_", "").isalnum():
            raise ValueError(f"table name {table!r} must be alphanumeric+underscore")
        self._table = table
        self._conn = sqlite3.connect(str(db_path), isolation_level=None)
        self._conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                sequence INTEGER PRIMARY KEY,
                timestamp_iso TEXT NOT NULL,
                actor_kind TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                action_payload BLOB NOT NULL,
                gate_verdicts_json TEXT NOT NULL,
                prior_hash TEXT NOT NULL,
                self_hash TEXT NOT NULL,
                corrects_sequence INTEGER
            )
            """
        )

    def append(self, entry: AuditEntry) -> None:
        self._conn.execute(
            f"INSERT INTO {self._table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.sequence,
                entry.timestamp.isoformat(),
                entry.actor_kind.value,
                entry.actor_id,
                entry.decision_type,
                entry.action_payload,
                json.dumps(dict(sorted(entry.gate_verdicts.items())), sort_keys=True),
                entry.prior_hash,
                entry.self_hash,
                entry.corrects_sequence,
            ),
        )

    def __iter__(self) -> Iterator[AuditEntry]:
        rows = self._conn.execute(
            f"SELECT sequence, timestamp_iso, actor_kind, actor_id, decision_type, "
            f"action_payload, gate_verdicts_json, prior_hash, self_hash, corrects_sequence "
            f"FROM {self._table} ORDER BY sequence ASC"
        )
        for row in rows:
            yield self._row_to_entry(row)

    def __len__(self) -> int:
        cur = self._conn.execute(f"SELECT COUNT(*) FROM {self._table}")
        result: int = cur.fetchone()[0]
        return result

    def get(self, sequence: int) -> AuditEntry:
        cur = self._conn.execute(
            f"SELECT sequence, timestamp_iso, actor_kind, actor_id, decision_type, "
            f"action_payload, gate_verdicts_json, prior_hash, self_hash, corrects_sequence "
            f"FROM {self._table} WHERE sequence = ?",
            (sequence,),
        )
        row = cur.fetchone()
        if row is None:
            raise IndexError(f"sequence {sequence} not found")
        return self._row_to_entry(row)

    def head_sequence(self) -> int:
        cur = self._conn.execute(f"SELECT MAX(sequence) FROM {self._table}")
        result = cur.fetchone()[0]
        return -1 if result is None else int(result)

    def head_self_hash(self) -> str:
        cur = self._conn.execute(
            f"SELECT self_hash FROM {self._table} ORDER BY sequence DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row is None:
            return GENESIS_PRIOR_HASH
        return str(row[0])

    @staticmethod
    def _row_to_entry(row: tuple[object, ...]) -> AuditEntry:
        return AuditEntry(
            sequence=int(row[0]),  # type: ignore[arg-type]
            timestamp=datetime.fromisoformat(str(row[1])),
            actor_kind=ActorKind(str(row[2])),
            actor_id=str(row[3]),
            decision_type=str(row[4]),
            action_payload=bytes(row[5]),  # type: ignore[arg-type]
            gate_verdicts=json.loads(str(row[6])),
            prior_hash=str(row[7]),
            self_hash=str(row[8]),
            corrects_sequence=None if row[9] is None else int(row[9]),  # type: ignore[arg-type]
        )
```

- [ ] **Step 4: Run tests — expect green**

Run: `pytest tests/test_ledger_store_sqlite.py -v`
Expected: 7 passed.

- [ ] **Step 5: mypy + ruff**

Run: `mypy --strict src/cre_agent_audit/governance/ledger_store_sqlite.py`
Expected: `Success`.

Run: `ruff check src/cre_agent_audit/governance/ledger_store_sqlite.py tests/test_ledger_store_sqlite.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add src/cre_agent_audit/governance/ledger_store_sqlite.py tests/test_ledger_store_sqlite.py
git commit -m "feat(audit-chain): add SqliteLedgerStore stdlib backend"
```

---

### Task B3: `JsonlLedgerStore`

**Files:**
- Create: `src/cre_agent_audit/governance/ledger_store_jsonl.py`
- Test: `tests/test_ledger_store_jsonl.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ledger_store_jsonl.py`:

```python
"""Tests for the JSONL-backed LedgerStore."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)
from cre_agent_audit.governance.ledger_store_jsonl import JsonlLedgerStore


def _entry(seq: int) -> AuditEntry:
    return AuditEntry(
        sequence=seq,
        timestamp=datetime(2026, 5, 28, tzinfo=timezone.utc),
        actor_kind=ActorKind.HUMAN,
        actor_id="user:gc",
        decision_type="bypass",
        action_payload=b"payload",
        gate_verdicts={"sovereign_veto": "BYPASSED"},
        prior_hash=GENESIS_PRIOR_HASH,
        self_hash="b" * 64,
    )


def test_empty_file_genesis(tmp_path: Path) -> None:
    store = JsonlLedgerStore(tmp_path / "ledger.jsonl")
    assert store.head_self_hash() == GENESIS_PRIOR_HASH
    assert len(store) == 0


def test_append_and_persist(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    store = JsonlLedgerStore(p)
    e = _entry(0)
    store.append(e)
    assert p.exists()
    assert len(store) == 1
    assert store.get(0) == e


def test_reopen_reads_existing(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    a = JsonlLedgerStore(p)
    a.append(_entry(0))
    a.append(_entry(1))
    del a
    b = JsonlLedgerStore(p)
    assert len(b) == 2


def test_corrupted_line_raises(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    p.write_text('{"sequence": "this-is-not-an-int"}\n')
    with pytest.raises((ValueError, KeyError)):
        list(JsonlLedgerStore(p))


def test_fsync_can_be_disabled(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    store = JsonlLedgerStore(p, fsync=False)
    store.append(_entry(0))
    assert len(store) == 1
```

- [ ] **Step 2: Run tests — expect import-level failures**

Run: `pytest tests/test_ledger_store_jsonl.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write the implementation**

Create `src/cre_agent_audit/governance/ledger_store_jsonl.py`:

```python
"""Append-only JSONL LedgerStore — ADR-0012 § Persistence backends.

One JSON object per line. Survives crash mid-write only if `fsync=True`
(the default). For higher durability, deployers should use an
external append-only object store (S3 + Object Lock) and write a
custom backend implementing `LedgerStore` against the same Protocol.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Iterator

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditEntry,
)


class JsonlLedgerStore:
    """JSONL file-backed `LedgerStore`."""

    def __init__(self, path: Path | str, *, fsync: bool = True) -> None:
        self._path = Path(path)
        self._fsync = fsync
        self._path.touch(exist_ok=True)

    def append(self, entry: AuditEntry) -> None:
        payload = {
            "sequence": entry.sequence,
            "timestamp": entry.timestamp.isoformat(),
            "actor_kind": entry.actor_kind.value,
            "actor_id": entry.actor_id,
            "decision_type": entry.decision_type,
            "action_payload_hex": entry.action_payload.hex(),
            "gate_verdicts": dict(sorted(entry.gate_verdicts.items())),
            "prior_hash": entry.prior_hash,
            "self_hash": entry.self_hash,
            "corrects_sequence": entry.corrects_sequence,
        }
        line = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            if self._fsync:
                os.fsync(f.fileno())

    def __iter__(self) -> Iterator[AuditEntry]:
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield self._decode(line)

    def __len__(self) -> int:
        with open(self._path, encoding="utf-8") as f:
            return sum(1 for ln in f if ln.strip())

    def get(self, sequence: int) -> AuditEntry:
        for entry in self:
            if entry.sequence == sequence:
                return entry
        raise IndexError(f"sequence {sequence} not found")

    def head_sequence(self) -> int:
        last = -1
        for entry in self:
            if entry.sequence > last:
                last = entry.sequence
        return last

    def head_self_hash(self) -> str:
        head = GENESIS_PRIOR_HASH
        max_seq = -1
        for entry in self:
            if entry.sequence > max_seq:
                max_seq = entry.sequence
                head = entry.self_hash
        return head

    @staticmethod
    def _decode(line: str) -> AuditEntry:
        d = json.loads(line)
        return AuditEntry(
            sequence=int(d["sequence"]),
            timestamp=datetime.fromisoformat(d["timestamp"]),
            actor_kind=ActorKind(d["actor_kind"]),
            actor_id=d["actor_id"],
            decision_type=d["decision_type"],
            action_payload=bytes.fromhex(d["action_payload_hex"]),
            gate_verdicts=d["gate_verdicts"],
            prior_hash=d["prior_hash"],
            self_hash=d["self_hash"],
            corrects_sequence=d.get("corrects_sequence"),
        )
```

- [ ] **Step 4: Run tests — expect green**

Run: `pytest tests/test_ledger_store_jsonl.py -v`
Expected: 5 passed.

- [ ] **Step 5: mypy + ruff**

Run: `mypy --strict src/cre_agent_audit/governance/ledger_store_jsonl.py && ruff check src/cre_agent_audit/governance/ledger_store_jsonl.py tests/test_ledger_store_jsonl.py`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add src/cre_agent_audit/governance/ledger_store_jsonl.py tests/test_ledger_store_jsonl.py
git commit -m "feat(audit-chain): add JsonlLedgerStore append-only backend"
```

---

### Task B4: Refactor `AuditLedger` to use `LedgerStore`

**Files:**
- Modify: `src/cre_agent_audit/governance/audit_chain.py:126-274`
- Modify: `tests/test_audit_chain.py` (existing — preserve all 13 tests; add parameterization)

- [ ] **Step 1: Read the existing `AuditLedger`**

Already read at audit_chain.py:126-274. Current state: `_entries: list[AuditEntry]` is the single source of truth.

- [ ] **Step 2: Write a new failing test that injects an alternate store**

Append to `tests/test_audit_chain.py`:

```python
from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore
from cre_agent_audit.governance.ledger_store_sqlite import SqliteLedgerStore


def test_audit_ledger_accepts_injected_store_inmemory() -> None:
    store = InMemoryLedgerStore()
    ledger = AuditLedger(store=store)
    entry = ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
    )
    assert len(store) == 1
    assert store.get(0) == entry


def test_audit_ledger_accepts_injected_store_sqlite(tmp_path: object) -> None:
    from pathlib import Path
    p = Path(tmp_path) / "l.db"  # type: ignore[arg-type]
    store = SqliteLedgerStore(p)
    ledger = AuditLedger(store=store)
    ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
    )
    ledger.verify_chain()  # uses store iteration


def test_audit_ledger_default_remains_in_memory() -> None:
    # Backward-compat: existing callers using AuditLedger() get the same behavior.
    ledger = AuditLedger()
    assert ledger.chain_head() == GENESIS_PRIOR_HASH
```

- [ ] **Step 3: Run — expect failure**

Run: `pytest tests/test_audit_chain.py::test_audit_ledger_accepts_injected_store_inmemory -v`
Expected: `TypeError: __init__() got an unexpected keyword argument 'store'`.

- [ ] **Step 4: Refactor `AuditLedger`**

Edit `src/cre_agent_audit/governance/audit_chain.py`:

- old_string: `@dataclass
class AuditLedger:
    """Append-only ledger of governance decisions.

    The ledger is the system of record for every agent decision, every gate
    verdict, and every operator transition. There is no public delete or
    truncate API by design (ADR-0003 invariant).
    """

    _entries: list[AuditEntry] = field(default_factory=list, init=False, repr=False)

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        """Return an immutable view of the entries."""
        return tuple(self._entries)`
- new_string: `@dataclass
class AuditLedger:
    """Append-only ledger of governance decisions.

    The ledger is the system of record for every agent decision, every gate
    verdict, and every operator transition. There is no public delete or
    truncate API by design (ADR-0003 invariant).

    Storage is pluggable via the `LedgerStore` Protocol (see ledger_store.py).
    The default backend is in-memory; deployers can inject SqliteLedgerStore,
    JsonlLedgerStore, or a custom backend (Postgres+WAL, S3+Object Lock,
    DynamoDB) per ADR-0012.
    """

    store: "LedgerStore" = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # Local import to avoid circular import at module load.
        from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore
        if self.store is None:  # type: ignore[unreachable]
            self.store = InMemoryLedgerStore()

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        """Return an immutable view of the entries."""
        return tuple(self.store)`

- [ ] **Step 5: Replace every internal use of `self._entries` with `self.store`**

Edit `src/cre_agent_audit/governance/audit_chain.py`:

- old_string: `        sequence = len(self._entries)
        prior_hash = self.chain_head()`
- new_string: `        sequence = len(self.store)
        prior_hash = self.chain_head()`

- old_string: `        self._entries.append(entry)
        return entry`
- new_string: `        self.store.append(entry)
        return entry`

- old_string: `        if corrects_sequence < 0 or corrects_sequence >= len(self._entries):
            raise ValueError(f"corrects_sequence {corrects_sequence} not in ledger")`
- new_string: `        if corrects_sequence < 0 or corrects_sequence >= len(self.store):
            raise ValueError(f"corrects_sequence {corrects_sequence} not in ledger")`

- old_string: `    def chain_head(self) -> str:
        """Return ``self_hash`` of the last entry (the chain head digest).

        Publish this value periodically to an external witness register
        (OpenTimestamps, Sigstore Rekor, regulator log) to convert the
        internally-consistent chain into an adversarially tamper-evident
        record. The genesis sentinel (SHA-256 zeroes) is returned for an
        empty ledger.
        """
        if not self._entries:
            return GENESIS_PRIOR_HASH
        return self._entries[-1].self_hash`
- new_string: `    def chain_head(self) -> str:
        """Return ``self_hash`` of the last entry (the chain head digest).

        Publish this value periodically to an external witness register
        (OpenTimestamps, Sigstore Rekor, regulator log) to convert the
        internally-consistent chain into an adversarially tamper-evident
        record. The genesis sentinel (SHA-256 zeroes) is returned for an
        empty ledger.
        """
        return self.store.head_self_hash()`

- old_string: `        previous_self_hash = GENESIS_PRIOR_HASH
        for index, entry in enumerate(self._entries):`
- new_string: `        previous_self_hash = GENESIS_PRIOR_HASH
        for index, entry in enumerate(self.store):`

- old_string: `    def _replace_entry_for_tests(self, index: int, replacement: AuditEntry) -> None:
        self._entries[index] = replacement`
- new_string: `    def _replace_entry_for_tests(self, index: int, replacement: AuditEntry) -> None:
        # Test-only seam. Requires the underlying store to expose mutation;
        # only InMemoryLedgerStore does. Production stores (SQLite, JSONL)
        # have no UPDATE path by Protocol design.
        from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore
        if not isinstance(self.store, InMemoryLedgerStore):
            raise TypeError("_replace_entry_for_tests only supported on InMemoryLedgerStore")
        self.store._entries[index] = replacement`

- [ ] **Step 6: Run tests — expect all green**

Run: `pytest tests/test_audit_chain.py -v`
Expected: all 16 tests pass (13 original + 3 new).

Run: `pytest`
Expected: 142+ tests pass, no regressions.

- [ ] **Step 7: mypy + ruff**

Run: `mypy --strict src/cre_agent_audit/governance/audit_chain.py`
Expected: `Success`.

- [ ] **Step 8: Update `src/cre_agent_audit/__init__.py`**

Edit `src/cre_agent_audit/__init__.py`:

- old_string: `from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditChainTamperError,
    AuditEntry,
    AuditLedger,
)`
- new_string: `from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditChainTamperError,
    AuditEntry,
    AuditLedger,
)
from cre_agent_audit.governance.ledger_store import (
    InMemoryLedgerStore,
    LedgerStore,
)
from cre_agent_audit.governance.ledger_store_jsonl import JsonlLedgerStore
from cre_agent_audit.governance.ledger_store_sqlite import SqliteLedgerStore`

- old_string: `    # Pattern 3 — Hash-chain Audit Ledger (ADR-0003)
    "ActorKind",
    "AuditChainTamperError",
    "AuditEntry",
    "AuditLedger",`
- new_string: `    # Pattern 3 — Hash-chain Audit Ledger (ADR-0003)
    "ActorKind",
    "AuditChainTamperError",
    "AuditEntry",
    "AuditLedger",
    "InMemoryLedgerStore",
    "JsonlLedgerStore",
    "LedgerStore",
    "SqliteLedgerStore",`

- [ ] **Step 9: Final verification + commit**

Run: `make verify`
Expected: green.

```bash
git add src/cre_agent_audit/governance/audit_chain.py src/cre_agent_audit/__init__.py tests/test_audit_chain.py
git commit -m "refactor(audit-chain): pluggable LedgerStore via Protocol injection"
```

---

### Task B5: `TimestampSource` Protocol + `LocalClockTimestampSource`

**Files:**
- Create: `src/cre_agent_audit/governance/timestamp_source.py`
- Test: `tests/test_timestamp_source.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_timestamp_source.py`:

```python
"""Tests for TimestampSource Protocol + LocalClockTimestampSource."""
from __future__ import annotations

from datetime import datetime, timezone

from cre_agent_audit.governance.timestamp_source import (
    LocalClockTimestampSource,
    TimestampSource,
    TrustedTimestamp,
)


def test_local_clock_returns_now() -> None:
    src: TimestampSource = LocalClockTimestampSource()
    before = datetime.now(timezone.utc)
    ts = src.stamp(b"any-digest")
    after = datetime.now(timezone.utc)
    assert before <= ts.asserted_at <= after
    assert ts.tsa_url is None
    assert ts.tsr_token_b64 is None
    assert ts.hash_algorithm == "sha256"


def test_trusted_timestamp_is_frozen() -> None:
    ts = TrustedTimestamp(
        asserted_at=datetime(2026, 5, 28, tzinfo=timezone.utc),
        tsa_url=None,
        tsr_token_b64=None,
    )
    import dataclasses
    assert dataclasses.is_dataclass(ts)
    try:
        ts.asserted_at = datetime.now(timezone.utc)  # type: ignore[misc]
        raise AssertionError("TrustedTimestamp must be frozen")
    except dataclasses.FrozenInstanceError:
        pass
```

- [ ] **Step 2: Run — expect ModuleNotFoundError**

Run: `pytest tests/test_timestamp_source.py -v`
Expected: import error.

- [ ] **Step 3: Write the minimal implementation**

Create `src/cre_agent_audit/governance/timestamp_source.py`:

```python
"""Trusted timestamp Protocol + reference impls — ADR-0012 § 1.3.

By default, `AuditEntry.timestamp` is the local system clock. For audit-grade
attestation under SOC 2 / SOX 404 / FFIEC discovery, deployers can inject an
`RFC3161TimestampSource` (this module) that obtains a signed timestamp from
a trusted Timestamp Authority and stores the opaque token alongside the
timestamp. The token can later be re-verified against the TSA's signing chain.

Stdlib-only network code. No `requests`, no `urllib3`. RFC 3161 codec in
`rfc3161_codec.py`. Verification (requires `pyca/cryptography`) is gated
behind the `audit-verify` extra in `rfc3161_verify.py`.
"""

from __future__ import annotations

import http.client
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol
from urllib.parse import urlparse


@dataclass(frozen=True)
class TrustedTimestamp:
    """A timestamp + optional TSA attestation."""

    asserted_at: datetime
    tsa_url: str | None
    tsr_token_b64: str | None
    hash_algorithm: str = "sha256"


class TimestampSource(Protocol):
    """Protocol — returns a `TrustedTimestamp` for a payload digest."""

    def stamp(self, payload_digest: bytes) -> TrustedTimestamp: ...


class LocalClockTimestampSource:
    """Default — uses `datetime.now(timezone.utc)`; no attestation."""

    def stamp(self, payload_digest: bytes) -> TrustedTimestamp:
        return TrustedTimestamp(
            asserted_at=datetime.now(timezone.utc),
            tsa_url=None,
            tsr_token_b64=None,
        )


@dataclass
class RFC3161TimestampSource:
    """RFC 3161 client — sends a TSQ, receives a TSR, parses the GenTime.

    On TSA failure, falls back to local clock by default (so a TSA outage
    cannot stall the audit pipeline). The fallback fires the `on_fallback`
    callback so the deployer can alert. Set `fallback_to_local_on_failure=False`
    to fail-closed instead.
    """

    tsa_url: str  # e.g., "https://freetsa.org/tsr"
    timeout_s: float = 5.0
    fallback_to_local_on_failure: bool = True
    on_fallback: Callable[[Exception], None] | None = None

    def stamp(self, payload_digest: bytes) -> TrustedTimestamp:
        from cre_agent_audit.governance.rfc3161_codec import (
            build_timestamp_request,
            parse_timestamp_response,
        )

        tsq = build_timestamp_request(payload_digest)
        try:
            tsr_bytes = self._post(tsq)
            asserted_at = parse_timestamp_response(tsr_bytes)
            import base64
            return TrustedTimestamp(
                asserted_at=asserted_at,
                tsa_url=self.tsa_url,
                tsr_token_b64=base64.b64encode(tsr_bytes).decode("ascii"),
            )
        except Exception as exc:
            if self.fallback_to_local_on_failure:
                if self.on_fallback is not None:
                    self.on_fallback(exc)
                return LocalClockTimestampSource().stamp(payload_digest)
            raise

    def _post(self, tsq_bytes: bytes) -> bytes:
        url = urlparse(self.tsa_url)
        if url.scheme not in ("http", "https"):
            raise ValueError(f"tsa_url must be http or https; got {url.scheme!r}")
        conn_cls = http.client.HTTPSConnection if url.scheme == "https" else http.client.HTTPConnection
        host = url.hostname or ""
        port = url.port or (443 if url.scheme == "https" else 80)
        if url.scheme == "https":
            ctx = ssl.create_default_context()
            conn = conn_cls(host, port, timeout=self.timeout_s, context=ctx)  # type: ignore[call-arg]
        else:
            conn = conn_cls(host, port, timeout=self.timeout_s)
        try:
            conn.request(
                "POST",
                url.path or "/",
                body=tsq_bytes,
                headers={
                    "Content-Type": "application/timestamp-query",
                    "Content-Length": str(len(tsq_bytes)),
                },
            )
            resp = conn.getresponse()
            if resp.status != 200:
                raise RuntimeError(f"TSA returned HTTP {resp.status}")
            return resp.read()
        finally:
            conn.close()
```

- [ ] **Step 4: Run tests — expect green**

Run: `pytest tests/test_timestamp_source.py -v`
Expected: 2 passed.

- [ ] **Step 5: mypy + ruff**

Run: `mypy --strict src/cre_agent_audit/governance/timestamp_source.py && ruff check src/cre_agent_audit/governance/timestamp_source.py tests/test_timestamp_source.py`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add src/cre_agent_audit/governance/timestamp_source.py tests/test_timestamp_source.py
git commit -m "feat(audit-chain): add TimestampSource Protocol + LocalClock + RFC3161 client"
```

---

### Task B6: RFC 3161 DER codec

**Files:**
- Create: `src/cre_agent_audit/governance/rfc3161_codec.py`
- Test: `tests/test_rfc3161_codec.py`
- Fixture: `tests/fixtures/rfc3161_tsr_sample.der`

- [ ] **Step 1: Capture a real FreeTSA TSR sample to use as a golden fixture**

This is a one-time setup. The test will read this fixture rather than depend on FreeTSA at test time.

```bash
mkdir -p tests/fixtures
# Run once to capture a known-good TSR. Skip if you already have one.
python -c "
import hashlib, http.client, ssl
from cre_agent_audit.governance.rfc3161_codec import build_timestamp_request
tsq = build_timestamp_request(hashlib.sha256(b'sample').digest())
ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection('freetsa.org', 443, context=ctx, timeout=10)
conn.request('POST', '/tsr', body=tsq, headers={'Content-Type': 'application/timestamp-query'})
data = conn.getresponse().read()
open('tests/fixtures/rfc3161_tsr_sample.der', 'wb').write(data)
print('captured', len(data), 'bytes')
"
```

(If FreeTSA is unreachable during fixture capture, fall back to a vendored sample from the OpenSSL test suite — see https://github.com/openssl/openssl/tree/master/test/recipes/80-test_ts_data — and document the source in `tests/fixtures/README.md`.)

- [ ] **Step 2: Write the failing tests**

Create `tests/test_rfc3161_codec.py`:

```python
"""Tests for the minimal RFC 3161 DER codec."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from cre_agent_audit.governance.rfc3161_codec import (
    build_timestamp_request,
    parse_timestamp_response,
)


def test_request_starts_with_der_sequence_tag() -> None:
    digest = hashlib.sha256(b"hello").digest()
    req = build_timestamp_request(digest)
    # DER SEQUENCE starts with 0x30
    assert req[0] == 0x30


def test_request_contains_sha256_oid() -> None:
    """OID 2.16.840.1.101.3.4.2.1 (sha256) DER bytes: 60 86 48 01 65 03 04 02 01"""
    req = build_timestamp_request(hashlib.sha256(b"hello").digest())
    sha256_oid = bytes([0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01])
    assert sha256_oid in req


def test_request_contains_digest() -> None:
    digest = hashlib.sha256(b"hello").digest()
    req = build_timestamp_request(digest)
    assert digest in req


def test_parse_response_from_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "rfc3161_tsr_sample.der"
    if not fixture.exists():
        import pytest
        pytest.skip("RFC 3161 TSR fixture not captured")
    ts = parse_timestamp_response(fixture.read_bytes())
    assert isinstance(ts, datetime)
    assert ts.tzinfo is not None
    # FreeTSA's clock should be within a year of now (sanity)
    now = datetime.now(timezone.utc)
    assert abs((now - ts).days) < 365
```

- [ ] **Step 3: Run — expect failure**

Run: `pytest tests/test_rfc3161_codec.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 4: Write the codec**

Create `src/cre_agent_audit/governance/rfc3161_codec.py`:

```python
"""Minimal DER ASN.1 codec for RFC 3161 TimeStampReq / TimeStampResp.

Implements only the subset RFC 3161 actually uses:
- OID, INTEGER, OCTET STRING, SEQUENCE, GeneralizedTime

For full DER work (signature verification, certificate chain validation),
use the optional `audit-verify` extra which pulls in `pyca/cryptography`.
This module is the "build the request, parse the timestamp" path — the
opaque token is preserved verbatim so a downstream verifier can validate
the TSA signature chain.

RFC 3161 references:
- Section 2.4.1 — TimeStampReq
- Section 2.4.2 — TimeStampResp
- Section 2.4.2 — TSTInfo.genTime
"""

from __future__ import annotations

from datetime import datetime, timezone

# OID 2.16.840.1.101.3.4.2.1 — id-sha256
_SHA256_OID = bytes([0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01])

# DER tags
_TAG_BOOLEAN = 0x01
_TAG_INTEGER = 0x02
_TAG_OCTET_STRING = 0x04
_TAG_NULL = 0x05
_TAG_OID = 0x06
_TAG_GENERALIZED_TIME = 0x18
_TAG_SEQUENCE = 0x30
_TAG_SET = 0x31


def _encode_length(n: int) -> bytes:
    if n < 128:
        return bytes([n])
    body = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(body)]) + body


def _tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + _encode_length(len(value)) + value


def build_timestamp_request(payload_digest: bytes) -> bytes:
    """Build a SHA-256 TimeStampReq DER blob for `payload_digest` (32 bytes)."""
    if len(payload_digest) != 32:
        raise ValueError("payload_digest must be 32 bytes (SHA-256)")
    # AlgorithmIdentifier { sha256 OID, NULL params }
    algo_id = _tlv(
        _TAG_SEQUENCE,
        _tlv(_TAG_OID, _SHA256_OID) + _tlv(_TAG_NULL, b""),
    )
    # MessageImprint { hashAlgorithm, hashedMessage }
    message_imprint = _tlv(
        _TAG_SEQUENCE,
        algo_id + _tlv(_TAG_OCTET_STRING, payload_digest),
    )
    # TimeStampReq { version=1, messageImprint, certReq=TRUE }
    version = _tlv(_TAG_INTEGER, bytes([1]))
    cert_req = _tlv(_TAG_BOOLEAN, bytes([0xFF]))
    return _tlv(_TAG_SEQUENCE, version + message_imprint + cert_req)


def parse_timestamp_response(tsr_bytes: bytes) -> datetime:
    """Extract GeneralizedTime from a TimeStampResp DER blob.

    The TSR wraps PKCSContentInfo wrapping SignedData wrapping eContent
    (an OCTET STRING) wrapping TSTInfo (a SEQUENCE) — TSTInfo.genTime is
    a GeneralizedTime in YYYYMMDDHHMMSS[.fff]Z form.

    We scan for the first GeneralizedTime tag inside the response. This is
    sufficient because TSTInfo.genTime is the only GeneralizedTime in the
    structure; finding the tag is unambiguous.
    """
    i = 0
    while i < len(tsr_bytes):
        if tsr_bytes[i] == _TAG_GENERALIZED_TIME:
            length, header_len = _decode_length_at(tsr_bytes, i + 1)
            value = tsr_bytes[i + 1 + header_len : i + 1 + header_len + length]
            return _parse_generalized_time(value)
        i += 1
    raise ValueError("no GeneralizedTime found in TSR")


def _decode_length_at(buf: bytes, offset: int) -> tuple[int, int]:
    """Return (length, header_byte_count_after_offset)."""
    first = buf[offset]
    if first < 0x80:
        return first, 1
    num_bytes = first & 0x7F
    if num_bytes == 0:
        raise ValueError("indefinite-length DER not supported")
    length = int.from_bytes(buf[offset + 1 : offset + 1 + num_bytes], "big")
    return length, 1 + num_bytes


def _parse_generalized_time(value: bytes) -> datetime:
    """Parse YYYYMMDDHHMMSS[.fff]Z into UTC datetime."""
    s = value.decode("ascii")
    if not s.endswith("Z"):
        raise ValueError("GeneralizedTime must end with Z (UTC)")
    s = s[:-1]
    if "." in s:
        base, frac = s.split(".", 1)
        micro = int(frac.ljust(6, "0")[:6])
    else:
        base, micro = s, 0
    if len(base) != 14:
        raise ValueError(f"unexpected GeneralizedTime body {value!r}")
    return datetime(
        year=int(base[0:4]),
        month=int(base[4:6]),
        day=int(base[6:8]),
        hour=int(base[8:10]),
        minute=int(base[10:12]),
        second=int(base[12:14]),
        microsecond=micro,
        tzinfo=timezone.utc,
    )
```

- [ ] **Step 5: Run tests — expect green**

Run: `pytest tests/test_rfc3161_codec.py -v`
Expected: 3-4 passed (4th skipped if no fixture).

- [ ] **Step 6: mypy + ruff**

Run: `mypy --strict src/cre_agent_audit/governance/rfc3161_codec.py && ruff check src/cre_agent_audit/governance/rfc3161_codec.py tests/test_rfc3161_codec.py`
Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add src/cre_agent_audit/governance/rfc3161_codec.py tests/test_rfc3161_codec.py tests/fixtures/rfc3161_tsr_sample.der
git commit -m "feat(audit-chain): minimal RFC 3161 DER codec (stdlib)"
```

---

### Task B7: Thread `TimestampSource` through `AuditLedger`

**Files:**
- Modify: `src/cre_agent_audit/governance/audit_chain.py`
- Modify: `tests/test_audit_chain.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_audit_chain.py`:

```python
from cre_agent_audit.governance.timestamp_source import (
    LocalClockTimestampSource,
    TimestampSource,
    TrustedTimestamp,
)


class _FakeTimestampSource:
    """Deterministic source for testing."""

    def __init__(self, asserted_at: datetime) -> None:
        self._at = asserted_at

    def stamp(self, payload_digest: bytes) -> TrustedTimestamp:
        return TrustedTimestamp(
            asserted_at=self._at,
            tsa_url="test://tsa",
            tsr_token_b64="ZmFrZQ==",
        )


def test_audit_ledger_uses_injected_timestamp_source() -> None:
    fixed = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    src: TimestampSource = _FakeTimestampSource(fixed)
    ledger = AuditLedger(timestamp_source=src)
    entry = ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
    )
    assert entry.timestamp == fixed
    assert entry.timestamp_token_b64 == "ZmFrZQ=="


def test_audit_ledger_default_timestamp_source_is_local_clock() -> None:
    ledger = AuditLedger()
    assert isinstance(ledger.timestamp_source, LocalClockTimestampSource)
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest tests/test_audit_chain.py::test_audit_ledger_uses_injected_timestamp_source -v`
Expected: `TypeError: __init__() got an unexpected keyword argument 'timestamp_source'`.

- [ ] **Step 3: Add `timestamp_token_b64` field to `AuditEntry`**

Edit `src/cre_agent_audit/governance/audit_chain.py`:

- old_string: `    sequence: int
    timestamp: datetime
    actor_kind: ActorKind
    actor_id: str
    decision_type: str
    action_payload: bytes
    gate_verdicts: dict[str, str]
    prior_hash: str
    self_hash: str
    corrects_sequence: int | None = None`
- new_string: `    sequence: int
    timestamp: datetime
    actor_kind: ActorKind
    actor_id: str
    decision_type: str
    action_payload: bytes
    gate_verdicts: dict[str, str]
    prior_hash: str
    self_hash: str
    corrects_sequence: int | None = None
    timestamp_token_b64: str | None = None
    """Base64-encoded RFC 3161 TSR token (if a trusted TSA was used).
    None for local-clock entries (backward-compatible default)."""`

- [ ] **Step 4: Include token in canonical hashing when present**

Edit `src/cre_agent_audit/governance/audit_chain.py`:

- old_string: `        payload = {
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat(),
            "actor_kind": self.actor_kind.value,
            "actor_id": self.actor_id,
            "decision_type": self.decision_type,
            # action_payload is included verbatim — base64-encode for JSON safety,
            # decoders can recover original bytes from the hex digest at verify time.
            "action_payload_hex": self.action_payload.hex(),
            "gate_verdicts": dict(sorted(self.gate_verdicts.items())),
            "prior_hash": self.prior_hash,
            "corrects_sequence": self.corrects_sequence,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")`
- new_string: `        payload: dict[str, object] = {
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat(),
            "actor_kind": self.actor_kind.value,
            "actor_id": self.actor_id,
            "decision_type": self.decision_type,
            # action_payload is included verbatim — base64-encode for JSON safety,
            # decoders can recover original bytes from the hex digest at verify time.
            "action_payload_hex": self.action_payload.hex(),
            "gate_verdicts": dict(sorted(self.gate_verdicts.items())),
            "prior_hash": self.prior_hash,
            "corrects_sequence": self.corrects_sequence,
        }
        # Include token only when present — preserves backward-compat with
        # v0.2.0 ledgers that never had this field. Mixing local-clock and
        # TSA-stamped entries in the same ledger is supported.
        if self.timestamp_token_b64 is not None:
            payload["timestamp_token_b64"] = self.timestamp_token_b64
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")`

- [ ] **Step 5: Update `_compute_self_hash` to mirror the conditional inclusion**

Edit `src/cre_agent_audit/governance/audit_chain.py`:

- old_string: `def _compute_self_hash(
    *,
    sequence: int,
    timestamp: datetime,
    actor_kind: ActorKind,
    actor_id: str,
    decision_type: str,
    action_payload: bytes,
    gate_verdicts: dict[str, str],
    prior_hash: str,
    corrects_sequence: int | None,
) -> str:
    """Internal helper — compute self_hash before constructing the frozen entry."""
    payload = {
        "sequence": sequence,
        "timestamp": timestamp.isoformat(),
        "actor_kind": actor_kind.value,
        "actor_id": actor_id,
        "decision_type": decision_type,
        "action_payload_hex": action_payload.hex(),
        "gate_verdicts": dict(sorted(gate_verdicts.items())),
        "prior_hash": prior_hash,
        "corrects_sequence": corrects_sequence,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()`
- new_string: `def _compute_self_hash(
    *,
    sequence: int,
    timestamp: datetime,
    actor_kind: ActorKind,
    actor_id: str,
    decision_type: str,
    action_payload: bytes,
    gate_verdicts: dict[str, str],
    prior_hash: str,
    corrects_sequence: int | None,
    timestamp_token_b64: str | None = None,
) -> str:
    """Internal helper — compute self_hash before constructing the frozen entry."""
    payload: dict[str, object] = {
        "sequence": sequence,
        "timestamp": timestamp.isoformat(),
        "actor_kind": actor_kind.value,
        "actor_id": actor_id,
        "decision_type": decision_type,
        "action_payload_hex": action_payload.hex(),
        "gate_verdicts": dict(sorted(gate_verdicts.items())),
        "prior_hash": prior_hash,
        "corrects_sequence": corrects_sequence,
    }
    if timestamp_token_b64 is not None:
        payload["timestamp_token_b64"] = timestamp_token_b64
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()`

- [ ] **Step 6: Add `timestamp_source` field to `AuditLedger` and use it in `append`**

Edit `src/cre_agent_audit/governance/audit_chain.py`:

- old_string: `    store: "LedgerStore" = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # Local import to avoid circular import at module load.
        from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore
        if self.store is None:  # type: ignore[unreachable]
            self.store = InMemoryLedgerStore()`
- new_string: `    store: "LedgerStore" = field(default=None)  # type: ignore[assignment]
    timestamp_source: "TimestampSource" = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # Local imports to avoid circular imports at module load.
        from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore
        from cre_agent_audit.governance.timestamp_source import LocalClockTimestampSource
        if self.store is None:  # type: ignore[unreachable]
            self.store = InMemoryLedgerStore()
        if self.timestamp_source is None:  # type: ignore[unreachable]
            self.timestamp_source = LocalClockTimestampSource()`

- old_string: `        sequence = len(self.store)
        prior_hash = self.chain_head()
        timestamp = now or datetime.now(timezone.utc)

        # Defensive copy so the ledger entry cannot be mutated via caller-held dicts.
        gate_verdicts_copy = dict(gate_verdicts)

        self_hash = _compute_self_hash(
            sequence=sequence,
            timestamp=timestamp,
            actor_kind=actor_kind,
            actor_id=actor_id,
            decision_type=decision_type,
            action_payload=action_payload,
            gate_verdicts=gate_verdicts_copy,
            prior_hash=prior_hash,
            corrects_sequence=corrects_sequence,
        )
        entry = AuditEntry(
            sequence=sequence,
            timestamp=timestamp,
            actor_kind=actor_kind,
            actor_id=actor_id,
            decision_type=decision_type,
            action_payload=action_payload,
            gate_verdicts=gate_verdicts_copy,
            prior_hash=prior_hash,
            self_hash=self_hash,
            corrects_sequence=corrects_sequence,
        )
        self.store.append(entry)
        return entry`
- new_string: `        sequence = len(self.store)
        prior_hash = self.chain_head()

        # Defensive copy so the ledger entry cannot be mutated via caller-held dicts.
        gate_verdicts_copy = dict(gate_verdicts)

        # Compute the payload digest the TimestampSource will attest to.
        # This is the entry's body BEFORE the timestamp is bound — the TSA
        # attests to the payload, then the timestamp + token are folded into
        # the canonical self_hash.
        import hashlib as _hashlib
        payload_digest = _hashlib.sha256(
            json.dumps(
                {
                    "sequence": sequence,
                    "actor_kind": actor_kind.value,
                    "actor_id": actor_id,
                    "decision_type": decision_type,
                    "action_payload_hex": action_payload.hex(),
                    "gate_verdicts": dict(sorted(gate_verdicts_copy.items())),
                    "prior_hash": prior_hash,
                    "corrects_sequence": corrects_sequence,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).digest()

        if now is not None:
            timestamp = now
            timestamp_token: str | None = None
        else:
            attested = self.timestamp_source.stamp(payload_digest)
            timestamp = attested.asserted_at
            timestamp_token = attested.tsr_token_b64

        self_hash = _compute_self_hash(
            sequence=sequence,
            timestamp=timestamp,
            actor_kind=actor_kind,
            actor_id=actor_id,
            decision_type=decision_type,
            action_payload=action_payload,
            gate_verdicts=gate_verdicts_copy,
            prior_hash=prior_hash,
            corrects_sequence=corrects_sequence,
            timestamp_token_b64=timestamp_token,
        )
        entry = AuditEntry(
            sequence=sequence,
            timestamp=timestamp,
            actor_kind=actor_kind,
            actor_id=actor_id,
            decision_type=decision_type,
            action_payload=action_payload,
            gate_verdicts=gate_verdicts_copy,
            prior_hash=prior_hash,
            self_hash=self_hash,
            corrects_sequence=corrects_sequence,
            timestamp_token_b64=timestamp_token,
        )
        self.store.append(entry)
        return entry`

- [ ] **Step 7: Update `verify_chain` to pass `timestamp_token_b64` through**

Edit `src/cre_agent_audit/governance/audit_chain.py`:

- old_string: `            recomputed = _compute_self_hash(
                sequence=entry.sequence,
                timestamp=entry.timestamp,
                actor_kind=entry.actor_kind,
                actor_id=entry.actor_id,
                decision_type=entry.decision_type,
                action_payload=entry.action_payload,
                gate_verdicts=entry.gate_verdicts,
                prior_hash=entry.prior_hash,
                corrects_sequence=entry.corrects_sequence,
            )`
- new_string: `            recomputed = _compute_self_hash(
                sequence=entry.sequence,
                timestamp=entry.timestamp,
                actor_kind=entry.actor_kind,
                actor_id=entry.actor_id,
                decision_type=entry.decision_type,
                action_payload=entry.action_payload,
                gate_verdicts=entry.gate_verdicts,
                prior_hash=entry.prior_hash,
                corrects_sequence=entry.corrects_sequence,
                timestamp_token_b64=entry.timestamp_token_b64,
            )`

- [ ] **Step 8: Add `TimestampSource` import (TYPE_CHECKING form to avoid cycle)**

Edit `src/cre_agent_audit/governance/audit_chain.py`:

- old_string: `from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum`
- new_string: `from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cre_agent_audit.governance.ledger_store import LedgerStore
    from cre_agent_audit.governance.timestamp_source import TimestampSource`

- [ ] **Step 9: Update `ledger_store_sqlite.py` and `ledger_store_jsonl.py` to round-trip the new field**

Edit `src/cre_agent_audit/governance/ledger_store_sqlite.py`:

- old_string: `        self._conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                sequence INTEGER PRIMARY KEY,
                timestamp_iso TEXT NOT NULL,
                actor_kind TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                action_payload BLOB NOT NULL,
                gate_verdicts_json TEXT NOT NULL,
                prior_hash TEXT NOT NULL,
                self_hash TEXT NOT NULL,
                corrects_sequence INTEGER
            )
            """
        )`
- new_string: `        self._conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                sequence INTEGER PRIMARY KEY,
                timestamp_iso TEXT NOT NULL,
                actor_kind TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                action_payload BLOB NOT NULL,
                gate_verdicts_json TEXT NOT NULL,
                prior_hash TEXT NOT NULL,
                self_hash TEXT NOT NULL,
                corrects_sequence INTEGER,
                timestamp_token_b64 TEXT
            )
            """
        )`

- old_string: `    def append(self, entry: AuditEntry) -> None:
        self._conn.execute(
            f"INSERT INTO {self._table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.sequence,
                entry.timestamp.isoformat(),
                entry.actor_kind.value,
                entry.actor_id,
                entry.decision_type,
                entry.action_payload,
                json.dumps(dict(sorted(entry.gate_verdicts.items())), sort_keys=True),
                entry.prior_hash,
                entry.self_hash,
                entry.corrects_sequence,
            ),
        )`
- new_string: `    def append(self, entry: AuditEntry) -> None:
        self._conn.execute(
            f"INSERT INTO {self._table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.sequence,
                entry.timestamp.isoformat(),
                entry.actor_kind.value,
                entry.actor_id,
                entry.decision_type,
                entry.action_payload,
                json.dumps(dict(sorted(entry.gate_verdicts.items())), sort_keys=True),
                entry.prior_hash,
                entry.self_hash,
                entry.corrects_sequence,
                entry.timestamp_token_b64,
            ),
        )`

- old_string: `    def __iter__(self) -> Iterator[AuditEntry]:
        rows = self._conn.execute(
            f"SELECT sequence, timestamp_iso, actor_kind, actor_id, decision_type, "
            f"action_payload, gate_verdicts_json, prior_hash, self_hash, corrects_sequence "
            f"FROM {self._table} ORDER BY sequence ASC"
        )
        for row in rows:
            yield self._row_to_entry(row)`
- new_string: `    def __iter__(self) -> Iterator[AuditEntry]:
        rows = self._conn.execute(
            f"SELECT sequence, timestamp_iso, actor_kind, actor_id, decision_type, "
            f"action_payload, gate_verdicts_json, prior_hash, self_hash, corrects_sequence, "
            f"timestamp_token_b64 "
            f"FROM {self._table} ORDER BY sequence ASC"
        )
        for row in rows:
            yield self._row_to_entry(row)`

- old_string: `    def get(self, sequence: int) -> AuditEntry:
        cur = self._conn.execute(
            f"SELECT sequence, timestamp_iso, actor_kind, actor_id, decision_type, "
            f"action_payload, gate_verdicts_json, prior_hash, self_hash, corrects_sequence "
            f"FROM {self._table} WHERE sequence = ?",
            (sequence,),
        )`
- new_string: `    def get(self, sequence: int) -> AuditEntry:
        cur = self._conn.execute(
            f"SELECT sequence, timestamp_iso, actor_kind, actor_id, decision_type, "
            f"action_payload, gate_verdicts_json, prior_hash, self_hash, corrects_sequence, "
            f"timestamp_token_b64 "
            f"FROM {self._table} WHERE sequence = ?",
            (sequence,),
        )`

- old_string: `    @staticmethod
    def _row_to_entry(row: tuple[object, ...]) -> AuditEntry:
        return AuditEntry(
            sequence=int(row[0]),  # type: ignore[arg-type]
            timestamp=datetime.fromisoformat(str(row[1])),
            actor_kind=ActorKind(str(row[2])),
            actor_id=str(row[3]),
            decision_type=str(row[4]),
            action_payload=bytes(row[5]),  # type: ignore[arg-type]
            gate_verdicts=json.loads(str(row[6])),
            prior_hash=str(row[7]),
            self_hash=str(row[8]),
            corrects_sequence=None if row[9] is None else int(row[9]),  # type: ignore[arg-type]
        )`
- new_string: `    @staticmethod
    def _row_to_entry(row: tuple[object, ...]) -> AuditEntry:
        return AuditEntry(
            sequence=int(row[0]),  # type: ignore[arg-type]
            timestamp=datetime.fromisoformat(str(row[1])),
            actor_kind=ActorKind(str(row[2])),
            actor_id=str(row[3]),
            decision_type=str(row[4]),
            action_payload=bytes(row[5]),  # type: ignore[arg-type]
            gate_verdicts=json.loads(str(row[6])),
            prior_hash=str(row[7]),
            self_hash=str(row[8]),
            corrects_sequence=None if row[9] is None else int(row[9]),  # type: ignore[arg-type]
            timestamp_token_b64=None if row[10] is None else str(row[10]),
        )`

Edit `src/cre_agent_audit/governance/ledger_store_jsonl.py`:

- old_string: `        payload = {
            "sequence": entry.sequence,
            "timestamp": entry.timestamp.isoformat(),
            "actor_kind": entry.actor_kind.value,
            "actor_id": entry.actor_id,
            "decision_type": entry.decision_type,
            "action_payload_hex": entry.action_payload.hex(),
            "gate_verdicts": dict(sorted(entry.gate_verdicts.items())),
            "prior_hash": entry.prior_hash,
            "self_hash": entry.self_hash,
            "corrects_sequence": entry.corrects_sequence,
        }`
- new_string: `        payload: dict[str, object] = {
            "sequence": entry.sequence,
            "timestamp": entry.timestamp.isoformat(),
            "actor_kind": entry.actor_kind.value,
            "actor_id": entry.actor_id,
            "decision_type": entry.decision_type,
            "action_payload_hex": entry.action_payload.hex(),
            "gate_verdicts": dict(sorted(entry.gate_verdicts.items())),
            "prior_hash": entry.prior_hash,
            "self_hash": entry.self_hash,
            "corrects_sequence": entry.corrects_sequence,
            "timestamp_token_b64": entry.timestamp_token_b64,
        }`

- old_string: `            corrects_sequence=d.get("corrects_sequence"),
        )`
- new_string: `            corrects_sequence=d.get("corrects_sequence"),
            timestamp_token_b64=d.get("timestamp_token_b64"),
        )`

- [ ] **Step 10: Run all tests — expect green**

Run: `pytest`
Expected: 142 → 147 tests pass.

- [ ] **Step 11: mypy + ruff + make verify**

Run: `make verify`
Expected: clean.

- [ ] **Step 12: Commit**

```bash
git add src/cre_agent_audit/governance/audit_chain.py src/cre_agent_audit/governance/ledger_store_sqlite.py src/cre_agent_audit/governance/ledger_store_jsonl.py tests/test_audit_chain.py
git commit -m "feat(audit-chain): thread TimestampSource through AuditLedger.append"
```

---

### Task B8: Witness anchor — Rekor + OpenTimestamps

**Files:**
- Create: `src/cre_agent_audit/governance/witness_anchor.py`
- Test: `tests/test_witness_anchor.py`
- Create: `examples/05_witness_anchor/run.py`

- [ ] **Step 1: Write failing tests using a mock HTTP server**

Create `tests/test_witness_anchor.py`:

```python
"""Tests for witness-anchor pattern (Rekor + OpenTimestamps)."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger
from cre_agent_audit.governance.witness_anchor import (
    OpenTimestampsWitness,
    RekorWitness,
    WitnessReceipt,
    anchor_to_witness,
)


class _MockRekorHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 (stdlib API)
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        body = json.dumps({
            "uuid": "deadbeef" * 8,
            "logIndex": 12345,
            "integratedTime": int(datetime.now(timezone.utc).timestamp()),
        }).encode("utf-8")
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:  # noqa: ARG002
        pass  # suppress test output


@pytest.fixture
def mock_rekor() -> "Iterator[str]":  # type: ignore[name-defined]
    server = HTTPServer(("127.0.0.1", 0), _MockRekorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_rekor_witness_returns_receipt(mock_rekor: str) -> None:
    w = RekorWitness(rekor_url=mock_rekor)
    receipt = w.anchor("a" * 64)
    assert isinstance(receipt, WitnessReceipt)
    assert receipt.register_name == "rekor"
    assert receipt.log_index == 12345


def test_anchor_to_witness_writes_audit_entry(mock_rekor: str) -> None:
    ledger = AuditLedger()
    ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="t",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
    )
    anchor_entry = anchor_to_witness(
        ledger=ledger, witness=RekorWitness(rekor_url=mock_rekor)
    )
    assert anchor_entry.decision_type == "witness_anchor"
    assert "witness_register" in anchor_entry.gate_verdicts
    assert anchor_entry.gate_verdicts["witness_register"] == "rekor"
    assert len(ledger.store) == 2
    ledger.verify_chain()


def test_witness_receipt_is_frozen() -> None:
    r = WitnessReceipt(
        register_name="rekor",
        register_url="http://x",
        submitted_at=datetime.now(timezone.utc),
        receipt_blob=b"",
        inclusion_uuid=None,
        log_index=None,
    )
    import dataclasses
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.register_name = "other"  # type: ignore[misc]
```

- [ ] **Step 2: Run — expect failure**

Run: `pytest tests/test_witness_anchor.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write the implementation**

Create `src/cre_agent_audit/governance/witness_anchor.py`:

```python
"""External-witness anchoring pattern — ADR-0012 § 1.4.

The hash-chained `AuditLedger` is internally consistent but not adversarially
tamper-evident on its own. Periodically anchoring `chain_head()` to an external
witness register (Rekor, OpenTimestamps, regulator-side log) converts it to
adversarially tamper-evident: the witness records what the head was at time T,
and a later forger cannot retroactively rewrite the chain without producing
a witness receipt that contradicts the public record.

Anchoring writes the receipt back to the ledger as a `decision_type="witness_anchor"`
entry. This binds the anchor into the same hash chain that's being protected —
tampering with the anchor record requires tampering with every entry after it.

Stdlib-only HTTP. No `python-rekor`, no `opentimestamps-client`. Receipts
preserve the opaque server response verbatim for later verification.
"""

from __future__ import annotations

import http.client
import json
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import urlparse

from cre_agent_audit.governance.audit_chain import ActorKind, AuditEntry, AuditLedger


@dataclass(frozen=True)
class WitnessReceipt:
    register_name: str         # "rekor" | "opentimestamps" | "custom"
    register_url: str
    submitted_at: datetime
    receipt_blob: bytes        # opaque to the ledger; verifier consumes
    inclusion_uuid: str | None
    log_index: int | None


class WitnessRegister(Protocol):
    def anchor(self, chain_head_hex: str) -> WitnessReceipt: ...


@dataclass
class RekorWitness:
    """Sigstore Rekor public transparency log client.

    POSTs a `hashedrekord` entry to Rekor's REST API; receives an inclusion
    UUID + logIndex. Default endpoint is the public Sigstore instance.
    """

    rekor_url: str = "https://rekor.sigstore.dev"
    timeout_s: float = 10.0

    def anchor(self, chain_head_hex: str) -> WitnessReceipt:
        if len(chain_head_hex) != 64:
            raise ValueError("chain_head_hex must be 64 chars (SHA-256)")
        body = json.dumps(
            {
                "apiVersion": "0.0.1",
                "kind": "hashedrekord",
                "spec": {
                    "data": {
                        "hash": {"algorithm": "sha256", "value": chain_head_hex},
                    },
                    "signature": {
                        # Repo policy: anchor the digest only; no signature key
                        # required. Rekor accepts hashedrekord with a placeholder
                        # signature field for transparency-log-only use.
                        "content": "",
                        "format": "x509",
                        "publicKey": {"content": ""},
                    },
                },
            }
        ).encode("utf-8")
        resp_body, status = _post(self.rekor_url + "/api/v1/log/entries", body, self.timeout_s)
        if status not in (200, 201):
            raise RuntimeError(f"Rekor returned HTTP {status}: {resp_body!r}")
        parsed = json.loads(resp_body)
        return WitnessReceipt(
            register_name="rekor",
            register_url=self.rekor_url,
            submitted_at=datetime.now(timezone.utc),
            receipt_blob=resp_body,
            inclusion_uuid=parsed.get("uuid"),
            log_index=parsed.get("logIndex"),
        )


@dataclass
class OpenTimestampsWitness:
    """OpenTimestamps calendar client. Submits the digest; receives a
    pending-commitment receipt that can later be upgraded to a Bitcoin-
    attestation receipt by re-submitting the same opaque blob."""

    calendar_urls: tuple[str, ...] = (
        "https://alice.btc.calendar.opentimestamps.org",
        "https://bob.btc.calendar.opentimestamps.org",
    )
    timeout_s: float = 10.0

    def anchor(self, chain_head_hex: str) -> WitnessReceipt:
        digest = bytes.fromhex(chain_head_hex)
        # OTS calendar API: POST /digest with raw 32-byte SHA-256 digest body.
        last_exc: Exception | None = None
        for url in self.calendar_urls:
            try:
                resp_body, status = _post(url + "/digest", digest, self.timeout_s,
                                          content_type="application/octet-stream")
                if status == 200:
                    return WitnessReceipt(
                        register_name="opentimestamps",
                        register_url=url,
                        submitted_at=datetime.now(timezone.utc),
                        receipt_blob=resp_body,
                        inclusion_uuid=None,
                        log_index=None,
                    )
                last_exc = RuntimeError(f"OTS calendar {url} returned HTTP {status}")
            except Exception as exc:
                last_exc = exc
        raise RuntimeError(f"all OTS calendars failed: {last_exc!r}")


def anchor_to_witness(
    *,
    ledger: AuditLedger,
    witness: WitnessRegister,
    actor_id: str = "system:witness_anchor",
) -> AuditEntry:
    """Anchor `ledger.chain_head()` to `witness`; record the receipt as a new entry."""
    head = ledger.chain_head()
    receipt = witness.anchor(head)
    return ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id=actor_id,
        decision_type="witness_anchor",
        action_payload=receipt.receipt_blob,
        gate_verdicts={
            "witness_register": receipt.register_name,
            "witness_url": receipt.register_url,
            "chain_head_anchored": head,
            "inclusion_uuid": receipt.inclusion_uuid or "",
            "log_index": str(receipt.log_index) if receipt.log_index is not None else "",
        },
    )


def _post(
    url: str,
    body: bytes,
    timeout_s: float,
    *,
    content_type: str = "application/json",
) -> tuple[bytes, int]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported scheme {parsed.scheme!r}")
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if parsed.scheme == "https":
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(host, port, timeout=timeout_s, context=ctx)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=timeout_s)
    try:
        conn.request(
            "POST",
            parsed.path or "/",
            body=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )
        resp = conn.getresponse()
        return resp.read(), resp.status
    finally:
        conn.close()
```

- [ ] **Step 4: Run tests — expect green**

Run: `pytest tests/test_witness_anchor.py -v`
Expected: 3 passed.

- [ ] **Step 5: Add the runnable example**

Create `examples/05_witness_anchor/run.py`:

```python
"""Example — anchor a synthetic ledger to a mock Rekor server.

This example runs entirely against a localhost mock and demonstrates the
anchor-as-ledger-entry semantics. Real deployments swap in
`RekorWitness(rekor_url="https://rekor.sigstore.dev")` or
`OpenTimestampsWitness()`.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger
from cre_agent_audit.governance.witness_anchor import RekorWitness, anchor_to_witness


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        n = int(self.headers.get("Content-Length", 0))
        self.rfile.read(n)
        body = json.dumps(
            {
                "uuid": "00" * 32,
                "logIndex": 1,
                "integratedTime": int(datetime.now(timezone.utc).timestamp()),
            }
        ).encode("utf-8")
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:  # noqa: ARG002
        pass


def main() -> None:
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}"

    ledger = AuditLedger()
    for i in range(3):
        ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id=f"agent:{i}",
            decision_type="screening_decision",
            action_payload=f"applicant {i}".encode(),
            gate_verdicts={"fair_housing": "PASS"},
        )
    print(f"ledger before anchor: {len(ledger.store)} entries, head={ledger.chain_head()[:12]}...")

    anchor_entry = anchor_to_witness(ledger=ledger, witness=RekorWitness(rekor_url=url))
    print(f"anchored — receipt UUID={anchor_entry.gate_verdicts['inclusion_uuid'][:12]}...")
    print(f"ledger after anchor: {len(ledger.store)} entries, head={ledger.chain_head()[:12]}...")
    ledger.verify_chain()
    print("verify_chain: PASS")

    server.shutdown()


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run example smoke-test**

Run: `python examples/05_witness_anchor/run.py`
Expected: `verify_chain: PASS` printed.

- [ ] **Step 7: Update CI workflow**

Edit `.github/workflows/test.yml`:

- old_string: `examples_job_run_marker_keep_in_mind:` (or the equivalent example run step — locate via `grep -n examples .github/workflows/test.yml`)

(If the workflow already loops over `examples/*/run.py`, no change needed — the new example is picked up. Verify with `ls examples/`.)

- [ ] **Step 8: Commit**

```bash
git add src/cre_agent_audit/governance/witness_anchor.py tests/test_witness_anchor.py examples/05_witness_anchor/run.py
git commit -m "feat(audit-chain): witness-anchor pattern (Rekor + OpenTimestamps)"
```

---


