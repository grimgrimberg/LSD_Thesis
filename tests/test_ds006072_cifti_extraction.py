from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from lsd_thesis.ds006072_cifti_extraction import (
    MODULE_NAMES,
    _extract_structure_family_series_from_dense,
    _resample_matrix,
    build_ds006072_cifti_extraction_status,
    write_ds006072_cifti_extraction_status,
)


def test_extract_structure_family_series_from_dense_uses_weighted_structure_means() -> None:
    data = np.arange(10 * 16, dtype=float).reshape(10, 16)
    structure_slices = {
        module: [slice(index * 2, index * 2 + 2)]
        for index, module in enumerate(MODULE_NAMES)
    }

    series = _extract_structure_family_series_from_dense(data, structure_slices)

    assert series.shape == (10, len(MODULE_NAMES))
    assert np.allclose(np.mean(series, axis=0), 0.0)
    assert np.allclose(np.std(series, axis=0), 1.0)


def test_resample_matrix_matches_requested_timepoint_count() -> None:
    matrix = np.asarray([[0.0, 0.0], [10.0, 20.0], [20.0, 40.0]], dtype=float)

    resampled = _resample_matrix(matrix, 5)

    assert resampled.shape == (5, 2)
    assert np.allclose(resampled[0], [0.0, 0.0])
    assert np.allclose(resampled[-1], [20.0, 40.0])


def test_cifti_extraction_status_fails_closed_without_payload_plan(tmp_path: Path) -> None:
    status = build_ds006072_cifti_extraction_status(tmp_path)

    assert status["analysis_status"] == "blocked_missing_minimum_payload_plan"
    assert status["cifti_empirical_viewer_ready"] is False


def test_cifti_extraction_status_detects_existing_subject_views(tmp_path: Path) -> None:
    result_dir = tmp_path / "results" / "psilocybin_ds006072"
    subject_views = result_dir / "empirical_viewer" / "subject_views"
    subject_views.mkdir(parents=True)
    (result_dir / "minimum_payload_plan.json").write_text(
        json.dumps(
            {
                "minimum_subjects_required": 3,
                "minimum_payloads_local_ready": True,
                "minimum_payload_plan_ready": True,
            }
        ),
        encoding="utf-8",
    )
    for index in range(3):
        (subject_views / f"P{index + 1}_run-01.json").write_text("{}", encoding="utf-8")

    status = build_ds006072_cifti_extraction_status(tmp_path)

    assert status["analysis_status"] == "implemented_ds006072_cifti_structure_family_empirical_viewer"
    assert status["cifti_empirical_viewer_ready"] is True
    assert status["subject_view_count"] == 3


def test_write_cifti_extraction_status_writes_artifacts(tmp_path: Path) -> None:
    status = write_ds006072_cifti_extraction_status(tmp_path)

    assert status["source_path"] == "results/psilocybin_ds006072/cifti_empirical_extraction_status.json"
    assert (tmp_path / status["source_path"]).exists()
    assert (tmp_path / status["report_path"]).exists()
