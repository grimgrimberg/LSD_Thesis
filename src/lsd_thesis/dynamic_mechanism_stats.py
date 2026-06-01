from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

from lsd_thesis.metrics_literature import state_occupancy_entropy, transition_entropy, transition_rate

MECHANISM_METRIC_BOOTSTRAP_ITERATIONS = 1024
MECHANISM_METRIC_BOOTSTRAP_ALPHA = 0.05
MECHANISM_METRIC_BOOTSTRAP_SEED = 20260520


def finite_array(values: Any) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[0] < 3 or array.shape[1] < 1:
        raise ValueError("Module time series must be shaped as [time, module] with at least three time points.")
    finite = np.where(np.isfinite(array), array, np.nan)
    column_means = np.nanmean(finite, axis=0)
    column_means = np.where(np.isfinite(column_means), column_means, 0.0)
    row_indices, column_indices = np.where(~np.isfinite(array))
    if len(row_indices):
        array = array.copy()
        array[row_indices, column_indices] = column_means[column_indices]
    return array


def _state_scores_from_reference(reference: np.ndarray, time_series: np.ndarray, score_mode: str = "pca") -> tuple[np.ndarray, np.ndarray]:
    reference_array = np.asarray(reference, dtype=float)
    target_array = np.asarray(time_series, dtype=float)
    if score_mode == "global_mean":
        return np.mean(reference_array, axis=1), np.mean(target_array, axis=1)
    if score_mode == "trajectory_norm":
        center = np.mean(reference_array, axis=0, keepdims=True)
        return np.linalg.norm(reference_array - center, axis=1), np.linalg.norm(target_array - center, axis=1)

    centered_reference = reference - np.mean(reference, axis=0, keepdims=True)
    if np.linalg.norm(centered_reference) <= 1e-12:
        return np.zeros(len(reference_array), dtype=float), np.zeros(len(target_array), dtype=float)
    _, _, vh = np.linalg.svd(centered_reference, full_matrices=False)
    component = vh[0]
    return centered_reference @ component, (target_array - np.mean(reference_array, axis=0, keepdims=True)) @ component


def state_labels_from_reference(
    reference: np.ndarray,
    time_series: np.ndarray,
    *,
    state_bins: int = 4,
    score_mode: str = "pca",
) -> np.ndarray:
    if state_bins < 2:
        raise ValueError("state_bins must be at least 2.")
    scores_reference, scores = _state_scores_from_reference(reference, time_series, score_mode=score_mode)
    if np.max(scores_reference) - np.min(scores_reference) <= 1e-12:
        return np.zeros(len(time_series), dtype=int)
    thresholds = np.quantile(scores_reference, [index / state_bins for index in range(1, state_bins)])
    return np.asarray(np.digitize(scores, thresholds, right=False), dtype=int)


def _mean_dwell_time(labels: np.ndarray) -> float:
    sequence = np.asarray(labels, dtype=int)
    if len(sequence) == 0:
        return 0.0
    change_points = np.where(np.diff(sequence) != 0)[0] + 1
    boundaries = np.concatenate(([0], change_points, [len(sequence)]))
    return float(np.mean(np.diff(boundaries)))


def transition_metrics(labels: np.ndarray) -> dict[str, float]:
    return {
        "state_occupancy_entropy": state_occupancy_entropy(labels),
        "transition_entropy": transition_entropy(labels),
        "transition_rate": transition_rate(labels),
        "mean_dwell_time": _mean_dwell_time(labels),
        "barrier_reduction_proxy": -_mean_dwell_time(labels),
    }


def mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    array = np.asarray(values, dtype=float)
    std = float(np.std(array, ddof=1)) if len(array) > 1 else 0.0
    return float(np.mean(array)), std


