from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[3]

CLAIM_STATUS_BY_FAMILY = {
    "ising_temperature_and_algorithmic_complexity": "future",
    "entropy_copbet": "future",
    "energy_landscape_network_control": "mixed",
    "react_receptor_connectivity": "blocked",
    "neuroreceptor_eigenmodes": "blocked",
    "dynamic_integration_segregation": "proxy-supported",
    "cortical_gradients_brainspace": "proxy-supported",
    "lsd_music_brainstates": "blocked",
    "gnw_iit_consciousness": "future",
    "mesoscale_reho": "future",
    "traveling_waves": "future",
    "dlpfc_granger_causality": "future",
    "translational_neuromodeling_teaching": "future",
}

CONNECTION_BY_FAMILY = {
    "ising_temperature_and_algorithmic_complexity": "Entropy/temperature ideas are benchmark inspiration only unless independently implemented and tested.",
    "entropy_copbet": "Toolbox ergonomics can inform reproducibility demos, but no wrapped analysis is promoted as original evidence.",
    "energy_landscape_network_control": "Network-control language maps to model-level transition-energy proxies, not receptor-level proof.",
    "react_receptor_connectivity": "Receptor-enriched connectivity remains a biological-prior target behind spatial-null and external-data gates.",
    "neuroreceptor_eigenmodes": "Receptor maps are prior layers and require null controls before claim promotion.",
    "dynamic_integration_segregation": "Integration/segregation metrics align with the macro-dynamics surrogate evidence layer.",
    "cortical_gradients_brainspace": "Gradient methods inform map-prior sensitivity, not completed external validation.",
    "lsd_music_brainstates": "Run-02/music analyses stay blocked for primary claims until motion/context controls pass.",
    "gnw_iit_consciousness": "Consciousness-theory archives are context only; this repo does not settle GNW/IIT claims.",
    "mesoscale_reho": "Regional-homogeneity analyses are future sensitivity checks.",
    "traveling_waves": "Traveling-wave framing is future work unless a dedicated local implementation exists.",
    "dlpfc_granger_causality": "Causality analysis is future validation context, not part of the current evidence package.",
    "translational_neuromodeling_teaching": "Teaching resources are secondary context and not thesis evidence.",
}


def _records(items: Any) -> list[dict[str, Any]]:
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    return raw if isinstance(raw, dict) else {}


def _runbook_families(repo_root: Path) -> list[str]:
    runbook_dir = repo_root / "prior_art" / "runbooks"
    if not runbook_dir.exists():
        return []
    return sorted(path.stem for path in runbook_dir.glob("*.md"))


