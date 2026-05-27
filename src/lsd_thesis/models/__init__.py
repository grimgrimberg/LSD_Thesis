"""Model-zoo interfaces for whole-brain surrogate simulators."""

from lsd_thesis.models.base import BaseBrainModel, SimulationResult
from lsd_thesis.models.bistable import BistableModel
from lsd_thesis.models.receptor_gradient_neural_mass import ReceptorGradientNeuralMassModel
from lsd_thesis.models.registry import available_models, get_model, register_model

__all__ = [
    "BaseBrainModel",
    "BistableModel",
    "ReceptorGradientNeuralMassModel",
    "SimulationResult",
    "available_models",
    "get_model",
    "register_model",
]
