from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import numpy as np
import plotly.graph_objects as go
from pydantic import BaseModel

from lsd_thesis.core import GraphConfig, RegimeConfig
from lsd_thesis.data.targets import (
    PerturbationTargetSet,
    load_perturbation_target_set,
    load_sober_target_set,
)
from lsd_thesis.fit import fit_sober_regime
from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import compute_observable_summary
from lsd_thesis.simulator import load_regime_config, run_simulation
from lsd_thesis.subject_split import build_subject_validation_boundary, load_subject_split_file
from lsd_thesis.utils import confidence_weight, get_version_stamp, save_figure

MechanismName = Literal[
    "more_cross_talk",
    "less_hierarchical_constraint",
    "more_stochasticity",
    "lower_switching_barrier",
]

MECHANISMS: tuple[MechanismName, ...] = (
    "more_cross_talk",
    "less_hierarchical_constraint",
    "more_stochasticity",
    "lower_switching_barrier",
)


class PerturbationEvaluation(BaseModel):
    mechanism: MechanismName
    strength: float
    score: float
    delta_metrics: dict[str, float]
    perturbed_metrics: dict[str, float]


class RobustPerturbationEvaluation(BaseModel):
    mechanism: MechanismName
    strength: float
    seed_count: int
    score_mean: float
    score_std: float
    delta_metrics_mean: dict[str, float]
    delta_metrics_std: dict[str, float]
    perturbed_metrics_mean: dict[str, float]
    sign_agreement_fraction: float


def _confidence_weight(label: str) -> float:
    return confidence_weight(label)


def summarize_perturbation_metrics(graph: GraphConfig, regime: RegimeConfig) -> dict[str, float]:
    result = run_simulation(graph, regime)
    observable = compute_observable_summary(result.time_series, graph.modules)
    return observable.metric_map()


def apply_mechanism(
    sober_regime: RegimeConfig,
    mechanism: MechanismName,
    strength: float,
) -> RegimeConfig:
    perturbed = sober_regime.model_copy(deep=True)
    if mechanism == "more_cross_talk":
        perturbed.global_parameters.cross_group_scale *= 1.0 + strength
    elif mechanism == "less_hierarchical_constraint":
        perturbed.global_parameters.constraint_scale *= max(0.0, 1.0 - strength)
    elif mechanism == "more_stochasticity":
        perturbed.module_defaults.temperature *= 1.0 + strength
    elif mechanism == "lower_switching_barrier":
        perturbed.module_defaults.barrier *= max(0.0, 1.0 - strength)
    return perturbed


def _score_delta(
    delta_metrics: dict[str, float],
    target_set: PerturbationTargetSet,
) -> float:
    score = 0.0
    for metric_name, target_delta in target_set.target_deltas.items():
        observed = delta_metrics[metric_name]
        scale = max(abs(target_delta), 1e-3)
        weight = _confidence_weight(target_set.confidence.get(metric_name, "moderate"))
        score += weight * ((observed - target_delta) / scale) ** 2
    return float(score)


def rank_perturbation_mechanisms(
    graph: GraphConfig,
    sober_regime: RegimeConfig,
    target_set: PerturbationTargetSet,
    strengths: tuple[float, ...] = (0.05, 0.1, 0.2, 0.3),
) -> list[PerturbationEvaluation]:
    sober_metrics = summarize_perturbation_metrics(graph, sober_regime)
    evaluations: list[PerturbationEvaluation] = []

    for mechanism in MECHANISMS:
        for strength in strengths:
            perturbed = apply_mechanism(sober_regime, mechanism, strength)
            perturbed_metrics = summarize_perturbation_metrics(graph, perturbed)
            delta_metrics = {
                key: perturbed_metrics[key] - sober_metrics[key] for key in target_set.target_deltas
            }
            evaluations.append(
                PerturbationEvaluation(
                    mechanism=mechanism,
                    strength=strength,
                    score=_score_delta(delta_metrics, target_set),
                    delta_metrics=delta_metrics,
                    perturbed_metrics=perturbed_metrics,
                )
            )

    return sorted(evaluations, key=lambda item: item.score)


