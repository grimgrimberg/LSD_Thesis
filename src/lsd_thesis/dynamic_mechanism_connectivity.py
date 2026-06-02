from __future__ import annotations

import math
from typing import cast

import numpy as np

from lsd_thesis.metrics_literature import safe_corrcoef, upper_triangle_vector


def finite_mean(values: list[float] | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    finite = array[np.isfinite(array)]
    return float(np.mean(finite)) if len(finite) else 0.0


def safe_vector_correlation(first: np.ndarray, second: np.ndarray) -> float:
    left = np.asarray(first, dtype=float)
    right = np.asarray(second, dtype=float)
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    if np.std(left) <= 1e-12 or np.std(right) <= 1e-12:
        return 0.0
    value = float(np.corrcoef(left, right)[0, 1])
    return value if math.isfinite(value) else 0.0


def mean_between(fc_matrix: np.ndarray, source_mask: np.ndarray, target_mask: np.ndarray) -> float:
    source = np.asarray(source_mask, dtype=bool)
    target = np.asarray(target_mask, dtype=bool)
    source_indices = np.flatnonzero(source)
    target_indices = np.flatnonzero(target)
    if len(source_indices) == 0 or len(target_indices) == 0:
        return 0.0
    same_group = np.array_equal(source, target)
    values: list[float] = []
    for source_index in source_indices:
        for target_index in target_indices:
            if source_index == target_index:
                continue
            if same_group and target_index <= source_index:
                continue
            values.append(float(fc_matrix[source_index, target_index]))
    return finite_mean(values)


def mean_within(fc_matrix: np.ndarray, mask: np.ndarray) -> float:
    return mean_between(fc_matrix, mask, mask)


def mean_between_networks(fc_matrix: np.ndarray, masks: dict[str, np.ndarray]) -> float:
    values = [
        mean_between(fc_matrix, masks["sensory"], masks["transmodal"]),
        mean_between(fc_matrix, masks["sensory"], masks["gateway"]),
        mean_between(fc_matrix, masks["transmodal"], masks["gateway"]),
    ]
    return finite_mean(values)


def mean_within_networks(fc_matrix: np.ndarray, masks: dict[str, np.ndarray]) -> float:
    values = [
        mean_within(fc_matrix, masks["sensory"]),
        mean_within(fc_matrix, masks["transmodal"]),
    ]
    return finite_mean(values)


def fc_path_length(time_series: np.ndarray, window_size: int | None = None) -> float:
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


def positive_fc_graph(fc_matrix: np.ndarray) -> np.ndarray:
    matrix = np.maximum(np.asarray(fc_matrix, dtype=float), 0.0)
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 0.0)
    return cast(np.ndarray, matrix)


def community_labels(masks: dict[str, np.ndarray]) -> np.ndarray:
    labels = np.full(len(masks["all"]), 3, dtype=int)
    labels[masks["sensory"]] = 0
    labels[masks["transmodal"]] = 1
    labels[masks["gateway"]] = 2
    return labels


def weighted_modularity(matrix: np.ndarray, community_labels: np.ndarray) -> float:
    graph = positive_fc_graph(matrix)
    total_weight = float(np.sum(graph))
    if total_weight <= 1e-12:
        return 0.0
    degree = np.sum(graph, axis=1)
    expected = np.outer(degree, degree) / total_weight
    same_community = community_labels[:, None] == community_labels[None, :]
    return float(np.sum((graph - expected) * same_community) / total_weight)


def mean_participation_coefficient(matrix: np.ndarray, community_labels: np.ndarray) -> float:
    graph = positive_fc_graph(matrix)
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
    return finite_mean(coefficients)


def global_efficiency(matrix: np.ndarray) -> float:
    graph = positive_fc_graph(matrix)
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
