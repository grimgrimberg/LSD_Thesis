from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.ds006072_validation import build_ds006072_comparable_validation_status
from lsd_thesis.dynamic_mechanism import (
    build_dynamic_mechanism_summary,
    load_empirical_pairs,
    summarize_network_control_energy,
)
from lsd_thesis.dynamic_robustness import build_dynamic_robustness_summary
from lsd_thesis.graph import load_graph_config

REPO_ROOT = Path(__file__).resolve().parents[2]
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
    return json.loads(path.read_text(encoding="utf-8"))


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


def _build_claim_evidence_matrix(components: dict[str, Any]) -> list[dict[str, Any]]:
    lsd = components.get("lsd_robustness", {})
    psilocybin = components.get("psilocybin_ds006072", {})
    structural = components.get("structural_connectome", {})
    receptor = components.get("receptor_priors", {})
    parcellation = components.get("parcellation_sensitivity", {})
    literature = components.get("literature_benchmark", {})
    return [
        _claim_row(
            claim="C survives LSD robustness checks",
            dataset="OpenNeuro ds003059 LSD/placebo empirical viewer",
            model_layer="C hierarchy/routing",
            null_control=(
                "subject bootstrap; run sensitivity; A/E state-label sensitivity; "
                "D window and E horizon stress tests"
            ),
            figure=(
                "dynamic_hierarchy_plot; robustness_bootstrap_plot; "
                "robustness_run_plot"
            ),
            export=(
                "results/dynamic_mechanism_ranking/exports/dynamic_mechanism_results.xlsx; "
                "results/thesis_evidence_loop/claim_evidence_matrix.csv"
            ),
            citation=(
                "Girn et al. 2026 Nature Medicine https://www.nature.com/articles/s41591-026-04287-9"
            ),
            limitation="Internal LSD-only proxy evidence; not causal mechanism proof.",
            status=_analysis_status(lsd),
        ),
        _claim_row(
            claim="C survives Schaefer/Yeo 100/200 and Yeo 7/17 with comparable direction",
            dataset="ds003059 parcellation sensitivity artifacts",
            model_layer="C hierarchy/routing",
            null_control="Schaefer 100/200 and Yeo 7/17 versus the current 8-module proxy",
            figure="parcellation_sensitivity_table",
            export=(
                "results/parcellation_sensitivity/parcellation_status.csv; "
                "results/parcellation_sensitivity/parcellation_ranking_comparison.csv; "
                "results/thesis_evidence_loop/exports/thesis_evidence_loop_tables.xlsx"
            ),
            citation="Schaefer et al. 2018 Cerebral Cortex https://doi.org/10.1093/cercor/bhx179",
            limitation=(
                "Status matrix is not full sensitivity evidence unless parcellation-specific "
                "empirical viewer and ranking rows exist."
            ),
            status=_parcellation_claim_status(parcellation),
        ),
        _claim_row(
            claim="E survives real structural-connectome graph",
            dataset="HCP Young Adult or local normative structural-connectome CSV",
            model_layer="E network-control energy",
            null_control="macro proxy graph; uniform graph; degree-expected graph; edge-weight rewires",
            figure="dynamic_control_plot; structural_proxy_null_table",
            export=(
                "results/structural_connectome/structural_connectome_status.json; "
                "results/structural_connectome/proxy_graph_control_nulls.csv"
            ),
            citation=(
                "HCP Young Adult https://www.humanconnectome.org/study/hcp-young-adult; "
                "Singleton et al. 2022 Nature Communications https://www.nature.com/articles/s41467-022-33578-1"
            ),
            limitation=(
                "Blocked unless HCP/normative structural graph CSV exists; proxy graph controls "
                "are not structural-connectome evidence."
            ),
            status=_analysis_status(structural),
        ),
        _claim_row(
            claim="E survives PET receptor-map priors",
            dataset="neuromaps/FS5ht 5-HT2A PET receptor prior projected to modules",
            model_layer="E receptor-informed network-control energy",
            null_control="uniform; random permutation; degree control; spatial/autocorrelation null",
            figure="dynamic_control_plot; receptor_null_table",
            export=(
                "results/receptor_priors/receptor_prior_status.json; "
                "results/receptor_priors/proxy_receptor_null_board.csv"
            ),
            citation=(
                "Markello et al. 2022 Nature Methods https://www.nature.com/articles/s41592-022-01625-w; "
                "Singleton et al. 2022 Nature Communications https://www.nature.com/articles/s41467-022-33578-1"
            ),
            limitation=(
                "Blocked unless PET-derived receptor prior and spatial nulls exist; current "
                "receptor board is a coarse proxy."
            ),
            status=_analysis_status(receptor),
        ),
        _claim_row(
            claim="ds006072 psilocybin reproduces the LSD A+B+C+D+E ranking",
            dataset="OpenNeuro ds006072 psilocybin precision functional mapping",
            model_layer="A+B+C+D+E mechanism ranking",
            null_control="same scoring rules as LSD; paired psilocybin/control empirical viewer",
            figure="thesis_loop_steps; planned LSD-vs-psilocybin ranking comparison",
            export=(
                "results/psilocybin_ds006072/psilocybin_ds006072_status.json; "
                "results/thesis_evidence_loop/exports/ds006072_summary.csv"
            ),
            citation=(
                "Dosenbach/Siegel group 2025 Scientific Data https://doi.org/10.1038/s41597-025-05189-0; "
                "OpenNeuro ds006072 https://openneuro.org/datasets/ds006072"
            ),
            limitation="Manifest readiness is not replication; no claim until comparable empirical viewer exists.",
            status=_analysis_status(psilocybin),
        ),
        _claim_row(
            claim="Final C/D/E pattern aligns with psychedelic mega-analysis and NCT anchors",
            dataset="ds003059 LSD proxy deltas plus literature benchmark rows",
            model_layer="C hierarchy/routing; D dynamic repertoire; E network-control energy",
            null_control="directional proxy benchmark; explicit mismatches retained",
            figure="literature_benchmark_plot; literature_benchmark_table",
            export=(
                "results/literature_benchmark/literature_benchmark.csv; "
                "results/thesis_evidence_loop/claim_evidence_matrix.csv"
            ),
            citation=(
                "Girn et al. 2026 Nature Medicine https://www.nature.com/articles/s41591-026-04287-9; "
                "Singleton et al. 2022 Nature Communications https://www.nature.com/articles/s41467-022-33578-1"
            ),
            limitation="Directional proxy benchmark only; not a mega-analysis or full NCT reproduction.",
            status=_analysis_status(literature),
        ),
        _claim_row(
            claim="Failed literature checks are diagnosed as contradiction or proxy mismatch",
            dataset="results/literature_benchmark/literature_benchmark.csv",
            model_layer="C/D/E failure-case analysis",
            null_control="row-level mismatch review; sign/opposes/weak checks",
            figure="literature_benchmark_table",
            export=(
                "results/literature_benchmark/literature_benchmark.csv; "
                "results/thesis_evidence_loop/claim_evidence_matrix.csv"
            ),
            citation=(
                "Girn et al. 2026 Nature Medicine https://www.nature.com/articles/s41591-026-04287-9; "
                "Singleton et al. 2022 Nature Communications https://www.nature.com/articles/s41467-022-33578-1"
            ),
            limitation=(
                "Requires explicit per-row mismatch reason; unresolved mismatches stay out of "
                "final conclusions."
            ),
            status=_literature_mismatch_status(literature),
        ),
    ]


