from __future__ import annotations

import math
from typing import Any, Literal

import networkx as nx
import numpy as np
from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from lsd_thesis.core import MODULE_GROUPS, GraphConfig, RegimeConfig
from lsd_thesis.metrics import compute_observable_summary
from lsd_thesis.simulator import run_simulation


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    regime: Literal["baseline", "perturbed"] = "baseline"
    within_group_scale: float | None = None
    cross_group_scale: float | None = None
    constraint_scale: float | None = None
    rigidity: float | None = None
    barrier: float | None = None
    temperature: float | None = None
    tau: float | None = None

    @field_validator(
        "within_group_scale",
        "cross_group_scale",
        "constraint_scale",
        "rigidity",
        "barrier",
        "temperature",
        "tau",
        mode="before",
    )
    @classmethod
    def _validate_numeric_parameter(cls, value: float | None, info: ValidationInfo) -> float | None:
        if value is None:
            return None
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Parameter must be finite.")
        field_name = str(info.field_name)
        if field_name == "constraint_scale":
            if number < 0.0:
                raise ValueError("constraint_scale must be non-negative.")
        elif number <= 0.0:
            raise ValueError("Parameter must be positive.")
        if field_name == "tau" and number < 0.05:
            raise ValueError("tau is too small for stable interactive simulation (min 0.05).")
        if number > 100.0:
            raise ValueError("Parameter too large (max 100).")
        return number


def graph_payload(graph: GraphConfig) -> dict[str, Any]:
    network = nx.Graph()
    for module in graph.modules:
        network.add_node(module)
    for i, source in enumerate(graph.modules):
        for j, target in enumerate(graph.modules):
            if i < j and graph.adjacency[i, j] != 0:
                network.add_edge(source, target, weight=float(graph.adjacency[i, j]))
    positions = nx.spring_layout(network, seed=9, weight="weight")

    return {
        "nodes": [
            {
                "name": module,
                "x": float(positions[module][0]),
                "y": float(positions[module][1]),
                "group": MODULE_GROUPS[module],
            }
            for module in graph.modules
        ],
        "edges": [
            {"source": source, "target": target, "weight": float(data["weight"])}
            for source, target, data in network.edges(data=True)
        ],
    }


def build_simulation_payload(graph: GraphConfig, regime: RegimeConfig) -> dict[str, Any]:
    result = run_simulation(graph, regime)
    if not np.all(np.isfinite(result.time_series)):
        raise ValueError("Simulation produced non-finite values; check regime parameters.")
    observable = compute_observable_summary(result.time_series, graph.modules)
    return {
        "time": result.time.tolist(),
        "modules": list(graph.modules),
        "time_series": result.time_series.tolist(),
        "fc_matrix": observable.fc_matrix.tolist(),
        "metrics": observable.metric_map(),
    }
