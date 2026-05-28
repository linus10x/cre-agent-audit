# Spec — Fair-Housing MI-Threshold Detector (ADR-0008 Update) · 2026-05-28

**Status:** Approved (brainstorming → design → spec) 2026-05-28
**Owner:** Kunjar Bhaduri
**Repo:** `linus10x/cre-agent-audit` (`main` at `dfd388a`)
**Version target:** `0.2.2` final (this is one of the three v0.2.2 close items)
**Closes:** F11 from `docs/SHIP-RECEIPT.md` — *MI-threshold learned-proxy detection in `fair_housing_preflight.py`*
**Pairs with:** [`docs/superpowers/specs/2026-05-28-audit-verify-rfc3161-design.md`](2026-05-28-audit-verify-rfc3161-design.md) (the other v0.2.2 close item)

## Goal

Close the lexical-only proxy detection limitation that ADR-0008's Fair-Housing Pre-Flight Gate explicitly bounded in v0.2.0. Ship a mutual-information-based learned-proxy detector that flags features carrying statistical signal about a protected-class attribute, even when those features are lexically opaque (zip-code-shaped features carrying voucher-status signal, etc.). Address the SafeRent class settlement's named failure mode (the AI scored voucher-holder applicants below threshold via features that did not name voucher status explicitly).

## Non-goals

- Not training-time fairness intervention (the framework is operator-side deployment governance, not model training)
- Not a fairness metric — this is a *signal-presence detector*, not a fairness-property certifier
- Not vendor-side detection (vendors who hide their feature set cannot be inspected at this layer; vendor-clauses cover the procurement side)
- Not a Sherman § 1 antitrust detector (orthogonal concern; RealPage replay covers that)
- Not a replacement for any disparate-impact analysis the deployer's counsel chooses (this is a pre-deployment signal, not a post-hoc fairness audit)

## Academic anchoring

The MI-threshold approach maps to the published statistical-fairness literature:

- **Kusner et al. 2017** — *Counterfactual Fairness* (NeurIPS). Defines protected-attribute proxies in terms of conditional-information flow.
- **Calmon et al. 2017** — *Optimized Pre-Processing for Discrimination Prevention* (NeurIPS). Pre-processing transforms that bound mutual information between features and protected attributes.
- **Hardt-Price-Srebro 2016** — *Equality of Opportunity in Supervised Learning*. The complementary equalized-odds metric this detector does NOT compute.
- **Pedreshi-Ruggieri-Turini 2008** — *Discrimination-aware data mining* (KDD). The early-discrimination-discovery literature.

The detector ships as a v0.2.2 implementation; the methodology paper this spec supports is `PUBLICATIONS.md` Draft 2 (ACM FAccT target Q3 2027).

## Voice + framing constraints (CLAUDE.md)

- Operator-with-leverage register; no marketing language
- Primary-source academic citations (case, court, dollar amount, ISO date for regulatory anchors; author, year, venue for academic anchors)
- "MI threshold is necessary, not sufficient — adopters owning a regulator-facing fairness defense should choose their fairness metric in consultation with counsel"
- No banned terms; no banned names
- Disclaimer line in every regulatory-adjacent file

## Architecture

### New module: `src/cre_agent_audit/governance/mi_threshold_detector.py`

Five types:

```python
@dataclass(frozen=True)
class ProtectedClassReference:
    """Operator-configured labeled sample for MI computation.

    `feature_samples` is a list of dicts; each dict maps feature_name
    to the feature value for one historical applicant. `protected_class_labels`
    is the parallel list (1 = protected, 0 = not protected). At least 30
    samples required for non-degenerate MI; warning emitted below 100.
    """
    feature_samples: tuple[Mapping[str, object], ...]
    protected_class_labels: tuple[int, ...]
    protected_class_name: str  # e.g. "voucher_holder"
```

```python
@dataclass(frozen=True)
class ProxyFinding:
    feature_name: str
    mi_score: float                # 0.0 = no info; 1.0 = perfect predictor
    threshold: float
    protected_class_name: str
    severity: Severity
```

```python
class MIReferenceUndersizedWarning(UserWarning): ...
class InvalidReferenceError(ValueError): ...
```

```python
class MutualInformationCalculator:
    """Stdlib-only mutual-information computation.

    For a binary protected attribute and binary/numeric features:
    - binary features: I(F; Y) computed directly from contingency table
    - numeric features: discretize into 4 quartile bins, then compute
      I(F_binned; Y)

    Uses base-2 log so MI is in bits; output range is [0, 1] for binary Y
    and a binary feature with the same support.
    """

    def __init__(self, reference: ProtectedClassReference) -> None: ...

    def mi_score(self, feature_name: str, applicant_value: object) -> float: ...

    def mi_scores_across_features(
        self, feature_names: Iterable[str]
    ) -> Mapping[str, float]: ...
```

```python
class MIThresholdDetector:
    """Flags features whose MI with the protected class exceeds threshold.

    Construction-time invariants:
    - reference has >= 30 samples (else InvalidReferenceError)
    - 30 <= reference.size < 100 emits MIReferenceUndersizedWarning
    - threshold in (0.0, 1.0]
    """

    def __init__(
        self,
        *,
        reference: ProtectedClassReference,
        mi_threshold: float = 0.10,
    ) -> None: ...

    def detect_proxies(
        self, applicant_features: Mapping[str, object]
    ) -> tuple[ProxyFinding, ...]:
        """Return findings only for features above the MI threshold.

        Empty tuple means no proxies detected. Note: a clean applicant
        run still produces an empty tuple even when the reference itself
        contains proxies — this detector reports findings *for the
        applicant's features*.
        """
```

