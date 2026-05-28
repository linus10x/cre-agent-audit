"""SafeRent-shaped synthetic ProtectedClassReference.

Engineered to produce a zip-code-shaped feature that carries MI above
threshold against voucher-holder status — the exact failure shape the
SafeRent class settlement (*Louis v. SafeRent Solutions, LLC*, D. Mass.,
November 20, 2024) named.

No real PII; no real operator data. Deterministic via ``random.Random(seed)``.
"""

from __future__ import annotations

import random

from cre_agent_audit.governance.mi_threshold_detector import (
    ProtectedClassReference,
)

_SEED = 20260528


def saferent_shaped_reference(n_samples: int = 1000, seed: int = _SEED) -> ProtectedClassReference:
    """Generate a 1,000-applicant reference with a hidden voucher-status proxy.

    - 50% of applicants are voucher-holders (protected_class_label = 1)
    - ``zip_code_quintile`` (5-bin) is correlated with voucher status: voucher
      holders are concentrated in quintiles 4 and 5 at p ≈ 0.8; non-voucher
      holders are concentrated in quintiles 1 and 2 at p ≈ 0.7
    - ``credit_score``: independent of voucher status (uniform 550-820)
    - ``income_x_rent``: independent (uniform 1.5-5.0)
    - ``applied_via_lottery``: weak correlation (p ≈ 0.55 vs 0.45); meant
      to demonstrate that not-every-correlated-feature gets flagged
    """
    rng = random.Random(seed)
    samples: list[dict[str, object]] = []
    labels: list[int] = []

    for _ in range(n_samples):
        is_voucher = rng.random() < 0.5
        labels.append(1 if is_voucher else 0)

        if is_voucher:
            zip_q = rng.choices([1, 2, 3, 4, 5], weights=[5, 5, 10, 35, 45])[0]
        else:
            zip_q = rng.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]

        credit = rng.randint(550, 820)
        income_x_rent = rng.uniform(1.5, 5.0)

        lottery = rng.random() < (0.55 if is_voucher else 0.45)

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
