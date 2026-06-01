from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, cast

import numpy as np


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_structural_dti_payload(repo_root: Path) -> dict[str, Any]:
    status_path = repo_root / "results" / "structural_connectome" / "structural_connectome_status.json"
    matrix_path = repo_root / "results" / "structural_connectome" / "hcp_macro_modules.csv"
    fallback_matrix_path = repo_root / "data" / "hcp_structural_connectome" / "macro_modules.csv"
    if not matrix_path.exists() and fallback_matrix_path.exists():
        matrix_path = fallback_matrix_path
    status = cast(dict[str, Any], json.loads(status_path.read_text(encoding="utf-8"))) if status_path.exists() else {}
    rows = _read_csv_rows(matrix_path)
    modules = [str(row.get("module", "")).strip() for row in rows if str(row.get("module", "")).strip()]
    if not rows or not modules:
        return {
            "analysis_status": status.get("analysis_status", "missing_structural_connectome_matrix"),
            "source_path": status_path.relative_to(repo_root).as_posix() if status_path.exists() else None,
            "matrix_path": matrix_path.relative_to(repo_root).as_posix(),
            "modules": [],
            "matrix": [],
            "edges": [],
            "nodes": [],
            "claim_guardrail": (
                "A DTI/tractography dynamics panel requires a macro-module structural-connectome matrix. "
                "It should be interpreted as anatomical coupling context, not drug-effect proof."
            ),
        }

    matrix = []
    for row in rows:
        matrix_row = []
        for module in modules:
            try:
                value = float(row.get(module, 0.0))
            except (TypeError, ValueError):
                value = 0.0
            matrix_row.append(value if math.isfinite(value) else 0.0)
        matrix.append(matrix_row)

    matrix_array = np.asarray(matrix, dtype=float)
    matrix_array = (matrix_array + matrix_array.T) / 2.0
    np.fill_diagonal(matrix_array, 0.0)
    max_weight = float(np.max(matrix_array)) if matrix_array.size else 0.0
    node_strengths = matrix_array.sum(axis=1) if matrix_array.size else np.zeros(len(modules))
    max_strength = float(np.max(node_strengths)) if node_strengths.size else 0.0
    edge_rows: list[dict[str, Any]] = []
    for source_index, source in enumerate(modules):
        for target_index, target in enumerate(modules):
            if source_index >= target_index:
                continue
            weight = float(matrix_array[source_index, target_index])
            if weight <= 0.0:
                continue
            edge_rows.append(
                {
                    "source": source,
                    "target": target,
                    "weight": weight,
                    "normalized_weight": weight / max_weight if max_weight > 0 else 0.0,
                }
            )
    edge_rows = sorted(edge_rows, key=lambda row: float(row["weight"]), reverse=True)
    nodes = []
    for index, module in enumerate(modules):
        angle = 2.0 * math.pi * index / max(len(modules), 1)
        strength = float(node_strengths[index])
        nodes.append(
            {
                "name": module,
                "x": math.cos(angle),
                "y": math.sin(angle),
                "strength": strength,
                "normalized_strength": strength / max_strength if max_strength > 0 else 0.0,
            }
        )
    return {
        "analysis_status": status.get("analysis_status", "structural_matrix_loaded"),
        "source_path": status_path.relative_to(repo_root).as_posix() if status_path.exists() else None,
        "matrix_path": matrix_path.relative_to(repo_root).as_posix(),
        "modules": modules,
        "matrix": matrix_array.tolist(),
        "nodes": nodes,
        "edges": edge_rows,
        "top_edges": edge_rows[:10],
        "module_count": len(modules),
        "edge_count": len(edge_rows),
        "density": len(edge_rows) / max((len(modules) * (len(modules) - 1)) / 2.0, 1.0),
        "strongest_edge": edge_rows[0] if edge_rows else None,
        "claim_guardrail": (
            "DTI/tractography-derived structural connectivity is used here as a dynamics prior: it constrains "
            "which macro-module transitions are anatomically plausible. It is not a raw DTI scan, not a receptor "
            "model, and not evidence by itself that LSD or psilocybin caused the observed dynamics."
        ),
        "dynamic_interpretation": (
            "Read this panel as the structural substrate for network-control and transition-energy questions. "
            "Strong edges are candidate low-cost anatomical routes; weak edges are candidate high-cost routes."
        ),
    }
