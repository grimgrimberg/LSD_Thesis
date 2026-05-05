from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

from lsd_thesis.core import MODULE_GROUPS, GraphConfig, RegimeConfig, SimulationResult


def load_regime_config(path: str | Path) -> RegimeConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)
    return RegimeConfig.model_validate(raw)


def build_effective_coupling_matrix(graph: GraphConfig, regime: RegimeConfig) -> np.ndarray:
    module_count = len(graph.modules)
    within_mask = np.zeros((module_count, module_count), dtype=float)
    cross_mask = np.zeros((module_count, module_count), dtype=float)

    for row_index, source in enumerate(graph.modules):
        for column_index, target in enumerate(graph.modules):
            if row_index == column_index:
                continue
            if MODULE_GROUPS[source] == MODULE_GROUPS[target]:
                within_mask[row_index, column_index] = 1.0
            else:
                cross_mask[row_index, column_index] = 1.0

    return (
        graph.adjacency * within_mask * regime.global_parameters.within_group_scale
        + graph.adjacency * cross_mask * regime.global_parameters.cross_group_scale
    )


def run_simulation(graph: GraphConfig, regime: RegimeConfig) -> SimulationResult:
    parameters = regime.parameters_for_modules(graph.modules)
    settings = regime.simulation
    rng = np.random.default_rng(settings.seed)
    effective_coupling = build_effective_coupling_matrix(graph, regime)

    module_count = len(graph.modules)
    state = rng.normal(loc=0.0, scale=0.05, size=module_count)
    adaptation = np.zeros(module_count, dtype=float)
    traces = np.zeros((settings.steps, module_count), dtype=float)

    for step in range(settings.steps):
        local_drive = parameters["barrier"] * (state - state**3)
        local_drive -= parameters["rigidity"] * (state - parameters["baseline_state"])
        local_drive -= parameters["adaptation_gain"] * adaptation

        cross_drive = parameters["coupling_scale"] * (effective_coupling @ np.tanh(state))
        constraint_drive = parameters["constraint_scale"] * (
            (graph.hierarchy_projection @ state) - state
        )

        drift = (local_drive + cross_drive + constraint_drive) / parameters["tau"]
        noise = parameters["temperature"] * rng.normal(size=module_count) * np.sqrt(settings.dt)

        state = state + settings.dt * drift + noise
        adaptation = adaptation + settings.dt * (
            (state - adaptation) / parameters["adaptation_tau"]
        )
        traces[step] = state

    kept = traces[settings.burn_in :]
    time = np.arange(len(kept), dtype=float) * settings.dt
    return SimulationResult(
        regime_name=regime.name,
        module_names=graph.modules,
        time=time,
        time_series=kept,
    )
