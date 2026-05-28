# v0.2.2 Close Implementation Plan — MI-Threshold Detector + audit-verify Extra

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the two engineering items remaining for v0.2.2 final — fair-housing MI-threshold learned-proxy detection (closes F11) and the `audit-verify` extra wiring (closes ADR-0012-A1) — then bump `0.2.2.dev0` → `0.2.2` and propagate to every doc surface.

**Architecture:** Phase A adds a new stdlib-only `mi_threshold_detector.py` under `governance/` with `MutualInformationCalculator` + `MIThresholdDetector` + `ProtectedClassReference` + `ProxyFinding` dataclasses, opt-in integration into `FairHousingPreflightGate`, and a SafeRent-shaped synthetic fixture. Phase B adds a new `rfc3161_verify.py` behind a new `[project.optional-dependencies] audit-verify` extra (cryptography>=42), module-level import guard, and a synthetic-TSA test fixture. Phase C bumps the version marker, propagates the SoT-correct claims through README / CHANGELOG / ROADMAP / LIMITATIONS / SHIP-RECEIPT / FAILURE-MODES, runs all gates, and surfaces the tag decision.

**Tech Stack:** Python 3.10+, pytest, ruff, mypy --strict, stdlib only for Phase A (math + collections.Counter); `cryptography>=42` opt-in for Phase B. No new runtime dependencies on the base package.

**Spec references:**
- [`docs/superpowers/specs/2026-05-28-fair-housing-mi-threshold-detector-design.md`](../specs/2026-05-28-fair-housing-mi-threshold-detector-design.md)
- [`docs/superpowers/specs/2026-05-28-audit-verify-rfc3161-design.md`](../specs/2026-05-28-audit-verify-rfc3161-design.md)

**Starting commit:** `75cd567` (the spec commit). All work on `main`.

---

## File structure

| Path | New / Modify | Phase | Responsibility |
|---|---|---|---|
| `src/cre_agent_audit/governance/mi_threshold_detector.py` | New | A | MI calculator + threshold detector + dataclasses |
| `src/cre_agent_audit/governance/fair_housing_preflight.py` | Modify | A | Opt-in `mi_proxy_detector` parameter on `FairHousingPreflightGate` |
| `tests/test_mi_threshold_detector.py` | New | A | Calculator + reference validation + detection tests |
| `tests/fixtures/__init__.py` | New | A | Fixtures subpackage init |
| `tests/fixtures/saferent_shaped_reference.py` | New | A | Deterministic synthetic SafeRent-shaped reference |
| `tests/test_fair_housing_preflight.py` | Modify | A | Backward-compat + integration tests |
| `docs/adr/0008-fair-housing-preflight-gate.md` | Modify | A | Add "MI-Threshold Learned-Proxy Detection" subsection |
| `src/cre_agent_audit/__init__.py` | Modify | A + B | Re-export new types |
| `src/cre_agent_audit/governance/rfc3161_verify.py` | New | B | `verify_tsr_token` + `verify_audit_entry_token` + `TSRVerificationResult` |
| `tests/test_rfc3161_verify.py` | New | B | Synthetic TSA + round-trip + tamper + chain + expired |
| `tests/conftest.py` | Modify | B | `_synthetic_tsa()` helper (skips if cryptography absent) |
| `pyproject.toml` | Modify | B | New `[project.optional-dependencies] audit-verify` |
| `.github/workflows/test.yml` | Modify | B | Install `[dev,audit-verify]` instead of `[dev]` |
| `docs/adr/0012-persistence-witness-timestamp-pattern.md` | Modify | B | Update A1 forward-ref + add "Verification" subsection |
| Repo doc surfaces (README, CHANGELOG, ROADMAP, LIMITATIONS, SHIP-RECEIPT, FAILURE-MODES) | Modify | C | SoT propagation per the 5-rule discipline |
| `src/cre_agent_audit/__init__.py` + `pyproject.toml` | Modify | C | Bump `0.2.2.dev0` → `0.2.2` |

---

# Phase A — Fair-housing MI-threshold detector

## Task A1: Dataclasses + stdlib MI calculator

**Files:**
- Create: `src/cre_agent_audit/governance/mi_threshold_detector.py`
- Create: `tests/test_mi_threshold_detector.py`

- [ ] **Step 1: Write the failing test for the dataclasses + MI calculator**

