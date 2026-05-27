from __future__ import annotations

from typing import Any, Protocol

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class SimulationResult(BaseModel):
    """Common model-zoo result for latent and optional BOLD-like activity."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    activity: np.ndarray
    bold: np.ndarray | None = None
    node_labels: tuple[str, ...]
    node_metadata: dict[str, dict[str, Any]] = Field(default_factory=dict)
    dt: float
    seed: int
    model_name: str
    config: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @property
    def time_series(self) -> np.ndarray:
        """Compatibility alias for older callers that expect `time_series`."""
        return self.activity


class BaseBrainModel(Protocol):
    model_name: str

    def simulate(self, config: dict[str, Any] | None = None, seed: int | None = None) -> SimulationResult:
        """Run a model and return a common model-zoo result."""
        ...

