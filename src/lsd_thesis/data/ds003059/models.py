from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict


class Ds003059RunRecord(BaseModel):
    subject: str
    session: str
    run: str
    filename: str
    relative_path: str
    url: str
    size: int

class Ds003059RestManifest(BaseModel):
    subjects: tuple[str, ...]
    runs: tuple[Ds003059RunRecord, ...]
    sidecars: tuple[str, ...]

class Ds003059EmpiricalRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    subject: str
    session: str
    run: str
    relative_path: str
    timepoints: int
    metrics: dict[str, float]
    fc_matrix: np.ndarray
    time_series_path: str
