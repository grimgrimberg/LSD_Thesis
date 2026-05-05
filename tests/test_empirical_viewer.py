from pathlib import Path
from types import SimpleNamespace

import nibabel as nib
import numpy as np

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.data.empirical_viewer import (
    build_empirical_run_views_from_records,
    build_empirical_viewer_payloads,
    build_run_empirical_view,
)


def test_build_run_empirical_view_contains_raw_previews_and_windows() -> None:
    timepoints = 18
    module_count = len(MODULE_NAMES)
    volume = np.zeros((10, 12, 8, timepoints), dtype=float)
    for index in range(timepoints):
        volume[..., index] = index
    bold_image = nib.Nifti1Image(volume, affine=np.eye(4))
    time_series = np.stack(
        [np.linspace(0.0, 1.0 + module_index, timepoints) for module_index in range(module_count)],
        axis=1,
    )

    payload = build_run_empirical_view(
        subject="sub-001",
        session="ses-PLCB",
        run="run-01",
        relative_path="sub-001/ses-PLCB/func/example.nii.gz",
        time_series=time_series,
        bold_image=bold_image,
        modules=MODULE_NAMES,
        window_count=3,
        preview_size=6,
    )

    assert payload["subject"] == "sub-001"
    assert payload["session"] == "ses-PLCB"
    assert payload["run"] == "run-01"
    assert payload["window_count"] == 3
    assert len(payload["global_signal"]) == timepoints
    assert len(payload["module_time_series"]) == timepoints
    assert set(payload["mean_raw_preview"]) == {"axial", "coronal", "sagittal"}
    assert len(payload["windows"]) == 3
    assert payload["windows"][0]["start_index"] == 0
    assert payload["windows"][0]["end_index"] > payload["windows"][0]["start_index"]
    assert set(payload["windows"][0]["raw_preview"]) == {"axial", "coronal", "sagittal"}
    assert len(payload["windows"][0]["fc_matrix"]) == module_count
    assert "within_network_stability" in payload["windows"][0]["metrics"]


