from __future__ import annotations

import csv
from pathlib import Path

from lsd_thesis.ds006072_validation import (
    MIN_COMPARABLE_SUBJECTS,
    build_ds006072_comparable_validation_status,
    build_ds006072_external_validation_readiness,
    build_session_availability_rows,
    build_subject_pairing_rows,
    classify_session,
)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_ds006072_condition_mapping_uses_drug_order_without_guessing() -> None:
    order = {"P1": {"Drug1": "MTP", "Drug2": "PSIL"}}

    assert classify_session("P1_Baseline1", "P1", order) == "baseline_control"
    assert classify_session("P1_Drug1", "P1", order) == "active_control_mtp"
    assert classify_session("P1_Drug2", "P1", order) == "psilocybin"
    assert classify_session("P9_Drug1", "P9", order) == "drug_session_requires_order_mapping"


def test_ds006072_pairing_rows_are_subject_level_and_local_ready_only_when_payloads_exist(tmp_path: Path) -> None:
    session_rows = [
        {"PatientName": "P1", "SessionID": "P1_Baseline1"},
        {"PatientName": "P1", "SessionID": "P1_Drug1"},
        {"PatientName": "P1", "SessionID": "P1_Drug2"},
    ]
    cifti_rows = [
        {
            "filename": "sub-1_Drug1_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
            "relative_path": "NON_BIDS/ciftis/sub-1_Drug1_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
            "is_processed_rest_cifti": "True",
            "url_available": "True",
            "size": "10",
        },
        {
            "filename": "sub-1_Drug2_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
            "relative_path": "NON_BIDS/ciftis/sub-1_Drug2_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
            "is_processed_rest_cifti": "True",
            "url_available": "True",
            "size": "10",
        },
    ]
    local_file = tmp_path / "data" / "ds006072" / "NON_BIDS" / "ciftis" / cifti_rows[1]["filename"]
    local_file.parent.mkdir(parents=True)
    local_file.write_text("placeholder", encoding="utf-8")

    availability = build_session_availability_rows(
        repo_root=tmp_path,
        session_rows=session_rows,
        cifti_rows=cifti_rows,
        drug_order={"P1": {"Drug1": "MTP", "Drug2": "PSIL"}},
    )
    pairing = build_subject_pairing_rows(availability)

    assert pairing[0]["primary_contrast_planned"] is True
    assert pairing[0]["primary_contrast_local_ready"] is False
    assert pairing[0]["psilocybin_local_cifti_count"] == 1
    assert pairing[0]["active_control_mtp_local_cifti_count"] == 0


def test_build_ds006072_readiness_locks_scoring_and_writes_fail_closed_status(tmp_path: Path) -> None:
    data_root = tmp_path / "data" / "ds006072"
    _write_csv(
        data_root / "session_data.csv",
        ["PatientName", "SessionID", "SessionNumber"],
        [
            {"PatientName": "P1", "SessionID": "P1_Baseline1", "SessionNumber": "sub-P1_ses-1"},
            {"PatientName": "P1", "SessionID": "P1_Drug1", "SessionNumber": "sub-P1_ses-2"},
            {"PatientName": "P1", "SessionID": "P1_Drug2", "SessionNumber": "sub-P1_ses-3"},
        ],
    )
    _write_csv(data_root / "ds006072_drug_order.csv", ["SubID", "Drug1", "Drug2"], [{"SubID": "P1", "Drug1": "MTP", "Drug2": "PSIL"}])
    _write_csv(
        data_root / "ds006072_cifti_manifest.csv",
        ["filename", "relative_path", "is_processed_rest_cifti", "url_available", "size"],
        [
            {
                "filename": "sub-1_Drug1_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
                "relative_path": "NON_BIDS/ciftis/sub-1_Drug1_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
                "is_processed_rest_cifti": "True",
                "url_available": "True",
                "size": "10",
            },
            {
                "filename": "sub-1_Drug2_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
                "relative_path": "NON_BIDS/ciftis/sub-1_Drug2_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
                "is_processed_rest_cifti": "True",
                "url_available": "True",
                "size": "10",
            },
        ],
    )
    (tmp_path / "results" / "stage_2").mkdir(parents=True)
    (tmp_path / "results" / "stage_2" / "empirical_sober_targets.yaml").write_text("target_deltas: {}\n", encoding="utf-8")
    (tmp_path / "results" / "stage_2" / "empirical_perturbation_targets.yaml").write_text("target_deltas: {}\n", encoding="utf-8")
    (tmp_path / "configs" / "targets").mkdir(parents=True)
    (tmp_path / "configs" / "targets" / "empirical_lsd_signatures.yaml").write_text("target_deltas: {}\n", encoding="utf-8")

    payload = build_ds006072_external_validation_readiness(tmp_path)

    assert payload["analysis_status"] == "extraction_contract_ready_missing_local_cifti_payloads"
    assert payload["primary_subject_count"] == 1
    assert payload["primary_subjects_local_ready"] == 0
    assert (tmp_path / "results" / "psilocybin_ds006072" / "unchanged_scoring_spec.json").exists()