def _input_status(repo_root: Path, input_roots: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, raw_info in input_roots.items():
        if not isinstance(raw_info, dict):
            continue
        relative_path = str(raw_info.get("relative_path") or "")
        if not relative_path:
            continue
        path = repo_root / relative_path
        rows.append(
            {
                "key": str(key),
                "label": str(raw_info.get("label") or key),
                "relative_path": relative_path,
                "exists": path.exists(),
                "status": "present" if path.exists() else "missing",
                "purpose": str(raw_info.get("purpose") or ""),
            }
        )
    return rows


def _comparison_rows(
    repo_root: Path,
    families: list[dict[str, Any]],
    family_counts: dict[str, int],
    claim_status_by_family: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    prior_root = repo_root / "prior_art"
    plan = _read_json(prior_root / "comparison_extraction_plan.json")
    input_roots = cast(dict[str, Any], plan.get("input_roots", {})) if isinstance(plan.get("input_roots"), dict) else {}
    input_rows = _input_status(repo_root, input_roots)
    input_by_key = {row["key"]: row for row in input_rows}

    rows: list[dict[str, Any]] = []
    for raw_family in _records(plan.get("families")):
        family = str(raw_family.get("family") or "")
        if not family:
            continue
        required_inputs = [str(item) for item in raw_family.get("required_inputs", []) if isinstance(item, str)]
        missing_inputs = [key for key in required_inputs if not input_by_key.get(key, {}).get("exists")]
        readiness = "ready_to_test" if not missing_inputs else "missing_inputs"
        extract_targets = [str(item) for item in raw_family.get("extract_targets", []) if isinstance(item, str)]
        rows.append(
            {
                "family": family,
                "label": str(raw_family.get("label") or family),
                "reproduction_rank": raw_family.get("reproduction_rank"),
                "reproducibility_score": str(raw_family.get("reproducibility_score") or "not ranked"),
                "source_count": family_counts.get(family, 0),
                "claim_status": claim_status_by_family.get(family, "future"),
                "required_inputs": required_inputs,
                "missing_inputs": missing_inputs,
                "readiness": readiness,
                "output_target": str(raw_family.get("output_target") or ""),
                "dry_run_command": str(raw_family.get("dry_run_command") or ""),
                "strict_command": str(raw_family.get("strict_command") or ""),
                "comparison_target": str(raw_family.get("comparison_target") or ""),
                "extract_targets": extract_targets,
                "extract_target_summary": "; ".join(extract_targets),
                "claim_boundary": str(raw_family.get("claim_boundary") or ""),
            }
        )

    return sorted(rows, key=lambda row: int(row["reproduction_rank"] or 999)), input_rows, str(plan.get("safety_policy") or "")


def build_prior_art_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    prior_root = repo_root / "prior_art"
    sources = _read_json(prior_root / "repository_sources.json")
    manifest = _read_json(prior_root / "repository_manifest.json")
    archive_manifest_path = prior_root / "archive_manifest.md"
    matrix_path = prior_root / "reproducibility_matrix.md"
    inventory_path = prior_root / "code_inventory.md"

    manifest_entries = cast(list[dict[str, Any]], manifest.get("entries", [])) if isinstance(manifest.get("entries"), list) else []
    source_entries = cast(list[dict[str, Any]], sources.get("repositories", [])) if isinstance(sources.get("repositories"), list) else []
    non_clone_sources = cast(list[dict[str, Any]], sources.get("non_clone_sources", [])) if isinstance(sources.get("non_clone_sources"), list) else []
    manifest_by_directory = {str(entry.get("directory")): entry for entry in manifest_entries}

    rows: list[dict[str, Any]] = []
    family_counts: dict[str, int] = defaultdict(int)
    for source in source_entries:
        directory = str(source.get("directory", ""))
        checked = manifest_by_directory.get(directory, {})
        family = str(source.get("family", "unknown"))
        family_counts[family] += 1
        rows.append(
            {
                "family": family,
                "name": str(source.get("name", directory or "repository")),
                "role": str(source.get("role", "")),
                "url": str(source.get("url", "")),
                "status": str(checked.get("status") or "not checked"),
                "directory": directory,
                "language": str(source.get("expected_language", "")),
                "ds003059_support": str(source.get("expected_ds003059_support", "")),
                "commit_or_policy": str(checked.get("checked_commit") or checked.get("error") or "not recorded"),
                "readme_file": checked.get("readme_file"),
                "license_file": checked.get("license_file"),
            }
        )
    for source in non_clone_sources:
        family = str(source.get("family", "unknown"))
        family_counts[family] += 1
        rows.append(
            {
                "family": family,
                "name": str(source.get("name", "non-clone source")),
                "role": str(source.get("role", "")),
                "url": str(source.get("url", "")),
                "status": "documented_non_clone_source",
                "directory": str(source.get("local_code_path") or ""),
                "language": "archive / documentation",
                "ds003059_support": str(source.get("clone_policy", "")),
                "commit_or_policy": str(source.get("clone_policy") or source.get("code_archive_md5") or "documented"),
                "readme_file": None,
                "license_file": None,
            }
        )

    runbook_families = _runbook_families(repo_root)
    family_names = sorted(set(runbook_families) | set(family_counts) | set(CLAIM_STATUS_BY_FAMILY))
    families = [
        {
            "family": family,
            "source_count": family_counts.get(family, 0),
            "runbook_path": f"prior_art/runbooks/{family}.md" if family in runbook_families else None,
            "claim_status": CLAIM_STATUS_BY_FAMILY.get(family, "future"),
            "connection": CONNECTION_BY_FAMILY.get(
                family,
                "Documented as prior-art context until local artifacts justify claim promotion.",
            ),
        }
        for family in family_names
    ]
    claim_status_by_family = {row["family"]: row["claim_status"] for row in families}
    comparison_rows, input_rows, safety_policy = _comparison_rows(repo_root, families, family_counts, claim_status_by_family)
    ready_rows = [row for row in comparison_rows if row["readiness"] == "ready_to_test"]

    return {
        "schema_version": "prior_art.dashboard_payload.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "dataset": sources.get("dataset", {"accession": "ds003059"}),
        "summary": {
            "family_count": len(families),
            "source_count": len(rows),
            "github_repository_count": len(source_entries),
            "non_clone_source_count": len(non_clone_sources),
            "checked_repository_count": sum(1 for row in rows if row["status"] == "existing"),
            "comparison_family_count": len(comparison_rows),
            "ready_comparison_family_count": len(ready_rows),
        },
        "families": families,
        "sources": sorted(rows, key=lambda row: (row["family"], row["name"].lower())),
        "input_status": input_rows,
        "comparison_plan": comparison_rows,
        "comparison_guardrail": safety_policy,
        "documents": [
            {"label": "Prior-art README", "href": "/artifacts/prior_art/README.md"},
            {"label": "Code inventory", "href": f"/artifacts/{inventory_path.relative_to(repo_root).as_posix()}"},
            {"label": "Reproducibility matrix", "href": f"/artifacts/{matrix_path.relative_to(repo_root).as_posix()}"},
            {"label": "Comparison/extraction plan", "href": "/artifacts/prior_art/comparison_extraction_plan.json"},
            {"label": "Archive manifest", "href": f"/artifacts/{archive_manifest_path.relative_to(repo_root).as_posix()}"},
        ],
        "claim_guardrail": (
            "Prior-art repositories are reproducibility context and inspiration. They are not copied into local analyses, "
            "and wrappers are not presented as original thesis evidence."
        ),
    }
