# Matter 03 — *U.S. v. RealPage, Inc. et al.* (ongoing antitrust litigation — alleged conduct)

> **⚠ Important framing.** This matter is **ongoing antitrust litigation**. *U.S. v. RealPage, Inc. et al.* was filed August 23, 2024 in the Middle District of North Carolina by the U.S. Department of Justice and 8 state attorneys general. The allegations are not adjudicated. Nothing in this worked example asserts or implies that the underlying conduct violates Sherman § 1 or any other antitrust statute. The replay surfaces *coordination signals* the operator-side framework would have made operator-visible — not legal conclusions.

**Primary source:** *U.S. v. RealPage, Inc. et al.*, Civil Action No. (M.D.N.C.), filed August 23, 2024 by the U.S. Department of Justice + 8 state attorneys general. **Ongoing antitrust litigation.**

**Filed:** August 23, 2024 — case is ongoing.

**Failure shape (as alleged in the complaint, not adjudicated):** Multifamily revenue-management vendor software allegedly enabled operators to share competitively sensitive data and act on a common algorithmic price recommendation. Operators that used the software allegedly experienced pricing patterns that converged with peer operators using the same software. The complaint alleges this constituted unlawful information-sharing under Sherman § 1; the defendants deny the allegations; the matter has not been adjudicated.

## What the operator-side framework would have surfaced (regardless of the merits)

The operator-side audit infrastructure (`cre-agent-audit`) would have produced two finding classes — *not as proof of antitrust violation*, but as *operator-side signals* an operator could have used to evaluate exposure and document deliberate independent decision-making.

1. **DEFCON-state operator awareness** — the DEFCON state machine (ADR-0001) is the canonical place to record the operator's posture toward vendor recommendations. A vendor-pricing surface where the vendor's recommendation has been adopted unmodified across all operators in a cohort is the DEFCON-state condition that ought to trigger operator review (regardless of the legal characterization). In this synthetic replay, 50 of 50 decisions accept the vendor's recommendation unmodified — a DEFCON-state signal the operator's risk function would surface.

2. **VendorScoreGate cohort drift signal** — when multiple operators using the same vendor + same model_version produce statistically clustered scoring outputs, the `VendorScoreGate` flags cohort drift as a finding for the operator's review. The signal does not prove coordination; it provides documentary evidence that the operator was aware of the cohort statistical pattern and made (or did not make) an independent decision in response. In this synthetic replay, 50 vendor-score emit entries land; the cohort-drift signal flags the entire batch as a single operator-review finding.

Neither finding is proof of Sherman § 1 violation. Both produce documentary evidence the operator can hand to counsel as part of an independent-judgment defense or as part of compliance-program documentation.

## What this replay does NOT do

- It does not adjudicate whether the underlying conduct violates Sherman § 1.
- It does not provide legal advice.
- It does not characterize the defendants' conduct as unlawful.
- It does not endorse the plaintiffs' theory or the defendants' theory.
- It does not produce evidence usable in any legal proceeding.

It is a worked example demonstrating which `cre-agent-audit` patterns would have made certain operator-side signals operator-visible at decision time.

## What this replay does

`replay.py` runs the framework against a 50-decision synthetic dataset engineered to reproduce the failure shape *as alleged in the complaint*. The dataset is in `synthetic_data.json` (no real PII, no real operator pricing data; shape-faithful only). The expected findings are declared in `expected_findings.json` (TDD contract).

Run it:

```bash
cre-replay run 03_realpage_ongoing_litigation
```

## Patterns engaged

- [ADR-0001 — DEFCON State Machine](../../../docs/adr/0001-defcon-state-machine.md)
- [ADR-0011 — Vendor-Output Adapter Pattern](../../../docs/adr/0011-vendor-output-adapter-pattern.md) (concrete `VendorScoreGate` shipped in v0.2.1)

## Disclaimer

This worked example is **not legal advice** and **does not adjudicate the underlying matter**. The underlying matter is **ongoing antitrust litigation**. Patterns are software; regulatory characterizations are reference mappings; consult counsel for applicability to your control environment.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
