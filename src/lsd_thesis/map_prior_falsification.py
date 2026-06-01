from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "map_prior_falsification.v1"
MAP_FAMILIES = ("receptor", "myelin", "functional_gradient", "gene_expression")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(raw).__name__}.")
    return raw


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _best_module_alignment(cortical: dict[str, Any]) -> dict[str, Any] | None:
    best = cortical.get("best_alignment")
    return best if isinstance(best, dict) else None


def _map_family_payload(neuromaps: dict[str, Any]) -> dict[str, Any]:
    payload = neuromaps.get("map_family_moran_nulls")
    if isinstance(payload, dict):
        return payload
    payload = neuromaps.get("receptor_moran_nulls")
    return payload if isinstance(payload, dict) else {}


def _family_coverage(map_family: dict[str, Any]) -> dict[str, bool]:
    coverage = map_family.get("family_coverage")
    if not isinstance(coverage, dict):
        return {family: False for family in MAP_FAMILIES}
    return {family: bool(coverage.get(family)) for family in MAP_FAMILIES}


def _best_spatial_result(map_family: dict[str, Any]) -> dict[str, Any] | None:
    best = map_family.get("best_result")
    return best if isinstance(best, dict) else None


def _ranked_spatial_rows(map_family: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    rows = map_family.get("results", [])
    if not isinstance(rows, list):
        return []
    clean = [row for row in rows if isinstance(row, dict)]
    clean.sort(key=lambda row: float(row.get("q", 1.0) if row.get("q") is not None else 1.0))
    return clean[:limit]


def _spatial_resolution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    joint_support = [row for row in rows if bool(row.get("fdr_pass")) and not bool(row.get("ci_crosses_zero", True))]
    fdr_only = [row for row in rows if bool(row.get("fdr_pass"))]
    ci_only = [row for row in rows if not bool(row.get("ci_crosses_zero", True))]
    ranked_by_abs_effect = sorted(
        rows,
        key=lambda row: abs(float(row.get("r", 0.0) if row.get("r") is not None else 0.0)),
        reverse=True,
    )
    status = "supported_map_prior_claim" if joint_support else "resolved_negative_not_promoted"
    return {
        "claim_resolution_status": status,
        "joint_fdr_and_ci_support_count": len(joint_support),
        "fdr_only_support_count": len(fdr_only),
        "ci_excludes_zero_without_fdr_count": len([row for row in ci_only if not bool(row.get("fdr_pass"))]),
        "top_abs_effect_rows": ranked_by_abs_effect[:6],
        "support_rule": "promote only if fdr_pass is true and ci_crosses_zero is false for at least one spatial-null family row",
    }


def build_map_prior_falsification_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    cortical_path = repo_root / "results" / "cortical_maps" / "cortical_map_alignment_status.json"
    neuromaps_path = repo_root / "results" / "cortical_maps" / "neuromaps_spatial_null_status.json"
    cortical = _read_json(cortical_path) or {}
    neuromaps = _read_json(neuromaps_path) or {}
    map_family = _map_family_payload(neuromaps)
    coverage = _family_coverage(map_family)
    module_fdr_count = int(cortical.get("fdr_supported_count") or 0)
    spatial_fdr_count = int(map_family.get("fdr_supported_count") or 0)
    spatial_complete = bool(neuromaps.get("spatial_autocorrelation_nulls_complete"))
    family_complete = all(coverage.values())
    best_module = _best_module_alignment(cortical)
    best_spatial = _best_spatial_result(map_family)
    spatial_rows = [row for row in map_family.get("results", []) if isinstance(row, dict)] if isinstance(map_family.get("results"), list) else []
    spatial_resolution = _spatial_resolution(spatial_rows)
    best_spatial_fdr_pass = bool(best_spatial.get("fdr_pass", False)) if best_spatial else False
    negative_result_ready = bool(
        spatial_complete
        and family_complete
        and module_fdr_count == 0
        and spatial_fdr_count == 0
        and not best_spatial_fdr_pass
        and spatial_resolution["joint_fdr_and_ci_support_count"] == 0
    )
    claim_resolution_status = (
        "supported_map_prior_claim" if spatial_resolution["joint_fdr_and_ci_support_count"] > 0 else "resolved_negative_not_promoted"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": "implemented_map_prior_claim_resolution" if negative_result_ready else "blocked_or_incomplete_map_prior_falsification",
        "negative_result_ready": negative_result_ready,
        "source_paths": {
            "module_alignment": _rel(cortical_path, repo_root),
            "spatial_nulls": _rel(neuromaps_path, repo_root),
        },
        "module_level": {
            "analysis_status": cortical.get("analysis_status"),
            "fdr_supported_count": module_fdr_count,
            "best_alignment": best_module,
            "claim_readiness": cortical.get("claim_readiness"),
        },
        "spatial_nulls": {
            "analysis_status": neuromaps.get("analysis_status"),
            "spatial_autocorrelation_nulls_complete": spatial_complete,
            "family_coverage": coverage,
            "fdr_supported_count": spatial_fdr_count,
            "best_result": best_spatial,
            "ranked_rows": _ranked_spatial_rows(map_family),
        },
        "claim_status": claim_resolution_status if negative_result_ready else "not_supported_yet",
        "claim_resolution": {
            **spatial_resolution,
            "module_fdr_supported_count": module_fdr_count,
            "spatial_fdr_supported_count": spatial_fdr_count,
            "family_coverage_complete": family_complete,
            "spatial_autocorrelation_nulls_complete": spatial_complete,
            "strict_gate_resolved": negative_result_ready,
        },
        "claim_effect": (
            "The receptor/myelin/gradient/gene-expression map-prior mechanism is formally downgraded: "
            "module-level permutation and Schaefer100 Moran spatial-null families contain no row with joint FDR support "
            "and a confidence interval excluding zero."
            if negative_result_ready
            else "Map-prior falsification is not complete until module and spatial-null evidence are both available."
        ),
        "presentation_rule": (
            "Present this as a negative/control result. It strengthens thesis credibility by showing that weak "
            "receptor/myelin/gradient priors do not carry the macro-dynamics claim."
        ),
        "limitations": [
            "This does not prove receptor, myelin, gradient, or gene-expression maps are irrelevant biologically.",
            "It only says the current dataset, targets, parcellation, and null family do not support promoting that mechanism claim.",
            "A future external dataset or different validated target could change this status.",
        ],
        "claim_guardrail": "Do not promote receptor/myelin/gradient mechanism claims from these map-prior results.",
    }


def _markdown(status: dict[str, Any]) -> str:
    spatial = status["spatial_nulls"]
    best = spatial.get("best_result") or {}
    resolution = status.get("claim_resolution", {})
    lines = [
        "# Map-Prior Falsification Status",
        "",
        status["claim_guardrail"],
        "",
        f"- Status: `{status['analysis_status']}`",
        f"- Claim status: `{status['claim_status']}`",
        f"- Negative result ready: `{str(status['negative_result_ready']).lower()}`",
        f"- Joint FDR + CI support count: `{resolution.get('joint_fdr_and_ci_support_count')}`",
        f"- CI-only rows without FDR: `{resolution.get('ci_excludes_zero_without_fdr_count')}`",
        f"- Module-level FDR-supported count: `{status['module_level']['fdr_supported_count']}`",
        f"- Spatial-null FDR-supported count: `{spatial['fdr_supported_count']}`",
        f"- Best spatial-null q: `{best.get('q')}`",
        f"- Best spatial-null CI crosses zero: `{best.get('ci_crosses_zero')}`",
        "",
        "## Claim effect",
        "",
        status["claim_effect"],
        "",
        "## Presentation rule",
        "",
        status["presentation_rule"],
        "",
    ]
    return "\n".join(lines)


def write_map_prior_falsification_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "cortical_maps"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_map_prior_falsification_status(repo_root)
    status_path = output_dir / "map_prior_falsification_status.json"
    report_path = output_dir / "map_prior_falsification_status.md"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    return status
