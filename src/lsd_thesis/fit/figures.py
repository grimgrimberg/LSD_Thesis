from __future__ import annotations

from pathlib import Path

import numpy as np
import plotly.graph_objects as go

from lsd_thesis.data.targets import SoberTargetSet
from lsd_thesis.utils import save_figure


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