def _mean_metric_rows(rows: list[dict[str, float]]) -> dict[str, float]:
    metric_names = list(rows[0].keys())
    return {
        name: float(np.mean([row[name] for row in rows]))
        for name in metric_names
    }


def _std_metric_rows(rows: list[dict[str, float]]) -> dict[str, float]:
    metric_names = list(rows[0].keys())
    ddof = 1 if len(rows) > 1 else 0
    return {
        name: float(np.std([row[name] for row in rows], ddof=ddof))
        for name in metric_names
    }


def _sign_agreement_fraction(delta_metrics: dict[str, float], target_set: PerturbationTargetSet) -> float:
    judged = 0
    aligned = 0
    for metric_name, target_delta in target_set.target_deltas.items():
        target_sign = np.sign(target_delta)
        observed_sign = np.sign(delta_metrics[metric_name])
        if target_sign == 0 or observed_sign == 0:
            continue
        judged += 1
        if target_sign == observed_sign:
            aligned += 1
    if judged == 0:
        return 0.0
    return float(aligned / judged)


def evaluate_perturbation_seed_panel(
    graph: GraphConfig,
    sober_regime: RegimeConfig,
    target_set: PerturbationTargetSet,
    mechanism: MechanismName,
    strength: float,
    seeds: tuple[int, ...],
) -> RobustPerturbationEvaluation:
    if not seeds:
        raise ValueError("At least one seed is required for a seed-panel evaluation.")

    score_rows: list[float] = []
    delta_rows: list[dict[str, float]] = []
    perturbed_rows: list[dict[str, float]] = []
    for seed in seeds:
        sober_variant = sober_regime.model_copy(deep=True)
        sober_variant.simulation.seed = seed
        perturbed_variant = apply_mechanism(sober_variant, mechanism, strength)
        perturbed_variant.simulation.seed = seed

        sober_metrics = summarize_perturbation_metrics(graph, sober_variant)
        perturbed_metrics = summarize_perturbation_metrics(graph, perturbed_variant)
        delta_metrics = {
            key: perturbed_metrics[key] - sober_metrics[key] for key in target_set.target_deltas
        }
        delta_rows.append(delta_metrics)
        perturbed_rows.append(perturbed_metrics)
        score_rows.append(_score_delta(delta_metrics, target_set))

    delta_mean = _mean_metric_rows(delta_rows)
    return RobustPerturbationEvaluation(
        mechanism=mechanism,
        strength=strength,
        seed_count=len(seeds),
        score_mean=float(np.mean(score_rows)),
        score_std=float(np.std(score_rows, ddof=1 if len(score_rows) > 1 else 0)),
        delta_metrics_mean=delta_mean,
        delta_metrics_std=_std_metric_rows(delta_rows),
        perturbed_metrics_mean=_mean_metric_rows(perturbed_rows),
        sign_agreement_fraction=_sign_agreement_fraction(delta_mean, target_set),
    )


def rank_perturbation_mechanisms_seed_panel(
    graph: GraphConfig,
    sober_regime: RegimeConfig,
    target_set: PerturbationTargetSet,
    strengths: tuple[float, ...],
    seeds: tuple[int, ...],
) -> list[RobustPerturbationEvaluation]:
    evaluations: list[RobustPerturbationEvaluation] = []
    for mechanism in MECHANISMS:
        for strength in strengths:
            evaluations.append(
                evaluate_perturbation_seed_panel(
                    graph=graph,
                    sober_regime=sober_regime,
                    target_set=target_set,
                    mechanism=mechanism,
                    strength=strength,
                    seeds=seeds,
                )
            )
    return sorted(evaluations, key=lambda item: item.score_mean)


