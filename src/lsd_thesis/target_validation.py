from __future__ import annotations

import csv
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from lsd_thesis.data.parcellations import get_parcellation_spec
from lsd_thesis.metrics_literature import compute_literature_metrics
from lsd_thesis.utils import resolve_under


def _finite_metric_map(metrics: Mapping[str, Any]) -> dict[str, float]:
    output: dict[str, float] = {}
    for key, value in metrics.items():
        if not isinstance(value, int | float | np.integer | np.floating):
            continue
        number = float(value)
        if np.isfinite(number):
            output[str(key)] = number
    return output


def _format_float(value: float | None) -> str:
    if value is None:
        return ""
    if not np.isfinite(value):
        return ""
    return f"{float(value):.12g}"


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))


def bootstrap_ci(
    values: Iterable[float],
    seed: int = 0,
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
) -> dict[str, float | int]:
    data = np.asarray([float(value) for value in values if np.isfinite(float(value))], dtype=float)
    if len(data) == 0:
        return {"n": 0, "mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n_bootstrap": int(n_bootstrap)}
    if len(data) == 1 or n_bootstrap <= 0:
        mean_value = round(float(np.mean(data)), 12)
        return {
            "n": int(len(data)),
            "mean": mean_value,
            "ci_low": mean_value,
            "ci_high": mean_value,
            "n_bootstrap": int(max(n_bootstrap, 0)),
        }

    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(data), size=(int(n_bootstrap), len(data)))
    boot_means = np.mean(data[indices], axis=1)
    ci_low, ci_high = np.quantile(boot_means, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {
        "n": int(len(data)),
        "mean": round(float(np.mean(data)), 12),
        "ci_low": round(float(ci_low), 12),
        "ci_high": round(float(ci_high), 12),
        "n_bootstrap": int(n_bootstrap),
    }


def _session_metric_means(records: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, float]]:
    grouped: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    for record in records:
        subject = str(record.get("subject", ""))
        session = str(record.get("session", ""))
        if not subject or not session:
            continue
        metrics = _finite_metric_map(record.get("metrics", {}))
        if metrics:
            grouped[(subject, session)].append(metrics)

    session_means: dict[tuple[str, str], dict[str, float]] = {}
    for key, rows in grouped.items():
        metric_names = sorted(set().union(*(row.keys() for row in rows)))
        means: dict[str, float] = {}
        for metric_name in metric_names:
            values = [row[metric_name] for row in rows if metric_name in row]
            if values:
                means[metric_name] = float(np.mean(values))
        session_means[key] = means
    return session_means


def _paired_metric_deltas(
    session_means: Mapping[tuple[str, str], Mapping[str, float]],
) -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
    paired_subjects = sorted(
        subject
        for subject, session in session_means
        if session == "ses-PLCB" and (subject, "ses-LSD") in session_means
    )
    deltas: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for subject in paired_subjects:
        placebo = session_means[(subject, "ses-PLCB")]
        lsd = session_means[(subject, "ses-LSD")]
        for metric_name in sorted(set(placebo).intersection(lsd)):
            deltas[metric_name].append(
                {
                    "subject": subject,
                    "delta": float(lsd[metric_name]) - float(placebo[metric_name]),
                    "placebo": float(placebo[metric_name]),
                    "lsd": float(lsd[metric_name]),
                }
            )
    return paired_subjects, deltas


