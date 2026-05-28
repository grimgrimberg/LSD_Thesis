from __future__ import annotations

import importlib.util
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "neuromaps_spatial_null_status.v1"
SCHAEFER_ID = "schaefer_100_yeo_7"
DEFAULT_N_PERM = 999
DEFAULT_SEED = 20260528
PET_RECEPTOR_MAPS = (
    {
        "map_id": "5ht2a_alt_hc19_savli",
        "family": "receptor",
        "label": "5-HT2A ALT/Savli PET, Schaefer100",
        "path": Path("results/external_ingestion/hansen_receptors/source/PET_parcellated/scale100/5HT2a_alt_hc19_savli.csv"),
    },
    {
        "map_id": "5ht2a_cimbi_hc29_beliveau",
        "family": "receptor",
        "label": "5-HT2A CIMBI/Beliveau PET, Schaefer100",
        "path": Path("results/external_ingestion/hansen_receptors/source/PET_parcellated/scale100/5HT2a_cimbi_hc29_beliveau.csv"),
    },
    {
        "map_id": "5ht2a_mdl_hc3_talbot",
        "family": "receptor",
        "label": "5-HT2A MDL/Talbot PET, Schaefer100",
        "path": Path("results/external_ingestion/hansen_receptors/source/PET_parcellated/scale100/5HT2a_mdl_hc3_talbot.csv"),
    },
)
TARGET_VECTOR_KEYS = (
    ("dmdc_condition_input", "DMDC condition-input vector", "condition_input_vector", "signed"),
    ("dmdc_condition_interaction", "DMDC condition-interaction vector", "condition_interaction_vector", "signed"),
    ("dmdc_condition_interaction_abs", "Absolute DMDC condition-interaction vector", "condition_interaction_vector", "absolute"),
)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(raw).__name__}.")
    return raw


def _rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _candidate_inputs(repo_root: Path) -> dict[str, str | bool]:
    surface_manifest = repo_root / "results" / "cortical_maps" / "neuromaps_surface_inputs.json"
    schaefer_summary = (
        repo_root
        / "results"
        / "stage_2"
        / "parcellations"
        / "schaefer_100_yeo_7"
        / "parcellation_extraction_summary.json"
    )
    cortical_alignment = repo_root / "results" / "cortical_maps" / "cortical_map_alignment_status.json"
    parcellation_summary = repo_root / "results" / "parcellation_sensitivity" / SCHAEFER_ID / "summary.json"
    pet_paths = [repo_root / item["path"] for item in PET_RECEPTOR_MAPS]
    return {
        "surface_manifest": _rel(surface_manifest, repo_root),
        "surface_manifest_exists": surface_manifest.exists(),
        "schaefer_100_yeo_7_summary": _rel(schaefer_summary, repo_root),
        "schaefer_100_yeo_7_summary_exists": schaefer_summary.exists(),
        "module_level_alignment_status": _rel(cortical_alignment, repo_root),
        "module_level_alignment_status_exists": cortical_alignment.exists(),
        "schaefer_100_yeo_7_mechanism_summary": _rel(parcellation_summary, repo_root),
        "schaefer_100_yeo_7_mechanism_summary_exists": parcellation_summary.exists(),
        "hansen_5ht2a_pet_scale100_csvs_present": all(path.exists() for path in pet_paths),
    }


def _neuromaps_runtime() -> dict[str, Any]:
    if importlib.util.find_spec("neuromaps") is None:
        return {
            "dependency_available": False,
            "null_api_importable": False,
            "version": None,
            "available_null_families": [],
            "runtime_error": "neuromaps is not installed",
        }
    try:
        import neuromaps
        from neuromaps import nulls
    except Exception as exc:
        return {
            "dependency_available": True,
            "null_api_importable": False,
            "version": None,
            "available_null_families": [],
            "runtime_error": f"{type(exc).__name__}: {exc}",
        }
    families = [
        name
        for name in (
            "alexander_bloch",
            "baum",
            "burt2018",
            "burt2020",
            "cornblath",
            "hungarian",
            "moran",
            "vasa",
            "vazquez_rodriguez",
        )
        if callable(getattr(nulls, name, None))
    ]
    return {
        "dependency_available": True,
        "null_api_importable": True,
        "version": getattr(neuromaps, "__version__", None),
        "available_null_families": families,
        "runtime_error": None,
    }


