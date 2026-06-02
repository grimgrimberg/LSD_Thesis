from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from lsd_thesis.dynamic_mechanism_connectivity import (
    mean_between,
    mean_within_networks,
    safe_vector_correlation,
)
from lsd_thesis.dynamic_mechanism_priors import (
    module_masks,
    module_prior_vectors,
    normalise_control_weights,
)
from lsd_thesis.dynamic_mechanism_stats import (
    aggregate_metric_deltas,
    collect_paired_metric_rows,
    run_metric_deltas,
)
from lsd_thesis.metrics_literature import safe_corrcoef


def _hierarchy_routing_metrics(modules: tuple[str, ...], time_series: np.ndarray) -> dict[str, float]:
    fc_matrix = safe_corrcoef(time_series)
    masks = module_masks(modules)
    priors = module_prior_vectors(modules)
    node_global_coupling = np.asarray(
        [
            mean_between(
                fc_matrix,
                np.eye(len(modules), dtype=bool)[index],
                np.ones(len(modules), dtype=bool),
            )
            for index in range(len(modules))
        ],
        dtype=float,
    )
    hierarchy_values = priors["hierarchy"]
    receptor_weights = priors["receptor"]
    sensory_transmodal = mean_between(fc_matrix, masks["sensory"], masks["transmodal"])
    sensory_global = mean_between(fc_matrix, masks["sensory"], ~masks["sensory"])
    associative_global = mean_between(fc_matrix, masks["transmodal"], ~masks["transmodal"])
    thalamic_global = mean_between(fc_matrix, masks["gateway"], masks["non_gateway"])
    thalamic_sensory = mean_between(fc_matrix, masks["gateway"], masks["sensory"])
    thalamic_transmodal = mean_between(fc_matrix, masks["gateway"], masks["transmodal"])
    hierarchy_differentiation = mean_within_networks(fc_matrix, masks) - sensory_transmodal
    hierarchy_gradient_magnitude = abs(safe_vector_correlation(hierarchy_values, node_global_coupling))
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
            np.average(node_global_coupling, weights=normalise_control_weights(receptor_weights))
        ),
        "receptor_global_coupling_alignment": safe_vector_correlation(receptor_weights, node_global_coupling),
    }


def summarize_hierarchy_routing(pairs: Sequence[Any]) -> dict[str, Any]:
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
    rows, metric_deltas = collect_paired_metric_rows(
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
    aggregate_rows = aggregate_metric_deltas(metric_deltas, expected_direction, expected_sign)
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
        "run_metric_deltas": run_metric_deltas(rows, metric_names, expected_direction, expected_sign),
        "pair_rows": rows,
        "support_score": float(np.mean(support_components)) if support_components else 0.0,
        "claim_guardrail": "Hierarchy/routing metrics are coarse FC proxies; they do not prove REBUS, precision relaxation, or thalamic gating.",
    }
