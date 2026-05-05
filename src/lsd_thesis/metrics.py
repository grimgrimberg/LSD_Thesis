from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from sklearn.cluster import KMeans

from lsd_thesis.core import MODULE_GROUPS, ObservableSummary, SummaryMetrics

if TYPE_CHECKING:
    from lsd_thesis.core import GraphConfig, RegimeConfig


def _upper_triangle(matrix: np.ndarray) -> np.ndarray:
    indices = np.triu_indices_from(matrix, k=1)
    return matrix[indices]


def safe_correlation_matrix(time_series: np.ndarray) -> np.ndarray:
    """Return a finite module correlation matrix, using zero correlation for constant channels."""
    if time_series.ndim != 2:
        raise ValueError("Time series must be shaped as [time, module].")
    module_count = time_series.shape[1]
    if len(time_series) < 2:
        return np.eye(module_count, dtype=float)

    centered = time_series - np.mean(time_series, axis=0, keepdims=True)
    norms = np.linalg.norm(centered, axis=0)
    denominator = np.outer(norms, norms)
    numerator = centered.T @ centered
    matrix = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator, dtype=float),
        where=denominator > 1e-12,
    )
    np.fill_diagonal(matrix, 1.0)
    return np.asarray(matrix, dtype=float)


def _sliding_window_fc_change(time_series: np.ndarray, window_size: int) -> float:
    if len(time_series) < window_size * 2:
        return 0.0

    vectors: list[np.ndarray] = []
    for start in range(0, len(time_series) - window_size + 1, window_size // 2):
        window_fc = safe_correlation_matrix(time_series[start : start + window_size])
        vectors.append(_upper_triangle(window_fc))

    if len(vectors) < 2:
        return 0.0

    deltas = [
        np.linalg.norm(current - previous)
        for previous, current in zip(vectors, vectors[1:], strict=False)
    ]
    return float(np.mean(deltas))


def _cluster_state_sequence(time_series: np.ndarray, cluster_count: int = 4) -> np.ndarray:
    unique_state_count = np.unique(time_series, axis=0).shape[0]
    if unique_state_count <= 1:
        return np.zeros(len(time_series), dtype=int)
    effective_clusters = max(2, min(cluster_count, len(time_series), unique_state_count))
    model = KMeans(n_clusters=effective_clusters, random_state=0, n_init=10)
    return np.asarray(model.fit_predict(time_series), dtype=int)


def _mean_fc_by_relation(fc_matrix: np.ndarray, modules: tuple[str, ...]) -> tuple[float, float]:
    within_values: list[float] = []
    cross_values: list[float] = []
    for i, source in enumerate(modules):
        for j, target in enumerate(modules):
            if j <= i:
                continue
            if MODULE_GROUPS[source] == MODULE_GROUPS[target]:
                within_values.append(float(fc_matrix[i, j]))
            else:
                cross_values.append(float(fc_matrix[i, j]))
    return float(np.mean(within_values)), float(np.mean(cross_values))


def _mean_dwell_time(labels: np.ndarray) -> float:
    change_points = np.where(np.diff(labels) != 0)[0] + 1
    boundaries = np.concatenate(([0], change_points, [len(labels)]))
    lengths = np.diff(boundaries)
    return float(np.mean(lengths))


def _safe_correlation(x: np.ndarray, y: np.ndarray) -> float:
    if np.std(x) < 1e-8 or np.std(y) < 1e-8:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def compute_summary_metrics(time_series: np.ndarray, modules: tuple[str, ...]) -> SummaryMetrics:
    if time_series.ndim != 2 or time_series.shape[1] != len(modules):
        raise ValueError("Time series must be shaped as [time, module].")

    fc_matrix = safe_correlation_matrix(time_series)
    window_size = max(40, min(120, len(time_series) // 4))
    dynamic_fc_change = _sliding_window_fc_change(time_series, window_size=window_size)

    labels = _cluster_state_sequence(time_series)
    counts = np.bincount(labels)
    probabilities = counts / counts.sum()
    entropy = -np.sum(probabilities * np.log(probabilities + 1e-12))
    entropy_denominator = np.log(len(probabilities))
    normalized_entropy = 0.0 if entropy_denominator < 1e-12 else float(entropy / entropy_denominator)
    switching_rate = float(np.mean(np.diff(labels) != 0))

    return SummaryMetrics(
        fc_matrix=fc_matrix,
        dynamic_fc_change=dynamic_fc_change,
        state_entropy=normalized_entropy,
        switching_rate=switching_rate,
        state_labels=labels,
    )


def compute_observable_summary(time_series: np.ndarray, modules: tuple[str, ...]) -> ObservableSummary:
    summary_metrics = compute_summary_metrics(time_series, modules)
    within_fc, cross_fc = _mean_fc_by_relation(summary_metrics.fc_matrix, modules)

    thalamic_index = modules.index("thalamic_gateway")
    thalamic_row = np.delete(summary_metrics.fc_matrix[thalamic_index], thalamic_index)
    sensory_indices = [index for index, name in enumerate(modules) if MODULE_GROUPS[name] == "sensory"]
    associative_indices = [index for index, name in enumerate(modules) if MODULE_GROUPS[name] == "associative"]
    sensory_signal = time_series[:, sensory_indices].mean(axis=1)
    associative_signal = time_series[:, associative_indices].mean(axis=1)

    return ObservableSummary(
        fc_matrix=summary_metrics.fc_matrix,
        within_network_stability=within_fc,
        cross_network_communication=cross_fc,
        thalamic_coupling=float(np.mean(thalamic_row)),
        hierarchical_compression=_safe_correlation(sensory_signal, associative_signal),
        entropy_diversity=summary_metrics.state_entropy,
        switching_rate=summary_metrics.switching_rate,
        metastability_proxy=summary_metrics.dynamic_fc_change,
        effective_barrier_proxy=_mean_dwell_time(summary_metrics.state_labels),
        state_labels=summary_metrics.state_labels,
    )


def multi_seed_summary(
    graph: GraphConfig,
    regime: RegimeConfig,
    n_seeds: int = 5,
    base_seed: int = 0,
) -> tuple[dict[str, float], dict[str, float]]:
    """Run *n_seeds* simulations and return (mean_metrics, std_metrics).

    Requires lazy imports to avoid circular dependencies (metrics ↔ simulator).
    """
    from lsd_thesis.simulator import run_simulation

    metric_rows: list[dict[str, float]] = []
    for offset in range(n_seeds):
        variant = regime.model_copy(deep=True)
        variant.simulation.seed = base_seed + offset
        result = run_simulation(graph, variant)
        observable = compute_observable_summary(result.time_series, graph.modules)
        metric_rows.append(observable.metric_map())

    metric_names = list(metric_rows[0].keys())
    mean_metrics = {
        name: float(np.mean([row[name] for row in metric_rows]))
        for name in metric_names
    }
    std_metrics = {
        name: float(np.std([row[name] for row in metric_rows], ddof=1))
        for name in metric_names
    }
    return mean_metrics, std_metrics
