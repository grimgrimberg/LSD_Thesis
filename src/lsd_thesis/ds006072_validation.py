from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import lsd_thesis.dynamic_mechanism as dynamic_mechanism_module
import lsd_thesis.dynamic_mechanism.connectivity as dynamic_mechanism_connectivity_module
import lsd_thesis.dynamic_mechanism.core as dynamic_mechanism_core_module
import lsd_thesis.dynamic_mechanism.hierarchy as dynamic_mechanism_hierarchy_module
import lsd_thesis.dynamic_mechanism.priors as dynamic_mechanism_priors_module
import lsd_thesis.dynamic_mechanism.repertoire as dynamic_mechanism_repertoire_module
import lsd_thesis.dynamic_mechanism.stats as dynamic_mechanism_stats_module
import lsd_thesis.dynamic_mechanism.transitions as dynamic_mechanism_transitions_module
from lsd_thesis.dynamic_mechanism.core import build_dynamic_mechanism_summary, load_empirical_pairs

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "ds006072_external_validation.v1"
DS006072_DATASET_ID = "ds006072"

NAMESPACE = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
PRIMARY_CONTRAST = "psilocybin_vs_active_control_mtp"
MIN_COMPARABLE_SUBJECTS = 3


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _path_ref(path: Path, repo_root: Path) -> str:
    try:
        return _rel(path, repo_root)
    except ValueError:
        return path.resolve().as_posix()


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
    scoring_code_paths = {
        "dynamic_mechanism": Path(dynamic_mechanism_module.__file__ or ""),
        "dynamic_mechanism_core": Path(dynamic_mechanism_core_module.__file__ or ""),
        "dynamic_mechanism_connectivity": Path(dynamic_mechanism_connectivity_module.__file__ or ""),
        "dynamic_mechanism_hierarchy": Path(dynamic_mechanism_hierarchy_module.__file__ or ""),
        "dynamic_mechanism_priors": Path(dynamic_mechanism_priors_module.__file__ or ""),
        "dynamic_mechanism_repertoire": Path(dynamic_mechanism_repertoire_module.__file__ or ""),
        "dynamic_mechanism_stats": Path(dynamic_mechanism_stats_module.__file__ or ""),
        "dynamic_mechanism_transitions": Path(dynamic_mechanism_transitions_module.__file__ or ""),
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
        "scoring_code_files": {
            name: {
                "path": _path_ref(path, repo_root),
                "exists": path.exists(),
                "sha256": _sha256_file(path),
                "entrypoint": "lsd_thesis.dynamic_mechanism.build_dynamic_mechanism_summary"
                if name == "dynamic_mechanism_core"
                else None,
            }
            for name, path in scoring_code_paths.items()
        },
        "claim_guardrail": "This locks the scoring rule. It is not an external validation result until paired ds006072 viewer records exist.",
    }
    path = output_dir / "unchanged_scoring_spec.json"
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    spec["source_path"] = _rel(path, repo_root)
    return spec


