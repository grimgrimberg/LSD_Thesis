from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from typing import Any, cast

import numpy as np

NodeMetadataLike = Mapping[str, Any] | object


def _as_finite_time_series(time_series: np.ndarray) -> np.ndarray:
    array = np.asarray(time_series, dtype=float)
    if array.ndim != 2:
        raise ValueError("Time series must be shaped as [time, node].")
    if array.shape[0] == 0 or array.shape[1] == 0:
        raise ValueError("Time series must contain at least one time point and one node.")

    finite = np.where(np.isfinite(array), array, np.nan)
    column_means = np.nanmean(finite, axis=0)
    column_means = np.where(np.isfinite(column_means), column_means, 0.0)
    row_indices, column_indices = np.where(~np.isfinite(array))
    if len(row_indices):
        array = array.copy()
        array[row_indices, column_indices] = column_means[column_indices]
    return array


def safe_corrcoef(time_series: np.ndarray) -> np.ndarray:
    """Return a finite correlation matrix for [time, node] data.

    Constant or all-missing channels are assigned zero off-diagonal correlation
    and one on the diagonal. This mirrors the legacy metric guardrail while
    allowing literature-metric code to work with partially cleaned empirical
    extracts.
    """
    array = _as_finite_time_series(time_series)
    node_count = array.shape[1]
    if array.shape[0] < 2:
        return np.eye(node_count, dtype=float)

    centered = array - np.mean(array, axis=0, keepdims=True)
    norms = np.linalg.norm(centered, axis=0)
    denominator = np.outer(norms, norms)
    numerator = centered.T @ centered
    matrix = np.divide(
        numerator,
        denominator,
        out=np.zeros((node_count, node_count), dtype=float),
        where=denominator > 1e-12,
    )
    matrix = np.clip(np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0), -1.0, 1.0)
    np.fill_diagonal(matrix, 1.0)
    return cast(np.ndarray, matrix)


def upper_triangle_vector(matrix: np.ndarray) -> np.ndarray:
    array = np.asarray(matrix, dtype=float)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("Matrix must be square.")
    return np.asarray(array[np.triu_indices(array.shape[0], k=1)], dtype=float)


def _metadata_dict(node: NodeMetadataLike) -> dict[str, Any]:
    if isinstance(node, Mapping):
        return dict(node)
    if is_dataclass(node):
        return dict(asdict(cast(Any, node)))
    values: dict[str, Any] = {}
    for key in (
        "node_label",
        "parcel_index",
        "yeo_network_label",
        "coarse_class",
        "hierarchy_value",
        "visual_weight",
        "sensory_weight",
        "somatomotor_weight",
        "transmodal_weight",
        "thalamus_weight",
        "striatum_weight",
    ):
        if hasattr(node, key):
            values[key] = getattr(node, key)
    return values


def _metadata_rows(node_metadata: Sequence[NodeMetadataLike]) -> list[dict[str, Any]]:
    rows = [_metadata_dict(node) for node in node_metadata]
    if not rows:
        raise ValueError("At least one node metadata row is required.")
    return rows


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(number):
        return default
    return number


