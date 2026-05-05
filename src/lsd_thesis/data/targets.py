from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml
from pydantic import BaseModel, ConfigDict


class MetricTarget(BaseModel):
    target: float
    weight: float = 1.0
    confidence: str = "moderate"
    note: str = ""


class SoberTargetSet(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dataset_anchor: str
    module_names: tuple[str, ...]
    metrics: dict[str, MetricTarget]
    fc_matrix: np.ndarray
    notes: tuple[str, ...]


class PerturbationTargetSet(BaseModel):
    metadata: dict[str, Any]
    target_deltas: dict[str, float]
    confidence: dict[str, str]


def load_sober_target_set(path: str | Path) -> SoberTargetSet:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)

    return SoberTargetSet(
        dataset_anchor=raw["dataset_anchor"],
        module_names=tuple(raw["module_names"]),
        metrics={
            metric_name: MetricTarget.model_validate(metric_value)
            for metric_name, metric_value in raw["metrics"].items()
        },
        fc_matrix=np.asarray(raw["fc_matrix"], dtype=float),
        notes=tuple(raw["notes"]),
    )


def load_perturbation_target_set(path: str | Path) -> PerturbationTargetSet:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)
    return PerturbationTargetSet.model_validate(raw)
