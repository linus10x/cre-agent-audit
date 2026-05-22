# Contributing to cre-agent-audit

The repo is open because the failure modes a community catches are an order of magnitude more than the failure modes any single author catches alone. Thank you for considering a contribution.

## What this repo welcomes

- **Regulatory-coverage PRs.** Each PR cites the specific statute or ordinance (with section number) and adds a test that fails on the current code and passes after the change. Examples: state-level SOI ordinance mappings, multi-language lease provenance extensions, new disparate-impact thresholds for a named jurisdiction.
- **Adversarial test cases.** Each issue first, PR with a passing test second. Each test exercises one veto reason code at an edge condition (a near-threshold confidence value · a feature name that almost matches a proxy list · a borderline jurisdiction).
- **Pattern extensions.** New ADRs proposed via PR with the ADR template (Context · Decision · Consequences · Alternatives · Regulatory Anchor · Related). Council bar of 9.5+ content with at least 3 affirmations from the maintainer's review slate before merge.
- **Documentation improvements.** Diagrams, runnable examples, contributor guides.

## Code style

- Python 3.10+
- `from __future__ import annotations` at the top of every module
- Type hints required on every public function
- `ruff check` and `mypy --strict` must pass cleanly before submission
- Branch coverage on changed code stays at or above 85%
- Imports sorted (ruff handles this with `--fix`)

## Test discipline (TDD)

Every code change follows the RED → GREEN → REFACTOR cycle:

1. **RED** — write the failing test first, run pytest to confirm it fails for the expected reason
2. **GREEN** — write the minimum code to pass that test
3. **REFACTOR** — clean up, keep all tests green

PRs that introduce production code without a failing test added in the same diff will be asked for a rewrite.

## Commit message convention

Conventional Commits format:

- `feat: <what was added>`
- `fix: <what was broken>`
- `docs: <what was clarified>`
- `test: <what was tested>`
- `refactor: <what was rearranged>`
- `chore: <what was kept tidy>`

Every commit carries a DCO sign-off line (`git commit -s`).

## ADR additions

Architecture Decision Records live under `docs/adr/NNNN-short-name.md`. To add one:

1. File a discussion or issue with the proposed ADR title and a one-paragraph context.
2. Wait for a maintainer to approve the slot or suggest revisions.
3. PR with the ADR following the template structure (Status · Date · Decider · Context · Decision · Consequences · Regulatory Anchor · CRE-specific notes · Related).
4. Council bar of 9.5+ content with at least 3-of-5 affirmations from the maintainer's review slate before merge.

## Pull request checklist

Before opening a PR:

- [ ] Tests added and failing-before-passing-after verified
- [ ] `ruff check src/ tests/ examples/` is clean
- [ ] `mypy --strict src/` is clean
- [ ] `pytest --cov=src` is at or above 85% branch coverage on changed code
- [ ] Regulatory citation included if the change touches `compliance_rules.yaml`
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] DCO sign-off on every commit

## Issue triage labels

- `good first issue` — bounded scope, clear acceptance, contributor-friendly
- `help wanted` — open for community work, may need maintainer guidance
- `regulatory-coverage` — adds or refines a regulation mapping
- `enhancement` — new feature or pattern
- `bug` — verified incorrect behavior
- `documentation` — clarifies docs without changing behavior
- `v0.2.x` · `v0.3` — milestone tagging
- `quality` — coverage, lint, property-based tests

## Security

For security disclosures see `SECURITY.md`. Do not file public issues for security findings — use the GitHub security advisory channel.

## Code of conduct

Be technically rigorous and personally kind. Disagree on the engineering, not on the engineer. Cite the statute, the test, or the line number — never the person.

## Maintainer contact

Issues and PRs are reviewed by Kunjar Bhaduri at `autonomy-ladder.io`. The repo is part of the Autonomy Ladder™ framework, a private-sector reference architecture for AI agent governance in commercial real estate operations.