def test_build_empirical_viewer_payloads_group_subject_and_gallery_shapes() -> None:
    def _run_view(subject: str, session: str, run: str, offset: float) -> dict[str, object]:
        return {
            "subject": subject,
            "session": session,
            "run": run,
            "relative_path": f"{subject}/{session}/func/{run}.nii.gz",
            "window_count": 2,
            "global_signal": [0.1 + offset, 0.2 + offset, 0.3 + offset],
            "module_time_series": [[offset] * len(MODULE_NAMES), [offset + 1.0] * len(MODULE_NAMES)],
            "metrics": {
                "within_network_stability": 0.2 + offset,
                "cross_network_communication": 0.1 + offset,
                "thalamic_coupling": 0.15 + offset,
                "hierarchical_compression": 0.05 + offset,
                "entropy_diversity": 0.9 - offset,
                "switching_rate": 0.2 + offset,
                "metastability_proxy": 1.0 + offset,
                "effective_barrier_proxy": 3.0 - offset,
            },
            "fc_matrix": np.full((len(MODULE_NAMES), len(MODULE_NAMES)), 0.1 + offset).tolist(),
            "mean_raw_preview": {
                "axial": [[1.0, 2.0], [3.0, 4.0]],
                "coronal": [[1.0, 2.0], [3.0, 4.0]],
                "sagittal": [[1.0, 2.0], [3.0, 4.0]],
            },
            "windows": [
                {
                    "index": 0,
                    "start_index": 0,
                    "end_index": 2,
                    "fc_matrix": np.full((len(MODULE_NAMES), len(MODULE_NAMES)), 0.2 + offset).tolist(),
                    "metrics": {
                        "within_network_stability": 0.25 + offset,
                        "cross_network_communication": 0.15 + offset,
                        "thalamic_coupling": 0.16 + offset,
                        "hierarchical_compression": 0.06 + offset,
                        "entropy_diversity": 0.85 - offset,
                        "switching_rate": 0.3 + offset,
                        "metastability_proxy": 1.05 + offset,
                        "effective_barrier_proxy": 2.5 - offset,
                    },
                    "raw_preview": {
                        "axial": [[1.0, 2.0], [3.0, 4.0]],
                        "coronal": [[1.0, 2.0], [3.0, 4.0]],
                        "sagittal": [[1.0, 2.0], [3.0, 4.0]],
                    },
                },
                {
                    "index": 1,
                    "start_index": 2,
                    "end_index": 3,
                    "fc_matrix": np.full((len(MODULE_NAMES), len(MODULE_NAMES)), 0.25 + offset).tolist(),
                    "metrics": {
                        "within_network_stability": 0.28 + offset,
                        "cross_network_communication": 0.18 + offset,
                        "thalamic_coupling": 0.18 + offset,
                        "hierarchical_compression": 0.08 + offset,
                        "entropy_diversity": 0.82 - offset,
                        "switching_rate": 0.32 + offset,
                        "metastability_proxy": 1.08 + offset,
                        "effective_barrier_proxy": 2.4 - offset,
                    },
                    "raw_preview": {
                        "axial": [[1.0, 2.0], [3.0, 4.0]],
                        "coronal": [[1.0, 2.0], [3.0, 4.0]],
                        "sagittal": [[1.0, 2.0], [3.0, 4.0]],
                    },
                },
            ],
        }

    payloads = build_empirical_viewer_payloads(
        run_views=[
            _run_view("sub-001", "ses-PLCB", "run-01", 0.0),
            _run_view("sub-001", "ses-LSD", "run-01", 0.05),
            _run_view("sub-002", "ses-PLCB", "run-01", 0.02),
            _run_view("sub-002", "ses-LSD", "run-01", 0.08),
        ],
        modules=MODULE_NAMES,
        gallery=[
            {
                "label": "Empirical group traces",
                "path": str(Path("results") / "stage_2" / "figures" / "empirical_group_traces.html"),
            }
        ],
    )

    assert payloads["group_overview"]["default_subject"] == "sub-001"
    assert payloads["group_overview"]["subjects"] == ["sub-001", "sub-002"]
    assert payloads["group_overview"]["runs"] == ["run-01"]
    assert set(payloads["group_overview"]["conditions"]) == {"ses-PLCB", "ses-LSD"}
    assert payloads["group_overview"]["paired_subject_count"] == 2
    assert "metrics_std" in payloads["group_overview"]["conditions"]["ses-PLCB"]
    assert "module_time_series_std" in payloads["group_overview"]["conditions"]["ses-LSD"]
    assert "delta_metrics" in payloads["group_overview"]
    assert "delta_metrics_std" in payloads["group_overview"]
    assert payloads["subject_index"]["sub-001"] == ["run-01"]
    subject_view = payloads["subject_views"]["sub-001"]["run-01"]
    assert set(subject_view["conditions"]) == {"ses-PLCB", "ses-LSD"}
    assert len(subject_view["window_deltas"]) == 2
    assert payloads["group_overview"]["gallery"][0]["label"] == "Empirical group traces"


def test_build_empirical_run_views_from_records_resolves_relative_time_series_paths(
    tmp_path: Path,
) -> None:
    dataset_dir = tmp_path / "dataset"
    output_dir = tmp_path / "stage_2"
    run_relative_path = Path("sub-001") / "ses-PLCB" / "func" / "example.nii.gz"
    run_path = dataset_dir / run_relative_path
    run_path.parent.mkdir(parents=True, exist_ok=True)

    volume = np.zeros((2, 2, 2, 6), dtype=float)
    for index in range(6):
        volume[..., index] = index
    nib.save(nib.Nifti1Image(volume, affine=np.eye(4)), run_path)

    time_series_path = output_dir / "module_time_series" / "example.npy"
    time_series_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(
        time_series_path,
        np.asarray([[float(index)] * len(MODULE_NAMES) for index in range(6)], dtype=float),
    )

    record = SimpleNamespace(
        subject="sub-001",
        session="ses-PLCB",
        run="run-01",
        relative_path=str(run_relative_path),
        time_series_path=str(Path("module_time_series") / "example.npy"),
    )

    run_views = build_empirical_run_views_from_records(
        [record],
        dataset_dir=dataset_dir,
        output_dir=output_dir,
        modules=MODULE_NAMES,
        window_count=2,
        preview_size=2,
    )

    assert len(run_views) == 1
    assert run_views[0]["subject"] == "sub-001"
    assert len(run_views[0]["module_time_series"]) == 6
