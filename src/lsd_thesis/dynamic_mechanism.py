from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.dynamic_mechanism_priors import (
    CONTROL_WEIGHT_FLOOR,
)
from lsd_thesis.dynamic_mechanism_priors import (
    module_masks as _module_masks,
)
from lsd_thesis.dynamic_mechanism_priors import (
    module_prior_vectors as _module_prior_vectors,
)
from lsd_thesis.dynamic_mechanism_priors import (
    normalise_control_weights as _normalise_control_weights,
)
from lsd_thesis.dynamic_mechanism_stats import (
    MECHANISM_METRIC_BOOTSTRAP_ALPHA,
    MECHANISM_METRIC_BOOTSTRAP_ITERATIONS,
    MECHANISM_METRIC_BOOTSTRAP_SEED,
)
from lsd_thesis.dynamic_mechanism_stats import (
    aggregate_metric_deltas as _aggregate_metric_deltas,
)
from lsd_thesis.dynamic_mechanism_stats import (
    collect_paired_metric_rows as _collect_paired_metric_rows,
)
from lsd_thesis.dynamic_mechanism_stats import (
    finite_array as _finite_array,
)
from lsd_thesis.dynamic_mechanism_stats import (
    mean_std as _mean_std,
)
from lsd_thesis.dynamic_mechanism_stats import (
    mean_step_distance as _mean_step_distance,
)
from lsd_thesis.dynamic_mechanism_stats import (
    run_metric_deltas as _run_metric_deltas,
)
from lsd_thesis.dynamic_mechanism_stats import (
    state_labels_from_reference as _state_labels_from_reference,
)
from lsd_thesis.dynamic_mechanism_stats import (
    transition_metrics as _transition_metrics,
)
from lsd_thesis.dynamic_mechanism_stats import (
    zscore_pair as _zscore_pair,
)
from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics_literature import (
    dynamic_fc_variance,
    safe_corrcoef,
    upper_triangle_vector,
)

PLACEBO_SESSION = "ses-PLCB"
LSD_SESSION = "ses-LSD"
SCHEMA_VERSION = 3
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MACRO_GRAPH_PATH = REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml"
CONTROL_HORIZON = 8
CONTROL_NULL_COUNT = 128


@dataclass(frozen=True)
class EmpiricalPair:
    subject: str
    run: str
    modules: tuple[str, ...]
    placebo: np.ndarray
    lsd: np.ndarray


@dataclass(frozen=True)
class ControlEnergySolver:
    dynamics_horizon: np.ndarray
    gramian_inverse: np.ndarray


def _default_modules(width: int) -> tuple[str, ...]:
    canonical = (
        "visual",
        "auditory",
        "salience",
        "default_mode",
        "executive_frontoparietal",
        "limbic_affective",
        "thalamic_gateway",
        "sensorimotor",
    )
    if width == len(canonical):
        return canonical
    return tuple(f"module_{index + 1}" for index in range(width))


def load_empirical_pairs(viewer_root: Path) -> list[EmpiricalPair]:
    subject_views_dir = viewer_root / "subject_views"
    if not subject_views_dir.exists():
        return []

    modules: tuple[str, ...] | None = None
    group_overview_path = viewer_root / "group_overview.json"
    if group_overview_path.exists():
        group_overview = json.loads(group_overview_path.read_text(encoding="utf-8"))
        module_names = group_overview.get("module_names")
        if isinstance(module_names, list) and all(isinstance(name, str) for name in module_names):
            modules = tuple(module_names)

    pairs: list[EmpiricalPair] = []
    for detail_path in sorted(subject_views_dir.glob("*.json")):
        detail = json.loads(detail_path.read_text(encoding="utf-8"))
        conditions = detail.get("conditions", {})
        if PLACEBO_SESSION not in conditions or LSD_SESSION not in conditions:
            continue
        placebo = _finite_array(conditions[PLACEBO_SESSION].get("module_time_series"))
        lsd = _finite_array(conditions[LSD_SESSION].get("module_time_series"))
        if placebo.shape != lsd.shape:
            continue
        pair_modules = modules or _default_modules(placebo.shape[1])
        if len(pair_modules) != placebo.shape[1]:
            pair_modules = _default_modules(placebo.shape[1])
        pairs.append(
            EmpiricalPair(
                subject=str(detail.get("subject") or detail_path.stem.rsplit("_", 1)[0]),
                run=str(detail.get("run") or detail_path.stem.rsplit("_", 1)[-1]),
                modules=pair_modules,
                placebo=placebo,
                lsd=lsd,
            )
        )
    return pairs


def _safe_vector_correlation(first: np.ndarray, second: np.ndarray) -> float:
    left = np.asarray(first, dtype=float)
    right = np.asarray(second, dtype=float)
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    if np.std(left) <= 1e-12 or np.std(right) <= 1e-12:
        return 0.0
    value = float(np.corrcoef(left, right)[0, 1])
    return value if math.isfinite(value) else 0.0


def summarize_transition_proxy(pairs: list[EmpiricalPair]) -> dict[str, Any]:
    metric_names = [
        "state_occupancy_entropy",
        "transition_entropy",
        "transition_rate",
        "mean_dwell_time",
        "barrier_reduction_proxy",
        "transition_step_distance_proxy",
    ]

    def transition_metrics_for_pair(pair: EmpiricalPair) -> tuple[dict[str, float], dict[str, float]]:
        reference = np.vstack([pair.placebo, pair.lsd])
        placebo_labels = _state_labels_from_reference(reference, pair.placebo)
        lsd_labels = _state_labels_from_reference(reference, pair.lsd)
        placebo_metrics = _transition_metrics(placebo_labels)
        lsd_metrics = _transition_metrics(lsd_labels)
        placebo_normalized, lsd_normalized = _zscore_pair(pair.placebo, pair.lsd)
        placebo_metrics["transition_step_distance_proxy"] = _mean_step_distance(placebo_normalized)
        lsd_metrics["transition_step_distance_proxy"] = _mean_step_distance(lsd_normalized)
        return placebo_metrics, lsd_metrics

    rows, metric_deltas = _collect_paired_metric_rows(pairs, metric_names, transition_metrics_for_pair)

    expected_direction = {
        "state_occupancy_entropy": "positive means broader state occupancy under LSD",
        "transition_entropy": "positive means more diverse transitions under LSD",
        "transition_rate": "positive means more frequent state switching under LSD",
        "mean_dwell_time": "negative means shorter dwell times under LSD",
        "barrier_reduction_proxy": "positive means shorter dwell times under LSD",
        "transition_step_distance_proxy": "positive means larger one-step macro-state movement under LSD",
    }
    expected_sign = {
        "state_occupancy_entropy": 1,
        "transition_entropy": 1,
        "transition_rate": 1,
        "mean_dwell_time": -1,
        "barrier_reduction_proxy": 1,
        "transition_step_distance_proxy": 1,
    }
    aggregate_rows = _aggregate_metric_deltas(
        metric_deltas,
        expected_direction,
        expected_sign,
        bootstrap_seed=MECHANISM_METRIC_BOOTSTRAP_SEED + 101,
    )

    support_components = [
        row["signed_effect_size"]
        for row in aggregate_rows
        if row["metric"]
        in {"transition_entropy", "transition_rate", "barrier_reduction_proxy", "transition_step_distance_proxy"}
    ]
    return {
        "method": "paired PCA-quantile macro-state labels plus paired-z trajectory step-distance proxy",
        "pair_count": len(rows),
        "metric_deltas": aggregate_rows,
        "run_metric_deltas": _run_metric_deltas(rows, metric_names, expected_direction, expected_sign),
        "pair_rows": rows,
        "support_score": float(np.mean(support_components)) if support_components else 0.0,
        "claim_guardrail": "Transition-state metrics are macro-state proxy summaries; they are not true biological energy barriers.",
    }


