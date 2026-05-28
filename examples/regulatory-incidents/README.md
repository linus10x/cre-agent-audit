# Regulatory-Incident Replays

Runnable Python replays of named settled (and one ongoing) matters in commercial real-estate AI. Each replay produces an `audit-evidence/<matter>.zip` bundle showing which `cre-agent-audit` patterns would have surfaced the failure modes the public record describes.

These are not legal opinions and they do not adjudicate the underlying matters. Patterns are software; regulatory characterizations are reference mappings; consult counsel for jurisdiction-specific applicability.

## Why this directory exists

The three settled-liability anchors of record in CRE-AI share one structural feature: the operator carried the liability when vendor-side audit could not produce the operator-side evidence regulators demanded. This directory replays those failure shapes against the operator-side framework (ADR-0014).

Each replay is implemented as an `IncidentReplay` Protocol subclass per `src/cre_agent_audit/regulatory_replay/`. The Protocol carries the matter's primary-source citations, declares which `cre-agent-audit` patterns are expected to fire, and produces a 6-artifact audit-evidence bundle (chain export + verify report + MI Proxy attestation + findings + controls description table + narrative).

## Run them

```bash
# After `pip install -e .` of cre-agent-audit:
cre-replay list                                    # show all matters
cre-replay run 01_transunion_rental_screening      # run one matter
cre-replay run-all                                 # run all matters
cre-replay verify <bundle.zip>                     # re-validate a bundle
```

## The three matters in this PR

| # | Matter | Primary source(s) | Patterns expected to fire |
|---|---|---|---|
| **01** | TransUnion Rental Screening Solutions — FTC + CFPB consent orders, October 2023, $15M civil money penalty, FCRA § 607(b) accuracy | FTC C-4810; CFPB 2023-CFPB-0008 | ADR-0003 (audit ledger) · ADR-0011 (vendor-output adapter) |
| **02** | *Louis v. SafeRent Solutions, LLC*, No. 1:22-cv-10800 (D. Mass.) — class settlement, November 20, 2024, ~$2.275M, five-year score-use injunction | D. Mass. docket | ADR-0002 (sovereign veto) · ADR-0008 (fair-housing pre-flight) |
| **03** | *U.S. v. RealPage, Inc. et al.* (M.D.N.C., filed August 23, 2024 by DOJ + 8 state AGs) — **ongoing antitrust litigation** | M.D.N.C. docket | ADR-0001 (DEFCON) · ADR-0011 (vendor-output adapter) |

Matter 03 is framed throughout as **alleged conduct**. The replay surfaces coordination *signals*; it does not adjudicate Sherman § 1 exposure. See the per-matter README for the disclaimer pattern.

## Want a deeper engagement?

See [`docs/services/`](../../docs/services/) for the productized service templates ($5K Diagnostic, $40K Audit, $15K/q Retainer, $25K-$50K Workshop, $50K-$200K Cohort, plus the private intel subscription and the practitioner bench).

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
