from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from lsd_thesis.setting_seed.data import DEFAULT_STAGE_2_DIR, _default_repo_root, load_run_records, load_tidy_time_series


@dataclass(frozen=True)
class LatentGeometryResult:
    coordinates: pd.DataFrame
    trajectory_metrics: pd.DataFrame
    subject_displacements: pd.DataFrame
    report_markdown: str
    run_02_available: bool


def trajectory_metrics_from_coordinates(coords: np.ndarray) -> dict[str, float]:
    array = np.asarray(coords, dtype=float)
    if array.ndim != 2 or array.shape[0] == 0:
        raise ValueError("Coordinates must be [time, latent_dim] with at least one row.")
    diffs = np.diff(array, axis=0)
    step_lengths = np.linalg.norm(diffs, axis=1) if len(diffs) else np.asarray([], dtype=float)
    centroid = np.mean(array, axis=0)
    dispersion = float(np.mean(np.linalg.norm(array - centroid, axis=1)))
    return {
        "centroid_pc1": float(centroid[0]) if array.shape[1] > 0 else 0.0,
        "centroid_pc2": float(centroid[1]) if array.shape[1] > 1 else 0.0,
        "trajectory_length": float(np.sum(step_lengths)),
        "trajectory_dispersion": dispersion,
        "latent_velocity": float(np.mean(step_lengths)) if len(step_lengths) else 0.0,
    }


def compute_latent_geometry(stage_2_dir: str | Path | None = None, seed: int = 20260512) -> LatentGeometryResult:
    stage_2_path = DEFAULT_STAGE_2_DIR if stage_2_dir is None else Path(stage_2_dir)
    tidy = load_tidy_time_series(stage_2_path)
    records = load_run_records(stage_2_path)
    run_02_available = any(str(record["run"]) == "run-02" for record in records)
    wide = tidy.pivot_table(
        index=["subject", "session", "condition", "run", "run_label", "time"],
        columns="module",
        values="value",
        sort=False,
    ).reset_index()
    module_columns = [column for column in wide.columns if column not in {"subject", "session", "condition", "run", "run_label", "time"}]
    pca = PCA(n_components=2, random_state=seed)
    coords = pca.fit_transform(wide[module_columns].to_numpy(dtype=float))
    coordinates = wide[["subject", "session", "condition", "run", "run_label", "time"]].copy()
    coordinates["pc1"] = coords[:, 0]
    coordinates["pc2"] = coords[:, 1]
    coordinates["analysis_label"] = "visualization-only descriptive PCA; not a subject-disjoint ML feature"

    metric_rows: list[dict[str, Any]] = []
    for key, frame in coordinates.groupby(["subject", "session", "condition", "run", "run_label"], sort=True):
        subject, session, condition, run, run_label = key
        metrics = trajectory_metrics_from_coordinates(frame[["pc1", "pc2"]].to_numpy(dtype=float))
        metric_rows.append(
            {
                "subject": subject,
                "session": session,
                "condition": condition,
                "run": run,
                "run_label": run_label,
                **metrics,
            }
        )
    trajectory = pd.DataFrame(metric_rows).sort_values(["subject", "session", "run"]).reset_index(drop=True)

    displacement_rows: list[dict[str, Any]] = []
    for subject, subject_frame in trajectory.groupby("subject", sort=True):
        for run, run_frame in subject_frame.groupby("run", sort=True):
            lsd = run_frame[run_frame["session"] == "ses-LSD"]
            plcb = run_frame[run_frame["session"] == "ses-PLCB"]
            if len(lsd) == 1 and len(plcb) == 1:
                displacement_rows.append(
                    {
                        "subject": subject,
                        "run": run,
                        "lsd_minus_placebo_centroid_distance": float(
                            np.linalg.norm(
                                lsd[["centroid_pc1", "centroid_pc2"]].to_numpy(dtype=float)[0]
                                - plcb[["centroid_pc1", "centroid_pc2"]].to_numpy(dtype=float)[0]
                            )
                        ),
                        "trajectory_length_delta": float(lsd["trajectory_length"].iloc[0] - plcb["trajectory_length"].iloc[0]),
                        "trajectory_dispersion_delta": float(lsd["trajectory_dispersion"].iloc[0] - plcb["trajectory_dispersion"].iloc[0]),
                    }
                )
    displacements = pd.DataFrame(displacement_rows)
    report = "\n".join(
        [
            "# Set / Setting / Seed Latent Geometry",
            "",
            "Status: visualization-only descriptive PCA over cached rest module time series.",
            "",
            "This PCA is fitted on the available rest cache for dashboard geometry only. It is not used for ML claims.",
            f"Run-02 available: {str(run_02_available).lower()}",
            "Rest1-to-Music and Music-to-Rest3 geometry are unavailable until run-02 extraction exists.",
            "",
        ]
    )
    return LatentGeometryResult(coordinates, trajectory, displacements, report, run_02_available)


def write_latent_outputs(
    stage_2_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    repo_root: str | Path | None = None,
    seed: int = 20260512,
) -> LatentGeometryResult:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    out_dir = root / "results" / "setting_seed" / "latent" if output_dir is None else Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = compute_latent_geometry(stage_2_dir=stage_2_dir, seed=seed)
    result.coordinates.to_csv(out_dir / "latent_coordinates.csv", index=False)
    result.trajectory_metrics.to_csv(out_dir / "trajectory_metrics.csv", index=False)
    result.subject_displacements.to_csv(out_dir / "subject_displacements.csv", index=False)
    (out_dir / "latent_report.md").write_text(result.report_markdown, encoding="utf-8")
    return result
