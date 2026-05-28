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


def test_write_thesis_upgrade_status_writes_strict_audit(tmp_path: Path) -> None:
    status = write_thesis_upgrade_status(tmp_path)

    status_path = tmp_path / "results" / "thesis_upgrade" / "thesis_upgrade_status.json"
    report_path = tmp_path / "results" / "thesis_upgrade" / "thesis_upgrade_status.md"

    assert status_path.exists()
    assert report_path.exists()
    assert status["source_path"] == "results/thesis_upgrade/thesis_upgrade_status.json"
    assert "Strict Completion Audit" in report_path.read_text(encoding="utf-8")
