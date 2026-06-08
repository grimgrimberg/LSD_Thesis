from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from lsd_thesis.dynamic_mechanism.stats import (
    MECHANISM_METRIC_BOOTSTRAP_SEED,
    aggregate_metric_deltas,
    collect_paired_metric_rows,
    mean_step_distance,
    run_metric_deltas,
    state_labels_from_reference,
    transition_metrics,
    zscore_pair,
)


def summarize_transition_proxy(pairs: Sequence[Any]) -> dict[str, Any]:
    metric_names = [
        "state_occupancy_entropy",
        "transition_entropy",
        "transition_rate",
        "mean_dwell_time",
        "barrier_reduction_proxy",
        "transition_step_distance_proxy",
    ]

    def transition_metrics_for_pair(pair: Any) -> tuple[dict[str, float], dict[str, float]]:
        reference = np.vstack([pair.placebo, pair.lsd])
        placebo_labels = state_labels_from_reference(reference, pair.placebo)
        lsd_labels = state_labels_from_reference(reference, pair.lsd)
        placebo_metrics = transition_metrics(placebo_labels)
        lsd_metrics = transition_metrics(lsd_labels)
        placebo_normalized, lsd_normalized = zscore_pair(pair.placebo, pair.lsd)
        placebo_metrics["transition_step_distance_proxy"] = mean_step_distance(placebo_normalized)
        lsd_metrics["transition_step_distance_proxy"] = mean_step_distance(lsd_normalized)
        return placebo_metrics, lsd_metrics

    rows, metric_deltas = collect_paired_metric_rows(pairs, metric_names, transition_metrics_for_pair)

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
    aggregate_rows = aggregate_metric_deltas(
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
        "run_metric_deltas": run_metric_deltas(rows, metric_names, expected_direction, expected_sign),
        "pair_rows": rows,
        "support_score": float(np.mean(support_components)) if support_components else 0.0,
        "claim_guardrail": "Transition-state metrics are macro-state proxy summaries; they are not true biological energy barriers.",
    }