def _matrix_from_csv(path: Path, modules: tuple[str, ...]) -> tuple[np.ndarray, str]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
    if not rows:
        raise ValueError(f"Graph CSV is empty: {path}")
    if {"source", "target", "weight"}.issubset(rows[0]):
        index = {module: idx for idx, module in enumerate(modules)}
        matrix = np.zeros((len(modules), len(modules)), dtype=float)
        for row in rows:
            source = str(row["source"])
            target = str(row["target"])
            if source not in index or target not in index:
                continue
            weight = float(row["weight"])
            matrix[index[source], index[target]] = weight
            matrix[index[target], index[source]] = weight
        return matrix, "edge_list"

    header_modules = [module for module in modules if module in rows[0]]
    if "module" in rows[0] and len(header_modules) == len(modules):
        row_by_module = {str(row["module"]): row for row in rows}
        matrix = np.asarray(
            [[float(row_by_module[source][target]) for target in modules] for source in modules],
            dtype=float,
        )
        return matrix, "square_matrix"
    raise ValueError(
        "Graph CSV must either contain source,target,weight columns or module plus one column per module."
    )


def _prior_vector_from_csv(path: Path, modules: tuple[str, ...]) -> tuple[np.ndarray, str]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
    by_module = {str(row.get("module")): row for row in rows}
    values: list[float] = []
    sources: set[str] = set()
    for module in modules:
        row = by_module.get(module)
        if row is None:
            raise ValueError(f"Receptor prior CSV is missing module '{module}'.")
        values.append(float(row.get("receptor_weight", row.get("weight", 0.0))))
        if row.get("source"):
            sources.add(str(row["source"]))
    source = "; ".join(sorted(sources)) if sources else path.as_posix()
    return np.asarray(values, dtype=float), source


