---
risk_id: AIR-OP-015
title: "Hallucinated lease-clause extraction reaches system of record without provenance"
category: operational
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
related_mitigations:
  - AIR-MIT-OP-PROV-01
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0007-lease-abstraction-provenance.md"
license: MIT
---

## Description

AI lease abstraction is the highest-ROI CRE-AI use case. Leading firms report 10× deal-execution improvement. The risk underneath is hallucination at the clause level. An AI that misses a break clause does not produce a 1% accuracy drop visible on a metrics dashboard — it produces a missed renewal trigger that costs more than the AI program saved. An AI that transposes a rent escalation produces a financial statement that ties to the wrong number. An AI that confabulates a co-tenancy clause produces a tenant-relations dispute that lands in litigation.

[TODO Week 7: expand the Provenance object specification, the 5 PROV-* veto reason codes (PROV-INCOMPLETE-MATERIAL · PROV-INCOMPLETE-SIGNIFICANT · PROV-LOW-CONFIDENCE-MATERIAL · PROV-HASH-MISMATCH · PROV-STALE-MODEL), the reviewer-signature sigil workflow — pull from ADR-0007 body. Council bar 9.5+ before submit.]

## Related mitigations

- `AIR-MIT-OP-PROV-01` — Autonomy Ladder™ Lease-Abstraction Provenance Chain (preventative + detective control)
