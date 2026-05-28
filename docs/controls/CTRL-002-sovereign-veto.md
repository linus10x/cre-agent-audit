# CTRL-002 — Sovereign Veto

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Run a non-overridable check at the agent boundary before any consequential decision; route bypass-justifications through designated human authority with logged exception. |
| **Control objective** | Three-lines-of-defense alignment — agent (1st line) proposes; sovereign veto (2nd line) checks against constraint surfaces; logged exception supports 3rd-line audit. |
| **Control owner (typical)** | Surface-specific — see ADR-0002 'Designating the Sovereign' RACI (CCO+GC for screening, CRO+GC+Audit Cmte for pricing, etc.) |
| **Frequency** | Per-decision (every agent action that touches a constraint surface) |
| **Type** | Preventive (blocks unauthorized decisions) + Detective (records every veto + every bypass) |
| **Evidence of operation** | Veto events and `SovereignBypass` records in `AuditLedger`; bypass-justification fields tagged with privilege metadata per ADR-0010 |
| **ADR** | [`docs/adr/0002-sovereign-veto.md`](../adr/0002-sovereign-veto.md) |
| **Implementation** | [`src/cre_agent_audit/governance/sovereign_veto.py`](../../src/cre_agent_audit/governance/sovereign_veto.py) |

## Test of design

Code review: confirm veto is non-overridable by the agent's reasoning context (separate module / separate service in production).

## Test of operating effectiveness

Quarterly: sample 20 bypass events; verify each carries a named owner (IdP-verified), regulatory or factual basis, timestamp, and authority-level matching the surface RACI.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | GOVERN 2.3 (risk decisions documented) · MANAGE 4.1 (post-deployment monitoring) |
| ISO/IEC 42001:2023 Annex A | A.6.2.1 (segregation of duties) · A.9.4.1 (access to functions and information) |
| COSO ICAIR component | Control Activities · Information & Communication |
| Big-4 standard AI-controls taxonomy | Human Oversight · Incident Response |

## Limitations and compensating controls

Does not cover vendor-side veto authority (see ADR-0011); does not defend against IdP compromise (out of scope — IAM controls own that); does not enforce two-party / quorum rule (deployer extension, not pattern primitive).

## Related

- ADR-0002 (full architectural reasoning)
- ADR-0003 (every event of this control writes to the audit chain)
- ADR-0010 (retention / privilege / discovery posture for evidence this control generates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