def seed_noise_null_summary(
    graph: GraphConfig,
    sober_regime: RegimeConfig,
    target_set: PerturbationTargetSet,
    seeds: tuple[int, ...],
    comparison_seed_offset: int = 10_000,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("At least one seed is required for a null evaluation.")

    score_rows: list[float] = []
    delta_rows: list[dict[str, float]] = []
    for seed in seeds:
        reference = sober_regime.model_copy(deep=True)
        comparison = sober_regime.model_copy(deep=True)
        reference.simulation.seed = seed
        comparison.simulation.seed = seed + comparison_seed_offset
        reference_metrics = summarize_perturbation_metrics(graph, reference)
        comparison_metrics = summarize_perturbation_metrics(graph, comparison)
        delta_metrics = {
            key: comparison_metrics[key] - reference_metrics[key]
            for key in target_set.target_deltas
        }
        delta_rows.append(delta_metrics)
        score_rows.append(_score_delta(delta_metrics, target_set))

    return {
        "seed_count": len(seeds),
        "comparison_seed_offset": comparison_seed_offset,
        "score_mean": float(np.mean(score_rows)),
        "score_std": float(np.std(score_rows, ddof=1 if len(score_rows) > 1 else 0)),
        "delta_metrics_mean": _mean_metric_rows(delta_rows),
        "delta_metrics_std": _std_metric_rows(delta_rows),
    }


def _save_figure(figure: go.Figure, path: Path) -> None:
    save_figure(figure, path)


def _ranking_figure(ranking: list[PerturbationEvaluation]) -> go.Figure:
    labels = [f"{item.mechanism}@{item.strength:.2f}" for item in ranking]
    figure = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=[item.score for item in ranking],
                marker_color="#7c3aed",
            )
        ]
    )
    figure.update_layout(
        title="Mechanism-Proxy Ranking Against Empirical Delta Targets",
        template="plotly_white",
        xaxis_title="Mechanism @ strength",
        yaxis_title="Delta mismatch score",
    )
    return figure


def _delta_comparison_figure(
    evaluation: PerturbationEvaluation,
    target_set: PerturbationTargetSet,
) -> go.Figure:
    metric_names = list(target_set.target_deltas.keys())
    target_values = [target_set.target_deltas[name] for name in metric_names]
    model_values = [evaluation.delta_metrics[name] for name in metric_names]

    figure = go.Figure()
    figure.add_trace(go.Bar(name="empirical target", x=metric_names, y=target_values))
    figure.add_trace(go.Bar(name="model delta", x=metric_names, y=model_values))
    figure.update_layout(
        barmode="group",
        template="plotly_white",
        title=f"Best Mechanism Delta Match: {evaluation.mechanism} @ {evaluation.strength:.2f}",
    )
    return figure


def _robust_ranking_figure(ranking: list[RobustPerturbationEvaluation]) -> go.Figure:
    labels = [f"{item.mechanism}@{item.strength:.2f}" for item in ranking]
    figure = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=[item.score_mean for item in ranking],
                error_y={
                    "type": "data",
                    "array": [item.score_std for item in ranking],
                    "visible": True,
                },
                marker_color="#0f766e",
            )
        ]
    )
    figure.update_layout(
        title="Seed-Panel Mechanism-Proxy Ranking Against Empirical Delta Targets",
        template="plotly_white",
        xaxis_title="Mechanism @ strength",
        yaxis_title="Mean delta mismatch score",
    )
    return figure


def _robust_delta_comparison_figure(
    evaluation: RobustPerturbationEvaluation,
    target_set: PerturbationTargetSet,
) -> go.Figure:
    metric_names = list(target_set.target_deltas.keys())
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            name="empirical target",
            x=metric_names,
            y=[target_set.target_deltas[name] for name in metric_names],
        )
    )
    figure.add_trace(
        go.Bar(
            name="seed-panel model mean",
            x=metric_names,
            y=[evaluation.delta_metrics_mean[name] for name in metric_names],
            error_y={
                "type": "data",
                "array": [evaluation.delta_metrics_std[name] for name in metric_names],
                "visible": True,
            },
        )
    )
    figure.update_layout(
        barmode="group",
        template="plotly_white",
        title=f"Seed-Panel Delta Match: {evaluation.mechanism} @ {evaluation.strength:.2f}",
    )
    return figure


