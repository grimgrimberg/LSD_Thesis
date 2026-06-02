from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from lsd_thesis.dynamic_mechanism_connectivity import (
    community_labels,
    fc_path_length,
    finite_mean,
    global_efficiency,
    mean_between_networks,
    mean_participation_coefficient,
    mean_within_networks,
    weighted_modularity,
)
from lsd_thesis.dynamic_mechanism_priors import module_masks
from lsd_thesis.dynamic_mechanism_stats import (
    aggregate_metric_deltas,
    collect_paired_metric_rows,
    mean_step_distance,
    run_metric_deltas,
    zscore_pair,
)
from lsd_thesis.metrics_literature import dynamic_fc_variance, safe_corrcoef, upper_triangle_vector


def _dynamic_repertoire_metrics(
    modules: tuple[str, ...],
    time_series: np.ndarray,
    window_size: int | None = None,
) -> dict[str, float]:
    fc_matrix = safe_corrcoef(time_series)
    masks = module_masks(modules)
    communities = community_labels(masks)
    within = mean_within_networks(fc_matrix, masks)
    between = mean_between_networks(fc_matrix, masks)
    modularity_q = weighted_modularity(fc_matrix, communities)
    return {
        "global_mean_fc": finite_mean(upper_triangle_vector(fc_matrix)),
        "within_network_segregation": within,
        "between_network_integration": between,
        "integration_segregation_balance": between - within,
        "dynamic_fc_variance": dynamic_fc_variance(time_series, window_size=window_size),
        "dynamic_fc_path_length": fc_path_length(time_series, window_size=window_size),
        "trajectory_step_distance": mean_step_distance(time_series),
        "graph_modularity_q": modularity_q,
        "graph_modularity_reduction_proxy": -modularity_q,
        "mean_participation_coefficient": mean_participation_coefficient(fc_matrix, communities),
        "global_efficiency": global_efficiency(fc_matrix),
    }


def summarize_dynamic_repertoire(pairs: Sequence[Any], *, window_size: int | None = None) -> dict[str, Any]:
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

    def repertoire_metrics_for_pair(pair: Any) -> tuple[dict[str, float], dict[str, float]]:
        placebo_normalized, lsd_normalized = zscore_pair(pair.placebo, pair.lsd)
        return (
            _dynamic_repertoire_metrics(pair.modules, placebo_normalized, window_size=window_size),
            _dynamic_repertoire_metrics(pair.modules, lsd_normalized, window_size=window_size),
        )

    rows, metric_deltas = collect_paired_metric_rows(pairs, metric_names, repertoire_metrics_for_pair)

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
    aggregate_rows = aggregate_metric_deltas(metric_deltas, expected_direction, expected_sign)
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
        "run_metric_deltas": run_metric_deltas(rows, metric_names, expected_direction, expected_sign),
        "pair_rows": rows,
        "support_score": float(np.mean(support_components)) if support_components else 0.0,
        "claim_guardrail": "Dynamic repertoire metrics are descriptive FC/time-series proxies; they are not direct measures of subjective richness.",
    }
