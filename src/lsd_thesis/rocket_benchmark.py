from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from lsd_thesis.subject_split import load_subject_split_file, validate_cv5_subject_split_manifest

ROCKET_BENCHMARK_SCHEMA_VERSION = "rocket_condition_benchmark.v1"


@dataclass(frozen=True)
class RocketKernel:
    weights: np.ndarray
    bias: float
    dilation: int


@dataclass(frozen=True)
class FoldIndices:
    fold: int
    train_idx: np.ndarray
    test_idx: np.ndarray
    train_subjects: tuple[str, ...]
    held_out_subjects: tuple[str, ...]
    split_id: str


def _classification_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, float]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
    }
    if len(np.unique(y_true)) < 2:
        metrics["roc_auc"] = float("nan")
    else:
        metrics["roc_auc"] = float(roc_auc_score(y_true, probabilities))
    return metrics


def _aggregate_folds(folds: list[dict[str, Any]]) -> dict[str, float]:
    aggregate: dict[str, float] = {}
    for metric_name in ("accuracy", "balanced_accuracy", "roc_auc", "brier_score"):
        values = np.asarray([float(fold[metric_name]) for fold in folds], dtype=float)
        aggregate[f"{metric_name}_mean"] = float(np.nanmean(values))
        aggregate[f"{metric_name}_std"] = float(np.nanstd(values))
    return aggregate


def _calibration_bins(y_true: np.ndarray, probabilities: np.ndarray, *, n_bins: int = 5) -> list[dict[str, float | int]]:
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows: list[dict[str, float | int]] = []
    for index in range(n_bins):
        lower = float(edges[index])
        upper = float(edges[index + 1])
        upper_mask = probabilities <= upper if index == n_bins - 1 else probabilities < upper
        mask = (probabilities >= lower) & upper_mask
        count = int(np.sum(mask))
        row: dict[str, float | int] = {"bin": index + 1, "lower": lower, "upper": upper, "count": count}
        if count:
            row["mean_probability"] = float(np.mean(probabilities[mask]))
            row["empirical_lsd_rate"] = float(np.mean(y_true[mask]))
        rows.append(row)
    return rows


def _posthoc_prediction_permutation_null(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    predictions: np.ndarray,
    *,
    observed_balanced_accuracy: float,
    n_permutations: int,
    random_state: int,
) -> dict[str, Any]:
    if n_permutations <= 0:
        return {
            "status": "not_run",
            "n_permutations": 0,
            "null_type": "posthoc_prediction_label_permutation_not_refit",
            "claim_gate": "blocked_until_permutation_null_is_run",
        }
    rng = np.random.default_rng(random_state + 10_000)
    rows: list[dict[str, float | int]] = []
    for permutation_index in range(1, n_permutations + 1):
        shuffled = rng.permutation(y_true)
        rows.append(
            {
                "permutation": permutation_index,
                "balanced_accuracy": float(balanced_accuracy_score(shuffled, predictions)),
                "brier_score": float(brier_score_loss(shuffled, probabilities)),
            }
        )
    null_values = np.asarray([float(row["balanced_accuracy"]) for row in rows], dtype=float)
    p_value = float((1 + np.sum(null_values >= observed_balanced_accuracy)) / (len(null_values) + 1))
    return {
        "status": "completed",
        "n_permutations": int(n_permutations),
        "null_type": "posthoc_prediction_label_permutation_not_refit",
        "observed_balanced_accuracy_mean": float(observed_balanced_accuracy),
        "null_balanced_accuracy_mean": float(np.mean(null_values)),
        "null_balanced_accuracy_std": float(np.std(null_values)),
        "balanced_accuracy_empirical_p_value": p_value,
        "claim_gate": "supporting_only_until_a_fold_refit_permutation_null_is_added",
        "rows": rows,
    }


def _metadata_vector(dataset: dict[str, np.ndarray], key: str, default: str, sample_count: int) -> np.ndarray:
    if key in dataset and len(dataset[key]) == sample_count:
        return np.asarray(dataset[key])
    return np.asarray([default] * sample_count)