def generate_stage_3_outputs(
    graph_path: str | Path,
    baseline_path: str | Path,
    sober_target_path: str | Path,
    perturbation_target_path: str | Path,
    output_dir: str | Path,
    report_path: str | Path,
    fit_iterations: int = 24,
    strengths: tuple[float, ...] = (0.05, 0.1, 0.2, 0.3),
    seed: int = 0,
    seed_panel: tuple[int, ...] | None = None,
    subject_split_path: str | Path | None = None,
    heldout_sober_target_path: str | Path | None = None,
    heldout_perturbation_target_path: str | Path | None = None,
) -> dict[str, Any]:
    graph = load_graph_config(graph_path)
    baseline = load_regime_config(baseline_path)
    sober_target = load_sober_target_set(sober_target_path)
    perturbation_target = load_perturbation_target_set(perturbation_target_path)
    subject_split = load_subject_split_file(subject_split_path) if subject_split_path is not None else None

    fit_result = fit_sober_regime(
        graph=graph,
        initial_regime=baseline,
        target_set=sober_target,
        iterations=fit_iterations,
        seed=seed,
    )
    ranking = rank_perturbation_mechanisms(
        graph=graph,
        sober_regime=fit_result.best_regime,
        target_set=perturbation_target,
        strengths=strengths,
    )
    best = ranking[0]
    resolved_seed_panel = seed_panel or tuple(seed + offset for offset in range(5))
    robust_ranking = rank_perturbation_mechanisms_seed_panel(
        graph=graph,
        sober_regime=fit_result.best_regime,
        target_set=perturbation_target,
        strengths=strengths,
        seeds=resolved_seed_panel,
    )
    robust_best = robust_ranking[0]
    null_summary = seed_noise_null_summary(
        graph=graph,
        sober_regime=fit_result.best_regime,
        target_set=perturbation_target,
        seeds=resolved_seed_panel,
    )
    heldout_validation_completed = False
    heldout_validation_evaluation: dict[str, Any] | None = None
    if subject_split is not None and subject_split.is_approved:
        if heldout_sober_target_path is None or heldout_perturbation_target_path is None:
            raise ValueError(
                "Approved subject split Stage 3 runs require held-out sober and perturbation target paths."
            )
        resolved_heldout_sober_path = Path(heldout_sober_target_path)
        resolved_heldout_perturbation_path = Path(heldout_perturbation_target_path)
        if not resolved_heldout_sober_path.exists() or not resolved_heldout_perturbation_path.exists():
            raise ValueError(
                "Approved subject split Stage 3 runs require existing held-out target artifacts from Stage 2."
            )
        heldout_sober_target = load_sober_target_set(resolved_heldout_sober_path)
        heldout_perturbation_target = load_perturbation_target_set(resolved_heldout_perturbation_path)
        heldout_eval = evaluate_perturbation_seed_panel(
            graph=graph,
            sober_regime=fit_result.best_regime,
            target_set=heldout_perturbation_target,
            mechanism=robust_best.mechanism,
            strength=robust_best.strength,
            seeds=resolved_seed_panel,
        )
        heldout_validation_completed = True
        heldout_validation_evaluation = {
            "status": "completed",
            "selection_rule": "Evaluate the Stage 3 robust-best mechanism selected on calibration subjects.",
            "selected_mechanism": robust_best.mechanism,
            "selected_strength": robust_best.strength,
            "heldout_sober_target_path": str(resolved_heldout_sober_path),
            "heldout_perturbation_target_path": str(resolved_heldout_perturbation_path),
            "heldout_dataset_anchor": heldout_sober_target.dataset_anchor,
            "seed_panel": list(resolved_seed_panel),
            "score_mean": heldout_eval.score_mean,
            "score_std": heldout_eval.score_std,
            "sign_agreement_fraction": heldout_eval.sign_agreement_fraction,
            "delta_metrics_mean": heldout_eval.delta_metrics_mean,
            "delta_metrics_std": heldout_eval.delta_metrics_std,
            "claim_guardrail": (
                "This is a subject-disjoint held-out empirical evaluation only because an approved split "
                "was configured and separate held-out target artifacts were evaluated."
            ),
        }

    output_path = Path(output_dir)
    figures_path = output_path / "figures"
    figures_path.mkdir(parents=True, exist_ok=True)

    _save_figure(_ranking_figure(ranking), figures_path / "mechanism_ranking.html")
    _save_figure(
        _delta_comparison_figure(best, perturbation_target),
        figures_path / "best_mechanism_delta_comparison.html",
    )
    _save_figure(
        _robust_ranking_figure(robust_ranking),
        figures_path / "mechanism_ranking_seed_panel.html",
    )
    _save_figure(
        _robust_delta_comparison_figure(robust_best, perturbation_target),
        figures_path / "best_mechanism_seed_panel_delta_comparison.html",
    )

    summary = {
        "best_mechanism": best.mechanism,
        "best_strength": best.strength,
        "best_score": best.score,
        "best_delta_metrics": best.delta_metrics,
        "ranking": [item.model_dump() for item in ranking],
        "seed_panel": list(resolved_seed_panel),
        "robust_best_mechanism": robust_best.mechanism,
        "robust_best_strength": robust_best.strength,
        "robust_best_score_mean": robust_best.score_mean,
        "robust_best_score_std": robust_best.score_std,
        "robust_best_sign_agreement_fraction": robust_best.sign_agreement_fraction,
        "robust_best_delta_metrics_mean": robust_best.delta_metrics_mean,
        "robust_best_delta_metrics_std": robust_best.delta_metrics_std,
        "robust_ranking": [item.model_dump() for item in robust_ranking],
        "seed_noise_null": null_summary,
        "version_stamp": get_version_stamp(Path(graph_path).resolve().parents[2]),
    }
    if subject_split is not None:
        summary["empirical_validation_boundary"] = build_subject_validation_boundary(
            subject_split,
            split_file_path=subject_split_path,
            held_out_validation_completed=heldout_validation_completed,
            selection_data_source="Stage 2 calibration subject subset",
            validation_data_source=(
                "Stage 3 evaluated held-out validation subject targets."
                if heldout_validation_completed
                else "Held-out validation subject subset; a real subject-disjoint Stage 3 empirical evaluation has not yet been run."
            ),
            selection_random_seed=seed,
        )
    if heldout_validation_evaluation is not None:
        summary["heldout_validation_evaluation"] = heldout_validation_evaluation
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "stage_3_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    report_lines = [
        "# Stage 3 Report",
        "",
        "## Plan",
        "",
        "- Fit a sober reference regime.",
        "- Apply four one-at-a-time perturbation mechanisms across a small strength grid.",
        "- Rank them against ds003059-derived LSD minus placebo macro delta targets.",
        "",
        "## Best Mechanism",
        "",
        f"- Mechanism: `{best.mechanism}`",
        f"- Strength: `{best.strength:.2f}`",
        f"- Score: `{best.score:.4f}`",
        "",
        "## Seed-Panel Robustness",
        "",
        f"- Seed panel: `{', '.join(str(item) for item in resolved_seed_panel)}`",
        f"- Robust best mechanism: `{robust_best.mechanism}`",
        f"- Robust best strength: `{robust_best.strength:.2f}`",
        f"- Robust mean score: `{robust_best.score_mean:.4f}`",
        f"- Robust score standard deviation: `{robust_best.score_std:.4f}`",
        f"- Robust target-sign agreement: `{robust_best.sign_agreement_fraction:.2f}`",
        f"- Seed-noise null mean score: `{null_summary['score_mean']:.4f}`",
        "",
        "## Sign-Mismatch Warning",
        "",
        "- The current ds003059 extraction should be compared against the literature-style target signs before interpreting the ranking.",
        "- Known conflicts under the current 8-module proxy are `within_network_stability`, `entropy_diversity`, and `metastability_proxy`.",
        "- The useful Stage 3 result is the ranking and mismatch profile, not an absolute mechanistic match.",
        "",
        "## Critical Review",
        "",
        (
            "- Stage 3 completed an approved subject-disjoint held-out empirical evaluation."
            if heldout_validation_completed
            else "- A subject-disjoint split file is configured, but Stage 3 has not completed a held-out empirical validation run."
            if subject_split is not None
            else "- No subject-disjoint split file is configured for this Stage 3 run."
        ),
        "- The current surrogate still underexpresses the ds003059 delta magnitudes; the best mechanism moves in the right direction but too weakly.",
        "- The coarse anatomical module mapping preserves some cross-network and thalamic shifts, "
        "but not a clean canonical psychedelic signature across all metrics.",
        "- The result should be treated as a ranked hypothesis list, not a mechanistic conclusion.",
        "- Candidate fit quality should be rechecked across a fixed seed panel before using the ranking as thesis evidence.",
        "",
    ]
    Path(report_path).write_text("\n".join(report_lines), encoding="utf-8")
    return summary
