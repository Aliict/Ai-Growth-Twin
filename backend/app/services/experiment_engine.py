"""A real (if synthetic) A/B test simulator: randomized control/variant
assignment, a two-proportion z-test, confidence interval, and p-value.

The LLM-generated hypothesis (see ai_features.generate_experiment) proposes
*what* to test and *what effect size to expect*; this module is what actually
measures whether an effect of that size would be statistically detectable,
by simulating a trial of a given sample size against the company's real
baseline conversion rate. It does not call an LLM.
"""

import math

import numpy as np

Z_95 = 1.959963984540054


def _normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def run_experiment_simulation(
    baseline_conversion_rate: float,
    expected_uplift_pct: float,
    sample_size_per_arm: int = 1000,
    random_seed: int | None = None,
) -> dict:
    """Simulate a randomized control/variant trial.

    `expected_uplift_pct` is treated as the assumed *true* effect size (from
    the hypothesis) that the variant population is generated with; the
    simulation then measures whether a trial of this sample size would
    actually detect that effect, the way a real experiment would.
    """
    rng = np.random.default_rng(random_seed)

    control_true_rate = min(max(baseline_conversion_rate, 0.0001), 0.9999)
    variant_true_rate = min(max(control_true_rate * (1 + expected_uplift_pct / 100), 0.0001), 0.9999)

    control_conversions = int(rng.binomial(sample_size_per_arm, control_true_rate))
    variant_conversions = int(rng.binomial(sample_size_per_arm, variant_true_rate))

    control_rate = control_conversions / sample_size_per_arm
    variant_rate = variant_conversions / sample_size_per_arm

    observed_uplift_pct = (
        (variant_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0.0
    )

    pooled_rate = (control_conversions + variant_conversions) / (2 * sample_size_per_arm)
    pooled_se = math.sqrt(pooled_rate * (1 - pooled_rate) * (2 / sample_size_per_arm))
    z_score = (variant_rate - control_rate) / pooled_se if pooled_se > 0 else 0.0
    p_value = 2 * (1 - _normal_cdf(abs(z_score)))

    diff = variant_rate - control_rate
    unpooled_se = math.sqrt(
        control_rate * (1 - control_rate) / sample_size_per_arm
        + variant_rate * (1 - variant_rate) / sample_size_per_arm
    )
    ci_low = diff - Z_95 * unpooled_se
    ci_high = diff + Z_95 * unpooled_se

    return {
        "sample_size_per_arm": sample_size_per_arm,
        "control_conversions": control_conversions,
        "control_rate": round(control_rate, 4),
        "variant_conversions": variant_conversions,
        "variant_rate": round(variant_rate, 4),
        "observed_uplift_pct": round(observed_uplift_pct, 2),
        "p_value": round(p_value, 4),
        "is_significant": bool(p_value < 0.05),
        "confidence_interval_low": round(ci_low, 4),
        "confidence_interval_high": round(ci_high, 4),
    }
