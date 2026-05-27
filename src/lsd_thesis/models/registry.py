from __future__ import annotations

from collections.abc import Callable

from lsd_thesis.models.base import BaseBrainModel
from lsd_thesis.models.bistable import BistableModel
from lsd_thesis.models.receptor_gradient_neural_mass import ReceptorGradientNeuralMassModel

ModelFactory = Callable[..., BaseBrainModel]

_MODEL_FACTORIES: dict[str, ModelFactory] = {
    "bistable": BistableModel,
    "legacy_bistable": BistableModel,
    "receptor_gradient_neural_mass": ReceptorGradientNeuralMassModel,
    "rgg_nmm": ReceptorGradientNeuralMassModel,
}


def available_models() -> tuple[str, ...]:
    return tuple(sorted(_MODEL_FACTORIES))


def register_model(name: str, factory: ModelFactory, aliases: tuple[str, ...] = ()) -> None:
    normalized_names = (name, *aliases)
    for model_name in normalized_names:
        _MODEL_FACTORIES[model_name] = factory


def get_model(name: str = "bistable", **kwargs: object) -> BaseBrainModel:
    try:
        factory = _MODEL_FACTORIES[name]
    except KeyError as error:
        available = ", ".join(available_models())
        raise ValueError(f"Unknown model '{name}'. Available models: {available}.") from error
    return factory(**kwargs)
