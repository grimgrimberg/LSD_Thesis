import numpy as np
import pytest

from lsd_thesis.dynamic_mechanism_priors import (
    module_masks,
    module_prior_vectors,
    normalise_control_weights,
)


def test_module_prior_vectors_keep_canonical_proxy_weights() -> None:
    modules = ("visual", "default_mode", "thalamic_gateway")

    priors = module_prior_vectors(modules)

    assert priors["uniform"].tolist() == [1.0, 1.0, 1.0]
    assert priors["receptor"].tolist() == [0.65, 1.0, 0.5]
    assert priors["hierarchy"].tolist() == [0.05, 0.95, 0.35]
    assert priors["sensory"].tolist() == [1.0, 0.0, 0.0]
    assert priors["transmodal"].tolist() == [0.0, 1.0, 0.0]
    assert priors["thalamic"].tolist() == [0.0, 0.0, 1.0]


def test_module_masks_fall_back_when_custom_names_lack_sensory_tokens() -> None:
    masks = module_masks(("parcel_a", "parcel_b", "thalamus"))

    assert masks["sensory"].tolist() == [True, False, False]
    assert masks["transmodal"].tolist() == [False, True, False]
    assert masks["gateway"].tolist() == [False, False, True]
    assert masks["non_gateway"].tolist() == [True, True, False]
    assert masks["all"].tolist() == [True, True, True]


def test_normalise_control_weights_is_finite_and_budget_matched() -> None:
    weights = normalise_control_weights(np.asarray([np.nan, 0.0, 2.0], dtype=float))

    assert np.isfinite(weights).all()
    assert float(np.mean(weights)) == pytest.approx(1.0)
    assert weights[0] == weights[1]
    assert weights[2] > weights[0]
