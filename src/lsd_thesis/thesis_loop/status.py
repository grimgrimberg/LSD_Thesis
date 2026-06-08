from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[3]
DS006072_DATASET_ID = "ds006072"
CLAIM_EVIDENCE_COLUMNS = [
    "claim",
    "dataset",
    "model layer",
    "null/control",
    "figure",
    "csv/xlsx export",
    "citation",
    "limitation",
    "status",
]

def _now() -> str:
    return datetime.now(UTC).isoformat()

def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path.as_posix()

def _write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str] | None = None) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    csv_headers = headers or sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path.as_posix()

def _markdown_cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")

def _write_markdown_table(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(_markdown_cell(row.get(header, "")) for header in headers) + " |" for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.as_posix()

def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))

def _status_row(
    step: str,
    label: str,
    status: str,
    artifact_target: str,
    evidence: str,
    blocker: str = "",
) -> dict[str, Any]:
    return {
        "step": step,
        "label": label,
        "status": status,
        "artifact_target": artifact_target,
        "evidence": evidence,
        "blocker": blocker,
    }

def _claim_row(
    *,
    claim: str,
    dataset: str,
    model_layer: str,
    null_control: str,
    figure: str,
    export: str,
    citation: str,
    limitation: str,
    status: str,
) -> dict[str, Any]:
    return {
        "claim": claim,
        "dataset": dataset,
        "model layer": model_layer,
        "null/control": null_control,
        "figure": figure,
        "csv/xlsx export": export,
        "citation": citation,
        "limitation": limitation,
        "status": status,
    }

def _analysis_status(component: dict[str, Any], fallback: str = "missing") -> str:
    return str(component.get("analysis_status") or fallback)

def _external_source_component_status(name: str, component: dict[str, Any]) -> str:
    status = _analysis_status(component)
    if name == "parcellation_sensitivity":
        rows = component.get("rows")
        implemented_rows = []
        if isinstance(rows, list):
            implemented_rows = [
                row
                for row in rows
                if isinstance(row, dict) and str(row.get("status")) == "implemented_mechanism_ranking"
            ]
        if not implemented_rows:
            return "blocked_missing_parcellation_viewers"
    return status

def _parcellation_claim_status(component: dict[str, Any]) -> str:
    required = {
        "schaefer_100_yeo_7",
        "schaefer_200_yeo_7",
        "schaefer_100_yeo_17",
        "schaefer_200_yeo_17",
    }
    rows = [row for row in component.get("rows", []) if isinstance(row, dict)]
    implemented = {
        str(row.get("parcellation_id")): str(row.get("top_layer"))
        for row in rows
        if row.get("status") == "implemented_mechanism_ranking"
    }
    if required.issubset(implemented) and all(implemented[parcellation_id] == "C" for parcellation_id in required):
        return "implemented_c_top_rank_all_requested_parcellations"
    if implemented:
        return "implemented_status_matrix_direction_review_required"
    return _analysis_status(component)

def _literature_mismatch_status(component: dict[str, Any]) -> str:
    if _analysis_status(component).startswith("blocked"):
        return _analysis_status(component)
    measurable = int(component.get("measurable_count") or 0)
    aligned = int(component.get("aligned_count") or 0)
    if measurable <= 0:
        return "blocked_no_measurable_literature_checks"
    failed = max(measurable - aligned, 0)
    if failed == 0:
        return "implemented_all_measurable_literature_checks_aligned"
    return f"requires_mismatch_diagnosis_{failed}_of_{measurable}_checks"
