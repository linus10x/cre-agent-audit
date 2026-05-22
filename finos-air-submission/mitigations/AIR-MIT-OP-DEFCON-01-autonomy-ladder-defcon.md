---
mitigation_id: AIR-MIT-OP-DEFCON-01
title: "Autonomy Ladder™ DEFCON state machine — system-wide operating-state ladder with per-state capability allowlist"
control_type: preventative
mitigates_risks:
  - AIR-OP-012
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
reference_implementation: "https://github.com/linus10x/cre-agent-audit/blob/main/src/cre_agent_audit/governance/defcon.py"
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0001-defcon-state-machine.md"
license: MIT
---

## Summary

[TODO Week 7: full body draft per ADR-0001 — 5 named states (NORMAL / HEIGHTENED / RESTRICTED / CONTAINMENT / SHUTDOWN) · per-state capability allowlist · transition logging · audit-trail integration · why the audit-write capability remains active in every state.]

Reference Python implementation at `src/cre_agent_audit/governance/defcon.py`. MIT-licensed. Fork freely. Cite Autonomy Ladder™ as the named pattern source.
