from __future__ import annotations

import csv
import json
import math
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lsd_thesis.data.ds003059 import MODULE_NAMES

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "external_ingestion.v1"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _finite_float(value: Any, *, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Expected numeric {field}, got {value!r}.") from exc
    if not math.isfinite(number):
        raise ValueError(f"Expected finite {field}, got {value!r}.")
    return number


def _empty_matrix() -> dict[str, dict[str, float]]:
    return {source: {target: 0.0 for target in MODULE_NAMES} for source in MODULE_NAMES}


def _matrix_from_edge_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    matrix = _empty_matrix()
    modules = set(MODULE_NAMES)
    for row in rows:
        source = str(row.get("source", "")).strip()
        target = str(row.get("target", "")).strip()
        if source not in modules or target not in modules:
            raise ValueError(f"Structural edge uses unknown module: source={source!r}, target={target!r}.")
        weight = _finite_float(row.get("weight"), field="weight")
        if weight < 0:
            raise ValueError("Structural-connectome weights must be non-negative.")
        matrix[source][target] = weight
        matrix[target][source] = weight
    return matrix


def _matrix_from_square_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    matrix = _empty_matrix()
    by_module = {str(row.get("module", "")).strip(): row for row in rows}
    missing = [module for module in MODULE_NAMES if module not in by_module]
    if missing:
        raise ValueError(f"Structural square matrix is missing module rows: {', '.join(missing)}.")
    for source in MODULE_NAMES:
        row = by_module[source]
        for target in MODULE_NAMES:
            if target not in row:
                raise ValueError(f"Structural square matrix is missing column {target!r}.")
            weight = _finite_float(row[target], field=f"{source}->{target}")
            if weight < 0:
                raise ValueError("Structural-connectome weights must be non-negative.")
            matrix[source][target] = weight
    return matrix


def load_structural_matrix(path: Path) -> dict[str, dict[str, float]]:
    rows = _read_csv(path)
    if not rows:
        raise ValueError("Structural-connectome CSV is empty.")
    fields = set(rows[0])
    if {"source", "target", "weight"}.issubset(fields):
        matrix = _matrix_from_edge_rows(rows)
    elif "module" in fields:
        matrix = _matrix_from_square_rows(rows)
    else:
        raise ValueError("Structural CSV must be source,target,weight edge list or module square matrix.")
    for module in MODULE_NAMES:
        matrix[module][module] = 0.0
    return matrix


def ingest_structural_connectome(
    source_csv: Path,
    *,
    repo_root: Path = REPO_ROOT,
    output_path: Path | None = None,
    provenance: str = "user_supplied_structural_connectome_csv",
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    source_csv = source_csv.resolve()
    output_path = output_path or repo_root / "data" / "hcp_structural_connectome" / "macro_modules.csv"
    matrix = load_structural_matrix(source_csv)
    rows = [{"module": source, **{target: matrix[source][target] for target in MODULE_NAMES}} for source in MODULE_NAMES]
    _write_csv(output_path, ["module", *MODULE_NAMES], rows)
    copied_source = output_path.parent / f"source_{source_csv.name}"
    if source_csv != copied_source:
        shutil.copy2(source_csv, copied_source)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "structural_connectome",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_csv": str(source_csv),
        "copied_source": _rel(copied_source, repo_root),
        "output_path": _rel(output_path, repo_root),
        "provenance": provenance,
        "module_count": len(MODULE_NAMES),
        "modules": list(MODULE_NAMES),
        "claim_guardrail": (
            "This validates and imports a structural-connectome matrix for sensitivity analysis. "
            "It does not prove receptor-level, clinical, or subjective psychedelic mechanisms."
        ),
    }
    manifest_path = output_path.parent / "structural_connectome_ingestion_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest_path"] = _rel(manifest_path, repo_root)
    return manifest


