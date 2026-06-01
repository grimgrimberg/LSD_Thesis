import json
from pathlib import Path

from lsd_thesis.thesis_upgrade import build_thesis_upgrade_status, write_thesis_upgrade_status


def test_thesis_upgrade_strict_requirements_fail_closed(tmp_path: Path) -> None:
    status = build_thesis_upgrade_status(tmp_path)

    requirements = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}
    package_requirements = {row["requirement_id"]: row for row in status["package_readiness_requirements"]}

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
    assert package_requirements["public_dashboard_static_snapshot"]["complete"] is False
    assert package_requirements["reproducible_archive_publication"]["complete"] is False
    assert status["readiness_summary"]["package_complete_gates"] == 0
    assert status["readiness_summary"]["package_total_gates"] == 2
    assert status["readiness_summary"]["package_missing_requirement_ids"] == [
        "public_dashboard_static_snapshot",
        "reproducible_archive_publication",
    ]
    assert status["components"]["neuromaps_spatial_nulls"]["gate"]["ready"] is False
    assert "not a full spatial-autocorrelation null model" in status["components"]["neuromaps_spatial_nulls"]["claim_guardrail"]


def test_thesis_upgrade_neuromaps_gate_requires_full_family_coverage(tmp_path: Path) -> None:
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
                        "gene_expression": False,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (cortical_dir / "cortical_map_alignment_status.json").write_text("{}", encoding="utf-8")

    status = build_thesis_upgrade_status(tmp_path)
    neuromaps = status["components"]["neuromaps_spatial_nulls"]
    requirement = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}[
        "neuromaps_spatial_autocorrelation_nulls"
    ]

    assert neuromaps["gate"]["ready"] is False
    assert neuromaps["family_coverage_ready"] is False
    assert neuromaps["required_map_families"] == [
        "receptor",
        "myelin",
        "functional_gradient",
        "gene_expression",
    ]
    assert requirement["complete"] is False
    assert "map-family Moran spatial-null coverage is still incomplete" in requirement["missing"]