def _dynamic_samples(pairs: list[EmpiricalPair]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    x_rows: list[np.ndarray] = []
    y_rows: list[np.ndarray] = []
    u_rows: list[float] = []
    subject_rows: list[str] = []
    for pair in pairs:
        placebo_normalized, lsd_normalized = _zscore_pair(pair.placebo, pair.lsd)
        for condition_value, normalized in ((0.0, placebo_normalized), (1.0, lsd_normalized)):
            x_rows.append(normalized[:-1])
            y_rows.append(normalized[1:])
            u_rows.extend([condition_value] * (len(normalized) - 1))
            subject_rows.extend([pair.subject] * (len(normalized) - 1))
    if not x_rows:
        raise ValueError("No dynamic samples are available for DMDc.")
    return (
        np.vstack(x_rows),
        np.vstack(y_rows),
        np.asarray(u_rows, dtype=float)[:, None],
        np.asarray(subject_rows, dtype="U64"),
        list(dict.fromkeys(subject_rows)),
    )


def _fit_linear_model(design: np.ndarray, target: np.ndarray) -> np.ndarray:
    return np.asarray(np.linalg.lstsq(design, target, rcond=None)[0], dtype=float)


def _fit_ridge_model(design: np.ndarray, target: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    penalty = np.eye(design.shape[1], dtype=float) * alpha
    if design.shape[1] > 0:
        penalty[-1, -1] = 0.0
    lhs = design.T @ design + penalty
    rhs = design.T @ target
    return np.asarray(np.linalg.solve(lhs, rhs), dtype=float)


def _rmse(prediction: np.ndarray, target: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(prediction - target))))


def summarize_dmdc(pairs: list[EmpiricalPair]) -> dict[str, Any]:
    if not pairs:
        return {
            "status": "missing",
            "fold_rows": [],
            "condition_input_vector": [],
            "condition_interaction_vector": [],
            "claim_guardrail": "DMDc was not run because no paired empirical viewer records were available.",
        }
    modules = pairs[0].modules
    x, y, u, subjects, unique_subjects = _dynamic_samples(pairs)
    fold_rows: list[dict[str, Any]] = []
    condition_vectors: list[np.ndarray] = []
    interaction_vectors: list[np.ndarray] = []
    ridge_alpha = 1.0
    for held_out_subject in unique_subjects:
        test_mask = subjects == held_out_subject
        train_mask = ~test_mask
        if not np.any(test_mask) or not np.any(train_mask):
            continue

        train_x = x[train_mask]
        train_y = y[train_mask]
        train_u = u[train_mask]
        test_x = x[test_mask]
        test_y = y[test_mask]
        test_u = u[test_mask]

        design_no_input = np.column_stack([train_x, np.ones(len(train_x))])
        weights_no_input = _fit_ridge_model(design_no_input, train_y, alpha=ridge_alpha)
        test_design_no_input = np.column_stack([test_x, np.ones(len(test_x))])
        prediction_no_input = test_design_no_input @ weights_no_input

        design_condition_input = np.column_stack([train_x, train_u, np.ones(len(train_x))])
        weights_condition_input = _fit_ridge_model(design_condition_input, train_y, alpha=ridge_alpha)
        test_design_condition_input = np.column_stack([test_x, test_u, np.ones(len(test_x))])
        prediction_condition_input = test_design_condition_input @ weights_condition_input

        train_interaction = train_x * train_u
        test_interaction = test_x * test_u
        design_condition_interaction = np.column_stack([train_x, train_u, train_interaction, np.ones(len(train_x))])
        weights_condition_interaction = _fit_ridge_model(
            design_condition_interaction,
            train_y,
            alpha=ridge_alpha,
        )
        test_design_condition_interaction = np.column_stack([test_x, test_u, test_interaction, np.ones(len(test_x))])
        prediction_condition_interaction = test_design_condition_interaction @ weights_condition_interaction

        rmse_no_input = _rmse(prediction_no_input, test_y)
        rmse_condition_input = _rmse(prediction_condition_input, test_y)
        rmse_condition_interaction = _rmse(prediction_condition_interaction, test_y)
        improvement = rmse_no_input - rmse_condition_input
        interaction_improvement = rmse_no_input - rmse_condition_interaction
        relative_improvement = 100.0 * improvement / rmse_no_input if rmse_no_input > 1e-12 else 0.0
        interaction_relative_improvement = (
            100.0 * interaction_improvement / rmse_no_input if rmse_no_input > 1e-12 else 0.0
        )
        condition_vector = np.asarray(weights_condition_input[len(modules)], dtype=float)
        interaction_matrix = np.asarray(
            weights_condition_interaction[len(modules) + 1 : len(modules) + 1 + len(modules)],
            dtype=float,
        )
        condition_vectors.append(condition_vector)
        interaction_vectors.append(np.mean(interaction_matrix, axis=1))
        fold_rows.append(
            {
                "held_out_subject": str(held_out_subject),
                "sample_count": int(np.sum(test_mask)),
                "rmse_no_input": rmse_no_input,
                "rmse_condition_input": rmse_condition_input,
                "rmse_condition_interaction": rmse_condition_interaction,
                "rmse_improvement": improvement,
                "relative_improvement_pct": relative_improvement,
                "condition_bias_rmse_improvement": improvement,
                "condition_bias_relative_improvement_pct": relative_improvement,
                "condition_interaction_rmse_improvement": interaction_improvement,
                "condition_interaction_relative_improvement_pct": interaction_relative_improvement,
            }
        )

    improvement_values = [float(row["rmse_improvement"]) for row in fold_rows]
    relative_values = [float(row["relative_improvement_pct"]) for row in fold_rows]
    interaction_improvement_values = [float(row["condition_interaction_rmse_improvement"]) for row in fold_rows]
    interaction_relative_values = [float(row["condition_interaction_relative_improvement_pct"]) for row in fold_rows]
    no_input_values = [float(row["rmse_no_input"]) for row in fold_rows]
    condition_input_values = [float(row["rmse_condition_input"]) for row in fold_rows]
    condition_interaction_values = [float(row["rmse_condition_interaction"]) for row in fold_rows]
    improvement_mean, improvement_std = _mean_std(improvement_values)
    relative_mean, relative_std = _mean_std(relative_values)
    interaction_improvement_mean, interaction_improvement_std = _mean_std(interaction_improvement_values)
    interaction_relative_mean, interaction_relative_std = _mean_std(interaction_relative_values)
    no_input_mean, no_input_std = _mean_std(no_input_values)
    condition_input_mean, condition_input_std = _mean_std(condition_input_values)
    condition_interaction_mean, condition_interaction_std = _mean_std(condition_interaction_values)
    mean_condition_vector = (
        np.mean(np.vstack(condition_vectors), axis=0)
        if condition_vectors
        else np.zeros(len(modules), dtype=float)
    )
    mean_interaction_vector = (
        np.mean(np.vstack(interaction_vectors), axis=0)
        if interaction_vectors
        else np.zeros(len(modules), dtype=float)
    )

    return {
        "status": "implemented_first_pass",
        "equation": "z_pair(x[t+1]) = A z_pair(x[t]) + B u_condition[t] + C (u_condition[t] * z_pair(x[t])) + bias + noise",
        "validation": "leave-one-subject-out one-step prediction with paired placebo/LSD normalization inside each subject/run record",
        "ridge_alpha": ridge_alpha,
        "selected_variant": "condition_interaction",
        "fold_count": len(fold_rows),
        "sample_count": int(len(x)),
        "fold_rows": fold_rows,
        "rmse_no_input_mean": no_input_mean,
        "rmse_no_input_std": no_input_std,
        "rmse_condition_input_mean": condition_input_mean,
        "rmse_condition_input_std": condition_input_std,
        "rmse_improvement_mean": improvement_mean,
        "rmse_improvement_std": improvement_std,
        "relative_improvement_pct_mean": relative_mean,
        "relative_improvement_pct_std": relative_std,
        "rmse_condition_interaction_mean": condition_interaction_mean,
        "rmse_condition_interaction_std": condition_interaction_std,
        "condition_interaction_rmse_improvement_mean": interaction_improvement_mean,
        "condition_interaction_rmse_improvement_std": interaction_improvement_std,
        "condition_interaction_relative_improvement_pct_mean": interaction_relative_mean,
        "condition_interaction_relative_improvement_pct_std": interaction_relative_std,
        "condition_input_vector": [
            {"module": module, "coefficient": float(value)}
            for module, value in zip(modules, mean_condition_vector, strict=True)
        ],
        "condition_interaction_vector": [
            {"module": module, "coefficient": float(value)}
            for module, value in zip(modules, mean_interaction_vector, strict=True)
        ],
        "support_score": interaction_relative_mean,
        "claim_guardrail": "DMDc coefficients are descriptive surrogate parameters, not real governing equations of LSD brain dynamics.",
    }


