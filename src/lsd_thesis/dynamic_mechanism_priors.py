from __future__ import annotations

from typing import cast

import numpy as np

CONTROL_WEIGHT_FLOOR = 0.10

PROXY_RECEPTOR_WEIGHTS = {
    "visual": 0.65,
    "auditory": 0.45,
    "salience": 0.70,
    "default_mode": 1.00,
    "executive_frontoparietal": 0.85,
    "limbic_affective": 0.70,
    "thalamic_gateway": 0.50,
    "sensorimotor": 0.35,
}
PROXY_HIERARCHY_VALUES = {
    "visual": 0.05,
    "auditory": 0.15,
    "salience": 0.55,
    "default_mode": 0.95,
    "executive_frontoparietal": 0.80,
    "limbic_affective": 0.70,
    "thalamic_gateway": 0.35,
    "sensorimotor": 0.10,
}
SENSORY_MODULES = {"visual", "auditory", "sensorimotor"}
TRANSMODAL_MODULES = {"salience", "default_mode", "executive_frontoparietal", "limbic_affective"}
GATEWAY_MODULES = {"thalamic_gateway"}


def infer_module_prior(module: str, prior: str) -> float:
    key = module.lower()
    if prior == "receptor":
        if module in PROXY_RECEPTOR_WEIGHTS:
            return PROXY_RECEPTOR_WEIGHTS[module]
        if "default" in key or "_def" in key:
            return 1.00
        if "cont" in key or "frontoparietal" in key or "executive" in key:
            return 0.85
        if "sal" in key or "ventattn" in key or "limbic" in key:
            return 0.70
        if "visual" in key or "_vis" in key or "viscent" in key or "visper" in key:
            return 0.65
        if "aud" in key:
            return 0.45
        if "som" in key or "motor" in key or "sommot" in key:
            return 0.35
        if "thalam" in key:
            return 0.50
        return 0.50
    if prior == "hierarchy":
        if module in PROXY_HIERARCHY_VALUES:
            return PROXY_HIERARCHY_VALUES[module]
        if "default" in key or "_def" in key:
            return 0.95
        if "cont" in key or "frontoparietal" in key or "executive" in key:
            return 0.80
        if "limbic" in key:
            return 0.70
        if "sal" in key or "ventattn" in key:
            return 0.55
        if "som" in key or "motor" in key or "sommot" in key:
            return 0.10
        if "visual" in key or "_vis" in key or "viscent" in key or "visper" in key:
            return 0.05
        if "thalam" in key:
            return 0.35
        return 0.50
    if prior == "sensory":
        sensory_tokens = ("visual", "_vis", "viscent", "visper", "aud", "som", "motor", "sommot")
        return 1.0 if module in SENSORY_MODULES or any(token in key for token in sensory_tokens) else 0.0
    if prior == "transmodal":
        return 1.0 if module in TRANSMODAL_MODULES or any(token in key for token in ("default", "_def", "cont", "front", "limbic")) else 0.0
    if prior == "thalamic":
        return 1.0 if module in GATEWAY_MODULES or "thalam" in key else 0.0
    return 0.0


def module_prior_vectors(modules: tuple[str, ...]) -> dict[str, np.ndarray]:
    return {
        "uniform": np.ones(len(modules), dtype=float),
        "receptor": np.asarray([infer_module_prior(module, "receptor") for module in modules], dtype=float),
        "hierarchy": np.asarray([infer_module_prior(module, "hierarchy") for module in modules], dtype=float),
        "sensory": np.asarray([infer_module_prior(module, "sensory") for module in modules], dtype=float),
        "transmodal": np.asarray([infer_module_prior(module, "transmodal") for module in modules], dtype=float),
        "thalamic": np.asarray([infer_module_prior(module, "thalamic") for module in modules], dtype=float),
    }


def normalise_control_weights(values: np.ndarray) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    vector = np.where(np.isfinite(vector), vector, 0.0)
    vector = np.maximum(vector, CONTROL_WEIGHT_FLOOR)
    mean_value = float(np.mean(vector))
    if mean_value <= 1e-12:
        return cast(np.ndarray, np.ones_like(vector, dtype=float))
    return cast(np.ndarray, vector / mean_value)


def module_masks(modules: tuple[str, ...]) -> dict[str, np.ndarray]:
    module_list = list(modules)
    sensory = np.asarray([infer_module_prior(module, "sensory") > 0.0 for module in module_list], dtype=bool)
    transmodal = np.asarray([infer_module_prior(module, "transmodal") > 0.0 for module in module_list], dtype=bool)
    gateway = np.asarray([infer_module_prior(module, "thalamic") > 0.0 for module in module_list], dtype=bool)
    if not np.any(sensory):
        sensory = np.asarray([index < max(1, len(module_list) // 3) for index in range(len(module_list))], dtype=bool)
    if not np.any(transmodal):
        transmodal = ~(sensory | gateway)
    return {
        "sensory": sensory,
        "transmodal": transmodal,
        "gateway": gateway,
        "non_gateway": ~gateway,
        "all": np.ones(len(module_list), dtype=bool),
    }
