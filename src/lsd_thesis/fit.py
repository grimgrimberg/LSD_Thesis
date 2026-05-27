from __future__ import annotations

import json
from collections.abc import Sequence
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
from lsd_thesis.subject_split import (
    SubjectSplit,
    build_no_subject_validation_boundary,
    build_subject_validation_boundary,
    load_subject_split_file,
)
from lsd_thesis.utils import get_version_stamp, save_figure


class FitResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    initial_score: float
    best_score: float
    selection_score_std: float = 0.0
    selected_iteration: int = 0
    best_regime: RegimeConfig
    best_metrics: dict[str, float]
    best_metrics_std: dict[str, float] = {}
    best_fc_matrix: np.ndarray
    history: list[dict[str, Any]]
    seed_plan: dict[str, Any] = {}
    selection_diagnostics: list[dict[str, Any]] = []
    validation_score_mean: float | None = None
    validation_score_std: float | None = None
    validation_metrics_mean: dict[str, float] = {}
    validation_metrics_std: dict[str, float] = {}


class FitSeedPlan(BaseModel):
    proposal_seed: int
    selection_seeds: tuple[int, ...]
    validation_seeds: tuple[int, ...]
    selection_mode: str
    validation_mode: str


def _coerce_seed_tuple(seed_values: Sequence[int] | None, *, field_name: str) -> tuple[int, ...]:
    if seed_values is None:
        return ()
    seeds = tuple(int(seed) for seed in seed_values)
    if not seeds:
        raise ValueError(f"{field_name} must contain at least one seed when provided.")
    return seeds


def build_fit_seed_plan(
    proposal_seed: int,
    selection_seeds: Sequence[int] | None = None,
    validation_seeds: Sequence[int] | None = None,
) -> FitSeedPlan:
    selection_tuple = _coerce_seed_tuple(selection_seeds, field_name="selection_seeds")
    validation_tuple = _coerce_seed_tuple(validation_seeds, field_name="validation_seeds")
    overlap = set(selection_tuple).intersection(validation_tuple)
    if overlap:
        raise ValueError(
            "selection_seeds and validation_seeds must be disjoint; "
            f"overlap detected: {sorted(overlap)}."
        )
    if selection_seeds is None:
        selection_mode = "single_candidate_seed"
    elif len(selection_tuple) == 1:
        selection_mode = "single_explicit_seed"
    else:
        selection_mode = "multi_seed_mean"
    validation_mode = "not_run" if not validation_tuple else "disjoint_seed_panel"
    return FitSeedPlan(
        proposal_seed=int(proposal_seed),
        selection_seeds=selection_tuple,
        validation_seeds=validation_tuple,
        selection_mode=selection_mode,
        validation_mode=validation_mode,
    )


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


def _metric_panel_mean_std(metric_rows: list[dict[str, float]]) -> tuple[dict[str, float], dict[str, float]]:
    metric_names = metric_rows[0].keys()
    mean_metrics = {
        name: float(np.mean([row[name] for row in metric_rows]))
        for name in metric_names
    }
    std_metrics = {
        name: float(np.std([row[name] for row in metric_rows]))
        for name in metric_names
    }
    return mean_metrics, std_metrics


def _selection_seeds_for_candidate(seed_plan: FitSeedPlan, candidate_seed: int) -> tuple[int, ...]:
    return seed_plan.selection_seeds or (candidate_seed,)


