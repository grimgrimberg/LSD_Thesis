from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

PRIMARY_LITERATURE_METRIC_WEIGHTS: dict[str, float] = {
    "unimodal_transmodal_fc": 2.0,
    "hierarchy_differentiation": 1.8,
    "gradient_flattening_delta": 1.8,
    "visual_global_connectivity": 1.6,
    "sensory_somatomotor_global_connectivity": 1.5,
    "transition_entropy": 1.4,
    "state_occupancy_entropy": 1.4,
    "thalamus_to_sensory_fc": 1.2,
    "striatum_to_sensory_fc": 1.1,
}

DIAGNOSTIC_LITERATURE_METRIC_WEIGHTS: dict[str, float] = {
    "global_mean_fc": 0.4,
    "dynamic_fc_variance": 0.8,
    "transition_rate": 0.8,
    "thalamus_to_transmodal_fc": 0.8,
    "within_network_stability": 0.3,
    "cross_network_communication": 0.3,
    "entropy_diversity": 0.3,
    "effective_barrier_proxy": 0.2,
    "metastability_proxy": 0.2,
}

DEFAULT_LITERATURE_METRIC_WEIGHTS: dict[str, float] = {
    **DIAGNOSTIC_LITERATURE_METRIC_WEIGHTS,
    **PRIMARY_LITERATURE_METRIC_WEIGHTS,
}


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(number):
        return default
    return number


def _metric_sign(value: float, tolerance: float = 1e-9) -> int:
    if value > tolerance:
        return 1
    if value < -tolerance:
        return -1
    return 0


def _mean_seed_delta(seed_metric_deltas: Sequence[Mapping[str, float]]) -> dict[str, float]:
    metric_names = sorted(set().union(*(row.keys() for row in seed_metric_deltas))) if seed_metric_deltas else []
    output: dict[str, float] = {}
    for metric_name in metric_names:
        values = [_finite_float(row.get(metric_name)) for row in seed_metric_deltas if metric_name in row]
        if values:
            output[metric_name] = float(np.mean(values))
    return output


def _seed_variance(seed_metric_deltas: Sequence[Mapping[str, float]], metric_names: Sequence[str]) -> float:
    penalties: list[float] = []
    for metric_name in metric_names:
        values = [_finite_float(row.get(metric_name)) for row in seed_metric_deltas if metric_name in row]
        if len(values) > 1:
            penalties.append(float(np.std(values, ddof=1)))
    return float(np.mean(penalties)) if penalties else 0.0


def literature_weighted_lsd_objective(
    *,
    empirical_delta: Mapping[str, float],
    model_delta: Mapping[str, float] | None = None,
    seed_metric_deltas: Sequence[Mapping[str, float]] | None = None,
    empirical_uncertainty: Mapping[str, float] | None = None,
    metric_weights: Mapping[str, float] | None = None,
    lambda_sign: float = 1.0,
    lambda_overshoot: float = 0.5,
    lambda_seed: float = 0.25,
    lambda_sparse: float = 0.0,
    active_parameter_count: int = 0,
) -> dict[str, Any]:
    """Score simulated LSD-minus-placebo deltas against empirical proxy deltas.

    The returned loss is a transparent surrogate fitting objective. It is
    sign-aware and uncertainty-aware, but it is not a pharmacological likelihood.
    """
    resolved_model_delta = dict(model_delta or {})
    if seed_metric_deltas:
        resolved_model_delta = _mean_seed_delta(seed_metric_deltas)
    weights = {**DEFAULT_LITERATURE_METRIC_WEIGHTS, **dict(metric_weights or {})}
    uncertainty = dict(empirical_uncertainty or {})

    metric_rows: list[dict[str, float | str | bool]] = []
    weighted_errors: list[float] = []
    sign_mismatches = 0
    overshoot_values: list[float] = []

    for metric_name in sorted(empirical_delta):
        if metric_name not in resolved_model_delta:
            continue
        empirical = _finite_float(empirical_delta[metric_name])
        modeled = _finite_float(resolved_model_delta[metric_name])
        scale = max(abs(empirical), _finite_float(uncertainty.get(metric_name)), 1e-3)
        normalized_error = (modeled - empirical) / scale
        weight = _finite_float(weights.get(metric_name, 1.0), default=1.0)
        weighted_error = weight * normalized_error**2
        empirical_sign = _metric_sign(empirical)
        modeled_sign = _metric_sign(modeled)
        sign_mismatch = empirical_sign != 0 and modeled_sign != 0 and empirical_sign != modeled_sign
        if sign_mismatch:
            sign_mismatches += 1
        overshoot = 0.0
        if empirical_sign != 0 and modeled_sign == empirical_sign and abs(modeled) > abs(empirical):
            overshoot = ((abs(modeled) - abs(empirical)) / scale) ** 2
            overshoot_values.append(overshoot)
        metric_rows.append(
            {
                "metric": metric_name,
                "empirical_delta": empirical,
                "model_delta": modeled,
                "weight": weight,
                "normalized_error": normalized_error,
                "weighted_error": weighted_error,
                "sign_match": not sign_mismatch,
                "overshoot": overshoot,
            }
        )
        weighted_errors.append(weighted_error)

    metric_names = [str(row["metric"]) for row in metric_rows]
    weighted_error_loss = float(np.mean(weighted_errors)) if weighted_errors else 0.0
    sign_penalty = float(sign_mismatches / max(len(metric_rows), 1))
    overshoot_penalty = float(np.mean(overshoot_values)) if overshoot_values else 0.0
    seed_penalty = _seed_variance(seed_metric_deltas or (), metric_names)
    sparsity_penalty = float(max(active_parameter_count, 0))
    loss = (
        weighted_error_loss
        + lambda_sign * sign_penalty
        + lambda_overshoot * overshoot_penalty
        + lambda_seed * seed_penalty
        + lambda_sparse * sparsity_penalty
    )

    return {
        "loss": float(loss),
        "weighted_error": weighted_error_loss,
        "sign_mismatch_penalty": sign_penalty,
        "overshoot_penalty": overshoot_penalty,
        "seed_variance_penalty": seed_penalty,
        "sparsity_penalty": sparsity_penalty,
        "metric_count": len(metric_rows),
        "metrics": metric_rows,
    }
