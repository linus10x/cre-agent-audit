# CTRL-010 — Audit-Chain Retention, Privilege & Discovery Posture

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Apply a documented retention schedule synchronized to relevant statutes of limitations to every audit-chain entry. Route bypass-justification fields and disparate-impact monitor outputs through attorney-client privilege and work-product workflows. Integrate litigation-hold with the audit chain so a hold suspends scheduled deletion. |
| **Control objective** | Retention-policy compliance + privilege preservation + discovery-readiness for the audit-evidence the operator's audit ledger produces. |
| **Control owner (typical)** | General Counsel (privilege routing + litigation-hold registry) + Chief Compliance Officer (retention schedule + statute-of-limitations mapping) + VP Engineering (deletion engine + hold integration) |
| **Frequency** | Per-entry (privilege classification at write time) + scheduled (retention sweep cadence per policy, typically monthly) + event-driven (litigation hold lift + drop) |
| **Type** | Preventive (privilege routing + hold) + Detective (retention sweep + reconciliation) |
| **Evidence of operation** | Retention-schedule document; privilege-classification log; litigation-hold registry with effective dates; periodic retention-sweep reports; reconciliation reports showing chain entries deleted under policy + entries preserved under hold. |
| **ADR** | [`docs/adr/0010-audit-chain-retention-privilege-discovery.md`](../adr/0010-audit-chain-retention-privilege-discovery.md) |
| **Implementation** | Policy + design layer (no single module — operator integrates the SOL config from `config/compliance_rules.json` with their litigation-hold and deletion engines) |

## Test of design

Document review: the retention schedule maps each `decision_type` to a statute of limitations (FCRA § 1681p; SEC 17a-4; state tenant-records statutes); the privilege-classification rule names which `gate_verdicts` fields carry attorney-client privilege; the litigation-hold registry has a deterministic precedence over scheduled deletion.

## Test of operating effectiveness

Quarterly: sample audit-chain entries scheduled for deletion in the prior period; for each, verify (1) deletion executed per policy when no hold applied, (2) hold-preserved entries remained intact, (3) privilege-routed bypass-justification fields were not exposed to non-privileged reviewers. Annual: simulated subpoena response exercise against the chain.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | GOVERN 1.1 (legal + regulatory considerations) · GOVERN 4.1 (org accountability) · MANAGE 2.4 (response and recovery) |
| ISO/IEC 42001:2023 Annex A | A.5.1 (information security policies) · A.18.1 (compliance with legal and contractual requirements) · A.18.1.3 (protection of records) |
| COSO ICAIR component | Control Environment · Information & Communication · Monitoring |
| Big-4 standard AI-controls taxonomy | Record Management · Legal & Regulatory Compliance · Discovery Readiness |

## Limitations and compensating controls

This control is policy + design — adopters integrate with their existing litigation-hold workflow, privilege-log workflow, and retention-engine workflow. Reference integration sketches (`RetentionScheduler` adapter, `LitigationHoldRegistry` Protocol, privilege-metadata extension to `AuditEntry`) are v0.3 candidates.

## Related

- ADR-0010 (full architectural reasoning + four policy artifacts)
- ADR-0002 (generates bypass-justification fields the privilege layer protects)
- ADR-0003 (the audit-chain ledger this control governs the retention of)
- ADR-0008 (disparate-impact monitor outputs are work-product candidates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
