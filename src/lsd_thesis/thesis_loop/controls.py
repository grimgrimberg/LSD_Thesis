from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, cast

import numpy as np

from lsd_thesis.dynamic_mechanism.core import summarize_network_control_energy

from .status import _load_json


def _matrix_from_csv(path: Path, modules: tuple[str, ...]) -> tuple[np.ndarray, str]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
    if not rows:
        raise ValueError(f"Graph CSV is empty: {path}")
    if {"source", "target", "weight"}.issubset(rows[0]):
        index = {module: idx for idx, module in enumerate(modules)}
        matrix = np.zeros((len(modules), len(modules)), dtype=float)
        for row in rows:
            source = str(row["source"])
            target = str(row["target"])
            if source not in index or target not in index:
                continue
            weight = float(row["weight"])
            matrix[index[source], index[target]] = weight
            matrix[index[target], index[source]] = weight
        return matrix, "edge_list"

    header_modules = [module for module in modules if module in rows[0]]
    if "module" in rows[0] and len(header_modules) == len(modules):
        row_by_module = {str(row["module"]): row for row in rows}
        matrix = np.asarray(
            [[float(row_by_module[source][target]) for target in modules] for source in modules],
            dtype=float,
        )
        return matrix, "square_matrix"
    raise ValueError(
        "Graph CSV must either contain source,target,weight columns or module plus one column per module."
    )

def _prior_vector_from_csv(path: Path, modules: tuple[str, ...]) -> tuple[np.ndarray, str]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
    by_module = {str(row.get("module")): row for row in rows}
    values: list[float] = []
    sources: set[str] = set()
    for module in modules:
        row = by_module.get(module)
        if row is None:
            raise ValueError(f"Receptor prior CSV is missing module '{module}'.")
        values.append(float(row.get("receptor_weight", row.get("weight", 0.0))))
        if row.get("source"):
            sources.add(str(row["source"]))
    source = "; ".join(sorted(sources)) if sources else path.as_posix()
    return np.asarray(values, dtype=float), source

def _metric_lookup(control: dict[str, Any]) -> dict[str, float]:
    return {
        str(row.get("metric")): float(row.get("mean_delta", 0.0))
        for row in control.get("metric_deltas", [])
    }

def _graph_control_row(label: str, control: dict[str, Any], *, rewire_index: int | None = None) -> dict[str, Any]:
    metrics = _metric_lookup(control)
    row = {
        "graph_control": label,
        "rewire_index": rewire_index,
        "support_score": float(control.get("support_score", 0.0)),
        "graph_source": control.get("graph_source", ""),
        "receptor_vs_random_energy_reduction_pct": metrics.get("receptor_vs_random_energy_reduction_pct"),
        "receptor_vs_uniform_energy_reduction_pct": metrics.get("receptor_vs_uniform_energy_reduction_pct"),
        "lsd_vs_placebo_receptor_transition_energy_reduction_pct": metrics.get(
            "lsd_vs_placebo_receptor_transition_energy_reduction_pct"
        ),
        "state_target_alignment_receptor": metrics.get("state_target_alignment_receptor"),
    }
    return row

def _uniform_graph_like(matrix: np.ndarray) -> np.ndarray:
    graph = np.maximum(np.asarray(matrix, dtype=float), 0.0)
    n = graph.shape[0]
    upper = graph[np.triu_indices(n, k=1)]
    positive_mean = float(np.mean(upper[upper > 0.0])) if np.any(upper > 0.0) else 1.0
    output = np.full((n, n), positive_mean, dtype=float)
    np.fill_diagonal(output, 0.0)
    return output

def _degree_expected_graph(matrix: np.ndarray) -> np.ndarray:
    graph = np.maximum(np.asarray(matrix, dtype=float), 0.0)
    degree = np.sum(graph, axis=1)
    total = float(np.sum(degree))
    if total <= 1e-12:
        return _uniform_graph_like(graph)
    output = np.outer(degree, degree) / total
    np.fill_diagonal(output, 0.0)
    return output

