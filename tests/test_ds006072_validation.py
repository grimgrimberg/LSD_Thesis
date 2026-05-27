from __future__ import annotations

import csv
from pathlib import Path

from lsd_thesis.ds006072_validation import (
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
