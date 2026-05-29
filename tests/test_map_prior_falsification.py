import json
from pathlib import Path

from lsd_thesis.map_prior_falsification import build_map_prior_falsification_status, write_map_prior_falsification_status


def test_map_prior_falsification_fails_closed_without_inputs(tmp_path: Path) -> None:
    status = build_map_prior_falsification_status(tmp_path)

    assert status["analysis_status"] == "blocked_or_incomplete_map_prior_falsification"
    assert status["negative_result_ready"] is False
    assert status["claim_status"] == "not_supported_yet"


def test_map_prior_falsification_marks_negative_result_when_fdr_and_ci_fail(tmp_path: Path) -> None:
    output_dir = tmp_path / "results" / "cortical_maps"
    output_dir.mkdir(parents=True)
    (output_dir / "cortical_map_alignment_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_module_level_external_map_alignment",
                "fdr_supported_count": 0,
                "best_alignment": {"q_value": 0.8, "ci_overlaps_zero": True},
                "claim_readiness": {"strong_receptor_myelin_gradient_claim": "not_supported_yet"},
            }
        ),
        encoding="utf-8",
    )
    (output_dir / "neuromaps_spatial_null_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_schaefer100_full_map_family_moran_spatial_nulls",
                "spatial_autocorrelation_nulls_complete": True,
                "map_family_moran_nulls": {
                    "fdr_supported_count": 0,
                    "family_coverage": {
                        "receptor": True,
                        "myelin": True,
                        "functional_gradient": True,
                        "gene_expression": True,
                    },
                    "best_result": {"q": 0.99, "fdr_pass": False, "ci_crosses_zero": True},
                    "results": [{"q": 0.99, "map_family": "receptor"}],
                },
            }
        ),
        encoding="utf-8",
    )

    status = build_map_prior_falsification_status(tmp_path)

    assert status["analysis_status"] == "implemented_negative_map_prior_result"
    assert status["negative_result_ready"] is True
    assert status["claim_status"] == "not_supported_yet"
    assert "formally downgraded" in status["claim_effect"]


def test_write_map_prior_falsification_status_writes_artifacts(tmp_path: Path) -> None:
    status = write_map_prior_falsification_status(tmp_path)

    assert status["source_path"] == "results/cortical_maps/map_prior_falsification_status.json"
    assert (tmp_path / "results" / "cortical_maps" / "map_prior_falsification_status.json").exists()
    assert (tmp_path / "results" / "cortical_maps" / "map_prior_falsification_status.md").exists()