def _verify_locked_scoring_spec(repo_root: Path, spec: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(spec, dict):
        return {
            "scoring_lock_verified": False,
            "missing_or_mismatched": ["missing unchanged_scoring_spec.json"],
            "checked_files": {},
        }

    checked_files: dict[str, dict[str, Any]] = {}
    missing_or_mismatched: list[str] = []
    groups = {
        "target_files": spec.get("target_files", {}),
        "scoring_code_files": spec.get("scoring_code_files", {}),
    }
    for group_name, files in groups.items():
        if not isinstance(files, dict):
            missing_or_mismatched.append(group_name)
            continue
        for name, payload in files.items():
            if not isinstance(payload, dict):
                missing_or_mismatched.append(f"{group_name}.{name}")
                continue
            rel_path = str(payload.get("path") or "")
            expected_hash = payload.get("sha256")
            path = Path(rel_path)
            if not path.is_absolute():
                path = repo_root / rel_path
            current_hash = _sha256_file(path)
            exists = path.exists()
            verified = bool(exists and expected_hash and current_hash == expected_hash)
            checked_files[f"{group_name}.{name}"] = {
                "path": rel_path,
                "exists": exists,
                "expected_sha256": expected_hash,
                "current_sha256": current_hash,
                "verified": verified,
            }
            if not verified:
                missing_or_mismatched.append(f"{group_name}.{name}")

    return {
        "scoring_lock_verified": not missing_or_mismatched,
        "missing_or_mismatched": missing_or_mismatched,
        "checked_files": checked_files,
    }


def _subject_count_from_pairs(pairs: list[Any]) -> int:
    return len({str(pair.subject) for pair in pairs})


def _subject_pair_counts(pairs: list[Any]) -> list[dict[str, Any]]:
    counts = Counter(str(pair.subject) for pair in pairs)
    return [{"subject": subject, "pair_count": count} for subject, count in sorted(counts.items())]


def _ranking_top_layer(summary: dict[str, Any] | None) -> str | None:
    if not isinstance(summary, dict):
        return None
    rows = summary.get("mechanism_ranking")
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        layer = rows[0].get("layer")
        return str(layer) if layer is not None else None
    return None


def _build_comparable_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# ds006072 Comparable Validation Status",
        "",
        payload["claim_guardrail"],
        "",
        f"- Status: `{payload['analysis_status']}`",
        f"- Unchanged scoring applied: `{str(payload['unchanged_scoring_applied']).lower()}`",
        f"- Scoring lock verified: `{str(payload['scoring_lock_verified']).lower()}`",
        f"- Pair count: `{payload['pair_count']}`",
        f"- Subject count: `{payload['subject_count']}`",
        f"- Required subject count: `{payload['minimum_comparable_subjects']}`",
        f"- Replication status: `{payload['replication_status']}`",
        "",
    ]
    if payload.get("blocker"):
        lines.extend(["## Blocker", "", str(payload["blocker"]), ""])
    if payload.get("mechanism_ranking"):
        lines.extend(["## Mechanism-Proxy Ranking", "", "| Rank | Layer | Score | Status |", "| ---: | --- | ---: | --- |"])
        for row in payload["mechanism_ranking"]:
            lines.append(
                "| {rank} | {layer} | {score:.3f} | {status} |".format(
                    rank=row.get("rank", ""),
                    layer=row.get("layer", ""),
                    score=float(row.get("score") or 0.0),
                    status=row.get("status", ""),
                )
            )
    return "\n".join(lines) + "\n"