def _finite_mean(values: list[float] | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if len(array) == 0:
        return 0.0
    return float(np.mean(array))


def _mean_between(fc_matrix: np.ndarray, source_mask: np.ndarray, target_mask: np.ndarray) -> float:
    source_indices = np.flatnonzero(source_mask)
    target_indices = np.flatnonzero(target_mask)
    if len(source_indices) == 0 or len(target_indices) == 0:
        return 0.0
    same_group = np.array_equal(source_mask, target_mask)
    values: list[float] = []
    for source in source_indices:
        for target in target_indices:
            if source == target:
                continue
            if same_group and target <= source:
                continue
            values.append(float(fc_matrix[source, target]))
    return _finite_mean(values)


def _mean_within(fc_matrix: np.ndarray, mask: np.ndarray) -> float:
    return _mean_between(fc_matrix, mask, mask)


def _mean_between_networks(fc_matrix: np.ndarray, masks: dict[str, np.ndarray]) -> float:
    values = [
        _mean_between(fc_matrix, masks["sensory"], masks["transmodal"]),
        _mean_between(fc_matrix, masks["sensory"], masks["gateway"]),
        _mean_between(fc_matrix, masks["transmodal"], masks["gateway"]),
    ]
    return _finite_mean(values)


def _mean_within_networks(fc_matrix: np.ndarray, masks: dict[str, np.ndarray]) -> float:
    values = [
        _mean_within(fc_matrix, masks["sensory"]),
        _mean_within(fc_matrix, masks["transmodal"]),
    ]
    return _finite_mean(values)


def _fc_path_length(time_series: np.ndarray, window_size: int | None = None) -> float:
    array = np.asarray(time_series, dtype=float)
    if window_size is None:
        window_size = max(8, min(40, len(array) // 4))
    if len(array) < window_size * 2:
        return 0.0
    step = max(1, window_size // 2)
    vectors: list[np.ndarray] = []
    for start in range(0, len(array) - window_size + 1, step):
        vectors.append(upper_triangle_vector(safe_corrcoef(array[start : start + window_size])))
    if len(vectors) < 2:
        return 0.0
    stacked = np.vstack(vectors)
    return float(np.mean(np.linalg.norm(np.diff(stacked, axis=0), axis=1)))


def _positive_fc_graph(fc_matrix: np.ndarray) -> np.ndarray:
    matrix = np.maximum(np.asarray(fc_matrix, dtype=float), 0.0)
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 0.0)
    return cast(np.ndarray, matrix)


def _community_labels(masks: dict[str, np.ndarray]) -> np.ndarray:
    labels = np.full(len(masks["all"]), 3, dtype=int)
    labels[masks["sensory"]] = 0
    labels[masks["transmodal"]] = 1
    labels[masks["gateway"]] = 2
    return labels


def _weighted_modularity(matrix: np.ndarray, community_labels: np.ndarray) -> float:
    graph = _positive_fc_graph(matrix)
    total_weight = float(np.sum(graph))
    if total_weight <= 1e-12:
        return 0.0
    degree = np.sum(graph, axis=1)
    expected = np.outer(degree, degree) / total_weight
    same_community = community_labels[:, None] == community_labels[None, :]
    return float(np.sum((graph - expected) * same_community) / total_weight)


def _mean_participation_coefficient(matrix: np.ndarray, community_labels: np.ndarray) -> float:
    graph = _positive_fc_graph(matrix)
    degree = np.sum(graph, axis=1)
    coefficients: list[float] = []
    for node_index, node_degree in enumerate(degree):
        if node_degree <= 1e-12:
            coefficients.append(0.0)
            continue
        community_fractions = []
        for community in sorted(set(community_labels.tolist())):
            community_weight = float(np.sum(graph[node_index, community_labels == community]))
            community_fractions.append((community_weight / node_degree) ** 2)
        coefficients.append(1.0 - float(np.sum(community_fractions)))
    return _finite_mean(coefficients)


def _global_efficiency(matrix: np.ndarray) -> float:
    graph = _positive_fc_graph(matrix)
    n_nodes = graph.shape[0]
    if n_nodes < 2 or float(np.sum(graph)) <= 1e-12:
        return 0.0
    distances = np.full((n_nodes, n_nodes), np.inf, dtype=float)
    np.fill_diagonal(distances, 0.0)
    positive_edges = graph > 1e-12
    distances[positive_edges] = 1.0 / graph[positive_edges]
    for pivot in range(n_nodes):
        distances = np.minimum(distances, distances[:, [pivot]] + distances[[pivot], :])
    finite_distances = distances[np.isfinite(distances) & (distances > 1e-12)]
    if len(finite_distances) == 0:
        return 0.0
    return float(np.mean(1.0 / finite_distances))


def _hierarchy_routing_metrics(modules: tuple[str, ...], time_series: np.ndarray) -> dict[str, float]:
    fc_matrix = safe_corrcoef(time_series)
    masks = _module_masks(modules)
    priors = _module_prior_vectors(modules)
    node_global_coupling = np.asarray(
        [_mean_between(fc_matrix, np.eye(len(modules), dtype=bool)[index], np.ones(len(modules), dtype=bool)) for index in range(len(modules))],
        dtype=float,
    )
    hierarchy_values = priors["hierarchy"]
    receptor_weights = priors["receptor"]
    sensory_transmodal = _mean_between(fc_matrix, masks["sensory"], masks["transmodal"])
    sensory_global = _mean_between(fc_matrix, masks["sensory"], ~masks["sensory"])
    associative_global = _mean_between(fc_matrix, masks["transmodal"], ~masks["transmodal"])
    thalamic_global = _mean_between(fc_matrix, masks["gateway"], masks["non_gateway"])
    thalamic_sensory = _mean_between(fc_matrix, masks["gateway"], masks["sensory"])
    thalamic_transmodal = _mean_between(fc_matrix, masks["gateway"], masks["transmodal"])
    hierarchy_differentiation = _mean_within_networks(fc_matrix, masks) - sensory_transmodal
    hierarchy_gradient_magnitude = abs(_safe_vector_correlation(hierarchy_values, node_global_coupling))
    return {
        "sensory_transmodal_coupling": sensory_transmodal,
        "sensory_global_coupling": sensory_global,
        "associative_global_coupling": associative_global,
        "thalamic_global_coupling": thalamic_global,
        "thalamic_sensory_coupling": thalamic_sensory,
        "thalamic_transmodal_coupling": thalamic_transmodal,
        "hierarchy_differentiation": hierarchy_differentiation,
        "hierarchy_flattening_proxy": -hierarchy_differentiation,
        "hierarchy_coupling_gradient_magnitude": hierarchy_gradient_magnitude,
        "hierarchy_gradient_flattening_proxy": -hierarchy_gradient_magnitude,
        "receptor_weighted_global_coupling": float(
            np.average(node_global_coupling, weights=_normalise_control_weights(receptor_weights))
        ),
        "receptor_global_coupling_alignment": _safe_vector_correlation(receptor_weights, node_global_coupling),
    }


def summarize_hierarchy_routing(pairs: list[EmpiricalPair]) -> dict[str, Any]:
    metric_names = [
        "sensory_transmodal_coupling",
        "sensory_global_coupling",
        "associative_global_coupling",
        "thalamic_global_coupling",
        "thalamic_sensory_coupling",
        "thalamic_transmodal_coupling",
        "hierarchy_differentiation",
        "hierarchy_flattening_proxy",
        "hierarchy_coupling_gradient_magnitude",
        "hierarchy_gradient_flattening_proxy",
        "receptor_weighted_global_coupling",
        "receptor_global_coupling_alignment",
    ]
    rows, metric_deltas = _collect_paired_metric_rows(
        pairs,
        metric_names,
        lambda pair: (
            _hierarchy_routing_metrics(pair.modules, pair.placebo),
            _hierarchy_routing_metrics(pair.modules, pair.lsd),
        ),
    )

    expected_direction = {
        "sensory_transmodal_coupling": "positive means stronger sensory-to-transmodal coupling under LSD",
        "sensory_global_coupling": "positive means stronger sensory/somatomotor global coupling under LSD",
        "associative_global_coupling": "negative means weaker associative-network global coupling under LSD",
        "thalamic_global_coupling": "positive means stronger thalamic-gateway coupling with cortex under LSD",
        "thalamic_sensory_coupling": "positive means stronger thalamic-gateway coupling with sensory modules under LSD",
        "thalamic_transmodal_coupling": "positive means stronger thalamic-gateway coupling with transmodal modules under LSD",
        "hierarchy_differentiation": "negative means reduced within-vs-cross hierarchy separation under LSD",
        "hierarchy_flattening_proxy": "positive means hierarchy differentiation is reduced under LSD",
        "hierarchy_coupling_gradient_magnitude": "negative means node global-coupling is less tied to the hierarchy proxy under LSD",
        "hierarchy_gradient_flattening_proxy": "positive means reduced hierarchy/global-coupling gradient strength under LSD",
        "receptor_weighted_global_coupling": "positive means stronger global coupling in high receptor-prior modules under LSD",
        "receptor_global_coupling_alignment": "positive means high receptor-prior modules align more with global coupling under LSD",
    }
    expected_sign = {
        "sensory_transmodal_coupling": 1,
        "sensory_global_coupling": 1,
        "associative_global_coupling": -1,
        "thalamic_global_coupling": 1,
        "thalamic_sensory_coupling": 1,
        "thalamic_transmodal_coupling": 1,
        "hierarchy_differentiation": -1,
        "hierarchy_flattening_proxy": 1,
        "hierarchy_coupling_gradient_magnitude": -1,
        "hierarchy_gradient_flattening_proxy": 1,
        "receptor_weighted_global_coupling": 1,
        "receptor_global_coupling_alignment": 1,
    }
    aggregate_rows = _aggregate_metric_deltas(metric_deltas, expected_direction, expected_sign)
    support_metrics = {
        "sensory_transmodal_coupling",
        "sensory_global_coupling",
        "associative_global_coupling",
        "thalamic_global_coupling",
        "hierarchy_flattening_proxy",
        "hierarchy_gradient_flattening_proxy",
        "receptor_weighted_global_coupling",
        "receptor_global_coupling_alignment",
    }
    support_components = [row["signed_effect_size"] for row in aggregate_rows if row["metric"] in support_metrics]
    return {
        "status": "implemented_first_pass",
        "method": "paired FC group metrics over sensory, transmodal/associative, and thalamic-gateway proxy modules",
        "pair_count": len(rows),
        "metric_deltas": aggregate_rows,
        "run_metric_deltas": _run_metric_deltas(rows, metric_names, expected_direction, expected_sign),
        "pair_rows": rows,
        "support_score": float(np.mean(support_components)) if support_components else 0.0,
        "claim_guardrail": "Hierarchy/routing metrics are coarse FC proxies; they do not prove REBUS, precision relaxation, or thalamic gating.",
    }


def _dynamic_repertoire_metrics(modules: tuple[str, ...], time_series: np.ndarray, window_size: int | None = None) -> dict[str, float]:
    fc_matrix = safe_corrcoef(time_series)
    masks = _module_masks(modules)
    communities = _community_labels(masks)
    within = _mean_within_networks(fc_matrix, masks)
    between = _mean_between_networks(fc_matrix, masks)
    modularity_q = _weighted_modularity(fc_matrix, communities)
    return {
        "global_mean_fc": _finite_mean(upper_triangle_vector(fc_matrix)),
        "within_network_segregation": within,
        "between_network_integration": between,
        "integration_segregation_balance": between - within,
        "dynamic_fc_variance": dynamic_fc_variance(time_series, window_size=window_size),
        "dynamic_fc_path_length": _fc_path_length(time_series, window_size=window_size),
        "trajectory_step_distance": _mean_step_distance(time_series),
        "graph_modularity_q": modularity_q,
        "graph_modularity_reduction_proxy": -modularity_q,
        "mean_participation_coefficient": _mean_participation_coefficient(fc_matrix, communities),
        "global_efficiency": _global_efficiency(fc_matrix),
    }


def summarize_dynamic_repertoire(pairs: list[EmpiricalPair], *, window_size: int | None = None) -> dict[str, Any]:
    metric_names = [
        "global_mean_fc",
        "within_network_segregation",
        "between_network_integration",
        "integration_segregation_balance",
        "dynamic_fc_variance",
        "dynamic_fc_path_length",
        "trajectory_step_distance",
        "graph_modularity_q",
        "graph_modularity_reduction_proxy",
        "mean_participation_coefficient",
        "global_efficiency",
    ]
    def repertoire_metrics_for_pair(pair: EmpiricalPair) -> tuple[dict[str, float], dict[str, float]]:
        placebo_normalized, lsd_normalized = _zscore_pair(pair.placebo, pair.lsd)
        return (
            _dynamic_repertoire_metrics(pair.modules, placebo_normalized, window_size=window_size),
            _dynamic_repertoire_metrics(pair.modules, lsd_normalized, window_size=window_size),
        )

    rows, metric_deltas = _collect_paired_metric_rows(pairs, metric_names, repertoire_metrics_for_pair)

    expected_direction = {
        "global_mean_fc": "positive means globally stronger FC under LSD",
        "within_network_segregation": "negative means weaker within-network segregation under LSD",
        "between_network_integration": "positive means stronger between-network integration under LSD",
        "integration_segregation_balance": "positive means integration increases relative to segregation under LSD",
        "dynamic_fc_variance": "positive means a broader time-varying FC repertoire under LSD",
        "dynamic_fc_path_length": "positive means larger movement through FC-state space under LSD",
        "trajectory_step_distance": "positive means larger macro-trajectory steps under LSD",
        "graph_modularity_q": "negative means lower graph modularity under LSD",
        "graph_modularity_reduction_proxy": "positive means reduced graph modularity under LSD",
        "mean_participation_coefficient": "positive means nodes distribute connectivity across more communities under LSD",
        "global_efficiency": "positive means stronger graph-theoretic integration under LSD",
    }
    expected_sign = {
        "global_mean_fc": 1,
        "within_network_segregation": -1,
        "between_network_integration": 1,
        "integration_segregation_balance": 1,
        "dynamic_fc_variance": 1,
        "dynamic_fc_path_length": 1,
        "trajectory_step_distance": 1,
        "graph_modularity_q": -1,
        "graph_modularity_reduction_proxy": 1,
        "mean_participation_coefficient": 1,
        "global_efficiency": 1,
    }
    aggregate_rows = _aggregate_metric_deltas(metric_deltas, expected_direction, expected_sign)
    support_metrics = {
        "within_network_segregation",
        "between_network_integration",
        "integration_segregation_balance",
        "dynamic_fc_variance",
        "dynamic_fc_path_length",
        "graph_modularity_reduction_proxy",
        "mean_participation_coefficient",
        "global_efficiency",
    }
    support_components = [row["signed_effect_size"] for row in aggregate_rows if row["metric"] in support_metrics]
    return {
        "status": "implemented_first_pass",
        "method": "paired dynamic-FC and integration/segregation proxy summaries",
        "window_size": window_size,
        "pair_count": len(rows),
        "metric_deltas": aggregate_rows,
        "run_metric_deltas": _run_metric_deltas(rows, metric_names, expected_direction, expected_sign),
        "pair_rows": rows,
        "support_score": float(np.mean(support_components)) if support_components else 0.0,
        "claim_guardrail": "Dynamic repertoire metrics are descriptive FC/time-series proxies; they are not direct measures of subjective richness.",
    }


def _control_graph_matrix(modules: tuple[str, ...], pairs: list[EmpiricalPair]) -> tuple[np.ndarray, str]:
    if modules == MODULE_NAMES and DEFAULT_MACRO_GRAPH_PATH.exists():
        graph = load_graph_config(DEFAULT_MACRO_GRAPH_PATH)
        return np.asarray(graph.adjacency, dtype=float), "configs/graphs/macro_modules.yaml macro-module proxy graph; not a subject structural connectome"

    matrices: list[np.ndarray] = []
    for pair in pairs:
        matrices.append(_positive_fc_graph(safe_corrcoef(pair.placebo)))
    if matrices:
        return np.mean(np.stack(matrices), axis=0), "mean positive placebo FC proxy graph; not a structural connectome"
    return np.zeros((len(modules), len(modules)), dtype=float), "empty graph fallback"


def _stable_dynamics_matrix(graph_matrix: np.ndarray) -> np.ndarray:
    graph = np.maximum(np.asarray(graph_matrix, dtype=float), 0.0)
    graph = (graph + graph.T) / 2.0
    np.fill_diagonal(graph, 0.0)
    n_nodes = graph.shape[0]
    if n_nodes == 0:
        return cast(np.ndarray, graph)
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(graph)))) if float(np.sum(graph)) > 1e-12 else 0.0
    normalized_graph = graph / spectral_radius if spectral_radius > 1e-12 else np.zeros_like(graph)
    return cast(np.ndarray, 0.35 * np.eye(n_nodes, dtype=float) + 0.50 * normalized_graph)


