from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from lsd_thesis.core import MODULE_GROUPS, GraphConfig, RegimeConfig
from lsd_thesis.graph import load_graph_config
from lsd_thesis.models.base import SimulationResult
from lsd_thesis.simulator import load_regime_config, run_simulation

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GRAPH_PATH = REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml"
DEFAULT_REGIME_PATH = REPO_ROOT / "configs" / "regimes" / "baseline.yaml"


class BistableModel:
    """Adapter for the legacy eight-module bistable surrogate."""

    model_name = "bistable"

    def __init__(
        self,
        graph: GraphConfig | None = None,
        regime: RegimeConfig | None = None,
        graph_path: str | Path = DEFAULT_GRAPH_PATH,
        regime_path: str | Path = DEFAULT_REGIME_PATH,
    ) -> None:
        self.graph_path = Path(graph_path)
        self.regime_path = Path(regime_path)
        self.graph = graph or load_graph_config(self.graph_path)
        self.regime = regime or load_regime_config(self.regime_path)

    def simulate(self, config: dict[str, Any] | None = None, seed: int | None = None) -> SimulationResult:
        resolved_graph = self.graph
        resolved_regime = self.regime.model_copy(deep=True)
        config_payload = self._config_payload()
        if config:
            if graph_path := config.get("graph_path"):
                resolved_graph = load_graph_config(Path(str(graph_path)))
                config_payload["graph_path"] = str(graph_path)
            if regime_path := config.get("regime_path"):
                resolved_regime = load_regime_config(Path(str(regime_path)))
                config_payload["regime_path"] = str(regime_path)
            config_payload["overrides"] = dict(config)
        if seed is not None:
            resolved_regime.simulation.seed = seed
            config_payload["seed_override"] = seed

        legacy_result = run_simulation(resolved_graph, resolved_regime)
        return SimulationResult(
            activity=np.asarray(legacy_result.time_series, dtype=float),
            bold=None,
            node_labels=tuple(legacy_result.module_names),
            node_metadata={
                name: {
                    "group": MODULE_GROUPS.get(name, "unknown"),
                    "legacy_module": True,
                }
                for name in legacy_result.module_names
            },
            dt=resolved_regime.simulation.dt,
            seed=resolved_regime.simulation.seed,
            model_name=self.model_name,
            config=config_payload,
            provenance={
                "source": "src/lsd_thesis/simulator.py",
                "legacy_regime_name": legacy_result.regime_name,
                "baseline_model": True,
            },
        )

    def _config_payload(self) -> dict[str, Any]:
        return {
            "graph_path": str(self.graph_path),
            "regime_path": str(self.regime_path),
            "regime_name": self.regime.name,
            "dt": self.regime.simulation.dt,
            "steps": self.regime.simulation.steps,
            "burn_in": self.regime.simulation.burn_in,
            "seed": self.regime.simulation.seed,
        }