def test_thesis_upgrade_marks_map_prior_claim_complete_when_resolved_negative(tmp_path: Path) -> None:
    output_dir = tmp_path / "results" / "cortical_maps"
    output_dir.mkdir(parents=True)
    (output_dir / "cortical_map_alignment_status.json").write_text(
        json.dumps(
            {
                "claim_readiness": {
                    "strong_receptor_myelin_gradient_claim": "not_supported_yet",
                    "required_for_stronger_claim": [
                        "Re-extract empirical LSD-placebo dynamic features at a higher-resolution cortical parcellation."
                    ],
                },
                "neuromaps_status": {
                    "analysis_status": "not_run_module_level_only",
                    "recommended_next_step": "Run spatial nulls.",
                },
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
                "spatial_nulls": {
                    "analysis_status": "implemented_schaefer100_full_map_family_moran_spatial_nulls",
                    "spatial_autocorrelation_nulls_complete": True,
                },
                "claim_resolution": {
                    "joint_fdr_and_ci_support_count": 0,
                    "family_coverage_complete": True,
                    "spatial_autocorrelation_nulls_complete": True,
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
    component = status["components"]["receptor_myelin_gradient_claim"]
    assert component["gate"]["evidence"] == (
        "results/cortical_maps/cortical_map_alignment_status.json; "
        "results/cortical_maps/map_prior_falsification_status.json"
    )
    assert component["claim_readiness"]["strong_receptor_myelin_gradient_claim"] == "resolved_negative_not_promoted"
    assert "Re-extract" not in " ".join(component["claim_readiness"]["required_for_stronger_claim"])
    assert component["neuromaps_status"]["analysis_status"] == "implemented_schaefer100_full_map_family_moran_spatial_nulls"
    assert component["neuromaps_status"]["spatial_autocorrelation_nulls_complete"] is True


def test_thesis_upgrade_rejects_positive_map_prior_claim_without_ci_support(tmp_path: Path) -> None:
    output_dir = tmp_path / "results" / "cortical_maps"
    output_dir.mkdir(parents=True)
    (output_dir / "cortical_map_alignment_status.json").write_text(
        json.dumps(
            {
                "claim_readiness": {
                    "strong_receptor_myelin_gradient_claim": "supported",
                },
                "fdr_supported_count": 1,
                "best_alignment": {
                    "fdr_pass": True,
                    "ci_crosses_zero": True,
                    "q": 0.01,
                },
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    component = status["components"]["receptor_myelin_gradient_claim"]
    requirement = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}[
        "receptor_myelin_gradient_claim"
    ]

    assert component["gate"]["ready"] is False
    assert requirement["complete"] is False
    assert component["positive_claim_support_ready"] is False
    assert "FDR support and CI" in requirement["missing"]


def test_thesis_upgrade_rejects_positive_map_prior_claim_without_ci_field(tmp_path: Path) -> None:
    output_dir = tmp_path / "results" / "cortical_maps"
    output_dir.mkdir(parents=True)
    (output_dir / "cortical_map_alignment_status.json").write_text(
        json.dumps(
            {
                "claim_readiness": {
                    "strong_receptor_myelin_gradient_claim": "supported",
                },
                "fdr_supported_count": 1,
                "best_alignment": {
                    "fdr_pass": True,
                    "q": 0.01,
                },
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    component = status["components"]["receptor_myelin_gradient_claim"]

    assert component["gate"]["ready"] is False
    assert component["positive_claim_support_ready"] is False
    assert component["best_alignment_ci_checked"] is False


def _write_valid_schaefer_yeo_outputs(tmp_path: Path) -> None:
    sensitivity_dir = tmp_path / "results" / "parcellation_sensitivity"
    canonical_dir = tmp_path / "results" / "stage_2" / "parcellations" / "schaefer_100_yeo_7"
    ranking_dir = sensitivity_dir / "schaefer_100_yeo_7"
    viewer_dir = canonical_dir / "empirical_viewer"
    ranking_dir.mkdir(parents=True)
    viewer_dir.mkdir(parents=True)
    canonical_dir.mkdir(parents=True, exist_ok=True)
    modules = [f"parcel_{index:03d}" for index in range(100)]
    subjects = ["sub-001", "sub-002"]
    runs = ["run-01", "run-03"]
    (canonical_dir / "parcellation_extraction_summary.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_schaefer_empirical_viewer",
                "parcellation_id": "schaefer_100_yeo_7",
                "subject_count": len(subjects),
                "record_count": 8,
                "module_count": len(modules),
                "ranking_pair_count": 4,
            }
        ),
        encoding="utf-8",
    )
    (viewer_dir / "group_overview.json").write_text(
        json.dumps(
            {
                "subjects": subjects,
                "runs": runs,
                "module_names": modules,
            }
        ),
        encoding="utf-8",
    )
    (ranking_dir / "summary.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_first_pass",
                "subject_count": len(subjects),
                "pair_count": 4,
                "modules": modules,
                "mechanism_ranking": [{"rank": 1, "layer": "C"}],
            }
        ),
        encoding="utf-8",
    )
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


def test_thesis_upgrade_marks_schaefer_yeo_complete_when_outputs_exist(tmp_path: Path) -> None:
    _write_valid_schaefer_yeo_outputs(tmp_path)

    status = build_thesis_upgrade_status(tmp_path)
    parcellation = status["components"]["canonical_parcellation"]

    assert parcellation["gate"]["ready"] is True
    assert parcellation["strict_requirement"]["complete"] is True
    assert parcellation["strict_requirement"]["missing"].startswith("None:")
    assert parcellation["completion_checks"] == {
        "has_extraction_summary": True,
        "has_empirical_viewer": True,
        "has_mechanism_ranking": True,
        "extraction_summary_ready": True,
        "empirical_viewer_ready": True,
        "mechanism_ranking_ready": True,
    }


def test_thesis_upgrade_rejects_empty_schaefer_yeo_outputs(tmp_path: Path) -> None:
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
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    parcellation = status["components"]["canonical_parcellation"]

    assert parcellation["gate"]["ready"] is False
    assert parcellation["strict_requirement"]["complete"] is False
    assert parcellation["completion_checks"]["extraction_summary_ready"] is False
    assert parcellation["completion_checks"]["empirical_viewer_ready"] is False
    assert parcellation["completion_checks"]["mechanism_ranking_ready"] is False


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

    assert motion["gate"]["ready"] is False
    assert motion["image_motion_qc_ready"] is True
    assert motion["proxy_control_layer_ready"] is True
    assert motion["fmriprep_motion_control_ready"] is False
    assert requirement["complete"] is False
    assert requirement["status"] == "blocked_missing_fmriprep_fd_dvars_censoring_motion_proof"
    assert "strict completion still requires fMRIPrep FD/DVARS/censoring motion proof" in requirement["missing"]


def test_thesis_upgrade_archive_gate_requires_release_url_and_doi(tmp_path: Path) -> None:
    archive_dir = tmp_path / "results" / "reproducible_archive"
    archive_dir.mkdir(parents=True)
    (archive_dir / "ARCHIVE_MANIFEST.json").write_text(
        json.dumps(
            {
                "schema_version": "reproducible_archive_manifest.v1",
                "artifact_count": 3,
                "artifacts": [],
                "recommended_publication": {
                    "code": "GitHub public repository release",
                    "doi": "Zenodo DOI minted from GitHub release",
                },
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    archive = status["components"]["reproducible_archive"]

    assert archive["archive_manifest_ready"] is True
    assert archive["archive_publication_ready"] is False
    assert archive["archive_publication_metadata"] == {
        "release_url_valid": False,
        "doi_valid": False,
        "archive_publication_ready": False,
    }
    assert archive["gate"]["ready"] is False
    assert archive["gate"]["status"] == "manifest_ready_release_doi_missing"
    assert "release and Zenodo DOI" in archive["gate"]["blocker"]


def test_thesis_upgrade_rocket_internal_signal_is_not_thesis_strength_ready(tmp_path: Path) -> None:
    rocket_dir = tmp_path / "results" / "training" / "rocket_condition_benchmark"
    rocket_dir.mkdir(parents=True)
    (rocket_dir / "comparison_summary.json").write_text(
        json.dumps(
            {
                "cv_strategy": "approved CV5 subject-disjoint manifest",
                "primary_evaluation_unit": "subject_session_run_aggregated_windows",
                "window_random_reporting": False,
                "model": "rocket_random_convolution_features_logistic_regression",
                "aggregate": {
                    "balanced_accuracy_mean": 0.67,
                    "roc_auc_mean": 0.71,
                },
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    rocket = status["components"]["rocket_strengthening"]

    assert rocket["internal_integrity_ready"] is True
    assert rocket["thesis_strength_ready"] is False
    assert rocket["strengthening_coverage"] == {
        "subject_disjoint_cv": True,
        "subject_session_run_aggregation": True,
        "no_window_random_reporting": True,
        "permutation_null": False,
        "calibration": False,
        "minirocket_or_multirocket_variant": False,
        "performance_floor": True,
    }
    assert rocket["gate"]["status"] == "supporting_internal_signal"
    assert rocket["gate"]["ready"] is False


def test_thesis_upgrade_rocket_strength_requires_performance_floor(tmp_path: Path) -> None:
    rocket_dir = tmp_path / "results" / "training" / "rocket_condition_benchmark"
    rocket_dir.mkdir(parents=True)
    (rocket_dir / "comparison_summary.json").write_text(
        json.dumps(
            {
                "cv_strategy": "approved CV5 subject-disjoint manifest",
                "primary_evaluation_unit": "subject_session_run_aggregated_windows",
                "window_random_reporting": False,
                "model": "minirocket_logistic_regression",
                "permutation_null": {"p_value": 0.04},
                "calibration": {"brier_score": 0.24},
                "aggregate": {
                    "balanced_accuracy_mean": 0.51,
                    "roc_auc_mean": 0.58,
                },
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    rocket = status["components"]["rocket_strengthening"]

    assert rocket["gate"]["ready"] is False
    assert rocket["gate"]["status"] == "supporting_internal_signal"
    assert rocket["performance_floor_ready"] is False
    assert rocket["strengthening_coverage"]["performance_floor"] is False


def _public_dashboard_status_payload(completion_status: str = "research_demo_ready_not_completed_thesis") -> dict[str, object]:
    return {
        "schema_version": "thesis_upgrade_status.v1",
        "generated_at_utc": "ignored-by-static-freshness-check",
        "readiness_summary": {
            "ready_gates": 6,
            "total_gates": 9,
            "strict_complete_gates": 4,
            "strict_total_gates": 6,
            "strict_missing_requirement_ids": ["motion_confound_control_result", "project_phase"],
            "package_complete_gates": 1,
            "package_total_gates": 2,
            "package_missing_requirement_ids": ["reproducible_archive_publication"],
            "remaining_hard_requirements": ["fMRIPrep FD/DVARS/censoring motion proof"],
            "remaining_packaging_requirements": ["Reproducible archive publication"],
            "completion_status": completion_status,
            "thesis_status": completion_status,
        },
        "gates": [
            {
                "label": "Public dashboard",
                "status": "static_snapshot_ready",
                "ready": True,
            }
        ],
        "strict_completion_requirements": [
            {
                "requirement_id": "motion_confound_control_result",
                "status": "implemented_image_derived_motion_qc_control",
                "complete": False,
            },
            {
                "requirement_id": "project_phase",
                "status": completion_status,
                "complete": False,
            },
        ],
        "package_readiness_requirements": [
            {
                "requirement_id": "public_dashboard_static_snapshot",
                "status": "static_snapshot_ready",
                "complete": True,
            },
            {
                "requirement_id": "reproducible_archive_publication",
                "status": "manifest_ready_release_doi_missing",
                "complete": False,
            },
        ],
    }


def test_thesis_upgrade_public_dashboard_gate_passes_when_static_snapshot_exists(tmp_path: Path) -> None:
    current_status = _public_dashboard_status_payload()
    current_dir = tmp_path / "results" / "thesis_upgrade"
    site_root = tmp_path / "_site"
    current_dir.mkdir(parents=True)
    (site_root / "dashboard").mkdir(parents=True)
    (site_root / "artifacts" / "results" / "thesis_upgrade").mkdir(parents=True)
    (site_root / "artifacts" / "results" / "reproducible_archive").mkdir(parents=True)
    (current_dir / "thesis_upgrade_status.json").write_text(json.dumps(current_status), encoding="utf-8")
    (site_root / "index.html").write_text("<!doctype html>\n", encoding="utf-8")
    (site_root / "dashboard" / "dashboard-data.json").write_text(
        json.dumps({"thesis_upgrade": current_status}),
        encoding="utf-8",
    )
    (site_root / "artifacts" / "results" / "thesis_upgrade" / "thesis_upgrade_status.json").write_text(
        json.dumps(current_status),
        encoding="utf-8",
    )
    (site_root / "artifacts" / "results" / "reproducible_archive" / "ARCHIVE_MANIFEST.json").write_text(
        "{}",
        encoding="utf-8",
    )
    (site_root / "pages_manifest.json").write_text(
        json.dumps(
            {
                "entrypoints": {
                    "index": "index.html",
                    "dashboard": "dashboard/index.html",
                },
                "artifacts": [
                    "artifacts/results/thesis_upgrade/thesis_upgrade_status.json",
                    "artifacts/results/reproducible_archive/ARCHIVE_MANIFEST.json",
                ],
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    dashboard = status["components"]["public_dashboard"]

    assert dashboard["gate"]["label"] == "Public dashboard"
    assert dashboard["gate"]["status"] == "static_snapshot_ready"
    assert dashboard["gate"]["ready"] is True
    assert dashboard["static_snapshot_ready"] is True
    assert dashboard["static_snapshot_fresh"] is True
    assert dashboard["manifest_entrypoints_ready"] is True
    assert dashboard["manifest_artifacts_ready"] is True
    assert dashboard["artifact_snapshot_current"] is True
    assert dashboard["dashboard_snapshot_current"] is True
    assert dashboard["snapshot_mismatches"] == []
    assert dashboard["missing_required_paths"] == []
    package_requirements = {row["requirement_id"]: row for row in status["package_readiness_requirements"]}
    assert package_requirements["public_dashboard_static_snapshot"]["complete"] is True
    assert package_requirements["reproducible_archive_publication"]["complete"] is False
    assert status["readiness_summary"]["package_complete_gates"] == 1
    assert status["readiness_summary"]["package_total_gates"] == 2
    assert status["readiness_summary"]["package_missing_requirement_ids"] == [
        "reproducible_archive_publication",
    ]
    assert status["readiness_summary"]["remaining_packaging_requirements"] == [
        "Reproducible archive publication",
    ]


def test_thesis_upgrade_public_dashboard_gate_rejects_stale_static_snapshot(tmp_path: Path) -> None:
    current_status = _public_dashboard_status_payload("research_demo_ready_not_completed_thesis")
    stale_status = _public_dashboard_status_payload("completed_neuroscience_thesis")
    site_root = tmp_path / "_site"
    current_dir = tmp_path / "results" / "thesis_upgrade"
    current_dir.mkdir(parents=True)
    (site_root / "dashboard").mkdir(parents=True)
    (site_root / "artifacts" / "results" / "thesis_upgrade").mkdir(parents=True)
    (site_root / "artifacts" / "results" / "reproducible_archive").mkdir(parents=True)
    (current_dir / "thesis_upgrade_status.json").write_text(json.dumps(current_status), encoding="utf-8")
    (site_root / "index.html").write_text("<!doctype html>\n", encoding="utf-8")
    (site_root / "dashboard" / "dashboard-data.json").write_text(
        json.dumps({"thesis_upgrade": stale_status}),
        encoding="utf-8",
    )
    (site_root / "artifacts" / "results" / "thesis_upgrade" / "thesis_upgrade_status.json").write_text(
        json.dumps(stale_status),
        encoding="utf-8",
    )
    (site_root / "artifacts" / "results" / "reproducible_archive" / "ARCHIVE_MANIFEST.json").write_text(
        "{}",
        encoding="utf-8",
    )
    (site_root / "pages_manifest.json").write_text(
        json.dumps(
            {
                "entrypoints": {
                    "index": "index.html",
                    "dashboard": "dashboard/index.html",
                },
                "artifacts": [
                    "artifacts/results/thesis_upgrade/thesis_upgrade_status.json",
                    "artifacts/results/reproducible_archive/ARCHIVE_MANIFEST.json",
                ],
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    dashboard = status["components"]["public_dashboard"]
    package_requirements = {row["requirement_id"]: row for row in status["package_readiness_requirements"]}

    assert dashboard["gate"]["status"] == "static_snapshot_stale"
    assert dashboard["gate"]["ready"] is False
    assert dashboard["static_snapshot_fresh"] is False
    assert dashboard["artifact_snapshot_current"] is False
    assert dashboard["dashboard_snapshot_current"] is False
    assert dashboard["snapshot_mismatches"] == [
        "published thesis status artifact is stale",
        "dashboard embedded thesis status is stale",
    ]
    assert package_requirements["public_dashboard_static_snapshot"]["complete"] is False
    assert "Static Pages snapshot is stale" in package_requirements["public_dashboard_static_snapshot"]["missing"]


def test_thesis_upgrade_archive_gate_rejects_unvalidated_publication_strings(tmp_path: Path) -> None:
    archive_dir = tmp_path / "results" / "reproducible_archive"
    archive_dir.mkdir(parents=True)
    (archive_dir / "ARCHIVE_MANIFEST.json").write_text(
        json.dumps(
            {
                "schema_version": "reproducible_archive_manifest.v1",
                "artifact_count": 3,
                "release_url": "https://github.com/grimgrimberg/LSD_Thesis",
                "doi": "10.not a valid DOI",
                "archive_publication_ready": True,
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    archive = status["components"]["reproducible_archive"]

    assert archive["archive_publication_ready"] is False
    assert archive["archive_publication_metadata"] == {
        "release_url_valid": False,
        "doi_valid": False,
        "archive_publication_ready": False,
    }
    assert archive["gate"]["ready"] is False
    assert archive["gate"]["status"] == "manifest_ready_release_doi_missing"


def test_thesis_upgrade_archive_gate_passes_with_release_url_and_doi(tmp_path: Path) -> None:
    archive_dir = tmp_path / "results" / "reproducible_archive"
    archive_dir.mkdir(parents=True)
    (archive_dir / "ARCHIVE_MANIFEST.json").write_text(
        json.dumps(
            {
                "schema_version": "reproducible_archive_manifest.v1",
                "artifact_count": 3,
                "release_url": "https://github.com/grimgrimberg/LSD_Thesis/releases/tag/v1.0.0",
                "doi": "10.5281/zenodo.1234567",
                "archive_publication_ready": True,
                "publication_metadata": {
                    "release_url": "https://github.com/grimgrimberg/LSD_Thesis/releases/tag/v1.0.0",
                    "doi": "10.5281/zenodo.1234567",
                    "release_url_valid": True,
                    "doi_valid": True,
                    "archive_publication_ready": True,
                },
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    archive = status["components"]["reproducible_archive"]

    assert archive["archive_manifest_ready"] is True
    assert archive["archive_publication_ready"] is True
    assert archive["archive_publication_metadata"] == {
        "release_url_valid": True,
        "doi_valid": True,
        "archive_publication_ready": True,
    }
    assert archive["release_url"] == "https://github.com/grimgrimberg/LSD_Thesis/releases/tag/v1.0.0"
    assert archive["doi"] == "10.5281/zenodo.1234567"
    assert archive["gate"]["ready"] is True
    assert archive["gate"]["status"] == "release_doi_ready"


def test_thesis_upgrade_rejects_implemented_motion_status_without_paired_control_readiness(
    tmp_path: Path,
) -> None:
    motion_dir = tmp_path / "results" / "setting_seed" / "motion"
    confound_dir = tmp_path / "results" / "confound_controls"
    motion_dir.mkdir(parents=True)
    confound_dir.mkdir(parents=True)
    (motion_dir / "motion_summary.json").write_text(
        json.dumps(
            {
                "motion_analysis_ready": True,
                "motion_pairing_ready": True,
                "paired_subject_run_count": 4,
                "minimum_paired_subject_run_count": 4,
            }
        ),
        encoding="utf-8",
    )
    (confound_dir / "motion_confound_control_status.json").write_text(
        json.dumps({"analysis_status": "implemented_fmriprep_fd_dvars_censoring_control"}),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    motion = status["components"]["motion_confound"]
    requirement = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}[
        "motion_confound_control_result"
    ]

    assert motion["motion_summary_pairing_ready"] is True
    assert motion["motion_summary_paired_subject_run_count"] == 4
    assert motion["motion_confound_control_ready"] is False
    assert motion["motion_confound_pairing_ready"] is False
    assert motion["motion_confound_has_association_rows"] is False
    assert motion["fmriprep_motion_control_ready"] is False
    assert requirement["complete"] is False
    assert requirement["status"] == "blocked_missing_fmriprep_fd_dvars_censoring_motion_proof"
    assert "implemented-looking" in requirement["missing"]
    assert "FD, DVARS, and censor/outlier feature families" in requirement["missing"]


def test_thesis_upgrade_requires_motion_control_feature_family_coverage(tmp_path: Path) -> None:
    motion_dir = tmp_path / "results" / "setting_seed" / "motion"
    confound_dir = tmp_path / "results" / "confound_controls"
    motion_dir.mkdir(parents=True)
    confound_dir.mkdir(parents=True)
    (motion_dir / "motion_summary.json").write_text(
        json.dumps(
            {
                "motion_analysis_ready": True,
                "motion_pairing_ready": True,
                "paired_subject_run_count": 4,
                "minimum_paired_subject_run_count": 4,
            }
        ),
        encoding="utf-8",
    )
    (confound_dir / "motion_confound_control_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_dedicated_motion_confound_control_result",
                "motion_confound_control_ready": True,
                "motion_pairing_ready": True,
                "paired_subject_run_count": 4,
                "minimum_paired_subject_run_count": 4,
                "merged_subject_run_count": 4,
                "association_rows": [
                    {
                        "motion_feature": "fd_mean_delta_lsd_minus_placebo",
                        "dynamic_metric": "transition_entropy_delta",
                        "n": 4,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    motion = status["components"]["motion_confound"]
    requirement = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}[
        "motion_confound_control_result"
    ]

    assert motion["motion_confound_has_association_rows"] is True
    assert motion["motion_confound_feature_family_coverage"] == {
        "fd": True,
        "dvars": False,
        "censoring": False,
    }
    assert motion["motion_confound_required_feature_families_ready"] is False
    assert motion["fmriprep_motion_control_ready"] is False
    assert requirement["complete"] is False


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


def _verified_scoring_lock() -> dict[str, object]:
    return {
        "scoring_lock_verified": True,
        "missing_or_mismatched": [],
        "checked_files": {
            "target_files.lsd_sober_targets": {
                "path": "results/stage_2/empirical_sober_targets.yaml",
                "exists": True,
                "expected_sha256": "abc",
                "current_sha256": "abc",
                "verified": True,
            },
            "scoring_code_files.dynamic_mechanism": {
                "path": "src/lsd_thesis/dynamic_mechanism.py",
                "exists": True,
                "expected_sha256": "def",
                "current_sha256": "def",
                "verified": True,
            },
        },
    }


def test_thesis_upgrade_marks_external_validation_complete_only_with_locked_comparable_scoring(tmp_path: Path) -> None:
    result_dir = tmp_path / "results" / "psilocybin_ds006072"
    result_dir.mkdir(parents=True)
    (result_dir / "comparable_empirical_validation_summary.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_ds006072_unchanged_scoring_validation",
                "unchanged_scoring_applied": True,
                "scoring_lock_verified": True,
                "scoring_lock": _verified_scoring_lock(),
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


def test_thesis_upgrade_external_validation_rejects_stale_scoring_lock_details(tmp_path: Path) -> None:
    result_dir = tmp_path / "results" / "psilocybin_ds006072"
    result_dir.mkdir(parents=True)
    (result_dir / "comparable_empirical_validation_summary.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_ds006072_unchanged_scoring_validation",
                "unchanged_scoring_applied": True,
                "scoring_lock_verified": True,
                "scoring_lock": {
                    "scoring_lock_verified": True,
                    "missing_or_mismatched": ["scoring_code_files.dynamic_mechanism"],
                    "checked_files": {
                        "scoring_code_files.dynamic_mechanism": {
                            "path": "src/lsd_thesis/dynamic_mechanism.py",
                            "exists": True,
                            "expected_sha256": "old",
                            "current_sha256": "new",
                            "verified": False,
                        }
                    },
                },
                "subject_count": 3,
                "minimum_comparable_subjects": 3,
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    external = status["components"]["external_validation"]
    requirement = {row["requirement_id"]: row for row in status["strict_completion_requirements"]}[
        "ds006072_external_validation"
    ]

    assert external["gate"]["ready"] is False
    assert external["scoring_lock_verified"] is False
    assert external["scoring_lock_details_verified"] is False
    assert requirement["complete"] is False


def test_receptor_structural_gate_uses_ready_language_when_both_layers_exist(tmp_path: Path) -> None:
    structural_dir = tmp_path / "results" / "structural_connectome"
    receptor_dir = tmp_path / "results" / "receptor_priors"
    ingestion_dir = tmp_path / "results" / "external_ingestion"
    structural_dir.mkdir(parents=True)
    receptor_dir.mkdir(parents=True)
    ingestion_dir.mkdir(parents=True)
    (structural_dir / "structural_connectome_status.json").write_text(
        json.dumps({"analysis_status": "implemented_hcp_structural_graph_sensitivity"}),
        encoding="utf-8",
    )
    (receptor_dir / "receptor_prior_status.json").write_text(
        json.dumps({"analysis_status": "implemented_pet_receptor_prior_sensitivity"}),
        encoding="utf-8",
    )
    (ingestion_dir / "external_ingestion_status.json").write_text(
        json.dumps(
            {
                "analysis_status": {
                    "structural_connectome": "ready",
                    "receptor_prior": "ready",
                }
            }
        ),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    receptor_structural = status["components"]["receptor_structural"]

    assert receptor_structural["gate"]["ready"] is True
    assert receptor_structural["gate"]["status"] == "fully_integrated"
    assert receptor_structural["structural_ingested"] is True
    assert receptor_structural["receptor_ingested"] is True
    assert "Documented structural-connectome graph sensitivity" in receptor_structural["gate"]["blocker"]
    assert "Need both" not in receptor_structural["gate"]["blocker"]
    assert "implemented sensitivity controls" in receptor_structural["claim_guardrail"]
    assert "proxy-only until" not in receptor_structural["claim_guardrail"]


def test_receptor_structural_gate_requires_ingestion_readiness(tmp_path: Path) -> None:
    structural_dir = tmp_path / "results" / "structural_connectome"
    receptor_dir = tmp_path / "results" / "receptor_priors"
    structural_dir.mkdir(parents=True)
    receptor_dir.mkdir(parents=True)
    (structural_dir / "structural_connectome_status.json").write_text(
        json.dumps({"analysis_status": "implemented_hcp_structural_graph_sensitivity"}),
        encoding="utf-8",
    )
    (receptor_dir / "receptor_prior_status.json").write_text(
        json.dumps({"analysis_status": "implemented_pet_receptor_prior_sensitivity"}),
        encoding="utf-8",
    )

    status = build_thesis_upgrade_status(tmp_path)
    receptor_structural = status["components"]["receptor_structural"]

    assert receptor_structural["gate"]["ready"] is False
    assert receptor_structural["gate"]["status"] == "proxy_or_blocked"
    assert receptor_structural["structural_ingested"] is False
    assert receptor_structural["receptor_ingested"] is False
    assert "implemented and ingested structural-connectome" in receptor_structural["gate"]["blocker"]


def test_thesis_upgrade_project_phase_completes_only_with_hard_motion_and_stronger_external_validation(
    tmp_path: Path,
) -> None:
    _write_valid_schaefer_yeo_outputs(tmp_path)

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
        json.dumps(
            {
                "motion_analysis_ready": True,
                "motion_pairing_ready": True,
                "paired_subject_run_count": 4,
                "minimum_paired_subject_run_count": 4,
            }
        ),
        encoding="utf-8",
    )
    (confound_dir / "motion_confound_control_status.json").write_text(
        json.dumps(
            {
                "analysis_status": "implemented_dedicated_motion_confound_control_result",
                "motion_confound_control_ready": True,
                "motion_pairing_ready": True,
                "paired_subject_run_count": 4,
                "minimum_paired_subject_run_count": 4,
                "merged_subject_run_count": 4,
                "association_rows": [
                    {
                        "motion_feature": "fd_mean_delta_lsd_minus_placebo",
                        "dynamic_metric": "transition_entropy_delta",
                        "n": 4,
                        "pearson_r": 0.1,
                        "pearson_p": 0.8,
                        "pearson_q": 0.8,
                        "motion_sensitivity_flag": False,
                    },
                    {
                        "motion_feature": "dvars_mean_delta_lsd_minus_placebo",
                        "dynamic_metric": "transition_entropy_delta",
                        "n": 4,
                        "pearson_r": 0.1,
                        "pearson_p": 0.8,
                        "pearson_q": 0.8,
                        "motion_sensitivity_flag": False,
                    },
                    {
                        "motion_feature": "motion_outlier_fraction_delta_lsd_minus_placebo",
                        "dynamic_metric": "transition_entropy_delta",
                        "n": 4,
                        "pearson_r": 0.1,
                        "pearson_p": 0.8,
                        "pearson_q": 0.8,
                        "motion_sensitivity_flag": False,
                    }
                ],
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
                "scoring_lock": _verified_scoring_lock(),
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
    _write_valid_schaefer_yeo_outputs(tmp_path)

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
                "scoring_lock": _verified_scoring_lock(),
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
