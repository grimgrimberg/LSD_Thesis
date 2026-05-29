import json
from pathlib import Path

from lsd_thesis.thesis_upgrade import build_thesis_upgrade_status, write_thesis_upgrade_status


def test_thesis_upgrade_strict_requirements_fail_closed(tmp_path: Path) -> None:
    status = build_thesis_upgrade_status(tmp_path)

    requirements = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}

    assert set(requirements) == {
        "schaefer_yeo_high_resolution",
        "neuromaps_spatial_autocorrelation_nulls",
        "ds006072_external_validation",
        "motion_confound_control_result",
        "receptor_myelin_gradient_claim",
        "project_phase",
    }
    assert requirements["schaefer_yeo_high_resolution"]["complete"] is False
    assert requirements["neuromaps_spatial_autocorrelation_nulls"]["complete"] is False
    assert requirements["ds006072_external_validation"]["complete"] is False
    assert requirements["motion_confound_control_result"]["complete"] is False
    assert requirements["receptor_myelin_gradient_claim"]["complete"] is False
    assert requirements["project_phase"]["status"] == "pi_pitch_ready_research_proposal_not_completed_thesis"
    assert status["readiness_summary"]["completion_status"] == "pi_pitch_ready_research_proposal_not_completed_thesis"
    assert status["components"]["neuromaps_spatial_nulls"]["gate"]["ready"] is False
    assert "not a full spatial-autocorrelation null model" in status["components"]["neuromaps_spatial_nulls"]["claim_guardrail"]


def test_thesis_upgrade_marks_schaefer_yeo_complete_when_outputs_exist(tmp_path: Path) -> None:
    sensitivity_dir = tmp_path / "results" / "parcellation_sensitivity"
    canonical_dir = tmp_path / "results" / "stage_2" / "parcellations" / "schaefer_100_yeo_7"
    ranking_dir = sensitivity_dir / "schaefer_100_yeo_7"
    viewer_dir = canonical_dir / "empirical_viewer"
    ranking_dir.mkdir(parents=True)
    viewer_dir.mkdir(parents=True)
    canonical_dir.mkdir(parents=True, exist_ok=True)
    (canonical_dir / "parcellation_extraction_summary.json").write_text("{}", encoding="utf-8")
    (viewer_dir / "group_overview.json").write_text("{}", encoding="utf-8")
    (ranking_dir / "summary.json").write_text("{}", encoding="utf-8")
    (sensitivity_dir / "parcellation_sensitivity_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_status_matrix",
                "rows": [
                    {
                        "parcellation_id": "schaefer_100_yeo_7",
                        "status": "implemented_mechanism_ranking",
                        "pair_count": 30,
                        "subject_count": 15,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    parcellation = status["components"]["canonical_parcellation"]

    assert parcellation["gate"]["ready"] is True
    assert parcellation["strict_requirement"]["complete"] is True
    assert parcellation["strict_requirement"]["missing"].startswith("None:")
    assert parcellation["completion_checks"] == {
        "has_extraction_summary": True,
        "has_empirical_viewer": True,
        "has_mechanism_ranking": True,
    }


def test_thesis_upgrade_external_validation_requires_comparable_scoring(tmp_path: Path) -> None:
    result_dir = tmp_path / "results" / "psilocybin_ds006072"
    result_dir.mkdir(parents=True)
    (result_dir / "external_validation_readiness.json").write_text(
        json.dumps(
            {
                "analysis_status": "extraction_contract_ready_missing_local_cifti_payloads",
                "primary_subject_count": 7,
                "primary_subjects_local_ready": 0,
                "blocker": "local payloads absent",
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    external = status["components"]["external_validation"]

    assert external["gate"]["ready"] is False
    assert external["strict_requirement"]["complete"] is False
    assert external["strict_requirement"]["status"] == "extraction_contract_ready_missing_local_cifti_payloads"
    assert "not comparable psilocybin/control dynamic extraction" in external["strict_requirement"]["missing"]


def test_thesis_upgrade_marks_external_validation_complete_only_with_locked_comparable_scoring(tmp_path: Path) -> None:
    result_dir = tmp_path / "results" / "psilocybin_ds006072"
    result_dir.mkdir(parents=True)
    (result_dir / "comparable_empirical_validation_summary.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_ds006072_unchanged_scoring_validation",
                "unchanged_scoring_applied": True,
                "scoring_lock_verified": True,
                "subject_count": 3,
                "minimum_comparable_subjects": 3,
                "replication_status": "ranking_replicates_lsd_top_layer",
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    external = status["components"]["external_validation"]

    assert external["gate"]["ready"] is True
    assert external["strict_requirement"]["complete"] is True
    assert external["scoring_lock_verified"] is True
    assert external["comparable_subject_count"] == 3


def test_write_thesis_upgrade_status_writes_strict_audit(tmp_path: Path) -> None:
    status = write_thesis_upgrade_status(tmp_path)

    status_path = tmp_path / "results" / "thesis_upgrade" / "thesis_upgrade_status.json"
    report_path = tmp_path / "results" / "thesis_upgrade" / "thesis_upgrade_status.md"

    assert status_path.exists()
    assert report_path.exists()
    assert status["source_path"] == "results/thesis_upgrade/thesis_upgrade_status.json"
    assert "Strict Completion Audit" in report_path.read_text(encoding="utf-8")
