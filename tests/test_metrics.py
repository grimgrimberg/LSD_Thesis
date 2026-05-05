from pathlib import Path

import pytest

from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import compute_summary_metrics
from lsd_thesis.simulator import load_regime_config, run_simulation

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.slow
def test_summary_metrics_have_expected_shapes_and_ranges() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    result = run_simulation(graph, regime)
    metrics = compute_summary_metrics(result.time_series, graph.modules)

    assert metrics.fc_matrix.shape == (8, 8)
    assert metrics.dynamic_fc_change >= 0.0
    assert 0.0 <= metrics.state_entropy <= 1.0
    assert metrics.switching_rate >= 0.0
