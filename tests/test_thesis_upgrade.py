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
    assert status["readiness_summary"]["strict_missing_gates"] == 6
    assert status["readiness_summary"]["strict_missing_requirement_ids"] == list(requirements)
    assert status["readiness_summary"]["remaining_hard_requirements"] == [
        "fMRIPrep FD/DVARS/censoring motion proof",
        "stronger parcellation-matched external validation",
    ]
    assert status["components"]["neuromaps_spatial_nulls"]["gate"]["ready"] is False
    assert "not a full spatial-autocorrelation null model" in status["components"]["neuromaps_spatial_nulls"]["claim_guardrail"]


def test_thesis_upgrade_marks_map_prior_claim_complete_when_resolved_negative(tmp_path: Path) -> None:
    output_dir = tmp_path / "results" / "cortical_maps"
    output_dir.mkdir(parents=True)
    (output_dir / "cortical_map_alignment_status.json").write_text(
        json.dumps(
            {
                "claim_readiness": {"strong_receptor_myelin_gradient_claim": "not_supported_yet"},
                "fdr_supported_count": 0,
            }
        ),
        encoding="utf-8",
    )
    (output_dir / "map_prior_falsification_status.json").write_text(
        json.dumps(
            {
                "negative_result_ready": True,
                "claim_status": "resolved_negative_not_promoted",
                "claim_resolution": {
                    "joint_fdr_and_ci_support_count": 0,
                    "strict_gate_resolved": True,
                },
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    requirement = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}[
        "receptor_myelin_gradient_claim"
    ]

    assert requirement["complete"] is True
    assert requirement["status"] == "resolved_negative_not_promoted"
    assert "negative/control result" in requirement["missing"]


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


def test_thesis_upgrade_keeps_strict_motion_incomplete_with_only_image_motion_qc(tmp_path: Path) -> None:
    confound_dir = tmp_path / "results" / "confound_controls"
    confound_dir.mkdir(parents=True)
    (confound_dir / "image_motion_qc_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_image_derived_motion_qc_control",
                "image_motion_qc_ready": True,
                "claim_status": "no_image_motion_qc_sensitivity_detected",
                "high_risk_image_motion_qc_association_count": 0,
                "unstable_high_burden_exclusion_count": 0,
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    motion = status["components"]["motion_confound"]
    requirement = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}[
        "motion_confound_control_result"
    ]

    assert motion["gate"]["ready"] is True
    assert motion["image_motion_qc_ready"] is True
    assert motion["fmriprep_motion_control_ready"] is False
    assert requirement["complete"] is False
    assert requirement["status"] == "blocked_missing_fmriprep_fd_dvars_censoring_motion_proof"
    assert "strict completion still requires fMRIPrep FD/DVARS/censoring motion proof" in requirement["missing"]


def test_thesis_upgrade_surfaces_fmriprep_preflight_status(tmp_path: Path) -> None:
    confound_dir = tmp_path / "results" / "confound_controls"
    confound_dir.mkdir(parents=True)
    (confound_dir / "image_motion_qc_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_image_derived_motion_qc_control",
                "image_motion_qc_ready": True,
            }
        ),
        encoding="utf-8",
    )
    (confound_dir / "fmriprep_motion_proof_plan.json").write_text(
        json.dumps(
            {
                "analysis_status": "blocked_derivative_snapshot_not_valid_raw_fmriprep_input",
                "fmriprep_motion_proof_ready": False,
                "blocker": "DatasetType=derivative",
                "next_action": "Obtain original raw BIDS or author confounds.",
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    motion = status["components"]["motion_confound"]
    requirement = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}[
        "motion_confound_control_result"
    ]

    assert motion["fmriprep_motion_proof_plan_ready"] is False
    assert motion["fmriprep_motion_proof_plan_status"] == "blocked_derivative_snapshot_not_valid_raw_fmriprep_input"
    assert "blocked_derivative_snapshot_not_valid_raw_fmriprep_input" in requirement["missing"]
    assert requirement["next_action"] == "Obtain original raw BIDS or author confounds."


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
                "ds006072_top_layer": "C",
                "lsd_reference_top_layer": "C",
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
    assert external["stronger_external_validation_ready"] is False
    assert external["ds006072_top_layer"] == "C"
    assert external["lsd_reference_top_layer"] == "C"
    assert external["gate"]["blocker"] == (
        "Comparable ds006072 empirical records were scored unchanged; upgrade scope if stronger parcellation matching is needed."
    )


def test_thesis_upgrade_project_phase_completes_only_with_hard_motion_and_stronger_external_validation(
    tmp_path: Path,
) -> None:
    sensitivity_dir = tmp_path / "results" / "parcellation_sensitivity"
    canonical_dir = tmp_path / "results" / "stage_2" / "parcellations" / "schaefer_100_yeo_7"
    viewer_dir = canonical_dir / "empirical_viewer"
    ranking_dir = sensitivity_dir / "schaefer_100_yeo_7"
    viewer_dir.mkdir(parents=True)
    ranking_dir.mkdir(parents=True)
    (canonical_dir / "parcellation_extraction_summary.json").write_text("{}", encoding="utf-8")
    (viewer_dir / "group_overview.json").write_text("{}", encoding="utf-8")
    (ranking_dir / "summary.json").write_text("{}", encoding="utf-8")
    (sensitivity_dir / "parcellation_sensitivity_status.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "parcellation_id": "schaefer_100_yeo_7",
                        "status": "implemented_mechanism_ranking",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    cortical_dir = tmp_path / "results" / "cortical_maps"
    cortical_dir.mkdir(parents=True)
    (cortical_dir / "neuromaps_spatial_null_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_schaefer100_full_map_family_moran_spatial_nulls",
                "spatial_autocorrelation_nulls_complete": True,
                "receptor_spatial_nulls_complete": True,
                "receptor_moran_nulls": {
                    "family_coverage": {
                        "receptor": True,
                        "myelin": True,
                        "functional_gradient": True,
                        "gene_expression": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (cortical_dir / "cortical_map_alignment_status.json").write_text("{}", encoding="utf-8")
    (cortical_dir / "map_prior_falsification_status.json").write_text(
        json.dumps(
            {
                "negative_result_ready": True,
                "claim_status": "resolved_negative_not_promoted",
            }
        ),
        encoding="utf-8",
    )

    motion_dir = tmp_path / "results" / "setting_seed" / "motion"
    confound_dir = tmp_path / "results" / "confound_controls"
    motion_dir.mkdir(parents=True)
    confound_dir.mkdir(parents=True)
    (motion_dir / "motion_summary.json").write_text(
        json.dumps({"motion_analysis_ready": True}),
        encoding="utf-8",
    )
    (confound_dir / "motion_confound_control_status.json").write_text(
        json.dumps({"analysis_status": "implemented_fmriprep_fd_dvars_censoring_control"}),
        encoding="utf-8",
    )

    external_dir = tmp_path / "results" / "psilocybin_ds006072"
    external_dir.mkdir(parents=True)
    (external_dir / "comparable_empirical_validation_summary.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_ds006072_unchanged_scoring_validation",
                "unchanged_scoring_applied": True,
                "scoring_lock_verified": True,
                "subject_count": 3,
                "minimum_comparable_subjects": 3,
                "stronger_external_validation_ready": True,
                "schaefer100_empirical_viewer_ready": True,
                "validation_scope": "parcellation_matched_schaefer100_yeo7_external_validation",
                "replication_status": "ranking_differs_from_lsd_top_layer",
                "ds006072_top_layer": "E",
                "lsd_reference_top_layer": "C",
            }
        ),
        encoding="utf-8",
    )
    (external_dir / "cifti_empirical_extraction_status.json").write_text(
        json.dumps(
            {
                "schaefer100_empirical_viewer_ready": True,
                "stronger_external_validation_ready": True,
                "schaefer100_module_contract": "CIFTI fsLR cortex Schaefer100/Yeo7 parcel external validation",
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    requirements = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}
    external = status["components"]["external_validation"]

    assert requirements["project_phase"]["complete"] is True
    assert requirements["project_phase"]["status"] == "completed_neuroscience_thesis"
    assert status["readiness_summary"]["completion_status"] == "completed_neuroscience_thesis"
    assert "ranking_differs_from_lsd_top_layer" in external["gate"]["blocker"]
    assert "ds006072 top=E, LSD reference top=C" in external["gate"]["blocker"]


def test_thesis_upgrade_project_phase_names_only_remaining_hard_requirements(tmp_path: Path) -> None:
    sensitivity_dir = tmp_path / "results" / "parcellation_sensitivity"
    canonical_dir = tmp_path / "results" / "stage_2" / "parcellations" / "schaefer_100_yeo_7"
    viewer_dir = canonical_dir / "empirical_viewer"
    ranking_dir = sensitivity_dir / "schaefer_100_yeo_7"
    viewer_dir.mkdir(parents=True)
    ranking_dir.mkdir(parents=True)
    (canonical_dir / "parcellation_extraction_summary.json").write_text("{}", encoding="utf-8")
    (viewer_dir / "group_overview.json").write_text("{}", encoding="utf-8")
    (ranking_dir / "summary.json").write_text("{}", encoding="utf-8")
    (sensitivity_dir / "parcellation_sensitivity_status.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "parcellation_id": "schaefer_100_yeo_7",
                        "status": "implemented_mechanism_ranking",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    cortical_dir = tmp_path / "results" / "cortical_maps"
    cortical_dir.mkdir(parents=True)
    (cortical_dir / "neuromaps_spatial_null_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_schaefer100_full_map_family_moran_spatial_nulls",
                "spatial_autocorrelation_nulls_complete": True,
                "receptor_spatial_nulls_complete": True,
                "receptor_moran_nulls": {
                    "family_coverage": {
                        "receptor": True,
                        "myelin": True,
                        "functional_gradient": True,
                        "gene_expression": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (cortical_dir / "cortical_map_alignment_status.json").write_text("{}", encoding="utf-8")
    (cortical_dir / "map_prior_falsification_status.json").write_text(
        json.dumps(
            {
                "negative_result_ready": True,
                "claim_status": "resolved_negative_not_promoted",
            }
        ),
        encoding="utf-8",
    )

    confound_dir = tmp_path / "results" / "confound_controls"
    confound_dir.mkdir(parents=True)
    (confound_dir / "image_motion_qc_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_image_derived_motion_qc_control",
                "image_motion_qc_ready": True,
            }
        ),
        encoding="utf-8",
    )

    external_dir = tmp_path / "results" / "psilocybin_ds006072"
    external_dir.mkdir(parents=True)
    (external_dir / "comparable_empirical_validation_summary.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_ds006072_unchanged_scoring_validation",
                "unchanged_scoring_applied": True,
                "scoring_lock_verified": True,
                "subject_count": 3,
                "minimum_comparable_subjects": 3,
                "stronger_external_validation_ready": True,
                "schaefer100_empirical_viewer_ready": True,
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    project = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}["project_phase"]

    assert project["complete"] is False
    assert "fMRIPrep FD/DVARS/censoring motion proof" in project["missing"]
    assert "stronger parcellation-matched external validation" not in project["missing"]
    assert status["readiness_summary"]["strict_missing_requirement_ids"] == [
        "motion_confound_control_result",
        "project_phase",
    ]
    assert status["readiness_summary"]["remaining_hard_requirements"] == [
        "fMRIPrep FD/DVARS/censoring motion proof",
    ]


def test_write_thesis_upgrade_status_writes_strict_audit(tmp_path: Path) -> None:
    status = write_thesis_upgrade_status(tmp_path)

    status_path = tmp_path / "results" / "thesis_upgrade" / "thesis_upgrade_status.json"
    report_path = tmp_path / "results" / "thesis_upgrade" / "thesis_upgrade_status.md"

    assert status_path.exists()
    assert report_path.exists()
    assert status["source_path"] == "results/thesis_upgrade/thesis_upgrade_status.json"
    assert "Strict Completion Audit" in report_path.read_text(encoding="utf-8")
