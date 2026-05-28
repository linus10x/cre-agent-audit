# CTRL-008 — Fair-Housing Pre-Flight Gate

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Run 5 ordered checks (FHA-PROXY · VOUCHER · SOI · CRIM · DISPARATE) on every agent action touching a protected decision surface; route veto bypasses through Sovereign Veto with auto-escalation (3 bypasses same owner → GC; 5 bypasses same reason → DEFCON-4). |
| **Control objective** | Materially reduce the class of failure modes the SafeRent + TransUnion regulatory matters exposed; produce the operator-side defensible record under FHA + ECOA + state housing statutes + Colorado AI Act. |
| **Control owner (typical)** | Chief Compliance Officer + General Counsel (joint authority per ADR-0002 RACI); Data Science lead (per-jurisdiction blocklist tuning) |
| **Frequency** | Per-decision on every protected surface (continuous) |
| **Type** | Preventive (blocks discriminatory features at gate) + Detective (DisparateImpactMonitor on outputs in 90-day window) |
| **Evidence of operation** | `FairHousingException` records on every bypass; cohort-specific selection-rate reports from `DisparateImpactMonitor`; per-jurisdiction blocklist version-controlled in `config/compliance_rules.yaml` |
| **ADR** | [`docs/adr/0008-fair-housing-preflight-gate.md`](../adr/0008-fair-housing-preflight-gate.md) |
| **Implementation** | [`src/cre_agent_audit/governance/fair_housing_preflight.py`](../../src/cre_agent_audit/governance/fair_housing_preflight.py) |

## Test of design

Code review: confirm 5 checks fire in order and that each veto carries a structured reason code; auto-escalation thresholds configured.

## Test of operating effectiveness

Quarterly: sample 20 vetoes and 20 bypasses; verify each bypass owner is IdP-verified, justification is documented, and authority level matches the RACI; review the disparate-impact monitor outputs for any cohorts approaching the four-fifths threshold.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | MAP 2.3 · MEASURE 2.11 (fairness metrics) · MANAGE 2.3 + 2.4 (decisions documented + inspection) |
| ISO/IEC 42001:2023 Annex A | A.5.33 (protection of personal data) · A.5.34 (privacy and protection of PII) |
| COSO ICAIR component | Control Activities · Monitoring |
| Big-4 standard AI-controls taxonomy | Human Oversight · Operational Monitoring |

## Limitations and compensating controls

Lexical-only proxy detection (does NOT detect learned proxies in embedding space or behavioral signals — see ADR-0008 'Scope of proxy detection' and `docs/LIMITATIONS.md`); four-fifths-rule only (does not engage fairness-metric pluralism — Kleinberg/Chouldechova 2016 impossibility results); state SOI coverage is partial (5 states tracked); doctrinal foundation is ICP v Texas 576 U.S. 519 (2015).

## Related

- ADR-0008 (full architectural reasoning)
- ADR-0003 (every event of this control writes to the audit chain)
- ADR-0010 (retention / privilege / discovery posture for evidence this control generates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
