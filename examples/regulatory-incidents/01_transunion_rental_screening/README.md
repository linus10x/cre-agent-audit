# Matter 01 — TransUnion Rental Screening Solutions

**Primary source:** *In re Trans Union Rental Screening Solutions* — joint FTC and CFPB consent orders, October 2023, $15M civil money penalty, FCRA § 607(b) accuracy.

**Filed:** October 12, 2023 (FTC + CFPB joint action)

**Failure shape:** Systemic accuracy failures in rental-screening reports — wrong addresses, mismatched criminal records, duplicate identities. The operator could not produce a chain-of-custody for the screening-report data feeding their tenancy decision, and the vendor's scoring model produced divergent scores on identical inputs without operator-visible signal.

## What the operator-side framework would have surfaced

The operator-side audit infrastructure (`cre-agent-audit`) would have produced two finding classes:

1. **Chain-of-custody breaks** — every screening report entering the operator's decision pipeline carries (or should carry) a source-document hash. The audit ledger (ADR-0003) captures the hash on every append. An entry without the hash is a finding the moment it lands. In this synthetic replay, 12 of 500 records lack the source-document hash; the audit ledger flags them.

2. **Vendor score drift on identical inputs** — when the same `input_hash` produces a different `score` under the same `model_version`, the `VendorScoreGate` (ADR-0011 v0.2.1 update) flags the drift. In this synthetic replay, 47 score-divergence pairs surface.

Both finding classes would have been operator-visible at decision time, not after a regulator inquiry. Both would have produced documentary evidence the operator could hand to FTC + CFPB Enforcement during the investigation phase.

## What this replay does

`replay.py` runs the framework against a 500-record synthetic dataset engineered to reproduce the failure shape. The dataset is in `synthetic_data.json` (no real PII; shape-faithful). The expected findings are declared in `expected_findings.json` (TDD contract: the replay must produce exactly these findings).

Run it:

```bash
cre-replay run 01_transunion_rental_screening
```

The bundle is written to `audit-evidence/01_transunion_rental_screening.zip` (six artifacts: `audit_chain.jsonl`, `verify_chain_report.json`, `mi_proxy_attestation.json`, `findings.json`, `controls_description_table.md`, `narrative.md`).

## Patterns engaged

- [ADR-0003 — Internally-Consistent Hash-Chained Audit Ledger](../../../docs/adr/0003-hash-chain-audit.md)
- [ADR-0011 — Vendor-Output Adapter Pattern](../../../docs/adr/0011-vendor-output-adapter-pattern.md) (concrete `VendorScoreGate` shipped in v0.2.1)

## Disclaimer

This worked example is not legal advice and does not adjudicate the underlying matter. Patterns are software; regulatory characterizations are reference mappings; consult counsel for applicability to your control environment.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
