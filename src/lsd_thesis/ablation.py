from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

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
from lsd_thesis.perturbation import (
    MECHANISMS,
    MechanismName,
    apply_mechanism,
    rank_perturbation_mechanisms,
    rank_perturbation_mechanisms_seed_panel,
    summarize_perturbation_metrics,
)
from lsd_thesis.simulator import load_regime_config
from lsd_thesis.utils import confidence_weight, get_version_stamp, save_figure


class AblationEvaluation(BaseModel):
    label: str
    score: float
    delta_metrics: dict[str, float]


class AblationStudy(BaseModel):
    single_mechanisms: list[AblationEvaluation]
    pairwise_mechanisms: list[AblationEvaluation]


def _confidence_weight(label: str) -> float:
    return confidence_weight(label)


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


def _delta_from_regimes(
    graph: GraphConfig,
    sober_regime: RegimeConfig,
    perturbed_regime: RegimeConfig,
) -> dict[str, float]:
    sober_metrics = summarize_perturbation_metrics(graph, sober_regime)
    perturbed_metrics = summarize_perturbation_metrics(graph, perturbed_regime)
    return {key: perturbed_metrics[key] - sober_metrics[key] for key in sober_metrics}


def run_ablation_study(
    graph: GraphConfig,
    sober_regime: RegimeConfig,
    target_set: PerturbationTargetSet,
    strengths: dict[MechanismName, float],
) -> AblationStudy:
    single_results: list[AblationEvaluation] = []
    pairwise_results: list[AblationEvaluation] = []

    for mechanism in MECHANISMS:
        perturbed = apply_mechanism(sober_regime, mechanism, strengths[mechanism])
        delta_metrics = _delta_from_regimes(graph, sober_regime, perturbed)
        single_results.append(
            AblationEvaluation(
                label=mechanism,
                score=_score_delta(delta_metrics, target_set),
                delta_metrics=delta_metrics,
            )
        )

    for mechanism_a, mechanism_b in itertools.combinations(MECHANISMS, 2):
        perturbed = apply_mechanism(sober_regime, mechanism_a, strengths[mechanism_a])
        perturbed = apply_mechanism(perturbed, mechanism_b, strengths[mechanism_b])
        delta_metrics = _delta_from_regimes(graph, sober_regime, perturbed)
        pairwise_results.append(
            AblationEvaluation(
                label=f"{mechanism_a}+{mechanism_b}",
                score=_score_delta(delta_metrics, target_set),
                delta_metrics=delta_metrics,
            )
        )

    return AblationStudy(
        single_mechanisms=sorted(single_results, key=lambda item: item.score),
        pairwise_mechanisms=sorted(pairwise_results, key=lambda item: item.score),
    )


def _save_figure(figure: go.Figure, path: Path) -> None:
    save_figure(figure, path)


def _single_figure(results: list[AblationEvaluation]) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Bar(
                x=[item.label for item in results],
                y=[item.score for item in results],
                marker_color="#2563eb",
            )
        ]
    )
    figure.update_layout(
        title="One-at-a-Time Mechanism Scores",
        template="plotly_white",
        yaxis_title="Delta mismatch score",
    )
    return figure


def _pairwise_figure(results: list[AblationEvaluation]) -> go.Figure:
    size = len(MECHANISMS)
    heatmap = np.full((size, size), np.nan, dtype=float)
    mechanism_to_index: dict[str, int] = {name: index for index, name in enumerate(MECHANISMS)}

    for item in results:
        mechanism_a, mechanism_b = item.label.split("+")
        i = mechanism_to_index[mechanism_a]
        j = mechanism_to_index[mechanism_b]
        heatmap[i, j] = item.score
        heatmap[j, i] = item.score

    figure = go.Figure(
        data=[
            go.Heatmap(
                z=heatmap,
                x=list(MECHANISMS),
                y=list(MECHANISMS),
                colorscale="Viridis",
            )
        ]
    )
    figure.update_layout(title="Pairwise Mechanism Scores", template="plotly_white")
    return figure


