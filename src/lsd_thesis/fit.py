from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go
from pydantic import BaseModel, ConfigDict

from lsd_thesis.core import GraphConfig, ModuleParameterOverride, RegimeConfig
from lsd_thesis.data.ds003059 import (
    DS003059_DATASET_ID,
    DS003059_VERSION,
    build_atlas_mapping_audit,
    build_empirical_data_quality_payload,
    generate_empirical_targets,
)
from lsd_thesis.data.empirical_viewer import (
    build_empirical_run_views_from_records,
    build_empirical_viewer_payloads,
    generate_empirical_gallery,
    write_empirical_viewer_cache,
)
from lsd_thesis.data.openneuro import build_openneuro_download_command, ds003059_subset_spec
from lsd_thesis.data.targets import SoberTargetSet, load_perturbation_target_set, load_sober_target_set
from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import compute_observable_summary, multi_seed_summary
from lsd_thesis.simulator import load_regime_config, run_simulation
from lsd_thesis.utils import get_version_stamp, save_figure


class FitResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    initial_score: float
    best_score: float
    best_regime: RegimeConfig
    best_metrics: dict[str, float]
    best_fc_matrix: np.ndarray
    history: list[dict[str, float | int]]


LEGACY_METRIC_ALIASES: dict[str, str] = {
    "within_group_fc": "within_network_stability",
    "cross_group_fc": "cross_network_communication",
    "state_entropy": "entropy_diversity",
    "dynamic_fc_change": "metastability_proxy",
}


def _with_legacy_aliases(metrics: dict[str, float]) -> dict[str, float]:
    expanded = dict(metrics)
    for legacy_name, canonical_name in LEGACY_METRIC_ALIASES.items():
        expanded[legacy_name] = metrics[canonical_name]
    return expanded


def summarize_regime(
    graph: GraphConfig, regime: RegimeConfig
) -> tuple[dict[str, float], np.ndarray]:
    result = run_simulation(graph, regime)
    observable = compute_observable_summary(result.time_series, graph.modules)
    return _with_legacy_aliases(observable.metric_map()), observable.fc_matrix


def _score_against_targets(
    metric_summary: dict[str, float],
    fc_matrix: np.ndarray,
    target_set: SoberTargetSet,
) -> float:
    score = 0.0
    for metric_name, target in target_set.metrics.items():
        lookup_name = LEGACY_METRIC_ALIASES.get(metric_name, metric_name)
        observed = metric_summary[lookup_name]
        scale = max(abs(target.target), 1e-3)
        score += target.weight * ((observed - target.target) / scale) ** 2

    fc_error = np.linalg.norm(fc_matrix - target_set.fc_matrix) / fc_matrix.size
    return float(score + fc_error**2)


def _candidate_from_initial(
    initial_regime: RegimeConfig,
    rng: np.random.Generator,
    seed: int,
    iteration: int = 0,
) -> RegimeConfig:
    candidate = initial_regime.model_copy(deep=True)
    # Use iteration-derived seed so different candidates explore different noise trajectories
    candidate.simulation.seed = seed + iteration

    candidate.global_parameters.within_group_scale = float(rng.uniform(0.6, 1.8))
    candidate.global_parameters.cross_group_scale = float(rng.uniform(0.6, 2.8))
    candidate.global_parameters.constraint_scale = float(rng.uniform(0.05, 0.9))
    candidate.module_defaults.rigidity = float(rng.uniform(0.18, 0.75))
    candidate.module_defaults.barrier = float(rng.uniform(0.65, 1.35))
    candidate.module_defaults.temperature = float(rng.uniform(0.05, 0.25))
    candidate.module_defaults.tau = float(rng.uniform(0.65, 1.15))
    candidate.module_overrides["thalamic_gateway"] = ModuleParameterOverride(
        cross_scale=float(rng.uniform(1.0, 2.8)),
        barrier=float(rng.uniform(0.7, 1.3)),
        temperature=float(rng.uniform(0.05, 0.24)),
    )
    candidate.module_overrides["default_mode"] = ModuleParameterOverride(
        rigidity=float(rng.uniform(0.12, 0.6)),
        constraint_scale=float(rng.uniform(0.02, 0.6)),
    )
    candidate.module_overrides["executive_frontoparietal"] = ModuleParameterOverride(
        rigidity=float(rng.uniform(0.12, 0.65)),
        constraint_scale=float(rng.uniform(0.02, 0.7)),
    )
    return candidate


