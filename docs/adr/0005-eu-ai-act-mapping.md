# ADR-0005 · Regulation-to-Pattern Mapping (compliance_rules.yaml)

**Status:** Accepted · inherited from finserv-agent-audit with CRE extensions
**Date:** 2026-05-26
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

An institutional CRE buyer of an AI-enabled platform — a portfolio company GC, a PE operating partner, a board risk committee — wants the answer to a single practical question: "If my regulator asks how this system meets requirement X, what part of the architecture is the answer?"

A README that says "compliant with EU AI Act and HUD AI guidance" is not the answer. A YAML file that maps **each named pattern in this repo to each named requirement in each named regulation** is the answer.

## Decision

Maintain a `config/compliance_rules.yaml` that for every governance pattern in this repo enumerates the regulations it satisfies, by name, section, and (where available) requirement ID. The YAML is the source of truth — code reads it at runtime to label audit-ledger entries.

Example shape:

```yaml
patterns:
  fair_housing_preflight_gate:
    regulations:
      - name: Fair Housing Act
        statute: 42 U.S.C. § 3604
        clause: "discrimination in the sale or rental of housing"
        pattern_function: "protected_class_proxy_detection"
      - name: ECOA
        statute: 15 U.S.C. § 1691
        clause: "discrimination in any aspect of a credit transaction"
        pattern_function: "voucher_status_non_discrimination"
      - name: Colorado AI Act
        statute: SB 189 (signed 2026-03-14)
        clause: "impact assessments for consequential decisions"
        effective_date: 2027-01-01
        pattern_function: "disparate_impact_monitor"
      - name: HUD AI Guidance
        statute: 2024 HUD memorandum on AI and Fair Housing
        pattern_function: "voucher_status_non_discrimination"

  lease_abstraction_provenance_chain:
    regulations:
      - name: SOC 2 Trust Services Criteria
        statute: AICPA TSP 100 (2017) CC7.2
        clause: "system monitoring and evidence preservation"
        pattern_function: "material_clause_provenance_required"

  tenant_pii_data_residency_partitioning:
    regulations:
      - name: GDPR
        statute: Regulation (EU) 2016/679 Art. 6
        clause: "lawful basis for processing personal data"
      - name: CCPA / CPRA
        statute: Cal. Civ. Code § 1798.100
        clause: "consumer rights to know, delete, correct, limit"
```

The YAML is versioned with the repo. Updates require a PR with a regulatory citation and a test that proves the pattern function still satisfies the cited clause.

## Consequences

**Positive.** Buyer due-diligence becomes a checklist exercise rather than an architectural interview. A regulator inquiry maps a citation to a pattern in one query. The board committee can ask "show me which regulations the gate satisfies" and get a single artifact, not a presentation.

**Negative.** Mappings drift. Regulations evolve. A mapping is correct when it ships and may not be correct 18 months later. Mitigation: every mapping carries an `effective_date` and (where applicable) a `last_reviewed_date`. The repo runs an annual review by maintainers and accepts PRs for jurisdictional updates from the community.

**Architectural.** The runtime reads the YAML to label every audit-ledger entry with the regulations satisfied by the gates that passed. A vetoed entry records which regulation triggered the veto.

## Regulatory anchor

This ADR is the meta-ADR — it documents how every other ADR maps to regulation. The specific anchors are in the YAML.

## CRE-specific notes

CRE has more jurisdictional layering than financial services. Federal Fair Housing Act sits under state ordinances (NY, CA, MA, MN) under municipal ordinances (NYC, SF, Seattle, Minneapolis). The YAML schema accommodates `jurisdiction_level: federal | state | municipal` so the gate can compose checks correctly for a multi-jurisdiction portfolio.

## Related

- All other ADRs — every pattern is mapped here
- ADR-0008 (Fair-Housing Pre-Flight) — most mappings live under this pattern
- ADR-0009 (Tenant-PII Residency) — jurisdictional mappings dominate