def _metric_lookup(control: dict[str, Any]) -> dict[str, float]:
    return {
        str(row.get("metric")): float(row.get("mean_delta", 0.0))
        for row in control.get("metric_deltas", [])
    }


def _graph_control_row(label: str, control: dict[str, Any], *, rewire_index: int | None = None) -> dict[str, Any]:
    metrics = _metric_lookup(control)
    row = {
        "graph_control": label,
        "rewire_index": rewire_index,
        "support_score": float(control.get("support_score", 0.0)),
        "graph_source": control.get("graph_source", ""),
        "receptor_vs_random_energy_reduction_pct": metrics.get("receptor_vs_random_energy_reduction_pct"),
        "receptor_vs_uniform_energy_reduction_pct": metrics.get("receptor_vs_uniform_energy_reduction_pct"),
        "lsd_vs_placebo_receptor_transition_energy_reduction_pct": metrics.get(
            "lsd_vs_placebo_receptor_transition_energy_reduction_pct"
        ),
        "state_target_alignment_receptor": metrics.get("state_target_alignment_receptor"),
    }
    return row


def _uniform_graph_like(matrix: np.ndarray) -> np.ndarray:
    graph = np.maximum(np.asarray(matrix, dtype=float), 0.0)
    n = graph.shape[0]
    upper = graph[np.triu_indices(n, k=1)]
    positive_mean = float(np.mean(upper[upper > 0.0])) if np.any(upper > 0.0) else 1.0
    output = np.full((n, n), positive_mean, dtype=float)
    np.fill_diagonal(output, 0.0)
    return output


def _degree_expected_graph(matrix: np.ndarray) -> np.ndarray:
    graph = np.maximum(np.asarray(matrix, dtype=float), 0.0)
    degree = np.sum(graph, axis=1)
    total = float(np.sum(degree))
    if total <= 1e-12:
        return _uniform_graph_like(graph)
    output = np.outer(degree, degree) / total
    np.fill_diagonal(output, 0.0)
    return output