def _minimum_control_energy(
    dynamics: np.ndarray,
    control_weights: np.ndarray,
    initial_state: np.ndarray,
    target_state: np.ndarray,
    horizon: int = CONTROL_HORIZON,
) -> float:
    solver = _build_control_energy_solver(dynamics, control_weights, horizon=horizon)
    return _minimum_control_energy_from_solver(solver, initial_state, target_state)


def _build_control_energy_solver(
    dynamics: np.ndarray,
    control_weights: np.ndarray,
    horizon: int = CONTROL_HORIZON,
) -> ControlEnergySolver:
    if dynamics.size == 0:
        return ControlEnergySolver(
            dynamics_horizon=np.zeros_like(dynamics, dtype=float),
            gramian_inverse=np.zeros_like(dynamics, dtype=float),
        )
    weights = _normalise_control_weights(control_weights)
    control_matrix = np.diag(weights)
    gramian = np.zeros_like(dynamics, dtype=float)
    power = np.eye(dynamics.shape[0], dtype=float)
    for _ in range(horizon):
        gramian += power @ control_matrix @ control_matrix.T @ power.T
        power = dynamics @ power
    gramian = (gramian + gramian.T) / 2.0 + 1e-8 * np.eye(dynamics.shape[0], dtype=float)
    return ControlEnergySolver(
        dynamics_horizon=np.linalg.matrix_power(dynamics, horizon),
        gramian_inverse=np.linalg.pinv(gramian, rcond=1e-8),
    )