def fit_sober_regime(
    graph: GraphConfig,
    initial_regime: RegimeConfig,
    target_set: SoberTargetSet,
    iterations: int = 24,
    seed: int = 0,
) -> FitResult:
    rng = np.random.default_rng(seed)
    seeded_initial = initial_regime.model_copy(deep=True)
    seeded_initial.simulation.seed = seed

    initial_metrics, initial_fc = summarize_regime(graph, seeded_initial)
    initial_score = _score_against_targets(initial_metrics, initial_fc, target_set)
    best_result = FitResult(
        initial_score=initial_score,
        best_score=initial_score,
        best_regime=seeded_initial,
        best_metrics=initial_metrics,
        best_fc_matrix=initial_fc,
        history=[
            {
                "iteration": 0,
                "score": initial_score,
                **initial_metrics,
            }
        ],
    )

    for iteration in range(1, iterations + 1):
        candidate = _candidate_from_initial(initial_regime, rng, seed=seed, iteration=iteration)
        metrics, fc_matrix = summarize_regime(graph, candidate)
        score = _score_against_targets(metrics, fc_matrix, target_set)
        best_result.history.append({"iteration": iteration, "score": score, **metrics})
        if score < best_result.best_score:
            best_result.best_score = score
            best_result.best_regime = candidate
            best_result.best_metrics = metrics
            best_result.best_fc_matrix = fc_matrix

    return best_result


def _save_figure(figure: go.Figure, path: Path) -> None:
    save_figure(figure, path)


def _metric_comparison_figure(
    best_metrics: dict[str, float], target_set: SoberTargetSet
) -> go.Figure:
    metric_names = list(target_set.metrics.keys())
    target_values = [target_set.metrics[name].target for name in metric_names]
    observed_values = [best_metrics[name] for name in metric_names]

    figure = go.Figure()
    figure.add_trace(go.Bar(name="target", x=metric_names, y=target_values, marker_color="#1d4ed8"))
    figure.add_trace(
        go.Bar(name="fitted", x=metric_names, y=observed_values, marker_color="#059669")
    )
    figure.update_layout(
        barmode="group",
        template="plotly_white",
        title="Sober Target Metrics vs Fitted Metrics",
    )
    return figure


def _fc_figure(fc_matrix: np.ndarray, modules: tuple[str, ...], title: str) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Heatmap(
                z=fc_matrix,
                x=list(modules),
                y=list(modules),
                zmin=-1.0,
                zmax=1.0,
                colorscale="RdBu",
            )
        ]
    )
    figure.update_layout(title=title, template="plotly_white")
    return figure


def _history_figure(history: list[dict[str, float | int]]) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Scatter(
                x=[row["iteration"] for row in history],
                y=[row["score"] for row in history],
                mode="lines+markers",
                line={"color": "#7c3aed"},
                name="score",
            )
        ]
    )
    figure.update_layout(title="Sober Fit Search History", template="plotly_white")
    return figure


def _infer_repo_root(graph_path: str | Path) -> Path:
    return Path(graph_path).resolve().parents[2]