def _delta_rows(
    deltas: Mapping[str, list[dict[str, Any]]],
    n_bootstrap: int,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, float | int]]]:
    summary: dict[str, dict[str, float | int]] = {}
    delta_rows: list[dict[str, Any]] = []
    ci_rows: list[dict[str, Any]] = []
    for metric_index, metric_name in enumerate(sorted(deltas)):
        values = [float(row["delta"]) for row in deltas[metric_name]]
        ci = bootstrap_ci(values, seed=seed + metric_index, n_bootstrap=n_bootstrap)
        std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        summary[metric_name] = {
            "delta_mean": float(ci["mean"]),
            "delta_std": std,
            "paired_subject_count": len(values),
            "ci_low": float(ci["ci_low"]),
            "ci_high": float(ci["ci_high"]),
        }
        delta_rows.append(
            {
                "metric": metric_name,
                "delta_mean": _format_float(float(ci["mean"])),
                "delta_std": _format_float(std),
                "paired_subject_count": len(values),
            }
        )
        ci_rows.append(
            {
                "metric": metric_name,
                "mean": _format_float(float(ci["mean"])),
                "ci_low": _format_float(float(ci["ci_low"])),
                "ci_high": _format_float(float(ci["ci_high"])),
                "n_bootstrap": int(ci["n_bootstrap"]),
            }
        )
    return delta_rows, ci_rows, summary