def _rewired_weight_graph(matrix: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    graph = np.maximum(np.asarray(matrix, dtype=float), 0.0)
    n = graph.shape[0]
    upper_indices = np.triu_indices(n, k=1)
    weights = np.asarray(graph[upper_indices], dtype=float)
    shuffled = rng.permutation(weights)
    output = np.zeros_like(graph, dtype=float)
    output[upper_indices] = shuffled
    output = output + output.T
    return output


def _build_proxy_graph_control_rows(pairs: list[Any], graph_matrix: np.ndarray) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    controls = {
        "macro_proxy_graph": graph_matrix,
        "uniform_weight_graph": _uniform_graph_like(graph_matrix),
        "degree_expected_graph": _degree_expected_graph(graph_matrix),
    }
    for label, matrix in controls.items():
        control = summarize_network_control_energy(
            pairs,
            graph_matrix_override=matrix,
            graph_source_override=f"{label}; proxy graph control, not HCP structural connectome",
            random_null_count=16,
        )
        rows.append(_graph_control_row(label, control))
    rng = np.random.default_rng(20260520)
    for rewire_index in range(16):
        control = summarize_network_control_energy(
            pairs,
            graph_matrix_override=_rewired_weight_graph(graph_matrix, rng),
            graph_source_override="rewired macro-proxy edge-weight null; not HCP structural connectome",
            random_null_count=8,
        )
        rows.append(_graph_control_row("edge_weight_rewire_null", control, rewire_index=rewire_index))
    return rows


def _coarse_receptor_null_rows(repo_root: Path, pairs: list[Any]) -> list[dict[str, Any]]:
    summary = _load_json(repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json")
    control = (
        summary.get("network_control_energy", {})
        if isinstance(summary, dict)
        else summarize_network_control_energy(pairs, random_null_count=32)
    )
    rows = []
    for row in control.get("metric_deltas", []):
        metric = str(row.get("metric", ""))
        null_family = "spatial_null_missing"
        if "uniform" in metric:
            null_family = "uniform_control"
        elif "random" in metric:
            null_family = "random_permutation"
        elif "degree" in metric:
            null_family = "degree_control"
        elif "receptor" in metric:
            null_family = "coarse_receptor_proxy"
        rows.append(
            {
                "metric": metric,
                "mean_delta": row.get("mean_delta"),
                "signed_effect_size": row.get("signed_effect_size"),
                "expected_direction": row.get("expected_direction"),
                "null_family": null_family,
                "prior_source": control.get("receptor_prior_source"),
                "claim_status": "proxy_only_not_pet_receptor_claim",
            }
        )
    rows.append(
        {
            "metric": "spatial_autocorrelation_preserving_null",
            "mean_delta": None,
            "signed_effect_size": None,
            "expected_direction": "PET-derived receptor map should outperform spatial nulls",
            "null_family": "spatial_null_missing",
            "prior_source": "missing PET receptor map",
            "claim_status": "blocked_until_neuromaps_or_FS5ht_projection_exists",
        }
    )
    return rows


def build_psilocybin_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "psilocybin_ds006072"
    viewer_root = output_dir / "empirical_viewer"
    readiness_path = output_dir / "external_validation_readiness.json"
    local_data_root = repo_root / "data" / DS006072_DATASET_ID
    metadata_manifest_path = local_data_root / "ds006072_metadata_manifest.json"
    func_manifest_path = local_data_root / "ds006072_func_manifest.json"
    metadata_manifest = _load_json(metadata_manifest_path)
    func_manifest = _load_json(func_manifest_path)
    readiness = _load_json(readiness_path)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "dataset_id": DS006072_DATASET_ID,
        "source": "OpenNeuro ds006072, Scientific Data 2025 psilocybin precision imaging dataset",
        "local_data_root": local_data_root.relative_to(repo_root).as_posix(),
        "viewer_root": viewer_root.relative_to(repo_root).as_posix(),
        "metadata_manifest": metadata_manifest_path.relative_to(repo_root).as_posix() if metadata_manifest_path.exists() else None,
        "metadata_snapshot_tag": metadata_manifest.get("snapshot_tag") if isinstance(metadata_manifest, dict) else None,
        "functional_manifest": func_manifest_path.relative_to(repo_root).as_posix() if func_manifest_path.exists() else None,
        "functional_manifest_rest_bold_nifti_count": (
            func_manifest.get("rest_bold_nifti_count") if isinstance(func_manifest, dict) else None
        ),
        "functional_manifest_rest_bold_total_size_bytes": (
            func_manifest.get("rest_bold_total_size_bytes") if isinstance(func_manifest, dict) else None
        ),
        "functional_manifest_processed_rest_cifti_count": (
            func_manifest.get("processed_rest_cifti_count") if isinstance(func_manifest, dict) else None
        ),
        "functional_manifest_processed_cifti_total_size_bytes": (
            func_manifest.get("processed_cifti_total_size_bytes") if isinstance(func_manifest, dict) else None
        ),
        "external_validation_readiness": readiness if isinstance(readiness, dict) else None,
        "external_validation_readiness_path": (
            readiness_path.relative_to(repo_root).as_posix() if readiness_path.exists() else None
        ),
        "claim_guardrail": "No psilocybin replication claim is allowed unless comparable paired drug/control empirical viewer records exist.",
    }
    comparable_validation = build_ds006072_comparable_validation_status(repo_root)
    if comparable_validation.get("unchanged_scoring_applied"):
        summary = comparable_validation.get("summary", {}) if isinstance(comparable_validation.get("summary"), dict) else {}
        payload.update(
            {
                "analysis_status": comparable_validation["analysis_status"],
                "pair_count": summary.get("pair_count", 0),
                "subject_count": summary.get("subject_count", 0),
                "mechanism_ranking": summary.get("mechanism_ranking", []),
                "summary": summary,
                "comparable_empirical_validation": comparable_validation,
                "comparable_empirical_validation_path": comparable_validation["source_path"],
                "unchanged_scoring_applied": True,
                "replication_status": comparable_validation.get("replication_status"),
            }
        )
    else:
        schema_path = output_dir / "required_empirical_viewer_schema.json"
        _write_json(
            schema_path,
            {
                "subject_views_pattern": "subject_views/{subject}_{run}.json",
                "required_conditions": ["control_or_placebo_session", "psilocybin_session"],
                "required_fields": [
                    "subject",
                    "run",
                    "conditions.<control>.module_time_series",
                    "conditions.<psilocybin>.module_time_series",
                ],
                "note": "The condition names must be harmonized before running the dynamic mechanism summary.",
            },
        )
        readiness_status = readiness.get("analysis_status") if isinstance(readiness, dict) else None
        readiness_blocker = readiness.get("blocker") if isinstance(readiness, dict) else None
        payload.update(
            {
                "analysis_status": (
                    comparable_validation.get("analysis_status")
                    or readiness_status
                    or (
                        "metadata_and_file_manifest_ready_missing_empirical_viewer"
                        if func_manifest_path.exists()
                        else "blocked_missing_local_ds006072_empirical_viewer"
                    )
                ),
                "pair_count": comparable_validation.get("pair_count", 0),
                "subject_count": comparable_validation.get("subject_count", 0),
                "blocker": (
                    comparable_validation.get("blocker")
                    or readiness_blocker
                    or (
                        "Expected comparable paired psilocybin/control empirical viewer records under "
                        f"{viewer_root.relative_to(repo_root).as_posix()}."
                    )
                ),
                "schema_template": schema_path.relative_to(repo_root).as_posix(),
                "comparable_empirical_validation": comparable_validation,
                "comparable_empirical_validation_path": comparable_validation["source_path"],
                "unchanged_scoring_applied": False,
                "replication_status": comparable_validation.get("replication_status"),
                "next_commands": [
                    "Build extraction readiness: .venv\\Scripts\\python.exe scripts\\build_ds006072_external_validation_readiness.py",
                    "Acquire or derive ds006072 paired psilocybin/control module time series under data/ds006072/.",
                    "Run metadata provenance first if missing: .venv\\Scripts\\python.exe scripts\\download_ds006072_metadata.py",
                    "Write subject-level JSON records matching results/stage_2/empirical_viewer/subject_views/*.json.",
                    "Then rerun: .venv\\Scripts\\python.exe scripts\\run_thesis_evidence_loop.py",
                ],
            }
        )
    payload["source_path"] = _write_json(output_dir / "psilocybin_ds006072_status.json", payload)
    return payload


def build_structural_connectome_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "structural_connectome"
    graph_candidates = [
        output_dir / "hcp_macro_modules.csv",
        repo_root / "data" / "hcp_structural_connectome" / "macro_modules.csv",
    ]
    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    pairs = load_empirical_pairs(viewer_root)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "artifact_target": output_dir.relative_to(repo_root).as_posix(),
        "expected_graph_files": [path.relative_to(repo_root).as_posix() for path in graph_candidates],
        "claim_guardrail": "HCP structural-control claims require a documented structural-connectome graph, not the macro-module proxy graph.",
    }
    graph_path = next((path for path in graph_candidates if path.exists()), None)
    if graph_path is None or not pairs:
        template_path = output_dir / "required_hcp_macro_modules_template.csv"
        proxy_graph_rows: list[dict[str, Any]] = []
        if pairs and (repo_root / "configs" / "graphs" / "macro_modules.yaml").exists():
            macro_graph = load_graph_config(repo_root / "configs" / "graphs" / "macro_modules.yaml")
            proxy_graph_rows = _build_proxy_graph_control_rows(pairs, np.asarray(macro_graph.adjacency, dtype=float))
            _write_csv(output_dir / "proxy_graph_control_nulls.csv", proxy_graph_rows)
        if graph_path is None:
            template_rows = [
                {"source": source, "target": target, "weight": ""}
                for idx, source in enumerate(MODULE_NAMES)
                for target in MODULE_NAMES[idx + 1 :]
            ]
            _write_csv(template_path, template_rows)
        payload.update(
            {
                "analysis_status": "blocked_missing_hcp_structural_graph" if graph_path is None else "blocked_missing_lsd_pairs",
                "blocker": "No local HCP/normative structural graph CSV was found." if graph_path is None else "No LSD empirical pairs were found.",
                "required_schema": "CSV edge list with source,target,weight or square matrix with module plus module columns.",
                "schema_template": template_path.relative_to(repo_root).as_posix() if graph_path is None else None,
                "proxy_graph_control_status": (
                    "implemented_macro_proxy_graph_controls_not_hcp" if proxy_graph_rows else "not_run"
                ),
                "proxy_graph_control_rows": proxy_graph_rows,
                "proxy_graph_control_path": (
                    (output_dir / "proxy_graph_control_nulls.csv").relative_to(repo_root).as_posix()
                    if proxy_graph_rows
                    else None
                ),
            }
        )
    else:
        graph_matrix, graph_kind = _matrix_from_csv(graph_path, pairs[0].modules)
        control = summarize_network_control_energy(
            pairs,
            graph_matrix_override=graph_matrix,
            graph_source_override=f"{graph_path.relative_to(repo_root).as_posix()} ({graph_kind})",
            graph_is_structural_connectome=True,
        )
        payload.update(
            {
                "analysis_status": "implemented_hcp_structural_graph_sensitivity",
                "graph_path": graph_path.relative_to(repo_root).as_posix(),
                "graph_kind": graph_kind,
                "pair_count": len(pairs),
                "network_control_energy": control,
            }
        )
        _write_csv(output_dir / "structural_network_control_metrics.csv", control.get("metric_deltas", []))
    payload["source_path"] = _write_json(output_dir / "structural_connectome_status.json", payload)
    return payload


