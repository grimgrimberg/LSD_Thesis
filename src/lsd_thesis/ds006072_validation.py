from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "ds006072_external_validation.v1"
DS006072_DATASET_ID = "ds006072"

NAMESPACE = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
PRIMARY_CONTRAST = "psilocybin_vs_active_control_mtp"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _session_suffix(session_id: str, patient: str) -> str:
    prefix = f"{patient}_"
    if session_id.startswith(prefix):
        return session_id[len(prefix) :]
    if "_" in session_id:
        return session_id.split("_", 1)[1]
    return session_id


def _session_drug_key(session_suffix: str) -> str | None:
    if session_suffix.startswith("Drug1"):
        return "Drug1"
    if session_suffix.startswith("Drug2"):
        return "Drug2"
    return None


def _openneuro_subject_token(patient: str) -> str:
    if patient.startswith("P"):
        return f"sub-{patient[1:]}"
    return f"sub-{patient}"


def classify_session(session_id: str, patient: str, drug_order: dict[str, dict[str, str]]) -> str:
    suffix = _session_suffix(session_id, patient)
    lowered = suffix.lower()
    if lowered.startswith("baseline"):
        return "baseline_control"
    drug_key = _session_drug_key(suffix)
    if drug_key is None:
        if lowered.startswith("between"):
            return "between_drug_followup_excluded_from_primary"
        if lowered.startswith("after"):
            return "post_drug_followup_excluded_from_primary"
        return "nonprimary_or_qc_session"
    drug_label = str(drug_order.get(patient, {}).get(drug_key, "")).upper()
    if drug_label == "PSIL":
        return "psilocybin"
    if drug_label == "MTP":
        return "active_control_mtp"
    return "drug_session_requires_order_mapping"


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values = []
    for item in root.findall("a:si", NAMESPACE):
        values.append("".join(text.text or "" for text in item.findall(".//a:t", NAMESPACE)))
    return values


def _xlsx_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value = cell.find("a:v", NAMESPACE)
    if value is None:
        inline = cell.find("a:is", NAMESPACE)
        if inline is None:
            return ""
        return "".join(text.text or "" for text in inline.findall(".//a:t", NAMESPACE)).strip()
    raw = value.text or ""
    if cell.get("t") == "s":
        try:
            return shared_strings[int(raw)].strip()
        except (IndexError, ValueError):
            return ""
    return raw.strip()


def _xlsx_worksheets(path: Path) -> list[list[list[str]]]:
    worksheets: list[list[list[str]]] = []
    with zipfile.ZipFile(path) as archive:
        shared_strings = _xlsx_shared_strings(archive)
        worksheet_names = [
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        ]
        for worksheet_name in worksheet_names:
            root = ET.fromstring(archive.read(worksheet_name))
            rows: list[list[str]] = []
            for row in root.findall(".//a:row", NAMESPACE):
                rows.append([_xlsx_cell_value(cell, shared_strings) for cell in row.findall("a:c", NAMESPACE)])
            worksheets.append(rows)
    return worksheets


def _load_drug_order_csv(path: Path) -> dict[str, dict[str, str]]:
    rows = _read_csv(path)
    mapping: dict[str, dict[str, str]] = {}
    for row in rows:
        subject = str(row.get("SubID") or row.get("subject") or row.get("Subject") or "").strip()
        if not subject:
            continue
        mapping[subject] = {
            "Drug1": str(row.get("Drug1") or row.get("drug1") or "").strip().upper(),
            "Drug2": str(row.get("Drug2") or row.get("drug2") or "").strip().upper(),
        }
    return mapping


def _load_drug_order_xlsx(path: Path) -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for rows in _xlsx_worksheets(path):
        for index, row in enumerate(rows):
            normalized = [value.strip() for value in row[:3]]
            if normalized == ["SubID", "Drug1", "Drug2"]:
                for data_row in rows[index + 1 :]:
                    if len(data_row) < 2 or not data_row[0].strip():
                        break
                    subject = data_row[0].strip()
                    mapping[subject] = {
                        "Drug1": data_row[1].strip().upper() if len(data_row) > 1 else "",
                        "Drug2": data_row[2].strip().upper() if len(data_row) > 2 else "",
                    }
                return mapping
    return mapping


def load_drug_order(repo_root: Path = REPO_ROOT) -> tuple[dict[str, dict[str, str]], str | None]:
    data_root = repo_root / "data" / DS006072_DATASET_ID
    csv_path = data_root / "ds006072_drug_order.csv"
    if csv_path.exists():
        return _load_drug_order_csv(csv_path), _rel(csv_path, repo_root)
    candidates = [path for path in data_root.glob("PPFM_session_notes*.xlsx") if not path.name.endswith(".part")]
    if candidates:
        path = candidates[0]
        return _load_drug_order_xlsx(path), _rel(path, repo_root)
    return {}, None


