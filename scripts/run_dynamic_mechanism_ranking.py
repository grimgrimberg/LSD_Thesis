from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import plotly.graph_objects as go

from lsd_thesis.dynamic_mechanism import write_dynamic_mechanism_summary
from lsd_thesis.dynamic_robustness import write_dynamic_robustness_summary


def _save_figure(figure: go.Figure, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(str(path), include_plotlyjs="cdn")
    return path.as_posix()


def _transition_figure(summary: dict[str, Any]) -> go.Figure:
    rows = summary["transition_proxy"]["metric_deltas"]
    figure = go.Figure(
        data=[
            go.Bar(
                x=[row["metric"] for row in rows],
                y=[row["mean_delta"] for row in rows],
                error_y={
                    "type": "data",
                    "array": [row["std_delta"] for row in rows],
                    "visible": True,
                },
                marker={"color": "#0f766e"},
                hovertext=[row["expected_direction"] for row in rows],
            )
        ]
    )
    figure.update_layout(
        title="A: Transition-State Proxy Deltas (LSD - Placebo)",
        xaxis_title="Transition proxy metric",
        yaxis_title="Mean paired delta",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return figure


def _metric_delta_figure(rows: list[dict[str, Any]], title: str, color: str) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Bar(
                x=[row["metric"] for row in rows],
                y=[row["mean_delta"] for row in rows],
                error_y={
                    "type": "data",
                    "array": [row["std_delta"] for row in rows],
                    "visible": True,
                },
                marker={"color": color},
                hovertext=[
                    f"{row.get('expected_direction', '')}<br>"
                    f"signed effect: {float(row.get('signed_effect_size', 0.0)):.4g}<br>"
                    f"sign consistency: {float(row.get('sign_consistency', 0.0)):.3g}"
                    for row in rows
                ],
            )
        ]
    )
    figure.update_layout(
        title=title,
        xaxis_title="Proxy metric",
        yaxis_title="Mean paired delta",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return figure


def _dmdc_figure(summary: dict[str, Any]) -> go.Figure:
    dmdc = summary["dmdc"]
    rows = dmdc.get("fold_rows", [])
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            name="No input",
            x=[row["held_out_subject"] for row in rows],
            y=[row["rmse_no_input"] for row in rows],
            marker={"color": "#64748b"},
        )
    )
    figure.add_trace(
        go.Bar(
            name="Condition input",
            x=[row["held_out_subject"] for row in rows],
            y=[row["rmse_condition_input"] for row in rows],
            marker={"color": "#b45309"},
        )
    )
    figure.add_trace(
        go.Bar(
            name="Condition interaction",
            x=[row["held_out_subject"] for row in rows],
            y=[row.get("rmse_condition_interaction") for row in rows],
            marker={"color": "#7c3aed"},
        )
    )
    figure.update_layout(
        title="B: DMDc Leave-One-Subject-Out One-Step Error",
        xaxis_title="Held-out subject",
        yaxis_title="RMSE",
        barmode="group",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return figure


def _condition_vector_figure(summary: dict[str, Any], key: str, title: str, color: str) -> go.Figure:
    rows = summary["dmdc"].get(key, [])
    figure = go.Figure(
        data=[
            go.Bar(
                x=[row["module"] for row in rows],
                y=[row["coefficient"] for row in rows],
                marker={"color": color},
            )
        ]
    )
    figure.update_layout(
        title=title,
        xaxis_title="Module",
        yaxis_title="Coefficient",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return figure


def _write_tables(summary: dict[str, Any], output_dir: Path) -> None:
    metric_fields = [
        "metric",
        "mean_delta",
        "std_delta",
        "effect_size",
        "signed_effect_size",
        "expected_sign",
        "sign_consistency",
        "sign_flip_p_value",
        "expected_direction",
    ]
    for section_key, filename in (
        ("transition_proxy", "transition_metric_deltas.csv"),
        ("hierarchy_routing", "hierarchy_routing_metric_deltas.csv"),
        ("dynamic_repertoire", "dynamic_repertoire_metric_deltas.csv"),
        ("network_control_energy", "network_control_energy_metric_deltas.csv"),
    ):
        path = output_dir / filename
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=metric_fields)
            writer.writeheader()
            writer.writerows(summary[section_key]["metric_deltas"])

    for section_key, filename in (
        ("transition_proxy", "transition_run_metric_deltas.csv"),
        ("hierarchy_routing", "hierarchy_routing_run_metric_deltas.csv"),
        ("dynamic_repertoire", "dynamic_repertoire_run_metric_deltas.csv"),
        ("network_control_energy", "network_control_energy_run_metric_deltas.csv"),
    ):
        path = output_dir / filename
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["run", *metric_fields])
            writer.writeheader()
            writer.writerows(summary[section_key].get("run_metric_deltas", []))

    network_energy_path = output_dir / "network_control_energy_profiles.csv"
    with network_energy_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["subject", "run", "profile", "mean_control_energy", "matched_state_count"],
        )
        writer.writeheader()
        writer.writerows(summary["network_control_energy"].get("energy_rows", []))

    dmdc_path = output_dir / "dmdc_loso_folds.csv"
    with dmdc_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "held_out_subject",
                "sample_count",
                "rmse_no_input",
                "rmse_condition_input",
                "rmse_condition_interaction",
                "rmse_improvement",
                "relative_improvement_pct",
                "condition_bias_rmse_improvement",
                "condition_bias_relative_improvement_pct",
                "condition_interaction_rmse_improvement",
                "condition_interaction_relative_improvement_pct",
            ],
        )
        writer.writeheader()
        writer.writerows(summary["dmdc"].get("fold_rows", []))


