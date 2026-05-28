from __future__ import annotations

import csv
import itertools
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from lsd_thesis.core import MODULE_NAMES

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "external_cortical_maps.v1"

SOURCE_REFERENCES: list[dict[str, str]] = [
    {
        "id": "neuromaps",
        "label": "Markello et al. 2022 neuromaps",
        "url": "https://www.nature.com/articles/s41592-022-01625-w",
        "role": "Canonical framework for brain-map comparison and spatial-autocorrelation-aware nulls.",
    },
    {
        "id": "margulies_gradient",
        "label": "Margulies et al. 2016 principal functional gradient",
        "url": "https://pubmed.ncbi.nlm.nih.gov/27791099/",
        "role": "Canonical sensory-to-default-mode cortical hierarchy reference.",
    },
    {
        "id": "glasser_hcp_myelin",
        "label": "Glasser et al. 2016 HCP multimodal parcellation/myelin mapping",
        "url": "https://pubmed.ncbi.nlm.nih.gov/27437579/",
        "role": "Canonical HCP multimodal cortical parcellation and T1w/T2w myelin context.",
    },
    {
        "id": "ahba_transcriptome",
        "label": "French and Paus 2015 AHBA cortical transcriptome",
        "url": "https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2015.00323/full",
        "role": "Canonical Allen Human Brain Atlas transcriptomic-map workflow reference.",
    },
    {
        "id": "lyons_first_psilocybin",
        "label": "Lyons et al. 2026 human brain changes after first psilocybin use",
        "url": "https://www.nature.com/articles/s41467-026-71962-3",
        "role": "Recent multimodal psilocybin benchmark for acute entropy, DTI, modularity, and well-being-linked outcomes.",
    },
    {
        "id": "psiconnect_dataset",
        "label": "Novelli et al. 2026 PsiConnect psilocybin multimodal neuroimaging dataset",
        "url": "https://www.nature.com/articles/s41597-026-07312-1",
        "role": "Recent Nature Portfolio dataset descriptor that can guide future authorized external validation, not used as validation here.",
    },
]

CANONICAL_PROXY_MAPS: list[dict[str, Any]] = [
    {
        "map_id": "hcp_t1w_t2w_myelin_hierarchy_proxy",
        "family": "myelin",
        "label": "HCP T1w/T2w myelin hierarchy proxy",
        "source_status": "canonical_direction_proxy_not_subject_hcp_extraction",
        "values": {
            "visual": 1.00,
            "auditory": 0.78,
            "salience": 0.44,
            "default_mode": 0.20,
            "executive_frontoparietal": 0.30,
            "limbic_affective": 0.16,
            "thalamic_gateway": 0.62,
            "sensorimotor": 0.95,
        },
        "interpretation": "Higher values approximate more myelinated sensory/unimodal cortex; lower values approximate transmodal cortex.",
        "source_reference_ids": ["glasser_hcp_myelin"],
    },
    {
        "map_id": "principal_functional_gradient_proxy",
        "family": "functional_gradient",
        "label": "Principal functional gradient proxy",
        "source_status": "canonical_direction_proxy_not_surface_gradient_projection",
        "values": {
            "visual": 0.00,
            "auditory": 0.16,
            "salience": 0.56,
            "default_mode": 1.00,
            "executive_frontoparietal": 0.84,
            "limbic_affective": 0.70,
            "thalamic_gateway": 0.34,
            "sensorimotor": 0.04,
        },
        "interpretation": "Higher values approximate transmodal/default-mode end of the principal cortical gradient.",
        "source_reference_ids": ["margulies_gradient", "neuromaps"],
    },
    {
        "map_id": "ahba_htr2a_expression_proxy",
        "family": "gene_expression",
        "label": "AHBA HTR2A expression-direction proxy",
        "source_status": "canonical_direction_proxy_not_ahba_reprojection",
        "values": {
            "visual": 0.22,
            "auditory": 0.54,
            "salience": 0.72,
            "default_mode": 0.95,
            "executive_frontoparietal": 0.86,
            "limbic_affective": 0.28,
            "thalamic_gateway": 0.50,
            "sensorimotor": 0.48,
        },
        "interpretation": "Coarse directional HTR2A transcriptomic prior; PET receptor maps should outrank this for receptor claims.",
        "source_reference_ids": ["ahba_transcriptome"],
    },
]


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _normalise(values: dict[str, float]) -> dict[str, float]:
    ordered = [_finite_float(values.get(module)) for module in MODULE_NAMES]
    minimum = min(ordered)
    maximum = max(ordered)
    span = max(maximum - minimum, 1e-12)
    return {module: (value - minimum) / span for module, value in zip(MODULE_NAMES, ordered, strict=True)}


