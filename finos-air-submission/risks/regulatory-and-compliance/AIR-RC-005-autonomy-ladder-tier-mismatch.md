---
risk_id: AIR-RC-005
title: "Unspecified human-oversight requirement for AI capability tier"
category: regulatory-and-compliance
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
related_mitigations:
  - AIR-MIT-RC-LADDER-01
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0004-autonomy-ladder-a0-a4.md"
license: MIT
---

## Description

"Is this AI program ready for production?" is the wrong question. The right question is "at what level of autonomy is this program ready, and what is the next promotable tier?" A program at full autonomy on a low-risk read-only task is shipping safely. A program at full autonomy on a sovereign-veto-required task is a settlement waiting to happen. Without a tier-explicit maturity scaffold and a promotion gate between tiers, regulators (EU AI Act Article 14 · NIST AI RMF Govern), institutional investors (LP letters specifying explainability requirements), and internal risk committees cannot distinguish a real governance posture from marketing language.

[TODO Week 7: expand the A0-A4 tier definitions, the A2→A3 promotion gate's four criteria (sovereign veto load-tested · audit ledger ≥ 90 days · shadow mode ≥ 30 days · circuit-breaker tested), severity classification — pull from ADR-0004 body. Council bar 9.5+ before submit.]

## Related mitigations

- `AIR-MIT-RC-LADDER-01` — Autonomy Ladder™ A0→A4 promotion gate (preventative control)