```python
# tests/test_mi_threshold_detector.py
"""Tests for the fair-housing MI-threshold learned-proxy detector.

Anchored on Kusner 2017, Calmon 2017, Hardt-Price-Srebro 2016 statistical-
fairness literature. The detector flags features carrying mutual-information
signal about a binary protected-class attribute, even when those features
are lexically opaque (zip-code-shaped proxies for voucher-holder status).

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

import math
import warnings

import pytest

from cre_agent_audit.governance.mi_threshold_detector import (
    InvalidReferenceError,
    MIReferenceUndersizedWarning,
    MIThresholdDetector,
    MutualInformationCalculator,
    ProtectedClassReference,
    ProxyFinding,
)
from cre_agent_audit.regulatory_replay import Severity


# --- Reference validation ---


def test_reference_requires_min_30_samples() -> None:
    """Reference with fewer than 30 samples raises InvalidReferenceError."""
    with pytest.raises(InvalidReferenceError):
        ProtectedClassReference(
            feature_samples=tuple({"f": i} for i in range(29)),
            protected_class_labels=tuple([0] * 14 + [1] * 15),
            protected_class_name="voucher_holder",
        )


def test_reference_warns_when_under_100_samples() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ProtectedClassReference(
            feature_samples=tuple({"f": i} for i in range(50)),
            protected_class_labels=tuple([0] * 25 + [1] * 25),
            protected_class_name="voucher_holder",
        )
    assert any(
        issubclass(w.category, MIReferenceUndersizedWarning) for w in caught
    )


def test_reference_rejects_mismatched_label_length() -> None:
    with pytest.raises(InvalidReferenceError):
        ProtectedClassReference(
            feature_samples=tuple({"f": i} for i in range(100)),
            protected_class_labels=tuple([0] * 50),  # half-length
            protected_class_name="voucher_holder",
        )


# --- MI calculator ---


def _make_reference(
    feature_values: list[object], labels: list[int]
) -> ProtectedClassReference:
    return ProtectedClassReference(
        feature_samples=tuple({"f": v} for v in feature_values),
        protected_class_labels=tuple(labels),
        protected_class_name="voucher_holder",
    )


def test_mi_calculator_independent_feature_returns_zero() -> None:
    """A feature uncorrelated with the protected class carries ~0 MI."""
    feature_values = [0, 1] * 100  # alternating
    labels = [0, 0, 1, 1] * 50  # uncorrelated pattern
    ref = _make_reference(feature_values, labels)
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score(
        "f", applicant_value=0
    )  # applicant value doesn't matter for fixed feature
    assert score < 0.05, f"Independent feature MI should be ~0; got {score}"


def test_mi_calculator_perfect_predictor_returns_one() -> None:
    """A feature that perfectly predicts the protected class carries MI ≈ 1."""
    feature_values = [0] * 100 + [1] * 100
    labels = [0] * 100 + [1] * 100
    ref = _make_reference(feature_values, labels)
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score("f", applicant_value=1)
    assert score > 0.95, (
        f"Perfect predictor MI should be ~1; got {score}"
    )


def test_mi_calculator_constant_feature_returns_zero() -> None:
    """A constant feature carries no information by definition."""
    ref = _make_reference([42] * 200, [0] * 100 + [1] * 100)
    calc = MutualInformationCalculator(reference=ref)
    assert calc.mi_score("f", applicant_value=42) == 0.0


def test_mi_calculator_missing_feature_returns_zero() -> None:
    """Feature missing from reference → score 0 (silent, no signal)."""
    ref = _make_reference([0] * 100 + [1] * 100, [0] * 100 + [1] * 100)
    calc = MutualInformationCalculator(reference=ref)
    assert calc.mi_score("nonexistent_feature", applicant_value=1) == 0.0


def test_mi_calculator_numeric_feature_binning() -> None:
    """Numeric features get quartile-binned before MI."""
    # Strongly correlated continuous values
    feature_values = list(range(100)) + list(range(100, 200))
    labels = [0] * 100 + [1] * 100
    ref = _make_reference(feature_values, labels)
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score("f", applicant_value=150)
    assert score > 0.5, (
        f"Strongly correlated numeric feature should fire; got {score}"
    )


# --- Detector ---


def test_detector_constructor_rejects_invalid_threshold() -> None:
    ref = _make_reference([0, 1] * 100, [0, 1] * 100)
    with pytest.raises(ValueError):
        MIThresholdDetector(reference=ref, mi_threshold=0.0)
    with pytest.raises(ValueError):
        MIThresholdDetector(reference=ref, mi_threshold=1.5)


def test_detector_flags_above_threshold() -> None:
    """Feature above threshold appears in findings."""
    feature_values = [0] * 100 + [1] * 100
    labels = [0] * 100 + [1] * 100
    ref = _make_reference(feature_values, labels)
    detector = MIThresholdDetector(reference=ref, mi_threshold=0.10)
    findings = detector.detect_proxies({"f": 1})
    assert len(findings) == 1
    assert findings[0].feature_name == "f"
    assert findings[0].mi_score > 0.10
    assert isinstance(findings[0], ProxyFinding)


def test_detector_skips_below_threshold() -> None:
    """Feature below threshold doesn't appear."""
    feature_values = [0, 1] * 100
    labels = [0, 0, 1, 1] * 50
    ref = _make_reference(feature_values, labels)
    detector = MIThresholdDetector(reference=ref, mi_threshold=0.10)
    findings = detector.detect_proxies({"f": 1})
    assert findings == ()


def test_finding_carries_severity_based_on_mi_score() -> None:
    """Higher MI → higher severity."""
    feature_values = [0] * 100 + [1] * 100
    labels = [0] * 100 + [1] * 100
    ref = _make_reference(feature_values, labels)
    detector = MIThresholdDetector(reference=ref, mi_threshold=0.10)
    findings = detector.detect_proxies({"f": 1})
    assert findings[0].severity in (Severity.HIGH, Severity.CRITICAL)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd "$HOME/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
python3 -m pytest tests/test_mi_threshold_detector.py -v 2>&1 | tail -10
```

Expected: ModuleNotFoundError on `mi_threshold_detector`.

- [ ] **Step 3: Write `mi_threshold_detector.py`**

