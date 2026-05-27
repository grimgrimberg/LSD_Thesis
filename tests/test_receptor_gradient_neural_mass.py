import numpy as np

from lsd_thesis.models.receptor_gradient_neural_mass import (
    NodeMetadata,
    PerturbationParameters,
    ReceptorGradientNeuralMassModel,
    RGGNeuralMassConfig,
    lightweight_hrf,
)
from lsd_thesis.models.registry import get_model


def _small_metadata() -> NodeMetadata:
    return NodeMetadata(
        node_labels=("visual", "default_mode", "thalamus", "striatum"),
        network_labels=("Visual", "Default", "Thalamus", "Striatum"),
        hierarchy_values=(0.0, 1.0, 0.4, 0.45),
        receptor_weights=(1.0, 0.2, 0.4, 0.3),
        visual_weights=(1.0, 0.0, 0.0, 0.0),
        sensory_weights=(1.0, 0.0, 0.0, 0.0),
        transmodal_weights=(0.0, 1.0, 0.0, 0.0),
        thalamus_weights=(0.0, 0.0, 1.0, 0.0),
        striatum_weights=(0.0, 0.0, 0.0, 1.0),
    )


def _small_config(**overrides: object) -> RGGNeuralMassConfig:
    values = {
        "node_metadata": _small_metadata(),
        "coupling_matrix": np.asarray(
            [
                [0.0, 0.2, 0.3, 0.2],
                [0.2, 0.0, 0.1, 0.2],
                [0.3, 0.1, 0.0, 0.1],
                [0.2, 0.2, 0.1, 0.0],
            ],
            dtype=float,
        ),
        "dt": 0.05,
        "n_steps": 90,
        "burn_in": 10,
        "seed": 7,
        "noise_sigma": 0.0,
        "bias_E": 0.15,
        "emit_bold": True,
    }
    values.update(overrides)
    return RGGNeuralMassConfig(**values)


def test_registry_returns_receptor_gradient_model_and_alias() -> None:
    assert get_model("receptor_gradient_neural_mass").model_name == "receptor_gradient_neural_mass"
    assert get_model("rgg_nmm").model_name == "receptor_gradient_neural_mass"


def test_rgg_simulation_is_deterministic_finite_and_shaped() -> None:
    model = ReceptorGradientNeuralMassModel(config=_small_config())

    result_a = model.simulate(seed=42)
    result_b = model.simulate(seed=42)

    assert result_a.activity.shape == (80, 4)
    assert result_a.bold is not None
    assert result_a.bold.shape == result_a.activity.shape
    assert result_a.node_labels == ("visual", "default_mode", "thalamus", "striatum")
    assert np.all(np.isfinite(result_a.activity))
    assert np.all(np.isfinite(result_a.bold))
    assert np.allclose(result_a.activity, result_b.activity)


def test_receptor_gain_changes_high_receptor_node_more_than_zero_weight_node() -> None:
    metadata = NodeMetadata(
        node_labels=("high_receptor", "zero_receptor"),
        network_labels=("Visual", "Visual"),
        hierarchy_values=(0.0, 0.0),
        receptor_weights=(1.0, 0.0),
        visual_weights=(0.0, 0.0),
        sensory_weights=(0.0, 0.0),
        transmodal_weights=(0.0, 0.0),
        thalamus_weights=(0.0, 0.0),
        striatum_weights=(0.0, 0.0),
    )
    config = RGGNeuralMassConfig(
        node_metadata=metadata,
        coupling_matrix=np.zeros((2, 2), dtype=float),
        n_steps=100,
        burn_in=10,
        noise_sigma=0.0,
        bias_E=0.2,
        emit_bold=False,
    )
    model = ReceptorGradientNeuralMassModel(config=config)

    baseline = model.simulate(seed=1).activity.mean(axis=0)
    perturbed = model.simulate(seed=1, perturbation=PerturbationParameters(receptor_gain_alpha=0.9)).activity.mean(axis=0)
    delta = np.abs(perturbed - baseline)

    assert delta[0] > delta[1] + 1e-4


def test_hierarchy_cross_coupling_selectively_changes_distant_edges() -> None:
    model = ReceptorGradientNeuralMassModel(config=_small_config())

    baseline = model.effective_coupling_matrix()
    perturbed = model.effective_coupling_matrix(PerturbationParameters(hierarchy_cross_coupling_eta=0.5))

    assert perturbed[0, 1] > baseline[0, 1]
    assert perturbed[2, 3] == baseline[2, 3]


def test_associative_decoherence_weakens_transmodal_edges() -> None:
    metadata = _small_metadata()
    config = _small_config(
        node_metadata=metadata,
        coupling_matrix=np.asarray(
            [
                [0.0, 0.2, 0.1, 0.1],
                [0.2, 0.0, 0.1, 0.4],
                [0.1, 0.1, 0.0, 0.1],
                [0.1, 0.4, 0.1, 0.0],
            ],
            dtype=float,
        ),
    )
    metadata = NodeMetadata(
        **{
            **metadata.to_serializable(),
            "transmodal_weights": (0.0, 1.0, 0.0, 1.0),
        }
    )
    model = ReceptorGradientNeuralMassModel(config=RGGNeuralMassConfig(**{**config.to_serializable(), "node_metadata": metadata}))

    baseline = model.effective_coupling_matrix()
    perturbed = model.effective_coupling_matrix(PerturbationParameters(associative_decoherence_lambda=0.25))

    assert perturbed[1, 3] < baseline[1, 3]
    assert perturbed[0, 2] == baseline[0, 2]


def test_thalamic_routing_changes_thalamus_to_sensory_edges() -> None:
    model = ReceptorGradientNeuralMassModel(config=_small_config())

    baseline = model.effective_coupling_matrix()
    perturbed = model.effective_coupling_matrix(PerturbationParameters(thalamic_routing_kappa=0.4))

    assert perturbed[2, 0] > baseline[2, 0]
    assert perturbed[2, 1] == baseline[2, 1]


def test_homeostasis_reduces_high_gain_runaway_activity() -> None:
    config = _small_config(
        baseline_gain=5.0,
        w_EE=4.0,
        w_EI=0.05,
        global_coupling=0.0,
        homeostasis_strength=0.0,
        emit_bold=False,
    )
    unstable = ReceptorGradientNeuralMassModel(config=config).simulate(seed=3).activity.mean()
    stabilized_config = RGGNeuralMassConfig(**{**config.to_serializable(), "homeostasis_strength": 2.0})
    stabilized = ReceptorGradientNeuralMassModel(config=stabilized_config).simulate(seed=3).activity.mean()

    assert stabilized < unstable


def test_lightweight_hrf_preserves_shape_and_is_finite() -> None:
    activity = np.zeros((40, 2), dtype=float)
    activity[5:10, 0] = 1.0
    bold = lightweight_hrf(activity, dt=0.1)

    assert bold.shape == activity.shape
    assert np.all(np.isfinite(bold))
    assert bold[:, 0].max() > 0.0
