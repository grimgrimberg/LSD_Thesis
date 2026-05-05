from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, balanced_accuracy_score, mean_absolute_error, mean_squared_error, r2_score, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.metrics import compute_observable_summary, compute_summary_metrics, safe_correlation_matrix

SUMMARY_METRIC_NAMES: tuple[str, ...] = (
    "within_network_stability",
    "cross_network_communication",
    "thalamic_coupling",
    "hierarchical_compression",
    "entropy_diversity",
    "switching_rate",
    "metastability_proxy",
    "effective_barrier_proxy",
)


def load_window_dataset(path: str | Path) -> dict[str, np.ndarray]:
    payload = np.load(Path(path))
    return {key: np.asarray(payload[key]) for key in payload.files}


def _safe_lag1_autocorrelation(series: np.ndarray) -> float:
    if len(series) < 2:
        return 0.0
    left = series[:-1] - np.mean(series[:-1])
    right = series[1:] - np.mean(series[1:])
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator < 1e-8:
        return 0.0
    return float(np.dot(left, right) / denominator)


def _safe_fc(window: np.ndarray) -> np.ndarray:
    return safe_correlation_matrix(window)


def _generic_metric_map(window: np.ndarray, modules: tuple[str, ...]) -> dict[str, float]:
    summary_metrics = compute_summary_metrics(window, modules)
    upper = summary_metrics.fc_matrix[np.triu_indices_from(summary_metrics.fc_matrix, k=1)]
    mean_fc = float(np.mean(upper)) if len(upper) else 0.0
    mean_abs_fc = float(np.mean(np.abs(upper))) if len(upper) else 0.0
    thalamic_index = modules.index("thalamic_gateway") if "thalamic_gateway" in modules else 0
    thalamic_row = np.delete(summary_metrics.fc_matrix[thalamic_index], thalamic_index)
    split_index = max(1, len(modules) // 2)
    left_signal = window[:, :split_index].mean(axis=1)
    right_signal = window[:, split_index:].mean(axis=1) if split_index < len(modules) else left_signal
    if np.std(left_signal) < 1e-8 or np.std(right_signal) < 1e-8:
        hierarchical = 0.0
    else:
        hierarchical = float(np.corrcoef(left_signal, right_signal)[0, 1])

    return {
        "within_network_stability": mean_abs_fc,
        "cross_network_communication": mean_fc,
        "thalamic_coupling": float(np.mean(thalamic_row)) if len(thalamic_row) else 0.0,
        "hierarchical_compression": hierarchical,
        "entropy_diversity": float(summary_metrics.state_entropy),
        "switching_rate": float(summary_metrics.switching_rate),
        "metastability_proxy": float(summary_metrics.dynamic_fc_change),
        "effective_barrier_proxy": float(np.mean(np.bincount(summary_metrics.state_labels))),
    }


def _window_metric_map(window: np.ndarray, modules: tuple[str, ...]) -> dict[str, float]:
    if modules == MODULE_NAMES:
        return compute_observable_summary(window, modules).metric_map()
    return _generic_metric_map(window, modules)


def engineer_window_features(
    windows: np.ndarray,
    module_names: tuple[str, ...] = MODULE_NAMES,
    *,
    include_fc_eigenvalues: bool = True,
) -> tuple[np.ndarray, list[str]]:
    if windows.ndim != 3:
        raise ValueError("Windows must be shaped [sample, time, module].")
    if windows.shape[-1] != len(module_names):
        raise ValueError("Window feature dimension must match module_names.")

    fc_indices = np.triu_indices(len(module_names), k=1)
    feature_names = list(f"metric.{name}" for name in SUMMARY_METRIC_NAMES)
    feature_names.append("global_signal_mean")
    feature_names.extend(f"mean.{name}" for name in module_names)
    feature_names.extend(f"std.{name}" for name in module_names)
    feature_names.extend(f"lag1.{name}" for name in module_names)
    feature_names.extend(f"fc.{module_names[i]}__{module_names[j]}" for i, j in zip(fc_indices[0], fc_indices[1], strict=False))
    if include_fc_eigenvalues:
        feature_names.extend(f"fc_eig_{index + 1}" for index in range(len(module_names)))

    feature_rows: list[list[float]] = []
    for window in windows:
        metric_map = _window_metric_map(window, module_names)
        fc_matrix = _safe_fc(window)
        eigenvalues = np.linalg.eigvalsh(fc_matrix)[::-1]

        row = [float(metric_map[name]) for name in SUMMARY_METRIC_NAMES]
        global_signal = window.mean(axis=1)
        row.append(float(np.mean(global_signal)))
        row.extend(float(value) for value in np.mean(window, axis=0))
        row.extend(float(value) for value in np.std(window, axis=0))
        row.extend(_safe_lag1_autocorrelation(window[:, index]) for index in range(window.shape[1]))
        row.extend(float(value) for value in fc_matrix[fc_indices])
        if include_fc_eigenvalues:
            row.extend(float(value) for value in eigenvalues)
        feature_rows.append(np.nan_to_num(np.asarray(row, dtype=float), nan=0.0, posinf=0.0, neginf=0.0).tolist())

    return np.asarray(feature_rows, dtype=float), feature_names


def build_window_eigenvalue_targets(windows: np.ndarray) -> tuple[np.ndarray, list[str]]:
    if windows.ndim != 3:
        raise ValueError("Windows must be shaped [sample, time, module].")

    targets = []
    for window in windows:
        fc_matrix = _safe_fc(window)
        targets.append(np.linalg.eigvalsh(fc_matrix)[::-1])

    target_names = [f"fc_eig_{index + 1}" for index in range(windows.shape[-1])]
    return np.asarray(targets, dtype=float), target_names


def _classification_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, float]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
    }
    if len(np.unique(y_true)) < 2:
        metrics["roc_auc"] = float("nan")
    else:
        metrics["roc_auc"] = float(roc_auc_score(y_true, probabilities))
    return metrics