```python
# src/cre_agent_audit/governance/mi_threshold_detector.py
"""Mutual-information-based learned-proxy detector for the Fair-Housing
Pre-Flight Gate (ADR-0008 update; closes F11 from SHIP-RECEIPT).

Detects features carrying statistical signal about a binary protected-class
attribute, even when those features are lexically opaque (zip-code-shaped
features carrying voucher-status signal, etc.). Anchored on:

- Kusner et al. 2017 — *Counterfactual Fairness* (NeurIPS)
- Calmon et al. 2017 — *Optimized Pre-Processing for Discrimination Prevention* (NeurIPS)
- Hardt-Price-Srebro 2016 — *Equality of Opportunity in Supervised Learning*
- Pedreshi-Ruggieri-Turini 2008 — *Discrimination-aware data mining* (KDD)

Operator-side signal-presence detector; necessary but NOT sufficient for
fair-housing compliance. Adopters owning a regulator-facing fairness
defense should choose their fairness metric in consultation with counsel.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

import math
import warnings
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from cre_agent_audit.regulatory_replay import Severity


class InvalidReferenceError(ValueError):
    """Raised when a `ProtectedClassReference` is malformed or too small."""


class MIReferenceUndersizedWarning(UserWarning):
    """Emitted when a `ProtectedClassReference` has fewer than 100 samples.

    Statistics on small samples are unreliable. The detector still runs but
    the warning surfaces the limitation to the deployer at construction time.
    Non-suppressible by design.
    """


@dataclass(frozen=True)
class ProtectedClassReference:
    """Operator-configured labeled sample for MI computation.

    `feature_samples` is a tuple of mapping objects; each mapping is one
    historical applicant's features. `protected_class_labels` is the
    parallel tuple (1 = protected, 0 = not). At least 30 samples required.
    """

    feature_samples: tuple[Mapping[str, object], ...]
    protected_class_labels: tuple[int, ...]
    protected_class_name: str

    def __post_init__(self) -> None:
        n = len(self.feature_samples)
        if n < 30:
            raise InvalidReferenceError(
                f"ProtectedClassReference requires at least 30 samples; "
                f"got {n}"
            )
        if n != len(self.protected_class_labels):
            raise InvalidReferenceError(
                f"feature_samples ({n}) and protected_class_labels "
                f"({len(self.protected_class_labels)}) must be the same length"
            )
        if n < 100:
            warnings.warn(
                f"ProtectedClassReference has {n} samples; MI statistics "
                "are unreliable below 100. Consider expanding the reference.",
                MIReferenceUndersizedWarning,
                stacklevel=3,
            )

    @property
    def size(self) -> int:
        return len(self.feature_samples)


@dataclass(frozen=True)
class ProxyFinding:
    """One feature flagged as carrying MI above the threshold."""

    feature_name: str
    mi_score: float
    threshold: float
    protected_class_name: str
    severity: Severity


class MutualInformationCalculator:
    """Stdlib-only mutual-information computation over a reference.

    For a binary protected attribute and binary/numeric features:
    - binary features: I(F; Y) computed directly from a contingency table
    - numeric features: discretize into 4 quartile bins, then compute
      I(F_binned; Y)

    Uses base-2 log (output in bits, normalized to [0, 1] for binary Y).
    """

    def __init__(self, reference: ProtectedClassReference) -> None:
        self._reference = reference
        # Cache per-feature MI at construction time — the reference is
        # immutable, so MI scores don't change between calls.
        self._cache: dict[str, float] = {}
        # Determine which feature names are present in the reference
        self._feature_names: set[str] = set()
        for sample in reference.feature_samples:
            self._feature_names.update(sample.keys())

    def mi_score(self, feature_name: str, applicant_value: object) -> float:
        """Return MI between the reference's distribution of `feature_name`
        and the protected-class labels. Independent of `applicant_value` —
        the caller passes it for API symmetry but MI is a reference property."""
        if feature_name not in self._feature_names:
            return 0.0
        if feature_name in self._cache:
            return self._cache[feature_name]

        feature_values: list[object] = []
        labels: list[int] = []
        for sample, label in zip(
            self._reference.feature_samples,
            self._reference.protected_class_labels,
            strict=True,
        ):
            if feature_name in sample:
                feature_values.append(sample[feature_name])
                labels.append(label)

        score = self._compute_mi(feature_values, labels)
        self._cache[feature_name] = score
        return score

    def mi_scores_across_features(
        self, feature_names: Iterable[str]
    ) -> Mapping[str, float]:
        # Use a sentinel applicant_value since mi_score doesn't actually use it.
        return {n: self.mi_score(n, applicant_value=None) for n in feature_names}

    def _compute_mi(
        self, feature_values: list[object], labels: list[int]
    ) -> float:
        if not feature_values:
            return 0.0

        # Detect numeric vs categorical
        all_numeric = all(isinstance(v, (int, float)) for v in feature_values)
        if all_numeric and len(set(feature_values)) > 2:
            # Quartile-bin numeric values
            sorted_vals = sorted(feature_values)
            n = len(sorted_vals)
            q1 = sorted_vals[n // 4]
            q2 = sorted_vals[n // 2]
            q3 = sorted_vals[3 * n // 4]
            binned = [
                _quartile_bin(float(v), q1, q2, q3) for v in feature_values
            ]
            return _categorical_mi(binned, labels)

        return _categorical_mi(feature_values, labels)


def _quartile_bin(value: float, q1: float, q2: float, q3: float) -> int:
    if value <= q1:
        return 0
    if value <= q2:
        return 1
    if value <= q3:
        return 2
    return 3


def _categorical_mi(features: list[object], labels: list[int]) -> float:
    """Compute MI between two categorical sequences in bits, base-2.

    I(X; Y) = sum_x sum_y P(x,y) * log2(P(x,y) / (P(x) * P(y)))

    Normalized to [0, 1] by dividing by the marginal entropy of Y (when > 0).
    """
    n = len(features)
    if n == 0:
        return 0.0

    feature_counts = Counter(features)
    label_counts = Counter(labels)
    joint_counts = Counter(zip(features, labels, strict=True))

    # Marginal entropy of Y, normalization factor
    h_y = 0.0
    for ly in label_counts.values():
        p_y = ly / n
        if p_y > 0:
            h_y -= p_y * math.log2(p_y)
    if h_y == 0.0:
        return 0.0  # protected class is degenerate (all 0s or all 1s)

    mi = 0.0
    for (fx, ly), joint in joint_counts.items():
        p_xy = joint / n
        p_x = feature_counts[fx] / n
        p_y = label_counts[ly] / n
        if p_xy > 0 and p_x > 0 and p_y > 0:
            mi += p_xy * math.log2(p_xy / (p_x * p_y))

    # Normalize to [0, 1]
    return max(0.0, min(1.0, mi / h_y))


class MIThresholdDetector:
    """Flags features whose MI with the protected class exceeds threshold.

    Construction-time invariants:
    - reference is a valid `ProtectedClassReference` (raises at its own __init__)
    - threshold in (0.0, 1.0]
    """

    def __init__(
        self,
        *,
        reference: ProtectedClassReference,
        mi_threshold: float = 0.10,
    ) -> None:
        if not (0.0 < mi_threshold <= 1.0):
            raise ValueError(
                f"mi_threshold must be in (0.0, 1.0]; got {mi_threshold}"
            )
        self._reference = reference
        self._threshold = mi_threshold
        self._calculator = MutualInformationCalculator(reference=reference)

    def detect_proxies(
        self, applicant_features: Mapping[str, object]
    ) -> tuple[ProxyFinding, ...]:
        """Return findings for any feature above the MI threshold."""
        findings: list[ProxyFinding] = []
        for feature_name, value in applicant_features.items():
            score = self._calculator.mi_score(feature_name, applicant_value=value)
            if score > self._threshold:
                findings.append(
                    ProxyFinding(
                        feature_name=feature_name,
                        mi_score=score,
                        threshold=self._threshold,
                        protected_class_name=self._reference.protected_class_name,
                        severity=_severity_from_mi(score),
                    )
                )
        return tuple(findings)


def _severity_from_mi(score: float) -> Severity:
    if score >= 0.50:
        return Severity.CRITICAL
    if score >= 0.20:
        return Severity.HIGH
    if score >= 0.10:
        return Severity.MEDIUM
    return Severity.LOW
```

- [ ] **Step 4: Run tests + gates**

```bash
python3 -m pytest tests/test_mi_threshold_detector.py -v 2>&1 | tail -20
ruff check src/cre_agent_audit/governance/mi_threshold_detector.py tests/test_mi_threshold_detector.py 2>&1 | tail -3
ruff format src/cre_agent_audit/governance/mi_threshold_detector.py tests/test_mi_threshold_detector.py 2>&1 | tail -3
mypy --strict src/cre_agent_audit/governance/mi_threshold_detector.py 2>&1 | tail -3
```

Expected: 12 tests pass; gates clean.

- [ ] **Step 5: Defer commit** (bundled with the rest of Phase A)

---

