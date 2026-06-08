from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np

from lsd_thesis.dynamic_mechanism.core import (
    CONTROL_HORIZON,
    EmpiricalPair,
    load_empirical_pairs,
    summarize_dynamic_repertoire,
    summarize_network_control_energy,
)
from lsd_thesis.dynamic_mechanism.stats import (
    aggregate_metric_deltas,
    mean_step_distance,
    state_labels_from_reference,
    transition_metrics,
    zscore_pair,
)

BOOTSTRAP_ITERATIONS = 256
ROBUSTNESS_RANDOM_NULL_COUNT = 32
ROBUSTNESS_SEED = 20260519

SUPPORT_METRICS = {
    "A": {
        "transition_entropy",
        "transition_rate",
        "barrier_reduction_proxy",
        "transition_step_distance_proxy",
    },
    "C": {
        "sensory_transmodal_coupling",
        "sensory_global_coupling",
        "associative_global_coupling",
        "thalamic_global_coupling",
        "hierarchy_flattening_proxy",
        "hierarchy_gradient_flattening_proxy",
        "receptor_weighted_global_coupling",
        "receptor_global_coupling_alignment",
    },
    "D": {
        "within_network_segregation",
        "between_network_integration",
        "integration_segregation_balance",
        "dynamic_fc_variance",
        "dynamic_fc_path_length",
        "graph_modularity_reduction_proxy",
        "mean_participation_coefficient",
        "global_efficiency",
    },
    "E": {
        "lsd_vs_placebo_receptor_transition_energy_reduction_pct",
        "lsd_vs_placebo_uniform_transition_energy_reduction_pct",
        "receptor_vs_random_energy_reduction_pct",
        "state_target_alignment_receptor",
    },
}

SECTION_BY_LAYER = {
    "A": "transition_proxy",
    "C": "hierarchy_routing",
    "D": "dynamic_repertoire",
    "E": "network_control_energy",
}


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if np.isfinite(number) else default


def _metric_metadata(metric_rows: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, int]]:
    expected_direction: dict[str, str] = {}
    expected_sign: dict[str, int] = {}
    for row in metric_rows:
        metric = str(row.get("metric", ""))
        if not metric:
            continue
        expected_direction[metric] = str(row.get("expected_direction", ""))
        sign = int(row.get("expected_sign", 1))
        expected_sign[metric] = sign if sign in {-1, 1} else 1
    return expected_direction, expected_sign


def _support_score_from_pair_rows(pair_rows: list[dict[str, Any]], metric_rows: list[dict[str, Any]], support_metrics: set[str]) -> float:
    expected_direction, expected_sign = _metric_metadata(metric_rows)
    metric_values: dict[str, list[float]] = {metric: [] for metric in expected_direction}
    for row in pair_rows:
        deltas = row.get("delta") or row.get("metrics") or {}
        if not isinstance(deltas, dict):
            continue
        for metric in metric_values:
            if metric in deltas:
                metric_values[metric].append(_finite_float(deltas[metric]))
    aggregate_rows = aggregate_metric_deltas(metric_values, expected_direction, expected_sign)
    components = [
        _finite_float(row.get("signed_effect_size"))
        for row in aggregate_rows
        if str(row.get("metric")) in support_metrics
    ]
    return float(np.mean(components)) if components else 0.0


def _score_b_from_fold_rows(fold_rows: list[dict[str, Any]]) -> float:
    values = [
        _finite_float(row.get("condition_interaction_relative_improvement_pct"))
        for row in fold_rows
        if isinstance(row, dict)
    ]
    return float(np.mean(values)) if values else 0.0


def _current_scores(summary: dict[str, Any]) -> dict[str, float]:
    scores = {
        str(row.get("layer")): _finite_float(row.get("score"))
        for row in summary.get("mechanism_ranking", [])
        if isinstance(row, dict) and row.get("layer")
    }
    if "B" not in scores:
        scores["B"] = _finite_float(summary.get("dmdc", {}).get("support_score"))
    return scores


def _rows_for_sample(pair_rows: list[dict[str, Any]], sampled_subjects: np.ndarray) -> list[dict[str, Any]]:
    by_subject: dict[str, list[dict[str, Any]]] = {}
    for row in pair_rows:
        by_subject.setdefault(str(row.get("subject", "")), []).append(row)
    sampled_rows: list[dict[str, Any]] = []
    for subject in sampled_subjects:
        sampled_rows.extend(by_subject.get(str(subject), []))
    return sampled_rows