def build_receptor_prior_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "receptor_priors"
    prior_candidates = [
        output_dir / "fs5ht_5ht2a_macro_modules.csv",
        repo_root / "data" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv",
        repo_root / "data" / "neuromaps" / "fs5ht_5ht2a_macro_modules.csv",
    ]
    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    pairs = load_empirical_pairs(viewer_root)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "artifact_target": output_dir.relative_to(repo_root).as_posix(),
        "expected_prior_files": [path.relative_to(repo_root).as_posix() for path in prior_candidates],
        "claim_guardrail": "Receptor-specific claims require PET-derived 5-HT2A/FS5ht priors and spatial nulls.",
    }
    prior_path = next((path for path in prior_candidates if path.exists()), None)
    if prior_path is None or not pairs:
        template_path = output_dir / "required_fs5ht_5ht2a_macro_modules_template.csv"
        proxy_null_rows = _coarse_receptor_null_rows(repo_root, pairs) if pairs else []
        if proxy_null_rows:
            _write_csv(output_dir / "proxy_receptor_null_board.csv", proxy_null_rows)
        if prior_path is None:
            _write_csv(
                template_path,
                [
                    {"module": module, "receptor_weight": "", "source": "PET-derived 5-HT2A map projected to this module"}
                    for module in MODULE_NAMES
                ],
            )
        payload.update(
            {
                "analysis_status": "blocked_missing_pet_receptor_prior" if prior_path is None else "blocked_missing_lsd_pairs",
                "blocker": "No local PET-derived receptor-prior CSV was found." if prior_path is None else "No LSD empirical pairs were found.",
                "required_schema": "CSV with module,receptor_weight and optional source columns.",
                "schema_template": template_path.relative_to(repo_root).as_posix() if prior_path is None else None,
                "proxy_null_board_status": (
                    "implemented_coarse_prior_null_board_not_pet" if proxy_null_rows else "not_run"
                ),
                "proxy_null_board_path": (
                    (output_dir / "proxy_receptor_null_board.csv").relative_to(repo_root).as_posix()
                    if proxy_null_rows
                    else None
                ),
                "proxy_null_board_rows": proxy_null_rows,
            }
        )
    else:
        receptor_vector, source = _prior_vector_from_csv(prior_path, pairs[0].modules)
        control = summarize_network_control_energy(
            pairs,
            prior_vectors_override={"receptor": receptor_vector},
            receptor_prior_source_override=f"PET-derived prior from {source}",
        )
        payload.update(
            {
                "analysis_status": "implemented_pet_receptor_prior_sensitivity",
                "prior_path": prior_path.relative_to(repo_root).as_posix(),
                "pair_count": len(pairs),
                "network_control_energy": control,
            }
        )
        _write_csv(output_dir / "receptor_prior_network_control_metrics.csv", control.get("metric_deltas", []))
    payload["source_path"] = _write_json(output_dir / "receptor_prior_status.json", payload)
    return payload


