from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from lsd_thesis.metrics_literature import compute_literature_metrics
from lsd_thesis.models.base import SimulationResult
from lsd_thesis.models.receptor_gradient_neural_mass import PerturbationParameters, ReceptorGradientNeuralMassModel
from lsd_thesis.objectives import literature_weighted_lsd_objective


@dataclass(frozen=True)
class PerturbationCandidate:
    label: str
    parameters: Mapping[str, float]

    @property
    def active_parameter_count(self) -> int:
        return sum(1 for value in self.parameters.values() if abs(float(value)) > 1e-12)


def default_perturbation_candidates() -> tuple[PerturbationCandidate, ...]:
    return (
        PerturbationCandidate("gain_only", {"receptor_gain_alpha": 0.20}),
        PerturbationCandidate("hierarchy_only", {"hierarchy_cross_coupling_eta": 0.20}),
        PerturbationCandidate("sensory_visual_only", {"visual_gain_beta": 0.12, "sensory_gain_gamma": 0.10}),
        PerturbationCandidate("thalamic_routing_only", {"thalamic_routing_kappa": 0.25}),
        PerturbationCandidate("striatal_routing_only", {"striatal_routing_kappa": 0.25}),
        PerturbationCandidate("noise_only", {"noise_delta": 0.01}),
        PerturbationCandidate("gain_hierarchy", {"receptor_gain_alpha": 0.15, "hierarchy_cross_coupling_eta": 0.15}),
        PerturbationCandidate("gain_sensory", {"receptor_gain_alpha": 0.15, "visual_gain_beta": 0.10, "sensory_gain_gamma": 0.08}),
        PerturbationCandidate("hierarchy_sensory", {"hierarchy_cross_coupling_eta": 0.15, "visual_gain_beta": 0.10, "sensory_gain_gamma": 0.08}),
        PerturbationCandidate(
            "gain_hierarchy_sensory",
            {"receptor_gain_alpha": 0.12, "hierarchy_cross_coupling_eta": 0.12, "visual_gain_beta": 0.08, "sensory_gain_gamma": 0.08},
        ),
        PerturbationCandidate(
            "gain_hierarchy_sensory_subcortical",
            {
                "receptor_gain_alpha": 0.12,
                "hierarchy_cross_coupling_eta": 0.12,
                "visual_gain_beta": 0.08,
                "sensory_gain_gamma": 0.08,
                "thalamic_routing_kappa": 0.15,
                "striatal_routing_kappa": 0.10,
            },
        ),
        PerturbationCandidate(
            "full_perturbation_vector",
            {
                "receptor_gain_alpha": 0.12,
                "hierarchy_cross_coupling_eta": 0.12,
                "visual_gain_beta": 0.08,
                "sensory_gain_gamma": 0.08,
                "associative_decoherence_lambda": 0.08,
                "thalamic_routing_kappa": 0.15,
                "striatal_routing_kappa": 0.10,
                "noise_delta": 0.005,
                "homeostasis_delta": 0.05,
            },
        ),
    )


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(number):
        return default
    return number


def _simulation_metadata_rows(result: SimulationResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in result.node_labels:
        raw = dict(result.node_metadata.get(label, {}))
        raw.setdefault("node_label", label)
        raw.setdefault("yeo_network_label", raw.get("network"))
        raw.setdefault("coarse_class", raw.get("group"))
        raw.setdefault("hierarchy_value", raw.get("hierarchy", 0.5))
        rows.append(raw)
    return rows


def _simulation_time_series(result: SimulationResult) -> np.ndarray:
    return np.asarray(result.bold if result.bold is not None else result.activity, dtype=float)


def _scalar_metrics(metrics: Mapping[str, Any]) -> dict[str, float]:
    output: dict[str, float] = {}
    for key, value in metrics.items():
        if isinstance(value, int | float | np.integer | np.floating):
            number = float(value)
            if np.isfinite(number):
                output[str(key)] = number
    return output


def _metric_delta(placebo_metrics: Mapping[str, float], lsd_metrics: Mapping[str, float]) -> dict[str, float]:
    return {
        metric_name: float(lsd_metrics[metric_name]) - float(placebo_metrics[metric_name])
        for metric_name in sorted(set(placebo_metrics).intersection(lsd_metrics))
    }


def summarize_seed_metric_deltas(seed_rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, float | int]]:
    metric_names = sorted(set().union(*(dict(row["metrics"]).keys() for row in seed_rows))) if seed_rows else []
    summary: dict[str, dict[str, float | int]] = {}
    for metric_name in metric_names:
        values = [_finite_float(dict(row["metrics"]).get(metric_name)) for row in seed_rows if metric_name in dict(row["metrics"])]
        if values:
            summary[metric_name] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                "n": len(values),
            }
    return summary