def _as_label(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _mask(rows: Sequence[dict[str, Any]], predicate: Any) -> np.ndarray:
    return np.asarray([bool(predicate(row)) for row in rows], dtype=bool)


def _visual_mask(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    return _mask(
        rows,
        lambda row: _as_float(row.get("visual_weight")) > 0.0
        or _as_label(row.get("yeo_network_label")) == "visual"
        or _as_label(row.get("coarse_class")) == "visual",
    )


def _somatomotor_mask(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    return _mask(
        rows,
        lambda row: _as_float(row.get("somatomotor_weight")) > 0.0
        or _as_label(row.get("yeo_network_label")) in {"sommot", "somatomotor"}
        or _as_label(row.get("coarse_class")) in {"somatomotor", "sensorimotor"},
    )


def _sensory_mask(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    visual = _visual_mask(rows)
    somatomotor = _somatomotor_mask(rows)
    explicit = _mask(
        rows,
        lambda row: _as_float(row.get("sensory_weight")) > 0.0
        or _as_label(row.get("coarse_class")) in {"sensory", "auditory"},
    )
    return cast(np.ndarray, visual | somatomotor | explicit)


def _transmodal_mask(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    return _mask(
        rows,
        lambda row: _as_float(row.get("transmodal_weight")) > 0.0
        or _as_label(row.get("yeo_network_label")) in {"default", "cont", "control", "limbic"}
        or _as_label(row.get("coarse_class")) in {"default", "control", "associative", "limbic"},
    )


def _thalamus_mask(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    return _mask(
        rows,
        lambda row: _as_float(row.get("thalamus_weight")) > 0.0
        or "thalam" in _as_label(row.get("node_label"))
        or "thalam" in _as_label(row.get("coarse_class")),
    )


def _striatum_mask(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    return _mask(
        rows,
        lambda row: _as_float(row.get("striatum_weight")) > 0.0
        or "striat" in _as_label(row.get("node_label"))
        or "caudate" in _as_label(row.get("node_label"))
        or "putamen" in _as_label(row.get("node_label"))
        or "striat" in _as_label(row.get("coarse_class")),
    )


def _finite_mean(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if len(finite) == 0:
        return 0.0
    return float(np.mean(finite))


def mean_fc_between_groups(fc_matrix: np.ndarray, source_mask: np.ndarray, target_mask: np.ndarray) -> float:
    fc = np.asarray(fc_matrix, dtype=float)
    if fc.ndim != 2 or fc.shape[0] != fc.shape[1]:
        raise ValueError("FC matrix must be square.")
    source_indices = np.flatnonzero(source_mask)
    target_indices = np.flatnonzero(target_mask)
    if len(source_indices) == 0 or len(target_indices) == 0:
        return 0.0

    values: list[float] = []
    same_group = np.array_equal(source_mask, target_mask)
    for source in source_indices:
        for target in target_indices:
            if source == target:
                continue
            if same_group and target <= source:
                continue
            values.append(float(fc[source, target]))
    return _finite_mean(np.asarray(values, dtype=float))


def mean_fc_within_group(fc_matrix: np.ndarray, group_mask: np.ndarray) -> float:
    return mean_fc_between_groups(fc_matrix, group_mask, group_mask)


def within_network_fc_by_yeo_network(
    fc_matrix: np.ndarray,
    node_metadata: Sequence[NodeMetadataLike],
) -> dict[str, float]:
    rows = _metadata_rows(node_metadata)
    network_labels = sorted(
        {
            str(row["yeo_network_label"])
            for row in rows
            if row.get("yeo_network_label") not in {None, ""}
        }
    )
    values: dict[str, float] = {}
    for network in network_labels:
        group = _mask(rows, lambda row, network=network: str(row.get("yeo_network_label")) == network)
        values[network] = mean_fc_within_group(fc_matrix, group)
    return values


def between_network_fc_matrix(
    fc_matrix: np.ndarray,
    node_metadata: Sequence[NodeMetadataLike],
) -> dict[str, dict[str, float]]:
    rows = _metadata_rows(node_metadata)
    network_labels = sorted(
        {
            str(row["yeo_network_label"])
            for row in rows
            if row.get("yeo_network_label") not in {None, ""}
        }
    )
    output: dict[str, dict[str, float]] = {}
    for source in network_labels:
        source_mask = _mask(rows, lambda row, source=source: str(row.get("yeo_network_label")) == source)
        output[source] = {}
        for target in network_labels:
            target_mask = _mask(rows, lambda row, target=target: str(row.get("yeo_network_label")) == target)
            if source == target:
                output[source][target] = mean_fc_within_group(fc_matrix, source_mask)
            else:
                output[source][target] = mean_fc_between_groups(fc_matrix, source_mask, target_mask)
    return output


def hierarchy_differentiation(
    fc_matrix: np.ndarray,
    node_metadata: Sequence[NodeMetadataLike],
) -> float:
    rows = _metadata_rows(node_metadata)
    sensory = _sensory_mask(rows)
    transmodal = _transmodal_mask(rows)
    within_values = [
        mean_fc_within_group(fc_matrix, sensory),
        mean_fc_within_group(fc_matrix, transmodal),
    ]
    cross_value = mean_fc_between_groups(fc_matrix, sensory, transmodal)
    return _finite_mean(np.asarray(within_values, dtype=float)) - cross_value


def gradient_flattening_delta(
    baseline_fc: np.ndarray,
    condition_fc: np.ndarray,
    node_metadata: Sequence[NodeMetadataLike],
) -> float:
    """Return positive values when hierarchy differentiation decreases."""
    return hierarchy_differentiation(baseline_fc, node_metadata) - hierarchy_differentiation(
        condition_fc,
        node_metadata,
    )


def state_occupancy_entropy(labels: np.ndarray) -> float:
    sequence = np.asarray(labels, dtype=int)
    if len(sequence) == 0:
        return 0.0
    counts = np.bincount(sequence - int(np.min(sequence)))
    counts = counts[counts > 0]
    if len(counts) <= 1:
        return 0.0
    probabilities = counts / counts.sum()
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    denominator = float(np.log(len(counts)))
    if denominator <= 1e-12:
        return 0.0
    return float(entropy / denominator)


def transition_entropy(labels: np.ndarray) -> float:
    sequence = np.asarray(labels, dtype=int)
    if len(sequence) < 2:
        return 0.0
    transitions = list(zip(sequence[:-1], sequence[1:], strict=False))
    counts = np.asarray(list(Counter(transitions).values()), dtype=float)
    if len(counts) == 0:
        return 0.0
    probabilities = counts / counts.sum()
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    state_count = len(np.unique(sequence))
    denominator = float(np.log(max(state_count * state_count, 2)))
    return 0.0 if denominator <= 1e-12 else float(entropy / denominator)


def transition_rate(labels: np.ndarray) -> float:
    sequence = np.asarray(labels, dtype=int)
    if len(sequence) < 2:
        return 0.0
    return float(np.mean(np.diff(sequence) != 0))


def _state_labels_from_timeseries(time_series: np.ndarray) -> np.ndarray:
    array = _as_finite_time_series(time_series)
    if len(array) == 0:
        return np.asarray([], dtype=int)
    centered = array - np.mean(array, axis=0, keepdims=True)
    if np.linalg.norm(centered) <= 1e-12:
        return np.zeros(len(array), dtype=int)
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    scores = centered @ vh[0]
    if np.max(scores) - np.min(scores) <= 1e-12:
        return np.zeros(len(scores), dtype=int)
    thresholds = np.quantile(scores, [0.25, 0.50, 0.75])
    return np.asarray(np.digitize(scores, thresholds, right=False), dtype=int)


def dynamic_fc_variance(time_series: np.ndarray, window_size: int | None = None) -> float:
    array = _as_finite_time_series(time_series)
    if window_size is None:
        window_size = max(20, min(80, len(array) // 4))
    if window_size < 4 or len(array) < window_size * 2:
        return 0.0
    step = max(1, window_size // 2)
    vectors: list[np.ndarray] = []
    for start in range(0, len(array) - window_size + 1, step):
        vectors.append(upper_triangle_vector(safe_corrcoef(array[start : start + window_size])))
    if len(vectors) < 2:
        return 0.0
    return float(np.mean(np.var(np.vstack(vectors), axis=0)))


def fc_to_sc_coupling(fc_matrix: np.ndarray, structural_connectivity: np.ndarray | None) -> float | None:
    if structural_connectivity is None:
        return None
    fc_vector = upper_triangle_vector(fc_matrix)
    sc_vector = upper_triangle_vector(np.asarray(structural_connectivity, dtype=float))
    valid = np.isfinite(fc_vector) & np.isfinite(sc_vector)
    if np.sum(valid) < 2 or np.std(fc_vector[valid]) <= 1e-12 or np.std(sc_vector[valid]) <= 1e-12:
        return 0.0
    return float(np.corrcoef(fc_vector[valid], sc_vector[valid])[0, 1])


def compute_literature_metrics(
    time_series: np.ndarray,
    node_metadata: Sequence[NodeMetadataLike],
    structural_connectivity: np.ndarray | None = None,
    window_size: int | None = None,
) -> dict[str, Any]:
    rows = _metadata_rows(node_metadata)
    array = _as_finite_time_series(time_series)
    if array.shape[1] != len(rows):
        raise ValueError("Time-series node count must match node metadata length.")

    fc_matrix = safe_corrcoef(array)
    sensory = _sensory_mask(rows)
    visual = _visual_mask(rows)
    somatomotor = _somatomotor_mask(rows)
    transmodal = _transmodal_mask(rows)
    thalamus = _thalamus_mask(rows)
    striatum = _striatum_mask(rows)
    labels = _state_labels_from_timeseries(array)
    hierarchy_value = hierarchy_differentiation(fc_matrix, rows)

    metrics: dict[str, Any] = {
        "global_mean_fc": _finite_mean(upper_triangle_vector(fc_matrix)),
        "unimodal_transmodal_fc": mean_fc_between_groups(fc_matrix, sensory, transmodal),
        "visual_global_connectivity": mean_fc_between_groups(fc_matrix, visual, ~visual),
        "sensory_somatomotor_global_connectivity": mean_fc_between_groups(
            fc_matrix,
            sensory | somatomotor,
            ~(sensory | somatomotor),
        ),
        "within_network_fc_by_yeo_network": within_network_fc_by_yeo_network(fc_matrix, rows),
        "between_network_fc_matrix": between_network_fc_matrix(fc_matrix, rows),
        "thalamus_to_sensory_fc": mean_fc_between_groups(fc_matrix, thalamus, sensory),
        "thalamus_to_transmodal_fc": mean_fc_between_groups(fc_matrix, thalamus, transmodal),
        "striatum_to_sensory_fc": mean_fc_between_groups(fc_matrix, striatum, sensory),
        "hierarchy_differentiation": hierarchy_value,
        "gradient_flattening_delta": 0.0,
        "state_occupancy_entropy": state_occupancy_entropy(labels),
        "transition_entropy": transition_entropy(labels),
        "transition_rate": transition_rate(labels),
        "dynamic_fc_variance": dynamic_fc_variance(array, window_size=window_size),
        "fc_to_sc_coupling": fc_to_sc_coupling(fc_matrix, structural_connectivity),
    }
    return metrics
