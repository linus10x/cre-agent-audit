---
mitigation_id: AIR-MIT-RC-FHA-01
title: "Autonomy Ladder™ Fair-Housing Pre-Flight Gate — 5 ordered checks + DisparateImpactMonitor + BypassRegistry auto-escalation"
control_type: preventative
mitigates_risks:
  - AIR-RC-007
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
reference_implementation: "https://github.com/linus10x/cre-agent-audit/blob/main/src/cre_agent_audit/governance/fair_housing_gate.py"
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0008-fair-housing-preflight-gate.md"
license: MIT
---

## Summary

[TODO Week 7: full body per ADR-0008 — 5 ordered checks (FHA-PROXY · FHA-VOUCHER · FHA-SOI · FHA-CRIM · FHA-DISPARATE) · DisparateImpactMonitor implementing the four-fifths rule on a 90-day rolling window · BypassRegistry with 3-owner-90d → GC escalation and 5-reason-90d → DEFCON-4 force · protected-surface enumeration (tenant screening · renewal pricing · marketing audience · housing credit · tenant communication personalization).]

Reference Python implementation at `src/cre_agent_audit/governance/fair_housing_gate.py`. MIT-licensed.