def _extract_empirical_targets(target_summary: Mapping[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    metrics = dict(target_summary.get("metrics", {}))
    empirical_delta: dict[str, float] = {}
    uncertainty: dict[str, float] = {}
    for metric_name, raw_payload in metrics.items():
        payload = dict(raw_payload)
        empirical_delta[str(metric_name)] = _finite_float(payload.get("delta_mean"))
        ci_low = payload.get("ci_low")
        ci_high = payload.get("ci_high")
        if ci_low is not None and ci_high is not None:
            uncertainty[str(metric_name)] = max(abs(_finite_float(ci_high) - _finite_float(ci_low)) / 3.92, 1e-3)
        else:
            uncertainty[str(metric_name)] = max(_finite_float(payload.get("delta_std")), 1e-3)
    return empirical_delta, uncertainty


def rank_ablation_candidates(
    *,
    empirical_delta: Mapping[str, float],
    candidate_deltas: Mapping[str, Mapping[str, float]],
    empirical_uncertainty: Mapping[str, float] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, model_delta in candidate_deltas.items():
        objective = literature_weighted_lsd_objective(
            empirical_delta=empirical_delta,
            model_delta=model_delta,
            empirical_uncertainty=empirical_uncertainty,
        )
        rows.append({"label": label, "loss": float(objective["loss"]), "metric_count": int(objective["metric_count"])})
    return sorted(rows, key=lambda row: row["loss"])


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))


def _evaluate_candidate(
    model: ReceptorGradientNeuralMassModel,
    candidate: PerturbationCandidate,
    seeds: Sequence[int],
    empirical_delta: Mapping[str, float],
    empirical_uncertainty: Mapping[str, float],
    config_overrides: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    seed_rows: list[dict[str, Any]] = []
    sign_rows: list[dict[str, Any]] = []
    overshoot_rows: list[dict[str, Any]] = []
    for seed in seeds:
        placebo = model.simulate(config=dict(config_overrides), seed=int(seed))
        perturbed = model.simulate(
            config=dict(config_overrides),
            seed=int(seed),
            perturbation=PerturbationParameters.from_any(dict(candidate.parameters)),
        )
        placebo_metrics = _scalar_metrics(compute_literature_metrics(_simulation_time_series(placebo), _simulation_metadata_rows(placebo)))
        lsd_metrics = _scalar_metrics(compute_literature_metrics(_simulation_time_series(perturbed), _simulation_metadata_rows(perturbed)))
        delta = _metric_delta(placebo_metrics, lsd_metrics)
        seed_objective = literature_weighted_lsd_objective(
            empirical_delta=empirical_delta,
            model_delta=delta,
            empirical_uncertainty=empirical_uncertainty,
            active_parameter_count=candidate.active_parameter_count,
            lambda_sparse=0.01,
        )
        seed_rows.append(
            {
                "label": candidate.label,
                "seed": int(seed),
                "loss": float(seed_objective["loss"]),
                "metrics": delta,
            }
        )
        for metric_row in seed_objective["metrics"]:
            sign_rows.append(
                {
                    "label": candidate.label,
                    "seed": int(seed),
                    "metric": metric_row["metric"],
                    "empirical_delta": metric_row["empirical_delta"],
                    "model_delta": metric_row["model_delta"],
                    "sign_match": metric_row["sign_match"],
                }
            )
            overshoot_rows.append(
                {
                    "label": candidate.label,
                    "seed": int(seed),
                    "metric": metric_row["metric"],
                    "overshoot": metric_row["overshoot"],
                }
            )

    seed_metric_deltas = [dict(row["metrics"]) for row in seed_rows]
    objective = literature_weighted_lsd_objective(
        empirical_delta=empirical_delta,
        seed_metric_deltas=seed_metric_deltas,
        empirical_uncertainty=empirical_uncertainty,
        active_parameter_count=candidate.active_parameter_count,
        lambda_sparse=0.01,
    )
    return (
        {
            "label": candidate.label,
            "parameters": dict(candidate.parameters),
            "active_parameter_count": candidate.active_parameter_count,
            "loss": float(objective["loss"]),
            "objective": objective,
            "delta_summary": summarize_seed_metric_deltas(seed_rows),
        },
        seed_rows,
        sign_rows,
        overshoot_rows,
    )


def _write_stage_5_report(report_path: Path, summary: Mapping[str, Any]) -> None:
    best = dict(summary["best_candidate"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage 5 Literature-Weighted Fit",
        "",
        "This stage compares receptor/gradient neural-mass LSD-minus-placebo proxy deltas against cached literature-aligned empirical deltas.",
        "It is a macro-dynamics surrogate objective, not a receptor-level or subjective-experience model.",
        "",
        "## Summary",
        "",
        f"- Status: {summary['status']}",
        f"- Seeds: {', '.join(str(seed) for seed in summary['seeds'])}",
        f"- Candidates: {summary['candidate_count']}",
        f"- Best candidate: {best['label']}",
        f"- Best loss: {best['loss']:.6g}",
        "",
        "## Guardrails",
        "",
        "- The quick run is a deterministic development budget, not a final optimization.",
        "- Seed variance, sign mismatch, and overshoot are explicit penalties.",
        "- A low loss is evidence of a better proxy match, not evidence of biological mechanism truth.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_stage_5_literature_fit(
    *,
    target_summary_path: str | Path,
    output_dir: str | Path,
    report_path: str | Path,
    seeds: Sequence[int] = (11, 17, 23),
    candidates: Sequence[PerturbationCandidate] | None = None,
    model_config_overrides: Mapping[str, Any] | None = None,
    n_bootstrap: int = 500,
) -> dict[str, Any]:
    del n_bootstrap
    target_summary = json.loads(Path(target_summary_path).read_text(encoding="utf-8"))
    empirical_delta, empirical_uncertainty = _extract_empirical_targets(target_summary)
    resolved_candidates = tuple(candidates or default_perturbation_candidates())
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    config_overrides = {
        "n_steps": 160,
        "burn_in": 30,
        "emit_bold": True,
        **dict(model_config_overrides or {}),
    }
    model = ReceptorGradientNeuralMassModel()

    candidate_summaries: list[dict[str, Any]] = []
    per_seed_rows: list[dict[str, Any]] = []
    sign_rows: list[dict[str, Any]] = []
    overshoot_rows: list[dict[str, Any]] = []
    for candidate in resolved_candidates:
        candidate_summary, candidate_seed_rows, candidate_sign_rows, candidate_overshoot_rows = _evaluate_candidate(
            model=model,
            candidate=candidate,
            seeds=seeds,
            empirical_delta=empirical_delta,
            empirical_uncertainty=empirical_uncertainty,
            config_overrides=config_overrides,
        )
        candidate_summaries.append(candidate_summary)
        per_seed_rows.extend(candidate_seed_rows)
        sign_rows.extend(candidate_sign_rows)
        overshoot_rows.extend(candidate_overshoot_rows)

    leaderboard = sorted(candidate_summaries, key=lambda row: float(row["loss"]))
    best_candidate = leaderboard[0] if leaderboard else {}
    placebo_summary = {
        "status": "evaluated_default_baseline",
        "model": "receptor_gradient_neural_mass",
        "seeds": list(seeds),
        "config_overrides": config_overrides,
        "notes": [
            "Quick Stage 5 uses the default receptor/gradient neural-mass config as the placebo baseline.",
            "A broader baseline parameter search is a future compute-budget expansion.",
        ],
    }
    lsd_summary = {
        "status": "candidate_leaderboard_complete",
        "best_candidate": best_candidate,
        "candidate_count": len(leaderboard),
        "notes": [
            "Candidate perturbations are named macro-dynamic hypotheses.",
            "Leaderboard ranking is objective-based and does not identify a true LSD mechanism.",
        ],
    }
    summary = {
        "status": "complete",
        "target_summary_path": str(target_summary_path),
        "seeds": list(seeds),
        "candidate_count": len(leaderboard),
        "best_candidate": best_candidate,
        "leaderboard": leaderboard,
        "outputs": {
            "literature_weighted_fit_summary": str(output_path / "literature_weighted_fit_summary.json"),
            "placebo_fit_summary": str(output_path / "placebo_fit_summary.json"),
            "lsd_perturbation_fit_summary": str(output_path / "lsd_perturbation_fit_summary.json"),
            "per_seed_metrics": str(output_path / "per_seed_metrics.csv"),
            "sign_match_table": str(output_path / "sign_match_table.csv"),
            "overshoot_table": str(output_path / "overshoot_table.csv"),
            "ablation_leaderboard": str(output_path / "ablation_leaderboard.csv"),
            "report": str(report_path),
        },
    }

    (output_path / "literature_weighted_fit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_path / "placebo_fit_summary.json").write_text(json.dumps(placebo_summary, indent=2), encoding="utf-8")
    (output_path / "lsd_perturbation_fit_summary.json").write_text(json.dumps(lsd_summary, indent=2), encoding="utf-8")
    _write_csv(
        output_path / "ablation_leaderboard.csv",
        ["label", "loss", "active_parameter_count", "metric_count", "parameters"],
        [
            {
                "label": row["label"],
                "loss": row["loss"],
                "active_parameter_count": row["active_parameter_count"],
                "metric_count": row["objective"]["metric_count"],
                "parameters": json.dumps(row["parameters"], sort_keys=True),
            }
            for row in leaderboard
        ],
    )
    _write_csv(
        output_path / "per_seed_metrics.csv",
        ["label", "seed", "loss", "metrics"],
        [
            {
                "label": row["label"],
                "seed": row["seed"],
                "loss": row["loss"],
                "metrics": json.dumps(row["metrics"], sort_keys=True),
            }
            for row in per_seed_rows
        ],
    )
    _write_csv(output_path / "sign_match_table.csv", ["label", "seed", "metric", "empirical_delta", "model_delta", "sign_match"], sign_rows)
    _write_csv(output_path / "overshoot_table.csv", ["label", "seed", "metric", "overshoot"], overshoot_rows)
    _write_stage_5_report(Path(report_path), summary)
    return summary
