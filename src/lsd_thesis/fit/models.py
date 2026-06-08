from __future__ import annotations

from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict

from lsd_thesis.core import RegimeConfig


class FitResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    initial_score: float
    best_score: float
    selection_score_std: float = 0.0
    selected_iteration: int = 0
    best_regime: RegimeConfig
    best_metrics: dict[str, float]
    best_metrics_std: dict[str, float] = {}
    best_fc_matrix: np.ndarray
    history: list[dict[str, Any]]
    seed_plan: dict[str, Any] = {}
    selection_diagnostics: list[dict[str, Any]] = []
    validation_score_mean: float | None = None
    validation_score_std: float | None = None
    validation_metrics_mean: dict[str, float] = {}
    validation_metrics_std: dict[str, float] = {}

class FitSeedPlan(BaseModel):
    proposal_seed: int
    selection_seeds: tuple[int, ...]
    validation_seeds: tuple[int, ...]
    selection_mode: str
    validation_mode: str