def _fold_rows_for_sample(fold_rows: list[dict[str, Any]], sampled_subjects: np.ndarray) -> list[dict[str, Any]]:
    by_subject = {str(row.get("held_out_subject")): row for row in fold_rows if isinstance(row, dict)}
    return [by_subject[str(subject)] for subject in sampled_subjects if str(subject) in by_subject]


def _bootstrap_scores(summary: dict[str, Any], *, iterations: int = BOOTSTRAP_ITERATIONS, seed: int = ROBUSTNESS_SEED) -> dict[str, Any]:
    subjects = [str(subject) for subject in summary.get("subjects", [])]
    if not subjects:
        return {
            "status": "missing_subjects",
            "iterations": 0,
            "bootstrap_score_rows": [],
            "layer_summary": [],
            "claim_guardrail": "Bootstrap uncertainty was not computed because no subjects were available.",
        }

    rng = np.random.default_rng(seed)
    score_rows: list[dict[str, Any]] = []
    fold_rows = summary.get("dmdc", {}).get("fold_rows", [])
    current_scores = _current_scores(summary)

    for iteration in range(iterations):
        sampled_subjects = rng.choice(subjects, size=len(subjects), replace=True)
        layer_scores: dict[str, float] = {}
        for layer, section_key in SECTION_BY_LAYER.items():
            section = summary.get(section_key, {})
            pair_rows = _rows_for_sample(section.get("pair_rows", []), sampled_subjects)
            layer_scores[layer] = _support_score_from_pair_rows(
                pair_rows,
                section.get("metric_deltas", []),
                SUPPORT_METRICS[layer],
            )
        layer_scores["B"] = _score_b_from_fold_rows(_fold_rows_for_sample(fold_rows, sampled_subjects))
        ranked_layers = sorted(layer_scores, key=lambda layer: layer_scores[layer], reverse=True)
        ranks = {layer: rank for rank, layer in enumerate(ranked_layers, start=1)}
        for layer, score in sorted(layer_scores.items()):
            score_rows.append(
                {
                    "iteration": iteration,
                    "layer": layer,
                    "score": score,
                    "rank": ranks[layer],
                }
            )

    layer_summary: list[dict[str, Any]] = []
    for layer in ["A", "B", "C", "D", "E"]:
        layer_rows = [row for row in score_rows if row["layer"] == layer]
        scores = np.asarray([row["score"] for row in layer_rows], dtype=float)
        rank_values = np.asarray([row["rank"] for row in layer_rows], dtype=float)
        layer_summary.append(
            {
                "layer": layer,
                "current_score": current_scores.get(layer),
                "score_mean": float(np.mean(scores)),
                "score_std": float(np.std(scores, ddof=1)) if len(scores) > 1 else 0.0,
                "score_ci_low": float(np.quantile(scores, 0.025)),
                "score_ci_high": float(np.quantile(scores, 0.975)),
                "median_rank": float(np.median(rank_values)),
                "rank_1_fraction": float(np.mean(rank_values == 1.0)),
            }
        )

    top_layer = max(layer_summary, key=lambda row: _finite_float(row["rank_1_fraction"]))
    return {
        "status": "implemented_subject_bootstrap",
        "iterations": iterations,
        "seed": seed,
        "resampling_unit": "subject with all cached run rows carried together",
        "bootstrap_score_rows": score_rows,
        "layer_summary": layer_summary,
        "top_layer_by_rank_1_fraction": top_layer["layer"],
        "claim_guardrail": (
            "Bootstrap intervals are descriptive stability checks over a small n=15 paired-subject dataset, "
            "not population confidence intervals."
        ),
    }


def _score_from_run_metric_rows(rows: list[dict[str, Any]], support_metrics: set[str]) -> float:
    components = [
        _finite_float(row.get("signed_effect_size"))
        for row in rows
        if str(row.get("metric")) in support_metrics
    ]
    return float(np.mean(components)) if components else 0.0