def _normalise_windows(train_windows: np.ndarray, test_windows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(train_windows, axis=(0, 1), keepdims=True)
    std = np.std(train_windows, axis=(0, 1), keepdims=True)
    std = np.where(std > 1e-6, std, 1.0)
    return (train_windows - mean) / std, (test_windows - mean) / std


def make_rocket_kernels(
    *,
    window_length: int,
    module_count: int,
    n_kernels: int,
    random_state: int,
) -> list[RocketKernel]:
    if window_length < 3:
        raise ValueError("ROCKET benchmark requires windows with at least three time points.")
    if module_count < 1:
        raise ValueError("ROCKET benchmark requires at least one module/channel.")
    if n_kernels <= 0:
        raise ValueError("n_kernels must be positive.")

    rng = np.random.default_rng(random_state)
    candidate_lengths = [length for length in (7, 9, 11) if length <= window_length]
    if not candidate_lengths:
        candidate_lengths = [window_length]
    kernels: list[RocketKernel] = []
    for _ in range(n_kernels):
        length = int(rng.choice(candidate_lengths))
        max_dilation = max(1, (window_length - 1) // max(length - 1, 1))
        dilation = int(rng.integers(1, max_dilation + 1))
        weights = rng.normal(0.0, 1.0, size=(length, module_count))
        weights = weights - np.mean(weights, axis=0, keepdims=True)
        kernels.append(
            RocketKernel(
                weights=np.asarray(weights, dtype=np.float32),
                bias=float(rng.uniform(-1.0, 1.0)),
                dilation=dilation,
            )
        )
    return kernels


def _kernel_response(window: np.ndarray, kernel: RocketKernel) -> np.ndarray:
    length = kernel.weights.shape[0]
    receptive_field = (length - 1) * kernel.dilation + 1
    stop = window.shape[0] - receptive_field + 1
    values = np.empty(max(stop, 0), dtype=np.float32)
    for start in range(stop):
        indices = start + np.arange(length) * kernel.dilation
        values[start] = float(np.sum(window[indices] * kernel.weights) + kernel.bias)
    return values


def rocket_transform(windows: np.ndarray, kernels: list[RocketKernel]) -> np.ndarray:
    if windows.ndim != 3:
        raise ValueError("Windows must be shaped [sample, time, module].")
    features = np.empty((windows.shape[0], len(kernels) * 2), dtype=np.float32)
    for kernel_index, kernel in enumerate(kernels):
        length = kernel.weights.shape[0]
        receptive_field = (length - 1) * kernel.dilation + 1
        stop = windows.shape[1] - receptive_field + 1
        if stop <= 0:
            features[:, kernel_index * 2] = 0.0
            features[:, kernel_index * 2 + 1] = 0.0
            continue
        offsets = np.arange(length) * kernel.dilation
        positions = np.arange(stop)[:, None] + offsets[None, :]
        sampled = windows[:, positions, :]
        responses = np.tensordot(sampled, kernel.weights, axes=([2, 3], [0, 1])) + kernel.bias
        features[:, kernel_index * 2] = np.max(responses, axis=1)
        features[:, kernel_index * 2 + 1] = np.mean(responses > 0.0, axis=1)
    return features


def _resolve_cv5_fold_path(raw_path: str, *, manifest_path: Path, repo_root: Path | None) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    if repo_root is not None and (repo_root / path).exists():
        return (repo_root / path).resolve()
    return (manifest_path.parent / path).resolve()


def _fold_indices_from_cv5_manifest(
    *,
    manifest_path: Path,
    subjects: np.ndarray,
    repo_root: Path | None,
    allow_candidate_cv5: bool,
) -> tuple[str, list[FoldIndices], dict[str, Any]]:
    summary = validate_cv5_subject_split_manifest(manifest_path, repo_root=repo_root)
    if summary["approval_status"] != "approved" and not allow_candidate_cv5:
        raise ValueError("ROCKET CV5 benchmark requires an approved CV5 manifest unless allow_candidate_cv5=True.")

    folds: list[FoldIndices] = []
    for fold_summary in summary["fold_summaries"]:
        fold_path = _resolve_cv5_fold_path(
            str(fold_summary["file_path"]),
            manifest_path=manifest_path,
            repo_root=repo_root,
        )
        split = load_subject_split_file(fold_path)
        train_subjects = tuple(split.selection_subjects)
        held_out_subjects = tuple(split.validation_subjects)
        train_idx = np.where(np.isin(subjects, train_subjects))[0]
        test_idx = np.where(np.isin(subjects, held_out_subjects))[0]
        if len(train_idx) == 0 or len(test_idx) == 0:
            raise ValueError(f"CV5 fold {split.split_id} does not map to non-empty dataset train/test windows.")
        folds.append(
            FoldIndices(
                fold=int(fold_summary["fold_index"]),
                train_idx=train_idx,
                test_idx=test_idx,
                train_subjects=train_subjects,
                held_out_subjects=held_out_subjects,
                split_id=str(split.split_id),
            )
        )
    strategy = f"{summary['approval_status']} CV5 subject-disjoint manifest"
    return strategy, folds, summary


def _leave_one_subject_out_folds(subjects: np.ndarray, labels: np.ndarray) -> tuple[str, list[FoldIndices], dict[str, Any]]:
    logo = LeaveOneGroupOut()
    folds: list[FoldIndices] = []
    unique_subjects = tuple(str(subject) for subject in np.unique(subjects))
    for fold_index, (train_idx, test_idx) in enumerate(logo.split(np.zeros(len(labels)), labels, subjects), start=1):
        held_out_subjects = tuple(str(subject) for subject in np.unique(subjects[test_idx]))
        train_subjects = tuple(str(subject) for subject in np.unique(subjects[train_idx]))
        folds.append(
            FoldIndices(
                fold=fold_index,
                train_idx=np.asarray(train_idx, dtype=int),
                test_idx=np.asarray(test_idx, dtype=int),
                train_subjects=train_subjects,
                held_out_subjects=held_out_subjects,
                split_id=f"leave_one_subject_out_{fold_index:02d}",
            )
        )
    return (
        "LeaveOneGroupOut(subject)",
        folds,
        {
            "approval_status": "not_applicable",
            "number_of_subjects": len(unique_subjects),
            "number_of_folds": len(unique_subjects),
            "validation_coverage_summary": {"every_subject_held_out_exactly_once": True},
        },
    )


def _aggregate_predictions_by_subject_session_run(window_predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in window_predictions:
        grouped[(int(row["fold"]), str(row["subject"]), str(row["session"]), str(row["run"]))].append(row)

    aggregate_rows: list[dict[str, Any]] = []
    for (fold, subject, session, run), rows in sorted(grouped.items()):
        labels = {int(row["y_true"]) for row in rows}
        if len(labels) != 1:
            raise ValueError(f"Aggregation unit has mixed labels: fold={fold}, subject={subject}, session={session}, run={run}.")
        probability = float(np.mean([float(row["probability_lsd"]) for row in rows]))
        prediction = int(probability >= 0.5)
        y_true = labels.pop()
        aggregate_rows.append(
            {
                "fold": fold,
                "subject": subject,
                "session": session,
                "run": run,
                "window_count": len(rows),
                "y_true": y_true,
                "y_pred": prediction,
                "probability_lsd": probability,
            }
        )
    return aggregate_rows


def _fit_rocket_fold(
    *,
    windows: np.ndarray,
    labels: np.ndarray,
    fold: FoldIndices,
    kernels: list[RocketKernel],
    random_state: int,
) -> tuple[np.ndarray, np.ndarray]:
    train_windows, test_windows = _normalise_windows(windows[fold.train_idx], windows[fold.test_idx])
    train_features = rocket_transform(train_windows, kernels)
    test_features = rocket_transform(test_windows, kernels)
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=random_state + fold.fold,
                ),
            ),
        ]
    )
    model.fit(train_features, labels[fold.train_idx])
    probabilities = np.asarray(model.predict_proba(test_features)[:, 1], dtype=float)
    predictions = (probabilities >= 0.5).astype(np.int8)
    return probabilities, predictions