def _write_scoring_targets(root: Path) -> None:
    (root / "results" / "stage_2").mkdir(parents=True, exist_ok=True)
    (root / "results" / "stage_2" / "empirical_sober_targets.yaml").write_text("target_deltas: {}\n", encoding="utf-8")
    (root / "results" / "stage_2" / "empirical_perturbation_targets.yaml").write_text("target_deltas: {}\n", encoding="utf-8")
    (root / "configs" / "targets").mkdir(parents=True, exist_ok=True)
    (root / "configs" / "targets" / "empirical_lsd_signatures.yaml").write_text("target_deltas: {}\n", encoding="utf-8")


def _write_minimal_ds006072_metadata(root: Path, subject_count: int = MIN_COMPARABLE_SUBJECTS) -> None:
    data_root = root / "data" / "ds006072"
    rows = []
    order_rows = []
    cifti_rows = []
    for index in range(1, subject_count + 1):
        subject = f"P{index}"
        rows.extend(
            [
                {"PatientName": subject, "SessionID": f"{subject}_Drug1", "SessionNumber": f"sub-P{index}_ses-1"},
                {"PatientName": subject, "SessionID": f"{subject}_Drug2", "SessionNumber": f"sub-P{index}_ses-2"},
            ]
        )
        order_rows.append({"SubID": subject, "Drug1": "MTP", "Drug2": "PSIL"})
        cifti_rows.extend(
            [
                {
                    "filename": f"sub-{index}_Drug1_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
                    "relative_path": f"NON_BIDS/ciftis/sub-{index}_Drug1_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
                    "is_processed_rest_cifti": "True",
                    "url_available": "True",
                    "size": "10",
                },
                {
                    "filename": f"sub-{index}_Drug2_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
                    "relative_path": f"NON_BIDS/ciftis/sub-{index}_Drug2_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii",
                    "is_processed_rest_cifti": "True",
                    "url_available": "True",
                    "size": "10",
                },
            ]
        )
    _write_csv(data_root / "session_data.csv", ["PatientName", "SessionID", "SessionNumber"], rows)
    _write_csv(data_root / "ds006072_drug_order.csv", ["SubID", "Drug1", "Drug2"], order_rows)
    _write_csv(data_root / "ds006072_cifti_manifest.csv", ["filename", "relative_path", "is_processed_rest_cifti", "url_available", "size"], cifti_rows)