def _manifest_matches_session(cifti_rows: list[dict[str, str]], patient: str, session_suffix: str) -> list[dict[str, str]]:
    token = _openneuro_subject_token(patient)
    prefix = f"{token}_{session_suffix}_"
    return [
        row
        for row in cifti_rows
        if _boolish(row.get("is_processed_rest_cifti"))
        and str(row.get("filename", "")).startswith(prefix)
        and _boolish(row.get("url_available"))
    ]


def build_session_availability_rows(
    *,
    repo_root: Path,
    session_rows: list[dict[str, str]],
    cifti_rows: list[dict[str, str]],
    drug_order: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    data_root = repo_root / "data" / DS006072_DATASET_ID
    rows: list[dict[str, Any]] = []
    for row in session_rows:
        patient = str(row.get("PatientName", "")).strip()
        session_id = str(row.get("SessionID", "")).strip()
        if not patient or not session_id:
            continue
        suffix = _session_suffix(session_id, patient)
        matches = _manifest_matches_session(cifti_rows, patient, suffix)
        local_count = sum(1 for item in matches if (data_root / str(item.get("relative_path", ""))).exists())
        rows.append(
            {
                "subject": patient,
                "session_id": session_id,
                "session_suffix": suffix,
                "condition": classify_session(session_id, patient, drug_order),
                "processed_rest_cifti_downloadable_count": len(matches),
                "processed_rest_cifti_local_count": local_count,
                "downloadable_size_bytes": sum(int(item.get("size") or 0) for item in matches),
            }
        )
    return rows


def build_subject_pairing_rows(session_availability_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    subjects = sorted({str(row["subject"]) for row in session_availability_rows})
    rows: list[dict[str, Any]] = []
    for subject in subjects:
        subject_rows = [row for row in session_availability_rows if row["subject"] == subject]
        by_condition: dict[str, list[dict[str, Any]]] = {}
        for row in subject_rows:
            by_condition.setdefault(str(row["condition"]), []).append(row)
        psil = by_condition.get("psilocybin", [])
        mtp = by_condition.get("active_control_mtp", [])
        baseline = by_condition.get("baseline_control", [])
        psil_local = sum(int(row["processed_rest_cifti_local_count"]) for row in psil)
        mtp_local = sum(int(row["processed_rest_cifti_local_count"]) for row in mtp)
        baseline_local = sum(int(row["processed_rest_cifti_local_count"]) for row in baseline)
        rows.append(
            {
                "subject": subject,
                "primary_contrast": PRIMARY_CONTRAST,
                "psilocybin_session_count": len(psil),
                "active_control_mtp_session_count": len(mtp),
                "baseline_session_count": len(baseline),
                "psilocybin_downloadable_cifti_count": sum(
                    int(row["processed_rest_cifti_downloadable_count"]) for row in psil
                ),
                "active_control_mtp_downloadable_cifti_count": sum(
                    int(row["processed_rest_cifti_downloadable_count"]) for row in mtp
                ),
                "baseline_downloadable_cifti_count": sum(
                    int(row["processed_rest_cifti_downloadable_count"]) for row in baseline
                ),
                "psilocybin_local_cifti_count": psil_local,
                "active_control_mtp_local_cifti_count": mtp_local,
                "baseline_local_cifti_count": baseline_local,
                "primary_contrast_planned": bool(psil and mtp),
                "primary_contrast_local_ready": bool(psil_local and mtp_local),
                "secondary_baseline_contrast_planned": bool(psil and baseline),
                "secondary_baseline_contrast_local_ready": bool(psil_local and baseline_local),
            }
        )
    return rows


def _write_scoring_spec(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    target_paths = {
        "lsd_sober_targets": repo_root / "results" / "stage_2" / "empirical_sober_targets.yaml",
        "lsd_perturbation_targets": repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml",
        "literature_targets": repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml",
    }
    spec = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _now(),
        "source_dataset_id": "ds003059",
        "external_dataset_id": DS006072_DATASET_ID,
        "fixed_rule": (
            "Run lsd_thesis.dynamic_mechanism.build_dynamic_mechanism_summary on ds006072 empirical viewer "
            "records without changing mechanism weights, metric direction rules, target files, or ranking code after "
            "seeing psilocybin results."
        ),
        "primary_contrast": PRIMARY_CONTRAST,
        "aggregation": "session/run summaries are paired within subject and interpreted at subject level before group claims",
        "target_files": {
            name: {
                "path": _rel(path, repo_root),
                "exists": path.exists(),
                "sha256": _sha256_file(path),
            }
            for name, path in target_paths.items()
        },
        "claim_guardrail": "This locks the scoring rule. It is not an external validation result until paired ds006072 viewer records exist.",
    }
    path = output_dir / "unchanged_scoring_spec.json"
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    spec["source_path"] = _rel(path, repo_root)
    return spec


def _write_summary(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# ds006072 External Validation Readiness",
        "",
        f"- Status: `{payload['analysis_status']}`",
        f"- Drug-order mapping source: `{payload.get('drug_order_source')}`",
        f"- Planned primary subjects: `{payload['primary_subject_count']}`",
        f"- Locally ready primary subjects: `{payload['primary_subjects_local_ready']}`",
        "",
        "## Claim boundary",
        "",
        payload["claim_guardrail"],
        "",
        "## Next step",
        "",
        payload["blocker"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_ds006072_external_validation_readiness(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    data_root = repo_root / "data" / DS006072_DATASET_ID
    output_dir = repo_root / "results" / "psilocybin_ds006072"
    output_dir.mkdir(parents=True, exist_ok=True)

    session_rows = _read_csv(data_root / "session_data.csv")
    cifti_rows = _read_csv(data_root / "ds006072_cifti_manifest.csv")
    drug_order, drug_order_source = load_drug_order(repo_root)
    session_availability_rows = build_session_availability_rows(
        repo_root=repo_root,
        session_rows=session_rows,
        cifti_rows=cifti_rows,
        drug_order=drug_order,
    )
    subject_pairing_rows = build_subject_pairing_rows(session_availability_rows)
    scoring_spec = _write_scoring_spec(repo_root, output_dir)

    session_path = output_dir / "ds006072_session_availability.csv"
    subject_path = output_dir / "condition_pairing_plan.csv"
    _write_csv(
        session_path,
        [
            "subject",
            "session_id",
            "session_suffix",
            "condition",
            "processed_rest_cifti_downloadable_count",
            "processed_rest_cifti_local_count",
            "downloadable_size_bytes",
        ],
        session_availability_rows,
    )
    _write_csv(
        subject_path,
        [
            "subject",
            "primary_contrast",
            "psilocybin_session_count",
            "active_control_mtp_session_count",
            "baseline_session_count",
            "psilocybin_downloadable_cifti_count",
            "active_control_mtp_downloadable_cifti_count",
            "baseline_downloadable_cifti_count",
            "psilocybin_local_cifti_count",
            "active_control_mtp_local_cifti_count",
            "baseline_local_cifti_count",
            "primary_contrast_planned",
            "primary_contrast_local_ready",
            "secondary_baseline_contrast_planned",
            "secondary_baseline_contrast_local_ready",
        ],
        subject_pairing_rows,
    )

    primary_rows = [row for row in subject_pairing_rows if row["primary_contrast_planned"]]
    local_ready_rows = [row for row in primary_rows if row["primary_contrast_local_ready"]]
    downloadable_subjects = [
        row
        for row in primary_rows
        if int(row["psilocybin_downloadable_cifti_count"])
        and int(row["active_control_mtp_downloadable_cifti_count"])
    ]
    drug_order_ready = bool(drug_order)
    scoring_locked = all(item["exists"] for item in scoring_spec["target_files"].values())
    if local_ready_rows and scoring_locked:
        analysis_status = "local_cifti_payloads_ready_for_comparable_extraction"
        blocker = "Run the ds006072 module time-series extraction and empirical-viewer writer, then rerun the thesis evidence loop."
    elif drug_order_ready and downloadable_subjects and scoring_locked:
        analysis_status = "extraction_contract_ready_missing_local_cifti_payloads"
        blocker = (
            "Drug-order mapping and unchanged scoring are locked, but local ds006072 CIFTI/module time-series "
            "payloads are absent. Download or provide authorized processed rest CIFTIs before claiming validation."
        )
    elif drug_order_ready and downloadable_subjects:
        analysis_status = "blocked_missing_lsd_scoring_lock"
        blocker = "Regenerate the ds003059 target/scoring artifacts before running unchanged ds006072 validation."
    else:
        analysis_status = "blocked_missing_drug_order_or_processed_rest_manifest"
        blocker = "Need ds006072 drug-order mapping and processed-rest CIFTI manifest before comparable extraction planning."

    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _now(),
        "dataset_id": DS006072_DATASET_ID,
        "analysis_status": analysis_status,
        "primary_contrast": PRIMARY_CONTRAST,
        "drug_order_source": drug_order_source,
        "drug_order_subject_count": len(drug_order),
        "session_count": len(session_rows),
        "processed_rest_cifti_manifest_count": len([row for row in cifti_rows if _boolish(row.get("is_processed_rest_cifti"))]),
        "primary_subject_count": len(primary_rows),
        "primary_subjects_downloadable": len(downloadable_subjects),
        "primary_subjects_local_ready": len(local_ready_rows),
        "session_availability_csv": _rel(session_path, repo_root),
        "condition_pairing_plan_csv": _rel(subject_path, repo_root),
        "unchanged_scoring_spec": scoring_spec["source_path"],
        "blocker": blocker,
        "claim_guardrail": (
            "This is an extraction-and-scoring gate for true external validation. It does not claim psilocybin "
            "replication until paired psilocybin/MTP empirical viewer records are generated and scored unchanged."
        ),
        "source": {
            "openneuro": "https://openneuro.org/datasets/ds006072",
            "scientific_data": "https://www.nature.com/articles/s41597-025-05189-0",
        },
    }
    readiness_path = output_dir / "external_validation_readiness.json"
    summary_path = output_dir / "external_validation_readiness.md"
    readiness_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_summary(summary_path, payload)
    payload["source_path"] = _rel(readiness_path, repo_root)
    payload["summary_path"] = _rel(summary_path, repo_root)
    return payload
