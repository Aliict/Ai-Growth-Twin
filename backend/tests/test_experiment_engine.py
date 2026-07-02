from app.services.experiment_engine import run_experiment_simulation


def test_result_invariants_hold_across_many_seeds():
    for seed in range(30):
        result = run_experiment_simulation(
            baseline_conversion_rate=0.1,
            expected_uplift_pct=20,
            sample_size_per_arm=1000,
            random_seed=seed,
        )
        assert 0.0 <= result["control_rate"] <= 1.0
        assert 0.0 <= result["variant_rate"] <= 1.0
        assert 0.0 <= result["p_value"] <= 1.0
        assert result["confidence_interval_low"] <= result["confidence_interval_high"]
        assert result["is_significant"] == (result["p_value"] < 0.05)


def test_null_effect_rarely_produces_false_positives():
    """When control and variant have the identical true rate, a 5%-significance
    z-test should flag 'significant' close to 5% of the time (Type I error
    rate), not routinely — this validates the z-test math itself."""
    significant_count = 0
    trials = 200
    for seed in range(trials):
        result = run_experiment_simulation(
            baseline_conversion_rate=0.15,
            expected_uplift_pct=0,
            sample_size_per_arm=1000,
            random_seed=seed,
        )
        if result["is_significant"]:
            significant_count += 1

    false_positive_rate = significant_count / trials
    assert false_positive_rate < 0.15  # generous margin above the expected ~5%


def test_large_true_effect_is_detected_most_of_the_time():
    """A large, real uplift with a big enough sample should be caught
    (statistical power), unlike the null-effect case above."""
    significant_count = 0
    trials = 50
    for seed in range(trials):
        result = run_experiment_simulation(
            baseline_conversion_rate=0.1,
            expected_uplift_pct=80,
            sample_size_per_arm=2000,
            random_seed=seed,
        )
        if result["is_significant"]:
            significant_count += 1

    assert significant_count / trials > 0.8
