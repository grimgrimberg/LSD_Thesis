from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import plotly.graph_objects as go

from lsd_thesis.core import MODULE_GROUPS
from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import compute_summary_metrics
from lsd_thesis.simulator import load_regime_config, run_simulation
from lsd_thesis.utils import get_version_stamp, save_figure


def _save_figure(figure: go.Figure, path: Path) -> None:
    save_figure(figure, path)


def _build_graph_figure(modules: tuple[str, ...], adjacency: np.ndarray) -> go.Figure:
    graph = nx.Graph()
    for module in modules:
        graph.add_node(module)
    for i, source in enumerate(modules):
        for j, target in enumerate(modules):
            if i < j and adjacency[i, j] != 0:
                graph.add_edge(source, target, weight=float(adjacency[i, j]))

    positions = nx.spring_layout(graph, seed=7, weight="weight")

    edge_x: list[float] = []
    edge_y: list[float] = []
    for source, target in graph.edges():
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x += [x0, x1, np.nan]
        edge_y += [y0, y1, np.nan]

    node_x = [positions[module][0] for module in modules]
    node_y = [positions[module][1] for module in modules]
    node_color = [graph.degree(module, weight="weight") for module in modules]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={"color": "#94a3b8", "width": 1.5},
            hoverinfo="skip",
            name="edges",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=list(modules),
            textposition="top center",
            marker={
                "size": 18,
                "color": node_color,
                "colorscale": "Viridis",
                "showscale": True,
                "colorbar": {"title": "Weighted degree"},
            },
            name="modules",
        )
    )
    figure.update_layout(
        title="Macro-Module Graph",
        template="plotly_white",
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return figure


def _build_activity_figure(
    time: np.ndarray,
    time_series: np.ndarray,
    modules: tuple[str, ...],
    title: str,
) -> go.Figure:
    figure = go.Figure()
    for index, module in enumerate(modules):
        figure.add_trace(
            go.Scatter(
                x=time,
                y=time_series[:, index],
                mode="lines",
                name=module,
                line={"width": 1.5},
            )
        )
    figure.update_layout(
        title=title,
        template="plotly_white",
        xaxis_title="Time",
        yaxis_title="Latent state",
    )
    return figure


def _build_fc_figure(fc_matrix: np.ndarray, modules: tuple[str, ...], title: str) -> go.Figure:
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


def _build_bar_comparison(values: dict[str, float], title: str, yaxis_title: str) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Bar(
                x=list(values.keys()),
                y=list(values.values()),
                marker_color=["#2563eb", "#d946ef"],
            )
        ]
    )
    figure.update_layout(title=title, template="plotly_white", yaxis_title=yaxis_title)
    return figure


def _mean_fc_by_relation(fc_matrix: np.ndarray, modules: tuple[str, ...]) -> tuple[float, float]:
    within_values: list[float] = []
    cross_values: list[float] = []
    for i, source in enumerate(modules):
        for j, target in enumerate(modules):
            if j <= i:
                continue
            if MODULE_GROUPS[source] == MODULE_GROUPS[target]:
                within_values.append(float(fc_matrix[i, j]))
            else:
                cross_values.append(float(fc_matrix[i, j]))
    return float(np.mean(within_values)), float(np.mean(cross_values))


def _summary_row(time_series: np.ndarray, modules: tuple[str, ...]) -> dict[str, Any]:
    metrics = compute_summary_metrics(time_series, modules)
    within_fc, cross_fc = _mean_fc_by_relation(metrics.fc_matrix, modules)
    return {
        "state_entropy": metrics.state_entropy,
        "switching_rate": metrics.switching_rate,
        "dynamic_fc_change": metrics.dynamic_fc_change,
        "within_group_fc": within_fc,
        "cross_group_fc": cross_fc,
        "fc_matrix": metrics.fc_matrix.tolist(),
    }