def _leave_one_subject_out_rows(
    paired_subjects: list[str],
    deltas: Mapping[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric_name in sorted(deltas):
        values_by_subject = {
            str(row["subject"]): float(row["delta"])
            for row in deltas[metric_name]
        }
        for subject in paired_subjects:
            remaining = [
                value for candidate, value in values_by_subject.items()
                if candidate != subject
            ]
            rows.append(
                {
                    "metric": metric_name,
                    "left_out_subject": subject,
                    "delta_mean": _format_float(float(np.mean(remaining)) if remaining else 0.0),
                    "remaining_subject_count": len(remaining),
                }
            )
    return rows


def _run_split_rows(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_run: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        run = str(record.get("run", "unknown"))
        by_run[run].append(record)

    rows: list[dict[str, Any]] = []
    for run, run_records in sorted(by_run.items()):
        session_means = _session_metric_means(list(run_records))
        _, deltas = _paired_metric_deltas(session_means)
        for metric_name in sorted(deltas):
            values = [float(row["delta"]) for row in deltas[metric_name]]
            rows.append(
                {
                    "run": run,
                    "metric": metric_name,
                    "delta_mean": _format_float(float(np.mean(values)) if values else 0.0),
                    "paired_subject_count": len(values),
                }
            )
    return rows


def _write_stage_2b_report(
    report_path: Path,
    summary: Mapping[str, Any],
    metric_summary: Mapping[str, Mapping[str, Any]],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage 2b Literature-Metric Target Validation",
        "",
        "This report summarizes literature-aligned proxy metrics on cached empirical resting-state records.",
        "It does not add receptor-level or subjective-experience claims.",
        "",
        "## Summary",
        "",
        f"- Status: {summary['status']}",
        f"- Source: {summary['source']}",
        f"- Records: {summary['record_count']}",
        f"- Paired subjects: {summary['paired_subject_count']}",
        f"- Metrics with paired deltas: {summary['metric_count']}",
        "",
        "## Metric Deltas",
        "",
        "| Metric | LSD - placebo mean | 95% bootstrap CI | Paired subjects |",
        "| --- | ---: | ---: | ---: |",
    ]
    for metric_name in sorted(metric_summary):
        row = metric_summary[metric_name]
        lines.append(
            "| "
            f"{metric_name} | "
            f"{_format_float(float(row['delta_mean']))} | "
            f"{_format_float(float(row['ci_low']))} to {_format_float(float(row['ci_high']))} | "
            f"{int(row['paired_subject_count'])} |"
        )
    if not metric_summary:
        lines.append("| none |  |  | 0 |")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- These are macro-dynamic target checks in the available parcellation space.",
            "- Sign conflicts or weak stability should be treated as model failure evidence, not polished away.",
            "- Schaefer/Yeo outputs remain metadata-prepared until real extraction is run.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_stage_2b_outputs(
    records: Sequence[Mapping[str, Any]],
    output_dir: str | Path,
    report_path: str | Path,
    seed: int = 0,
    n_bootstrap: int = 500,
    source: str = "provided_records",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    resolved_records = [dict(record) for record in records]
    session_means = _session_metric_means(resolved_records)
    paired_subjects, deltas = _paired_metric_deltas(session_means)
    delta_rows, ci_rows, metric_summary = _delta_rows(deltas, n_bootstrap=n_bootstrap, seed=seed)
    leave_one_rows = _leave_one_subject_out_rows(paired_subjects, deltas)
    run_split_rows = _run_split_rows(resolved_records)

    summary = {
        "status": "complete" if metric_summary else "blocked_no_paired_metric_deltas",
        "source": source,
        "record_count": len(resolved_records),
        "paired_subjects": paired_subjects,
        "paired_subject_count": len(paired_subjects),
        "metric_count": len(metric_summary),
        "metrics": metric_summary,
        "outputs": {
            "target_reliability_summary": str(output_path / "target_reliability_summary.json"),
            "literature_metric_deltas": str(output_path / "literature_metric_deltas.csv"),
            "bootstrap_metric_cis": str(output_path / "bootstrap_metric_cis.csv"),
            "leave_one_subject_out": str(output_path / "leave_one_subject_out.csv"),
            "run_split_stability": str(output_path / "run_split_stability.csv"),
            "report": str(report_path),
        },
        "notes": [
            "Deltas are paired LSD minus placebo session means.",
            "Only finite scalar literature metrics are included in CSV target validation.",
            "This is empirical target validation, not a pharmacological mechanism claim.",
        ],
    }

    (output_path / "target_reliability_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    _write_csv(
        output_path / "literature_metric_deltas.csv",
        ["metric", "delta_mean", "delta_std", "paired_subject_count"],
        delta_rows,
    )
    _write_csv(
        output_path / "bootstrap_metric_cis.csv",
        ["metric", "mean", "ci_low", "ci_high", "n_bootstrap"],
        ci_rows,
    )
    _write_csv(
        output_path / "leave_one_subject_out.csv",
        ["metric", "left_out_subject", "delta_mean", "remaining_subject_count"],
        leave_one_rows,
    )
    _write_csv(
        output_path / "run_split_stability.csv",
        ["run", "metric", "delta_mean", "paired_subject_count"],
        run_split_rows,
    )
    _write_stage_2b_report(Path(report_path), summary, metric_summary)
    return summary


def generate_stage_2b_from_stage2(
    stage_2_dir: str | Path,
    output_dir: str | Path,
    report_path: str | Path,
    parcellation_id: str = "harvard_oxford_8",
    seed: int = 0,
    n_bootstrap: int = 500,
) -> dict[str, Any]:
    stage_2_path = Path(stage_2_dir)
    summaries_path = stage_2_path / "empirical_run_summaries.json"
    if not summaries_path.exists():
        raise FileNotFoundError(f"Missing Stage 2 empirical summaries: {summaries_path}")
    records = json.loads(summaries_path.read_text(encoding="utf-8"))
    spec = get_parcellation_spec(parcellation_id)

    literature_records: list[dict[str, Any]] = []
    for record in records:
        time_series_path = resolve_under(stage_2_path, str(record["time_series_path"]))
        if not time_series_path.exists():
            raise FileNotFoundError(f"Missing cached time series: {time_series_path}")
        time_series = np.load(time_series_path)
        metrics = compute_literature_metrics(time_series, spec.node_metadata)
        literature_records.append(
            {
                "subject": str(record["subject"]),
                "session": str(record["session"]),
                "run": str(record["run"]),
                "metrics": _finite_metric_map(metrics),
                "source_time_series_path": str(time_series_path),
            }
        )

    return generate_stage_2b_outputs(
        literature_records,
        output_dir=output_dir,
        report_path=report_path,
        seed=seed,
        n_bootstrap=n_bootstrap,
        source=f"cached_stage_2_{parcellation_id}",
    )