def _minimum_control_energy_from_solver(
    solver: ControlEnergySolver,
    initial_state: np.ndarray,
    target_state: np.ndarray,
) -> float:
    if solver.dynamics_horizon.size == 0:
        return 0.0
    drift = solver.dynamics_horizon @ np.asarray(initial_state, dtype=float)
    residual = np.asarray(target_state, dtype=float) - drift
    energy = float(residual.T @ solver.gramian_inverse @ residual)
    return energy if math.isfinite(energy) and energy >= 0.0 else 0.0


def _matched_state_pairs(
    pair: EmpiricalPair,
    *,
    state_bins: int = 4,
    state_score_mode: str = "pca",
) -> tuple[list[tuple[np.ndarray, np.ndarray]], np.ndarray]:
    placebo_normalized, lsd_normalized = _zscore_pair(pair.placebo, pair.lsd)
    reference = np.vstack([placebo_normalized, lsd_normalized])
    placebo_labels = _state_labels_from_reference(reference, placebo_normalized, state_bins=state_bins, score_mode=state_score_mode)
    lsd_labels = _state_labels_from_reference(reference, lsd_normalized, state_bins=state_bins, score_mode=state_score_mode)
    state_pairs: list[tuple[np.ndarray, np.ndarray]] = []
    target_displacements: list[np.ndarray] = []
    for state_label in sorted(set(placebo_labels.tolist()) & set(lsd_labels.tolist())):
        placebo_mask = placebo_labels == state_label
        lsd_mask = lsd_labels == state_label
        if not np.any(placebo_mask) or not np.any(lsd_mask):
            continue
        placebo_state = np.mean(placebo_normalized[placebo_mask], axis=0)
        lsd_state = np.mean(lsd_normalized[lsd_mask], axis=0)
        state_pairs.append((placebo_state, lsd_state))
        target_displacements.append(np.abs(lsd_state - placebo_state))
    if not state_pairs:
        placebo_state = np.mean(placebo_normalized, axis=0)
        lsd_state = np.mean(lsd_normalized, axis=0)
        state_pairs.append((placebo_state, lsd_state))
        target_displacements.append(np.abs(lsd_state - placebo_state))
    return state_pairs, np.mean(np.stack(target_displacements), axis=0)