def _build_empirical_provenance(
    *,
    dataset_anchor: str,
    manifest: Any,
    target_paths: dict[str, str],
    viewer_cache_paths: dict[str, str] | None,
) -> dict[str, Any]:
    runs = [run.relative_path for run in manifest.runs]
    sessions = sorted({run.session for run in manifest.runs})
    return {
        "dataset_id": DS003059_DATASET_ID,
        "dataset_version": DS003059_VERSION,
        "dataset_anchor": dataset_anchor,
        "subjects": list(manifest.subjects),
        "subject_count": len(manifest.subjects),
        "sessions": sessions,
        "runs": runs,
        "run_count": len(runs),
        "target_paths": target_paths,
        "viewer_cache_paths": viewer_cache_paths or {},
        "notes": [
            "Canonical Stage 2 provenance reflects the full empirical cohort used to derive the fitted targets.",
            "The single-subject MVP subset helper is written separately as a convenience bootstrap artifact and is not the canonical fit provenance.",
        ],
    }


def generate_stage_2_outputs(
    graph_path: str | Path,
    baseline_path: str | Path,
    target_path: str | Path,
    output_dir: str | Path,
    report_path: str | Path,
    iterations: int = 24,
    seed: int = 0,
    dataset_dir: str | Path | None = None,
    subjects: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    repo_root = _infer_repo_root(graph_path)
    graph = load_graph_config(graph_path)
    regime = load_regime_config(baseline_path)
    empirical_outputs: dict[str, Any] | None = None
    resolved_target_path = Path(target_path)
    if dataset_dir is not None:
        empirical_outputs = generate_empirical_targets(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            subjects=subjects,
        )
        resolved_target_path = Path(empirical_outputs["sober_target_path"])

    target_set = load_sober_target_set(resolved_target_path)
    atlas_audit = build_atlas_mapping_audit(include_voxel_counts=True, allow_fetch=False)
    fit_result = fit_sober_regime(graph, regime, target_set, iterations=iterations, seed=seed)
    subset_spec = ds003059_subset_spec()
    mvp_helper = {
        "subset_spec": subset_spec.model_dump(),
        "download_command": build_openneuro_download_command(subset_spec, "data/ds003059_mvp"),
        "notes": [
            "This is a convenience bootstrap helper for a minimal ds003059 subset.",
            "It is not the canonical provenance record for Stage 2 empirical fitting.",
        ],
    }

    output_path = Path(output_dir)
    figures_path = output_path / "figures"
    atlas_audit_path = output_path / "atlas_mapping_audit.json"
    figures_path.mkdir(parents=True, exist_ok=True)

    _save_figure(
        _metric_comparison_figure(fit_result.best_metrics, target_set),
        figures_path / "sober_metric_fit.html",
    )
    _save_figure(
        _fc_figure(target_set.fc_matrix, graph.modules, "Curated Sober FC Target"),
        figures_path / "target_sober_fc_matrix.html",
    )
    _save_figure(
        _fc_figure(fit_result.best_fc_matrix, graph.modules, "Fitted Sober FC Matrix"),
        figures_path / "fitted_sober_fc_matrix.html",
    )
    _save_figure(
        _history_figure(fit_result.history),
        figures_path / "sober_fit_history.html",
    )

    viewer_cache_paths: dict[str, str] | None = None
    gallery_outputs: list[dict[str, str]] = []
    empirical_data_quality: dict[str, Any] | None = None
    viewer_root = output_path / "empirical_viewer"
    existing_group_overview = viewer_root / "group_overview.json"
    existing_subject_index = viewer_root / "subject_index.json"
    existing_subject_views = viewer_root / "subject_views"
    if (
        empirical_outputs is not None
        and existing_group_overview.exists()
        and existing_subject_index.exists()
        and existing_subject_views.exists()
    ):
        viewer_cache_paths = {
            "group_overview_path": str(existing_group_overview),
            "subject_index_path": str(existing_subject_index),
            "subject_views_dir": str(existing_subject_views),
        }
        cached_overview = json.loads(existing_group_overview.read_text(encoding="utf-8"))
        gallery_outputs = list(cached_overview.get("gallery", []))
    elif empirical_outputs is not None and dataset_dir is not None:
        run_views = build_empirical_run_views_from_records(
            empirical_outputs["run_records"],
            dataset_dir=dataset_dir,
            output_dir=output_path,
            modules=graph.modules,
        )
        viewer_payloads = build_empirical_viewer_payloads(run_views, modules=graph.modules)
        gallery_outputs = generate_empirical_gallery(
            viewer_payloads["group_overview"],
            figures_dir=figures_path,
        )
        viewer_payloads["group_overview"]["gallery"] = gallery_outputs
        viewer_cache_paths = write_empirical_viewer_cache(
            viewer_payloads,
            output_dir=output_path / "empirical_viewer",
        )
    if empirical_outputs is not None:
        empirical_delta_set = load_perturbation_target_set(empirical_outputs["perturbation_target_path"])
        literature_target_path = repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml"
        literature_delta_set = (
            load_perturbation_target_set(literature_target_path)
            if literature_target_path.exists()
            else None
        )
        empirical_data_quality = build_empirical_data_quality_payload(
            records=list(empirical_outputs["run_records"]),
            empirical_deltas=empirical_delta_set.target_deltas,
            literature_deltas=literature_delta_set.target_deltas if literature_delta_set else None,
        )

    summary = {
        "dataset_anchor": target_set.dataset_anchor,
        "initial_score": fit_result.initial_score,
        "best_score": fit_result.best_score,
        "best_metrics": fit_result.best_metrics,
        "best_parameters": {
            "within_group_scale": fit_result.best_regime.global_parameters.within_group_scale,
            "cross_group_scale": fit_result.best_regime.global_parameters.cross_group_scale,
            "constraint_scale": fit_result.best_regime.global_parameters.constraint_scale,
            "rigidity": fit_result.best_regime.module_defaults.rigidity,
            "barrier": fit_result.best_regime.module_defaults.barrier,
            "temperature": fit_result.best_regime.module_defaults.temperature,
            "tau": fit_result.best_regime.module_defaults.tau,
        },
        "target_path": str(resolved_target_path),
        "atlas_mapping_audit_path": str(atlas_audit_path),
    }

    # Multi-seed uncertainty for the best regime
    best_mean, best_std = multi_seed_summary(graph, fit_result.best_regime, n_seeds=5, base_seed=seed)
    summary["best_metrics_mean"] = best_mean
    summary["best_metrics_std"] = best_std
    summary["version_stamp"] = get_version_stamp(repo_root)

    if empirical_outputs is not None:
        summary["empirical_subjects"] = list(empirical_outputs["manifest"].subjects)
        summary["empirical_run_count"] = len(empirical_outputs["manifest"].runs)
        summary["perturbation_target_path"] = empirical_outputs["perturbation_target_path"]
        summary["empirical_provenance"] = _build_empirical_provenance(
            dataset_anchor=target_set.dataset_anchor,
            manifest=empirical_outputs["manifest"],
            target_paths={
                "sober": str(resolved_target_path),
                "perturbation": empirical_outputs["perturbation_target_path"],
            },
            viewer_cache_paths=viewer_cache_paths,
        )
        if empirical_data_quality is not None:
            summary["empirical_data_quality_path"] = str(output_path / "empirical_data_quality.json")
    if viewer_cache_paths is not None:
        summary["empirical_viewer"] = viewer_cache_paths
        summary["empirical_gallery"] = gallery_outputs

    output_path.mkdir(parents=True, exist_ok=True)
    atlas_audit_path.write_text(
        json.dumps(atlas_audit, indent=2),
        encoding="utf-8",
    )
    if empirical_data_quality is not None:
        (output_path / "empirical_data_quality.json").write_text(
            json.dumps(empirical_data_quality, indent=2),
            encoding="utf-8",
        )
    (output_path / "stage_2_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (output_path / "ds003059_mvp_subset_plan.json").write_text(
        json.dumps(mvp_helper, indent=2),
        encoding="utf-8",
    )

    report_lines = [
        "# Stage 2 Report",
        "",
        "## Plan",
        "",
        "- Load actual ds003059 resting-state targets when a dataset directory is provided; otherwise fall back to the placeholder config.",
        "- Fit the sober baseline regime with a transparent random search around the baseline config.",
        "- Save the canonical full empirical cohort provenance and keep the MVP subset helper as a separate convenience bootstrap artifact.",
        "",
        "## What Is Fitted Exactly",
        "",
        "- Within-network stability",
        "- Cross-network communication",
        "- Thalamic coupling",
        "- Hierarchical compression",
        "- Entropy / diversity",
        "- Switching rate",
        "- Dynamic FC change / metastability proxy",
        "- Effective barrier proxy",
        "- The sober FC target matrix",
        "",
        "## What Is Only Qualitatively Anchored",
        "",
        "- The atlas-to-module mapping, which is a transparent coarse anatomical proxy rather than a canonical network parcellation.",
        "- The interpretation of these summary metrics as macro-level signatures rather than direct mechanistic readouts.",
        "- The sign agreement between the current 8-module ds003059 extraction and the literature-style target file.",
        "",
        "## Empirical Sign Check",
        "",
        "- The current paired ds003059 extraction supports increased cross-network communication and thalamic coupling under this proxy.",
        "- It conflicts with the literature-style target signs for `within_network_stability`, `entropy_diversity`, and `metastability_proxy`.",
        "- Stage 3 and Stage 4 should therefore be presented as mismatch analysis under one coarse anatomical proxy.",
        "",
        "## Atlas Mapping Audit",
        "",
        f"- Atlas audit artifact: `{atlas_audit_path.name}`",
        f"- Assigned atlas voxels: `{atlas_audit['assigned_voxels'] or 'not computed in cached fast run'}`",
        f"- Overlapping source labels: `{len(atlas_audit['overlaps'])}`",
        "",
        "## Empirical Data Quality",
        "",
        f"- Data quality artifact: `{'empirical_data_quality.json' if empirical_data_quality else 'not available'}`",
        f"- Paired subjects: `{empirical_data_quality['paired_subject_count'] if empirical_data_quality else 'n/a'}`",
        f"- Complete subjects: `{empirical_data_quality['complete_subject_count'] if empirical_data_quality else 'n/a'}`",
        f"- Sign conflicts: `{len(empirical_data_quality['sign_conflicts']) if empirical_data_quality else 'n/a'}`",
        "",
        "## Empirical Viewer Outputs",
        "",
        "- Group-average empirical overview cache",
        "- Subject/run paired empirical detail cache",
        "- Precomputed empirical gallery figures for traces, FC, and delta summaries",
        "",
        "## Results",
        "",
        f"- Initial score: {fit_result.initial_score:.4f}",
        f"- Best score: {fit_result.best_score:.4f}",
        f"- Best within-network stability: {fit_result.best_metrics['within_network_stability']:.4f}",
        f"- Best cross-network communication: {fit_result.best_metrics['cross_network_communication']:.4f}",
        f"- Best entropy / diversity: {fit_result.best_metrics['entropy_diversity']:.4f}",
        f"- Best switching rate: {fit_result.best_metrics['switching_rate']:.4f}",
        "",
        "## Critical Review",
        "",
        "- The fitting loop is intentionally small and transparent, so it should be treated as calibration rather than optimization proof.",
        "- If actual ds003059 targets were used, the remaining mismatch is now a model limitation rather than a placeholder-data limitation.",
        "- The full empirical cohort provenance is the canonical reproducibility record for this run.",
        "- The saved MVP subset helper is a convenience bootstrap artifact and is not the canonical fit provenance.",
        "- The empirical viewer uses downsampled window previews for interpretability and speed; it is not a diagnostic-grade imaging viewer.",
        "- The current Harvard-Oxford macro-module mapping contains overlapping source labels; "
        "the label-image builder resolves those overlaps by assignment order.",
        "",
        "## Provenance",
        "",
        "- The canonical Stage 2 provenance comes from the full empirical cohort used to derive the fitted targets.",
        "- The MVP subset helper is stored separately as a convenience bootstrap artifact for lightweight ds003059 setup.",
        "",
    ]
    Path(report_path).write_text("\n".join(report_lines), encoding="utf-8")
    return summary
