"""Tests for multi-seed uncertainty and utils module."""

from pathlib import Path

import pytest

from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import multi_seed_summary
from lsd_thesis.simulator import load_regime_config
from lsd_thesis.utils import confidence_weight, mean_metric_dict

ROOT = Path(__file__).resolve().parents[1]


def test_multi_seed_summary_returns_mean_and_std_for_all_metrics() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    mean_metrics, std_metrics = multi_seed_summary(graph, regime, n_seeds=3, base_seed=0)

    assert set(mean_metrics.keys()) == set(std_metrics.keys())
    for name in mean_metrics:
        assert isinstance(mean_metrics[name], float)
        assert isinstance(std_metrics[name], float)
        assert std_metrics[name] >= 0.0


def test_multi_seed_summary_std_is_nonzero_for_stochastic_metrics() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    _, std_metrics = multi_seed_summary(graph, regime, n_seeds=3, base_seed=0)

    # At least some metrics should vary across seeds
    nonzero_count = sum(1 for v in std_metrics.values() if v > 1e-10)
    assert nonzero_count > 0, "Expected some variance across seeds"


def test_multi_seed_summary_single_seed_reports_zero_uncertainty() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    mean_metrics, std_metrics = multi_seed_summary(graph, regime, n_seeds=1, base_seed=0)

    assert set(mean_metrics.keys()) == set(std_metrics.keys())
    assert mean_metrics
    assert all(value == 0.0 for value in std_metrics.values())


def test_multi_seed_summary_rejects_zero_seed_panel() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    with pytest.raises(ValueError, match="n_seeds"):
        multi_seed_summary(graph, regime, n_seeds=0, base_seed=0)


def test_confidence_weight_returns_expected_values() -> None:
    assert confidence_weight("strong") == 2.0
    assert confidence_weight("weak") == 0.8
    assert confidence_weight("unknown_label") == 1.0


def test_mean_metric_dict_computes_correct_average() -> None:
    rows = [
        {"a": 1.0, "b": 2.0},
        {"a": 3.0, "b": 4.0},
    ]
    result = mean_metric_dict(rows)
    assert result["a"] == 2.0
    assert result["b"] == 3.0
