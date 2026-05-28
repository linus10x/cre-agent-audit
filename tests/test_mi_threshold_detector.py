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

import warnings
from collections.abc import Sequence

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


def _make_reference(
    feature_values: Sequence[object], labels: Sequence[int]
) -> ProtectedClassReference:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", MIReferenceUndersizedWarning)
        return ProtectedClassReference(
            feature_samples=tuple({"f": v} for v in feature_values),
            protected_class_labels=tuple(labels),
            protected_class_name="voucher_holder",
        )


# --- Reference validation -------------------------------------------------- #


def test_reference_requires_min_30_samples() -> None:
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
    assert any(issubclass(w.category, MIReferenceUndersizedWarning) for w in caught)


def test_reference_rejects_mismatched_label_length() -> None:
    with pytest.raises(InvalidReferenceError):
        ProtectedClassReference(
            feature_samples=tuple({"f": i} for i in range(100)),
            protected_class_labels=tuple([0] * 50),
            protected_class_name="voucher_holder",
        )


# --- MI calculator --------------------------------------------------------- #


def test_mi_calculator_independent_feature_returns_low_score() -> None:
    feature_values = [0, 1] * 100
    labels = [0, 0, 1, 1] * 50
    ref = _make_reference(feature_values, labels)
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score("f", applicant_value=0)
    assert score < 0.05, f"Independent feature MI should be ~0; got {score}"


def test_mi_calculator_perfect_predictor_returns_one() -> None:
    feature_values = [0] * 100 + [1] * 100
    labels = [0] * 100 + [1] * 100
    ref = _make_reference(feature_values, labels)
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score("f", applicant_value=1)
    assert score > 0.95, f"Perfect predictor MI should be ~1; got {score}"


def test_mi_calculator_constant_feature_returns_zero() -> None:
    ref = _make_reference([42] * 200, [0] * 100 + [1] * 100)
    calc = MutualInformationCalculator(reference=ref)
    assert calc.mi_score("f", applicant_value=42) == 0.0


def test_mi_calculator_missing_feature_returns_zero() -> None:
    ref = _make_reference([0] * 100 + [1] * 100, [0] * 100 + [1] * 100)
    calc = MutualInformationCalculator(reference=ref)
    assert calc.mi_score("nonexistent_feature", applicant_value=1) == 0.0


def test_mi_calculator_numeric_feature_binning() -> None:
    feature_values = list(range(100)) + list(range(100, 200))
    labels = [0] * 100 + [1] * 100
    ref = _make_reference(feature_values, labels)
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score("f", applicant_value=150)
    assert score > 0.5, f"Strongly correlated numeric feature should fire; got {score}"


# --- Detector -------------------------------------------------------------- #


def test_detector_constructor_rejects_invalid_threshold() -> None:
    ref = _make_reference([0, 1] * 100, [0, 1] * 100)
    with pytest.raises(ValueError):
        MIThresholdDetector(reference=ref, mi_threshold=0.0)
    with pytest.raises(ValueError):
        MIThresholdDetector(reference=ref, mi_threshold=1.5)


def test_detector_flags_above_threshold() -> None:
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
    feature_values = [0, 1] * 100
    labels = [0, 0, 1, 1] * 50
    ref = _make_reference(feature_values, labels)
    detector = MIThresholdDetector(reference=ref, mi_threshold=0.10)
    findings = detector.detect_proxies({"f": 1})
    assert findings == ()


def test_finding_carries_severity_based_on_mi_score() -> None:
    feature_values = [0] * 100 + [1] * 100
    labels = [0] * 100 + [1] * 100
    ref = _make_reference(feature_values, labels)
    detector = MIThresholdDetector(reference=ref, mi_threshold=0.10)
    findings = detector.detect_proxies({"f": 1})
    assert findings[0].severity in (Severity.HIGH, Severity.CRITICAL)


# --- SafeRent-shaped synthetic fixture ------------------------------------ #


def test_saferent_fixture_zip_code_quintile_carries_strong_mi() -> None:
    """The engineered ``zip_code_quintile`` feature should carry MI > 0.10."""
    from tests.fixtures.saferent_shaped_reference import saferent_shaped_reference

    ref = saferent_shaped_reference()
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score("zip_code_quintile", applicant_value=4)
    assert score > 0.10, f"zip_code_quintile should be flagged; got MI={score:.3f}"


def test_saferent_fixture_credit_score_does_not_carry_mi() -> None:
    """Independent features should NOT be flagged."""
    from tests.fixtures.saferent_shaped_reference import saferent_shaped_reference

    ref = saferent_shaped_reference()
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score("credit_score", applicant_value=720)
    assert score < 0.10, f"credit_score should not be flagged; got MI={score:.3f}"


def test_saferent_fixture_end_to_end_proxy_detection() -> None:
    """The detector flags the zip-code proxy on a SafeRent-shaped applicant."""
    from tests.fixtures.saferent_shaped_reference import saferent_shaped_reference

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
