---
risk_id: AIR-OP-012
title: "Unbounded state transitions in agentic systems under operational stress"
category: operational
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
related_mitigations:
  - AIR-MIT-OP-DEFCON-01
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0001-defcon-state-machine.md"
license: MIT
---

## Description

An AI program touching workflows where the cost of an unsafe operating state — degraded model availability · unverified deployment · regulator inquiry in flight · data-quality incident — is asymmetric. A single hour of agent autonomy during a known-unsafe condition can produce hundreds of decisions that later require manual unwind. Per-decision risk checks are necessary but insufficient: some risk conditions are system-wide and need a system-wide brake.

[TODO Week 7: expand the contributing factors, financial-services and CRE-specific examples, severity classification, detection signals — pull from ADR-0001 body. Council bar 9.5+ before submit.]

## Related mitigations

- `AIR-MIT-OP-DEFCON-01` — Autonomy Ladder™ DEFCON state machine (preventative control)