def _load_numeric_vector(path: Path, expected_size: int = 100) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
    raw = path.read_text(encoding="utf-8").replace("\n", ",").split(",")
    values = np.asarray([float(item.strip()) for item in raw if item.strip()], dtype=float)
    if values.shape != (expected_size,):
        raise ValueError(f"Expected {expected_size} values in {path}, found {values.size}.")
    return values


def _load_schaefer_atlas_path(repo_root: Path) -> Path:
    summary_path = repo_root / "results" / "stage_2" / "parcellations" / SCHAEFER_ID / "parcellation_extraction_summary.json"
    payload = _read_json(summary_path) or {}
    atlas_path = payload.get("atlas_metadata", {}).get("maps_path") if isinstance(payload.get("atlas_metadata"), dict) else None
    if not atlas_path:
        raise FileNotFoundError("Missing Schaefer atlas maps_path in parcellation extraction summary.")
    path = Path(str(atlas_path))
    if not path.is_absolute():
        path = repo_root / path
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _schaefer_centroids(atlas_path: Path, expected_size: int = 100) -> np.ndarray:
    image = nib.load(str(atlas_path))
    data = np.asarray(image.get_fdata(), dtype=float)
    centroids: list[np.ndarray] = []
    for label in range(1, expected_size + 1):
        voxels = np.column_stack(np.where(np.isclose(data, label)))
        if voxels.size == 0:
            raise ValueError(f"Atlas {atlas_path} is missing Schaefer label {label}.")
        world = nib.affines.apply_affine(image.affine, voxels)
        centroids.append(np.asarray(world, dtype=float).mean(axis=0))
    return np.vstack(centroids)


