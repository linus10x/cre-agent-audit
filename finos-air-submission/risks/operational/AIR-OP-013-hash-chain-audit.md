---
risk_id: AIR-OP-013
title: "Non-reconstructable decision trail for autonomous AI actions"
category: operational
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
related_mitigations:
  - AIR-MIT-OP-AUDIT-01
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0003-hash-chain-audit.md"
license: MIT
---

## Description

A regulator inquiring about an AI decision twelve months after the fact needs an answer that does not depend on whether the agent code, the prompt, the model weights, or the operator's intentions have changed in the interim. The answer must be a record that was true when the decision was made and cannot have been tampered with since. Standard application logging is insufficient — logs are mutable, deletable, and reconstructable in ways that do not survive scrutiny by an adversarial third party.

[TODO Week 7: expand the contributing factors, financial-services and CRE-specific examples (TransUnion · SafeRent · RealPage audit-replay scenarios), severity classification, detection signals — pull from ADR-0003 body. Council bar 9.5+ before submit.]

## Related mitigations

- `AIR-MIT-OP-AUDIT-01` — Autonomy Ladder™ Hash-chain Audit Ledger (detective control)