def evaluate_rocket_condition_model(
    dataset: dict[str, np.ndarray],
    *,
    n_kernels: int = 128,
    random_state: int = 11,
    cv5_manifest_path: str | Path | None = None,
    repo_root: str | Path | None = None,
    allow_candidate_cv5: bool = False,
    n_permutations: int = 0,
) -> dict[str, Any]:
    windows = np.asarray(dataset["windows"], dtype=np.float32)
    labels = np.asarray(dataset["condition"], dtype=np.int8)
    subjects = np.asarray(dataset["subject"], dtype="U64")
    if windows.ndim != 3:
        raise ValueError("Dataset windows must be shaped [sample, time, module].")
    if len(windows) != len(labels) or len(windows) != len(subjects):
        raise ValueError("Dataset windows, condition labels, and subjects must have the same length.")
    if len(np.unique(subjects)) < 2:
        raise ValueError("Subject-disjoint ROCKET benchmark requires at least two unique subjects.")

    sessions = _metadata_vector(dataset, "session", "unknown", len(windows))
    runs = _metadata_vector(dataset, "run", "unknown", len(windows))
    kernels = make_rocket_kernels(
        window_length=int(windows.shape[1]),
        module_count=int(windows.shape[2]),
        n_kernels=n_kernels,
        random_state=random_state,
    )
    resolved_repo_root = Path(repo_root).resolve() if repo_root is not None else None
    if cv5_manifest_path is not None:
        strategy, folds, split_summary = _fold_indices_from_cv5_manifest(
            manifest_path=Path(cv5_manifest_path).resolve(),
            subjects=subjects,
            repo_root=resolved_repo_root,
            allow_candidate_cv5=allow_candidate_cv5,
        )
    else:
        strategy, folds, split_summary = _leave_one_subject_out_folds(subjects, labels)

    window_predictions: list[dict[str, Any]] = []
    window_folds: list[dict[str, Any]] = []
    for fold in folds:
        probabilities, predictions = _fit_rocket_fold(
            windows=windows,
            labels=labels,
            fold=fold,
            kernels=kernels,
            random_state=random_state,
        )
        window_metrics = _classification_metrics(labels[fold.test_idx], probabilities, predictions)
        window_folds.append(
            {
                "fold": fold.fold,
                "split_id": fold.split_id,
                "held_out_subjects": list(fold.held_out_subjects),
                "train_subject_count": len(fold.train_subjects),
                "held_out_subject_count": len(fold.held_out_subjects),
                "window_count": int(len(fold.test_idx)),
                **window_metrics,
            }
        )
        for sample_idx, probability, prediction in zip(fold.test_idx, probabilities, predictions, strict=False):
            window_predictions.append(
                {
                    "fold": fold.fold,
                    "split_id": fold.split_id,
                    "subject": str(subjects[sample_idx]),
                    "session": str(sessions[sample_idx]),
                    "run": str(runs[sample_idx]),
                    "y_true": int(labels[sample_idx]),
                    "y_pred": int(prediction),
                    "probability_lsd": float(probability),
                }
            )

    subject_session_run_predictions = _aggregate_predictions_by_subject_session_run(window_predictions)
    folds_primary: list[dict[str, Any]] = []
    for fold in folds:
        rows = [row for row in subject_session_run_predictions if int(row["fold"]) == fold.fold]
        y_true = np.asarray([int(row["y_true"]) for row in rows], dtype=np.int8)
        probabilities = np.asarray([float(row["probability_lsd"]) for row in rows], dtype=float)
        predictions = np.asarray([int(row["y_pred"]) for row in rows], dtype=np.int8)
        metrics = _classification_metrics(y_true, probabilities, predictions)
        folds_primary.append(
            {
                "fold": fold.fold,
                "split_id": fold.split_id,
                "held_out_subjects": list(fold.held_out_subjects),
                "train_subject_count": len(fold.train_subjects),
                "held_out_subject_count": len(fold.held_out_subjects),
                "aggregation_unit_count": len(rows),
                **metrics,
            }
        )

    primary_y_true = np.asarray([int(row["y_true"]) for row in subject_session_run_predictions], dtype=np.int8)
    primary_probabilities = np.asarray(
        [float(row["probability_lsd"]) for row in subject_session_run_predictions], dtype=float
    )
    primary_predictions = np.asarray([int(row["y_pred"]) for row in subject_session_run_predictions], dtype=np.int8)
    aggregate = _aggregate_folds(folds_primary)

    return {
        "schema_version": ROCKET_BENCHMARK_SCHEMA_VERSION,
        "task": "lsd_vs_placebo_condition_classification",
        "model": "rocket_random_convolution_features_logistic_regression",
        "cv_strategy": strategy,
        "split_summary": split_summary,
        "primary_evaluation_unit": "subject_session_run_aggregated_windows",
        "primary_metric_source": "subject/session/run mean probability after subject-disjoint fold prediction",
        "window_random_reporting": False,
        "leakage_controls": [
            "train/test splits are grouped by subject",
            "normalization is fit only on training windows inside each fold",
            "ROCKET kernels are generated from shape and seed only, not from labels or held-out values",
            "reported primary metrics aggregate window probabilities to subject/session/run units",
        ],
        "dataset": {
            "sample_count": int(windows.shape[0]),
            "window_length": int(windows.shape[1]),
            "module_count": int(windows.shape[2]),
            "subject_count": int(len(np.unique(subjects))),
            "fold_count": len(folds),
            "positive_rate": float(np.mean(labels)),
        },
        "rocket": {
            "n_kernels": int(n_kernels),
            "feature_count": int(2 * n_kernels),
            "features_per_kernel": ["max", "proportion_positive_values"],
            "random_state": int(random_state),
        },
        "folds": folds_primary,
        "aggregate": aggregate,
        "calibration": {
            "brier_score": float(brier_score_loss(primary_y_true, primary_probabilities)),
            "bins": _calibration_bins(primary_y_true, primary_probabilities),
            "claim_gate": "Calibration is diagnostic and must be interpreted with small-n uncertainty.",
        },
        "permutation_null": _posthoc_prediction_permutation_null(
            primary_y_true,
            primary_probabilities,
            primary_predictions,
            observed_balanced_accuracy=aggregate["balanced_accuracy_mean"],
            n_permutations=n_permutations,
            random_state=random_state,
        ),
        "subject_session_run_predictions": subject_session_run_predictions,
        "window_folds_secondary": window_folds,
        "window_aggregate_secondary": _aggregate_folds(window_folds),
        "window_predictions_secondary": window_predictions,
        "claim_guardrail": (
            "ROCKET results are internal subject-disjoint proxy classification diagnostics. "
            "They are not receptor-level, clinical, subjective-experience, or external-validity evidence."
        ),
    }


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.floating | np.integer):
        return value.item()
    return value


