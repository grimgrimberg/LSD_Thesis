import json
import uuid
from pathlib import Path

import numpy as np

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.setting_seed.latent import compute_latent_geometry, trajectory_metrics_from_coordinates


def _write_stage2_fixture(name: str) -> Path:
    root = Path("results") / "setting_seed" / "test_fixtures" / f"{name}_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    stage_2 = root / "stage_2"
    series_dir = stage_2 / "module_time_series"
    series_dir.mkdir(parents=True)
    records: list[dict[str, object]] = []
    for subject_offset, subject in enumerate(["sub-001", "sub-002"]):
        for session_offset, session in enumerate(["ses-PLCB", "ses-LSD"]):
            for run_offset, run in enumerate(["run-01", "run-03"]):
                base = subject_offset + session_offset * 2 + run_offset * 3
                values = np.asarray(
                    [[base + time + module * 0.1 for module in range(len(MODULE_NAMES))] for time in range(5)],
                    dtype=float,
                )
                file_name = f"{subject}_{session}_{run}_modules.npy"
                np.save(series_dir / file_name, values)
                records.append(
                    {
                        "subject": subject,
                        "session": session,
                        "run": run,
                        "time_series_path": str(Path("module_time_series") / file_name),
                    }
                )
    (stage_2 / "empirical_run_summaries.json").write_text(json.dumps(records), encoding="utf-8")
    return stage_2


def test_trajectory_metrics_from_coordinates_are_geometric() -> None:
    coords = np.asarray([[0.0, 0.0], [3.0, 4.0], [6.0, 8.0]], dtype=float)

    metrics = trajectory_metrics_from_coordinates(coords)

    assert metrics["trajectory_length"] == 10.0
    assert metrics["latent_velocity"] == 5.0
    assert metrics["trajectory_dispersion"] > 0.0


def test_compute_latent_geometry_is_deterministic_and_labels_visualization_only() -> None:
    stage_2 = _write_stage2_fixture("latent")

    first = compute_latent_geometry(stage_2, seed=23)
    second = compute_latent_geometry(stage_2, seed=23)

    assert first.coordinates.equals(second.coordinates)
    assert {"pc1", "pc2"}.issubset(first.coordinates.columns)
    assert first.trajectory_metrics["run"].isin(["run-01", "run-03"]).all()
    assert first.run_02_available is False
    assert "visualization-only" in first.report_markdown