def _regression_metrics(y_true: np.ndarray, predictions: np.ndarray) -> dict[str, float]:
    mae = float(mean_absolute_error(y_true, predictions))
    rmse = float(np.sqrt(mean_squared_error(y_true, predictions)))
    if y_true.shape[0] < 2:
        r2 = float("nan")
    else:
        r2 = float(r2_score(y_true, predictions, multioutput="uniform_average"))
    return {
        "eigen_mae": mae,
        "eigen_rmse": rmse,
        "eigen_r2": r2,
    }


def _aggregate_folds(folds: list[dict[str, float | int | str]]) -> dict[str, float]:
    metric_names = tuple(
        key
        for key in folds[0]
        if key not in {"fold", "left_out_subject"}
    )
    aggregate: dict[str, float] = {}
    for name in metric_names:
        values = np.asarray([float(fold[name]) for fold in folds], dtype=float)
        aggregate[f"{name}_mean"] = float(np.nanmean(values))
        aggregate[f"{name}_std"] = float(np.nanstd(values))
    return aggregate


def _top_logistic_features(coefficient_rows: list[np.ndarray], feature_names: list[str], limit: int = 12) -> list[dict[str, float | str]]:
    coefficients = np.asarray(coefficient_rows, dtype=float)
    mean_abs = np.mean(np.abs(coefficients), axis=0)
    signed_mean = np.mean(coefficients, axis=0)
    ranking = np.argsort(mean_abs)[::-1][:limit]
    return [
        {
            "feature": feature_names[index],
            "importance": float(mean_abs[index]),
            "signed_weight": float(signed_mean[index]),
        }
        for index in ranking
    ]


