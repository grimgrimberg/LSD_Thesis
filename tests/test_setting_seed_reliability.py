import numpy as np

from lsd_thesis.setting_seed.reliability import (
    bootstrap_ci,
    classify_reliability_tier,
    sign_consistency,
    summarize_metric_reliability,
)


def test_bootstrap_ci_is_deterministic() -> None:
    values = np.asarray([0.8, 1.0, 1.1, 1.2], dtype=float)

    first = bootstrap_ci(values, seed=17, iterations=250)
    second = bootstrap_ci(values, seed=17, iterations=250)

    assert first == second
    assert first[0] > 0.0
    assert first[1] > first[0]


def test_stable_feature_is_classified_tier_a() -> None:
    values = np.asarray([0.8, 1.0, 1.1, 1.2], dtype=float)
    summary = summarize_metric_reliability("synthetic_metric", values, confidence="strong", expected_sign=1, seed=13)

    assert summary["tier"] == "Tier A"
    assert summary["sign_consistency"] == 1.0
    assert summary["theory_sign_conflict"] is False


def test_unstable_feature_is_classified_fragile() -> None:
    values = np.asarray([-1.0, 0.8, -0.4, 0.5], dtype=float)
    summary = summarize_metric_reliability("synthetic_metric", values, confidence="weak", expected_sign=1, seed=13)

    assert summary["tier"] == "Tier C"
    assert summary["sign_consistency"] < 0.75


def test_theory_conflicted_coherent_feature_is_diagnostic() -> None:
    tier = classify_reliability_tier(
        mean_delta=0.5,
        ci_low=0.2,
        ci_high=0.8,
        sign_consistency_fraction=1.0,
        confidence="moderate",
        theory_sign_conflict=True,
        missingness_fraction=0.0,
    )

    assert tier == "Tier D"


def test_sign_consistency_handles_zero_without_divide_by_zero() -> None:
    assert sign_consistency(np.asarray([0.0, 0.0], dtype=float), reference_delta=0.0) == 0.0