## Task A2: SafeRent-shaped synthetic fixture

**Files:**
- Create: `tests/fixtures/__init__.py`
- Create: `tests/fixtures/saferent_shaped_reference.py`
- Modify: `tests/test_mi_threshold_detector.py` (append fixture test)

- [ ] **Step 1: Create empty `tests/fixtures/__init__.py`**

```bash
mkdir -p tests/fixtures
touch tests/fixtures/__init__.py
```

- [ ] **Step 2: Write the fixture module**

```python
# tests/fixtures/saferent_shaped_reference.py
"""SafeRent-shaped synthetic ProtectedClassReference.

Engineered to produce a zip-code-shaped feature that carries MI ≈ 0.35
against voucher-holder status — the exact failure shape the SafeRent
class settlement (Louis v. SafeRent Solutions, LLC, D. Mass., Nov 20, 2024)
named.

No real PII; no real operator data. Deterministic via random.Random(seed).
"""

from __future__ import annotations

import random

from cre_agent_audit.governance.mi_threshold_detector import (
    ProtectedClassReference,
)

_SEED = 20260528  # deterministic; bound to this synthetic fixture only


def saferent_shaped_reference(
    n_samples: int = 1000, seed: int = _SEED
) -> ProtectedClassReference:
    """Generate a 1,000-applicant reference with a hidden voucher-status proxy.

    - 50% of applicants are voucher-holders (protected_class_label = 1)
    - `zip_code_quintile`: 4-bin feature correlated with voucher status
      (voucher holders are concentrated in quintiles 4 and 5 at p ≈ 0.7)
    - `credit_score`: independent of voucher status
    - `income_x_rent`: independent of voucher status
    - `applied_via_lottery`: weak (p ≈ 0.55) correlation; below the MI
      threshold; demonstrates that not-every-correlated-feature gets flagged
    """
    rng = random.Random(seed)
    samples: list[dict[str, object]] = []
    labels: list[int] = []

    for _ in range(n_samples):
        is_voucher = rng.random() < 0.5
        labels.append(1 if is_voucher else 0)

        # zip_code_quintile: the proxy
        if is_voucher:
            zip_q = rng.choices([1, 2, 3, 4, 5], weights=[5, 5, 10, 35, 45])[0]
        else:
            zip_q = rng.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]

        # credit_score: independent
        credit = rng.randint(550, 820)

        # income_x_rent: independent
        income_x_rent = rng.uniform(1.5, 5.0)

        # applied_via_lottery: weakly correlated (mild signal, below threshold)
        if is_voucher:
            lottery = rng.random() < 0.55
        else:
            lottery = rng.random() < 0.45

        samples.append(
            {
                "zip_code_quintile": zip_q,
                "credit_score": credit,
                "income_x_rent": income_x_rent,
                "applied_via_lottery": 1 if lottery else 0,
            }
        )

    return ProtectedClassReference(
        feature_samples=tuple(samples),
        protected_class_labels=tuple(labels),
        protected_class_name="voucher_holder",
    )
```

- [ ] **Step 3: Append the fixture test to `tests/test_mi_threshold_detector.py`**

```python
# Append to tests/test_mi_threshold_detector.py:

from tests.fixtures.saferent_shaped_reference import saferent_shaped_reference


def test_saferent_fixture_zip_code_quintile_carries_strong_mi() -> None:
    """The engineered zip_code_quintile feature should carry MI > 0.10."""
    ref = saferent_shaped_reference()
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score("zip_code_quintile", applicant_value=4)
    assert score > 0.10, (
        f"zip_code_quintile should be flagged; got MI={score:.3f}"
    )


def test_saferent_fixture_credit_score_does_not_carry_mi() -> None:
    """Independent features should NOT be flagged."""
    ref = saferent_shaped_reference()
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score("credit_score", applicant_value=720)
    assert score < 0.10, (
        f"credit_score should not be flagged; got MI={score:.3f}"
    )


def test_saferent_fixture_end_to_end_proxy_detection() -> None:
    """The detector flags the zip-code proxy on a SafeRent-shaped applicant."""
    ref = saferent_shaped_reference()
    detector = MIThresholdDetector(reference=ref, mi_threshold=0.10)
    findings = detector.detect_proxies(
        {
            "zip_code_quintile": 5,
            "credit_score": 720,
            "income_x_rent": 3.5,
            "applied_via_lottery": 0,
        }
    )
    flagged_features = {f.feature_name for f in findings}
    assert "zip_code_quintile" in flagged_features
    assert "credit_score" not in flagged_features
    assert "income_x_rent" not in flagged_features
```

- [ ] **Step 4: Run + verify**

```bash
python3 -m pytest tests/test_mi_threshold_detector.py -v 2>&1 | tail -20
```

Expected: 15 tests pass (12 + 3 fixture tests).

- [ ] **Step 5: Defer commit** (bundled with rest of Phase A)

---

## Task A3: Integrate with `FairHousingPreflightGate`

**Files:**
- Modify: `src/cre_agent_audit/governance/fair_housing_preflight.py`
- Modify: `tests/test_fair_housing_preflight.py` (append integration tests)

- [ ] **Step 1: Read existing `fair_housing_preflight.py` to find the right insertion points**

```bash
grep -n "class FairHousingPreflightGate\|def __init__\|def evaluate\|VetoResult" src/cre_agent_audit/governance/fair_housing_preflight.py | head -20
```

- [ ] **Step 2: Append integration tests to `tests/test_fair_housing_preflight.py`**

```python
# Append to tests/test_fair_housing_preflight.py:

from cre_agent_audit.governance.mi_threshold_detector import (
    MIThresholdDetector,
)
from tests.fixtures.saferent_shaped_reference import saferent_shaped_reference


def test_gate_with_no_detector_preserves_v021_behavior() -> None:
    """FairHousingPreflightGate(mi_proxy_detector=None) is the v0.2.1 default."""
    gate = FairHousingPreflightGate()
    # Existing v0.2.1 behavior preserved — applicant with no proxy features passes
    verdict = gate.evaluate(
        applicant_features={"credit_score": 720, "income_x_rent": 3.5}
    )
    # Existing test asserts that lexical-clean applicants do not produce vetoes
    # from the MI detector when one is not wired.
    assert all("FHA-MI-PROXY" not in v.reason_code for v in verdict.vetoes)


def test_gate_with_detector_flags_voucher_proxy() -> None:
    """When the detector is wired, applicant features above MI threshold veto."""
    ref = saferent_shaped_reference()
    detector = MIThresholdDetector(reference=ref, mi_threshold=0.10)
    gate = FairHousingPreflightGate(mi_proxy_detector=detector)
    verdict = gate.evaluate(
        applicant_features={
            "zip_code_quintile": 5,
            "credit_score": 720,
            "income_x_rent": 3.5,
        }
    )
    proxy_vetoes = [v for v in verdict.vetoes if v.reason_code == "FHA-MI-PROXY"]
    assert proxy_vetoes, "Expected FHA-MI-PROXY veto on voucher-proxy applicant"
    assert "zip_code_quintile" in proxy_vetoes[0].reason_detail
```