def _load_receptor_prior(repo_root: Path, output_path: Path) -> dict[str, Any] | None:
    candidates = [
        repo_root / "results" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv",
        repo_root / "data" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv",
    ]
    receptor_path = next((path for path in candidates if path.exists() and path.is_file()), None)
    if receptor_path is not None:
        rows = _read_csv(receptor_path)
        by_module = {str(row.get("module", "")).strip(): row for row in rows}
        if all(module in by_module for module in MODULE_NAMES):
            values = {
                module: _finite_float(
                    by_module[module].get("receptor_weight", by_module[module].get("weight")),
                    default=0.0,
                )
                for module in MODULE_NAMES
            }
            return {
                "map_id": "pet_5ht2a_receptor_prior",
                "family": "receptor",
                "label": "PET 5-HT2A receptor prior",
                "source_status": "local_hansen_pet_projection_loaded",
                "source_path": _rel(receptor_path, repo_root),
                "values": _normalise(values),
                "interpretation": "Higher values approximate stronger projected 5-HT2A PET prior at the macro-module level.",
                "source_reference_ids": ["neuromaps"],
            }

    if output_path.exists() and output_path.is_file():
        try:
            previous = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}
        for row in previous.get("maps", []):
            if row.get("map_id") == "pet_5ht2a_receptor_prior" and isinstance(row.get("values"), dict):
                values = {module: _finite_float(row["values"].get(module), default=0.0) for module in MODULE_NAMES}
                return {
                    "map_id": "pet_5ht2a_receptor_prior",
                    "family": "receptor",
                    "label": "PET 5-HT2A receptor prior",
                    "source_status": "reused_committed_derived_snapshot_missing_local_pet_csv",
                    "source_path": previous.get("source_path"),
                    "values": _normalise(values),
                    "interpretation": "Derived PET prior snapshot reused because the local ignored CSV was not present.",
                    "source_reference_ids": ["neuromaps"],
                }
    return None


def _load_map_specs(repo_root: Path, output_path: Path) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    receptor = _load_receptor_prior(repo_root, output_path)
    if receptor is not None:
        specs.append(receptor)
    for spec in CANONICAL_PROXY_MAPS:
        specs.append({**spec, "values": _normalise(spec["values"])})
    return specs


