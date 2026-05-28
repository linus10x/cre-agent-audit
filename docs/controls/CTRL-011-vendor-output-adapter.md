# CTRL-011 — Vendor-Output Adapter (`VendorScoreGate`)

> **Reference pattern, not legal or audit advice.** See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Control description

| Field | Value |
|---|---|
| **Control activity** | Capture every third-party AI scoring decision into the operator's audit chain with full provenance (`vendor_id`, `input_hash`, `score`, `model_version`, `timestamp`). Detect score drift on the `(vendor_id, input_hash, model_version)` key: same input + same advertised model + different score surfaces as a flagged `decision_type="vendor_score_drift"` entry. Default posture raises `VendorScoreDriftDetected` so the pipeline halts rather than silently absorbing the change. |
| **Control objective** | Operator-side documentation of every vendor AI-decision used in the operator's pipeline + detection of silent vendor-patch failures (the exact failure mode the SafeRent class settlement named: undocumented threshold scoring on voucher-holder applicants). |
| **Control owner (typical)** | VP Engineering (gate operation + drift threshold) + Chief Risk Officer (vendor-review playbook + halt-vs-shadow-mode posture) + General Counsel (vendor procurement clause; FCRA § 615 adverse-action documentation) |
| **Frequency** | Per-decision (continuous on every vendor scoring call) + on-drift (event-driven; raises by default) |
| **Type** | Detective (drift detection) + Preventive (fail-closed halt by default) + Corrective (vendor-review playbook on drift) |
| **Evidence of operation** | The audit chain entries with `decision_type="vendor_score_emit"` and `decision_type="vendor_score_drift"`; the vendor-review playbook output; quarterly cohort-drift reports. |
| **ADR** | [`docs/adr/0011-vendor-output-adapter-pattern.md`](../adr/0011-vendor-output-adapter-pattern.md) (design baseline + v0.2.1 concrete `VendorScoreGate` implementation update) |
| **Implementation** | [`src/cre_agent_audit/governance/vendor_score_gate.py`](../../src/cre_agent_audit/governance/vendor_score_gate.py) — `VendorScoreGate` Protocol + `InMemoryVendorScoreGate` default backend |

## Test of design

Code review: `emit()` validates score is finite and in `[0.0, 1.0]`; `(vendor_id, input_hash, model_version)` drift surfaces as a flagged chain entry written BEFORE the exception propagates (drift is auditable even when the caller swallows the error); `raise_on_drift=False` available for shadow-mode rollouts; a new `model_version` is recorded as a separate entry, not silently absorbed as drift.

## Test of operating effectiveness

Quarterly: sample a vendor's `emit()` events for the prior period; for each, verify (1) the chain entry carries the full provenance, (2) any drift events triggered the vendor-review playbook, (3) any model-version transitions are documented in the chain rather than absorbed silently. Annual: vendor-cohort drift report comparing aggregate vendor-score behavior across the operator's portfolio.

## Framework mappings

| Framework | Mapping |
|---|---|
| NIST AI RMF 1.0 | GOVERN 6.1 (third-party AI providers) · MEASURE 2.1 (performance + impact monitored) · MANAGE 4.1 (third-party risk management) |
| ISO/IEC 42001:2023 Annex A | A.8.1 (asset management — third-party AI components) · A.15.1 (supplier relationships) · A.15.2 (supplier service delivery management) |
| COSO ICAIR component | Risk Assessment · Control Activities · Monitoring |
| Big-4 standard AI-controls taxonomy | Third-Party Risk Management · Vendor AI Governance · Adverse-Action Documentation |

## Limitations and compensating controls

The drift check fires on `(vendor_id, input_hash, model_version)`; a vendor that silently changes the model WITHOUT advancing `model_version` would not be detected by this control alone (compensating control: independent score-distribution monitoring; vendor procurement clause requiring model-version transparency — see `docs/vendor-clauses/`). Replay against the matter under [`examples/regulatory-incidents/01_transunion_rental_screening/`](../../examples/regulatory-incidents/01_transunion_rental_screening/) to validate operating effectiveness on a SafeRent-shaped or TransUnion-shaped failure mode.

## Related

- ADR-0011 (full architectural reasoning)
- ADR-0003 (every emit writes to the audit chain)
- ADR-0008 (Fair-Housing Pre-Flight Gate consumes vendor outputs subject to this control)
- ADR-0014 (operator-side AI governance category — VendorScoreGate is structurally vendor-agnostic by design)
- [`examples/regulatory-incidents/01_transunion_rental_screening/`](../../examples/regulatory-incidents/01_transunion_rental_screening/) (motivating named matter)
- `docs/vendor-clauses/` (procurement-side companion)