### Modified module: `src/cre_agent_audit/governance/fair_housing_preflight.py`

`FairHousingPreflightGate.__init__` gains an optional `mi_proxy_detector: MIThresholdDetector | None = None` parameter. When supplied, the gate runs the detector after the lexical proxy check; any flagged feature produces a `FHA-MI-PROXY` veto with the flagged feature names and MI scores in the veto reason metadata.

**Backward-compatible:** Existing `FairHousingPreflightGate()` callers see no change.

### Modified ADR: `docs/adr/0008-fair-housing-preflight-gate.md`

New subsection "MI-Threshold Learned-Proxy Detection" added under the Decision section. Cites the academic literature. Names the limitation explicitly: "MI signal-presence is necessary but not sufficient for fair-housing compliance; adopters' counsel chooses the fairness metric."

### Modified ADR-0008 footer

Update the "Limitations" subsection — drop the "lexical-only proxy detection bound" claim (now superseded) but preserve the "Adopters owning a regulator-facing fairness defense should choose their fairness metric in consultation with counsel" line.

### Tests

`tests/test_mi_threshold_detector.py`:
- Calculator: independent features → MI ≈ 0; perfect-predictor feature → MI ≈ 1; one degenerate-constant feature → MI = 0
- Reference validation: < 30 samples raises; 30..99 warns; >= 100 quiet
- Detection: feature above threshold flagged; feature below threshold absent
- SafeRent-shaped synthetic fixture: 1,000-applicant reference + 50-feature applicant including a zip-code-shaped proxy with MI ≈ 0.35 against voucher status → flagged

`tests/test_fair_housing_preflight.py` (extended):
- Backward compat: `FairHousingPreflightGate()` (no detector) preserves all v0.2.1 behavior
- Integration: gate with detector + proxy-positive applicant → `FHA-MI-PROXY` veto with feature names

### Synthetic fixture

`tests/fixtures/saferent_shaped_reference.py` — Python module (not JSON, for determinism via `random.Random(seed)`) generating a 1,000-applicant reference dataset where:
- Voucher status (protected class) is correlated with `zip_code_quintile` at p ≈ 0.4 (MI ≈ 0.35)
- All other features are independent of voucher status (MI ≈ 0)
- Output is a `ProtectedClassReference` instance

This is the SafeRent-shaped fixture explicitly committed in the original `docs/SHIP-RECEIPT.md` F11 deferred item.

## Data flow

```
Operator deploy-time:
    reference = saferent_shaped_reference()  # or load operator's labeled sample
    detector = MIThresholdDetector(reference=reference, mi_threshold=0.10)
    gate = FairHousingPreflightGate(mi_proxy_detector=detector)

At each decision:
    applicant_features = {
        "credit_score": 720,
        "income_x_rent": 3.5,
        "zip_code_quintile": 5,  # proxy
        ...
    }
    verdict = gate.evaluate(applicant_features)
    # If zip_code_quintile carries MI > 0.10 against voucher status in the
    # reference, verdict carries FHA-MI-PROXY veto with the flagged feature.
```

## Error handling

- Empty reference (no samples) → `InvalidReferenceError` at `__init__`
- Mismatched feature_samples vs. protected_class_labels length → `InvalidReferenceError`
- `mi_threshold` outside `(0.0, 1.0]` → `ValueError`
- Reference < 30 samples → `InvalidReferenceError` (refuse to run; statistics are unreliable)
- 30 ≤ reference < 100 → `MIReferenceUndersizedWarning` (run but flag)
- Feature missing from applicant → score = 0 (silent; no signal)
- All-zero feature column → MI = 0 (no information; not flagged)

## Constraints applied

- Zero new runtime dependencies (stdlib `math` + `collections.Counter` only)
- Backward-compatible: `FairHousingPreflightGate()` with no detector unchanged
- mypy --strict clean
- ruff check + ruff format --check clean
- SoT propagation: ADR-0008 update first, then README + ROADMAP + LIMITATIONS + SHIP-RECEIPT + CHANGELOG follow
- Banned-term + banned-name greps zero hits on every committed file
- TDD: tests first, watch fail, implement
- Disclaimer line on every regulatory-adjacent file

## Out-of-scope (explicit)

- Continuous-numeric feature MI via differential-entropy estimation (uses quartile binning; refinement is v0.3+)
- Multi-class protected attributes (binary only in v0.2.2; multi-class is v0.3+)
- Causal-fairness extensions (Pearl-style counterfactual reasoning is out of scope)
- A `FairnessMetric` Protocol (this ship is signal-presence; metrics are separate)
- Training-time intervention (we are deployment governance, not training)
- Direct integration with `VendorScoreGate` (vendor-output-side proxy detection is a v0.3+ candidate)

## Verification of completion

The v0.2.2 close on this item completes when:
1. All tests pass (existing 294 + new ~15)
2. ruff + ruff format --check + mypy --strict clean
3. ADR-0008 updated and the staleness test still passes against the new claims
4. README + ROADMAP + LIMITATIONS + SHIP-RECEIPT updated and the staleness test still passes
5. Council pass: 10/10 from the engineering slate (Majors, Fowler, Orosz, Welsh-Larson, Clark) + López de Prado (rigor) on the academic citations + Gil (positioning) on the category-claim continuity

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
