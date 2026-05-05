from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

from lsd_thesis.core import MODULE_NAMES, GraphConfig


def _matrix_from_mapping(
    modules: tuple[str, ...],
    mapping: dict[str, dict[str, float]],
) -> np.ndarray:
    matrix = np.zeros((len(modules), len(modules)), dtype=float)
    for row_index, source in enumerate(modules):
        for column_index, target in enumerate(modules):
            matrix[row_index, column_index] = float(mapping[source][target])
    return matrix


def load_graph_config(path: str | Path) -> GraphConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)

    modules = tuple(raw["modules"])
    if modules != MODULE_NAMES:
        raise ValueError(f"Expected canonical module ordering {MODULE_NAMES}, got {modules}")

    adjacency = _matrix_from_mapping(modules, raw["adjacency"])
    hierarchy_projection = _matrix_from_mapping(modules, raw["hierarchy_projection"])
    return GraphConfig(
        modules=modules,
        adjacency=adjacency,
        hierarchy_projection=hierarchy_projection,
    )
