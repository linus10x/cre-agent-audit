# CTRL-005 — Regulation-to-Pattern Mapping

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Load the runtime regulation→pattern mapping JSON; expose pattern→regulation and regulation→pattern queries; serve the credibility anchor for adoption-decision memos. |
| **Control objective** | Make every governance pattern queryable against the regulations it satisfies; prevent silent drift between the YAML source of truth and runtime behavior. |
| **Control owner (typical)** | VP Engineering (loader operation) + General Counsel (regulation-citation review) + Chief Compliance Officer (annual mapping update) |
| **Frequency** | Continuous (runtime queries) + per-PR (CI verifies JSON-YAML sync) + annual (full mapping review) |
| **Type** | Detective (queryable evidence of pattern→regulation coverage) + Compliance (supports audit-program mapping) |
| **Evidence of operation** | `compliance_rules.json` (committed); `compliance_rules.yaml` (author-time source); CI sync-check log; annual mapping-review minutes |
| **ADR** | [`docs/adr/0005-regulation-loader.md`](../adr/0005-*.md) |
| **Implementation** | [`src/cre_agent_audit/governance/regulation_loader.py`](../../src/cre_agent_audit/governance/regulation_loader.py) |

## Test of design

Code review: loader rejects non-JSON file extensions explicitly (preserves zero-dep claim); schema-validation raises with specific failure naming.

## Test of operating effectiveness

Annual: re-verify every regulation citation against primary source (statute text / agency press release / court docket); record verification in `docs/SESSION-AUDIT.md`-style Verified Facts Ledger.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | GOVERN 1.1 · MAP 2.3 (system requirements) · MEASURE 3.1 (approaches and metrics) |
| ISO/IEC 42001:2023 Annex A | A.5.36 (compliance with policies, rules, and standards) · A.18.1.1 (identification of applicable legislation) |
| COSO ICAIR component | Information & Communication · Monitoring |
| Big-4 standard AI-controls taxonomy | Lifecycle Governance · Operational Monitoring |

## Limitations and compensating controls

Mappings are author-asserted, not regulator-asserted (annual re-verification required); does not cover jurisdiction-specific implementation guidance (deployer + counsel responsibility); state-level mappings are partial (5 states tracked as v0.2.0 good-first-issues).

## Related

- ADR-0005 (full architectural reasoning)
- ADR-0003 (every event of this control writes to the audit chain)
- ADR-0010 (retention / privilege / discovery posture for evidence this control generates)
- `docs/MAPPING-MATRICES.md` (cross-pattern framework mapping)