def _profile_energy(
    solver: ControlEnergySolver,
    state_pairs: list[tuple[np.ndarray, np.ndarray]],
) -> float:
    return _finite_mean(
        [
            _minimum_control_energy_from_solver(solver, initial_state, target_state)
            for initial_state, target_state in state_pairs
        ]
    )


def _mean_timepoint_transition_energy(
    solver: ControlEnergySolver,
    time_series: np.ndarray,
) -> float:
    if len(time_series) < 2:
        return 0.0
    return _finite_mean(
        [
            _minimum_control_energy_from_solver(solver, time_series[index], time_series[index + 1])
            for index in range(len(time_series) - 1)
        ]
    )


def _pct_reduction(reference: float, candidate: float) -> float:
    if reference <= 1e-12:
        return 0.0
    return float(100.0 * (reference - candidate) / reference)


def summarize_network_control_energy(
    pairs: list[EmpiricalPair],
    *,
    horizon: int = CONTROL_HORIZON,
    random_null_count: int = CONTROL_NULL_COUNT,
    rng_seed: int = 20260519,
    state_bins: int = 4,
    state_score_mode: str = "pca",
    graph_matrix_override: np.ndarray | None = None,
    graph_source_override: str | None = None,
    graph_is_structural_connectome: bool = False,
    prior_vectors_override: dict[str, np.ndarray] | None = None,
    receptor_prior_source_override: str | None = None,
) -> dict[str, Any]:
    if not pairs:
        return {
            "status": "missing",
            "metric_deltas": [],
            "run_metric_deltas": [],
            "pair_rows": [],
            "energy_rows": [],
            "control_profiles": [],
            "support_score": 0.0,
            "claim_guardrail": "Network-control energy was not run because no paired empirical viewer records were available.",
        }

    modules = pairs[0].modules
    if graph_matrix_override is None:
        graph_matrix, graph_source = _control_graph_matrix(modules, pairs)
    else:
        graph_matrix = np.asarray(graph_matrix_override, dtype=float)
        graph_source = graph_source_override or "caller-supplied graph matrix"
        if graph_matrix.shape != (len(modules), len(modules)):
            raise ValueError(
                f"Graph matrix shape {graph_matrix.shape} does not match module count {len(modules)}."
            )
    dynamics = _stable_dynamics_matrix(graph_matrix)
    priors = _module_prior_vectors(modules)
    if prior_vectors_override:
        for profile_name, vector in prior_vectors_override.items():
            prior_array = np.asarray(vector, dtype=float)
            if prior_array.shape != (len(modules),):
                raise ValueError(
                    f"Prior vector '{profile_name}' shape {prior_array.shape} does not match module count {len(modules)}."
                )
            priors[profile_name] = prior_array
    degree = np.sum(np.maximum(graph_matrix, 0.0), axis=1)
    priors["degree"] = degree if float(np.sum(degree)) > 1e-12 else np.ones(len(modules), dtype=float)
    profile_names = ["uniform", "receptor", "hierarchy", "sensory", "transmodal", "thalamic", "degree"]
    profile_solvers = {
        profile_name: _build_control_energy_solver(dynamics, priors[profile_name], horizon=horizon)
        for profile_name in profile_names
    }

    rng = np.random.default_rng(rng_seed)
    random_solvers = [
        _build_control_energy_solver(dynamics, rng.permutation(priors["receptor"]), horizon=horizon)
        for _ in range(random_null_count)
    ]
    rows: list[dict[str, Any]] = []
    energy_rows: list[dict[str, Any]] = []
    metric_names = [
        "lsd_vs_placebo_receptor_transition_energy_reduction_pct",
        "lsd_vs_placebo_uniform_transition_energy_reduction_pct",
        "receptor_vs_uniform_energy_reduction_pct",
        "receptor_vs_random_energy_reduction_pct",
        "hierarchy_vs_uniform_energy_reduction_pct",
        "transmodal_vs_uniform_energy_reduction_pct",
        "state_target_alignment_receptor",
    ]
    metric_values: dict[str, list[float]] = {metric: [] for metric in metric_names}

    for pair in pairs:
        state_pairs, target_displacement = _matched_state_pairs(pair, state_bins=state_bins, state_score_mode=state_score_mode)
        placebo_normalized, lsd_normalized = _zscore_pair(pair.placebo, pair.lsd)
        placebo_receptor_transition_energy = _mean_timepoint_transition_energy(profile_solvers["receptor"], placebo_normalized)
        lsd_receptor_transition_energy = _mean_timepoint_transition_energy(profile_solvers["receptor"], lsd_normalized)
        placebo_uniform_transition_energy = _mean_timepoint_transition_energy(profile_solvers["uniform"], placebo_normalized)
        lsd_uniform_transition_energy = _mean_timepoint_transition_energy(profile_solvers["uniform"], lsd_normalized)
        energies = {
            profile_name: _profile_energy(profile_solvers[profile_name], state_pairs)
            for profile_name in profile_names
        }
        random_energies = [
            _profile_energy(random_solver, state_pairs)
            for random_solver in random_solvers
        ]
        random_mean = _finite_mean(random_energies)
        random_std = float(np.std(np.asarray(random_energies, dtype=float), ddof=1)) if len(random_energies) > 1 else 0.0
        metrics = {
            "lsd_vs_placebo_receptor_transition_energy_reduction_pct": _pct_reduction(
                placebo_receptor_transition_energy,
                lsd_receptor_transition_energy,
            ),
            "lsd_vs_placebo_uniform_transition_energy_reduction_pct": _pct_reduction(
                placebo_uniform_transition_energy,
                lsd_uniform_transition_energy,
            ),
            "receptor_vs_uniform_energy_reduction_pct": _pct_reduction(energies["uniform"], energies["receptor"]),
            "receptor_vs_random_energy_reduction_pct": _pct_reduction(random_mean, energies["receptor"]),
            "hierarchy_vs_uniform_energy_reduction_pct": _pct_reduction(energies["uniform"], energies["hierarchy"]),
            "transmodal_vs_uniform_energy_reduction_pct": _pct_reduction(energies["uniform"], energies["transmodal"]),
            "state_target_alignment_receptor": _safe_vector_correlation(priors["receptor"], target_displacement),
        }
        for metric, value in metrics.items():
            metric_values[metric].append(value)
        for profile_name, energy in energies.items():
            energy_rows.append(
                {
                    "subject": pair.subject,
                    "run": pair.run,
                    "profile": profile_name,
                    "mean_control_energy": energy,
                    "matched_state_count": len(state_pairs),
                }
            )
        energy_rows.append(
            {
                "subject": pair.subject,
                "run": pair.run,
                "profile": "random_receptor_permutation_mean",
                "mean_control_energy": random_mean,
                "matched_state_count": len(state_pairs),
            }
        )
        rows.append(
            {
                "subject": pair.subject,
                "run": pair.run,
                "matched_state_count": len(state_pairs),
                "energies": {**energies, "random_receptor_permutation_mean": random_mean, "random_receptor_permutation_std": random_std},
                "condition_transition_energies": {
                    "placebo_receptor": placebo_receptor_transition_energy,
                    "lsd_receptor": lsd_receptor_transition_energy,
                    "placebo_uniform": placebo_uniform_transition_energy,
                    "lsd_uniform": lsd_uniform_transition_energy,
                },
                "metrics": metrics,
                "target_displacement": {
                    module: float(value)
                    for module, value in zip(modules, target_displacement, strict=True)
                },
            }
        )

    expected_direction = {
        "lsd_vs_placebo_receptor_transition_energy_reduction_pct": (
            "positive means LSD within-condition transitions need less receptor-profile control energy than placebo"
        ),
        "lsd_vs_placebo_uniform_transition_energy_reduction_pct": (
            "positive means LSD within-condition transitions need less uniform-control energy than placebo"
        ),
        "receptor_vs_uniform_energy_reduction_pct": "positive means receptor-prior control needs less energy than uniform control",
        "receptor_vs_random_energy_reduction_pct": "positive means receptor-prior control needs less energy than random receptor-prior permutations",
        "hierarchy_vs_uniform_energy_reduction_pct": "positive means hierarchy-prior control needs less energy than uniform control",
        "transmodal_vs_uniform_energy_reduction_pct": "positive means transmodal-prior control needs less energy than uniform control",
        "state_target_alignment_receptor": "positive means modules with higher receptor prior align with larger LSD-minus-placebo state displacement",
    }
    expected_sign = {metric: 1 for metric in metric_names}
    aggregate_rows = _aggregate_metric_deltas(
        metric_values,
        expected_direction,
        expected_sign,
        bootstrap_seed=MECHANISM_METRIC_BOOTSTRAP_SEED + 202,
    )
    support_components = [
        row["signed_effect_size"]
        for row in aggregate_rows
        if row["metric"]
        in {
            "lsd_vs_placebo_receptor_transition_energy_reduction_pct",
            "lsd_vs_placebo_uniform_transition_energy_reduction_pct",
            "receptor_vs_random_energy_reduction_pct",
            "state_target_alignment_receptor",
        }
    ]

    return {
        "status": "implemented_proxy_control_energy",
        "method": (
            "finite-horizon discrete network-control energy over matched PCA-state centroids; "
            "control profiles share the same mean control budget"
        ),
        "equation": "x[t+1] = A_graph x[t] + B_profile u[t]; energy = min sum_t ||u[t]||^2 over a finite horizon",
        "horizon": horizon,
        "state_bins": state_bins,
        "state_score_mode": state_score_mode,
        "control_weight_floor": CONTROL_WEIGHT_FLOOR,
        "random_null_count": random_null_count,
        "graph_source": graph_source,
        "graph_is_structural_connectome": graph_is_structural_connectome,
        "receptor_prior_source": receptor_prior_source_override
        or "coarse module-level proxy prior from receptor-gradient model config; not a PET-derived receptor map",
        "pair_count": len(rows),
        "metric_deltas": aggregate_rows,
        "run_metric_deltas": _run_metric_deltas(
            [{"run": row["run"], "delta": row["metrics"]} for row in rows],
            metric_names,
            expected_direction,
            expected_sign,
        ),
        "pair_rows": rows,
        "energy_rows": energy_rows,
        "control_profiles": [
            {
                "profile": profile_name,
                "module_weights": {
                    module: float(value)
                    for module, value in zip(modules, _normalise_control_weights(priors[profile_name]), strict=True)
                },
            }
            for profile_name in profile_names
        ],
        "support_score": float(np.mean(support_components)) if support_components else 0.0,
        "claim_guardrail": (
            "E is a receptor/hierarchy-informed proxy-control test. It is not full receptor-informed network control theory "
            "until a structural connectome and PET-derived receptor map are added."
        ),
    }