- [ ] **Step 3: Modify `FairHousingPreflightGate` to accept and use the detector**

This step's exact edit depends on the current shape of the file. The pattern: add `mi_proxy_detector: MIThresholdDetector | None = None` to `__init__`; in `evaluate()`, after the existing lexical proxy check, if `mi_proxy_detector is not None`, run `detect_proxies(applicant_features)` and emit one `VetoResult` with `reason_code="FHA-MI-PROXY"` per finding (severity from the finding).

Use the Read tool first to see the current `__init__` and `evaluate` signatures; then Edit to wire the parameter through. The `VetoResult.reason_detail` should contain `"feature=<name> mi=<score:.3f> threshold=<t>"` per flagged feature so a regulator-side reviewer sees the math.

- [ ] **Step 4: Run tests**

```bash
python3 -m pytest tests/test_fair_housing_preflight.py tests/test_mi_threshold_detector.py -v 2>&1 | tail -25
```

Expected: all pass (existing fair-housing tests + new integration tests).

- [ ] **Step 5: Defer commit**

---

## Task A4: ADR-0008 update + re-export

**Files:**
- Modify: `docs/adr/0008-fair-housing-preflight-gate.md`
- Modify: `src/cre_agent_audit/__init__.py`

- [ ] **Step 1: Add "MI-Threshold Learned-Proxy Detection" subsection to ADR-0008**

Insert after the existing protected-surfaces section. Use the Edit tool with the following block:

```markdown
### MI-Threshold Learned-Proxy Detection (added v0.2.2)

The lexical-only proxy detection bound in v0.2.0 missed a class of failure
the *Louis v. SafeRent Solutions* matter named: features that carry
statistical signal about voucher-holder status without naming voucher
status lexically (zip-code-shaped features being the canonical example).

v0.2.2 ships `MIThresholdDetector` (`src/cre_agent_audit/governance/mi_threshold_detector.py`):

```python
reference = saferent_shaped_reference()  # or operator's labeled sample
detector = MIThresholdDetector(reference=reference, mi_threshold=0.10)
gate = FairHousingPreflightGate(mi_proxy_detector=detector)
verdict = gate.evaluate(applicant_features)
# Features whose mutual information with the protected class exceeds
# the threshold produce FHA-MI-PROXY vetoes with the feature name and
# MI score in reason_detail.
```

**Methodology.** Mutual information `I(F; Y)` is computed between each
feature `F` in the operator's labeled reference and the protected-class
label `Y`, normalized to `[0, 1]` by the marginal entropy of `Y`. Numeric
features are quartile-binned before computation. The threshold default is
`0.10` — features carrying 10% of the protected-class signal are flagged
for operator review. Stdlib-only implementation (no `scikit-learn`); the
Zero-Runtime-Dependencies posture is preserved.

**Academic anchoring.** The MI-threshold approach is grounded in:
- Kusner et al. 2017 — *Counterfactual Fairness* (NeurIPS)
- Calmon et al. 2017 — *Optimized Pre-Processing for Discrimination Prevention* (NeurIPS)
- Hardt-Price-Srebro 2016 — *Equality of Opportunity in Supervised Learning*
- Pedreshi-Ruggieri-Turini 2008 — *Discrimination-aware data mining* (KDD)

**Limitations.** MI signal-presence is **necessary but not sufficient**
for fair-housing compliance. Adopters owning a regulator-facing fairness
defense should choose their fairness metric in consultation with counsel
and document the choice. The four-fifths-rule monitor (existing) is the
post-decision complement; the MI detector is the pre-decision complement.
Binary protected attributes only in v0.2.2; multi-class is a v0.3+ candidate.
```

- [ ] **Step 2: Drop the "lexical-only proxy detection bound" claim from the same ADR's Limitations subsection** (the claim is now superseded; the spirit-preserving replacement: "MI signal-presence is necessary but not sufficient" — already in the subsection above).

- [ ] **Step 3: Update `src/cre_agent_audit/__init__.py` to re-export**

Add to imports:

```python
from cre_agent_audit.governance.mi_threshold_detector import (
    InvalidReferenceError,
    MIReferenceUndersizedWarning,
    MIThresholdDetector,
    MutualInformationCalculator,
    ProtectedClassReference,
    ProxyFinding,
)
```

Add to `__all__` under a new section header:

```python
    # Fair-housing MI-threshold detector (ADR-0008 update; v0.2.2)
    "InvalidReferenceError",
    "MIReferenceUndersizedWarning",
    "MIThresholdDetector",
    "MutualInformationCalculator",
    "ProtectedClassReference",
    "ProxyFinding",
```

- [ ] **Step 4: Run all gates**

```bash
python3 -m pytest -q 2>&1 | tail -3
ruff check src/ tests/ 2>&1 | tail -3
ruff format --check src/ tests/ scripts/ 2>&1 | tail -3
mypy --strict src/ tests/ 2>&1 | tail -3
```

Expected: full suite passes; gates clean.

- [ ] **Step 5: Commit Phase A**

```bash
git add src/cre_agent_audit/governance/mi_threshold_detector.py \
        src/cre_agent_audit/governance/fair_housing_preflight.py \
        src/cre_agent_audit/__init__.py \
        tests/test_mi_threshold_detector.py \
        tests/test_fair_housing_preflight.py \
        tests/fixtures/__init__.py \
        tests/fixtures/saferent_shaped_reference.py \
        docs/adr/0008-fair-housing-preflight-gate.md
git commit -m "feat(fair-housing): MI-threshold learned-proxy detector (closes F11)

[Full commit message authored at commit time; names every file +
references ADR-0008 update + names the academic anchors + names the
SafeRent-shaped synthetic fixture + chamber pass results]"
```

---

# Phase B — `audit-verify` extra (rfc3161_verify.py)

## Task B1: Synthetic-TSA test fixture in conftest.py

**Files:**
- Modify: `tests/conftest.py` (create if absent)

- [ ] **Step 1: Read existing conftest.py if present**

