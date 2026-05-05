from __future__ import annotations

import warnings

import numpy as np

from lsd_thesis.condition_models import (
    build_window_eigenvalue_targets,
    engineer_window_features,
    evaluate_sklearn_condition_models,
    evaluate_sklearn_multitask_models,
)


def test_engineer_window_features_returns_expected_feature_count_and_names() -> None:
    windows = np.asarray(
        [
            [[0.0, 1.0], [1.0, 2.0], [0.5, 1.5], [1.5, 2.5]],
            [[1.0, 0.0], [2.0, 1.0], [1.5, 0.5], [2.5, 1.5]],
        ],
        dtype=float,
    )

    features, names = engineer_window_features(windows, module_names=("visual", "auditory"))

    assert features.shape == (2, 18)
    assert len(names) == 18
    assert names[0] == "metric.within_network_stability"
    assert "mean.visual" in names
    assert "std.auditory" in names
    assert "lag1.visual" in names
    assert "fc.visual__auditory" in names
    assert "fc_eig_1" in names


def test_build_window_eigenvalue_targets_returns_descending_fc_spectra() -> None:
    windows = np.asarray(
        [
            [[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 3.0]],
            [[0.0, 5.0], [1.0, 5.0], [2.0, 5.0], [3.0, 5.0]],
        ],
        dtype=float,
    )

    eigen_targets, target_names = build_window_eigenvalue_targets(windows)

    assert eigen_targets.shape == (2, 2)
    assert target_names == ["fc_eig_1", "fc_eig_2"]
    np.testing.assert_allclose(eigen_targets[0], np.asarray([2.0, 0.0]), atol=1e-6)
    np.testing.assert_allclose(eigen_targets[1], np.asarray([1.0, 1.0]), atol=1e-6)


def test_constant_window_eigenvalue_targets_are_finite_without_runtime_warnings() -> None:
    windows = np.ones((2, 16, 3), dtype=float)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", RuntimeWarning)
        eigen_targets, target_names = build_window_eigenvalue_targets(windows)

    assert captured == []
    assert eigen_targets.shape == (2, 3)
    assert target_names == ["fc_eig_1", "fc_eig_2", "fc_eig_3"]
    assert np.all(np.isfinite(eigen_targets))


def test_evaluate_sklearn_condition_models_uses_subject_held_out_cv() -> None:
    base_plcb = np.zeros((64, 8), dtype=float)
    base_lsd = np.ones((64, 8), dtype=float) * 1.5
    windows = []
    labels = []
    subjects = []
    for subject_index, subject in enumerate(("sub-001", "sub-002", "sub-003"), start=1):
        subject_shift = subject_index * 0.05
        windows.append(base_plcb + subject_shift)
        labels.append(0)
        subjects.append(subject)
        windows.append(base_lsd + subject_shift)
        labels.append(1)
        subjects.append(subject)

    dataset = {
        "windows": np.asarray(windows, dtype=float),
        "condition": np.asarray(labels, dtype=np.int8),
        "subject": np.asarray(subjects, dtype="U32"),
    }

    results = evaluate_sklearn_condition_models(dataset, module_names=tuple(f"m{i}" for i in range(8)))

    assert results["dataset"]["sample_count"] == 6
    assert results["dataset"]["subject_count"] == 3
    assert results["dataset"]["fold_count"] == 3
    assert set(results["models"]) == {"logistic_regression", "hist_gradient_boosting"}
    assert len(results["models"]["logistic_regression"]["folds"]) == 3
    assert results["models"]["logistic_regression"]["aggregate"]["accuracy_mean"] >= 0.99
    assert results["models"]["hist_gradient_boosting"]["aggregate"]["balanced_accuracy_mean"] >= 0.99
    assert results["models"]["logistic_regression"]["top_features"]


def test_evaluate_sklearn_multitask_models_reports_classification_and_eigen_metrics() -> None:
    timeline = np.linspace(0.0, 2.0 * np.pi, 64, endpoint=False)
    base_plcb = np.stack(
        [
            np.sin(timeline),
            np.cos(timeline),
            np.sin(timeline + 0.5),
            np.cos(timeline + 0.5),
            np.sin(timeline + 1.0),
            np.cos(timeline + 1.0),
            np.sin(timeline + 1.5),
            np.cos(timeline + 1.5),
        ],
        axis=1,
    )
    base_lsd = np.stack(
        [
            np.sin(timeline),
            np.sin(timeline + 0.05),
            np.sin(timeline + 0.1),
            np.sin(timeline + 0.15),
            np.sin(timeline + 0.2),
            np.sin(timeline + 0.25),
            np.sin(timeline + 0.3),
            np.sin(timeline + 0.35),
        ],
        axis=1,
    )

    windows = []
    labels = []
    subjects = []
    for subject_index, subject in enumerate(("sub-001", "sub-002", "sub-003"), start=1):
        subject_scale = 1.0 + subject_index * 0.05
        subject_shift = subject_index * 0.02
        windows.append(base_plcb * subject_scale + subject_shift)
        labels.append(0)
        subjects.append(subject)
        windows.append(base_lsd * subject_scale + subject_shift)
        labels.append(1)
        subjects.append(subject)

    dataset = {
        "windows": np.asarray(windows, dtype=float),
        "condition": np.asarray(labels, dtype=np.int8),
        "subject": np.asarray(subjects, dtype="U32"),
    }

    results = evaluate_sklearn_multitask_models(dataset, module_names=tuple(f"m{i}" for i in range(8)))

    assert results["dataset"]["sample_count"] == 6
    assert results["dataset"]["subject_count"] == 3
    assert results["dataset"]["fold_count"] == 3
    assert results["target_names"] == [f"fc_eig_{index}" for index in range(1, 9)]
    assert set(results["models"]) == {"ridge_multitask", "hist_gradient_multitask"}
    assert len(results["models"]["ridge_multitask"]["folds"]) == 3
    assert results["models"]["ridge_multitask"]["aggregate"]["accuracy_mean"] >= 0.99
    assert results["models"]["ridge_multitask"]["aggregate"]["eigen_mae_mean"] <= 0.05
    assert results["models"]["hist_gradient_multitask"]["aggregate"]["balanced_accuracy_mean"] >= 0.99
