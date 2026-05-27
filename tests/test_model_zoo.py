from pathlib import Path

import numpy as np
import pytest

from lsd_thesis.graph import load_graph_config
from lsd_thesis.simulator import load_regime_config, run_simulation

ROOT = Path(__file__).resolve().parents[1]


def test_registry_returns_bistable_model() -> None:
    from lsd_thesis.models.bistable import BistableModel
    from lsd_thesis.models.registry import get_model

    model = get_model("bistable")

    assert isinstance(model, BistableModel)
    assert model.model_name == "bistable"


def test_registry_accepts_legacy_bistable_alias() -> None:
    from lsd_thesis.models.registry import get_model

    assert get_model("legacy_bistable").model_name == "bistable"


def test_registry_unknown_model_raises_helpful_error() -> None:
    from lsd_thesis.models.registry import get_model

    with pytest.raises(ValueError, match="Unknown model 'missing_model'. Available models:"):
        get_model("missing_model")


def test_bistable_wrapper_matches_legacy_simulator_output() -> None:
    from lsd_thesis.models.bistable import BistableModel

    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    wrapped = BistableModel(graph=graph, regime=regime).simulate()
    legacy = run_simulation(graph, regime)

    assert wrapped.model_name == "bistable"
    assert wrapped.node_labels == graph.modules
    assert wrapped.dt == regime.simulation.dt
    assert wrapped.seed == regime.simulation.seed
    assert wrapped.bold is None
    assert wrapped.activity.shape == legacy.time_series.shape
    assert np.allclose(wrapped.activity, legacy.time_series)
    assert wrapped.node_metadata["visual"]["group"] == "sensory"


def test_bistable_wrapper_seed_override_is_deterministic() -> None:
    from lsd_thesis.models.bistable import BistableModel

    model = BistableModel()

    result_a = model.simulate(seed=123)
    result_b = model.simulate(seed=123)
    result_c = model.simulate(seed=124)

    assert np.allclose(result_a.activity, result_b.activity)
    assert not np.allclose(result_a.activity, result_c.activity)