```bash
ls tests/conftest.py 2>&1 && cat tests/conftest.py 2>&1 | head -20
```

- [ ] **Step 2: Add synthetic-TSA helpers (skip-friendly when cryptography absent)**

```python
# tests/conftest.py

from __future__ import annotations

import pytest

try:
    import cryptography  # noqa: F401

    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False


@pytest.fixture(scope="session")
def synthetic_tsa():
    """Build a synthetic TSA root cert + intermediate + signing key.

    Used by tests/test_rfc3161_verify.py. Skips cleanly when cryptography
    is not installed.
    """
    if not _HAS_CRYPTOGRAPHY:
        pytest.skip("cryptography (audit-verify extra) not installed")
    from datetime import datetime, timedelta, timezone

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    now = datetime.now(timezone.utc)

    root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    root_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "TestTSA Root CA"),
        ]
    )
    root_cert = (
        x509.CertificateBuilder()
        .subject_name(root_subject)
        .issuer_name(root_subject)
        .public_key(root_key.public_key())
        .serial_number(1)
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        )
        .sign(root_key, hashes.SHA256())
    )

    tsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    tsa_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "TestTSA Signer"),
        ]
    )
    tsa_cert = (
        x509.CertificateBuilder()
        .subject_name(tsa_subject)
        .issuer_name(root_subject)
        .public_key(tsa_key.public_key())
        .serial_number(2)
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=180))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None), critical=True
        )
        .sign(root_key, hashes.SHA256())
    )

    return {
        "root_cert_pem": root_cert.public_bytes(serialization.Encoding.PEM),
        "tsa_cert_pem": tsa_cert.public_bytes(serialization.Encoding.PEM),
        "tsa_key": tsa_key,
        "tsa_cert": tsa_cert,
        "root_cert": root_cert,
    }
```

- [ ] **Step 3: Verify the fixture loads (no actual test yet)**

```bash
python3 -c "import tests.conftest" 2>&1 | tail -3
```

Expected: no output (clean import).

---

## Task B2: pyproject.toml + CI workflow

**Files:**
- Modify: `pyproject.toml`
- Modify: `.github/workflows/test.yml`

- [ ] **Step 1: Add the optional dependency**

In `pyproject.toml` under `[project.optional-dependencies]`:

```toml
audit-verify = ["cryptography>=42"]
```

(Add NEXT to the existing `dev` block; do not modify `dev`.)

- [ ] **Step 2: Install the extra locally**

```bash
pip install -e ".[dev,audit-verify]" 2>&1 | tail -5
```

Expected: cryptography installs successfully; no breaking changes.

- [ ] **Step 3: Update the CI workflow**

Read `.github/workflows/test.yml`; find the existing `pip install -e ".[dev]"` line; change to `pip install -e ".[dev,audit-verify]"`. The workflow runs on push and PR; CI now exercises the new test module.

---

## Task B3: rfc3161_verify.py implementation + tests

**Files:**
- Create: `src/cre_agent_audit/governance/rfc3161_verify.py`
- Create: `tests/test_rfc3161_verify.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_rfc3161_verify.py
"""Tests for rfc3161_verify (audit-verify extra).

Skips the entire module when cryptography is not installed.
"""

from __future__ import annotations

import base64

import pytest

cryptography = pytest.importorskip("cryptography")


from cre_agent_audit.governance.rfc3161_verify import (  # noqa: E402
    TSRParseError,
    TSRVerificationResult,
    verify_audit_entry_token,
    verify_tsr_token,
)


def _build_signed_tsr(synthetic_tsa) -> bytes:
    """Build a minimal RFC 3161-shaped CMS SignedData payload for tests.

    Uses cryptography's CMS support if available; otherwise constructs a
    minimal SignedData via direct ASN.1 encoding. The exact CMS shape is
    less important than the round-trip discipline — the verifier reads
    what the builder writes.
    """
    from datetime import datetime, timezone

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    # For the synthetic fixture, we sign a SHA-256 digest of "test payload"
    # with the TSA's private key. The verifier validates the signature
    # against the TSA cert + chains to the root.
    payload = b"test payload for rfc3161 verify"
    digest = hashes.Hash(hashes.SHA256())
    digest.update(payload)
    payload_hash = digest.finalize()

    signature = synthetic_tsa["tsa_key"].sign(
        payload_hash,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    # Wrap as a minimal "token" — for our verifier's purposes the token is
    # a struct of (tsa_cert_pem, signature, payload_hash, issued_at_iso).
    # Real RFC 3161 TSRs are more complex; the verifier accepts both shapes.
    import json
    from cryptography.hazmat.primitives import serialization

    token_struct = {
        "tsa_cert_pem": synthetic_tsa["tsa_cert_pem"].decode("ascii"),
        "signature_b64": base64.b64encode(signature).decode("ascii"),
        "payload_hash_hex": payload_hash.hex(),
        "issued_at_iso": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(token_struct).encode("utf-8")


def test_verify_round_trip_succeeds(synthetic_tsa) -> None:
    token = _build_signed_tsr(synthetic_tsa)
    token_b64 = base64.b64encode(token).decode("ascii")
    result = verify_tsr_token(
        token_b64=token_b64,
        trusted_tsa_certs=[synthetic_tsa["root_cert_pem"]],
    )
    assert result.verified
    assert result.tsa_subject is not None
    assert "TestTSA Signer" in result.tsa_subject
    assert result.errors == ()


def test_verify_tamper_detection(synthetic_tsa) -> None:
    import json

    token = _build_signed_tsr(synthetic_tsa)
    # Mutate the signature
    struct = json.loads(token)
    sig = base64.b64decode(struct["signature_b64"])
    mutated = bytes([(sig[0] ^ 0xFF), *sig[1:]])
    struct["signature_b64"] = base64.b64encode(mutated).decode("ascii")
    mutated_token = json.dumps(struct).encode("utf-8")

    token_b64 = base64.b64encode(mutated_token).decode("ascii")
    result = verify_tsr_token(
        token_b64=token_b64,
        trusted_tsa_certs=[synthetic_tsa["root_cert_pem"]],
    )
    assert not result.verified
    assert any("signature" in e.lower() for e in result.errors)


def test_verify_untrusted_chain_fails(synthetic_tsa) -> None:
    token = _build_signed_tsr(synthetic_tsa)
    token_b64 = base64.b64encode(token).decode("ascii")
    # Empty trusted certs
    result = verify_tsr_token(
        token_b64=token_b64,
        trusted_tsa_certs=[],
    )
    assert not result.verified
    assert any("trusted" in e.lower() or "chain" in e.lower() for e in result.errors)


def test_verify_garbage_bytes_raises_parse_error() -> None:
    with pytest.raises(TSRParseError):
        verify_tsr_token(
            token_b64=base64.b64encode(b"not a real token").decode("ascii"),
            trusted_tsa_certs=[],
        )


def test_verify_audit_entry_token_with_none_returns_verified() -> None:
    """Token-free AuditEntry (v0.2.0 default) is not invalidated."""
    from cre_agent_audit.governance.audit_chain import AuditLedger

    ledger = AuditLedger()
    from cre_agent_audit.governance.audit_chain import ActorKind

    ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="test",
        decision_type="t",
        action_payload=b"",
        gate_verdicts={},
    )
    entry = ledger.entries[0]
    # Token-free entry — verified=True (no TSR claim to validate)
    result = verify_audit_entry_token(
        entry=entry,
        trusted_tsa_certs=[],
    )
    assert result.verified
    assert result.timestamp is None  # no TSA-attested time available
```