def _evaluate_single_model(
    *,
    model_name: str,
    build_model: Any,
    features: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    feature_names: list[str],
) -> dict[str, Any]:
    logo = LeaveOneGroupOut()
    folds: list[dict[str, float | int | str]] = []
    coefficient_rows: list[np.ndarray] = []
    predictions: list[dict[str, float | int | str]] = []

    for fold_index, (train_idx, test_idx) in enumerate(logo.split(features, labels, groups), start=1):
        model = build_model()
        model.fit(features[train_idx], labels[train_idx])
        fold_probabilities = np.asarray(model.predict_proba(features[test_idx])[:, 1], dtype=float)
        fold_predictions = (fold_probabilities >= 0.5).astype(np.int8)
        fold_metrics = _classification_metrics(labels[test_idx], fold_probabilities, fold_predictions)
        left_out_subject = str(np.unique(groups[test_idx])[0])
        folds.append({"fold": fold_index, "left_out_subject": left_out_subject, **fold_metrics})

        for sample_idx, probability, prediction in zip(test_idx, fold_probabilities, fold_predictions, strict=False):
            predictions.append(
                {
                    "fold": fold_index,
                    "subject": str(groups[sample_idx]),
                    "y_true": int(labels[sample_idx]),
                    "y_pred": int(prediction),
                    "probability_lsd": float(probability),
                }
            )

        if model_name == "logistic_regression":
            coefficient_rows.append(np.asarray(model.named_steps["classifier"].coef_[0], dtype=float))

    result: dict[str, Any] = {
        "folds": folds,
        "aggregate": _aggregate_folds(folds),
        "predictions": predictions,
    }
    if coefficient_rows:
        result["top_features"] = _top_logistic_features(coefficient_rows, feature_names)
    return result


def _evaluate_multitask_model(
    *,
    model_name: str,
    build_classifier: Any,
    build_regressor: Any,
    features: np.ndarray,
    labels: np.ndarray,
    eigen_targets: np.ndarray,
    groups: np.ndarray,
    feature_names: list[str],
    target_names: list[str],
) -> dict[str, Any]:
    logo = LeaveOneGroupOut()
    folds: list[dict[str, float | int | str]] = []
    classification_predictions: list[dict[str, float | int | str]] = []
    eigen_prediction_rows: list[dict[str, Any]] = []
    classification_rows: list[np.ndarray] = []
    regression_rows: list[np.ndarray] = []

    for fold_index, (train_idx, test_idx) in enumerate(logo.split(features, labels, groups), start=1):
        classifier = build_classifier()
        regressor = build_regressor()
        classifier.fit(features[train_idx], labels[train_idx])
        regressor.fit(features[train_idx], eigen_targets[train_idx])

        class_probabilities = np.asarray(classifier.predict_proba(features[test_idx])[:, 1], dtype=float)
        class_predictions = (class_probabilities >= 0.5).astype(np.int8)
        fold_eigen_predictions = np.asarray(regressor.predict(features[test_idx]), dtype=float)
        fold_metrics = {
            **_classification_metrics(labels[test_idx], class_probabilities, class_predictions),
            **_regression_metrics(eigen_targets[test_idx], fold_eigen_predictions),
        }
        left_out_subject = str(np.unique(groups[test_idx])[0])
        folds.append({"fold": fold_index, "left_out_subject": left_out_subject, **fold_metrics})

        for local_index, sample_idx in enumerate(test_idx):
            classification_predictions.append(
                {
                    "fold": fold_index,
                    "subject": str(groups[sample_idx]),
                    "y_true": int(labels[sample_idx]),
                    "y_pred": int(class_predictions[local_index]),
                    "probability_lsd": float(class_probabilities[local_index]),
                }
            )
            eigen_prediction_rows.append(
                {
                    "fold": fold_index,
                    "subject": str(groups[sample_idx]),
                    "true_eigenvalues": [
                        float(eigen_targets[sample_idx, target_index])
                        for target_index, _ in enumerate(target_names)
                    ],
                    "predicted_eigenvalues": [
                        float(fold_eigen_predictions[local_index, target_index])
                        for target_index, _ in enumerate(target_names)
                    ],
                }
            )

        if model_name == "ridge_multitask":
            classification_rows.append(np.asarray(classifier.named_steps["classifier"].coef_[0], dtype=float))
            estimators = regressor.named_steps["regressor"].estimators_
            regression_rows.append(np.vstack([np.asarray(estimator.coef_, dtype=float) for estimator in estimators]))

    result: dict[str, Any] = {
        "folds": folds,
        "aggregate": _aggregate_folds(folds),
        "classification_predictions": classification_predictions,
        "eigen_predictions": eigen_prediction_rows,
    }
    if classification_rows:
        result["top_classification_features"] = _top_logistic_features(classification_rows, feature_names)
    if regression_rows:
        averaged_rows = [row.mean(axis=0) for row in regression_rows]
        result["top_regression_features"] = _top_logistic_features(averaged_rows, feature_names)
    return result