def _write_external_viewer(
    root: Path,
    subject_count: int = MIN_COMPARABLE_SUBJECTS,
    viewer_root: Path | None = None,
) -> None:
    viewer_root = viewer_root or root / "results" / "psilocybin_ds006072" / "empirical_viewer"
    subject_views = viewer_root / "subject_views"
    subject_views.mkdir(parents=True, exist_ok=True)
    modules = [
        "visual",
        "auditory",
        "salience",
        "default_mode",
        "executive_frontoparietal",
        "limbic_affective",
        "thalamic_gateway",
        "sensorimotor",
    ]
    (viewer_root / "group_overview.json").write_text(
        __import__("json").dumps({"module_names": modules}),
        encoding="utf-8",
    )
    for index in range(1, subject_count + 1):
        base = float(index)
        placebo = [[base + time * 0.1 + module * 0.01 for module in range(len(modules))] for time in range(6)]
        psilocybin = [[base + time * 0.16 + module * 0.015 for module in range(len(modules))] for time in range(6)]
        payload = {
            "subject": f"P{index}",
            "run": "run-01",
            "conditions": {
                "ses-PLCB": {
                    "module_time_series": placebo
                },
                "ses-LSD": {
                    "module_time_series": psilocybin
                },
            },
        }
        (subject_views / f"P{index}_run-01.json").write_text(
            __import__("json").dumps(payload),
            encoding="utf-8",
        )


def test_comparable_validation_fails_closed_without_empirical_viewer(tmp_path: Path) -> None:
    _write_scoring_targets(tmp_path)
    _write_minimal_ds006072_metadata(tmp_path)

    payload = build_ds006072_comparable_validation_status(tmp_path)

    assert payload["analysis_status"] == "blocked_missing_local_ds006072_empirical_viewer"
    assert payload["scoring_lock_verified"] is True
    assert payload["unchanged_scoring_applied"] is False
    assert payload["pair_count"] == 0
    assert (tmp_path / "results" / "psilocybin_ds006072" / "comparable_empirical_validation_summary.json").exists()


def test_comparable_validation_scores_harmonized_pairs_with_locked_rule(tmp_path: Path) -> None:
    _write_scoring_targets(tmp_path)
    _write_minimal_ds006072_metadata(tmp_path)
    _write_external_viewer(tmp_path)

    payload = build_ds006072_comparable_validation_status(tmp_path)

    assert payload["analysis_status"] == "implemented_ds006072_unchanged_scoring_validation"
    assert payload["scoring_lock_verified"] is True
    assert payload["unchanged_scoring_applied"] is True
    assert payload["subject_count"] == MIN_COMPARABLE_SUBJECTS
    assert payload["pair_count"] == MIN_COMPARABLE_SUBJECTS
    assert payload["mechanism_ranking"]
    assert payload["stronger_external_validation_ready"] is False


def test_comparable_validation_prefers_schaefer100_viewer_when_ready(tmp_path: Path) -> None:
    _write_scoring_targets(tmp_path)
    _write_minimal_ds006072_metadata(tmp_path)
    schaefer_viewer = (
        tmp_path
        / "results"
        / "psilocybin_ds006072"
        / "parcellations"
        / "schaefer_100_yeo_7"
        / "empirical_viewer"
    )
    _write_external_viewer(tmp_path, viewer_root=schaefer_viewer)
    status_dir = tmp_path / "results" / "psilocybin_ds006072"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / "cifti_empirical_extraction_status.json").write_text(
        __import__("json").dumps(
            {
                "analysis_status": "implemented_ds006072_schaefer100_parcellation_empirical_viewer",
                "cifti_empirical_viewer_ready": True,
                "schaefer100_empirical_viewer_ready": True,
                "stronger_external_validation_ready": True,
                "schaefer100_viewer_root": "results/psilocybin_ds006072/parcellations/schaefer_100_yeo_7/empirical_viewer",
                "schaefer100_module_contract": "CIFTI fsLR cortex Schaefer100/Yeo7 parcel external validation",
                "schaefer100_parcellation_id": "schaefer_100_yeo_7",
            }
        ),
        encoding="utf-8",
    )

    payload = build_ds006072_comparable_validation_status(tmp_path)

    assert payload["analysis_status"] == "implemented_ds006072_unchanged_scoring_validation"
    assert payload["viewer_root"] == "results/psilocybin_ds006072/parcellations/schaefer_100_yeo_7/empirical_viewer"
    assert payload["validation_scope"] == "parcellation_matched_schaefer100_yeo7_external_validation"
    assert payload["schaefer100_empirical_viewer_ready"] is True
    assert payload["stronger_external_validation_ready"] is True
