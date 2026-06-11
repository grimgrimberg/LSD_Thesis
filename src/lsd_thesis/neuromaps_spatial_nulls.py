from __future__ import annotations

import importlib.util
import json
import math
import os
import shutil
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import nibabel as nib
import numpy as np

# neuromaps 0.0.x still touches pkg_resources through dependency runtime paths.
# The project pins setuptools below the removal boundary; this filter keeps
# Pages builds clean without muting unrelated deprecation warnings.
warnings.filterwarnings(
    "ignore",
    message=r"pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "neuromaps_spatial_null_status.v1"
SCHAEFER_ID = "schaefer_100_yeo_7"
DEFAULT_N_PERM = 999
DEFAULT_SEED = 20260528
PET_RECEPTOR_MAPS: tuple[dict[str, Any], ...] = (
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
PUBLIC_SURFACE_ANNOTATION_MAPS: tuple[dict[str, Any], ...] = (
    {
        "map_id": "hcp1200_myelinmap",
        "family": "myelin",
        "label": "HCP S1200 myelin map, Schaefer100 via fsLR32k",
        "source": "hcps1200",
        "desc": "myelinmap",
        "space": "fsLR",
        "den": "32k",
    },
    {
        "map_id": "margulies2016_fcgradient01",
        "family": "functional_gradient",
        "label": "Margulies 2016 principal functional gradient, Schaefer100 via fsLR32k",
        "source": "margulies2016",
        "desc": "fcgradient01",
        "space": "fsLR",
        "den": "32k",
    },
    {
        "map_id": "abagen_genepc1",
        "family": "gene_expression",
        "label": "Abagen AHBA gene-expression PC1, Schaefer100 via fsaverage10k",
        "source": "abagen",
        "desc": "genepc1",
        "space": "fsaverage",
        "den": "10k",
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
    annotation_dir = repo_root / "results" / "cortical_maps" / "neuromaps_annotations"
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
        "public_fslr_annotation_cache": _rel(repo_root / ".neuromaps-data", repo_root),
        "public_fslr_annotation_cache_exists": (repo_root / ".neuromaps-data").exists(),
        "derived_neuromaps_annotation_dir": _rel(annotation_dir, repo_root),
        "derived_neuromaps_annotation_dir_exists": annotation_dir.exists(),
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
    image = cast(nib.Nifti1Image, nib.load(str(atlas_path)))
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


def _neuromaps_data_dir(repo_root: Path) -> Path:
    raw = os.environ.get("NEUROMAPS_DATA")
    path = Path(raw) if raw else repo_root / ".neuromaps-data"
    path.mkdir(parents=True, exist_ok=True)
    os.environ["NEUROMAPS_DATA"] = str(path.resolve())
    return path


def _public_annotation_record(source: str, desc: str, space: str, den: str, hemi: str) -> dict[str, Any]:
    from neuromaps.datasets.annotations import get_dataset_info

    matches = [
        item
        for item in get_dataset_info("annotations", return_restricted=False)
        if item.get("source") == source
        and item.get("desc") == desc
        and item.get("space") == space
        and item.get("den") == den
        and item.get("hemi") == hemi
    ]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one public {space}{den} annotation for {source}/{desc}/{hemi}, found {len(matches)}.")
    return cast(dict[str, Any], matches[0])


def _fetch_public_surface_annotation_pair(
    repo_root: Path,
    source: str,
    desc: str,
    space: str,
    den: str,
) -> tuple[tuple[Path, Path], list[dict[str, Any]]]:
    from neuromaps.datasets.annotations import _fetch_file

    data_dir = _neuromaps_data_dir(repo_root)
    paths: list[Path] = []
    provenance: list[dict[str, Any]] = []
    for hemi in ("L", "R"):
        record = _public_annotation_record(source, desc, space, den, hemi)
        path = data_dir / "annotations" / str(record["rel_path"]) / str(record["fname"])
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            downloaded = _fetch_file(record["url"], path.parent, verbose=0, md5sum=record["checksum"])
            shutil.move(str(downloaded), path)
        paths.append(path)
        provenance.append(
            {
                "source": source,
                "desc": desc,
                "hemi": hemi,
                "space": record.get("space"),
                "den": record.get("den"),
                "format": record.get("format"),
                "tags": record.get("tags", []),
                "checksum": record.get("checksum"),
                "url": record.get("url"),
                "cache_path": _rel(path, repo_root) if path.is_relative_to(repo_root) else str(path),
            }
        )
    return (paths[0], paths[1]), provenance


def _schaefer_surface_parcellation_paths(repo_root: Path, atlas_path: Path, space: str, den: str) -> tuple[Path, Path]:
    from neuromaps import transforms

    output_dir = repo_root / "results" / "cortical_maps" / "neuromaps_annotations"
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = (
        output_dir / f"schaefer100_from_mni_space-{space}_den-{den}_hemi-L_label.gii",
        output_dir / f"schaefer100_from_mni_space-{space}_den-{den}_hemi-R_label.gii",
    )
    if all(path.exists() for path in paths):
        return paths
    _neuromaps_data_dir(repo_root)
    if space == "fsLR":
        projected = transforms.mni152_to_fslr(str(atlas_path), den, method="nearest")
    elif space == "fsaverage":
        projected = transforms.mni152_to_fsaverage(str(atlas_path), den, method="nearest")
    else:
        raise ValueError(f"Unsupported surface annotation space: {space}")
    for path, image in zip(paths, projected, strict=True):
        nib.save(image, path)
    return paths


def _write_parcellated_vector_csv(path: Path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(",".join(f"{float(value):.10g}" for value in values.tolist()) + "\n", encoding="utf-8")


def _load_public_annotation_maps(repo_root: Path, atlas_path: Path, expected_size: int = 100) -> dict[str, dict[str, Any]]:
    from neuromaps.images import load_data
    from neuromaps.parcellate import vertices_to_parcels

    output_dir = repo_root / "results" / "cortical_maps" / "neuromaps_annotations"
    maps: dict[str, dict[str, Any]] = {}
    for item in PUBLIC_SURFACE_ANNOTATION_MAPS:
        space = str(item["space"])
        den = str(item["den"])
        parcellation_paths = _schaefer_surface_parcellation_paths(repo_root, atlas_path, space, den)
        annotation_paths, provenance = _fetch_public_surface_annotation_pair(repo_root, str(item["source"]), str(item["desc"]), space, den)
        vertex_data = load_data(tuple(str(path) for path in annotation_paths))
        vector = np.asarray(vertices_to_parcels(vertex_data, tuple(str(path) for path in parcellation_paths), background=0), dtype=float).squeeze()
        if vector.shape != (expected_size,):
            raise ValueError(f"Expected {expected_size} values for {item['map_id']}, found {vector.shape}.")
        if int(np.isfinite(vector).sum()) != expected_size:
            raise ValueError(f"Public annotation {item['map_id']} has missing Schaefer100 parcel values.")
        vector_path = output_dir / f"{item['map_id']}_schaefer100.csv"
        _write_parcellated_vector_csv(vector_path, vector)
        maps[str(item["map_id"])] = {
            "map_id": item["map_id"],
            "family": item["family"],
            "label": item["label"],
            "source_path": _rel(vector_path, repo_root),
            "values": vector,
            "source_provenance": provenance,
            "parcellation_surface_paths": [_rel(path, repo_root) for path in parcellation_paths],
        }
    manifest = {
        "schema_version": "neuromaps_public_annotations.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "parcellation_id": SCHAEFER_ID,
        "map_space": "Surface annotations parcellated through Schaefer100 labels projected from MNI152 to each annotation surface space.",
        "maps": [
            {
                "map_id": payload["map_id"],
                "family": payload["family"],
                "label": payload["label"],
                "source_path": payload["source_path"],
                "source_provenance": payload["source_provenance"],
            }
            for payload in maps.values()
        ],
        "claim_guardrail": "These are public atlas priors parcellated to Schaefer100. They are spatial priors, not drug-effect measurements.",
    }
    (output_dir / "public_annotation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
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


def _run_map_family_moran_nulls(repo_root: Path) -> dict[str, Any]:
    from neuromaps import nulls

    expected_size = 100
    atlas_path = _load_schaefer_atlas_path(repo_root)
    centroids = _schaefer_centroids(atlas_path, expected_size=expected_size)
    dist_lh, dist_rh = _hemisphere_distance_matrices(centroids)
    brain_maps: dict[str, dict[str, Any]] = {}
    brain_maps.update(_load_receptor_maps(repo_root, expected_size=expected_size))
    brain_maps.update(_load_public_annotation_maps(repo_root, atlas_path, expected_size=expected_size))
    dynamic_targets = _load_dynamic_targets(repo_root, expected_size=expected_size)

    rows: list[dict[str, Any]] = []
    for map_id, map_payload in brain_maps.items():
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
    family_coverage = {
        "receptor": any(row["map_family"] == "receptor" for row in rows),
        "myelin": any(row["map_family"] == "myelin" for row in rows),
        "functional_gradient": any(row["map_family"] == "functional_gradient" for row in rows),
        "gene_expression": any(row["map_family"] == "gene_expression" for row in rows),
    }
    complete_family_coverage = bool(
        family_coverage["receptor"]
        and family_coverage["myelin"]
        and family_coverage["functional_gradient"]
        and family_coverage["gene_expression"]
    )
    return {
        "method": "schaefer100_neuromaps_moran_public_map_families",
        "parcellation_id": SCHAEFER_ID,
        "atlas_path": _rel(atlas_path, repo_root) if atlas_path.is_relative_to(repo_root) else str(atlas_path),
        "map_inputs": [
            {
                "map_id": payload["map_id"],
                "family": payload["family"],
                "label": payload["label"],
                "source_path": payload["source_path"],
                "source_provenance": payload.get("source_provenance", []),
                "parcellation_surface_paths": payload.get("parcellation_surface_paths", []),
            }
            for payload in brain_maps.values()
        ],
        "n_nodes": expected_size,
        "n_perm": DEFAULT_N_PERM,
        "seed": DEFAULT_SEED,
        "map_count": len(brain_maps),
        "target_count": len(dynamic_targets),
        "test_count": len(rows),
        "results": rows,
        "best_result": best,
        "fdr_supported_count": sum(1 for row in rows if row["fdr_pass"] and row["ci_crosses_zero"] is False),
        "family_coverage": family_coverage,
        "complete_map_family_coverage": complete_family_coverage,
        "complete_receptor_myelin_gradient_coverage": bool(
            family_coverage["receptor"] and family_coverage["myelin"] and family_coverage["functional_gradient"]
        ),
        "limitations": [
            "This is a Schaefer100 parcellated Moran null, not a surface-level spin/permutation null.",
            "Public surface priors are parcellated through Schaefer100 labels projected from MNI152 to each source surface space.",
            "The receptor/myelin/gradient mechanism claim is not promoted unless FDR and CI gates pass.",
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
    map_family_nulls: dict[str, Any] | None = None
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
            map_family_nulls = _run_map_family_moran_nulls(repo_root)
            status = (
                "implemented_schaefer100_full_map_family_moran_spatial_nulls"
                if map_family_nulls.get("complete_map_family_coverage")
                else "implemented_schaefer100_receptor_myelin_gradient_moran_spatial_nulls"
            )
            blocker = (
                "Schaefer100 Moran spatial nulls cover receptor, myelin, functional-gradient, and gene-expression priors. "
                "Surface-level spin/null extensions remain a stricter future sensitivity analysis."
                if map_family_nulls.get("complete_map_family_coverage")
                else "Schaefer100 Moran spatial nulls now cover receptor, myelin, and functional-gradient priors. "
                "Full completion still needs gene-expression and preferably surface-level null coverage."
            )
        except Exception as exc:
            status = "blocked_map_family_moran_null_execution_failed"
            execution_error = f"{type(exc).__name__}: {exc}"
            blocker = f"Map-family Moran spatial null execution failed: {execution_error}"
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
        "spatial_autocorrelation_nulls_complete": bool(map_family_nulls and map_family_nulls.get("complete_map_family_coverage")),
        "partial_spatial_autocorrelation_nulls_complete": map_family_nulls is not None,
        "receptor_spatial_nulls_complete": bool(map_family_nulls and map_family_nulls["family_coverage"].get("receptor")),
        "myelin_spatial_nulls_complete": bool(map_family_nulls and map_family_nulls["family_coverage"].get("myelin")),
        "functional_gradient_spatial_nulls_complete": bool(map_family_nulls and map_family_nulls["family_coverage"].get("functional_gradient")),
        "gene_expression_spatial_nulls_complete": bool(map_family_nulls and map_family_nulls["family_coverage"].get("gene_expression")),
        "dependency_available": dependency_available,
        "null_api_importable": null_api_importable,
        "neuromaps_runtime": runtime,
        "execution_error": execution_error,
        "candidate_inputs": inputs,
        "receptor_moran_nulls": map_family_nulls,
        "map_family_moran_nulls": map_family_nulls,
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
            "receptor_myelin_gradient_spatial_nulls_executed_claim_not_promoted"
            if map_family_nulls is not None
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
            "## Map-family Moran nulls",
            "",
            f"- Receptor spatial nulls complete: `{str(status['receptor_spatial_nulls_complete']).lower()}`",
            f"- Myelin spatial nulls complete: `{str(status['myelin_spatial_nulls_complete']).lower()}`",
            f"- Functional-gradient spatial nulls complete: `{str(status['functional_gradient_spatial_nulls_complete']).lower()}`",
            f"- Gene-expression spatial nulls complete: `{str(status['gene_expression_spatial_nulls_complete']).lower()}`",
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