def _load_dynamic_targets(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    summary_path = repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json"
    if not summary_path.exists():
        return [], {
            "analysis_status": "missing_dynamic_mechanism_summary",
            "source_path": _rel(summary_path, repo_root),
            "claim_guardrail": "External maps cannot be aligned until module-level LSD-placebo dynamic vectors exist.",
        }
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    modules = [str(module) for module in summary.get("modules", MODULE_NAMES)]
    interaction_rows = summary.get("dmdc", {}).get("condition_interaction_vector", [])
    input_rows = summary.get("dmdc", {}).get("condition_input_vector", [])

    def by_module(rows: list[dict[str, Any]]) -> dict[str, float]:
        raw = {str(row.get("module")): _finite_float(row.get("coefficient")) for row in rows}
        return {module: raw.get(module, 0.0) for module in MODULE_NAMES}

    interaction = by_module(interaction_rows)
    condition_input = by_module(input_rows)
    targets = [
        {
            "target_id": "dmdc_lsd_specific_state_update",
            "label": "DMDC LSD-specific state-update coefficient",
            "values": interaction,
            "interpretation": "Signed module coefficient for condition-by-state dynamics under LSD.",
        },
        {
            "target_id": "dmdc_lsd_specific_update_magnitude",
            "label": "DMDC LSD-specific update magnitude",
            "values": {module: abs(value) for module, value in interaction.items()},
            "interpretation": "Unsigned module magnitude of LSD-specific state-update change.",
        },
        {
            "target_id": "dmdc_condition_input",
            "label": "DMDC condition-input coefficient",
            "values": condition_input,
            "interpretation": "Signed module coefficient for the direct LSD-vs-placebo condition input.",
        },
    ]
    return targets, {
        "analysis_status": "module_level_dmdc_targets_loaded",
        "source_path": _rel(summary_path, repo_root),
        "modules_in_summary": modules,
        "claim_guardrail": "These vectors are module-level empirical-dynamics summaries, not voxelwise brain-map data.",
    }


def _pearson(x_values: list[float], y_values: list[float]) -> float | None:
    x = np.asarray(x_values, dtype=float)
    y = np.asarray(y_values, dtype=float)
    if x.size != y.size or x.size < 4:
        return None
    x = x - float(np.mean(x))
    y = y - float(np.mean(y))
    denom = float(np.linalg.norm(x) * np.linalg.norm(y))
    if denom <= 1e-12:
        return None
    return float(np.dot(x, y) / denom)


def _exact_permutation_p(x_values: list[float], y_values: list[float], observed_r: float | None) -> float | None:
    if observed_r is None:
        return None
    threshold = abs(observed_r)
    total = 0
    extreme = 0
    for permuted in itertools.permutations(x_values):
        permuted_r = _pearson(list(permuted), y_values)
        if permuted_r is None:
            continue
        total += 1
        if abs(permuted_r) >= threshold - 1e-12:
            extreme += 1
    return (extreme + 1) / (total + 1) if total else None


def _correlation_ci(r_value: float | None, n: int) -> tuple[float | None, float | None]:
    if r_value is None or n <= 3:
        return None, None
    clipped = max(min(r_value, 0.999999), -0.999999)
    z_value = math.atanh(clipped)
    se = 1.0 / math.sqrt(n - 3)
    return math.tanh(z_value - 1.96 * se), math.tanh(z_value + 1.96 * se)


def _bh_q_values(rows: list[dict[str, Any]]) -> None:
    indexed = [(index, row.get("permutation_p")) for index, row in enumerate(rows) if row.get("permutation_p") is not None]
    indexed.sort(key=lambda pair: float(pair[1]))
    m = len(indexed)
    previous = 1.0
    q_by_index: dict[int, float] = {}
    for rank_from_end, (index, p_value) in enumerate(reversed(indexed), start=1):
        rank = m - rank_from_end + 1
        q_value = min(previous, float(p_value) * m / rank)
        previous = q_value
        q_by_index[index] = q_value
    for index, row in enumerate(rows):
        q_value = q_by_index.get(index)
        row["q_value"] = q_value
        row["fdr_significant_0_05"] = bool(q_value is not None and q_value <= 0.05)
        row["alignment_status"] = (
            "fdr_supported_module_proxy"
            if row["fdr_significant_0_05"] and not row.get("ci_overlaps_zero", True)
            else ("nominal_only_not_fdr" if row.get("permutation_p") is not None and row["permutation_p"] <= 0.05 else "exploratory_no_fdr_support")
        )


def _alignment_rows(map_specs: list[dict[str, Any]], targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for map_spec in map_specs:
        map_values = [_finite_float(map_spec["values"].get(module)) for module in MODULE_NAMES]
        for target in targets:
            target_values = [_finite_float(target["values"].get(module)) for module in MODULE_NAMES]
            r_value = _pearson(map_values, target_values)
            p_value = _exact_permutation_p(map_values, target_values, r_value)
            ci_low, ci_high = _correlation_ci(r_value, len(MODULE_NAMES))
            rows.append(
                {
                    "map_id": map_spec["map_id"],
                    "map_label": map_spec["label"],
                    "map_family": map_spec["family"],
                    "target_id": target["target_id"],
                    "target_label": target["label"],
                    "pearson_r": r_value,
                    "abs_pearson_r": abs(r_value) if r_value is not None else None,
                    "permutation_p": p_value,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "ci_overlaps_zero": bool(ci_low is None or ci_high is None or ci_low <= 0 <= ci_high),
                    "n_modules": len(MODULE_NAMES),
                    "method": "exact_module_label_permutation_null_not_surface_spatial_null",
                }
            )
    _bh_q_values(rows)
    return rows


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# External cortical-map alignment",
        "",
        payload["claim_guardrail"],
        "",
        "| Map | Target | r | p | q | CI overlaps zero | Status |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload.get("alignment_rows", []):
        lines.append(
            "| {map} | {target} | {r:.3f} | {p:.4f} | {q:.4f} | {ci} | {status} |".format(
                map=row["map_label"],
                target=row["target_label"],
                r=float(row["pearson_r"]) if row["pearson_r"] is not None else float("nan"),
                p=float(row["permutation_p"]) if row["permutation_p"] is not None else float("nan"),
                q=float(row["q_value"]) if row["q_value"] is not None else float("nan"),
                ci="yes" if row["ci_overlaps_zero"] else "no",
                status=row["alignment_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Method boundary",
            "",
            payload["neuromaps_status"]["claim_guardrail"],
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_cortical_map_alignment(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "cortical_maps"
    output_path = output_dir / "cortical_map_alignment_status.json"
    map_specs = _load_map_specs(repo_root, output_path)
    targets, target_status = _load_dynamic_targets(repo_root)
    alignment_rows = _alignment_rows(map_specs, targets) if map_specs and targets else []
    best = max(alignment_rows, key=lambda row: float(row.get("abs_pearson_r") or -1.0), default=None)
    fdr_count = sum(1 for row in alignment_rows if row.get("fdr_significant_0_05"))
    strong_claim_ready = bool(
        best is not None
        and best.get("fdr_significant_0_05")
        and not best.get("ci_overlaps_zero", True)
        and str(best.get("method")) != "exact_module_label_permutation_null_not_surface_spatial_null"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": "implemented_module_level_external_map_alignment" if alignment_rows else "missing_alignment_inputs",
        "module_contract": list(MODULE_NAMES),
        "maps": map_specs,
        "dynamic_targets": targets,
        "dynamic_target_status": target_status,
        "alignment_rows": alignment_rows,
        "best_alignment": best,
        "fdr_supported_count": fdr_count,
        "claim_readiness": {
            "strong_receptor_myelin_gradient_claim": "ready" if strong_claim_ready else "not_supported_yet",
            "current_best_result": (
                "The strongest current module-level alignment is still exploratory because FDR significance and CI-zero gates are not both passed."
                if best is not None
                else "No alignment rows are available."
            ),
            "required_for_stronger_claim": [
                "Re-extract empirical LSD-placebo dynamic features at a higher-resolution cortical parcellation rather than only the 8-module presentation layer.",
                "Project receptor, myelin, functional-gradient, and AHBA maps into the same parcellation.",
                "Run spatial-autocorrelation-aware nulls with neuromaps or equivalent surface/parcellation nulls.",
                "Retain q-value, FDR-significance, CI-overlap, and external-dataset replication gates before strengthening claims.",
            ],
            "claim_boundary": "The dashboard may say these maps are plausible anatomical/molecular priors. It should not say they prove receptor, myelin, or gradient mechanisms.",
        },
        "parcellation_upgrade": {
            "current_contract": "8_macro_modules_for_readable_dashboard_and_legacy_pipeline_compatibility",
            "recommendation": "Do not simply rename the 8 modules. Keep them as a public-facing bridge layer and add a separate high-resolution inference layer.",
            "recommended_next_contract": "Schaefer-100 or Schaefer-200 parcels with Yeo-7/Yeo-17 network labels, plus optional Glasser/HCP-MMP1.0 sensitivity.",
            "why": (
                "Schaefer/Yeo is easier to align with neuromaps and resting-state network literature; Glasser is anatomically rich for myelin/HCP claims but harder to match "
                "to every external map and subcortical target. The thesis should report high-resolution inference first and aggregate to 8 modules only for explanation."
            ),
            "minimum_next_artifacts": [
                "results/cortical_maps/schaefer_yield_manifest.json",
                "results/cortical_maps/surface_spatial_null_status.json",
                "results/cortical_maps/high_resolution_map_alignment_status.json",
            ],
        },
        "recent_psilocybin_benchmark": {
            "source_reference_id": "lyons_first_psilocybin",
            "study": "Human brain changes after first psilocybin use",
            "journal": "Nature Communications",
            "published": "2026-05-05",
            "doi": "10.1038/s41467-026-71962-3",
            "dose_and_design": "Exploratory within-subject study in psychedelic-naive healthy participants; 1 mg control dose and later 25 mg psilocybin.",
            "dashboard_relevance": [
                "Adds a recent human benchmark where acute entropy increase is a central mechanistic readout.",
                "Supports showing DTI/structural findings as long-timescale anatomical context, not acute drug-state proof.",
                "Highlights modularity and network organization as useful longitudinal outcomes.",
                "Reinforces caution: DTI axial-diffusivity interpretation is biologically non-specific and must be confound-guarded.",
            ],
            "metric_mapping": [
                {
                    "article_measure": "EEG Lempel-Ziv complexity / entropy at 1-2 hours",
                    "dashboard_proxy": "entropy-like and transition-diversity macro-dynamics",
                    "use": "external mechanistic plausibility anchor",
                    "claim_boundary": "not direct replication because modality, drug, timing, and dataset differ",
                },
                {
                    "article_measure": "fMRI network modularity change over one month",
                    "dashboard_proxy": "integration, segregation, modularity, and dynamic-repertoire summaries",
                    "use": "motivates modularity/integration as longitudinal outcomes",
                    "claim_boundary": "not an LSD validation and not a same-time-scale comparison",
                },
                {
                    "article_measure": "DTI axial diffusivity in prefrontal-subcortical tracts",
                    "dashboard_proxy": "structural-connectome/DTI prior and network-control route constraints",
                    "use": "supports showing white-matter structure as context",
                    "claim_boundary": "DTI interpretation is non-specific; do not infer neuroplastic mechanism from this thesis panel",
                },
                {
                    "article_measure": "one-month well-being and next-day insight associations",
                    "dashboard_proxy": "none yet",
                    "use": "future outcome-alignment target if behavioral scales are authorized and ingested",
                    "claim_boundary": "no subjective or clinical outcome claim in the current thesis pipeline",
                },
            ],
            "caveats": [
                "healthy psychedelic-naive sample",
                "exploratory fixed-order design",
                "psilocybin rather than LSD",
                "weak or absent enduring fMRI effects except selected network associations",
                "DTI axial-diffusivity biology is non-specific",
            ],
        },
        "future_external_dataset_context": {
            "source_reference_id": "psiconnect_dataset",
            "study": "PsiConnect: Multimodal Neuroimaging of Context-Dependent Brain and Behaviour Dynamics under Psilocybin",
            "journal": "Scientific Data",
            "published": "2026-05-21",
            "doi": "10.1038/s41597-026-07312-1",
            "status": "candidate_future_authorized_external_dataset_not_ingested",
            "claim_boundary": "Useful for planning future external validation only; it is not evidence for the current scores until data are obtained and scored unchanged.",
        },
        "source_references": SOURCE_REFERENCES,
        "neuromaps_status": {
            "analysis_status": "not_run_module_level_only",
            "recommended_next_step": "Project source maps and empirical LSD-placebo effects to a common cortical surface/parcellation and run neuromaps spatial nulls.",
            "claim_guardrail": (
                "This pass compares maps after aggregation to the 8-module thesis contract with exact label-permutation p-values. "
                "It is not a full neuromaps surface-level spatial-autocorrelation null analysis."
            ),
        },
        "claim_guardrail": (
            "External receptor, myelin, functional-gradient, and transcriptomic maps are treated as anatomical or molecular priors. "
            "Agreement with LSD-placebo dynamics is exploratory module-level proxy evidence, not receptor pharmacology, clinical validation, "
            "or subjective-experience evidence."
        ),
    }


def write_cortical_map_alignment_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "cortical_maps"
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_cortical_map_alignment(repo_root, output_dir)
    status_path = output_dir / "cortical_map_alignment_status.json"
    markdown_path = output_dir / "cortical_map_alignment.md"
    payload["source_path"] = _rel(status_path, repo_root)
    payload["markdown_path"] = _rel(markdown_path, repo_root)
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(payload, markdown_path)
    return payload