def generate_stage_4_outputs(
    graph_path: str | Path,
    baseline_path: str | Path,
    sober_target_path: str | Path,
    perturbation_target_path: str | Path,
    output_dir: str | Path,
    report_path: str | Path,
    fit_iterations: int = 24,
    seed: int = 0,
    seed_panel: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    graph = load_graph_config(graph_path)
    baseline = load_regime_config(baseline_path)
    sober_target = load_sober_target_set(sober_target_path)
    perturbation_target = load_perturbation_target_set(perturbation_target_path)

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
        strengths=(0.1, 0.25, 0.5, 0.75),
    )
    resolved_seed_panel = seed_panel or tuple(seed + offset for offset in range(5))
    robust_ranking = rank_perturbation_mechanisms_seed_panel(
        graph=graph,
        sober_regime=fit_result.best_regime,
        target_set=perturbation_target,
        strengths=(0.1, 0.25, 0.5, 0.75),
        seeds=resolved_seed_panel,
    )

    strengths: dict[MechanismName, float] = {mechanism: 0.25 for mechanism in MECHANISMS}
    resolved_mechanisms: set[MechanismName] = set()
    for item in robust_ranking:
        if item.mechanism not in resolved_mechanisms:
            strengths[item.mechanism] = item.strength
            resolved_mechanisms.add(item.mechanism)
    study = run_ablation_study(
        graph=graph,
        sober_regime=fit_result.best_regime,
        target_set=perturbation_target,
        strengths=strengths,
    )

    output_path = Path(output_dir)
    figures_path = output_path / "figures"
    figures_path.mkdir(parents=True, exist_ok=True)

    _save_figure(
        _single_figure(study.single_mechanisms), figures_path / "single_mechanism_ablation.html"
    )
    _save_figure(
        _pairwise_figure(study.pairwise_mechanisms), figures_path / "pairwise_ablation_heatmap.html"
    )

    summary = {
        "strengths": strengths,
        "single_mechanisms": [item.model_dump() for item in study.single_mechanisms],
        "pairwise_mechanisms": [item.model_dump() for item in study.pairwise_mechanisms],
        "one_shot_ranking": [item.model_dump() for item in ranking],
        "seed_panel": list(resolved_seed_panel),
        "robust_strength_source": [item.model_dump() for item in robust_ranking],
        "version_stamp": get_version_stamp(Path(graph_path).resolve().parents[2]),
    }
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "stage_4_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    report_lines = [
        "# Stage 4 Report",
        "",
        "## Plan",
        "",
        "- Run one-at-a-time ablations at the best currently available mechanism strengths.",
        "- Run pairwise combinations to see whether combinations help more than any single mechanism.",
        "- Rank the mechanisms by ds003059 empirical-delta mismatch score.",
        "",
        "## Results",
        "",
        f"- Best single mechanism: `{study.single_mechanisms[0].label}` with score `{study.single_mechanisms[0].score:.4f}`",
        f"- Best pairwise mechanism: `{study.pairwise_mechanisms[0].label}` with score `{study.pairwise_mechanisms[0].score:.4f}`",
        f"- Strengths selected from seed-panel ranking over seeds: `{', '.join(str(item) for item in resolved_seed_panel)}`",
        "",
        "## Critical Review",
        "",
        "- Pairwise combinations should be judged against the best single-mechanism score, not treated as automatically better.",
        "- Because Stage 3 fits remain weak, this ablation ranking should be interpreted as provisional.",
        "- The strongest value of this stage is identifying which mechanisms are ineffective or noisy under the current simulator.",
        "- Ablation rankings should be shown with the Stage 2 sign-mismatch warning.",
        "",
    ]
    Path(report_path).write_text("\n".join(report_lines), encoding="utf-8")
    return summary
