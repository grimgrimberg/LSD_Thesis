from pathlib import Path

import numpy as np
import pytest

from lsd_thesis.neuromaps_spatial_nulls import (
    _benjamini_hochberg,
    _hemisphere_distance_matrices,
    _pearson_r,
    build_neuromaps_spatial_null_status,
    write_neuromaps_spatial_null_status,
)


def test_neuromaps_spatial_null_status_fails_closed_without_inputs(tmp_path: Path) -> None:
    status = build_neuromaps_spatial_null_status(tmp_path)

    assert status["spatial_autocorrelation_nulls_complete"] is False
    assert status["claim_status"] == "not_implemented_full_neuromaps_spatial_nulls"
    assert "null_api_importable" in status
    assert "neuromaps_runtime" in status
    assert status["analysis_status"] in {
        "blocked_missing_neuromaps_dependency",
        "blocked_neuromaps_null_api_not_importable",
        "blocked_missing_surface_or_high_resolution_map_inputs",
        "blocked_missing_neuromaps_surface_input_manifest",
        "blocked_receptor_moran_null_execution_failed",
        "blocked_map_family_moran_null_execution_failed",
    }
    assert "not a substitute" in status["claim_guardrail"]


def test_write_neuromaps_spatial_null_status_writes_artifacts(tmp_path: Path) -> None:
    status = write_neuromaps_spatial_null_status(tmp_path)

    assert status["source_path"] == "results/cortical_maps/neuromaps_spatial_null_status.json"
    assert (tmp_path / status["source_path"]).exists()
    assert (tmp_path / status["report_path"]).exists()


def test_spatial_null_helpers_are_deterministic() -> None:
    assert _pearson_r(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0])) == pytest.approx(1.0)

    q_values = _benjamini_hochberg([0.01, 0.04, 0.20])

    assert q_values == pytest.approx([0.03, 0.06, 0.20])


def test_hemisphere_distance_matrices_split_even_centroids() -> None:
    centroids = np.array(
        [
            [0.0, 0.0, 0.0],
            [3.0, 4.0, 0.0],
            [10.0, 0.0, 0.0],
            [10.0, 6.0, 8.0],
        ]
    )

    left, right = _hemisphere_distance_matrices(centroids)

    assert left.shape == (2, 2)
    assert right.shape == (2, 2)
    assert left[0, 1] == 5.0
    assert right[0, 1] == 10.0