def _literature_support_rows() -> list[dict[str, str]]:
    return [
        {
            "layer": "A",
            "claim_supported": "Transition/barrier language is a proxy framing, not a demonstrated biological energy landscape.",
            "source": "Carhart-Harris and Friston 2019 REBUS; energy/free-energy framing is theoretical.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/31221820/",
        },
        {
            "layer": "B",
            "claim_supported": "DMDc is a defensible data-driven controlled-dynamics baseline, but it is not network-control energy.",
            "source": "Proctor, Brunton, and Kutz 2016 Dynamic Mode Decomposition with Control.",
            "url": "https://epubs.siam.org/doi/10.1137/15M1013857",
        },
        {
            "layer": "C",
            "claim_supported": "Hierarchy/routing proxies are motivated by sensory-associative and thalamic connectivity findings.",
            "source": "Preller et al. 2018 eLife; Preller et al. 2019 PNAS.",
            "url": "https://elifesciences.org/articles/35082",
        },
        {
            "layer": "D",
            "claim_supported": "Dynamic repertoire and integration/segregation are directly studied LSD fMRI targets.",
            "source": "Luppi et al. 2021 NeuroImage; Atasoy et al. 2017 Scientific Reports.",
            "url": "https://www.nature.com/articles/s41598-017-17546-0",
        },
        {
            "layer": "E",
            "claim_supported": "Receptor-informed control-energy landscape tests are directly motivated by psychedelic network-control papers.",
            "source": "Singleton et al. 2022 Nature Communications; Gu et al. 2015 controllability of structural brain networks.",
            "url": "https://www.nature.com/articles/s41467-022-33578-1",
        },
    ]