def _run_sensitivity(summary: dict[str, Any]) -> dict[str, Any]:
    run_rows: list[dict[str, Any]] = []
    for layer, section_key in SECTION_BY_LAYER.items():
        section = summary.get(section_key, {})
        rows_by_run: dict[str, list[dict[str, Any]]] = {}
        for row in section.get("run_metric_deltas", []):
            rows_by_run.setdefault(str(row.get("run", "unknown")), []).append(row)
        for run, rows in sorted(rows_by_run.items()):
            run_rows.append(
                {
                    "layer": layer,
                    "run": run,
                    "support_score": _score_from_run_metric_rows(rows, SUPPORT_METRICS[layer]),
                    "metric_count": len(rows),
                }
            )
    return {
        "status": "implemented_from_run_metric_deltas",
        "run_rows": run_rows,
        "claim_guardrail": (
            "Run sensitivity uses cached run-01/run-03 metric aggregates; B is excluded because the DMDc LOSO "
            "baseline is subject-fold based, not run-specific."
        ),
    }


def _transition_summary_for_state_method(
    pairs: list[EmpiricalPair],
    *,
    state_method: str,
    state_bins: int,
    score_mode: str,
) -> dict[str, Any]:
    metric_names = [
        "state_occupancy_entropy",
        "transition_entropy",
        "transition_rate",
        "mean_dwell_time",
        "barrier_reduction_proxy",
        "transition_step_distance_proxy",
    ]
    metric_deltas: dict[str, list[float]] = {metric: [] for metric in metric_names}
    for pair in pairs:
        placebo_normalized, lsd_normalized = zscore_pair(pair.placebo, pair.lsd)
        reference = np.vstack([placebo_normalized, lsd_normalized])
        placebo_labels = state_labels_from_reference(reference, placebo_normalized, state_bins=state_bins, score_mode=score_mode)
        lsd_labels = state_labels_from_reference(reference, lsd_normalized, state_bins=state_bins, score_mode=score_mode)
        placebo_metrics = transition_metrics(placebo_labels)
        lsd_metrics = transition_metrics(lsd_labels)
        placebo_metrics["transition_step_distance_proxy"] = mean_step_distance(placebo_normalized)
        lsd_metrics["transition_step_distance_proxy"] = mean_step_distance(lsd_normalized)
        for metric in metric_names:
            metric_deltas[metric].append(float(lsd_metrics[metric] - placebo_metrics[metric]))

    expected_direction = {
        "state_occupancy_entropy": "positive means broader state occupancy under LSD",
        "transition_entropy": "positive means more diverse transitions under LSD",
        "transition_rate": "positive means more frequent state switching under LSD",
        "mean_dwell_time": "negative means shorter dwell times under LSD",
        "barrier_reduction_proxy": "positive means shorter dwell times under LSD",
        "transition_step_distance_proxy": "positive means larger one-step macro-state movement under LSD",
    }
    expected_sign = {
        "state_occupancy_entropy": 1,
        "transition_entropy": 1,
        "transition_rate": 1,
        "mean_dwell_time": -1,
        "barrier_reduction_proxy": 1,
        "transition_step_distance_proxy": 1,
    }
    metric_rows = aggregate_metric_deltas(metric_deltas, expected_direction, expected_sign)
    score = float(np.mean([row["signed_effect_size"] for row in metric_rows if row["metric"] in SUPPORT_METRICS["A"]]))
    return {
        "state_method": state_method,
        "state_bins": state_bins,
        "score_mode": score_mode,
        "layer": "A",
        "support_score": score,
        "metric_deltas": metric_rows,
    }


def _metric_mean(metric_rows: list[dict[str, Any]], metric: str) -> float | None:
    for row in metric_rows:
        if row.get("metric") == metric:
            return _finite_float(row.get("mean_delta"))
    return None