def _hemisphere_distance_matrices(centroids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if centroids.ndim != 2 or centroids.shape[0] % 2 != 0:
        raise ValueError(f"Expected even node-by-coordinate centroid matrix, got {centroids.shape}.")
    half = centroids.shape[0] // 2
    output: list[np.ndarray] = []
    for hemi_centroids in (centroids[:half], centroids[half:]):
        diff = hemi_centroids[:, None, :] - hemi_centroids[None, :, :]
        dist = np.sqrt(np.sum(diff * diff, axis=2))
        np.fill_diagonal(dist, 0.0)
        output.append(dist.astype(float))
    return output[0], output[1]


def _load_dynamic_targets(repo_root: Path, expected_size: int = 100) -> dict[str, dict[str, Any]]:
    summary_path = repo_root / "results" / "parcellation_sensitivity" / SCHAEFER_ID / "summary.json"
    payload = _read_json(summary_path) or {}
    dmdc = payload.get("dmdc", {})
    if not isinstance(dmdc, dict):
        raise ValueError(f"Missing dmdc block in {summary_path}.")
    targets: dict[str, dict[str, Any]] = {}
    for target_id, label, key, transform in TARGET_VECTOR_KEYS:
        rows = dmdc.get(key)
        if not isinstance(rows, list):
            raise ValueError(f"Missing {key} in {summary_path}.")
        values = np.asarray([float(row["coefficient"]) for row in rows if isinstance(row, dict) and "coefficient" in row], dtype=float)
        if values.shape != (expected_size,):
            raise ValueError(f"Expected {expected_size} coefficients for {key}, found {values.size}.")
        if transform == "absolute":
            values = np.abs(values)
        targets[target_id] = {
            "target_id": target_id,
            "label": label,
            "source_key": key,
            "transform": transform,
            "values": values,
        }
    return targets


def _load_receptor_maps(repo_root: Path, expected_size: int = 100) -> dict[str, dict[str, Any]]:
    maps: dict[str, dict[str, Any]] = {}
    vectors: list[np.ndarray] = []
    for item in PET_RECEPTOR_MAPS:
        path = repo_root / item["path"]
        vector = _load_numeric_vector(path, expected_size=expected_size)
        vectors.append(vector)
        maps[str(item["map_id"])] = {
            "map_id": item["map_id"],
            "family": item["family"],
            "label": item["label"],
            "source_path": item["path"].as_posix(),
            "values": vector,
        }
    if vectors:
        maps["5ht2a_hansen_scale100_mean"] = {
            "map_id": "5ht2a_hansen_scale100_mean",
            "family": "receptor",
            "label": "Mean Hansen 5-HT2A PET prior, Schaefer100",
            "source_path": "mean_of_hansen_5ht2a_scale100_pet_csvs",
            "values": np.vstack(vectors).mean(axis=0),
        }
    return maps


def _pearson_r(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 3:
        return float("nan")
    x = np.asarray(x[mask], dtype=float)
    y = np.asarray(y[mask], dtype=float)
    if np.isclose(np.std(x), 0.0) or np.isclose(np.std(y), 0.0):
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _fisher_ci(r: float, n: int, alpha: float = 0.05) -> tuple[float | None, float | None]:
    if not math.isfinite(r) or n <= 3:
        return None, None
    clipped = max(min(float(r), 0.999999), -0.999999)
    z = math.atanh(clipped)
    se = 1.0 / math.sqrt(n - 3)
    zcrit = 1.959963984540054
    if not math.isclose(alpha, 0.05):
        zcrit = 1.959963984540054
    return math.tanh(z - zcrit * se), math.tanh(z + zcrit * se)


def _spatial_p_value(observed_r: float, null_rs: np.ndarray) -> float:
    null_rs = np.asarray(null_rs, dtype=float)
    null_rs = null_rs[np.isfinite(null_rs)]
    if not math.isfinite(observed_r) or null_rs.size == 0:
        return float("nan")
    exceed = int(np.sum(np.abs(null_rs) >= abs(observed_r)))
    return float((exceed + 1) / (null_rs.size + 1))


def _benjamini_hochberg(p_values: list[float]) -> list[float]:
    q_values = [float("nan")] * len(p_values)
    valid = [(idx, float(p)) for idx, p in enumerate(p_values) if math.isfinite(float(p))]
    if not valid:
        return q_values
    ordered = sorted(valid, key=lambda item: item[1])
    m = len(ordered)
    running = 1.0
    for rank_from_end, (idx, p_value) in enumerate(reversed(ordered), start=1):
        rank = m - rank_from_end + 1
        running = min(running, p_value * m / rank)
        q_values[idx] = float(min(running, 1.0))
    return q_values


def _run_receptor_moran_nulls(repo_root: Path) -> dict[str, Any]:
    from neuromaps import nulls

    expected_size = 100
    atlas_path = _load_schaefer_atlas_path(repo_root)
    centroids = _schaefer_centroids(atlas_path, expected_size=expected_size)
    dist_lh, dist_rh = _hemisphere_distance_matrices(centroids)
    receptor_maps = _load_receptor_maps(repo_root, expected_size=expected_size)
    dynamic_targets = _load_dynamic_targets(repo_root, expected_size=expected_size)

    rows: list[dict[str, Any]] = []
    for map_id, map_payload in receptor_maps.items():
        prior = np.asarray(map_payload["values"], dtype=float)
        surrogates = np.asarray(
            nulls.moran(prior, distmat=(dist_lh.copy(), dist_rh.copy()), n_perm=DEFAULT_N_PERM, seed=DEFAULT_SEED),
            dtype=float,
        )
        if surrogates.shape != (expected_size, DEFAULT_N_PERM):
            raise ValueError(f"Expected Moran surrogates with shape {(expected_size, DEFAULT_N_PERM)}, got {surrogates.shape}.")
        for target_id, target_payload in dynamic_targets.items():
            target = np.asarray(target_payload["values"], dtype=float)
            observed_r = _pearson_r(prior, target)
            null_rs = np.asarray([_pearson_r(surrogates[:, idx], target) for idx in range(surrogates.shape[1])], dtype=float)
            p_spatial = _spatial_p_value(observed_r, null_rs)
            ci_low, ci_high = _fisher_ci(observed_r, expected_size)
            rows.append(
                {
                    "map_id": map_id,
                    "map_label": map_payload["label"],
                    "map_family": map_payload["family"],
                    "target_id": target_id,
                    "target_label": target_payload["label"],
                    "target_transform": target_payload["transform"],
                    "source_path": map_payload["source_path"],
                    "n_nodes": expected_size,
                    "n_perm": DEFAULT_N_PERM,
                    "null_family": "neuromaps.nulls.moran",
                    "distance_space": "Schaefer100 parcel-centroid Euclidean distances split by hemisphere",
                    "r": observed_r,
                    "spatial_p": p_spatial,
                    "ci95_low": ci_low,
                    "ci95_high": ci_high,
                    "ci_crosses_zero": bool(ci_low is None or ci_high is None or ci_low <= 0.0 <= ci_high),
                }
            )

    q_values = _benjamini_hochberg([float(row["spatial_p"]) for row in rows])
    for row, q_value in zip(rows, q_values, strict=True):
        row["q"] = q_value
        row["fdr_pass"] = bool(math.isfinite(q_value) and q_value <= 0.05)
        row["claim_status"] = (
            "exploratory_receptor_prior_supported_by_moran_null"
            if row["fdr_pass"] and row["ci_crosses_zero"] is False
            else "not_supported_yet"
        )
    best = min(rows, key=lambda row: float(row["q"]) if math.isfinite(float(row["q"])) else float("inf")) if rows else None
    return {
        "method": "receptor_only_schaefer100_neuromaps_moran",
        "parcellation_id": SCHAEFER_ID,
        "atlas_path": _rel(atlas_path, repo_root) if atlas_path.is_relative_to(repo_root) else str(atlas_path),
        "n_nodes": expected_size,
        "n_perm": DEFAULT_N_PERM,
        "seed": DEFAULT_SEED,
        "map_count": len(receptor_maps),
        "target_count": len(dynamic_targets),
        "test_count": len(rows),
        "results": rows,
        "best_result": best,
        "fdr_supported_count": sum(1 for row in rows if row["fdr_pass"] and row["ci_crosses_zero"] is False),
        "family_coverage": {
            "receptor": True,
            "myelin": False,
            "functional_gradient": False,
            "gene_expression": False,
        },
        "limitations": [
            "This is a Schaefer100 parcellated Moran null, not a surface-level spin/permutation null.",
            "Only Hansen 5-HT2A PET receptor priors are tested here; myelin, gradient, and gene-expression maps remain missing.",
            "The receptor/myelin/gradient mechanism claim is not promoted unless the broader family coverage and FDR gates pass.",
        ],
    }


def build_neuromaps_spatial_null_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    cortical_path = repo_root / "results" / "cortical_maps" / "cortical_map_alignment_status.json"
    cortical_payload = _read_json(cortical_path) or {}
    inputs = _candidate_inputs(repo_root)
    runtime = _neuromaps_runtime()
    dependency_available = bool(runtime["dependency_available"])
    null_api_importable = bool(runtime["null_api_importable"])
    has_surface_manifest = bool(inputs["surface_manifest_exists"])
    has_high_resolution_summary = bool(inputs["schaefer_100_yeo_7_summary_exists"])
    has_mechanism_summary = bool(inputs["schaefer_100_yeo_7_mechanism_summary_exists"])
    has_hansen_pet = bool(inputs["hansen_5ht2a_pet_scale100_csvs_present"])
    receptor_nulls: dict[str, Any] | None = None
    execution_error: str | None = None

    if not dependency_available:
        status = "blocked_missing_neuromaps_dependency"
        blocker = "The optional neuromaps package is not installed in the current environment."
    elif not null_api_importable:
        status = "blocked_neuromaps_null_api_not_importable"
        blocker = f"neuromaps is installed, but its null-model API cannot import: {runtime['runtime_error']}"
    elif not has_surface_manifest and not has_high_resolution_summary:
        status = "blocked_missing_surface_or_high_resolution_map_inputs"
        blocker = "No surface/parcellated map manifest or completed Schaefer/Yeo empirical layer exists for spatial nulls."
    elif has_high_resolution_summary and has_mechanism_summary and has_hansen_pet:
        try:
            receptor_nulls = _run_receptor_moran_nulls(repo_root)
            status = "implemented_partial_receptor_schaefer100_moran_spatial_nulls"
            blocker = (
                "Receptor-only Schaefer100 Moran spatial nulls are executed. Full completion still needs myelin, "
                "functional-gradient, gene-expression, and preferably surface-level null coverage."
            )
        except Exception as exc:
            status = "blocked_receptor_moran_null_execution_failed"
            execution_error = f"{type(exc).__name__}: {exc}"
            blocker = f"Receptor-only Moran spatial null execution failed: {execution_error}"
    elif not has_surface_manifest:
        status = "blocked_missing_neuromaps_surface_input_manifest"
        blocker = "High-resolution outputs exist, but there is no neuromaps surface/input manifest describing map space and null family."
    else:
        status = "ready_to_run_neuromaps_spatial_nulls_not_executed"
        blocker = "Inputs are present, but this artifact has not yet recorded completed spatial-autocorrelation null results."

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": status,
        "spatial_autocorrelation_nulls_complete": False,
        "partial_spatial_autocorrelation_nulls_complete": receptor_nulls is not None,
        "receptor_spatial_nulls_complete": receptor_nulls is not None,
        "dependency_available": dependency_available,
        "null_api_importable": null_api_importable,
        "neuromaps_runtime": runtime,
        "execution_error": execution_error,
        "candidate_inputs": inputs,
        "receptor_moran_nulls": receptor_nulls,
        "module_level_alignment_status": cortical_payload.get("analysis_status", "missing_module_level_alignment"),
        "current_module_statistic": (
            cortical_payload.get("alignment_rows", [{}])[0].get("method", "not_run")
            if isinstance(cortical_payload.get("alignment_rows"), list) and cortical_payload.get("alignment_rows")
            else "not_run"
        ),
        "required_execution_contract": {
            "map_space": "surface or high-resolution Schaefer/Yeo parcellation, not only 8 macro modules",
            "null_family": "neuromaps spatial-autocorrelation preserving nulls appropriate to the map space",
            "correction": "FDR across receptor, myelin, gradient, and transcriptomic map families",
            "reported_gates": ["r", "p", "q", "FDR pass", "CI overlap with zero", "claim status"],
            "available_null_families": runtime["available_null_families"],
        },
        "blocker": blocker,
        "claim_status": (
            "partial_receptor_spatial_nulls_executed_claim_not_promoted"
            if receptor_nulls is not None
            else "not_implemented_full_neuromaps_spatial_nulls"
        ),
        "claim_guardrail": "The current exact 8-module permutation test is not a substitute for neuromaps spatial-autocorrelation null testing.",
    }


def _markdown(status: dict[str, Any]) -> str:
    inputs = status["candidate_inputs"]
    return "\n".join(
        [
            "# Neuromaps Spatial Null Status",
            "",
            status["claim_guardrail"],
            "",
            f"- Status: `{status['analysis_status']}`",
            f"- neuromaps dependency available: `{str(status['dependency_available']).lower()}`",
            f"- neuromaps null API importable: `{str(status['null_api_importable']).lower()}`",
            f"- neuromaps version: `{status['neuromaps_runtime']['version']}`",
            f"- Spatial nulls complete: `{str(status['spatial_autocorrelation_nulls_complete']).lower()}`",
            f"- Current module statistic: `{status['current_module_statistic']}`",
            f"- Blocker: {status['blocker']}",
            "",
            "## Partial receptor Moran nulls",
            "",
            f"- Receptor spatial nulls complete: `{str(status['receptor_spatial_nulls_complete']).lower()}`",
            f"- Partial spatial nulls complete: `{str(status['partial_spatial_autocorrelation_nulls_complete']).lower()}`",
            f"- Execution error: `{status['execution_error']}`",
            "",
            "## Candidate inputs",
            "",
            f"- Surface manifest: `{inputs['surface_manifest']}` exists=`{str(inputs['surface_manifest_exists']).lower()}`",
            f"- Schaefer 100/Yeo 7 summary: `{inputs['schaefer_100_yeo_7_summary']}` exists=`{str(inputs['schaefer_100_yeo_7_summary_exists']).lower()}`",
            f"- Module-level alignment: `{inputs['module_level_alignment_status']}` exists=`{str(inputs['module_level_alignment_status_exists']).lower()}`",
            "",
            "## Required execution contract",
            "",
            "- Use surface or high-resolution Schaefer/Yeo map space.",
            "- Use a neuromaps spatial-autocorrelation preserving null family appropriate to that space.",
            "- Report r, p, q, FDR pass, CI overlap with zero, and claim status.",
            "",
        ]
    )


def write_neuromaps_spatial_null_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "cortical_maps"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_neuromaps_spatial_null_status(repo_root)
    status_path = output_dir / "neuromaps_spatial_null_status.json"
    report_path = output_dir / "neuromaps_spatial_null_status.md"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    return status