def build_ds006072_comparable_validation_status(
    repo_root: Path = REPO_ROOT,
    *,
    refresh_scoring_lock: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = repo_root / "results" / "psilocybin_ds006072"
    output_dir.mkdir(parents=True, exist_ok=True)
    readiness = build_ds006072_external_validation_readiness(repo_root)
    scoring_spec_path = output_dir / "unchanged_scoring_spec.json"
    existing_scoring_spec = json.loads(scoring_spec_path.read_text(encoding="utf-8")) if scoring_spec_path.exists() else None
    extraction_status_path = output_dir / "cifti_empirical_extraction_status.json"
    extraction_status = json.loads(extraction_status_path.read_text(encoding="utf-8")) if extraction_status_path.exists() else {}
    schaefer100_ready = bool(extraction_status.get("schaefer100_empirical_viewer_ready"))
    viewer_root = (
        repo_root / str(extraction_status.get("schaefer100_viewer_root"))
        if schaefer100_ready and extraction_status.get("schaefer100_viewer_root")
        else output_dir / "empirical_viewer"
    )
    subject_views_dir = viewer_root / "subject_views"
    use_existing_lock = (
        subject_views_dir.exists()
        and isinstance(existing_scoring_spec, dict)
        and not refresh_scoring_lock
    )
    scoring_spec: dict[str, Any] | None
    if refresh_scoring_lock:
        scoring_spec = _write_scoring_spec(repo_root, output_dir)
    elif use_existing_lock:
        scoring_spec = existing_scoring_spec
    else:
        scoring_spec = json.loads(scoring_spec_path.read_text(encoding="utf-8")) if scoring_spec_path.exists() else None
    scoring_lock = _verify_locked_scoring_spec(repo_root, scoring_spec)
    subject_view_count = len(list(subject_views_dir.glob("*.json"))) if subject_views_dir.exists() else 0
    lsd_summary_path = repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json"
    lsd_summary = json.loads(lsd_summary_path.read_text(encoding="utf-8")) if lsd_summary_path.exists() else None
    lsd_top_layer = _ranking_top_layer(lsd_summary)

    base_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _now(),
        "dataset_id": DS006072_DATASET_ID,
        "primary_contrast": PRIMARY_CONTRAST,
        "viewer_root": _rel(viewer_root, repo_root),
        "subject_views_dir": _rel(subject_views_dir, repo_root),
        "subject_view_count": subject_view_count,
        "minimum_comparable_subjects": MIN_COMPARABLE_SUBJECTS,
        "readiness_status": readiness.get("analysis_status"),
        "readiness_path": "results/psilocybin_ds006072/external_validation_readiness.json",
        "unchanged_scoring_spec": "results/psilocybin_ds006072/unchanged_scoring_spec.json",
        "scoring_lock_verified": bool(scoring_lock["scoring_lock_verified"]),
        "scoring_lock": scoring_lock,
        "scoring_lock_refresh_requested": bool(refresh_scoring_lock),
        "unchanged_scoring_applied": False,
        "pair_count": 0,
        "subject_count": 0,
        "subject_pair_counts": [],
        "mechanism_ranking": [],
        "lsd_reference_top_layer": lsd_top_layer,
        "ds006072_top_layer": None,
        "replication_status": "not_scored",
        "extraction_status_path": "results/psilocybin_ds006072/cifti_empirical_extraction_status.json",
        "extraction_status": extraction_status.get("analysis_status"),
        "extraction_module_contract": (
            extraction_status.get("schaefer100_module_contract")
            if schaefer100_ready
            else extraction_status.get("module_contract")
        ),
        "structure_family_viewer_ready": bool(extraction_status.get("cifti_empirical_viewer_ready")),
        "schaefer100_empirical_viewer_ready": schaefer100_ready,
        "stronger_external_validation_ready": schaefer100_ready,
        "schaefer100_parcellation_id": extraction_status.get("schaefer100_parcellation_id"),
        "validation_scope": (
            "parcellation_matched_schaefer100_yeo7_external_validation"
            if schaefer100_ready
            else "structure_family_external_stress_test"
            if extraction_status.get("module_contract")
            else "harmonized_empirical_viewer_external_validation"
        ),
        "claim_guardrail": (
            "This artifact is the ds006072 external-validation gate. It only passes when paired local "
            "psilocybin/control empirical-viewer records exist and are scored with the locked ds003059 rule. "
            "A Schaefer100/Yeo7 validation scope is stronger than the CIFTI structure-family stress test, but "
            "still remains a small-subject cross-drug stress test rather than a population replication."
        ),
    }

    if not subject_views_dir.exists():
        payload = {
            **base_payload,
            "analysis_status": "blocked_missing_local_ds006072_empirical_viewer",
            "blocker": (
                "No paired ds006072 empirical-viewer subject views exist. Provide harmonized records under "
                f"{_rel(subject_views_dir, repo_root)} with ses-PLCB control and ses-LSD psilocybin aliases."
            ),
        }
    elif not scoring_lock["scoring_lock_verified"]:
        payload = {
            **base_payload,
            "analysis_status": "blocked_scoring_lock_not_verified",
            "blocker": (
                "The unchanged-scoring lock is missing or its target/code hashes no longer match: "
                + ", ".join(scoring_lock["missing_or_mismatched"])
            ),
        }
    else:
        pairs = load_empirical_pairs(viewer_root)
        pair_count = len(pairs)
        subject_count = _subject_count_from_pairs(pairs)
        if pair_count == 0:
            payload = {
                **base_payload,
                "analysis_status": "blocked_no_harmonized_ds006072_pairs",
                "blocker": (
                    f"Found {subject_view_count} subject-view files, but none contained both required harmonized "
                    "conditions: ses-PLCB for active-control MTP and ses-LSD for psilocybin."
                ),
            }
        elif subject_count < MIN_COMPARABLE_SUBJECTS:
            payload = {
                **base_payload,
                "analysis_status": "blocked_insufficient_ds006072_subjects_for_external_validation",
                "pair_count": pair_count,
                "subject_count": subject_count,
                "subject_pair_counts": _subject_pair_counts(pairs),
                "blocker": (
                    f"Only {subject_count} comparable ds006072 subjects are present; "
                    f"need at least {MIN_COMPARABLE_SUBJECTS} before reporting external validation."
                ),
            }
        else:
            summary = build_dynamic_mechanism_summary(viewer_root)
            summary["dataset_scope"] = (
                "OpenNeuro ds006072 paired psilocybin/MTP empirical viewer records scored with the locked ds003059 rule"
            )
            extraction_contract = (
                extraction_status.get("schaefer100_module_contract")
                if schaefer100_ready
                else extraction_status.get("module_contract")
            )
            if extraction_contract:
                summary["dataset_scope"] += f"; extraction contract: {extraction_contract}"
            ds006072_top_layer = _ranking_top_layer(summary)
            replication_status = (
                "ranking_replicates_lsd_top_layer"
                if lsd_top_layer is not None and ds006072_top_layer == lsd_top_layer
                else "ranking_differs_from_lsd_top_layer"
                if lsd_top_layer is not None and ds006072_top_layer is not None
                else "scored_no_lsd_reference_top_layer"
            )
            payload = {
                **base_payload,
                "analysis_status": "implemented_ds006072_unchanged_scoring_validation",
                "unchanged_scoring_applied": True,
                "pair_count": int(summary.get("pair_count") or pair_count),
                "subject_count": int(summary.get("subject_count") or subject_count),
                "subject_pair_counts": _subject_pair_counts(pairs),
                "mechanism_ranking": summary.get("mechanism_ranking", []),
                "summary": summary,
                "ds006072_top_layer": ds006072_top_layer,
                "replication_status": replication_status,
                "blocker": "",
                "claim_status": (
                    "external_parcellation_matched_validation_supports_lsd_top_layer"
                    if schaefer100_ready
                    and replication_status == "ranking_replicates_lsd_top_layer"
                    else "external_parcellation_matched_validation_scored_but_does_not_replicate_lsd_top_layer"
                    if schaefer100_ready
                    else
                    "external_structure_family_validation_supports_lsd_top_layer"
                    if extraction_status.get("module_contract")
                    and replication_status == "ranking_replicates_lsd_top_layer"
                    else "external_validation_supports_lsd_top_layer"
                    if replication_status == "ranking_replicates_lsd_top_layer"
                    else "external_validation_scored_but_does_not_replicate_lsd_top_layer"
                ),
            }

    status_path = output_dir / "comparable_empirical_validation_summary.json"
    report_path = output_dir / "comparable_empirical_validation_summary.md"
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_build_comparable_markdown(payload), encoding="utf-8")
    payload["source_path"] = _rel(status_path, repo_root)
    payload["report_path"] = _rel(report_path, repo_root)
    return payload


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
            "This is an extraction-and-scoring gate for external stress testing. Paired psilocybin/MTP empirical "
            "viewer records plus unchanged scoring are required before the stress test can run, and top-layer "
            "mismatches remain negative or partial external evidence."
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
