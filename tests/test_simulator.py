from pathlib import Path

import numpy as np

from lsd_thesis.graph import load_graph_config
from lsd_thesis.simulator import (
    build_effective_coupling_matrix,
    load_regime_config,
    run_simulation,
)

ROOT = Path(__file__).resolve().parents[1]


def test_seeded_simulation_is_deterministic() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    result_a = run_simulation(graph, regime)
    result_b = run_simulation(graph, regime)

    assert np.allclose(result_a.time_series, result_b.time_series)


def test_changing_seed_changes_trajectory() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    altered = regime.model_copy(deep=True)
    altered.simulation.seed = regime.simulation.seed + 1

    baseline = run_simulation(graph, regime)
    changed = run_simulation(graph, altered)

    assert not np.allclose(baseline.time_series, changed.time_series)


def test_effective_coupling_matrix_separates_within_and_cross_group_edges() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    coupling = build_effective_coupling_matrix(graph, regime)
    visual_index = graph.modules.index("visual")
    auditory_index = graph.modules.index("auditory")
    default_mode_index = graph.modules.index("default_mode")

    assert coupling[visual_index, auditory_index] == (
        graph.adjacency[visual_index, auditory_index] * regime.global_parameters.within_group_scale
    )
    assert coupling[visual_index, default_mode_index] == (
        graph.adjacency[visual_index, default_mode_index]
        * regime.global_parameters.cross_group_scale
    )
