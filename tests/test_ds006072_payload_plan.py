from __future__ import annotations

import csv
from pathlib import Path

from lsd_thesis.ds006072_payload_plan import build_ds006072_payload_plan_status, write_ds006072_payload_plan_status


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_fixture_manifests(root: Path, subject_count: int = 3, local: bool = False) -> None:
    data_root = root / "data" / "ds006072"
    session_rows = []
    order_rows = []
    cifti_rows = []
    for index in range(1, subject_count + 1):
        subject = f"P{index}"
        session_rows.extend(
            [
                {"PatientName": subject, "SessionID": f"{subject}_Drug1"},
                {"PatientName": subject, "SessionID": f"{subject}_Drug2"},
            ]
        )
        order_rows.append({"SubID": subject, "Drug1": "MTP", "Drug2": "PSIL"})
        for suffix in ("Drug1", "Drug2"):
            filename = f"sub-{index}_{suffix}_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii"
            relative_path = f"NON_BIDS/ciftis/{filename}"
            cifti_rows.append(
                {
                    "filename": filename,
                    "relative_path": relative_path,
                    "is_processed_rest_cifti": "True",
                    "url_available": "True",
                    "url": f"https://example.test/{filename}",
                    "size": "4",
                }
            )
            if local:
                local_path = data_root / relative_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(b"data")
    _write_csv(data_root / "session_data.csv", ["PatientName", "SessionID"], session_rows)
    _write_csv(data_root / "ds006072_drug_order.csv", ["SubID", "Drug1", "Drug2"], order_rows)
    _write_csv(
        data_root / "ds006072_cifti_manifest.csv",
        ["filename", "relative_path", "is_processed_rest_cifti", "url_available", "url", "size"],
        cifti_rows,
    )


def test_payload_plan_selects_minimum_downloadable_pairs(tmp_path: Path) -> None:
    _write_fixture_manifests(tmp_path, subject_count=4)

    status = build_ds006072_payload_plan_status(tmp_path, minimum_subjects=3)

    assert status["analysis_status"] == "minimum_payload_download_plan_ready_missing_local_payloads"
    assert status["minimum_payload_plan_ready"] is True
    assert status["minimum_payloads_local_ready"] is False
    assert status["selected_subject_count"] == 3
    assert status["selected_file_count"] == 6
    assert status["selected_total_size_bytes"] == 24
    assert {row["condition"] for row in status["selected_files"]} == {"active_control_mtp", "psilocybin"}


def test_payload_plan_marks_local_ready_when_selected_files_exist(tmp_path: Path) -> None:
    _write_fixture_manifests(tmp_path, subject_count=3, local=True)

    status = build_ds006072_payload_plan_status(tmp_path, minimum_subjects=3)

    assert status["analysis_status"] == "minimum_validation_payloads_local_ready_for_extraction"
    assert status["minimum_payloads_local_ready"] is True
    assert status["selected_local_ready_subject_count"] == 3


def test_write_payload_plan_status_writes_public_artifacts(tmp_path: Path) -> None:
    _write_fixture_manifests(tmp_path, subject_count=3)

    status = write_ds006072_payload_plan_status(tmp_path)

    assert status["source_path"] == "results/psilocybin_ds006072/minimum_payload_plan.json"
    assert (tmp_path / status["source_path"]).exists()
    assert (tmp_path / status["report_path"]).exists()
