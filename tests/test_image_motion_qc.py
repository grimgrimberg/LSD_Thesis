import json
from pathlib import Path

import nibabel as nib
import numpy as np

from lsd_thesis.image_motion_qc import build_image_motion_qc_status, summarize_bold_image


def _write_bold(path: Path, scale: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.ones((5, 5, 5, 6), dtype=np.float32) * 20.0
    for timepoint in range(data.shape[3]):
        data[2, 2, 2, timepoint] += scale * (timepoint + 1)
        data[min(4, 1 + timepoint % 3), 3, 2, timepoint] += scale * 0.5
    image = nib.Nifti1Image(data, affine=np.diag([2.0, 2.0, 2.0, 1.0]))
    nib.save(image, str(path))


def _write_subject_view(root: Path, subject: str, run: str, metric_value: float) -> None:
    view = {
        "subject": subject,
        "run": run,
        "conditions": {
            "ses-LSD": {
                "relative_path": f"data/ds003059/{subject}/ses-LSD/func/{subject}_ses-LSD_task-rest_{run}_bold.nii.gz"
            },
            "ses-PLCB": {
                "relative_path": f"data/ds003059/{subject}/ses-PLCB/func/{subject}_ses-PLCB_task-rest_{run}_bold.nii.gz"
            },
        },
        "delta_metrics": {
            "switching_rate": metric_value,
            "metastability_proxy": metric_value * 0.25,
        },
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{subject}_{run}.json").write_text(json.dumps(view), encoding="utf-8")


def test_summarize_bold_image_reports_image_qc_features(tmp_path: Path) -> None:
    path = tmp_path / "bold.nii.gz"
    _write_bold(path, scale=4.0)

    summary = summarize_bold_image(path, repo_root=tmp_path, stride=1)

    assert summary["volume_count"] == 6
    assert summary["sampled_voxel_count"] > 0
    assert summary["image_dvars_mean"] > 0
    assert summary["com_displacement_max_mm"] >= 0


def test_image_motion_qc_builds_subject_run_associations(tmp_path: Path) -> None:
    view_root = tmp_path / "results" / "stage_2" / "empirical_viewer" / "subject_views"
    for index in range(4):
        subject = f"sub-{index + 1:03d}"
        run = "run-01"
        _write_subject_view(view_root, subject, run, metric_value=float(index + 1))
        _write_bold(
            tmp_path / "data" / "ds003059" / subject / "ses-LSD" / "func" / f"{subject}_ses-LSD_task-rest_{run}_bold.nii.gz",
            scale=float(index + 2),
        )
        _write_bold(
            tmp_path / "data" / "ds003059" / subject / "ses-PLCB" / "func" / f"{subject}_ses-PLCB_task-rest_{run}_bold.nii.gz",
            scale=1.0,
        )

    status = build_image_motion_qc_status(tmp_path, stride=1)

    assert status["analysis_status"] == "implemented_image_derived_motion_qc_control"
    assert status["image_motion_qc_ready"] is True
    assert status["subject_run_count"] == 4
    assert status["raw_bold_file_count"] == 8
    assert status["association_rows"]


def test_image_motion_qc_fails_closed_without_paired_bold(tmp_path: Path) -> None:
    view_root = tmp_path / "results" / "stage_2" / "empirical_viewer" / "subject_views"
    _write_subject_view(view_root, "sub-001", "run-01", metric_value=1.0)

    status = build_image_motion_qc_status(tmp_path, stride=1)

    assert status["image_motion_qc_ready"] is False
    assert status["analysis_status"] == "blocked_insufficient_raw_bold_subject_run_overlap"
    assert status["missing_or_failed_record_count"] == 1