def load_receptor_prior_rows(path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    if not rows:
        raise ValueError("Receptor-prior CSV is empty.")
    by_module = {str(row.get("module", "")).strip(): row for row in rows}
    missing = [module for module in MODULE_NAMES if module not in by_module]
    if missing:
        raise ValueError(f"Receptor-prior CSV is missing modules: {', '.join(missing)}.")
    raw_values = []
    for module in MODULE_NAMES:
        row = by_module[module]
        field = "receptor_weight" if "receptor_weight" in row else "weight"
        raw_values.append(_finite_float(row.get(field), field=f"{module}.{field}"))
    min_value = min(raw_values)
    max_value = max(raw_values)
    span = max(max_value - min_value, 1e-12)
    normalized = [(value - min_value) / span for value in raw_values]
    return [
        {
            "module": module,
            "receptor_weight": value,
            "raw_receptor_weight": raw_value,
            "source": str(by_module[module].get("source") or "PET-derived receptor prior projection"),
        }
        for module, value, raw_value in zip(MODULE_NAMES, normalized, raw_values, strict=True)
    ]


def ingest_receptor_prior(
    source_csv: Path,
    *,
    repo_root: Path = REPO_ROOT,
    output_path: Path | None = None,
    provenance: str = "user_supplied_pet_receptor_prior_csv",
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    source_csv = source_csv.resolve()
    output_path = output_path or repo_root / "data" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv"
    rows = load_receptor_prior_rows(source_csv)
    _write_csv(output_path, ["module", "receptor_weight", "raw_receptor_weight", "source"], rows)
    copied_source = output_path.parent / f"source_{source_csv.name}"
    if source_csv != copied_source:
        shutil.copy2(source_csv, copied_source)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "receptor_prior",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_csv": str(source_csv),
        "copied_source": _rel(copied_source, repo_root),
        "output_path": _rel(output_path, repo_root),
        "provenance": provenance,
        "normalization": "min_max_0_1_within_supplied_module_vector",
        "module_count": len(MODULE_NAMES),
        "modules": list(MODULE_NAMES),
        "claim_guardrail": (
            "This validates and imports a PET-derived receptor-prior vector for sensitivity analysis. "
            "It remains a parcellation-level prior, not receptor pharmacology or subjective-experience evidence."
        ),
    }
    manifest_path = output_path.parent / "receptor_prior_ingestion_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest_path"] = _rel(manifest_path, repo_root)
    return manifest


def build_external_ingestion_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    path_candidates = {
        "ds006072_metadata": [repo_root / "data" / "ds006072" / "ds006072_metadata_manifest.json"],
        "ds006072_func_manifest": [repo_root / "data" / "ds006072" / "ds006072_func_manifest.json"],
        "structural_matrix": [
            repo_root / "results" / "structural_connectome" / "hcp_macro_modules.csv",
            repo_root / "data" / "hcp_structural_connectome" / "macro_modules.csv",
        ],
        "structural_manifest": [
            repo_root / "results" / "structural_connectome" / "structural_connectome_ingestion_manifest.json",
            repo_root
            / "data"
            / "hcp_structural_connectome"
            / "structural_connectome_ingestion_manifest.json",
        ],
        "receptor_prior": [
            repo_root / "results" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv",
            repo_root / "data" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv",
        ],
        "receptor_manifest": [
            repo_root / "results" / "receptor_priors" / "receptor_prior_ingestion_manifest.json",
            repo_root / "data" / "receptor_priors" / "receptor_prior_ingestion_manifest.json",
        ],
    }
    paths = {
        name: next((path for path in candidates if path.exists() and path.is_file()), candidates[0])
        for name, candidates in path_candidates.items()
    }
    ready = {name: path.exists() and path.is_file() for name, path in paths.items()}
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "ready": ready,
        "paths": {name: _rel(path, repo_root) for name, path in paths.items()},
        "path_candidates": {
            name: [_rel(path, repo_root) for path in candidates] for name, candidates in path_candidates.items()
        },
        "analysis_status": {
            "ds006072_metadata": "ready" if ready["ds006072_metadata"] else "missing",
            "ds006072_func_manifest": "ready" if ready["ds006072_func_manifest"] else "missing",
            "structural_connectome": "ready" if ready["structural_matrix"] else "missing_local_structural_matrix",
            "receptor_prior": "ready" if ready["receptor_prior"] else "missing_local_pet_receptor_prior",
        },
        "next_commands": {
            "ds006072_metadata": "uv run python scripts/download_ds006072_metadata.py",
            "ds006072_functional_manifest": "uv run python scripts/build_ds006072_func_manifest.py",
            "ingest_structural": "uv run python scripts/ingest_external_priors.py --structural-csv <path-to-structural-csv>",
            "ingest_receptor": "uv run python scripts/ingest_external_priors.py --receptor-csv <path-to-receptor-csv>",
            "refresh_thesis_loop": "uv run python scripts/run_thesis_evidence_loop.py",
        },
        "claim_guardrail": (
            "External ingestion readiness is provenance and schema readiness. It is not external validation until "
            "comparable empirical viewer records and unchanged scoring rules produce results."
        ),
    }


def write_external_ingestion_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "external_ingestion"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_external_ingestion_status(repo_root)
    status_path = output_dir / "external_ingestion_status.json"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    status["source_path"] = _rel(status_path, repo_root)
    return status
