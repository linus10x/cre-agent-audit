# Session Plan — v0.2.0 Public Launch

**Date:** 2026-05-27
**Branch:** `release/v0.2.0` (cut from `main`)
**Local/remote parity:** ✅ Empty diff against `origin/main` (excluding `.claude/settings.local.json`, which is correctly excluded via Kunjar's global gitignore).
**Commits on main pre-session:** 2 — `e9d2f6e` (settled-liability lede), `da70a86` (v0.2.0 patterns + 140 tests + 89% coverage).

## Five council decisions baked into this session

1. **pyyaml → stdlib JSON** (5/5 chambers). Replace YAML runtime parsing with stdlib `json`; preserve human-author YAML via build script + checked-in JSON. Restores Zero-Dependencies parity with sibling.
2. **FINOS folder → private branch + 3-file `governance-artifacts/` carve-out** (4/5 chambers). Protects FINOS WG relationship; preserves visible credibility signal on main.
3. **Two file renames** (5/5 chambers). `governance/fair_housing_gate.py` → `governance/fair_housing_preflight.py`; `governance/tenant_pii_partition.py` → `governance/tenant_pii_residency.py`. Aligns source-tree with canonical pattern vocabulary used in ADRs, config, FINOS AIR.
4. **Stage 2c rigorous primary-source fact-check** (adversarial review F1, F29). Every regulatory citation verified before rewrite; unverifiable facts SOFTENED with fallback wording. RealPage status, Colorado AI Act statute number, TransUnion + SafeRent docket cites, all URLs.
5. **Tamper-evident reframing** (adversarial review F10). SHA-256 chain alone is internally-consistent, not adversarially tamper-evident without external witness. Reframe + add `chain_head_digest()` method for deployer-side anchoring.

## 33 adversarial findings — 26 folded, 7 deferred to v0.2.1

See full plan at `~/.claude/plans/mission-take-linus10x-cre-agent-audit-lovely-marshmallow.md` for the F1–F33 cross-reference table.

**Folded this session:** F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, F13, F14, F15, F16, F17, F18, F19, F20, F21, F22, F23, F25, F26, F27, F28, F29, F30, F31.

**Deferred to v0.2.1 (named in SHIP-RECEIPT):**
- F12 partial — vendor adapter IMPLEMENTATION (v0.2.0 ships design only as ADR-0011)
- F11 partial — MI-threshold learned-proxy DETECTION (v0.2.0 ships lexical-only with bounded ADR claim)
- F20 partial — pluggable persistence backend + RFC 3161 timestamps + witness-anchor INTEGRATION (v0.2.0 ships `chain_head_digest()` method for deployer-side anchoring + design notes)
- F24 partial — Zenodo DOI requires user-side Zenodo+GitHub OAuth (surfaced manually Stage 12.4)
- F32 — named-GC reference quotes (cannot source today; v0.2.1 candidate)
- F33 — full negative-results / failure-mode appendix (Limitations section + LIMITATIONS.md serve as v0.2.0 substitute)

## Time budget (revised)

Original mission prompt: 5h10m. Adversarial-review-folded plan: ~10h50m total across 17 stages. Descope ladder in plan if time-pressed: drop Stage 7 (Big-4 overlay) → Stage 8.4 (PRIOR-ART) + 8.3 (LIMITATIONS) → Stage 8.1 (vendor-clauses) + 8.2 (PE_DUE_DILIGENCE) → Stage 6 (new ADRs). Never descope Stages 2c (fact-check), 3 (renames + tamper-evident reframing), 4.1 (README), 4.2 (ADR disclaimers + bounded claims), or 5 (FINOS).

## Target ship

Today, 2026-05-27 EOD. Launch post fires Mon 2026-06-02 7:30 AM CT (4-day quiet-observation buffer).

## Working branch protocol

All Stage 0–9 work lands on `release/v0.2.0`. Stage 10 opens PR back to main with self-review per `requesting-code-review` skill. Squash-merge to main. Stages 11–16 land directly on main (post-flip).