def _rewired_weight_graph(matrix: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    graph = np.maximum(np.asarray(matrix, dtype=float), 0.0)
    n = graph.shape[0]
    upper_indices = np.triu_indices(n, k=1)
    weights = np.asarray(graph[upper_indices], dtype=float)
    shuffled = rng.permutation(weights)
    output = np.zeros_like(graph, dtype=float)
    output[upper_indices] = shuffled
    output = output + output.T
    return cast(np.ndarray, output)

def _build_graph_control_rows(
    pairs: list[Any],
    graph_matrix: np.ndarray,
    *,
    primary_label: str,
    graph_source_note: str,
    rewire_source_note: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    controls = {
        primary_label: graph_matrix,
        "uniform_weight_graph": _uniform_graph_like(graph_matrix),
        "degree_expected_graph": _degree_expected_graph(graph_matrix),
    }
    for label, matrix in controls.items():
        control = summarize_network_control_energy(
            pairs,
            graph_matrix_override=matrix,
            graph_source_override=f"{label}; {graph_source_note}",
            random_null_count=16,
        )
        rows.append(_graph_control_row(label, control))
    rng = np.random.default_rng(20260520)
    for rewire_index in range(16):
        control = summarize_network_control_energy(
            pairs,
            graph_matrix_override=_rewired_weight_graph(graph_matrix, rng),
            graph_source_override=rewire_source_note,
            random_null_count=8,
        )
        rows.append(_graph_control_row("edge_weight_rewire_null", control, rewire_index=rewire_index))
    return rows

def _build_proxy_graph_control_rows(pairs: list[Any], graph_matrix: np.ndarray) -> list[dict[str, Any]]:
    return _build_graph_control_rows(
        pairs,
        graph_matrix,
        primary_label="macro_proxy_graph",
        graph_source_note="proxy graph control, not HCP structural connectome",
        rewire_source_note="rewired macro-proxy edge-weight null; not HCP structural connectome",
    )

def _build_structural_graph_control_rows(
    pairs: list[Any], graph_matrix: np.ndarray, *, graph_path: Path
) -> list[dict[str, Any]]:
    return _build_graph_control_rows(
        pairs,
        graph_matrix,
        primary_label="hcp_structural_graph",
        graph_source_note=f"HCP/normative structural graph sensitivity from {graph_path.as_posix()}",
        rewire_source_note=(
            "rewired HCP/normative structural edge-weight null; preserves the edge-weight distribution "
            "but not the original graph topology"
        ),
    )

def _coarse_receptor_null_rows(repo_root: Path, pairs: list[Any]) -> list[dict[str, Any]]:
    summary = _load_json(repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json")
    control = (
        summary.get("network_control_energy", {})
        if isinstance(summary, dict)
        else summarize_network_control_energy(pairs, random_null_count=32)
    )
    rows = []
    for row in control.get("metric_deltas", []):
        metric = str(row.get("metric", ""))
        null_family = "spatial_null_missing"
        if "uniform" in metric:
            null_family = "uniform_control"
        elif "random" in metric:
            null_family = "random_permutation"
        elif "degree" in metric:
            null_family = "degree_control"
        elif "receptor" in metric:
            null_family = "coarse_receptor_proxy"
        rows.append(
            {
                "metric": metric,
                "mean_delta": row.get("mean_delta"),
                "signed_effect_size": row.get("signed_effect_size"),
                "expected_direction": row.get("expected_direction"),
                "null_family": null_family,
                "prior_source": control.get("receptor_prior_source"),
                "claim_status": "proxy_only_not_pet_receptor_claim",
            }
        )
    rows.append(
        {
            "metric": "spatial_autocorrelation_preserving_null",
            "mean_delta": None,
            "signed_effect_size": None,
            "expected_direction": "PET-derived receptor map should outperform spatial nulls",
            "null_family": "spatial_null_missing",
            "prior_source": "missing PET receptor map",
            "claim_status": "blocked_until_neuromaps_or_FS5ht_projection_exists",
        }
    )
    return rows