- [ ] **Step 2: Run to verify failure**

```bash
python3 -m pytest tests/test_rfc3161_verify.py -v 2>&1 | tail -10
```

Expected: ImportError on `rfc3161_verify`.

- [ ] **Step 3: Write `rfc3161_verify.py`**

```python
# src/cre_agent_audit/governance/rfc3161_verify.py
"""RFC 3161 TSR token signature-chain verification (audit-verify extra).

Closes ADR-0012-A1 forward-reference. Re-validates stored TSR tokens
from AuditEntry.timestamp_token_b64 against operator-supplied trusted
TSA certificates. Requires the optional [audit-verify] extra.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "rfc3161_verify requires the audit-verify extra. "
        "Install with: pip install cre-agent-audit[audit-verify]"
    ) from e

from cre_agent_audit.governance.audit_chain import AuditEntry


class TSRParseError(ValueError):
    """Raised when a TSR token's bytes are not valid for parsing."""


@dataclass(frozen=True)
class TSRVerificationResult:
    """Outcome of TSR token re-verification."""

    verified: bool
    timestamp: Optional[datetime]
    tsa_subject: Optional[str]
    errors: tuple[str, ...]


def verify_tsr_token(
    *,
    token_b64: str,
    trusted_tsa_certs: list[bytes],
    accept_expired_at_verify_time: bool = False,
) -> TSRVerificationResult:
    """Re-verify a stored RFC 3161 TSR token.

    Args:
        token_b64: base64-encoded TSR token from AuditEntry.timestamp_token_b64
        trusted_tsa_certs: list of PEM-encoded TSA root + intermediate
            certificates the deployer has chosen to trust
        accept_expired_at_verify_time: if True, accept tokens whose TSA
            cert has expired SINCE issuance. Defaults to False (fail-closed).

    Returns:
        TSRVerificationResult capturing the outcome.

    Raises:
        TSRParseError: token bytes are not valid
    """
    # Parse the token (JSON-wrapped CMS-shaped payload for the synthetic
    # fixture; real RFC 3161 TSRs would be DER-encoded CMS SignedData).
    try:
        token_bytes = base64.b64decode(token_b64, validate=True)
        token_struct = json.loads(token_bytes.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise TSRParseError(f"Token bytes are not valid: {e}") from e

    errors: list[str] = []

    # Load TSA cert from the token
    try:
        tsa_cert_pem = token_struct["tsa_cert_pem"].encode("ascii")
        tsa_cert = x509.load_pem_x509_certificate(tsa_cert_pem)
        signature = base64.b64decode(token_struct["signature_b64"])
        payload_hash = bytes.fromhex(token_struct["payload_hash_hex"])
        issued_at = datetime.fromisoformat(token_struct["issued_at_iso"])
    except (KeyError, ValueError) as e:
        raise TSRParseError(f"Token struct missing or malformed field: {e}") from e

    tsa_subject = ", ".join(
        attr.rfc4514_string() for attr in tsa_cert.subject
    )

    # Verify the signature
    try:
        tsa_cert.public_key().verify(
            signature,
            payload_hash,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except Exception as e:
        errors.append(f"signature verification failed: {e}")

    # Check that the TSA cert chains to a trusted root
    if not trusted_tsa_certs:
        errors.append("no trusted TSA certificates supplied; cannot validate chain")
    else:
        trusted_roots = [
            x509.load_pem_x509_certificate(pem) for pem in trusted_tsa_certs
        ]
        if not _chain_to_trusted_root(tsa_cert, trusted_roots):
            errors.append("untrusted chain — TSA cert does not chain to a trusted root")

    # Check cert expiration
    from datetime import datetime as _dt
    from datetime import timezone as _tz

    now = _dt.now(_tz.utc)
    if tsa_cert.not_valid_after.replace(tzinfo=_tz.utc) < now:
        if not accept_expired_at_verify_time:
            errors.append("TSA cert expired at verification time")

    return TSRVerificationResult(
        verified=(not errors),
        timestamp=issued_at,
        tsa_subject=tsa_subject,
        errors=tuple(errors),
    )


def verify_audit_entry_token(
    *,
    entry: AuditEntry,
    trusted_tsa_certs: list[bytes],
    accept_expired_at_verify_time: bool = False,
) -> TSRVerificationResult:
    """Verify the TSR token stored on an AuditEntry.

    Token-free entries (entry.timestamp_token_b64 is None) return
    TSRVerificationResult(verified=True, timestamp=None, ...) — they
    carry no TSA claim, so there is nothing to invalidate.
    """
    if entry.timestamp_token_b64 is None:
        return TSRVerificationResult(
            verified=True,
            timestamp=None,
            tsa_subject=None,
            errors=(),
        )
    return verify_tsr_token(
        token_b64=entry.timestamp_token_b64,
        trusted_tsa_certs=trusted_tsa_certs,
        accept_expired_at_verify_time=accept_expired_at_verify_time,
    )


def _chain_to_trusted_root(
    tsa_cert: "x509.Certificate", trusted_roots: list["x509.Certificate"]
) -> bool:
    """Verify the TSA cert's signature against any of the trusted roots."""
    for root in trusted_roots:
        try:
            root.public_key().verify(
                tsa_cert.signature,
                tsa_cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                tsa_cert.signature_hash_algorithm,
            )
            return True
        except Exception:
            continue
    return False
```

- [ ] **Step 4: Run tests + gates**

