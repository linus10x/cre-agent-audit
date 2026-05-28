# Matter 02 — *Louis v. SafeRent Solutions, LLC*

**Primary source:** *Louis v. SafeRent Solutions, LLC*, No. 1:22-cv-10800 (D. Mass.) — class settlement, November 20, 2024, approximately $2.275M, five-year score-use injunction on voucher-holder applicants.

**Filed:** Original class action 2022; settlement approved November 20, 2024.

**Failure shape:** A vendor tenant-screening AI scored voucher-holder applicants below a tenancy threshold without documenting why. The threshold was undisclosed; the override path was undocumented; the operator could not justify the cohort-level disparate outcome when challenged. The five-year score-use injunction the settlement imposed effectively says: the operator cannot use the vendor's score for voucher-holder applicants for five years. That is a vendor-side audit failure at the structural level.

## What the operator-side framework would have surfaced

The operator-side audit infrastructure (`cre-agent-audit`) would have produced two finding classes:

1. **Voucher-status proxy detection** — the Fair-Housing Pre-Flight Gate (ADR-0008) screens applicant features for protected-class proxies before model evaluation. Voucher-status is a HUD-protected source-of-income surrogate; a feature that proxies for voucher-holder status is flagged at preflight. In this synthetic replay, 89 of 1,000 applicants carry voucher-proxy features that the preflight gate catches.

2. **Sovereign veto on blanket criminal-history exclusion** — the Sovereign Veto (ADR-0002) blocks decisions that match named-prohibited patterns. A blanket criminal-history exclusion is one such pattern (HUD guidance, April 2016). In this synthetic replay, 12 blanket-exclusion attempts trigger the veto.

Both finding classes would have stopped the matter at decision time. Both would have produced documentary evidence the operator could hand to plaintiffs' counsel demonstrating bounded operation — and would have made the cohort-level disparate-impact analysis tractable rather than catastrophic.

## What this replay does

`replay.py` runs the framework against a 1,000-applicant synthetic dataset engineered to reproduce the failure shape. The dataset is in `synthetic_data.json` (no real PII; shape-faithful). The expected findings are declared in `expected_findings.json` (TDD contract).

Run it:

```bash
cre-replay run 02_saferent_voucher_screening
```

## Patterns engaged

- [ADR-0002 — Sovereign Veto](../../../docs/adr/0002-sovereign-veto.md)
- [ADR-0008 — Fair-Housing Pre-Flight Gate](../../../docs/adr/0008-fair-housing-preflight-gate.md)

## Disclaimer

This worked example is not legal advice and does not adjudicate the underlying matter. Patterns are software; regulatory characterizations are reference mappings; consult counsel for applicability to your control environment.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