def bootstrap_ci(
    values: list[float],
    *,
    seed: int = MECHANISM_METRIC_BOOTSTRAP_SEED,
    n_bootstrap: int = MECHANISM_METRIC_BOOTSTRAP_ITERATIONS,
    alpha: float = MECHANISM_METRIC_BOOTSTRAP_ALPHA,
) -> dict[str, float | int]:
    data = np.asarray([float(value) for value in values if np.isfinite(float(value))], dtype=float)
    if len(data) == 0:
        return {"n": 0, "mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n_bootstrap": int(n_bootstrap)}
    if len(data) == 1 or n_bootstrap <= 0:
        mean_value = round(float(np.mean(data)), 12)
        return {
            "n": int(len(data)),
            "mean": mean_value,
            "ci_low": mean_value,
            "ci_high": mean_value,
            "n_bootstrap": int(max(n_bootstrap, 0)),
        }
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(data), size=(int(n_bootstrap), len(data)))
    boot_means = np.mean(data[indices], axis=1)
    ci_low, ci_high = np.quantile(boot_means, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {
        "n": int(len(data)),
        "mean": round(float(np.mean(data)), 12),
        "ci_low": round(float(ci_low), 12),
        "ci_high": round(float(ci_high), 12),
        "n_bootstrap": int(n_bootstrap),
    }


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    if not p_values:
        return []
    p = np.asarray([float(value) for value in p_values], dtype=float)
    finite = np.isfinite(p)
    if not np.any(finite):
        return [1.0] * len(p_values)
    ranked = np.argsort(p[finite])
    finite_values = p[finite]
    sorted_finite = finite_values[ranked]
    m = float(len(sorted_finite))
    ranked_q = np.minimum.accumulate((m / np.arange(len(sorted_finite), 0, -1)) * sorted_finite[::-1])[::-1]
    ranked_q = np.asarray(np.minimum(ranked_q, 1.0), dtype=float)
    q = np.ones_like(p, dtype=float)
    finite_q = np.empty_like(finite_values, dtype=float)
    finite_q[ranked] = ranked_q
    q[finite] = finite_q
    q[~finite] = 1.0
    return [float(value) for value in q]


def _effect_size(mean_value: float, std_value: float) -> float:
    if abs(std_value) <= 1e-12:
        return 0.0 if abs(mean_value) <= 1e-12 else float(np.sign(mean_value))
    return float(mean_value / std_value)


def _sign_flip_p_value(values: list[float], expected_sign: int) -> float:
    signed = [expected_sign * float(value) for value in values if abs(float(value)) > 1e-12]
    n = len(signed)
    if n == 0:
        return 1.0
    successes = sum(value > 0.0 for value in signed)
    numerator = sum(math.comb(n, k) for k in range(successes, n + 1))
    return float(min(1.0, numerator / (2**n)))


def _sign_consistency(values: list[float], expected_sign: int) -> float:
    signed = [expected_sign * float(value) for value in values if abs(float(value)) > 1e-12]
    if not signed:
        return 0.0
    return float(np.mean(np.asarray(signed, dtype=float) > 0.0))


def aggregate_metric_deltas(
    metric_deltas: dict[str, list[float]],
    expected_direction: dict[str, str],
    expected_sign: dict[str, int],
    *,
    bootstrap_seed: int = MECHANISM_METRIC_BOOTSTRAP_SEED,
) -> list[dict[str, Any]]:
    aggregate_rows: list[dict[str, Any]] = []
    for metric_index, (metric, values) in enumerate(metric_deltas.items()):
        sign = expected_sign.get(metric, 1)
        mean_delta, std_delta = mean_std(values)
        effect = _effect_size(mean_delta, std_delta)
        ci = bootstrap_ci(values, seed=bootstrap_seed + metric_index)
        row = {
            "metric": metric,
            "mean_delta": mean_delta,
            "std_delta": std_delta,
            "effect_size": effect,
            "signed_effect_size": float(sign * effect),
            "expected_sign": sign,
            "sign_consistency": _sign_consistency(values, sign),
            "sign_flip_p_value": _sign_flip_p_value(values, sign),
            "expected_direction": expected_direction.get(metric, ""),
            "n_pairs": ci["n"],
            "n_bootstrap": ci["n_bootstrap"],
            "ci_low": ci["ci_low"],
            "ci_high": ci["ci_high"],
        }
        aggregate_rows.append(row)
    fdr_values = benjamini_hochberg([float(row["sign_flip_p_value"]) for row in aggregate_rows])
    for row, q_value in zip(aggregate_rows, fdr_values, strict=True):
        row["sign_flip_q_value"] = q_value
        row["significant_after_fdr_0_05"] = q_value < 0.05
        row["significant_after_fdr_0.05"] = q_value < 0.05
    return aggregate_rows


def collect_paired_metric_rows(
    pairs: Sequence[Any],
    metric_names: Sequence[str],
    metric_builder: Callable[[Any], tuple[dict[str, float], dict[str, float]]],
) -> tuple[list[dict[str, Any]], dict[str, list[float]]]:
    metric_deltas: dict[str, list[float]] = {metric: [] for metric in metric_names}
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        placebo_metrics, lsd_metrics = metric_builder(pair)
        deltas = {metric: float(lsd_metrics[metric] - placebo_metrics[metric]) for metric in metric_names}
        for metric, value in deltas.items():
            metric_deltas[metric].append(value)
        rows.append(
            {
                "subject": pair.subject,
                "run": pair.run,
                "placebo": placebo_metrics,
                "lsd": lsd_metrics,
                "delta": deltas,
            }
        )
    return rows, metric_deltas


def run_metric_deltas(
    pair_rows: list[dict[str, Any]],
    metrics: list[str],
    expected_direction: dict[str, str],
    expected_sign: dict[str, int],
) -> list[dict[str, Any]]:
    by_run: dict[str, dict[str, list[float]]] = {}
    for row in pair_rows:
        run = str(row.get("run", "unknown"))
        by_run.setdefault(run, {metric: [] for metric in metrics})
        deltas = row.get("delta", {})
        for metric in metrics:
            by_run[run][metric].append(float(deltas.get(metric, 0.0)))

    output: list[dict[str, Any]] = []
    for run, deltas in sorted(by_run.items()):
        for row in aggregate_metric_deltas(deltas, expected_direction, expected_sign):
            output.append({"run": run, **row})
    return output


def zscore_pair(placebo: np.ndarray, lsd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    stacked = np.vstack([placebo, lsd])
    mean = np.mean(stacked, axis=0, keepdims=True)
    std = np.std(stacked, axis=0, keepdims=True)
    std = np.where(std > 1e-8, std, 1.0)
    return (placebo - mean) / std, (lsd - mean) / std


def mean_step_distance(time_series: np.ndarray) -> float:
    if len(time_series) < 2:
        return 0.0
    return float(np.mean(np.linalg.norm(np.diff(time_series, axis=0), axis=1)))
