from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from lsd_thesis.data.ds003059 import MODULE_NAMES
from lsd_thesis.data.parcellations import get_parcellation_spec
from lsd_thesis.external_ingestion import ingest_receptor_prior, ingest_structural_connectome

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "hansen_macro_priors.v1"

HANSEN_REPOSITORY_URL = "https://github.com/netneurolab/hansen_receptors"
HANSEN_LICENSE = "CC BY-NC-SA 4.0"
RAW_BASE_URL = "https://raw.githubusercontent.com/netneurolab/hansen_receptors/main/data"

RECEPTOR_FILES = (
    "PET_parcellated/scale100/5HT2a_cimbi_hc29_beliveau.csv",
    "PET_parcellated/scale100/5HT2a_alt_hc19_savli.csv",
    "PET_parcellated/scale100/5HT2a_mdl_hc3_talbot.csv",
)
STRUCTURAL_FILE = "schaefer/sc_weighted.npy"

COARSE_TO_MODULE = {
    "visual": "visual",
    "somatomotor": "sensorimotor",
    "salience_ventral_attention": "salience",
    "default": "default_mode",
    "control": "executive_frontoparietal",
    "limbic": "limbic_affective",
}

IMPUTED_MODULE_SOURCES = {
    "auditory": ("somatomotor",),
    "thalamic_gateway": (
        "visual",
        "somatomotor",
        "salience_ventral_attention",
        "default",
        "control",
        "limbic",
    ),
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sample_size_from_filename(filename: str) -> int:
    match = re.search(r"_hc(\d+)_", filename)
    if match is None:
        return 1
    return max(int(match.group(1)), 1)


def _fetch_source_file(
    relative_path: str,
    *,
    cache_dir: Path,
    fetch_missing: bool,
) -> dict[str, Any]:
    url = f"{RAW_BASE_URL}/{relative_path}"
    target = cache_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        if not fetch_missing:
            raise FileNotFoundError(f"Missing cached Hansen source file: {target}")
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = response.read()
        target.write_bytes(payload)
    else:
        payload = target.read_bytes()
    return {
        "relative_path": relative_path,
        "url": url,
        "cache_path": target.as_posix(),
        "sha256": _sha256_bytes(payload),
        "size_bytes": len(payload),
    }


def _load_pet_vector(path: Path) -> np.ndarray:
    values = np.loadtxt(path, delimiter=",", ndmin=1)
    values = np.asarray(values, dtype=float).reshape(-1)
    if values.shape != (100,):
        raise ValueError(f"Expected a Schaefer-100 PET vector in {path}, got shape {values.shape}.")
    if not np.all(np.isfinite(values)):
        raise ValueError(f"PET vector contains non-finite values: {path}")
    return values


def _load_structural_matrix(path: Path) -> np.ndarray:
    with path.open("rb") as handle:
        matrix = np.load(io.BytesIO(handle.read()))
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape != (100, 100):
        raise ValueError(f"Expected a 100x100 Schaefer structural matrix in {path}, got shape {matrix.shape}.")
    if not np.all(np.isfinite(matrix)):
        raise ValueError(f"Structural matrix contains non-finite values: {path}")
    if np.any(matrix < 0):
        raise ValueError(f"Structural matrix contains negative weights: {path}")
    return (matrix + matrix.T) / 2.0


def _zscore(values: np.ndarray) -> np.ndarray:
    std = float(np.std(values))
    if std <= 1e-12:
        return np.zeros_like(values, dtype=float)
    return (values - float(np.mean(values))) / std


def _parcel_class_indices() -> dict[str, list[int]]:
    spec = get_parcellation_spec("schaefer_100_yeo_7")
    classes: dict[str, list[int]] = {}
    for index, node in enumerate(spec.node_metadata):
        classes.setdefault(str(node.coarse_class), []).append(index)
    return classes


def _module_indices() -> tuple[dict[str, list[int]], dict[str, dict[str, Any]]]:
    class_indices = _parcel_class_indices()
    module_indices: dict[str, list[int]] = {}
    projection: dict[str, dict[str, Any]] = {}
    for coarse_class, module in COARSE_TO_MODULE.items():
        indices = list(class_indices.get(coarse_class, []))
        module_indices[module] = indices
        projection[module] = {
            "projection_status": "direct_schaefer_yeo7_class",
            "source_classes": [coarse_class],
            "parcel_count": len(indices),
        }
    for module, source_classes in IMPUTED_MODULE_SOURCES.items():
        indices = [
            index
            for source_class in source_classes
            for index in class_indices.get(source_class, [])
        ]
        module_indices[module] = indices
        projection[module] = {
            "projection_status": "imputed_from_cortical_schaefer_yeo7_classes",
            "source_classes": list(source_classes),
            "parcel_count": len(indices),
        }
    missing = [module for module in MODULE_NAMES if module not in module_indices or not module_indices[module]]
    if missing:
        raise ValueError(f"Cannot project Hansen sources to modules: missing {', '.join(missing)}.")
    return module_indices, projection


def _combine_receptor_maps(receptor_maps: list[tuple[str, np.ndarray]]) -> tuple[np.ndarray, list[dict[str, Any]]]:
    weighted: list[np.ndarray] = []
    weights: list[float] = []
    source_rows: list[dict[str, Any]] = []
    for filename, values in receptor_maps:
        sample_size = _sample_size_from_filename(filename)
        z_values = _zscore(values)
        weighted.append(z_values * float(sample_size))
        weights.append(float(sample_size))
        source_rows.append(
            {
                "filename": filename,
                "healthy_control_n": sample_size,
                "raw_mean": float(np.mean(values)),
                "raw_std": float(np.std(values)),
                "zscore_before_averaging": True,
            }
        )
    if not weighted or not weights:
        raise ValueError("At least one receptor map is required.")
    return np.sum(np.vstack(weighted), axis=0) / float(np.sum(weights)), source_rows


def project_receptor_to_modules(receptor_maps: list[tuple[str, np.ndarray]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    combined, source_rows = _combine_receptor_maps(receptor_maps)
    module_indices, projection = _module_indices()
    rows: list[dict[str, Any]] = []
    for module in MODULE_NAMES:
        indices = module_indices[module]
        projected = float(np.mean(combined[indices]))
        rows.append(
            {
                "module": module,
                "receptor_weight": projected,
                "source": "Hansen et al. Schaefer-100 PET 5-HT2A maps; z-scored and sample-size weighted",
                "projection_status": projection[module]["projection_status"],
                "source_classes": "|".join(projection[module]["source_classes"]),
                "parcel_count": projection[module]["parcel_count"],
            }
        )
    return rows, {
        "source_receptor_maps": source_rows,
        "aggregation": "within-map z-score, then healthy-control-sample-size weighted average across 5-HT2A maps",
        "module_projection": projection,
    }


def project_structural_to_modules(structural_matrix: np.ndarray) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    matrix = np.asarray(structural_matrix, dtype=float)
    if matrix.shape != (100, 100):
        raise ValueError(f"Expected structural matrix shape (100, 100), got {matrix.shape}.")
    module_indices, projection = _module_indices()
    macro = np.zeros((len(MODULE_NAMES), len(MODULE_NAMES)), dtype=float)
    for row_index, source in enumerate(MODULE_NAMES):
        source_indices = module_indices[source]
        for column_index, target in enumerate(MODULE_NAMES):
            target_indices = module_indices[target]
            macro[row_index, column_index] = float(
                np.mean(matrix[np.ix_(source_indices, target_indices)])
            )
    macro = (macro + macro.T) / 2.0
    np.fill_diagonal(macro, 0.0)
    off_diagonal = macro[~np.eye(len(MODULE_NAMES), dtype=bool)]
    max_weight = float(np.max(off_diagonal)) if off_diagonal.size else 0.0
    if max_weight > 0.0 and math.isfinite(max_weight):
        macro = macro / max_weight
    rows: list[dict[str, Any]] = []
    for row_index, source in enumerate(MODULE_NAMES):
        rows.append(
            {
                "module": source,
                **{target: float(macro[row_index, column_index]) for column_index, target in enumerate(MODULE_NAMES)},
            }
        )
    return rows, {
        "aggregation": "mean Schaefer-100 structural weights between projected macro-module parcel sets; max off-diagonal normalized to 1",
        "module_projection": projection,
    }


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_summary(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Hansen PET/SC Macro-Module Projection",
        "",
        f"- Generated: `{manifest['generated_at_utc']}`",
        f"- Source repository: {manifest['source_repository']}",
        f"- Source license: `{manifest['source_license']}`",
        f"- Receptor output: `{manifest['outputs']['receptor_prior']}`",
        f"- Structural output: `{manifest['outputs']['structural_connectome']}`",
        "",
        "## Claim boundary",
        "",
        manifest["claim_guardrail"],
        "",
        "## Projection notes",
        "",
        "- Schaefer/Yeo-7 has no explicit auditory or thalamic parcel class.",
        "- `auditory` is imputed from somatomotor parcels.",
        "- `thalamic_gateway` is imputed from the global cortical Schaefer parcel set.",
        "- These priors support sensitivity analysis only; they are not receptor pharmacology or a biological thalamic model.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def derive_hansen_macro_priors(
    *,
    repo_root: Path = REPO_ROOT,
    cache_dir: Path | None = None,
    output_dir: Path | None = None,
    fetch_missing: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    cache_dir = cache_dir or repo_root / "results" / "external_ingestion" / "hansen_receptors" / "source"
    output_dir = output_dir or repo_root / "results" / "external_ingestion" / "hansen_receptors"
    cache_dir = cache_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_files = [
        _fetch_source_file(relative_path, cache_dir=cache_dir, fetch_missing=fetch_missing)
        for relative_path in (*RECEPTOR_FILES, STRUCTURAL_FILE)
    ]
    receptor_maps = [
        (relative_path, _load_pet_vector(cache_dir / relative_path))
        for relative_path in RECEPTOR_FILES
    ]
    receptor_rows, receptor_projection = project_receptor_to_modules(receptor_maps)
    structural_rows, structural_projection = project_structural_to_modules(
        _load_structural_matrix(cache_dir / STRUCTURAL_FILE)
    )

    receptor_source_path = output_dir / "fs5ht_5ht2a_macro_modules_raw.csv"
    structural_source_path = output_dir / "hcp_macro_modules_projected_from_schaefer100.csv"
    _write_csv(
        receptor_source_path,
        ["module", "receptor_weight", "source", "projection_status", "source_classes", "parcel_count"],
        receptor_rows,
    )
    _write_csv(structural_source_path, ["module", *MODULE_NAMES], structural_rows)

    receptor_manifest = ingest_receptor_prior(
        receptor_source_path,
        repo_root=repo_root,
        output_path=repo_root / "results" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv",
        provenance="hansen_receptors_schaefer100_5ht2a_pet_projection",
    )
    structural_manifest = ingest_structural_connectome(
        structural_source_path,
        repo_root=repo_root,
        output_path=repo_root / "results" / "structural_connectome" / "hcp_macro_modules.csv",
        provenance="hansen_receptors_schaefer100_weighted_structural_projection",
    )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _now(),
        "source_repository": HANSEN_REPOSITORY_URL,
        "source_license": HANSEN_LICENSE,
        "source_files": source_files,
        "source_file_policy": (
            "Raw Hansen files are downloaded into a local cache for reproducibility. "
            "Public artifacts should cite the URLs and checksums rather than claiming ownership of the source data."
        ),
        "receptor_projection": receptor_projection,
        "structural_projection": structural_projection,
        "outputs": {
            "hansen_manifest": _rel(output_dir / "hansen_macro_projection_manifest.json", repo_root),
            "hansen_summary": _rel(output_dir / "hansen_macro_projection_summary.md", repo_root),
            "receptor_source_csv": _rel(receptor_source_path, repo_root),
            "structural_source_csv": _rel(structural_source_path, repo_root),
            "receptor_prior": receptor_manifest["output_path"],
            "structural_connectome": structural_manifest["output_path"],
            "receptor_ingestion_manifest": receptor_manifest["manifest_path"],
            "structural_ingestion_manifest": structural_manifest["manifest_path"],
        },
        "claim_guardrail": (
            "This is an authorized public PET/SC projection into the repository macro-module contract. "
            "It strengthens receptor/structural sensitivity layers but does not make receptor-level, clinical, "
            "subjective-experience, auditory, or thalamic biological claims."
        ),
    }
    manifest_path = output_dir / "hansen_macro_projection_manifest.json"
    summary_path = output_dir / "hansen_macro_projection_summary.md"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _write_summary(summary_path, manifest)
    return manifest
