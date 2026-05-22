---
risk_id: AIR-RC-006
title: "Untraceable mapping from production controls to specific regulatory anchors"
category: regulatory-and-compliance
contributors:
  - Kunjar Bhaduri (Autonomy Ladder™ framework · autonomy-ladder.io)
related_mitigations:
  - AIR-MIT-RC-MAPPING-01
adr_back_reference: "https://github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0005-eu-ai-act-mapping.md"
license: MIT
---

## Description

An institutional buyer of an AI-enabled platform — a portfolio company general counsel · a PE operating partner · a board risk committee — needs the answer to a single practical question: *if my regulator asks how this system meets requirement X, what part of the architecture is the answer?* A README that says "compliant with EU AI Act and HUD AI guidance" is not the answer. A machine-readable file that maps each named pattern in the system to each named requirement in each named regulation is the answer.

[TODO Week 7: expand the compliance_rules.yaml schema, the NIST AI RMF function mapping (GOVERN / MAP / MEASURE / MANAGE), the Treasury FS AI RMF 230-control overlay, the per-jurisdiction layering — pull from ADR-0005 body. Council bar 9.5+ before submit.]

## Related mitigations

- `AIR-MIT-RC-MAPPING-01` — Autonomy Ladder™ Regulation-to-Pattern Mapping (detective control · YAML source-of-truth)
