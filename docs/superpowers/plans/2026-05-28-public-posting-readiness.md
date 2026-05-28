# Public-Posting Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land repo polish on `main` + draft a chamber-passed LinkedIn long-form and X short-form on the topic "your hash chain can be perfect and your verifier can still lie," ready for the user to publish without further edits.

**Architecture:** Three artifact streams. (1) README freshness + discoverability + voice scrub committed to `main`. (2) Two draft files under `docs/posts/` carrying the LinkedIn long-form and the two X variants. (3) A council-pass block appended to each draft after a 10/10 review against the brand-work slate (Clark / Welsh / Adler / López de Prado / Gil). No publish, no tag, no Zenodo.

**Tech Stack:** git, gh, ripgrep (`rg`) or grep, pytest, ruff, mypy, Python 3.10+. No new dependencies. Drafts are pure markdown.

**Spec reference:** [`docs/superpowers/specs/2026-05-28-public-posting-readiness-design.md`](../specs/2026-05-28-public-posting-readiness-design.md)

**Working tree assumption:** branch is `main` at `a2c9b07` (the spec commit) or later. All work in this plan happens on `main`.

---

## File structure

| Path | New / Modify | Responsibility |
|---|---|---|
| `README.md` | Modify | Freshen stats, add v0.2.1.dev2 in-flight indicator, add Failure-modes discoverability + ADR-0013 entry + MI Proxy / VendorScoreGate / AuditConsumer pattern summaries. |
| `docs/posts/2026-05-28-verifier-lie-linkedin.md` | New | LinkedIn long-form draft (220-word target) + 5-chamber council pass block. |
| `docs/posts/2026-05-28-verifier-lie-x.md` | New | X single-tweet variant + X 5-tweet thread variant + 5-chamber council pass block per variant. |
| `.gitignore` | Conditional modify | Only if Task 6 determines `creaudit.md` is internal scratch. |

---

## Task 1: Confirm current test count and coverage

**Files:** none (read-only).

- [ ] **Step 1: Run the full test suite, capture pass count.**

```bash
cd "/Users/kunjarbhaduri/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
python3 -m pytest -q 2>&1 | tail -3
```

Expected: `234 passed in <N>s`. If different, use the actual number in Task 2.

- [ ] **Step 2: Run pytest-cov and capture branch coverage.**

```bash
python3 -m pytest --cov=src/cre_agent_audit --cov-report=term-missing -q 2>&1 | tail -5
```

Expected: a "TOTAL ... XX%" line. Record the percentage for Task 2. If pytest-cov is not installed or the command fails, fall back to the README's existing 89% number and note in the commit that coverage was not re-measured this session.

---

## Task 2: README polish — stats, badges, discoverability, patterns

**Files:**
- Modify: `README.md` (multiple locations)

The README is 324 lines. Edits are surgical — do not rewrite sections that are already accurate. The line-number references below are approximate; locate by content match.

- [ ] **Step 1: Read the current "At a glance" table.**

```bash
grep -n "## At a glance" README.md
```

Note the line range (the table follows for ~10 lines).

- [ ] **Step 2: Update test count.**

```python
# Edit pattern: replace the literal "142 passing" with the value captured in Task 1 (expected "234 passing").
```

Use the Edit tool with:
- `old_string`: `| Tests | 142 passing |`
- `new_string`: `| Tests | 234 passing |`

- [ ] **Step 3: Update coverage if Task 1 produced a different number.**

```
old_string: | Branch coverage | 89% |
new_string: | Branch coverage | <Task 1 value>% |
```

Skip this step if Task 1 fell back to the existing 89%.

- [ ] **Step 4: Add an in-flight pre-release badge.**

The README currently has these badges (around lines 5–11). Insert a new badge below the `v0.2.0` release badge and above the Autonomy Ladder family badge:

```markdown
[![v0.2.1.dev2 in flight](https://img.shields.io/badge/in--flight-v0.2.1.dev2-orange)](CHANGELOG.md)
```

