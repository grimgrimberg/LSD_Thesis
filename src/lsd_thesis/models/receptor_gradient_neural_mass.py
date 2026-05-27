from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, cast

import numpy as np
import yaml

from lsd_thesis.core import MODULE_GROUPS, MODULE_NAMES
from lsd_thesis.graph import load_graph_config
from lsd_thesis.models.base import SimulationResult

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "models" / "receptor_gradient_neural_mass.yaml"
DEFAULT_GRAPH_PATH = REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml"


def _as_tuple(values: tuple[Any, ...] | list[Any]) -> tuple[Any, ...]:
    return tuple(values)


@dataclass
class NodeMetadata:
    node_labels: tuple[str, ...] = MODULE_NAMES
    network_labels: tuple[str, ...] = (
        "Visual",
        "Auditory",
        "Salience",
        "Default",
        "Frontoparietal",
        "Limbic",
        "Thalamus",
        "Somatomotor",
    )
    hierarchy_values: tuple[float, ...] = (0.05, 0.15, 0.55, 0.95, 0.80, 0.70, 0.35, 0.10)
    receptor_weights: tuple[float, ...] = (0.65, 0.45, 0.70, 1.00, 0.85, 0.70, 0.50, 0.35)
    visual_weights: tuple[float, ...] = (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    sensory_weights: tuple[float, ...] = (1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    transmodal_weights: tuple[float, ...] = (0.0, 0.0, 0.6, 1.0, 0.9, 0.8, 0.0, 0.0)
    thalamus_weights: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    striatum_weights: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.35, 0.0, 0.0)

    def __post_init__(self) -> None:
        for name in (
            "node_labels",
            "network_labels",
            "hierarchy_values",
            "receptor_weights",
            "visual_weights",
            "sensory_weights",
            "transmodal_weights",
            "thalamus_weights",
            "striatum_weights",
        ):
            setattr(self, name, _as_tuple(getattr(self, name)))
        lengths = {
            len(self.node_labels),
            len(self.network_labels),
            len(self.hierarchy_values),
            len(self.receptor_weights),
            len(self.visual_weights),
            len(self.sensory_weights),
            len(self.transmodal_weights),
            len(self.thalamus_weights),
            len(self.striatum_weights),
        }
        if len(lengths) != 1:
            raise ValueError("All node metadata arrays must have the same length.")

    @property
    def node_count(self) -> int:
        return len(self.node_labels)

    def array(self, name: str) -> np.ndarray:
        return np.asarray(getattr(self, name), dtype=float)

    def to_serializable(self) -> dict[str, Any]:
        return {key: list(value) for key, value in asdict(self).items()}

    def metadata_by_node(self) -> dict[str, dict[str, Any]]:
        return {
            label: {
                "network": self.network_labels[index],
                "group": MODULE_GROUPS.get(label, self.network_labels[index]),
                "hierarchy": float(self.hierarchy_values[index]),
                "receptor_weight": float(self.receptor_weights[index]),
                "visual_weight": float(self.visual_weights[index]),
                "sensory_weight": float(self.sensory_weights[index]),
                "transmodal_weight": float(self.transmodal_weights[index]),
                "thalamus_weight": float(self.thalamus_weights[index]),
                "striatum_weight": float(self.striatum_weights[index]),
                "metadata_is_proxy": True,
            }
            for index, label in enumerate(self.node_labels)
        }


@dataclass
class PerturbationParameters:
    receptor_gain_alpha: float = 0.0
    hierarchy_cross_coupling_eta: float = 0.0
    visual_gain_beta: float = 0.0
    sensory_gain_gamma: float = 0.0
    associative_decoherence_lambda: float = 0.0
    thalamic_routing_kappa: float = 0.0
    striatal_routing_kappa: float = 0.0
    noise_delta: float = 0.0
    homeostasis_delta: float = 0.0

    @classmethod
    def from_any(cls, value: PerturbationParameters | dict[str, Any] | None) -> PerturbationParameters:
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(**value)
        raise TypeError(f"Unsupported perturbation parameters: {type(value).__name__}")

    def to_serializable(self) -> dict[str, float]:
        return {key: float(value) for key, value in asdict(self).items()}


@dataclass
class RGGNeuralMassConfig:
    node_metadata: NodeMetadata = field(default_factory=NodeMetadata)
    coupling_matrix: np.ndarray | list[list[float]] | None = None
    graph_path: str | Path | None = DEFAULT_GRAPH_PATH
    global_coupling: float = 0.7
    noise_sigma: float = 0.02
    tau_E: float = 1.0  # noqa: N815
    tau_I: float = 1.5  # noqa: N815
    w_EE: float = 1.4  # noqa: N815
    w_EI: float = 1.0  # noqa: N815
    w_IE: float = 1.0  # noqa: N815
    w_II: float = 0.4  # noqa: N815
    baseline_gain: float = 1.2
    bias_E: float = 0.05  # noqa: N815
    bias_I: float = 0.0  # noqa: N815
    initial_state_scale: float = 0.03
    homeostasis_strength: float = 0.5
    homeostasis_target: float = 0.45
    dt: float = 0.05
    n_steps: int = 240
    burn_in: int = 40
    seed: int = 17
    emit_bold: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.node_metadata, dict):
            self.node_metadata = NodeMetadata(**self.node_metadata)
        if self.n_steps <= self.burn_in:
            raise ValueError("n_steps must be greater than burn_in.")
        if self.dt <= 0.0:
            raise ValueError("dt must be positive.")
        if self.coupling_matrix is None:
            self.coupling_matrix = _default_coupling_matrix(self.node_metadata, self.graph_path)
        else:
            self.coupling_matrix = np.asarray(self.coupling_matrix, dtype=float)
        if self.coupling_matrix.shape != (self.node_metadata.node_count, self.node_metadata.node_count):
            raise ValueError("coupling_matrix shape must match node metadata length.")

    def to_serializable(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["node_metadata"] = self.node_metadata.to_serializable()
        payload["coupling_matrix"] = np.asarray(self.coupling_matrix, dtype=float).tolist()
        if payload["graph_path"] is not None:
            payload["graph_path"] = str(payload["graph_path"])
        return payload


def _default_coupling_matrix(metadata: NodeMetadata, graph_path: str | Path | None) -> np.ndarray:
    if graph_path is not None and tuple(metadata.node_labels) == MODULE_NAMES:
        graph = load_graph_config(graph_path)
        return np.asarray(graph.adjacency, dtype=float)
    return np.zeros((metadata.node_count, metadata.node_count), dtype=float)


def _sigmoid(value: np.ndarray) -> np.ndarray:
    clipped = np.clip(value, -60.0, 60.0)
    return np.asarray(1.0 / (1.0 + np.exp(-clipped)), dtype=float)


def _row_normalize(matrix: np.ndarray) -> np.ndarray:
    row_sums = matrix.sum(axis=1, keepdims=True)
    return cast(
        np.ndarray,
        np.divide(matrix, row_sums, out=np.zeros_like(matrix, dtype=float), where=row_sums > 1e-12),
    )


def lightweight_hrf(activity: np.ndarray, dt: float, duration: float = 24.0) -> np.ndarray:
    if activity.ndim != 2:
        raise ValueError("Activity must be shaped as [time, node].")
    time = np.arange(0.0, duration, dt, dtype=float)
    if len(time) == 0:
        return activity.copy()
    peak = np.power(time, 6.0) * np.exp(-time)
    undershoot = 0.35 * np.power(time, 12.0) * np.exp(-time) / 900.0
    kernel = peak - undershoot
    kernel = np.maximum(kernel, 0.0)
    total = float(kernel.sum())
    if total <= 1e-12:
        return activity.copy()
    kernel = kernel / total
    columns = [
        np.convolve(activity[:, index], kernel, mode="full")[: activity.shape[0]]
        for index in range(activity.shape[1])
    ]
    return np.asarray(np.stack(columns, axis=1), dtype=float)


def load_receptor_gradient_config(path: str | Path) -> RGGNeuralMassConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    accepted = {item.name for item in fields(RGGNeuralMassConfig)}
    payload = {key: value for key, value in dict(raw).items() if key in accepted}
    return RGGNeuralMassConfig(**payload)


class ReceptorGradientNeuralMassModel:
    model_name = "receptor_gradient_neural_mass"

    def __init__(self, config: RGGNeuralMassConfig | dict[str, Any] | None = None, config_path: str | Path | None = None) -> None:
        if config is not None:
            self.config = config if isinstance(config, RGGNeuralMassConfig) else RGGNeuralMassConfig(**config)
            self.config_path = None
        elif config_path is not None:
            self.config = load_receptor_gradient_config(config_path)
            self.config_path = Path(config_path)
        elif DEFAULT_CONFIG_PATH.exists():
            self.config = load_receptor_gradient_config(DEFAULT_CONFIG_PATH)
            self.config_path = DEFAULT_CONFIG_PATH
        else:
            self.config = RGGNeuralMassConfig()
            self.config_path = None

    def node_gain(self, perturbation: PerturbationParameters | dict[str, Any] | None = None) -> np.ndarray:
        resolved = PerturbationParameters.from_any(perturbation)
        metadata = self.config.node_metadata
        gain = self.config.baseline_gain * (
            1.0
            + resolved.receptor_gain_alpha * metadata.array("receptor_weights")
            + resolved.visual_gain_beta * metadata.array("visual_weights")
            + resolved.sensory_gain_gamma * metadata.array("sensory_weights")
        )
        return np.maximum(gain, 0.01)

    def effective_coupling_matrix(self, perturbation: PerturbationParameters | dict[str, Any] | None = None) -> np.ndarray:
        resolved = PerturbationParameters.from_any(perturbation)
        metadata = self.config.node_metadata
        matrix = np.asarray(self.config.coupling_matrix, dtype=float).copy()

        hierarchy = metadata.array("hierarchy_values")
        hierarchy_distance = np.abs(hierarchy[:, None] - hierarchy[None, :])
        unimodal_transmodal = (
            (metadata.array("sensory_weights")[:, None] > 0.0)
            & (metadata.array("transmodal_weights")[None, :] > 0.0)
        ) | (
            (metadata.array("transmodal_weights")[:, None] > 0.0)
            & (metadata.array("sensory_weights")[None, :] > 0.0)
        )
        hierarchy_mask = (hierarchy_distance > 0.35) | unimodal_transmodal
        matrix *= 1.0 + resolved.hierarchy_cross_coupling_eta * hierarchy_distance * hierarchy_mask

        transmodal = metadata.array("transmodal_weights") > 0.5
        transmodal_pair = transmodal[:, None] & transmodal[None, :]
        matrix *= np.where(
            transmodal_pair,
            max(0.0, 1.0 - resolved.associative_decoherence_lambda),
            1.0,
        )

        sensory = metadata.array("sensory_weights") > 0.0
        thalamus = metadata.array("thalamus_weights") > 0.0
        striatum = metadata.array("striatum_weights") > 0.0
        thalamic_pair = (thalamus[:, None] & sensory[None, :]) | (sensory[:, None] & thalamus[None, :])
        striatal_pair = (striatum[:, None] & sensory[None, :]) | (sensory[:, None] & striatum[None, :])
        matrix *= np.where(thalamic_pair, 1.0 + resolved.thalamic_routing_kappa, 1.0)
        matrix *= np.where(striatal_pair, 1.0 + resolved.striatal_routing_kappa, 1.0)

        np.fill_diagonal(matrix, 0.0)
        return np.asarray(np.maximum(matrix, 0.0), dtype=float)

    def simulate(
        self,
        config: dict[str, Any] | None = None,
        seed: int | None = None,
        perturbation: PerturbationParameters | dict[str, Any] | None = None,
    ) -> SimulationResult:
        runtime_config = self.config if config is None else RGGNeuralMassConfig(**{**self.config.to_serializable(), **config})
        resolved_perturbation = PerturbationParameters.from_any(
            perturbation or (config or {}).get("perturbation")
        )
        effective_seed = runtime_config.seed if seed is None else seed
        rng = np.random.default_rng(effective_seed)
        node_count = runtime_config.node_metadata.node_count
        excitatory = np.clip(
            runtime_config.homeostasis_target + rng.normal(0.0, runtime_config.initial_state_scale, size=node_count),
            0.0,
            1.0,
        )
        inhibitory = np.clip(
            runtime_config.homeostasis_target + rng.normal(0.0, runtime_config.initial_state_scale, size=node_count),
            0.0,
            1.0,
        )
        activity = np.zeros((runtime_config.n_steps, node_count), dtype=float)
        coupling = _row_normalize(self.effective_coupling_matrix(resolved_perturbation))
        gain = self.node_gain(resolved_perturbation)
        noise_sigma = max(0.0, runtime_config.noise_sigma + resolved_perturbation.noise_delta)
        homeostasis_strength = max(0.0, runtime_config.homeostasis_strength + resolved_perturbation.homeostasis_delta)

        for step in range(runtime_config.n_steps):
            global_feedback = homeostasis_strength * (float(np.mean(excitatory)) - runtime_config.homeostasis_target)
            local_feedback = homeostasis_strength * (excitatory - runtime_config.homeostasis_target)
            excitatory_input = gain * (
                runtime_config.w_EE * excitatory
                - runtime_config.w_EI * inhibitory
                + runtime_config.global_coupling * (coupling @ excitatory)
                + runtime_config.bias_E
                - global_feedback
                - local_feedback
            )
            inhibitory_input = (
                runtime_config.w_IE * excitatory
                - runtime_config.w_II * inhibitory
                + runtime_config.bias_I
                + local_feedback
            )
            excitatory_target = _sigmoid(excitatory_input)
            inhibitory_target = _sigmoid(inhibitory_input)
            excitatory += runtime_config.dt * ((-excitatory + excitatory_target) / runtime_config.tau_E)
            inhibitory += runtime_config.dt * ((-inhibitory + inhibitory_target) / runtime_config.tau_I)
            if noise_sigma > 0.0:
                excitatory += noise_sigma * rng.normal(size=node_count) * np.sqrt(runtime_config.dt)
            excitatory = np.clip(excitatory, 0.0, 1.5)
            inhibitory = np.clip(inhibitory, 0.0, 1.5)
            activity[step] = excitatory

        kept_activity = activity[runtime_config.burn_in :]
        bold = lightweight_hrf(kept_activity, dt=runtime_config.dt) if runtime_config.emit_bold else None
        return SimulationResult(
            activity=kept_activity,
            bold=bold,
            node_labels=tuple(runtime_config.node_metadata.node_labels),
            node_metadata=runtime_config.node_metadata.metadata_by_node(),
            dt=runtime_config.dt,
            seed=effective_seed,
            model_name=self.model_name,
            config=runtime_config.to_serializable(),
            provenance={
                "source": "src/lsd_thesis/models/receptor_gradient_neural_mass.py",
                "config_path": str(self.config_path) if self.config_path is not None else None,
                "perturbation": resolved_perturbation.to_serializable(),
                "claim_boundary": "surrogate neural-mass model; not receptor-level pharmacology",
            },
        )