def build_dynamic_mechanism_summary(
    viewer_root: Path,
    *,
    network_control_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pairs = load_empirical_pairs(viewer_root)
    modules = list(pairs[0].modules) if pairs else []
    runs = sorted({pair.run for pair in pairs})
    subjects = sorted({pair.subject for pair in pairs})
    transition_proxy = summarize_transition_proxy(pairs)
    dmdc = summarize_dmdc(pairs)
    hierarchy_routing = summarize_hierarchy_routing(pairs)
    dynamic_repertoire = summarize_dynamic_repertoire(pairs)
    network_control_energy = summarize_network_control_energy(pairs, **(network_control_kwargs or {}))

    implemented_rankings: list[dict[str, Any]] = [
        {
            "rank": None,
            "layer": "A",
            "mechanism": "transition_state_proxy",
            "status": "implemented_first_pass",
            "score": transition_proxy["support_score"],
            "evidence": "state occupancy, transition entropy, transition rate, dwell/barrier, and step-distance proxies",
        },
        {
            "rank": None,
            "layer": "B",
            "mechanism": "dmdc_condition_interaction",
            "status": (
                "implemented_predictive_baseline"
                if float(dmdc.get("support_score", 0.0)) > 0.0
                else "implemented_negative_control_baseline"
            ),
            "score": dmdc.get("support_score", 0.0),
            "evidence": "leave-one-subject-out one-step RMSE change; retained as a predictive baseline, not control-energy evidence",
        },
        {
            "rank": None,
            "layer": "C",
            "mechanism": "hierarchy_routing_layer",
            "status": "implemented_first_pass",
            "score": hierarchy_routing["support_score"],
            "evidence": "sensory-transmodal, associative, thalamic-gateway, and hierarchy-flattening FC proxies",
        },
        {
            "rank": None,
            "layer": "D",
            "mechanism": "dynamic_repertoire_layer",
            "status": "implemented_first_pass",
            "score": dynamic_repertoire["support_score"],
            "evidence": "integration, segregation, graph modularity, participation, dynamic-FC variance, and trajectory-step proxies",
        },
        {
            "rank": None,
            "layer": "E",
            "mechanism": "receptor_informed_network_control_energy",
            "status": network_control_energy["status"],
            "score": network_control_energy["support_score"],
            "evidence": "finite-horizon control energy with receptor, hierarchy, transmodal, random, and degree-control profiles",
        },
    ]
    implemented_rankings = sorted(implemented_rankings, key=lambda row: float(row["score"]), reverse=True)
    for index, row in enumerate(implemented_rankings, start=1):
        row["rank"] = index

    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_status": "implemented_first_pass" if pairs else "missing_empirical_pairs",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inference_metadata": {
            "metric_ci_alpha": MECHANISM_METRIC_BOOTSTRAP_ALPHA,
            "metric_bootstrap_iterations": MECHANISM_METRIC_BOOTSTRAP_ITERATIONS,
            "multiple_testing": "Benjamini-Hochberg FDR q-values on sign-flip familywise tests",
            "metric_bootstrap_seed_base": MECHANISM_METRIC_BOOTSTRAP_SEED,
        },
        "source_viewer_root": str(viewer_root.as_posix()),
        "dataset_scope": "cached ds003059 paired placebo/LSD empirical viewer records",
        "pair_count": len(pairs),
        "subject_count": len(subjects),
        "subjects": subjects,
        "runs": runs,
        "modules": modules,
        "transition_proxy": transition_proxy,
        "dmdc": dmdc,
        "hierarchy_routing": hierarchy_routing,
        "dynamic_repertoire": dynamic_repertoire,
        "network_control_energy": network_control_energy,
        "mechanism_ranking": implemented_rankings,
        "literature_support": _literature_support_rows(),
        "claim_guardrail": (
            "These are AI/ML surrogate results for ranking macro-dynamic mechanisms; "
            "they do not establish receptor-level, clinical, external-validity, or subjective-experience claims."
        ),
        "limitations": [
            "Macro-state labels use a deterministic PCA-quantile proxy; clustering choices remain a sensitivity risk even with step-distance diagnostics.",
            "DMDc uses one-step ridge-linear prediction on paired-normalized cached module trajectories; it is a baseline, not the network-control result.",
            "C and D use coarse 8-module FC and graph proxies, not canonical network or thalamic-nucleus definitions.",
            (
                "E currently uses a macro-module proxy graph and coarse receptor priors; it is not full "
                "structural-connectome/PET receptor-informed network control theory."
            ),
            (
                "Nulls include receptor-weight permutations and degree controls, but not yet degree-preserving "
                "structural graph rewires or spatial-autocorrelation-preserving receptor-map nulls."
            ),
            (
                "Metric summaries now include bootstrap confidence intervals and BH-FDR correction for "
                "sign-consistency p-values; with small n these are uncertainty descriptors, not population claims."
            ),
            "Run-02 music data are available in the fMRI explorer but are not part of this primary A+B+C+D+E ranking summary.",
        ],
    }


def write_dynamic_mechanism_summary(
    viewer_root: Path,
    output_dir: Path,
    *,
    network_control_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = build_dynamic_mechanism_summary(viewer_root, network_control_kwargs=network_control_kwargs)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    summary["source_path"] = summary_path.as_posix()
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