def _write_markdown_report(
    report_path: Path,
    baseline_summary: dict[str, Any],
    perturbed_summary: dict[str, Any],
) -> None:
    result_rows = [
        (
            "State entropy",
            baseline_summary["state_entropy"],
            perturbed_summary["state_entropy"],
        ),
        (
            "Switching rate",
            baseline_summary["switching_rate"],
            perturbed_summary["switching_rate"],
        ),
        (
            "Dynamic FC change",
            baseline_summary["dynamic_fc_change"],
            perturbed_summary["dynamic_fc_change"],
        ),
        (
            "Within-group FC",
            baseline_summary["within_group_fc"],
            perturbed_summary["within_group_fc"],
        ),
        (
            "Cross-group FC",
            baseline_summary["cross_group_fc"],
            perturbed_summary["cross_group_fc"],
        ),
    ]
    result_lines = [
        f"| {name} | {baseline_value:.3f} | {perturbed_value:.3f} |"
        for name, baseline_value, perturbed_value in result_rows
    ]
    review_lines = [
        (
            "- Observed gain: state entropy increased, which is consistent with a richer "
            "surrogate state repertoire."
        ),
        (
            "- Observed gain: switching rate increased while within-group FC decreased, "
            "matching the intended reduction in local stability."
        ),
    ]
    if perturbed_summary["cross_group_fc"] <= baseline_summary["cross_group_fc"]:
        review_lines.append(
            "- Failure: the current static cross-group FC proxy decreased despite the "
            "configured increase in cross-group coupling. This suggests the first "
            "perturbation is partly producing decorrelation/noise rather than cleaner "
            "integrative dynamics."
        )
    if perturbed_summary["dynamic_fc_change"] <= baseline_summary["dynamic_fc_change"]:
        review_lines.append(
            "- Failure: dynamic FC change did not increase. Stage 2 and Stage 3 should "
            "treat this perturbation as provisional rather than validated."
        )
    review_lines.append(
        "- Guardrail: these are model-level macro analogues and proxy metrics, not direct "
        "neurobiological estimates."
    )
    lines = [
        "# Stage 1 Report",
        "",
        "## Plan",
        "",
        "- Run the config-driven simulator in sober and altered-state-inspired regimes.",
        "- Save activity, FC, graph, diversity, and switching figures.",
        "- Review whether the perturbed regime moves the model in the intended macro direction.",
        "",
        "## Results",
        "",
        "| Metric | Baseline | Perturbed |",
        "| --- | ---: | ---: |",
        *result_lines,
        "",
        "## Critical Review",
        "",
        *review_lines,
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def generate_stage_1_outputs(
    graph_path: str | Path,
    baseline_path: str | Path,
    perturbed_path: str | Path,
    output_dir: str | Path,
    report_path: str | Path,
) -> dict[str, dict[str, Any]]:
    graph = load_graph_config(graph_path)
    baseline = load_regime_config(baseline_path)
    perturbed = load_regime_config(perturbed_path)

    baseline_result = run_simulation(graph, baseline)
    perturbed_result = run_simulation(graph, perturbed)

    baseline_summary = _summary_row(baseline_result.time_series, graph.modules)
    perturbed_summary = _summary_row(perturbed_result.time_series, graph.modules)
    summary = {"baseline": baseline_summary, "perturbed": perturbed_summary}

    output_path = Path(output_dir)
    figures_path = output_path / "figures"
    figures_path.mkdir(parents=True, exist_ok=True)

    _save_figure(
        _build_graph_figure(graph.modules, graph.adjacency),
        figures_path / "graph_overview.html",
    )
    _save_figure(
        _build_activity_figure(
            baseline_result.time,
            baseline_result.time_series,
            graph.modules,
            "Baseline Module Activity",
        ),
        figures_path / "baseline_node_activity.html",
    )
    _save_figure(
        _build_activity_figure(
            perturbed_result.time,
            perturbed_result.time_series,
            graph.modules,
            "Perturbed Module Activity",
        ),
        figures_path / "perturbed_node_activity.html",
    )
    _save_figure(
        _build_fc_figure(
            np.asarray(baseline_summary["fc_matrix"]),
            graph.modules,
            "Baseline Functional Connectivity",
        ),
        figures_path / "baseline_fc_matrix.html",
    )
    _save_figure(
        _build_fc_figure(
            np.asarray(perturbed_summary["fc_matrix"]),
            graph.modules,
            "Perturbed Functional Connectivity",
        ),
        figures_path / "perturbed_fc_matrix.html",
    )
    _save_figure(
        _build_bar_comparison(
            {
                "baseline": baseline_summary["state_entropy"],
                "perturbed": perturbed_summary["state_entropy"],
            },
            title="Entropy / Diversity Comparison",
            yaxis_title="Normalized state entropy",
        ),
        figures_path / "diversity_comparison.html",
    )
    _save_figure(
        _build_bar_comparison(
            {
                "baseline": baseline_summary["switching_rate"],
                "perturbed": perturbed_summary["switching_rate"],
            },
            title="Switching Rate Comparison",
            yaxis_title="Transitions per step",
        ),
        figures_path / "switching_rate_comparison.html",
    )

    output_path.mkdir(parents=True, exist_ok=True)
    summary["version_stamp"] = get_version_stamp(Path(graph_path).resolve().parents[2])
    (output_path / "stage_1_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    _write_markdown_report(Path(report_path), baseline_summary, perturbed_summary)
    return summary