Use the Edit tool with:
- `old_string`: ``[![v0.2.0](https://img.shields.io/badge/release-v0.2.0-blue)](https://github.com/linus10x/cre-agent-audit/releases/tag/v0.2.0)
[![Autonomy Ladder™ family]``
- `new_string`: ``[![v0.2.0](https://img.shields.io/badge/release-v0.2.0-blue)](https://github.com/linus10x/cre-agent-audit/releases/tag/v0.2.0)
[![v0.2.1.dev2 in flight](https://img.shields.io/badge/in--flight-v0.2.1.dev2-orange)](CHANGELOG.md)
[![Autonomy Ladder™ family]``

- [ ] **Step 5: Add a "Failure modes" entry to the table of contents.**

Find the line `- [Limitations and what this stack does NOT do](#limitations-and-what-this-stack-does-not-do)` and add the new entry above it.

Use the Edit tool with:
- `old_string`: `- [Limitations and what this stack does NOT do](#limitations-and-what-this-stack-does-not-do)`
- `new_string`: `- [Failure modes](#failure-modes)
- [Limitations and what this stack does NOT do](#limitations-and-what-this-stack-does-not-do)`

- [ ] **Step 6: Add the "Failure modes" body section.**

Find the heading `## Limitations and what this stack does NOT do` and add a new section above it.

Use the Edit tool with:
- `old_string`: `## Limitations and what this stack does NOT do`
- `new_string`: ``## Failure modes

[`FAILURE-MODES.md`](FAILURE-MODES.md) is the repo-root matrix of 8 adversarial / partition / corruption failure-mode classes: storage drift, sequence gap / split-brain, adversarial replay in-trust-boundary, timestamp tampering, witness disagreement, backend permission revocation, **verifier compromise** (the Module Integrity Proxy in ADR-0013), and **vendor AI scoring drift** (the VendorScoreGate). Each row names the detection mechanism (resolved to a real callable in the codebase or marked `NOT YET IMPLEMENTED` with a tracking marker) and the recovery action. A companion test enforces doc/code parity — the build fails on drift.

The audit chain is **tamper-detecting within its trust boundary by default**. Tamper-*evidence* against an attacker who controls the ledger host requires the external witness pattern (RFC 3161 trusted timestamps + Sigstore Rekor / OpenTimestamps), and tamper-detection of the *verifier itself* requires the MI Proxy hook (out-of-band SHA-256 + HMAC attestation by default; opt-in SLSA / in-toto / Sigstore cosign).

## Limitations and what this stack does NOT do``

- [ ] **Step 7: Add ADR-0013 to the ADR list.**

Locate the section where ADR-0010 / ADR-0011 / ADR-0012 are mentioned (likely in "Patterns included" or "Architecture overview"). The repo currently has ADRs 0001–0013. If the README lists ADRs explicitly with one-liners, add an ADR-0013 entry. If the README only references the count or directory, no edit is needed.

Grep first:

```bash
grep -n "ADR-0012\|ADR-0011\|ADR-0010" README.md | head -10
```

If results show explicit per-ADR one-liners, add:

```markdown
- **ADR-0013 — MI Proxy** · out-of-band Module Integrity verifier chain-of-custody; default HMAC backend, opt-in SLSA / in-toto / Sigstore cosign; fail-closed via `IntegrityVerificationError` when attestation fails.
```

If results show only counts or directory references, skip this step.

- [ ] **Step 8: Add MI Proxy / VendorScoreGate / AuditConsumer to "Patterns included" section.**

Find `## Patterns included` heading and inspect the existing format. If it uses ADR numbers + one-liners, append three entries matching the format. If it uses a different format, match that format.

Skip if the section is already up to date (it predates ADR-0013 so it almost certainly is not).

- [ ] **Step 9: Verify the edits render correctly.**

```bash
wc -l README.md && head -100 README.md | tail -50
```

Confirm the new badge line, the new TOC entry, and the new Failure modes section all appear in the right places. No `<!-- placeholder -->` left over.

- [ ] **Step 10: Confirm no banned terms introduced.**

```bash
grep -iE "delve|leverage|navigate|journey|transformative|unleash|unlock|game-changer|in today's|as a leader|robust|cutting-edge|seamless" README.md
```

Expected: zero hits. If hits appear, the new content needs revision. Banned terms list per CLAUDE.md voice rule. Note: a hit on "leverage" in a verb form ("leverage existing X") is banned; "leveraged" as in financial terminology in a quoted regulatory citation is not — context-check before editing.

- [ ] **Step 11: Defer commit.** The README commit is bundled with Tasks 3–6 in Task 7.

---

## Task 3: Repo-wide grep — banned terms (auto-fix)

**Files:** any file with a hit (read-only at this task; edits in Step 3).

Per spec D1.5: banned terms in committed files under `src/`, `docs/`, root `.md`, `tests/`, or `examples/` are fixed at the line automatically (terms are unambiguously banned).

- [ ] **Step 1: Run the grep across scoped paths.**

```bash
cd "/Users/kunjarbhaduri/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
grep -RInE 'delve|leverage|navigate|journey|transformative|unleash|unlock|game-changer|in today'\''s|as a leader|robust|cutting-edge|seamless' \
  --include='*.md' --include='*.py' --include='*.yml' --include='*.yaml' \
  README.md ARCHITECTURE.md CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTING.md DISCLAIMER.md FAILURE-MODES.md ROADMAP.md SECURITY.md \
  src/ docs/ tests/ examples/ 2>/dev/null | head -50
```

Note: `creaudit.md` is included only if Task 6 decides it stays public.

- [ ] **Step 2: For each hit, classify.**

For each hit, judgment classes:
- (a) **Auto-fixable banned-term usage in framework voice**: rewrite the line to a neutral synonym (e.g., "leverage" → "use" or "build on"; "robust" → "tested" or specific quantitative claim; "seamless" → name what is actually preserved, e.g., "backward-compatible").
- (b) **In-quotation regulatory citation**: the term appears inside a quote from a primary source (FTC consent order, statute text). LEAVE — that's a citation, not framework voice.
- (c) **In a variable name or technical identifier**: e.g., `leverage_ratio` in a financial-services adapter (unlikely in this repo). LEAVE — that's a domain term.

- [ ] **Step 3: Apply (a) fixes one file at a time.**

For each file with class-(a) hits:
- Read the file (or affected range)
- Use the Edit tool to replace the banned term with the neutral synonym
- Re-grep that file to confirm the hit is gone

- [ ] **Step 4: Re-run the grep across the same scope.**

```bash
grep -RInE 'delve|leverage|navigate|journey|transformative|unleash|unlock|game-changer|in today'\''s|as a leader|robust|cutting-edge|seamless' \
  --include='*.md' --include='*.py' --include='*.yml' --include='*.yaml' \
  README.md ARCHITECTURE.md CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTING.md DISCLAIMER.md FAILURE-MODES.md ROADMAP.md SECURITY.md \
  src/ docs/ tests/ examples/ 2>/dev/null | wc -l
```

Expected: lower than Step 1, with the remaining hits being class (b) or (c) only. Surface the count in the commit message.

- [ ] **Step 5: Defer commit** (bundled in Task 7).

---

## Task 4: Repo-wide grep — banned names (surface, do not auto-edit)

**Files:** any file with a hit (read-only).

Per spec D1.6: banned names are context-sensitive. Surface to the user; do not auto-edit.

- [ ] **Step 1: Run the grep.**

Populate `$NAMES_PATTERN` from the four banned names listed in `CLAUDE.md` § "Refusals" before running. The pattern is **not** embedded in this committed plan, so this plan file does not itself name the entities the rule forbids.

```bash
cd "/Users/kunjarbhaduri/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
NAMES_PATTERN='<populate from CLAUDE.md>'
grep -RIni "$NAMES_PATTERN" \
  --include='*.md' --include='*.py' --include='*.yml' --include='*.yaml' \
  . 2>/dev/null | grep -v "^./.git/" | head -30
```

- [ ] **Step 2: Report findings inline (in the chat, not a file).**

For each hit, report: `<file>:<line>: <context excerpt>`. The user decides per hit. No edits applied in this task.

- [ ] **Step 3: If user approves an edit in chat, apply it now and re-grep.** Otherwise skip — Task 7 commits whatever state results.

---

## Task 5: APEX / ShadowForge / SPARTA framing check

**Files:** any file with a hit (read-only).

Per spec D1.7 and CLAUDE.md: if mentioned at all, framing must read as "private quantitative options research program with López de Prado as named advisor." This repo is `cre-agent-audit` (CRE), not the trading repo — likely no hits.

- [ ] **Step 1: Run the grep.**

```bash
cd "/Users/kunjarbhaduri/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
grep -RIni 'APEX\|ShadowForge\|SPARTA' \
  --include='*.md' --include='*.py' --include='*.yml' --include='*.yaml' \
  . 2>/dev/null | grep -v "^./.git/" | head -20
```

- [ ] **Step 2: For each hit, classify.**

- (a) Mention of APEX-as-trading-system → must use the public-safe framing. Edit if needed.
- (b) Acronym hit unrelated to the trading program (e.g., "APEX" as an acronym for some unrelated framework) → leave.

- [ ] **Step 3: Apply (a) edits.** None expected in this repo.

---

## Task 6: `creaudit.md` scratch file disposition

**Files:**
- Read: `creaudit.md` (76K)
- Conditional modify: `.gitignore`, `creaudit.md` (cached state)

Per spec D1.8: decide whether `creaudit.md` is internal scratch (gitignore + remove from cache) or public material (leave).

- [ ] **Step 1: Read first 80 lines of `creaudit.md`.**

```python
# Use the Read tool with file_path=creaudit.md, limit=80
```

Classify by content:
- Engineer-credible top-level doc with clean structure → leave as public.
- Working draft with TODOs, internal notes, scratch reasoning, dated session journal → internal scratch.

- [ ] **Step 2: Surface the classification inline.**

Report: "creaudit.md classified as <public | internal scratch>. Recommendation: <leave | gitignore + git rm --cached>."

- [ ] **Step 3: If internal scratch and user does not object, apply.**

```bash
echo "creaudit.md" >> .gitignore
git rm --cached creaudit.md
```

If public, no action.

- [ ] **Step 4: Defer commit** (bundled in Task 7).

---

## Task 7: Commit and push the repo-polish bundle

**Files:** all changes from Tasks 2–6.

- [ ] **Step 1: Inspect the staged + unstaged diff.**

```bash
cd "/Users/kunjarbhaduri/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
git status
git diff
```

Confirm only intended files appear: `README.md`, possibly `.gitignore`, possibly individual `*.md` files from Task 3 voice scrub.

- [ ] **Step 2: Run pre-commit local gates.**

```bash
python3 -m pytest -q 2>&1 | tail -3
ruff check src/ tests/ 2>&1 | tail -3
ruff format --check src/ tests/ scripts/ 2>&1 | tail -3
```

Expected: 234 passed, ruff check + format clean. No source code was touched in Tasks 2–6; the gates should pass without surprises. If they fail, stop and surface — the polish work shouldn't break the gates.

- [ ] **Step 3: Stage + commit.**

```bash
git add README.md .gitignore <any other files touched in Tasks 3–6>
git commit -m "$(cat <<'EOF'
docs(readme): freshen stats, add FAILURE-MODES + ADR-0013 discoverability, voice scrub

PR #31 post-merge polish on main:
- README At a glance: 142 → 234 tests (coverage verified at <%>)
- New v0.2.1.dev2 in-flight badge (separate from the v0.2.0 stable badge)
- New Failure modes section in TOC + body linking FAILURE-MODES.md
- ADR-0013 (MI Proxy) added to the ADR catalog
- MI Proxy / VendorScoreGate / AuditConsumer one-liners under Patterns
- Voice scrub: <N> banned-term replacements across <file list>

No code changed; no tests changed. Pytest + ruff + mypy still clean.
EOF
)"
```

- [ ] **Step 4: Push to origin/main.**

```bash
git push origin main
```

- [ ] **Step 5: Wait for CI.**

```bash
until gh run list --branch main --limit 1 --json status -q '.[0].status' 2>/dev/null | grep -q completed; do sleep 5; done
gh run list --branch main --limit 1 --json status,conclusion,headSha 2>&1 | head -2
```

Expected: `"conclusion":"success"`. If `"failure"`, debug + fix on `main` (it's docs-only — likely a ruff format check on a `.md` if anything; address per the CI log).

---

## Task 8: LinkedIn long-form draft

**Files:**
- Create: `docs/posts/2026-05-28-verifier-lie-linkedin.md`

Per spec D2: target 220 words. Structure: Hook · cost · what shipped · what's deferred · provocation · hashtags.

- [ ] **Step 1: Create the file with the draft.**

Use the Write tool with the content below. Word count target: 200–240 words (CLAUDE.md range 150–300 with 220 as the spec target). Final text:

```markdown
# LinkedIn long-form — verifier lie · 2026-05-28

**Status:** Draft. Not published. Council-pass block appended below.

---

Your hash chain can be perfect, and your verifier can still lie.

That is the gap behind the three settled-liability anchors every CRE operator now writes against. TransUnion Rental Screening Solutions — joint FTC and CFPB consent orders, October 2023, $15M civil money penalty. Louis v. SafeRent Solutions — class settlement in the District of Massachusetts, November 2024, approximately $2.275M with a five-year score-use injunction on voucher-holder applicants. United States v. RealPage et al. — DOJ plus eight state attorneys general, August 2024, ongoing antitrust litigation. None of these defendants had a missing chain. They had audit that did not, or could not, prove what the system was bounded to do.

`cre-agent-audit` v0.2.0 shipped the foundation: nine MIT-licensed governance patterns, primary-source citations, zero runtime dependencies, hash-chained ledger. v0.2.1.dev2 — merged today — adds four pieces I wanted closer to the trust boundary. A `FAILURE-MODES.md` matrix the build refuses to let drift. An MI Proxy for verifier chain-of-custody (ADR-0013) — fail-closed when the verifier's own attestation does not check. A `VendorScoreGate` that detects silent vendor-model drift on the same input. A consolidated `AuditConsumer` so the seams inject through one interface.

Three items remain before I cut v0.2.1: fair-housing MI-threshold detector, named-GC reference quotes, and the `audit-verify` extra. Those land next.

If your audit verifier itself is compromised, how would you know?

→ [github.com/linus10x/cre-agent-audit](https://github.com/linus10x/cre-agent-audit) · [autonomy-ladder.io](https://autonomy-ladder.io)

#AIGovernance #CommercialRealEstate #CTO #ChiefAIOfficer #LegacyModernization #FinTech

> Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.

---

## Council pass — 2026-05-28

| Mentor | Score | Note |
|---|---|---|
| Dorie Clark | __/10 | _filled in Task 11_ |
| Justin Welsh | __/10 | _filled in Task 11_ |
| Lou Adler | __/10 | _filled in Task 11_ |
| Marcos López de Prado | __/10 | _filled in Task 11_ |
| Elad Gil | __/10 | _filled in Task 11_ |
```

- [ ] **Step 2: Count words.**

```bash
awk '/^---$/{c++; next} c==1 && !/^#/ && !/^>/ && !/^→/ {print}' docs/posts/2026-05-28-verifier-lie-linkedin.md | wc -w
```

Expected: 200–240 (target 220). If wildly off, revise the body until in range.

- [ ] **Step 3: Banned-term check on the draft.**

```bash
grep -iE 'delve|leverage|navigate|journey|transformative|unleash|unlock|game-changer|in today'\''s|as a leader|robust|cutting-edge|seamless' docs/posts/2026-05-28-verifier-lie-linkedin.md
```

Expected: zero hits.

- [ ] **Step 4: Banned-name check on the draft.**

```bash
# Populate $NAMES_PATTERN per CLAUDE.md § Refusals (same pattern as Task 4).
grep -iE "$NAMES_PATTERN" docs/posts/2026-05-28-verifier-lie-linkedin.md
```

Expected: zero hits.

- [ ] **Step 5: Defer commit** (bundled in Task 13).

---

## Task 9: X — single-tweet variant

**Files:**
- Create / append: `docs/posts/2026-05-28-verifier-lie-x.md`

Per spec D3 variant (a): ≤ 280 characters including the URL. Target ≤ 260 to leave URL slack.

- [ ] **Step 1: Create the file with variant (a).**

Use the Write tool. Final text for the variant:

```markdown
# X drafts — verifier lie · 2026-05-28

**Status:** Drafts. Not published. Two variants below. Council-pass blocks per variant.

---

## Variant (a) — single tweet

Your hash chain can be perfect, and your verifier can still lie.

`cre-agent-audit` v0.2.1.dev2 (merged) ships an MI Proxy: out-of-band attestation, fail-closed on mismatch. Plus a vendor-score-drift gate.

If your audit verifier is compromised, how would you know?

→ github.com/linus10x/cre-agent-audit

### Council pass — variant (a) — 2026-05-28

| Mentor | Score | Note |
|---|---|---|
| Dorie Clark | __/10 | _filled in Task 12_ |
| Justin Welsh | __/10 | _filled in Task 12_ |
| Lou Adler | __/10 | _filled in Task 12_ |
| Marcos López de Prado | __/10 | _filled in Task 12_ |
| Elad Gil | __/10 | _filled in Task 12_ |
```

- [ ] **Step 2: Confirm character count of the tweet body only.**

```bash
# Extract everything between "## Variant (a) — single tweet" and the next "###" header, strip markdown framing, count chars.
sed -n '/^## Variant (a)/,/^### Council/p' docs/posts/2026-05-28-verifier-lie-x.md | sed '1d;$d' | tr -d '\n' | wc -c
```

Expected: ≤ 280, target ≤ 260. If over, tighten the tweet body until in range.

- [ ] **Step 3: Banned-term and banned-name check on the file.** Same commands as Task 8 Steps 3–4 against this file.

---

## Task 10: X — 5-tweet thread variant

**Files:**
- Append to: `docs/posts/2026-05-28-verifier-lie-x.md`

Per spec D3 variant (b): 5 tweets, each ≤ 280 chars. No hashtags inside the thread; one hashtag set on the closing tweet.

- [ ] **Step 1: Append variant (b) to the file.**

Use the Edit tool with `old_string` matching the last line of variant (a)'s council block and append:

```markdown
---

## Variant (b) — 5-tweet thread

**1/5** Your hash chain can be perfect, and your verifier can still lie.

That is the gap behind every CRE-AI settled-liability anchor on the record.

**2/5** TransUnion Rental Screening — FTC + CFPB, $15M, Oct 2023. SafeRent — D. Mass. class settlement, ~$2.275M, Nov 2024. RealPage — DOJ + 8 state AGs, ongoing.

None had a missing chain. They had audit that could not prove bounded operation.

**3/5** `cre-agent-audit` v0.2.1.dev2 (merged) closes four pieces closer to the trust boundary:

· FAILURE-MODES.md matrix the build refuses to let drift
· MI Proxy (ADR-0013) — fail-closed verifier attestation
· VendorScoreGate — silent-vendor-drift detection
· consolidated AuditConsumer

**4/5** Three items still gate the v0.2.1 tag: fair-housing MI-threshold detector, named-GC reference quotes, the `audit-verify` extra wiring.

Those land next. The framework matures in public.

**5/5** If your audit verifier itself is compromised, how would you know?

→ github.com/linus10x/cre-agent-audit

#AIGovernance #CommercialRealEstate #CTO #ChiefAIOfficer

### Council pass — variant (b) — 2026-05-28

| Mentor | Score | Note |
|---|---|---|
| Dorie Clark | __/10 | _filled in Task 12_ |
| Justin Welsh | __/10 | _filled in Task 12_ |
| Lou Adler | __/10 | _filled in Task 12_ |
| Marcos López de Prado | __/10 | _filled in Task 12_ |
| Elad Gil | __/10 | _filled in Task 12_ |
```

- [ ] **Step 2: Per-tweet character count.**

```bash
# Each tweet block starts with "**N/5**". Extract bodies and count.
awk '/^\*\*[1-5]\/5\*\*/{flag=1; body=""; next} /^---$/||/^###/{if(flag){print length(body); flag=0}} flag{body=body $0}' docs/posts/2026-05-28-verifier-lie-x.md
```

Expected: 5 numbers each ≤ 280. If any over, revise that tweet only.

- [ ] **Step 3: Banned-term and banned-name check on the file.** Same commands as Task 8 Steps 3–4 against the full X drafts file.

---

## Task 11: Council pass — LinkedIn draft

**Files:**
- Modify: `docs/posts/2026-05-28-verifier-lie-linkedin.md` (council-pass block only)

Per spec D4 + § "Council slate": 10/10 from each of the 5; capped at 3 revision passes.

- [ ] **Step 1: Score the draft against each mentor's perspective.**

For each mentor, write 1–2 sentences in their voice:

- **Dorie Clark**: Does the post claim a recognized-expert territory? Is the increment narrated (what landed, what's still deferred)? Score 1–10.
- **Justin Welsh**: Does the hook earn the next sentence? Is the structure tight (hook · payoff · CTA)? Is there one clear takeaway? Score 1–10.
- **Lou Adler**: Does this read for a CTO / Chief AI Officer audience? Is the executive POV credible (numbers, scar-tissue, not aspiration)? Score 1–10.
- **Marcos López de Prado**: Are the primary-source citations rigorous (case names, dates, dollar amounts, court districts)? Zero buzzwords? Score 1–10.
- **Elad Gil**: Does this distinguish from competition (other AI audit tools just log; this one closes verifier-integrity)? Is the venture-credibility intact? Score 1–10.

- [ ] **Step 2: Fill in the council-pass block.**

Replace each `__/10 | _filled in Task 11_` with the score + a 1-sentence note.

- [ ] **Step 3: Decide pass / revise.**

- All 5 are 10/10 → PASS. Continue to Task 12.
- Any < 10 → revise the relevant draft section, re-score the affected mentor(s). Capped at 3 revision passes total.
- 3 revision passes without 10/10 → STOP. Surface the blocker and skip Task 13. Do not commit a < 10 draft.

---

## Task 12: Council pass — X drafts (both variants)

**Files:**
- Modify: `docs/posts/2026-05-28-verifier-lie-x.md` (two council-pass blocks)

- [ ] **Step 1: Score variant (a) and variant (b) independently against the same 5 mentors.**

Same mentor checklist as Task 11. Score each variant separately. Different variants may score differently — the single tweet trades depth for sharpness; the thread trades sharpness for completeness.

- [ ] **Step 2: Fill in both council-pass blocks.**

- [ ] **Step 3: Decide pass / revise per variant.**

Same rules as Task 11 Step 3. Each variant capped at 3 revision passes independently. If both variants pass 10/10, both stay in the file. If one variant fails to reach 10/10 after 3 passes, surface the blocker and leave the failed variant in the file with its scores; the user can pick the passing variant.

---

## Task 13: Commit and push the post drafts

**Files:**
- `docs/posts/2026-05-28-verifier-lie-linkedin.md`
- `docs/posts/2026-05-28-verifier-lie-x.md`

- [ ] **Step 1: Verify both files exist and contain final content + council blocks.**

```bash
ls -la docs/posts/
wc -l docs/posts/2026-05-28-verifier-lie-linkedin.md docs/posts/2026-05-28-verifier-lie-x.md
```

- [ ] **Step 2: Final banned-term + banned-name sweep across both files.**

```bash
grep -iE 'delve|leverage|navigate|journey|transformative|unleash|unlock|game-changer|in today'\''s|as a leader|robust|cutting-edge|seamless' docs/posts/2026-05-28-verifier-lie-linkedin.md docs/posts/2026-05-28-verifier-lie-x.md
grep -iE "$NAMES_PATTERN" docs/posts/2026-05-28-verifier-lie-linkedin.md docs/posts/2026-05-28-verifier-lie-x.md
```

Both expected: zero hits.

- [ ] **Step 3: Stage + commit.**

```bash
git add docs/posts/2026-05-28-verifier-lie-linkedin.md docs/posts/2026-05-28-verifier-lie-x.md
git commit -m "$(cat <<'EOF'
docs(posts): drafts — verifier-lie LinkedIn long-form + X (single + thread)

Drafts only. Not published. Both files carry council-pass blocks scored
10/10 against the brand-work slate (Dorie Clark · Justin Welsh · Lou
Adler · Marcos López de Prado · Elad Gil).

Anchor framing: most "AI audit" tools log decisions; this framework
treats the verifier itself as a trust-boundary asset and ships an out-
of-band integrity proxy. ADR-0013 (MI Proxy) is the central anchor;
FAILURE-MODES.md Row 7 (Verifier compromise) is the secondary.

Constraints applied: no specific carrier or vendor customer named;
RealPage stays "ongoing litigation"; no Colorado law reference;
banned-term + banned-name sweeps zero hits; disclaimer line present.

User clicks publish. No publish from this session.
EOF
)"
```

- [ ] **Step 4: Push.**

```bash
git push origin main
```

- [ ] **Step 5: Wait for CI.**

```bash
until gh run list --branch main --limit 1 --json status -q '.[0].status' 2>/dev/null | grep -q completed; do sleep 5; done
gh run list --branch main --limit 1 --json status,conclusion,headSha 2>&1 | head -2
```

Expected: success. If failure, the only plausible cause is a markdown lint somewhere — fix on main and re-push.

---

## Task 14: Sign-off message

**Files:** none (inline summary in the chat).

- [ ] **Step 1: Compose the sign-off message.**

Inline content includes:
- One-paragraph what-shipped summary
- Repo-polish diff summary (which README sections + which voice-scrub files)
- LinkedIn draft (full text, ready to paste)
- X variant (a) (full text, ready to paste)
- X variant (b) (full text, ready to paste — numbered tweets clearly)
- Council scores per draft (5 mentors × 3 drafts)
- One sentence on what's NOT in scope (no tag, no publish, no DOI)
- One sentence: "Publish when ready."

- [ ] **Step 2: Send.**

This closes the session.

---

## Self-review

Done after the plan was written.

1. **Spec coverage:** D1 → Tasks 2–7. D2 → Task 8. D3 → Tasks 9–10. D4 → Tasks 11–12. D5 → Task 14. Every spec deliverable has at least one task.
2. **Placeholder scan:** No "TBD", "TODO", or "fill in later" in the executable steps. The council-pass blocks have `_filled in Task 11_` / `_filled in Task 12_` placeholders that are *intentionally* filled by the later task — the plan names which task fills them, so this is not a placeholder ambiguity.
3. **Type consistency:** Function / file names match across tasks: `MIProxy`, `VendorScoreGate`, `AuditConsumer`, `FAILURE-MODES.md`, `docs/posts/2026-05-28-verifier-lie-linkedin.md`, `docs/posts/2026-05-28-verifier-lie-x.md` used identically throughout.
4. **Ambiguity check:** Pass / revise rules in Tasks 11–12 are explicit (10/10 or revise; capped at 3 passes; what to do on cap failure). Auto-fix vs. surface rules in Tasks 3–4 are explicit per the spec.

No issues to fix inline.

---

## Execution handoff

Plan complete. Per the executing-plans skill chain already active in this session, this plan is executed inline (not subagent-driven), with checkpoints at Task 7 commit (after repo polish) and Task 13 commit (after drafts), and the council-pass tasks (11–12) as the quality gate.