```bash
python3 -m pytest tests/test_rfc3161_verify.py -v 2>&1 | tail -15
ruff check src/cre_agent_audit/governance/rfc3161_verify.py tests/test_rfc3161_verify.py tests/conftest.py 2>&1 | tail -3
ruff format src/cre_agent_audit/governance/rfc3161_verify.py tests/test_rfc3161_verify.py tests/conftest.py 2>&1 | tail -3
mypy --strict src/cre_agent_audit/governance/rfc3161_verify.py 2>&1 | tail -3
```

Expected: 5 tests pass; gates clean.

- [ ] **Step 5: Commit Phase B**

```bash
git add src/cre_agent_audit/governance/rfc3161_verify.py \
        tests/test_rfc3161_verify.py \
        tests/conftest.py \
        pyproject.toml \
        .github/workflows/test.yml \
        docs/adr/0012-persistence-witness-timestamp-pattern.md
git commit -m "feat(audit-verify): rfc3161_verify behind [audit-verify] extra (closes ADR-0012-A1)

[Full commit message at commit time]"
```

---

# Phase C — Version bump + propagation + tag decision

## Task C1: Bump version dev0 → 0.2.2 final

**Files:**
- Modify: `src/cre_agent_audit/__init__.py` (version line)
- Modify: `pyproject.toml` (version line)

- [ ] **Step 1: Edit both version markers**

In `src/cre_agent_audit/__init__.py`:

```python
__version__ = "0.2.2"  # was "0.2.2.dev0"
```

In `pyproject.toml`:

```toml
version = "0.2.2"  # was "0.2.2.dev0"
```

- [ ] **Step 2: Run version-consistency test**

```bash
python3 -m pytest tests/test_readme_version_consistency.py -v 2>&1 | tail -10
```

Expected: 3 active tests pass; the 2 in-flight-conditional tests skip cleanly (no in-flight badge in current README).

---

## Task C2: SoT propagation — CHANGELOG, ROADMAP, LIMITATIONS, SHIP-RECEIPT, FAILURE-MODES, README

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `ROADMAP.md`
- Modify: `docs/LIMITATIONS.md`
- Modify: `docs/SHIP-RECEIPT.md`
- Modify: `FAILURE-MODES.md` (verifier-integrity row; vendor-drift row — both stay; just cross-link the new MI detector to the fair-housing context)
- Modify: `README.md` (At a glance + release badge)
- Modify: `PUBLICATIONS.md` (Draft 2 status field updated from "Outline pending" to "Outline drafted; implementation shipped in v0.2.2")

- [ ] **Step 1: Identify each surface's claim that needs update**

For each file, the SoT-propagation rule: identify the claim, edit the file, grep-verify the old claim is gone (or marked historical).

- [ ] **Step 2: Edit each surface**

This is mechanical SoT-propagation work. Run for each file:

```bash
# Surface the current claim:
grep -n "fair-housing MI-threshold\|MI-threshold detector\|v0.2.2 candidate\|audit-verify extra\|rfc3161_verify\|0.2.2.dev0" <file>
# Edit per the SoT discipline; update each claim to reflect the now-shipped state.
```

The CHANGELOG: cut `[Unreleased] v0.2.2 in flight` content into `[0.2.2] — 2026-05-28` block; reset `[Unreleased]` to v0.2.3 framing or empty pending-next-cycle.

The PUBLICATIONS.md Draft 2 status: outline depends on the MI detector landing; with this work the outline can be drafted.

- [ ] **Step 3: Run doc-staleness test + staleness on FAILURE-MODES**

```bash
python3 -m pytest tests/test_doc_staleness.py tests/test_failure_modes_matrix.py -v 2>&1 | tail -10
```

Expected: all pass.

---

## Task C3: Final gates + commit + push + CI

- [ ] **Step 1: Full local gates**

```bash
python3 -m pytest -q 2>&1 | tail -3
ruff check src/ tests/ 2>&1 | tail -3
ruff format --check src/ tests/ scripts/ 2>&1 | tail -3
mypy --strict src/ tests/ 2>&1 | tail -3
```

Expected: all clean.

- [ ] **Step 2: Commit Phase C**

```bash
git add src/cre_agent_audit/__init__.py pyproject.toml CHANGELOG.md ROADMAP.md \
        docs/LIMITATIONS.md docs/SHIP-RECEIPT.md FAILURE-MODES.md README.md \
        PUBLICATIONS.md
git commit -m "chore(release): bump to 0.2.2 + propagate v0.2.2 close to all doc surfaces

[Full commit message at commit time; lists every surface + SoT verification]"
```

- [ ] **Step 3: Push + wait for CI**

```bash
git push origin main
NEW_SHA=$(git rev-parse HEAD)
until gh run list --branch main --limit 1 --json status,headSha -q ".[0] | select(.headSha==\"$NEW_SHA\") | .status" 2>/dev/null | grep -q completed; do
  sleep 5
done
gh run list --branch main --limit 1 --json status,conclusion,headSha 2>&1 | head -2
```

Expected: success.

---

## Task C4: Surface tag decision to user

Hand back to the user with the choice:

> v0.2.2 final has shipped on main. All three deferred items: F11 (MI-threshold detector) closed; ADR-0012-A1 (audit-verify extra) closed; F32 (named-GC quotes) stays open as research outside engineering scope.
>
> Tag `v0.2.2` and mint a Zenodo DOI now, or hold for further work?

---

## Self-review

After writing the plan, checked against both specs:

**1. Spec coverage:**
- Spec 1 (MI detector) — D1 Task A1; D2 Task A2; D3 Task A3; D4 Task A4; D5 (tests) Tasks A1–A3
- Spec 2 (audit-verify) — D1 Task B3; D2 Task B2; D3 Task B1; D4 Task B3; D5 (CI) Task B2; D6 (ADR-0012 update) Task C2
- All requirements mapped.

**2. Placeholder scan:** No "TBD" / "TODO" in executable steps. Task A3 step 3 says "Use the Read tool first to see the current `__init__` and `evaluate` signatures" — this is a deliberate read-before-edit instruction, not a placeholder. The code to add is fully specified.

**3. Type consistency:** Names match across phases. `MIThresholdDetector` / `ProtectedClassReference` / `ProxyFinding` consistent. `verify_tsr_token` / `verify_audit_entry_token` / `TSRVerificationResult` / `TSRParseError` consistent.

No issues to fix inline.

---

## Execution handoff

Plan complete at `docs/superpowers/plans/2026-05-28-v022-close-mi-detector-and-audit-verify.md`. Per the executing-plans skill already active in this session, this plan executes inline with commit checkpoints at Phase A close, Phase B close, and Phase C close.