def _write_generic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_robustness_tables(robustness: dict[str, Any], output_dir: Path) -> dict[str, str]:
    robustness_dir = output_dir / "robustness"
    written: dict[str, str] = {}
    table_specs = {
        "bootstrap_layer_summary": robustness.get("subject_bootstrap", {}).get("layer_summary", []),
        "bootstrap_score_rows": robustness.get("subject_bootstrap", {}).get("bootstrap_score_rows", []),
        "run_sensitivity": robustness.get("run_sensitivity", {}).get("run_rows", []),
        "e_horizon_sensitivity": robustness.get("e_horizon_sensitivity", {}).get("rows", []),
        "state_label_sensitivity": robustness.get("state_label_sensitivity", {}).get("rows", []),
        "d_window_sensitivity": robustness.get("d_window_sensitivity", {}).get("rows", []),
        "literature_benchmark": robustness.get("literature_benchmark", {}).get("rows", []),
        "claim_verdicts": robustness.get("claim_verdicts", []),
    }
    for name, rows in table_specs.items():
        path = robustness_dir / f"{name}.csv"
        _write_generic_csv(path, rows)
        written[name] = path.as_posix()
    return written


def _write_markdown_report(summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    ranking_rows = summary.get("mechanism_ranking", [])
    transition_rows = summary["transition_proxy"]["metric_deltas"]
    hierarchy_rows = summary["hierarchy_routing"]["metric_deltas"]
    repertoire_rows = summary["dynamic_repertoire"]["metric_deltas"]
    control_rows = summary["network_control_energy"]["metric_deltas"]
    dmdc = summary["dmdc"]
    network_control = summary["network_control_energy"]
    lines = [
        "# Dynamic Mechanism Ranking: A+B+C+D+E Proxy-Control Pass",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Scope",
        "",
        summary["claim_guardrail"],
        "",
        f"- Dataset scope: {summary['dataset_scope']}",
        f"- Paired subject/run records: {summary['pair_count']}",
        f"- Subjects: {summary['subject_count']}",
        f"- Runs: {', '.join(summary['runs'])}",
        "",
        "## Mechanism Ranking",
        "",
        "| Rank | Layer | Mechanism | Status | Score | Evidence |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in ranking_rows:
        rank = row["rank"] if row["rank"] is not None else "not ranked"
        score = f"{row['score']:.6g}" if isinstance(row.get("score"), (int, float)) else "n/a"
        lines.append(f"| {rank} | {row['layer']} | `{row['mechanism']}` | {row['status']} | {score} | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Literature Grounding",
            "",
            "| Layer | What it supports | Source |",
            "| --- | --- | --- |",
        ]
    )
    for row in summary.get("literature_support", []):
        lines.append(f"| {row['layer']} | {row['claim_supported']} | [{row['source']}]({row['url']}) |")
    lines.extend(
        [
            "",
            "## A. Transition-State Proxy",
            "",
            summary["transition_proxy"]["claim_guardrail"],
            "",
            "| Metric | Mean Delta | SD | Signed Effect | Direction |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in transition_rows:
        lines.append(
            f"| `{row['metric']}` | {row['mean_delta']:.6g} | {row['std_delta']:.6g} | "
            f"{row['signed_effect_size']:.6g} | {row['expected_direction']} "
            f"(sign consistency {row['sign_consistency']:.3g}, sign-test p={row['sign_flip_p_value']:.3g}) |"
        )
    lines.extend(
        [
            "",
            "## B. DMDc / Controlled Dynamics",
            "",
            dmdc["claim_guardrail"],
            "",
            f"- Validation: {dmdc['validation']}",
            f"- Selected variant for B score: `{dmdc['selected_variant']}`",
            f"- Ridge alpha: {dmdc['ridge_alpha']}",
            f"- Fold count: {dmdc['fold_count']}",
            f"- No-input RMSE: {dmdc['rmse_no_input_mean']:.6g} +/- {dmdc['rmse_no_input_std']:.6g}",
            f"- Condition-bias RMSE: {dmdc['rmse_condition_input_mean']:.6g} +/- {dmdc['rmse_condition_input_std']:.6g}",
            f"- Condition-interaction RMSE: {dmdc['rmse_condition_interaction_mean']:.6g} +/- {dmdc['rmse_condition_interaction_std']:.6g}",
            f"- Condition-bias relative RMSE improvement: {dmdc['relative_improvement_pct_mean']:.6g}% +/- {dmdc['relative_improvement_pct_std']:.6g}%",
            (
                "- Condition-interaction relative RMSE improvement: "
                f"{dmdc['condition_interaction_relative_improvement_pct_mean']:.6g}% +/- "
                f"{dmdc['condition_interaction_relative_improvement_pct_std']:.6g}%"
            ),
            "",
            (
                "Interpretation: B is only evidence for controlled dynamics if the held-out condition-interaction "
                "variant improves one-step prediction. A near-zero or negative improvement is a meaningful negative result."
            ),
            "",
            "## C. Hierarchy / Routing Evidence Layer",
            "",
            summary["hierarchy_routing"]["claim_guardrail"],
            "",
            "| Metric | Mean Delta | SD | Signed Effect | Direction |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in hierarchy_rows:
        lines.append(
            f"| `{row['metric']}` | {row['mean_delta']:.6g} | {row['std_delta']:.6g} | "
            f"{row['signed_effect_size']:.6g} | {row['expected_direction']} "
            f"(sign consistency {row['sign_consistency']:.3g}, sign-test p={row['sign_flip_p_value']:.3g}) |"
        )
    lines.extend(
        [
            "",
            "## D. Dynamic Repertoire Evidence Layer",
            "",
            summary["dynamic_repertoire"]["claim_guardrail"],
            "",
            "| Metric | Mean Delta | SD | Signed Effect | Direction |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in repertoire_rows:
        lines.append(
            f"| `{row['metric']}` | {row['mean_delta']:.6g} | {row['std_delta']:.6g} | "
            f"{row['signed_effect_size']:.6g} | {row['expected_direction']} "
            f"(sign consistency {row['sign_consistency']:.3g}, sign-test p={row['sign_flip_p_value']:.3g}) |"
        )
    lines.extend(
        [
            "",
            "## E. Receptor-Informed Network-Control Energy",
            "",
            network_control["claim_guardrail"],
            "",
            f"- Method: {network_control['method']}",
            f"- Equation: `{network_control['equation']}`",
            f"- Horizon: {network_control['horizon']}",
            f"- Graph source: {network_control['graph_source']}",
            f"- Structural connectome: {network_control['graph_is_structural_connectome']}",
            f"- Receptor prior source: {network_control['receptor_prior_source']}",
            f"- Random receptor-prior permutation nulls per pair: {network_control['random_null_count']}",
            "",
            "| Metric | Mean Value | SD | Signed Effect | Direction |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in control_rows:
        lines.append(
            f"| `{row['metric']}` | {row['mean_delta']:.6g} | {row['std_delta']:.6g} | "
            f"{row['signed_effect_size']:.6g} | {row['expected_direction']} "
            f"(sign consistency {row['sign_consistency']:.3g}, sign-test p={row['sign_flip_p_value']:.3g}) |"
        )
    robustness = summary.get("robustness", {})
    if robustness:
        bootstrap_rows = robustness.get("subject_bootstrap", {}).get("layer_summary", [])
        horizon_rows = robustness.get("e_horizon_sensitivity", {}).get("rows", [])
        literature_rows = robustness.get("literature_benchmark", {}).get("rows", [])
        claim_rows = robustness.get("claim_verdicts", [])
        lines.extend(
            [
                "",
                "## Robustness And Literature Benchmark",
                "",
                robustness.get("claim_guardrail", "Robustness artifacts are not loaded."),
                "",
                "### Subject Bootstrap",
                "",
                "| Layer | Score Mean | 95% Bootstrap Interval | Rank-1 Fraction | Median Rank |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in bootstrap_rows:
            lines.append(
                f"| {row['layer']} | {row['score_mean']:.6g} | "
                f"{row['score_ci_low']:.6g} to {row['score_ci_high']:.6g} | "
                f"{row['rank_1_fraction']:.3g} | {row['median_rank']:.3g} |"
            )
        lines.extend(
            [
                "",
                "### E Horizon Sensitivity",
                "",
                "| Horizon | E Support Score | LSD Receptor Energy Reduction % | Receptor vs Random Energy Reduction % |",
                "| ---: | ---: | ---: | ---: |",
            ]
        )
        for row in horizon_rows:
            lines.append(
                f"| {row['horizon']} | {row['support_score']:.6g} | "
                f"{row['lsd_receptor_energy_reduction_pct']:.6g} | "
                f"{row['receptor_vs_random_energy_reduction_pct']:.6g} |"
            )
        lines.extend(
            [
                "",
                "### Claim Verdicts",
                "",
                "| Claim | Verdict | Evidence | Next Action |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in claim_rows:
            lines.append(f"| {row['claim']} | {row['verdict']} | {row['evidence']} | {row['next_action']} |")
        lines.extend(
            [
                "",
                "### Literature Benchmark",
                "",
                "| Benchmark | Layer | Metric | Status | Observed Delta | Caveat |",
                "| --- | --- | --- | --- | ---: | --- |",
            ]
        )
        for row in literature_rows:
            observed = row.get("observed_mean_delta")
            observed_text = f"{observed:.6g}" if isinstance(observed, int | float) else "n/a"
            lines.append(
                f"| {row['benchmark']} | {row['layer']} | `{row['project_metric']}` | "
                f"{row['status']} | {observed_text} | {row['caveat']} |"
            )
    lines.extend(
        [
            "",
            "## Generated Artifacts",
            "",
            "- `results/dynamic_mechanism_ranking/summary.json`",
            "- `results/dynamic_mechanism_ranking/transition_metric_deltas.csv`",
            "- `results/dynamic_mechanism_ranking/hierarchy_routing_metric_deltas.csv`",
            "- `results/dynamic_mechanism_ranking/dynamic_repertoire_metric_deltas.csv`",
            "- `results/dynamic_mechanism_ranking/network_control_energy_metric_deltas.csv`",
            "- `results/dynamic_mechanism_ranking/network_control_energy_profiles.csv`",
            "- `results/dynamic_mechanism_ranking/dmdc_loso_folds.csv`",
            "- `results/dynamic_mechanism_ranking/figures/transition_proxy_deltas.html`",
            "- `results/dynamic_mechanism_ranking/figures/dmdc_fold_rmse.html`",
            "- `results/dynamic_mechanism_ranking/figures/dmdc_condition_vector.html`",
            "- `results/dynamic_mechanism_ranking/figures/dmdc_condition_interaction_vector.html`",
            "- `results/dynamic_mechanism_ranking/figures/hierarchy_routing_deltas.html`",
            "- `results/dynamic_mechanism_ranking/figures/dynamic_repertoire_deltas.html`",
            "- `results/dynamic_mechanism_ranking/figures/network_control_energy.html`",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["limitations"])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _robustness_bootstrap_figure(robustness: dict[str, Any]) -> go.Figure:
    rows = robustness.get("subject_bootstrap", {}).get("layer_summary", [])
    y = [float(row.get("score_mean", 0.0)) for row in rows]
    ci_high = [max(0.0, float(row.get("score_ci_high", 0.0)) - value) for row, value in zip(rows, y, strict=True)]
    ci_low = [max(0.0, value - float(row.get("score_ci_low", 0.0))) for row, value in zip(rows, y, strict=True)]
    figure = go.Figure(
        data=[
            go.Bar(
                x=[row.get("layer") for row in rows],
                y=y,
                error_y={"type": "data", "array": ci_high, "arrayminus": ci_low, "visible": True},
                marker={"color": "#0f766e"},
                hovertext=[
                    f"rank-1 fraction: {float(row.get('rank_1_fraction', 0.0)):.3g}<br>"
                    f"median rank: {float(row.get('median_rank', 0.0)):.3g}"
                    for row in rows
                ],
            )
        ]
    )
    figure.update_layout(
        title="Robustness: Subject Bootstrap Layer Scores",
        xaxis_title="Layer",
        yaxis_title="Bootstrap mean support score",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return figure


def _run_sensitivity_figure(robustness: dict[str, Any]) -> go.Figure:
    rows = robustness.get("run_sensitivity", {}).get("run_rows", [])
    runs = sorted({row.get("run") for row in rows})
    figure = go.Figure()
    for run in runs:
        run_rows = [row for row in rows if row.get("run") == run]
        figure.add_trace(
            go.Bar(
                name=str(run),
                x=[row.get("layer") for row in run_rows],
                y=[row.get("support_score") for row in run_rows],
            )
        )
    figure.update_layout(
        title="Robustness: Run-01 vs Run-03 Support Scores",
        xaxis_title="Layer",
        yaxis_title="Support score",
        barmode="group",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return figure


def _horizon_sensitivity_figure(robustness: dict[str, Any]) -> go.Figure:
    rows = robustness.get("e_horizon_sensitivity", {}).get("rows", [])
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            name="E support score",
            x=[row.get("horizon") for row in rows],
            y=[row.get("support_score") for row in rows],
            mode="lines+markers",
            line={"color": "#4338ca"},
        )
    )
    figure.add_trace(
        go.Scatter(
            name="LSD receptor energy reduction %",
            x=[row.get("horizon") for row in rows],
            y=[row.get("lsd_receptor_energy_reduction_pct") for row in rows],
            mode="lines+markers",
            yaxis="y2",
            line={"color": "#b45309"},
        )
    )
    figure.update_layout(
        title="Robustness: E Horizon Sensitivity",
        xaxis_title="Control horizon",
        yaxis={"title": "Support score"},
        yaxis2={"title": "Energy reduction %", "overlaying": "y", "side": "right"},
        legend={"orientation": "h"},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return figure


def _window_sensitivity_figure(robustness: dict[str, Any]) -> go.Figure:
    rows = robustness.get("d_window_sensitivity", {}).get("rows", [])
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            name="D support score",
            x=[row.get("window_size") for row in rows],
            y=[row.get("support_score") for row in rows],
            mode="lines+markers",
            line={"color": "#0f766e"},
        )
    )
    figure.add_trace(
        go.Scatter(
            name="dynamic FC variance delta",
            x=[row.get("window_size") for row in rows],
            y=[row.get("dynamic_fc_variance_delta") for row in rows],
            mode="lines+markers",
            yaxis="y2",
            line={"color": "#be123c"},
        )
    )
    figure.update_layout(
        title="Robustness: D Dynamic-FC Window Sensitivity",
        xaxis_title="Window size",
        yaxis={"title": "Support score"},
        yaxis2={"title": "Dynamic-FC variance delta", "overlaying": "y", "side": "right"},
        legend={"orientation": "h"},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return figure


def _literature_benchmark_figure(robustness: dict[str, Any]) -> go.Figure:
    rows = robustness.get("literature_benchmark", {}).get("rows", [])
    color_map = {"aligned": "#277342", "opposes_or_weak": "#b9402a", "missing_required_region": "#9b6818", "missing": "#9b6818"}
    figure = go.Figure(
        data=[
            go.Bar(
                x=[row.get("benchmark") for row in rows],
                y=[
                    1 if row.get("sign_match") is True else -1 if row.get("sign_match") is False else 0
                    for row in rows
                ],
                marker={"color": [color_map.get(str(row.get("status")), "#64748b") for row in rows]},
                hovertext=[
                    f"{row.get('source')}<br>{row.get('interpretation')}<br>{row.get('caveat')}"
                    for row in rows
                ],
            )
        ]
    )
    figure.update_layout(
        title="Literature Benchmark: Directional Proxy Alignment",
        xaxis_title="Benchmark",
        yaxis_title="Aligned = 1, opposed = -1, missing = 0",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return figure


def write_robustness_figures(robustness: dict[str, Any], output_dir: Path) -> dict[str, str]:
    figures_dir = output_dir / "figures"
    return {
        "robustness_bootstrap": _save_figure(
            _robustness_bootstrap_figure(robustness),
            figures_dir / "robustness_bootstrap_layer_scores.html",
        ),
        "robustness_run_sensitivity": _save_figure(
            _run_sensitivity_figure(robustness),
            figures_dir / "robustness_run_sensitivity.html",
        ),
        "robustness_e_horizon": _save_figure(
            _horizon_sensitivity_figure(robustness),
            figures_dir / "robustness_e_horizon_sensitivity.html",
        ),
        "robustness_d_window": _save_figure(
            _window_sensitivity_figure(robustness),
            figures_dir / "robustness_d_window_sensitivity.html",
        ),
        "literature_benchmark": _save_figure(
            _literature_benchmark_figure(robustness),
            figures_dir / "literature_benchmark_alignment.html",
        ),
    }


def write_dynamic_figures(summary: dict[str, Any], output_dir: Path) -> dict[str, str]:
    figures_dir = output_dir / "figures"
    return {
        "transition_proxy": _save_figure(_transition_figure(summary), figures_dir / "transition_proxy_deltas.html"),
        "dmdc_fold_rmse": _save_figure(_dmdc_figure(summary), figures_dir / "dmdc_fold_rmse.html"),
        "dmdc_condition_vector": _save_figure(
            _condition_vector_figure(
                summary,
                "condition_input_vector",
                "B: Mean DMDc Condition-Bias Vector",
                "#2563eb",
            ),
            figures_dir / "dmdc_condition_vector.html",
        ),
        "dmdc_condition_interaction_vector": _save_figure(
            _condition_vector_figure(
                summary,
                "condition_interaction_vector",
                "B: Mean DMDc Condition-Interaction Vector",
                "#7c3aed",
            ),
            figures_dir / "dmdc_condition_interaction_vector.html",
        ),
        "hierarchy_routing": _save_figure(
            _metric_delta_figure(
                summary["hierarchy_routing"]["metric_deltas"],
                "C: Hierarchy / Routing Proxy Deltas (LSD - Placebo)",
                "#be123c",
            ),
            figures_dir / "hierarchy_routing_deltas.html",
        ),
        "dynamic_repertoire": _save_figure(
            _metric_delta_figure(
                summary["dynamic_repertoire"]["metric_deltas"],
                "D: Dynamic Repertoire Proxy Deltas (LSD - Placebo)",
                "#0f766e",
            ),
            figures_dir / "dynamic_repertoire_deltas.html",
        ),
        "network_control_energy": _save_figure(
            _metric_delta_figure(
                summary["network_control_energy"]["metric_deltas"],
                "E: Receptor-Informed Network-Control Energy Support Metrics",
                "#4338ca",
            ),
            figures_dir / "network_control_energy.html",
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build A+B+C+D+E dynamic mechanism ranking artifacts from cached empirical viewer data.")
    parser.add_argument("--viewer-root", default="results/stage_2/empirical_viewer", help="Stage 2 empirical viewer cache root.")
    parser.add_argument("--output-dir", default="results/dynamic_mechanism_ranking", help="Output directory for ranking artifacts.")
    parser.add_argument("--report-path", default="docs/stage_reports/dynamic_mechanism_ranking.md", help="Markdown report path.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    viewer_root = Path(args.viewer_root)
    summary = write_dynamic_mechanism_summary(viewer_root, output_dir)
    robustness = write_dynamic_robustness_summary(summary, viewer_root, output_dir / "robustness")
    figure_paths = write_dynamic_figures(summary, output_dir)
    robustness["figure_paths"] = write_robustness_figures(robustness, output_dir)
    robustness["table_paths"] = _write_robustness_tables(robustness, output_dir)
    summary["robustness"] = robustness
    summary["literature_benchmark"] = robustness.get("literature_benchmark")
    summary["claim_verdicts"] = robustness.get("claim_verdicts", [])
    figure_paths.update(robustness["figure_paths"])
    summary["figure_paths"] = figure_paths
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_tables(summary, output_dir)
    _write_markdown_report(summary, Path(args.report_path))

    print(f"wrote {output_dir / 'summary.json'}")
    print(f"wrote {args.report_path}")
    print(f"pair_count={summary['pair_count']}")
    print(f"dmdc_relative_improvement_pct_mean={summary['dmdc'].get('relative_improvement_pct_mean', 'n/a')}")


if __name__ == "__main__":
    main()
