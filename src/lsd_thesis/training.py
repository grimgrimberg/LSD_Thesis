from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from lsd_thesis.utils import resolve_under


def slice_windows(time_series: np.ndarray, window_length: int, stride: int) -> np.ndarray:
    if time_series.ndim != 2:
        raise ValueError("Time series must be [time, feature].")
    if window_length <= 0 or stride <= 0:
        raise ValueError("Window length and stride must be positive.")
    if len(time_series) < window_length:
        return np.empty((0, window_length, time_series.shape[1]), dtype=float)

    windows = [
        time_series[start : start + window_length]
        for start in range(0, len(time_series) - window_length + 1, stride)
    ]
    return np.asarray(windows, dtype=float)


def build_window_dataset(
    stage_2_dir: str | Path,
    window_length: int = 64,
    stride: int = 16,
) -> dict[str, Any]:
    stage_2_path = Path(stage_2_dir)
    records = json.loads((stage_2_path / "empirical_run_summaries.json").read_text(encoding="utf-8"))

    windows: list[np.ndarray] = []
    condition_labels: list[int] = []
    subjects: list[str] = []
    sessions: list[str] = []
    runs: list[str] = []

    for record in records:
        ts_path = resolve_under(stage_2_path, str(record["time_series_path"]))
        time_series = np.load(ts_path)
        run_windows = slice_windows(time_series, window_length=window_length, stride=stride)
        if len(run_windows) == 0:
            continue

        windows.extend(run_windows)
        condition = 1 if record["session"] == "ses-LSD" else 0
        condition_labels.extend([condition] * len(run_windows))
        subjects.extend([record["subject"]] * len(run_windows))
        sessions.extend([record["session"]] * len(run_windows))
        runs.extend([record["run"]] * len(run_windows))

    return {
        "windows": np.asarray(windows, dtype=float),
        "condition": np.asarray(condition_labels, dtype=np.int8),
        "subject": np.asarray(subjects, dtype="U32"),
        "session": np.asarray(sessions, dtype="U16"),
        "run": np.asarray(runs, dtype="U16"),
        "window_length": window_length,
        "stride": stride,
    }