def build_parcellation_sensitivity_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "parcellation_sensitivity"
    stage2_parcellation_root = repo_root / "results" / "stage_2" / "parcellations"
    candidates = {
        "schaefer_100_yeo_7": stage2_parcellation_root / "schaefer_100_yeo_7",
        "schaefer_200_yeo_7": stage2_parcellation_root / "schaefer_200_yeo_7",
        "schaefer_100_yeo_17": stage2_parcellation_root / "schaefer_100_yeo_17",
        "schaefer_200_yeo_17": stage2_parcellation_root / "schaefer_200_yeo_17",
    }
    rows: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for parcellation_id, root in candidates.items():
        viewer_root = root / "empirical_viewer"
        metadata_path = root / "node_metadata.json"
        precomputed_summary_path = output_dir / parcellation_id / "summary.json"
        if precomputed_summary_path.exists():
            summary = _load_json(precomputed_summary_path) or {}
            rows.append(
                {
                    "parcellation_id": parcellation_id,
                    "status": "implemented_mechanism_ranking",
                    "pair_count": summary.get("pair_count", 0),
                    "subject_count": summary.get("subject_count", 0),
                    "top_layer": summary.get("mechanism_ranking", [{}])[0].get("layer"),
                    "summary_path": precomputed_summary_path.relative_to(repo_root).as_posix(),
                }
            )
            comparisons.extend(
                {
                    "parcellation_id": parcellation_id,
                    "rank": row.get("rank"),
                    "layer": row.get("layer"),
                    "score": row.get("score"),
                    "status": row.get("status"),
                }
                for row in summary.get("mechanism_ranking", [])
            )
        elif viewer_root.exists():
            summary = build_dynamic_mechanism_summary(viewer_root, network_control_kwargs={"random_null_count": 16})
            rows.append(
                {
                    "parcellation_id": parcellation_id,
                    "status": "implemented_mechanism_ranking" if summary.get("pair_count", 0) else "blocked_empty_viewer",
                    "pair_count": summary.get("pair_count", 0),
                    "subject_count": summary.get("subject_count", 0),
                    "top_layer": summary.get("mechanism_ranking", [{}])[0].get("layer"),
                    "summary_path": None,
                }
            )
            comparisons.extend(
                {
                    "parcellation_id": parcellation_id,
                    "rank": row.get("rank"),
                    "layer": row.get("layer"),
                    "score": row.get("score"),
                    "status": row.get("status"),
                }
                for row in summary.get("mechanism_ranking", [])
            )
        else:
            rows.append(
                {
                    "parcellation_id": parcellation_id,
                    "status": "metadata_ready_extraction_not_run" if metadata_path.exists() else "blocked_missing_metadata_and_viewer",
                    "pair_count": 0,
                    "subject_count": 0,
                    "top_layer": None,
                    "blocker": f"No empirical_viewer found at {viewer_root.relative_to(repo_root).as_posix()}",
                }
            )
    payload = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "analysis_status": "implemented_status_matrix",
        "rows": rows,
        "ranking_comparison_rows": comparisons,
        "claim_guardrail": "Parcellation sensitivity is not a completed empirical result unless a parcellation-specific empirical_viewer exists.",
    }
    _write_csv(output_dir / "parcellation_status.csv", rows)
    if comparisons:
        _write_csv(output_dir / "parcellation_ranking_comparison.csv", comparisons)
    payload["source_path"] = _write_json(output_dir / "parcellation_sensitivity_status.json", payload)
    return payload


