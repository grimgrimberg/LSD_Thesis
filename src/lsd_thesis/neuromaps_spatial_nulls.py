from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "neuromaps_spatial_null_status.v1"


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
    return {
        "surface_manifest": _rel(surface_manifest, repo_root),
        "surface_manifest_exists": surface_manifest.exists(),
        "schaefer_100_yeo_7_summary": _rel(schaefer_summary, repo_root),
        "schaefer_100_yeo_7_summary_exists": schaefer_summary.exists(),
        "module_level_alignment_status": _rel(cortical_alignment, repo_root),
        "module_level_alignment_status_exists": cortical_alignment.exists(),
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

    if not dependency_available:
        status = "blocked_missing_neuromaps_dependency"
        blocker = "The optional neuromaps package is not installed in the current environment."
    elif not null_api_importable:
        status = "blocked_neuromaps_null_api_not_importable"
        blocker = f"neuromaps is installed, but its null-model API cannot import: {runtime['runtime_error']}"
    elif not has_surface_manifest and not has_high_resolution_summary:
        status = "blocked_missing_surface_or_high_resolution_map_inputs"
        blocker = "No surface/parcellated map manifest or completed Schaefer/Yeo empirical layer exists for spatial nulls."
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
        "dependency_available": dependency_available,
        "null_api_importable": null_api_importable,
        "neuromaps_runtime": runtime,
        "candidate_inputs": inputs,
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
        "claim_status": "not_implemented_full_neuromaps_spatial_nulls",
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
