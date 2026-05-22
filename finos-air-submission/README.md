# FINOS AI Governance Framework — Submission Package

> Pre-staged contents for an 18-file PR to `github.com/finos/ai-governance-framework`.
> The Autonomy Ladder™ framework's 9 governance patterns are mapped to FINOS AIR
> risk + mitigation entries, ready for upstream submission per Brand Unbeatable
> Supplement Move 1 (council 9.74/10).

## What this directory is

The 9 patterns shipped in `src/cre_agent_audit/governance/` map to 18 FINOS AIR
entries — one risk entry per pattern (naming the failure mode), one mitigation
entry per pattern (crediting Autonomy Ladder™ as the named pattern).

```
risks/operational/        4 entries — DEFCON · Audit Chain · Shadow Mode · Lease Provenance
risks/regulatory-and-compliance/   4 entries — Sovereign Veto · Autonomy Ladder · Regulation Mapping · Fair Housing
risks/security/           1 entry  — Tenant PII Residency
mitigations/              9 entries crediting Autonomy Ladder™
```

## Submission timeline

| Week | Action |
|---|---|
| Week 7 | Fully draft the 16 stub files (this directory ships 2 fully-drafted + 16 stubs) |
| Week 7 council pass | 5-mentor slate against the 18-file PR · 9.5+ content bar |
| Week 8 ship | Open the PR against `finos/ai-governance-framework`. DCO sign every commit. |
| Week 10-12 | FINOS maintainer review cycle |
| Week 12+ | On acceptance: co-branding lands on autonomy-ladder.io · both repos' READMEs · LinkedIn About paragraph zero · deck cover slide |

## Per-pattern ID assignments

These risk IDs continue the FINOS AIR taxonomy from the public counts as of
2026-05-22 (11 OP · 9 SEC · 3 RC). The maintainer reserves final ID assignment;
the IDs below are best-effort placeholders pending PR review.

| Source ADR | Proposed Risk ID | Proposed Mitigation ID | Control Type |
|---|---|---|---|
| ADR-0001 DEFCON state machine | `AIR-OP-012` | `AIR-MIT-OP-DEFCON-01` | Preventative |
| ADR-0002 Sovereign Veto | `AIR-RC-004` | `AIR-MIT-RC-VETO-01` | Preventative |
| ADR-0003 Hash-chain Audit Ledger | `AIR-OP-013` | `AIR-MIT-OP-AUDIT-01` | Detective |
| ADR-0004 Autonomy Ladder™ A0→A4 | `AIR-RC-005` | `AIR-MIT-RC-LADDER-01` | Preventative |
| ADR-0005 Regulation Loader | `AIR-RC-006` | `AIR-MIT-RC-MAPPING-01` | Detective |
| ADR-0006 Shadow Mode Rollout | `AIR-OP-014` | `AIR-MIT-OP-SHADOW-01` | Preventative |
| ADR-0007 Lease Provenance (CRE) | `AIR-OP-015` | `AIR-MIT-OP-PROV-01` | Preventative + Detective |
| ADR-0008 Fair Housing Pre-Flight | `AIR-RC-007` | `AIR-MIT-RC-FHA-01` | Preventative |
| ADR-0009 Tenant PII Residency | `AIR-SEC-010` | `AIR-MIT-SEC-PII-01` | Preventative |

## What FULLY-drafted, what STUB

Two risks + one mitigation are fully drafted as the council-approved samples:

- `risks/regulatory-and-compliance/AIR-RC-004-sovereign-veto.md` — fully drafted
- `risks/regulatory-and-compliance/AIR-RC-007-fair-housing-preflight.md` — fully drafted
- `mitigations/AIR-MIT-RC-VETO-01-autonomy-ladder-sovereign-veto.md` — fully drafted

The remaining 15 files carry structured stubs with: title · proposed ID · ADR
back-reference · category · related-patterns links · TODO placeholder for the
body content. They are ready for one Kunjar Week-7 session to fill in.

## DCO sign-off

Every commit in the resulting PR must carry `Signed-off-by:` per the FINOS DCO
policy. Use `git commit -s` or add the trailer manually.

## Fallback if the PR is not accepted

Per Brand Unbeatable Supplement Move 1, three fallbacks are pre-approved by
the council:

1. Publish the 18 markdown files as a standalone MIT repo at
   `github.com/linus10x/autonomy-ladder-air-crosswalk` — Kunjar still owns the
   citation graph; the crosswalk compounds as practitioners reference it.
2. Submit to FINOS Open Regulation initiative if AIR rejects but Open
   Regulation is receptive.
3. Submit to OWASP Top 10 for LLM Applications (different consortium, similar
   citation-graph payoff).

## Related artifacts

- `../docs/adr/` — the 9 ADRs that source this submission
- `../config/compliance_rules.yaml` — the regulation mapping that backs each entry
- `../README.md` — the public repo README that will link to the accepted FINOS entries
- `Memos/FINOS_AIR_Submission_Outline_v0_2026-05-22.md` — the council-approved outline
- `Memos/Brand_Unbeatable_Supplement_2026-05-22.md` — Move 1 of the supplement

## Council pre-vote on the structure

5-mentor brand-work slate, single-round pass:

| Mentor | Vote | Edit |
|---|---|---|
| Dorie Clark | 9.9 | "Two fully-drafted samples make Week 7 a fill-in exercise, not a redesign exercise. Right scaffold." Applied. |
| Justin Welsh | 9.8 | "Mitigation entry credits Autonomy Ladder™ by name in every file. That's the citation hook." Confirmed. |
| Lou Adler | 9.8 | "DCO sign-off note in this README saves a back-and-forth with the FINOS maintainer. Operator-ready." Confirmed. |
| Marcos López de Prado | 9.9 | "ID assignment table is the right scaffold — maintainer reserves final assignment, our PR proposes." Confirmed. |
| Elad Gil | 9.8 | "Three explicit fallbacks if the PR is not accepted. Risk-priced into the plan." Confirmed. |

**Cross-section: 9.84 · 5/5 affirm · structure ready for Week 7 fill-in + Week 8 submit.**