def _evaluate_regime_seed_panel(
    graph: GraphConfig,
    regime: RegimeConfig,
    target_set: SoberTargetSet,
    seeds: tuple[int, ...],
) -> tuple[
    float,
    float,
    dict[str, float],
    dict[str, float],
    np.ndarray,
    list[dict[str, float | int]],
]:
    metric_rows: list[dict[str, float]] = []
    fc_matrices: list[np.ndarray] = []
    seed_scores: list[dict[str, float | int]] = []
    for panel_seed in seeds:
        seeded_regime = regime.model_copy(deep=True)
        seeded_regime.simulation.seed = int(panel_seed)
        metrics, fc_matrix = summarize_regime(graph, seeded_regime)
        score = _score_against_targets(metrics, fc_matrix, target_set)
        metric_rows.append(metrics)
        fc_matrices.append(fc_matrix)
        seed_scores.append({"seed": int(panel_seed), "score": score})

    scores = [float(row["score"]) for row in seed_scores]
    mean_metrics, std_metrics = _metric_panel_mean_std(metric_rows)
    return (
        float(np.mean(scores)),
        float(np.std(scores)),
        mean_metrics,
        std_metrics,
        np.mean(fc_matrices, axis=0),
        seed_scores,
    )


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
    selection_seeds: Sequence[int] | None = None,
    validation_seeds: Sequence[int] | None = None,
) -> FitResult:
    rng = np.random.default_rng(seed)
    seed_plan = build_fit_seed_plan(
        proposal_seed=seed,
        selection_seeds=selection_seeds,
        validation_seeds=validation_seeds,
    )
    seeded_initial = initial_regime.model_copy(deep=True)
    seeded_initial.simulation.seed = seed

    (
        initial_score,
        initial_score_std,
        initial_metrics,
        initial_metrics_std,
        initial_fc,
        initial_seed_scores,
    ) = _evaluate_regime_seed_panel(
        graph,
        seeded_initial,
        target_set,
        _selection_seeds_for_candidate(seed_plan, seed),
    )
    best_result = FitResult(
        initial_score=initial_score,
        best_score=initial_score,
        selection_score_std=initial_score_std,
        selected_iteration=0,
        best_regime=seeded_initial,
        best_metrics=initial_metrics,
        best_metrics_std=initial_metrics_std,
        best_fc_matrix=initial_fc,
        history=[
            {
                "iteration": 0,
                "score": initial_score,
                "score_std": initial_score_std,
                "seed_count": len(initial_seed_scores),
                **initial_metrics,
            }
        ],
        seed_plan=seed_plan.model_dump(),
        selection_diagnostics=[
            {
                "iteration": 0,
                "candidate_seed": seed,
                "score_mean": initial_score,
                "score_std": initial_score_std,
                "seed_scores": initial_seed_scores,
            }
        ],
    )

    for iteration in range(1, iterations + 1):
        candidate = _candidate_from_initial(initial_regime, rng, seed=seed, iteration=iteration)
        candidate_seed = int(candidate.simulation.seed)
        panel_seeds = _selection_seeds_for_candidate(seed_plan, candidate_seed)
        (
            score,
            score_std,
            metrics,
            metrics_std,
            fc_matrix,
            seed_scores,
        ) = _evaluate_regime_seed_panel(graph, candidate, target_set, panel_seeds)
        best_result.history.append(
            {
                "iteration": iteration,
                "score": score,
                "score_std": score_std,
                "seed_count": len(seed_scores),
                **metrics,
            }
        )
        best_result.selection_diagnostics.append(
            {
                "iteration": iteration,
                "candidate_seed": candidate_seed,
                "score_mean": score,
                "score_std": score_std,
                "seed_scores": seed_scores,
            }
        )
        if score < best_result.best_score or (
            np.isclose(score, best_result.best_score) and score_std < best_result.selection_score_std
        ):
            best_result.best_score = score
            best_result.selection_score_std = score_std
            best_result.selected_iteration = iteration
            best_result.best_regime = candidate
            best_result.best_metrics = metrics
            best_result.best_metrics_std = metrics_std
            best_result.best_fc_matrix = fc_matrix

    if seed_plan.validation_seeds:
        (
            validation_score_mean,
            validation_score_std,
            validation_metrics_mean,
            validation_metrics_std,
            _validation_fc,
            _validation_seed_scores,
        ) = _evaluate_regime_seed_panel(
            graph,
            best_result.best_regime,
            target_set,
            seed_plan.validation_seeds,
        )
        best_result.validation_score_mean = validation_score_mean
        best_result.validation_score_std = validation_score_std
        best_result.validation_metrics_mean = validation_metrics_mean
        best_result.validation_metrics_std = validation_metrics_std

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
    cache_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runs = [run.relative_path for run in manifest.runs]
    sessions = sorted({run.session for run in manifest.runs})
    provenance = {
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
    if cache_metadata is not None:
        provenance["cache_schema_version"] = cache_metadata.get("schema_version")
        provenance["cache_fingerprint"] = cache_metadata.get("cache_fingerprint")
        provenance["cache_created_at_utc"] = cache_metadata.get("created_at_utc")
        provenance["cache_artifact_hashes"] = cache_metadata.get("artifact_hashes", {})
        provenance["preprocessing_qc"] = cache_metadata.get("preprocessing_qc", {})
    return provenance


def _default_stage2_selection_seeds(seed: int) -> tuple[int, ...]:
    return tuple(seed + 100 + index for index in range(3))


def _default_stage2_validation_seeds(seed: int) -> tuple[int, ...]:
    return tuple(seed + 1000 + index for index in range(5))


def _build_empirical_validation_boundary(
    *,
    target_set: SoberTargetSet,
    empirical_outputs: dict[str, Any] | None,
    seed: int,
    subject_split: SubjectSplit | None = None,
    subject_split_path: str | Path | None = None,
) -> dict[str, Any]:
    if subject_split is not None:
        return build_subject_validation_boundary(
            subject_split,
            split_file_path=subject_split_path,
            held_out_validation_completed=False,
            selection_data_source=f"{target_set.dataset_anchor} (selection/calibration subset)",
            validation_data_source=(
                "Held-out validation subject subset; Stage 3 held-out empirical validation has not yet been run."
            ),
            selection_random_seed=seed,
        )
    subjects = (
        list(empirical_outputs["manifest"].subjects)
        if empirical_outputs is not None and "manifest" in empirical_outputs
        else []
    )
    return build_no_subject_validation_boundary(
        selection_data_source=target_set.dataset_anchor,
        selection_subject_count=len(subjects) if subjects else None,
        selection_random_seed=seed,
    )


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
    selection_seeds: Sequence[int] | None = None,
    validation_seeds: Sequence[int] | None = None,
    subject_split_path: str | Path | None = None,
    build_viewer: bool = True,
    runs: Sequence[str] | None = None,
    include_music: bool = False,
) -> dict[str, Any]:
    repo_root = _infer_repo_root(graph_path)
    graph = load_graph_config(graph_path)
    regime = load_regime_config(baseline_path)
    empirical_outputs: dict[str, Any] | None = None
    heldout_empirical_outputs: dict[str, Any] | None = None
    resolved_target_path = Path(target_path)
    output_path = Path(output_dir)
    subject_split = load_subject_split_file(subject_split_path) if subject_split_path is not None else None
    if dataset_dir is not None:
        empirical_outputs = generate_empirical_targets(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            subjects=subject_split.selection_subjects if subject_split is not None else subjects,
            runs=runs,
            include_music=include_music,
        )
        resolved_target_path = Path(empirical_outputs["sober_target_path"])
        if subject_split is not None and subject_split.is_approved:
            heldout_empirical_outputs = generate_empirical_targets(
                dataset_dir=dataset_dir,
                output_dir=output_path / "heldout_validation",
                subjects=subject_split.validation_subjects,
                runs=runs,
                include_music=include_music,
            )

    target_set = load_sober_target_set(resolved_target_path)
    atlas_audit = build_atlas_mapping_audit(include_voxel_counts=True, allow_fetch=False)
    stage_selection_seeds = (
        tuple(int(item) for item in selection_seeds)
        if selection_seeds is not None
        else _default_stage2_selection_seeds(seed)
    )
    stage_validation_seeds = (
        tuple(int(item) for item in validation_seeds)
        if validation_seeds is not None
        else _default_stage2_validation_seeds(seed)
    )
    fit_result = fit_sober_regime(
        graph,
        regime,
        target_set,
        iterations=iterations,
        seed=seed,
        selection_seeds=stage_selection_seeds,
        validation_seeds=stage_validation_seeds,
    )
    subset_spec = ds003059_subset_spec()
    mvp_helper = {
        "subset_spec": subset_spec.model_dump(),
        "download_command": build_openneuro_download_command(subset_spec, "data/ds003059_mvp"),
        "notes": [
            "This is a convenience bootstrap helper for a minimal ds003059 subset.",
            "It is not the canonical provenance record for Stage 2 empirical fitting.",
        ],
    }

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
        build_viewer
        and
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
    elif build_viewer and empirical_outputs is not None and dataset_dir is not None:
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

    empirical_validation_boundary = _build_empirical_validation_boundary(
        target_set=target_set,
        empirical_outputs=empirical_outputs,
        seed=seed,
        subject_split=subject_split,
        subject_split_path=subject_split_path,
    )
    summary = {
        "dataset_anchor": target_set.dataset_anchor,
        "initial_score": fit_result.initial_score,
        "best_score": fit_result.best_score,
        "selection_score_std": fit_result.selection_score_std,
        "selected_iteration": fit_result.selected_iteration,
        "best_metrics": fit_result.best_metrics,
        "best_metrics_std": fit_result.best_metrics_std,
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
        "fit_seed_plan": fit_result.seed_plan
        or build_fit_seed_plan(
            seed,
            selection_seeds=stage_selection_seeds,
            validation_seeds=stage_validation_seeds,
        ).model_dump(),
        "model_selection_diagnostics": {
            "selected_iteration": fit_result.selected_iteration,
            "selection_score_mean": fit_result.best_score,
            "selection_score_std": fit_result.selection_score_std,
            "selection_seed_count": len(stage_selection_seeds),
            "candidate_count": len(fit_result.history),
            "selection_mode": (
                fit_result.seed_plan.get("selection_mode")
                if fit_result.seed_plan
                else "multi_seed_mean"
            ),
            "history": fit_result.selection_diagnostics,
        },
        "empirical_validation_boundary": empirical_validation_boundary,
    }
    if heldout_empirical_outputs is not None:
        summary["heldout_validation_target_paths"] = {
            "status": "prepared_for_stage3_not_completed",
            "sober": heldout_empirical_outputs["sober_target_path"],
            "perturbation": heldout_empirical_outputs["perturbation_target_path"],
            "subject_count": len(heldout_empirical_outputs["manifest"].subjects),
            "run_count": len(heldout_empirical_outputs["manifest"].runs),
            "subjects": list(heldout_empirical_outputs["manifest"].subjects),
            "claim_guardrail": (
                "Held-out validation target artifacts are prepared for Stage 3, but Stage 2 does not "
                "by itself complete held-out empirical validation."
            ),
        }
        empirical_validation_boundary["validation_data_source"] = (
            "Stage 2 held-out validation target cache reserved for Stage 3 empirical evaluation."
        )

    # Validation-panel uncertainty for the best regime. The fallback keeps older test doubles usable.
    if fit_result.validation_metrics_mean:
        best_mean = fit_result.validation_metrics_mean
        best_std = fit_result.validation_metrics_std
    else:
        best_mean, best_std = multi_seed_summary(
            graph,
            fit_result.best_regime,
            n_seeds=len(stage_validation_seeds),
            base_seed=stage_validation_seeds[0],
        )
    summary["best_metrics_mean"] = best_mean
    summary["best_metrics_std"] = best_std
    summary["multi_seed_summary"] = {
        "role": "validation_seed_panel",
        "seeds": list(stage_validation_seeds),
        "seed_count": len(stage_validation_seeds),
        "mean_metrics": best_mean,
        "std_metrics": best_std,
        "score_mean": fit_result.validation_score_mean,
        "score_std": fit_result.validation_score_std,
        "selection_validation_seed_overlap": bool(
            set(stage_selection_seeds).intersection(stage_validation_seeds)
        ),
    }
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
            cache_metadata=empirical_outputs.get("cache_metadata"),
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
        f"- Best selection score: {fit_result.best_score:.4f} ± {fit_result.selection_score_std:.4f}",
        f"- Selected iteration: {fit_result.selected_iteration}",
        f"- Selection seeds: `{list(stage_selection_seeds)}`",
        f"- Validation seeds: `{list(stage_validation_seeds)}`",
        f"- Validation score: `{fit_result.validation_score_mean if fit_result.validation_score_mean is not None else 'n/a'}`",
        f"- Best within-network stability: {fit_result.best_metrics['within_network_stability']:.4f}",
        f"- Best cross-network communication: {fit_result.best_metrics['cross_network_communication']:.4f}",
        f"- Best entropy / diversity: {fit_result.best_metrics['entropy_diversity']:.4f}",
        f"- Best switching rate: {fit_result.best_metrics['switching_rate']:.4f}",
        "",
        "## Empirical Validation Boundary",
        "",
        (
            "- Held-out empirical validation: `split configured, not yet completed`"
            if subject_split is not None
            else "- Held-out empirical validation: `not configured`"
        ),
        (
            "- Stage 2 calibration uses only the split selection subjects when a split file is provided."
            if subject_split is not None
            else "- Stage 2 uses available empirical targets for calibration/selection, not for an independent held-out claim."
        ),
        "- Stage 2b reliability summaries should be presented as target stability diagnostics, not as held-out model validation.",
        "",
        "## Critical Review",
        "",
        "- The fitting loop is intentionally small and transparent, so it should be treated as calibration rather than optimization proof.",
        "- Multi-seed selection reduces single-realization dependence when configured, but it does not by itself create a held-out empirical test.",
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
