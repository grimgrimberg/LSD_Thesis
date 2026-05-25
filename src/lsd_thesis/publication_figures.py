from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np

from lsd_thesis.publication import PublicationEvidence


@dataclass(slots=True)
class PublicationFigure:
    figure_id: str
    path: Path
    caption: str
    limitations: str


def _require_stage1_panel(stage1: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    baseline = stage1.get("baseline")
    perturbed = stage1.get("perturbed")
    if not isinstance(baseline, dict) or not isinstance(perturbed, dict):
        raise ValueError("stage1 evidence must include baseline and perturbed metric mappings")
    return baseline, perturbed


def _metric_value(panel: dict[str, Any], metric_name: str) -> float:
    if metric_name not in panel:
        raise ValueError(f"Missing stage1 metric '{metric_name}'")
    return float(panel[metric_name])


def _stage2_change_label(initial_score: float, best_score: float) -> str:
    delta = best_score - initial_score
    if delta < 0:
        return f"Change: decreased by {abs(delta):.2f}"
    if delta > 0:
        return f"Change: increased by {delta:.2f}"
    return "Change: no change"


def _save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _build_stage1_metric_shift_figure(evidence: PublicationEvidence, path: Path) -> PublicationFigure:
    baseline, perturbed = _require_stage1_panel(evidence.stage1)
    metrics = ("state_entropy", "switching_rate")
    metric_labels = ("State entropy\n(bits, proxy)", "Switching rate\n(transitions / step)")
    baseline_values = [_metric_value(baseline, metric) for metric in metrics]
    perturbed_values = [_metric_value(perturbed, metric) for metric in metrics]

    positions = np.arange(len(metrics))
    width = 0.34

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.bar(positions - width / 2, baseline_values, width=width, label="Baseline", color="#1d4ed8")
    ax.bar(positions + width / 2, perturbed_values, width=width, label="Perturbed", color="#d946ef")
    ax.set_xticks(positions)
    ax.set_xticklabels(metric_labels)
    ax.set_ylabel("Proxy metric value (metric-specific units)")
    ax.set_title("Stage 1 metric shift")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    _save_figure(fig, path)

    return PublicationFigure(
        figure_id="stage1_metric_shift",
        path=path,
        caption=(
            "Stage 1 compares baseline and perturbed proxy values for entropy and switching rate with units shown on the axis labels."
        ),
        limitations=(
            "These are surrogate macro-dynamics only. They do not claim receptor-level realism, "
            "subjective experience, or direct biological measurement."
        ),
    )


def _build_stage2_fit_robustness_figure(evidence: PublicationEvidence, path: Path) -> PublicationFigure:
    stage2 = evidence.stage2
    labels = ("Initial", "Selected score")
    values = (stage2.initial_score, stage2.best_score)
    colors = ("#0f172a", "#14b8a6")

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    bars = ax.bar(labels, values, color=colors, width=0.55)
    ax.set_ylabel("Objective score (unitless; lower is better)")
    ax.set_title("Stage 2 objective comparison")
    ax.grid(axis="y", alpha=0.2)
    ax.text(
        0.5,
        0.96,
        f"{_stage2_change_label(stage2.initial_score, stage2.best_score)}\n"
        f"Subjects: {stage2.subject_count}  Runs: {stage2.run_count}",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#cbd5e1"},
    )
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    summary_lines = []
    for metric_name in sorted(stage2.multi_seed_mean):
        mean_value = stage2.multi_seed_mean[metric_name]
        std_value = stage2.multi_seed_std.get(metric_name)
        if std_value is None:
            summary_lines.append(f"{metric_name}: {mean_value:.3f}")
        else:
            summary_lines.append(f"{metric_name}: {mean_value:.3f} +/- {std_value:.3f}")
    if summary_lines:
        ax.text(
            0.02,
            0.02,
            "\n".join(summary_lines),
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=8.5,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "#f8fafc", "edgecolor": "#cbd5e1"},
        )

    fig.tight_layout()
    _save_figure(fig, path)

    return PublicationFigure(
        figure_id="stage2_fit_robustness",
        path=path,
        caption=(
            "Stage 2 compares the initial objective with the selected score from the optimization step and summarizes limited repeatability evidence."
        ),
        limitations=(
            f"This figure summarizes a cached benchmark anchored to {stage2.dataset_anchor}. It is evidence of "
            "fit quality and run-to-run consistency, not a proof of generalization."
        ),
    )


def generate_publication_figures(
    evidence: PublicationEvidence,
    output_dir: str | Path,
) -> dict[str, PublicationFigure]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    figure_bundle = {
        "stage1_metric_shift": _build_stage1_metric_shift_figure(
            evidence,
            output_path / "stage1_metric_shift.png",
        ),
        "stage2_fit_robustness": _build_stage2_fit_robustness_figure(
            evidence,
            output_path / "stage2_fit_robustness.png",
        ),
    }
    return figure_bundle
