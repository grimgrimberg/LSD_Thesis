from pathlib import Path

from lsd_thesis.neuromaps_spatial_nulls import build_neuromaps_spatial_null_status, write_neuromaps_spatial_null_status


def test_neuromaps_spatial_null_status_fails_closed_without_inputs(tmp_path: Path) -> None:
    status = build_neuromaps_spatial_null_status(tmp_path)

    assert status["spatial_autocorrelation_nulls_complete"] is False
    assert status["claim_status"] == "not_implemented_full_neuromaps_spatial_nulls"
    assert status["analysis_status"] in {
        "blocked_missing_neuromaps_dependency",
        "blocked_missing_surface_or_high_resolution_map_inputs",
    }
    assert "not a substitute" in status["claim_guardrail"]


def test_write_neuromaps_spatial_null_status_writes_artifacts(tmp_path: Path) -> None:
    status = write_neuromaps_spatial_null_status(tmp_path)

    assert status["source_path"] == "results/cortical_maps/neuromaps_spatial_null_status.json"
    assert (tmp_path / status["source_path"]).exists()
    assert (tmp_path / status["report_path"]).exists()
