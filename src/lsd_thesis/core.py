from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

MODULE_NAMES: tuple[str, ...] = (
    "visual",
    "auditory",
    "salience",
    "default_mode",
    "executive_frontoparietal",
    "limbic_affective",
    "thalamic_gateway",
    "sensorimotor",
)

MODULE_GROUPS: dict[str, str] = {
    "visual": "sensory",
    "auditory": "sensory",
    "sensorimotor": "sensory",
    "salience": "associative",
    "default_mode": "associative",
    "executive_frontoparietal": "associative",
    "limbic_affective": "associative",
    "thalamic_gateway": "gateway",
}


class GraphConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    modules: tuple[str, ...]
    adjacency: np.ndarray
    hierarchy_projection: np.ndarray


class SimulationSettings(BaseModel):
    dt: float
    steps: int
    burn_in: int = 0
    seed: int

    @model_validator(mode="after")
    def _check_burn_in(self) -> SimulationSettings:
        if self.burn_in >= self.steps:
            raise ValueError(f"burn_in ({self.burn_in}) must be less than steps ({self.steps}).")
        return self


class GlobalParameters(BaseModel):
    within_group_scale: float = 1.0
    cross_group_scale: float = 1.0
    constraint_scale: float


class ModuleParameters(BaseModel):
    barrier: float = 1.0
    rigidity: float = 0.5
    adaptation_gain: float = 0.25
    adaptation_tau: float = 3.0
    tau: float = 1.0
    temperature: float = 0.1
    baseline_state: float = 0.0
    cross_scale: float | None = None
    constraint_scale: float | None = None

    def merged(
        self,
        override: ModuleParameters | ModuleParameterOverride | None,
    ) -> ModuleParameters:
        if override is None:
            return self.model_copy(deep=True)

        values = self.model_dump()
        for key, value in override.model_dump(exclude_none=True).items():
            values[key] = value
        return ModuleParameters.model_validate(values)


class ModuleParameterOverride(BaseModel):
    barrier: float | None = None
    rigidity: float | None = None
    adaptation_gain: float | None = None
    adaptation_tau: float | None = None
    tau: float | None = None
    temperature: float | None = None
    baseline_state: float | None = None
    cross_scale: float | None = None
    constraint_scale: float | None = None


class RegimeConfig(BaseModel):
    name: str
    simulation: SimulationSettings
    global_parameters: GlobalParameters
    module_defaults: ModuleParameters
    module_overrides: dict[str, ModuleParameterOverride] = Field(default_factory=dict)

    def parameters_for_modules(self, modules: tuple[str, ...]) -> dict[str, np.ndarray]:
        merged = [
            self.module_defaults.merged(self.module_overrides.get(module_name))
            for module_name in modules
        ]
        coupling_scale = np.asarray(
            [item.cross_scale if item.cross_scale is not None else 1.0 for item in merged],
            dtype=float,
        )
        constraint_scale = np.asarray(
            [
                item.constraint_scale
                if item.constraint_scale is not None
                else self.global_parameters.constraint_scale
                for item in merged
            ],
            dtype=float,
        )
        return {
            "barrier": np.asarray([item.barrier for item in merged], dtype=float),
            "rigidity": np.asarray([item.rigidity for item in merged], dtype=float),
            "adaptation_gain": np.asarray([item.adaptation_gain for item in merged], dtype=float),
            "adaptation_tau": np.asarray([item.adaptation_tau for item in merged], dtype=float),
            "tau": np.asarray([item.tau for item in merged], dtype=float),
            "temperature": np.asarray([item.temperature for item in merged], dtype=float),
            "baseline_state": np.asarray([item.baseline_state for item in merged], dtype=float),
            "coupling_scale": coupling_scale,
            "constraint_scale": constraint_scale,
        }


class SimulationResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    regime_name: str
    module_names: tuple[str, ...]
    time: np.ndarray
    time_series: np.ndarray


class SummaryMetrics(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    fc_matrix: np.ndarray
    dynamic_fc_change: float
    state_entropy: float
    switching_rate: float
    state_labels: np.ndarray


class ObservableSummary(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    fc_matrix: np.ndarray
    within_network_stability: float
    cross_network_communication: float
    thalamic_coupling: float
    hierarchical_compression: float
    entropy_diversity: float
    switching_rate: float
    metastability_proxy: float
    effective_barrier_proxy: float
    state_labels: np.ndarray

    def metric_map(self) -> dict[str, float]:
        return {
            "within_network_stability": self.within_network_stability,
            "cross_network_communication": self.cross_network_communication,
            "thalamic_coupling": self.thalamic_coupling,
            "hierarchical_compression": self.hierarchical_compression,
            "entropy_diversity": self.entropy_diversity,
            "switching_rate": self.switching_rate,
            "metastability_proxy": self.metastability_proxy,
            "effective_barrier_proxy": self.effective_barrier_proxy,
        }
