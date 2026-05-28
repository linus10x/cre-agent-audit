"""Mutual-information-based learned-proxy detector for the Fair-Housing
Pre-Flight Gate (ADR-0008 update; closes F11 from SHIP-RECEIPT).

Detects features carrying statistical signal about a binary protected-class
attribute, even when those features are lexically opaque (zip-code-shaped
features carrying voucher-status signal, etc.). Anchored on:

- Kusner et al. 2017 — Counterfactual Fairness (NeurIPS)
- Calmon et al. 2017 — Optimized Pre-Processing for Discrimination Prevention (NeurIPS)
- Hardt-Price-Srebro 2016 — Equality of Opportunity in Supervised Learning
- Pedreshi-Ruggieri-Turini 2008 — Discrimination-aware data mining (KDD)

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
    """Raised when a ``ProtectedClassReference`` is malformed or too small."""


class MIReferenceUndersizedWarning(UserWarning):
    """Emitted when a ``ProtectedClassReference`` has fewer than 100 samples.

    Statistics on small samples are unreliable. The detector still runs but
    the warning surfaces the limitation to the deployer at construction time.
    Non-suppressible by design.
    """


@dataclass(frozen=True)
class ProtectedClassReference:
    """Operator-configured labeled sample for MI computation.

    ``feature_samples`` is a tuple of mapping objects; each mapping is one
    historical applicant's features. ``protected_class_labels`` is the
    parallel tuple (1 = protected, 0 = not). At least 30 samples required.
    """

    feature_samples: tuple[Mapping[str, object], ...]
    protected_class_labels: tuple[int, ...]
    protected_class_name: str

    def __post_init__(self) -> None:
        n = len(self.feature_samples)
        if n < 30:
            raise InvalidReferenceError(
                f"ProtectedClassReference requires at least 30 samples; got {n}"
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
    - binary / categorical features: ``I(F; Y)`` computed directly from a
      contingency table
    - numeric features (more than 2 distinct values): discretize into 4
      quartile bins, then compute ``I(F_binned; Y)``

    Uses base-2 log (output in bits), normalized to ``[0, 1]`` by the
    marginal entropy of ``Y``.
    """

    def __init__(self, reference: ProtectedClassReference) -> None:
        self._reference = reference
        self._cache: dict[str, float] = {}
        self._feature_names: set[str] = set()
        for sample in reference.feature_samples:
            self._feature_names.update(sample.keys())

    def mi_score(self, feature_name: str, applicant_value: object) -> float:
        """Return MI between the reference's distribution of ``feature_name``
        and the protected-class labels.

        Independent of ``applicant_value`` — the caller passes it for API
        symmetry but MI is a reference property.
        """
        del applicant_value  # API symmetry; MI is a reference property
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

    def mi_scores_across_features(self, feature_names: Iterable[str]) -> Mapping[str, float]:
        return {n: self.mi_score(n, applicant_value=None) for n in feature_names}

    def _compute_mi(self, feature_values: list[object], labels: list[int]) -> float:
        if not feature_values:
            return 0.0

        all_numeric = all(isinstance(v, (int, float)) for v in feature_values)
        distinct = len(set(feature_values))
        if all_numeric and distinct > 2:
            numeric_values = [v for v in feature_values if isinstance(v, (int, float))]
            sorted_vals = sorted(float(v) for v in numeric_values)
            n = len(sorted_vals)
            q1 = sorted_vals[n // 4]
            q2 = sorted_vals[n // 2]
            q3 = sorted_vals[3 * n // 4]
            binned: list[object] = [_quartile_bin(float(v), q1, q2, q3) for v in numeric_values]
            return _categorical_mi(binned, labels)

        return _categorical_mi(list(feature_values), labels)


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

    ``I(X; Y) = sum_x sum_y P(x,y) * log2(P(x,y) / (P(x) * P(y)))``,
    normalized to ``[0, 1]`` by the marginal entropy of ``Y``.
    """
    n = len(features)
    if n == 0:
        return 0.0

    feature_counts = Counter(features)
    label_counts = Counter(labels)
    joint_counts = Counter(zip(features, labels, strict=True))

    h_y = 0.0
    for ly in label_counts.values():
        p_y = ly / n
        if p_y > 0:
            h_y -= p_y * math.log2(p_y)
    if h_y == 0.0:
        return 0.0

    mi = 0.0
    for (fx, ly), joint in joint_counts.items():
        p_xy = joint / n
        p_x = feature_counts[fx] / n
        p_y = label_counts[ly] / n
        if p_xy > 0 and p_x > 0 and p_y > 0:
            mi += p_xy * math.log2(p_xy / (p_x * p_y))

    return max(0.0, min(1.0, mi / h_y))


class MIThresholdDetector:
    """Flags features whose MI with the protected class exceeds threshold."""

    def __init__(
        self,
        *,
        reference: ProtectedClassReference,
        mi_threshold: float = 0.10,
    ) -> None:
        if not (0.0 < mi_threshold <= 1.0):
            raise ValueError(f"mi_threshold must be in (0.0, 1.0]; got {mi_threshold}")
        self._reference = reference
        self._threshold = mi_threshold
        self._calculator = MutualInformationCalculator(reference=reference)

    def detect_proxies(self, applicant_features: Mapping[str, object]) -> tuple[ProxyFinding, ...]:
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