def _state_label_sensitivity(pairs: list[EmpiricalPair]) -> dict[str, Any]:
    methods = [
        ("pca_quantile_4", 4, "pca"),
        ("pca_quantile_3", 3, "pca"),
        ("global_mean_quantile_4", 4, "global_mean"),
        ("trajectory_norm_quantile_4", 4, "trajectory_norm"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (state_method, state_bins, score_mode) in enumerate(methods):
        transition = _transition_summary_for_state_method(
            pairs,
            state_method=state_method,
            state_bins=state_bins,
            score_mode=score_mode,
        )
        rows.append(
            {
                "layer": "A",
                "state_method": state_method,
                "state_bins": state_bins,
                "score_mode": score_mode,
                "support_score": transition["support_score"],
                "transition_entropy_delta": _metric_mean(transition["metric_deltas"], "transition_entropy"),
                "transition_rate_delta": _metric_mean(transition["metric_deltas"], "transition_rate"),
                "barrier_reduction_proxy_delta": _metric_mean(transition["metric_deltas"], "barrier_reduction_proxy"),
            }
        )
        network_control = summarize_network_control_energy(
            pairs,
            horizon=CONTROL_HORIZON,
            random_null_count=ROBUSTNESS_RANDOM_NULL_COUNT,
            rng_seed=ROBUSTNESS_SEED + index,
            state_bins=state_bins,
            state_score_mode=score_mode,
        )
        rows.append(
            {
                "layer": "E",
                "state_method": state_method,
                "state_bins": state_bins,
                "score_mode": score_mode,
                "support_score": network_control["support_score"],
                "lsd_receptor_energy_reduction_pct": _metric_mean(
                    network_control["metric_deltas"],
                    "lsd_vs_placebo_receptor_transition_energy_reduction_pct",
                ),
                "receptor_vs_random_energy_reduction_pct": _metric_mean(
                    network_control["metric_deltas"],
                    "receptor_vs_random_energy_reduction_pct",
                ),
                "state_target_alignment_receptor": _metric_mean(
                    network_control["metric_deltas"],
                    "state_target_alignment_receptor",
                ),
            }
        )
    return {
        "status": "implemented_a_e_state_label_sensitivity",
        "rows": rows,
        "claim_guardrail": (
            "State-label sensitivity tests whether A/E depend on the PCA-quartile state proxy; "
            "it does not validate any state label as a biological state."
        ),
    }


def _horizon_sensitivity(pairs: list[EmpiricalPair]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, horizon in enumerate([4, 8, 12, 16]):
        network_control = summarize_network_control_energy(
            pairs,
            horizon=horizon,
            random_null_count=ROBUSTNESS_RANDOM_NULL_COUNT,
            rng_seed=ROBUSTNESS_SEED + 100 + index,
        )
        rows.append(
            {
                "layer": "E",
                "horizon": horizon,
                "support_score": network_control["support_score"],
                "lsd_receptor_energy_reduction_pct": _metric_mean(
                    network_control["metric_deltas"],
                    "lsd_vs_placebo_receptor_transition_energy_reduction_pct",
                ),
                "lsd_uniform_energy_reduction_pct": _metric_mean(
                    network_control["metric_deltas"],
                    "lsd_vs_placebo_uniform_transition_energy_reduction_pct",
                ),
                "receptor_vs_random_energy_reduction_pct": _metric_mean(
                    network_control["metric_deltas"],
                    "receptor_vs_random_energy_reduction_pct",
                ),
                "state_target_alignment_receptor": _metric_mean(
                    network_control["metric_deltas"],
                    "state_target_alignment_receptor",
                ),
            }
        )
    return {
        "status": "implemented_e_horizon_sensitivity",
        "rows": rows,
        "random_null_count": ROBUSTNESS_RANDOM_NULL_COUNT,
        "claim_guardrail": "E horizon sensitivity is still run on the macro-module proxy graph, not a structural connectome.",
    }


def _window_sensitivity(pairs: list[EmpiricalPair]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for window_size in [20, 40, 60, 80]:
        repertoire = summarize_dynamic_repertoire(pairs, window_size=window_size)
        rows.append(
            {
                "layer": "D",
                "window_size": window_size,
                "support_score": repertoire["support_score"],
                "integration_segregation_balance_delta": _metric_mean(
                    repertoire["metric_deltas"],
                    "integration_segregation_balance",
                ),
                "dynamic_fc_variance_delta": _metric_mean(repertoire["metric_deltas"], "dynamic_fc_variance"),
                "dynamic_fc_path_length_delta": _metric_mean(repertoire["metric_deltas"], "dynamic_fc_path_length"),
                "global_efficiency_delta": _metric_mean(repertoire["metric_deltas"], "global_efficiency"),
            }
        )
    return {
        "status": "implemented_d_window_sensitivity",
        "rows": rows,
        "claim_guardrail": "D window-size sensitivity only addresses dynamic-FC parameter dependence inside the current 8-module proxy space.",
    }


def _section_metric(summary: dict[str, Any], section_key: str, metric: str) -> dict[str, Any] | None:
    for row in summary.get(section_key, {}).get("metric_deltas", []):
        if row.get("metric") == metric:
            return cast(dict[str, Any], row)
    return None


def _benchmark_row(
    summary: dict[str, Any],
    *,
    benchmark: str,
    layer: str,
    section_key: str,
    metric: str,
    expected_sign: int,
    source: str,
    url: str,
    interpretation: str,
    caveat: str,
) -> dict[str, Any]:
    metric_row = _section_metric(summary, section_key, metric)
    if metric_row is None:
        return {
            "benchmark": benchmark,
            "layer": layer,
            "project_metric": metric,
            "expected_sign": expected_sign,
            "observed_mean_delta": None,
            "observed_signed_effect_size": None,
            "sign_match": None,
            "status": "missing",
            "source": source,
            "url": url,
            "interpretation": interpretation,
            "caveat": caveat,
        }
    observed = _finite_float(metric_row.get("mean_delta"))
    sign_match = observed * expected_sign > 0.0 if abs(observed) > 1e-12 else False
    return {
        "benchmark": benchmark,
        "layer": layer,
        "project_metric": metric,
        "expected_sign": expected_sign,
        "observed_mean_delta": observed,
        "observed_signed_effect_size": metric_row.get("signed_effect_size"),
        "sign_match": sign_match,
        "status": "aligned" if sign_match else "opposes_or_weak",
        "source": source,
        "url": url,
        "interpretation": interpretation,
        "caveat": caveat,
    }


def _literature_benchmark(summary: dict[str, Any]) -> dict[str, Any]:
    nature_medicine_url = "https://www.nature.com/articles/s41591-026-04287-9"
    singleton_url = "https://www.nature.com/articles/s41467-022-33578-1"
    rows = [
        _benchmark_row(
            summary,
            benchmark="2026 Nature Medicine transmodal-unimodal coupling",
            layer="C",
            section_key="hierarchy_routing",
            metric="sensory_transmodal_coupling",
            expected_sign=1,
            source="Girn et al., Nature Medicine 2026",
            url=nature_medicine_url,
            interpretation="Direct coarse proxy for increased coupling between unimodal/sensory and transmodal systems.",
            caveat="Current project uses 8 modules, not the consortium atlas/Bayesian mega-analysis pipeline.",
        ),
        _benchmark_row(
            summary,
            benchmark="2026 Nature Medicine increased between-network integration",
            layer="D",
            section_key="dynamic_repertoire",
            metric="between_network_integration",
            expected_sign=1,
            source="Girn et al., Nature Medicine 2026",
            url=nature_medicine_url,
            interpretation="Graph-dynamic proxy for enhanced integration across broad systems.",
            caveat="Integration metric is descriptive FC, not the exact mega-analysis posterior.",
        ),
        _benchmark_row(
            summary,
            benchmark="2026 Nature Medicine within-network coupling reduction",
            layer="D",
            section_key="dynamic_repertoire",
            metric="within_network_segregation",
            expected_sign=-1,
            source="Girn et al., Nature Medicine 2026",
            url=nature_medicine_url,
            interpretation="Checks whether the current data show reduced segregation/within-system coupling.",
            caveat="The paper notes not all visually apparent patterns yielded high-confidence posteriors.",
        ),
        _benchmark_row(
            summary,
            benchmark="2026 Nature Medicine thalamic-unimodal coupling",
            layer="C",
            section_key="hierarchy_routing",
            metric="thalamic_sensory_coupling",
            expected_sign=1,
            source="Girn et al., Nature Medicine 2026",
            url=nature_medicine_url,
            interpretation="Coarse thalamic-gateway to sensory/unimodal proxy.",
            caveat="The current thalamic module is coarse and does not resolve thalamic nuclei.",
        ),
        _benchmark_row(
            summary,
            benchmark="Singleton 2022 lower psychedelic control energy",
            layer="E",
            section_key="network_control_energy",
            metric="lsd_vs_placebo_receptor_transition_energy_reduction_pct",
            expected_sign=1,
            source="Singleton et al., Nature Communications 2022",
            url=singleton_url,
            interpretation="Local proxy check for lower transition-control energy under LSD.",
            caveat="This is not full receptor-informed NCT until structural connectome and PET receptor maps are added.",
        ),
        _benchmark_row(
            summary,
            benchmark="Singleton 2022 receptor-informed control placement",
            layer="E",
            section_key="network_control_energy",
            metric="receptor_vs_random_energy_reduction_pct",
            expected_sign=1,
            source="Singleton et al., Nature Communications 2022",
            url=singleton_url,
            interpretation="Tests whether the coarse receptor prior beats random receptor-prior permutations.",
            caveat="A negative or weak result should block receptor-specific claims.",
        ),
    ]
    striatal_row = _benchmark_row(
        summary,
        benchmark="2026 Nature Medicine striatal-unimodal coupling",
        layer="C/D",
        section_key="hierarchy_routing",
        metric="striatal_sensory_coupling",
        expected_sign=1,
        source="Girn et al., Nature Medicine 2026",
        url=nature_medicine_url,
        interpretation="Proxy check for stronger striatal coupling with sensory/unimodal systems.",
        caveat=(
            "Requires a dedicated striatal parcel; the Harvard-Oxford striatal target is still a bilateral "
            "proxy, not a nucleus-level mega-analysis reproduction."
        ),
    )
    if striatal_row["status"] == "missing":
        striatal_row.update(
            {
                "project_metric": "not_available_current_proxy_without_striatal_parcel",
                "status": "missing_required_region",
                "interpretation": "Needs striatum/caudate/putamen parcels before this can be tested.",
                "caveat": "Do not claim striatal support from cortical-only or current 8-module proxy rows.",
            }
        )
    rows.append(striatal_row)
    aligned = sum(row.get("sign_match") is True for row in rows)
    measurable = sum(row.get("sign_match") is not None for row in rows)
    return {
        "status": "implemented_metric_mapping",
        "rows": rows,
        "aligned_count": aligned,
        "measurable_count": measurable,
        "alignment_fraction": float(aligned / measurable) if measurable else 0.0,
        "claim_guardrail": (
            "Literature benchmarking compares directionally mapped proxy metrics to published targets; "
            "it is not a reproduction of the cited studies."
        ),
    }


def literature_benchmark_from_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return _literature_benchmark(summary)


def _claim_verdicts(summary: dict[str, Any], robustness: dict[str, Any], literature: dict[str, Any]) -> list[dict[str, Any]]:
    bootstrap_layers = {row["layer"]: row for row in robustness.get("subject_bootstrap", {}).get("layer_summary", [])}
    e_rows = {row.get("horizon"): row for row in robustness.get("e_horizon_sensitivity", {}).get("rows", [])}
    default_e = e_rows.get(CONTROL_HORIZON, {})
    receptor_metric = _section_metric(summary, "network_control_energy", "receptor_vs_random_energy_reduction_pct")
    control_metric = _section_metric(summary, "network_control_energy", "lsd_vs_placebo_receptor_transition_energy_reduction_pct")
    c_bootstrap = bootstrap_layers.get("C", {})
    literature_rows = literature.get("rows", [])
    transmodal: dict[str, Any] = next(
        (row for row in literature_rows if "transmodal-unimodal" in str(row.get("benchmark"))),
        {},
    )
    striatal: dict[str, Any] = next(
        (row for row in literature_rows if "striatal" in str(row.get("benchmark"))),
        {},
    )
    return [
        {
            "claim": "C hierarchy/routing is currently the strongest implemented LSD mechanism layer.",
            "verdict": "supported_first_pass" if _finite_float(c_bootstrap.get("rank_1_fraction")) >= 0.5 else "needs_more_robustness",
            "evidence": f"Bootstrap rank-1 fraction={_finite_float(c_bootstrap.get('rank_1_fraction')):.3f}.",
            "next_action": "Re-run C under Schaefer/Yeo and motion-sensitive exclusions before final thesis claims.",
        },
        {
            "claim": "E supports a landscape-flattening proxy.",
            "verdict": "supported_proxy" if _finite_float(control_metric.get("mean_delta") if control_metric else 0.0) > 0 else "not_supported",
            "evidence": f"Default-horizon receptor transition-energy reduction={_finite_float(default_e.get('lsd_receptor_energy_reduction_pct')):.3f}%.",
            "next_action": "Replace macro graph with structural connectome and add graph-rewire nulls.",
        },
        {
            "claim": "E supports receptor-specific control placement.",
            "verdict": "not_supported_yet" if _finite_float(receptor_metric.get("mean_delta") if receptor_metric else 0.0) <= 0 else "supported_proxy_only",
            "evidence": f"Receptor-vs-random energy reduction={_finite_float(receptor_metric.get('mean_delta') if receptor_metric else 0.0):.3f}%.",
            "next_action": "Replace coarse priors with PET 5-HT2A maps and spatial nulls before making receptor claims.",
        },
        {
            "claim": "Current LSD patterns align with the 2026 transmodal-unimodal benchmark.",
            "verdict": "directionally_aligned" if transmodal.get("sign_match") is True else "not_aligned_or_missing",
            "evidence": f"C sensory-transmodal mean delta={_finite_float(transmodal.get('observed_mean_delta')):.4f}.",
            "next_action": "Test the same benchmark in ds006072 and Schaefer/Yeo parcellations.",
        },
        {
            "claim": "Current LSD patterns address striatal/unimodal effects.",
            "verdict": (
                "directionally_aligned_proxy"
                if striatal.get("sign_match") is True
                else "not_aligned_or_missing"
                if striatal.get("observed_mean_delta") is not None
                else "not_testable_current_proxy"
            ),
            "evidence": (
                f"Striatal-sensory mean delta={_finite_float(striatal.get('observed_mean_delta')):.4f}."
                if striatal.get("observed_mean_delta") is not None
                else str(striatal.get("project_metric", "missing striatum metric"))
            ),
            "next_action": (
                "Interpret as a proxy benchmark only; keep nucleus-level Nature Medicine claims out of final conclusions."
                if striatal.get("observed_mean_delta") is not None
                else "Add striatal parcels before comparing this part of the Nature Medicine result."
            ),
        },
        {
            "claim": "B DMDc is the main control-theory result.",
            "verdict": "reject_as_main_claim",
            "evidence": f"B bootstrap rank-1 fraction={_finite_float(bootstrap_layers.get('B', {}).get('rank_1_fraction')):.3f}.",
            "next_action": "Keep B as a negative/sanity baseline unless held-out prediction improves clearly.",
        },
    ]


def build_dynamic_robustness_summary(summary: dict[str, Any], viewer_root: Path) -> dict[str, Any]:
    pairs = load_empirical_pairs(viewer_root)
    if not pairs:
        return {
            "schema_version": 1,
            "analysis_status": "missing_empirical_pairs",
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "claim_guardrail": "Robustness was not computed because paired empirical viewer records were unavailable.",
        }
    subject_bootstrap = _bootstrap_scores(summary)
    robustness = {
        "schema_version": 1,
        "analysis_status": "implemented_first_pass_robustness",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_viewer_root": viewer_root.as_posix(),
        "pair_count": len(pairs),
        "subject_count": len({pair.subject for pair in pairs}),
        "subject_bootstrap": subject_bootstrap,
        "run_sensitivity": _run_sensitivity(summary),
        "e_horizon_sensitivity": _horizon_sensitivity(pairs),
        "state_label_sensitivity": _state_label_sensitivity(pairs),
        "d_window_sensitivity": _window_sensitivity(pairs),
        "claim_guardrail": (
            "These robustness checks are in-sample stress tests on the cached LSD data. "
            "They do not replace the ds006072 cross-drug stress test, structural-connectome controls, "
            "PET receptor maps, or Schaefer/Yeo sensitivity."
        ),
    }
    literature = _literature_benchmark(summary)
    robustness["literature_benchmark"] = literature
    robustness["claim_verdicts"] = _claim_verdicts(summary, robustness, literature)
    return robustness


def write_dynamic_robustness_summary(summary: dict[str, Any], viewer_root: Path, output_dir: Path) -> dict[str, Any]:
    robustness = build_dynamic_robustness_summary(summary, viewer_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "robustness_summary.json"
    robustness["source_path"] = output_path.as_posix()
    output_path.write_text(json.dumps(robustness, indent=2), encoding="utf-8")
    return robustness
