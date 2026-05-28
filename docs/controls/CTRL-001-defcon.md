# CTRL-001 — DEFCON State Machine

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Maintain a system-wide DEFCON state (5 levels) that gates which agent capabilities are permitted in the current operational posture. |
| **Control objective** | Operational risk management — degrade gracefully under stress; deny high-blast-radius operations when monitoring indicates degraded confidence. |
| **Control owner (typical)** | Chief Risk Officer (state transitions) + VP Engineering (capability allowlist tuning) |
| **Frequency** | Continuous (state transitions are event-driven; capability checks fire on every agent action) |
| **Type** | Preventive (denies capabilities) + Detective (records state transitions) |
| **Evidence of operation** | DEFCON state transitions and capability-denial events in `AuditLedger` (ADR-0003); weekly DEFCON-state report to the operating-partner review |
| **ADR** | [`docs/adr/0001-defcon.md`](../adr/0001-*.md) |
| **Implementation** | [`src/cre_agent_audit/governance/defcon.py`](../../src/cre_agent_audit/governance/defcon.py) |

## Test of design

Code review: per-state capability allowlist matches operator's documented risk-appetite-by-state matrix.

## Test of operating effectiveness

Quarterly: sample 10 state transitions over the period; verify each transition's trigger was recorded and the resulting capability allowlist took effect on the next action.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | GOVERN 1.6 (incident response) · MANAGE 2.3 (risk decisions documented) |
| ISO/IEC 42001:2023 Annex A | A.6.1.2 (risk treatment options) · A.10.1.3 (operations management) |
| COSO ICAIR component | Risk Assessment · Monitoring |
| Big-4 standard AI-controls taxonomy | Operational Monitoring · Incident Response |

## Limitations and compensating controls

Does not auto-rollback deployments; does not cover model-quality monitoring (use Shadow Mode, Pattern 6); does not cover human authentication for state-transition authority (use SovereignVeto + Designating-the-Sovereign RACI, ADR-0002).

## Related

- ADR-0001 (full architectural reasoning)
- ADR-0003 (every event of this control writes to the audit chain)
- ADR-0010 (retention / privilege / discovery posture for evidence this control generates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
