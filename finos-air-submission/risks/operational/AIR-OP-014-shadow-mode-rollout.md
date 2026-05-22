---
risk_id: AIR-OP-014
title: "New AI capability promoted to production without parallel-shadow validation"
category: operational
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
related_mitigations:
  - AIR-MIT-OP-SHADOW-01
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0006-shadow-mode-rollout.md"
license: MIT
---

## Description

A new agent capability — a new lease-clause classifier · an updated tenant-screening model · a revised rent-optimization rule set — promoted directly from "works in the lab" to "live in production" without parallel-shadow validation. The conventional canary approach is insufficient for regulated decisions because even 1% of regulated traffic is a measurable settled-liability surface.

[TODO Week 7: expand the contributing factors, the 4-class promotion-gate matrix (7d / 30d / 60d / 90d), severity classification, the zero-worse-direction veto rule on fair-housing surfaces — pull from ADR-0006 body. Council bar 9.5+ before submit.]

## Related mitigations

- `AIR-MIT-OP-SHADOW-01` — Autonomy Ladder™ Shadow Mode Rollout (preventative control)
