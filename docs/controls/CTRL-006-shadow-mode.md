# CTRL-006 — Shadow-Mode Rollout

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Run candidate model outputs in parallel with production for a configured period; gate promotion on aggregate + cohort divergence; enforce zero-worse-direction on protected cohorts. |
| **Control objective** | SR 11-7-aligned model-risk control: every model promotion has documented evidence of behavior under representative traffic before live activation. |
| **Control owner (typical)** | VP Engineering (shadow run operation) + Chief Compliance Officer (divergence-threshold sign-off) + Data Science lead (cohort definition) |
| **Frequency** | Per-promotion (any model change touching an A2+ surface) |
| **Type** | Preventive (blocks under-evidenced promotion) + Detective (records divergence per cohort) |
| **Evidence of operation** | `PromotionVerdict` artifacts; shadow-run divergence reports per decision class (7d / 30d / 60d / 90d windows); zero-worse-direction proof per protected cohort |
| **ADR** | [`docs/adr/0006-shadow-mode.md`](../adr/0006-shadow-mode-rollout.md) |
| **Implementation** | [`src/cre_agent_audit/governance/shadow_mode.py`](../../src/cre_agent_audit/governance/shadow_mode.py) |

## Test of design

Code review: `ShadowRouter` runs candidate and production in parallel without affecting live outcomes; divergence threshold per decision class is configured per the operator's risk-appetite matrix.

## Test of operating effectiveness

Per-promotion: review the shadow-run evidence pack; verify the divergence falls within configured thresholds; verify zero-worse-direction on protected cohorts for fair-housing-touching surfaces.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | MAP 4.1 (mapping risks) · MANAGE 2.4 (mechanisms for inspection) |
| ISO/IEC 42001:2023 Annex A | A.14.2.1 (secure development policy) · A.14.2.8 (system security testing) |
| COSO ICAIR component | Risk Assessment · Control Activities |
| Big-4 standard AI-controls taxonomy | Model Validation · Lifecycle Governance |

## Limitations and compensating controls

Does not validate model behavior on adversarial inputs (use a separate red-team); does not cover backward-compatibility checks on schema changes; relies on the live decision distribution being representative of post-promotion conditions.

## Related

- ADR-0006 (full architectural reasoning)
- ADR-0003 (every event of this control writes to the audit chain)
- ADR-0010 (retention / privilege / discovery posture for evidence this control generates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
