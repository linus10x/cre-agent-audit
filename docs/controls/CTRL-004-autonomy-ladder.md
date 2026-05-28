# CTRL-004 — Autonomy Ladder™ A0→A4

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Classify every AI workflow against the A0→A4 ladder; gate promotion between tiers with a four-criterion evidence requirement (sovereign veto live + audit ledger ≥90d + shadow mode ≥30d + circuit-breaker tested). |
| **Control objective** | Size autonomy to the assurance case the operator can defend; provide regulators, LPs, and audit committees with a documented promotion-decision audit trail. |
| **Control owner (typical)** | VP Engineering (tier classification) + Chief Compliance Officer (promotion-gate evidence sign-off) + Chief Risk Officer (A2→A3 + A3→A4 promotion authority) |
| **Frequency** | Per-workflow (initial classification) + per-promotion-request (gate-evidence review) + annual (re-classification review) |
| **Type** | Preventive (blocks under-evidenced promotions) + Detective (records every promotion decision + every blocked promotion) |
| **Evidence of operation** | `PromotionGateReport` artifacts; A2→A3 four-criterion evidence pack; annual re-classification record |
| **ADR** | [`docs/adr/0004-autonomy-ladder.md`](../adr/0004-*.md) |
| **Implementation** | [`src/cre_agent_audit/governance/autonomy_ladder.py`](../../src/cre_agent_audit/governance/autonomy_ladder.py) |

## Test of design

Code review: `PromotionRequirements.evaluate()` rejects promotions missing any of the four criteria; rejection produces a `PromotionGateNotMet` with specific criterion failure naming.

## Test of operating effectiveness

Annual: review all A2→A3 promotions in the period; verify each carries the four-criterion evidence pack; sample one for outside-counsel walkthrough.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | GOVERN 1.1 (accountability mechanisms) · MAP 1.1 (context) · MANAGE 2.3 (risk decisions documented) |
| ISO/IEC 42001:2023 Annex A | A.6.1.2 (segregation of duties) · A.5.32 (information security in project management) |
| COSO ICAIR component | Control Environment · Risk Assessment |
| Big-4 standard AI-controls taxonomy | Lifecycle Governance · Human Oversight |

## Limitations and compensating controls

Per-task numerical scoring is intentionally not encoded (qualitative + compose-pattern defined; calibration is per-deployer); cross-organization autonomy transferability is local to the assurance case; A4 → A3 revert is an operator runbook item, not a framework primitive.

## Related

- ADR-0004 (full architectural reasoning)
- ADR-0003 (every event of this control writes to the audit chain)
- ADR-0010 (retention / privilege / discovery posture for evidence this control generates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
