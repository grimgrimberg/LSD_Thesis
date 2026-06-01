from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from lsd_thesis.external_source_plan import EXTERNAL_SOURCE_PLAN_COLUMNS

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

DEFAULT_OUTPUT_DIR = REPO_ROOT / "results" / "thesis_evidence_loop" / "exports"
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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))


def _headers(rows: list[dict[str, Any]]) -> list[str]:
    if rows and all(column in rows[0] for column in CLAIM_EVIDENCE_COLUMNS):
        return CLAIM_EVIDENCE_COLUMNS
    if rows and all(column in rows[0] for column in EXTERNAL_SOURCE_PLAN_COLUMNS):
        return EXTERNAL_SOURCE_PLAN_COLUMNS
    return sorted({key for row in rows for key in row})


def _write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output_headers = headers or _headers(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _ds006072_summary(repo_root: Path) -> list[dict[str, Any]]:
    manifest = _load_json(repo_root / "data" / "ds006072" / "ds006072_func_manifest.json")
    metadata = _load_json(repo_root / "data" / "ds006072" / "ds006072_metadata_manifest.json")
    return [
        {"item": "snapshot_tag", "value": manifest.get("snapshot_tag") or metadata.get("snapshot_tag")},
        {"item": "subject_count", "value": manifest.get("subject_count")},
        {"item": "functional_file_count", "value": manifest.get("functional_file_count")},
        {"item": "rest_bold_nifti_count", "value": manifest.get("rest_bold_nifti_count")},
        {"item": "rest_bold_total_size_bytes", "value": manifest.get("rest_bold_total_size_bytes")},
        {"item": "processed_cifti_count", "value": manifest.get("processed_cifti_count")},
        {"item": "processed_rest_cifti_count", "value": manifest.get("processed_rest_cifti_count")},
        {"item": "processed_cifti_total_size_bytes", "value": manifest.get("processed_cifti_total_size_bytes")},
        {"item": "metadata_manifest", "value": metadata.get("source_path")},
        {"item": "functional_manifest", "value": manifest.get("source_path")},
        {"item": "cifti_manifest_csv", "value": manifest.get("cifti_csv_path")},
    ]


def export_thesis_loop_tables(repo_root: Path, output_dir: Path) -> dict[str, str]:
    from export_dynamic_mechanism_tables import _write_xlsx

    loop = _load_json(repo_root / "results" / "thesis_evidence_loop" / "thesis_evidence_loop_status.json")
    status_rows = list(loop.get("status_rows", []))
    claim_rows = _read_csv(repo_root / "results" / "thesis_evidence_loop" / "claim_evidence_matrix.csv")
    external_source_rows = _read_csv(repo_root / "results" / "thesis_evidence_loop" / "external_source_plan.csv")
    if not external_source_rows:
        external_source_rows = list(loop.get("external_source_plan", []))
    parcellation_rows = _read_csv(repo_root / "results" / "parcellation_sensitivity" / "parcellation_status.csv")
    parcellation_ranking_rows = _read_csv(repo_root / "results" / "parcellation_sensitivity" / "parcellation_ranking_comparison.csv")
    graph_rows = _read_csv(repo_root / "results" / "structural_connectome" / "proxy_graph_control_nulls.csv")
    receptor_rows = _read_csv(repo_root / "results" / "receptor_priors" / "proxy_receptor_null_board.csv")
    ds006072_rows = _ds006072_summary(repo_root)

    tables = {
        "status_rows": status_rows,
        "external_source_plan": external_source_rows,
        "claim_evidence_matrix": claim_rows,
        "ds006072_summary": ds006072_rows,
        "parcellation_status": parcellation_rows,
        "parcellation_ranking": parcellation_ranking_rows,
        "proxy_graph_nulls": graph_rows,
        "receptor_null_board": receptor_rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        _write_csv(output_dir / f"{name}.csv", rows)
    workbook_path = output_dir / "thesis_evidence_loop_tables.xlsx"
    _write_xlsx(
        workbook_path,
        {
            name: (_headers(rows), rows)
            for name, rows in tables.items()
        },
    )
    return {
        "output_dir": output_dir.as_posix(),
        "workbook_path": workbook_path.as_posix(),
        "claim_matrix_csv": (output_dir / "claim_evidence_matrix.csv").as_posix(),
        "external_source_plan_csv": (output_dir / "external_source_plan.csv").as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export thesis evidence-loop status and null tables to CSV/XLSX.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    outputs = export_thesis_loop_tables(args.repo_root.resolve(), args.output_dir)
    print(json.dumps(outputs, indent=2), flush=True)


if __name__ == "__main__":
    main()
