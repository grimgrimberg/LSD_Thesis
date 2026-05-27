import json
from pathlib import Path

import numpy as np
import pytest

from lsd_thesis.training import build_window_dataset, slice_windows


def test_slice_windows_builds_overlapping_fixed_length_windows() -> None:
    time_series = np.arange(30, dtype=float).reshape(10, 3)

    windows = slice_windows(time_series, window_length=4, stride=3)

    assert windows.shape == (3, 4, 3)
    assert np.array_equal(windows[0], time_series[0:4])
    assert np.array_equal(windows[1], time_series[3:7])
    assert np.array_equal(windows[2], time_series[6:10])


def test_build_window_dataset_rejects_time_series_paths_outside_stage_dir(tmp_path: Path) -> None:
    stage_2_dir = tmp_path / "stage_2"
    stage_2_dir.mkdir()
    outside_path = tmp_path / "outside.npy"
    np.save(outside_path, np.zeros((80, 2), dtype=float))
    (stage_2_dir / "empirical_run_summaries.json").write_text(
        json.dumps(
            [
                {
                    "subject": "sub-001",
                    "session": "ses-LSD",
                    "run": "run-01",
                    "time_series_path": "../outside.npy",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="outside the allowed root"):
        build_window_dataset(stage_2_dir, window_length=16, stride=8)


def test_build_window_dataset_rejects_windows_drive_style_time_series_paths(tmp_path: Path) -> None:
    stage_2_dir = tmp_path / "stage_2"
    stage_2_dir.mkdir()
    (stage_2_dir / "empirical_run_summaries.json").write_text(
        json.dumps(
            [
                {
                    "subject": "sub-001",
                    "session": "ses-LSD",
                    "run": "run-01",
                    "time_series_path": "D:\\LSD_Thesis\\results\\stage_2\\module_time_series\\example.npy",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="outside the allowed root"):
        build_window_dataset(stage_2_dir, window_length=16, stride=8)