def build_literature_benchmark_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "literature_benchmark"
    summary = _load_json(repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json")
    if summary is None:
        payload = {
            "schema_version": 1,
            "generated_at_utc": _now(),
            "analysis_status": "blocked_missing_dynamic_summary",
            "blocker": "Run scripts/run_dynamic_mechanism_ranking.py first.",
        }
    else:
        robustness = build_dynamic_robustness_summary(summary, repo_root / "results" / "stage_2" / "empirical_viewer")
        benchmark = robustness.get("literature_benchmark", {})
        rows = list(benchmark.get("rows", []))
        payload = {
            "schema_version": 1,
            "generated_at_utc": _now(),
            "analysis_status": "implemented_directional_proxy_benchmark",
            "aligned_count": benchmark.get("aligned_count"),
            "measurable_count": benchmark.get("measurable_count"),
            "alignment_fraction": benchmark.get("alignment_fraction"),
            "rows": rows,
            "claim_guardrail": benchmark.get("claim_guardrail"),
        }
        _write_csv(output_dir / "literature_benchmark.csv", rows)
    payload["source_path"] = _write_json(output_dir / "literature_benchmark_status.json", payload)
    return payload


def build_thesis_evidence_loop(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    dynamic_summary = _load_json(repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json")
    c_bootstrap = None
    if dynamic_summary and dynamic_summary.get("robustness", {}).get("subject_bootstrap"):
        for row in dynamic_summary["robustness"]["subject_bootstrap"].get("layer_summary", []):
            if row.get("layer") == "C":
                c_bootstrap = row.get("rank_1_fraction")
                break
    lsd_status = {
        "analysis_status": "implemented_lsd_robustness"
        if dynamic_summary and dynamic_summary.get("robustness", {}).get("analysis_status")
        else "blocked_missing_dynamic_robustness",
        "source_path": "results/dynamic_mechanism_ranking/summary.json",
        "evidence": (
            f"C rank-1 fraction={c_bootstrap}"
            if c_bootstrap is not None
            else "Run scripts/run_dynamic_mechanism_ranking.py first."
        ),
    }
    psilocybin = build_psilocybin_status(repo_root)
    structural = build_structural_connectome_status(repo_root)
    receptor = build_receptor_prior_status(repo_root)
    parcellation = build_parcellation_sensitivity_status(repo_root)
    literature = build_literature_benchmark_status(repo_root)
    literature_evidence = (
        f"{literature.get('aligned_count', 0)}/{literature.get('measurable_count', 0)} "
        "measurable proxy checks aligned."
    )
    status_rows = [
        _status_row(
            "1",
            "LSD robustness",
            lsd_status["analysis_status"],
            "results/dynamic_mechanism_ranking/robustness/",
            lsd_status["evidence"],
        ),
        _status_row(
            "2",
            "Psilocybin ds006072",
            psilocybin["analysis_status"],
            "results/psilocybin_ds006072/",
            psilocybin.get("blocker", "Comparable ranking generated."),
        ),
        _status_row(
            "3",
            "HCP structural graph",
            structural["analysis_status"],
            "results/structural_connectome/",
            structural.get("blocker", "Structural graph sensitivity generated."),
        ),
        _status_row(
            "4",
            "PET receptor priors",
            receptor["analysis_status"],
            "results/receptor_priors/",
            receptor.get("blocker", "PET receptor sensitivity generated."),
        ),
        _status_row(
            "5",
            "Schaefer/Yeo sensitivity",
            parcellation["analysis_status"],
            "results/parcellation_sensitivity/",
            "Status matrix generated; see per-parcellation rows.",
        ),
        _status_row(
            "6",
            "Mega-analysis comparison",
            literature["analysis_status"],
            "results/literature_benchmark/",
            literature_evidence,
        ),
    ]
    payload = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "analysis_status": "implemented_loop_status_artifacts",
        "status_rows": status_rows,
        "components": {
            "lsd_robustness": lsd_status,
            "psilocybin_ds006072": psilocybin,
            "structural_connectome": structural,
            "receptor_priors": receptor,
            "parcellation_sensitivity": parcellation,
            "literature_benchmark": literature,
        },
        "claim_guardrail": (
            "Implemented/blocked statuses are evidence. A blocked status means the code path and artifact contract exist, "
            "but the raw local data required for the scientific claim are absent."
        ),
    }
    claim_evidence_matrix = _build_claim_evidence_matrix(payload["components"])
    output_dir = repo_root / "results" / "thesis_evidence_loop"
    claim_csv_path = output_dir / "claim_evidence_matrix.csv"
    claim_markdown_path = output_dir / "claim_evidence_matrix.md"
    _write_csv(output_dir / "status_rows.csv", status_rows)
    payload["claim_evidence_matrix"] = claim_evidence_matrix
    payload["claim_evidence_matrix_columns"] = CLAIM_EVIDENCE_COLUMNS
    payload["claim_evidence_matrix_paths"] = {
        "csv": claim_csv_path.relative_to(repo_root).as_posix(),
        "markdown": claim_markdown_path.relative_to(repo_root).as_posix(),
    }
    _write_csv(
        claim_csv_path,
        claim_evidence_matrix,
        CLAIM_EVIDENCE_COLUMNS,
    )
    _write_markdown_table(
        claim_markdown_path,
        claim_evidence_matrix,
        CLAIM_EVIDENCE_COLUMNS,
    )
    payload["source_path"] = _write_json(output_dir / "thesis_evidence_loop_status.json", payload)
    return payload
