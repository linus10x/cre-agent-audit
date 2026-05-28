# Pull request

## Summary

<!-- One or two sentences describing what this PR changes and why. -->

## Type of change

- [ ] Bug fix (regression or factual-error correction)
- [ ] New pattern or pattern extension (ADR update or new ADR required)
- [ ] Regulatory mapping addition (state mapping, vendor clause, etc.)
- [ ] Documentation update (README, ADR, controls, prior-art, etc.)
- [ ] Refactor / code-quality (no behavior change)
- [ ] CI / tooling (workflow, pre-commit, Makefile)

## Compliance + governance checklist

- [ ] **Regulatory citations:** every new statutory / case / settlement reference cites a primary source (statute text, agency press release, court docket — not a secondary law-firm alert or news article)
- [ ] **Bounded claims:** no overclaim language ("closes the gap," "defensible record of," "tamper-evident" without external witness) — use the bounded phrasing patterns in existing ADRs
- [ ] **Disclaimer:** if this PR adds a new ADR, the ADR carries the disclaimer header
- [ ] **ADR boundary:** if this PR changes a pattern's scope, the "What this does NOT cover" section is updated
- [ ] **Banned words audit:** the diff contains none of: delve, leverage, navigate, journey, transformative, unleash, unlock, game-changer
- [ ] **No banned openers:** "In today's", "As a leader"
- [ ] **Confidentiality:** no client, vendor, or counterparty identified in the diff (use generic framing: "PE-backed CRE operating company," "a top-3 wealth-platform vendor")

## Engineering checklist

- [ ] `make verify` passes locally (ruff + ruff format + mypy --strict + pytest --cov-fail-under=85 + JSON-sync + wheel-build + import-smoke)
- [ ] New code paths covered by tests; coverage held ≥ 85%
- [ ] If `compliance_rules.yaml` changed, `scripts/build_compliance_json.py` was re-run and the JSON is committed in sync
- [ ] No new runtime dependencies introduced (zero-deps invariant); dev deps only if necessary
- [ ] Public API changes reflected in `src/cre_agent_audit/__init__.py` `__all__`

## Documentation checklist

- [ ] README updated if user-visible behavior changed
- [ ] ADR added or updated if architectural decision changed
- [ ] CHANGELOG entry added under `[Unreleased]`
- [ ] If this PR adds a control, `docs/controls/CTRL-NNN-<slug>.md` is created or updated
- [ ] If this PR maps to a new framework, `docs/MAPPING-MATRICES.md` is updated

## Test plan

<!-- Bulleted list of what was tested locally and how. -->

- [ ] Local: `make verify` green
- [ ] Local: relevant `examples/*/run.py` exercised
- [ ] CI: matrix Python 3.10 / 3.11 / 3.12 green

## Related issues / ADRs

<!-- Closes #123, references ADR-0008, etc. -->
