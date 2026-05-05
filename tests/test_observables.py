from pathlib import Path

from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import compute_observable_summary
from lsd_thesis.simulator import load_regime_config, run_simulation

ROOT = Path(__file__).resolve().parents[1]


def test_compute_observable_summary_exposes_shared_macro_metrics() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    result = run_simulation(graph, regime)

    summary = compute_observable_summary(result.time_series, graph.modules)

    assert summary.fc_matrix.shape == (8, 8)
    assert summary.metric_map()["within_network_stability"] == summary.within_network_stability
    assert summary.metric_map()["cross_network_communication"] == summary.cross_network_communication
    assert 0.0 <= summary.entropy_diversity <= 1.0
    assert summary.switching_rate >= 0.0
    assert summary.metastability_proxy >= 0.0
    assert summary.effective_barrier_proxy > 0.0
