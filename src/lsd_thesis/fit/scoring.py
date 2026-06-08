from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from lsd_thesis.core import GraphConfig, ModuleParameterOverride, RegimeConfig
from lsd_thesis.data.targets import SoberTargetSet
from lsd_thesis.metrics import compute_observable_summary
from lsd_thesis.simulator import run_simulation

from .models import FitResult, FitSeedPlan
from .seeds import build_fit_seed_plan

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