def write_rocket_outputs(summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "comparison_summary.json").write_text(json.dumps(_plain(summary), indent=2), encoding="utf-8")
    _write_table(output_dir / "subject_session_run_predictions.csv", summary["subject_session_run_predictions"])
    _write_table(output_dir / "window_predictions_secondary.csv", summary["window_predictions_secondary"])
    _write_report(output_dir / "benchmark_report.md", summary)


def _write_table(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    aggregate = summary["aggregate"]
    lines = [
        "# ROCKET Condition Benchmark",
        "",
        f"- CV: `{summary['cv_strategy']}`",
        f"- Primary unit: `{summary['primary_evaluation_unit']}`",
        f"- Window-random reporting: `{str(summary['window_random_reporting']).lower()}`",
        f"- Kernels: {summary['rocket']['n_kernels']} ({summary['rocket']['feature_count']} features)",
        f"- Subjects: {summary['dataset']['subject_count']}",
        f"- Windows: {summary['dataset']['sample_count']}",
        "",
        "## Primary Subject/Run Aggregated Metrics",
        "",
        f"- Accuracy: {aggregate['accuracy_mean']:.3f} +/- {aggregate['accuracy_std']:.3f}",
        f"- Balanced accuracy: {aggregate['balanced_accuracy_mean']:.3f} +/- {aggregate['balanced_accuracy_std']:.3f}",
        f"- ROC AUC: {aggregate['roc_auc_mean']:.3f} +/- {aggregate['roc_auc_std']:.3f}",
        f"- Brier score: {aggregate['brier_score_mean']:.3f} +/- {aggregate['brier_score_std']:.3f}",
        "",
        "## Calibration and Null Gates",
        "",
        f"- Subject/run Brier score: {summary['calibration']['brier_score']:.3f}",
        f"- Permutation null status: `{summary['permutation_null']['status']}`",
        "",
        "## Fold Metrics",
        "",
        "| Fold | Held-out subjects | Aggregation units | Balanced accuracy | ROC AUC |",
        "| ---: | --- | ---: | ---: | ---: |",
    ]
    if summary["permutation_null"].get("status") == "completed":
        null = summary["permutation_null"]
        lines.insert(
            -5,
            f"- Post-hoc label-permutation p-value: {null['balanced_accuracy_empirical_p_value']:.3f} "
            f"over {null['n_permutations']} permutations",
        )
    for fold in summary["folds"]:
        held_out = ", ".join(str(subject) for subject in fold["held_out_subjects"])
        lines.append(
            f"| {fold['fold']} | {held_out} | {fold['aggregation_unit_count']} | "
            f"{fold['balanced_accuracy']:.3f} | {fold['roc_auc']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Primary reporting aggregates window probabilities to subject/session/run units.",
            "- Raw window-level metrics are secondary diagnostics only.",
            "- No random window-level train/test split is used.",
            f"- {summary['claim_guardrail']}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