def evaluate_sklearn_condition_models(
    dataset: dict[str, np.ndarray],
    module_names: tuple[str, ...] = MODULE_NAMES,
    random_state: int = 7,
) -> dict[str, Any]:
    windows = np.asarray(dataset["windows"], dtype=float)
    labels = np.asarray(dataset["condition"], dtype=np.int8)
    groups = np.asarray(dataset["subject"])
    if len(np.unique(groups)) < 2:
        raise ValueError("Subject-held-out CV requires at least two unique subjects.")

    features, feature_names = engineer_window_features(windows, module_names=module_names)

    models = {
        "logistic_regression": lambda: Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=2000,
                        random_state=random_state,
                        class_weight="balanced",
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": lambda: HistGradientBoostingClassifier(
            max_depth=3,
            learning_rate=0.05,
            max_iter=200,
            min_samples_leaf=1,
            random_state=random_state,
            early_stopping=False,
        ),
    }

    results = {
        model_name: _evaluate_single_model(
            model_name=model_name,
            build_model=builder,
            features=features,
            labels=labels,
            groups=groups,
            feature_names=feature_names,
        )
        for model_name, builder in models.items()
    }

    return {
        "dataset": {
            "sample_count": int(windows.shape[0]),
            "window_length": int(windows.shape[1]),
            "module_count": int(windows.shape[2]),
            "subject_count": int(len(np.unique(groups))),
            "fold_count": int(len(np.unique(groups))),
            "positive_rate": float(np.mean(labels)),
        },
        "feature_names": feature_names,
        "models": results,
    }


def evaluate_sklearn_multitask_models(
    dataset: dict[str, np.ndarray],
    module_names: tuple[str, ...] = MODULE_NAMES,
    random_state: int = 7,
) -> dict[str, Any]:
    windows = np.asarray(dataset["windows"], dtype=float)
    labels = np.asarray(dataset["condition"], dtype=np.int8)
    groups = np.asarray(dataset["subject"])
    if len(np.unique(groups)) < 2:
        raise ValueError("Subject-held-out CV requires at least two unique subjects.")

    features, feature_names = engineer_window_features(
        windows,
        module_names=module_names,
        include_fc_eigenvalues=False,
    )
    eigen_targets, target_names = build_window_eigenvalue_targets(windows)

    models = {
        "ridge_multitask": {
            "classifier": lambda: Pipeline(
                steps=[
                    ("scaler", StandardScaler()),
                    (
                        "classifier",
                        LogisticRegression(
                            max_iter=2000,
                            random_state=random_state,
                            class_weight="balanced",
                        ),
                    ),
                ]
            ),
            "regressor": lambda: Pipeline(
                steps=[
                    ("scaler", StandardScaler()),
                    ("regressor", MultiOutputRegressor(Ridge(alpha=1.0))),
                ]
            ),
        },
        "hist_gradient_multitask": {
            "classifier": lambda: HistGradientBoostingClassifier(
                max_depth=3,
                learning_rate=0.05,
                max_iter=200,
                min_samples_leaf=1,
                random_state=random_state,
                early_stopping=False,
            ),
            "regressor": lambda: MultiOutputRegressor(
                HistGradientBoostingRegressor(
                    max_depth=3,
                    learning_rate=0.05,
                    max_iter=200,
                    min_samples_leaf=1,
                    random_state=random_state,
                    early_stopping=False,
                )
            ),
        },
    }

    results = {
        model_name: _evaluate_multitask_model(
            model_name=model_name,
            build_classifier=model_builders["classifier"],
            build_regressor=model_builders["regressor"],
            features=features,
            labels=labels,
            eigen_targets=eigen_targets,
            groups=groups,
            feature_names=feature_names,
            target_names=target_names,
        )
        for model_name, model_builders in models.items()
    }

    return {
        "dataset": {
            "sample_count": int(windows.shape[0]),
            "window_length": int(windows.shape[1]),
            "module_count": int(windows.shape[2]),
            "subject_count": int(len(np.unique(groups))),
            "fold_count": int(len(np.unique(groups))),
            "positive_rate": float(np.mean(labels)),
        },
        "feature_names": feature_names,
        "target_names": target_names,
        "models": results,
    }
