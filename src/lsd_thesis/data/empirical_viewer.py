from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import nibabel as nib
import numpy as np
import plotly.graph_objects as go

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.metrics import compute_observable_summary
from lsd_thesis.utils import mean_metric_dict, save_figure


def _save_figure(figure: go.Figure, path: Path) -> None:
    save_figure(figure, path)


def _mean_metric_dict(metric_rows: list[dict[str, float]]) -> dict[str, float]:
    return mean_metric_dict(metric_rows)


def _std_metric_dict(metric_rows: list[dict[str, float]]) -> dict[str, float]:
    metric_names = metric_rows[0].keys()
    return {
        name: float(np.std([row[name] for row in metric_rows], ddof=1))
        for name in metric_names
    }


def _resample_vector(values: np.ndarray, point_count: int) -> np.ndarray:
    if len(values) == point_count:
        return values.astype(float, copy=True)
    positions = np.linspace(0, len(values) - 1, point_count)
    return np.asarray(np.interp(positions, np.arange(len(values)), values), dtype=float)


def _resample_matrix(values: np.ndarray, point_count: int) -> np.ndarray:
    columns = [_resample_vector(values[:, index], point_count) for index in range(values.shape[1])]
    return np.stack(columns, axis=1)


def _window_bounds(length: int, window_count: int) -> list[tuple[int, int]]:
    boundaries = np.linspace(0, length, window_count + 1, dtype=int)
    windows: list[tuple[int, int]] = []
    for start, end in zip(boundaries[:-1], boundaries[1:], strict=False):
        if end <= start:
            end = min(length, start + 1)
        windows.append((int(start), int(end)))
    return windows


def _normalize_plane(plane: np.ndarray) -> np.ndarray:
    minimum = float(np.min(plane))
    maximum = float(np.max(plane))
    if maximum - minimum < 1e-8:
        return np.zeros_like(plane, dtype=float)
    return (plane - minimum) / (maximum - minimum)


def _downsample_plane(plane: np.ndarray, preview_size: int) -> list[list[float]]:
    rows = np.linspace(0, plane.shape[0] - 1, min(preview_size, plane.shape[0]), dtype=int)
    cols = np.linspace(0, plane.shape[1] - 1, min(preview_size, plane.shape[1]), dtype=int)
    reduced = plane[np.ix_(rows, cols)]
    normalized = _normalize_plane(reduced)
    return [[float(value) for value in row] for row in normalized.astype(float)]


def _matrix_to_lists(matrix: np.ndarray) -> list[list[float]]:
    return [[float(value) for value in row] for row in matrix]


def _preview_from_volume(volume: np.ndarray, preview_size: int) -> dict[str, list[list[float]]]:
    x_mid = volume.shape[0] // 2
    y_mid = volume.shape[1] // 2
    z_mid = volume.shape[2] // 2
    return {
        "axial": _downsample_plane(np.asarray(volume[:, :, z_mid], dtype=float), preview_size),
        "coronal": _downsample_plane(np.asarray(volume[:, y_mid, :], dtype=float), preview_size),
        "sagittal": _downsample_plane(np.asarray(volume[x_mid, :, :], dtype=float), preview_size),
    }


def _observable_payload(time_series: np.ndarray, modules: tuple[str, ...]) -> tuple[dict[str, float], list[list[float]]]:
    observable = compute_observable_summary(time_series, modules)
    fc_matrix = np.nan_to_num(observable.fc_matrix, nan=0.0).astype(float)
    return observable.metric_map(), _matrix_to_lists(fc_matrix)


def build_run_empirical_view(
    subject: str,
    session: str,
    run: str,
    relative_path: str,
    time_series: np.ndarray,
    bold_image: nib.Nifti1Image,
    modules: tuple[str, ...] = MODULE_NAMES,
    window_count: int = 6,
    preview_size: int = 24,
) -> dict[str, Any]:
    volume = np.asarray(bold_image.dataobj, dtype=float)
    if volume.ndim != 4:
        raise ValueError("BOLD image must be 4D.")
    if time_series.shape[0] != volume.shape[3]:
        raise ValueError("Time series length must match the image time dimension.")

    metrics, fc_matrix = _observable_payload(time_series, modules)
    mean_volume = np.mean(volume, axis=3)
    global_signal = np.mean(volume, axis=(0, 1, 2))

    windows: list[dict[str, Any]] = []
    for index, (start, end) in enumerate(_window_bounds(time_series.shape[0], window_count)):
        window_series = time_series[start:end]
        window_metrics, window_fc = _observable_payload(window_series, modules)
        window_preview = _preview_from_volume(np.mean(volume[:, :, :, start:end], axis=3), preview_size)
        windows.append(
            {
                "index": index,
                "start_index": start,
                "end_index": end,
                "fc_matrix": window_fc,
                "metrics": window_metrics,
                "raw_preview": window_preview,
            }
        )

    return {
        "subject": subject,
        "session": session,
        "run": run,
        "relative_path": relative_path,
        "window_count": window_count,
        "global_signal": global_signal.astype(float).tolist(),
        "module_time_series": time_series.astype(float).tolist(),
        "metrics": metrics,
        "fc_matrix": fc_matrix,
        "mean_raw_preview": _preview_from_volume(mean_volume, preview_size),
        "windows": windows,
    }


def _average_nested_matrices(matrices: list[list[list[float]]]) -> list[list[float]]:
    averaged = np.mean(np.asarray(matrices, dtype=float), axis=0)
    return _matrix_to_lists(np.asarray(averaged, dtype=float))


def _average_nested_previews(previews: list[dict[str, list[list[float]]]]) -> dict[str, list[list[float]]]:
    return {
        plane: _matrix_to_lists(
            np.asarray(
                np.mean(np.asarray([preview[plane] for preview in previews], dtype=float), axis=0),
                dtype=float,
            )
        )
        for plane in ("axial", "coronal", "sagittal")
    }


def _aggregate_condition_views(
    condition_views: list[dict[str, Any]],
    modules: tuple[str, ...],
    trace_points: int = 120,
) -> dict[str, Any]:
    module_series = [
        _resample_matrix(np.asarray(view["module_time_series"], dtype=float), trace_points)
        for view in condition_views
    ]
    global_signals = [
        _resample_vector(np.asarray(view["global_signal"], dtype=float), trace_points)
        for view in condition_views
    ]
    module_series_array = np.asarray(module_series, dtype=float)
    global_signal_array = np.asarray(global_signals, dtype=float)
    window_count = int(condition_views[0]["window_count"])
    window_rows: list[dict[str, Any]] = []
    for index in range(window_count):
        indexed_windows = [view["windows"][index] for view in condition_views]
        window_rows.append(
            {
                "index": index,
                "fc_matrix": _average_nested_matrices(
                    [window["fc_matrix"] for window in indexed_windows]
                ),
                "metrics": _mean_metric_dict(
                    [dict(window["metrics"]) for window in indexed_windows]
                ),
                "raw_preview": _average_nested_previews(
                    [dict(window["raw_preview"]) for window in indexed_windows]
                ),
            }
        )

    return {
        "window_count": window_count,
        "metrics": _mean_metric_dict([dict(view["metrics"]) for view in condition_views]),
        "metrics_std": _std_metric_dict([dict(view["metrics"]) for view in condition_views]),
        "fc_matrix": _average_nested_matrices([view["fc_matrix"] for view in condition_views]),
        "global_signal": _resample_vector(np.mean(global_signal_array, axis=0), trace_points).tolist(),
        "global_signal_std": np.std(global_signal_array, axis=0, ddof=0).astype(float).tolist(),
        "module_time_series": np.mean(module_series_array, axis=0).astype(float).tolist(),
        "module_time_series_std": np.std(module_series_array, axis=0, ddof=0).astype(float).tolist(),
        "mean_raw_preview": _average_nested_previews(
            [dict(view["mean_raw_preview"]) for view in condition_views]
        ),
        "windows": window_rows,
        "module_names": list(modules),
        "subject_count": len(condition_views),
    }


def build_empirical_viewer_payloads(
    run_views: list[dict[str, Any]],
    modules: tuple[str, ...] = MODULE_NAMES,
    gallery: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if not run_views:
        raise ValueError("At least one run view is required.")

    subjects = sorted({str(view["subject"]) for view in run_views})
    runs = sorted({str(view["run"]) for view in run_views})

    subject_session_views: dict[tuple[str, str], dict[str, Any]] = {}
    for subject in subjects:
        for session in sorted({str(view["session"]) for view in run_views if str(view["subject"]) == subject}):
            grouped_runs = [
                view
                for view in run_views
                if str(view["subject"]) == subject and str(view["session"]) == session
            ]
            if not grouped_runs:
                continue
            subject_session_views[(subject, session)] = _aggregate_condition_views(grouped_runs, modules)

    grouped_by_session: dict[str, list[dict[str, Any]]] = {}
    for (_, session), session_view in subject_session_views.items():
        grouped_by_session.setdefault(session, []).append(session_view)

    paired_subjects = sorted(
        subject
        for subject in subjects
        if (subject, "ses-PLCB") in subject_session_views and (subject, "ses-LSD") in subject_session_views
    )
    delta_metrics_rows = [
        {
            name: float(
                subject_session_views[(subject, "ses-LSD")]["metrics"][name]
                - subject_session_views[(subject, "ses-PLCB")]["metrics"][name]
            )
            for name in subject_session_views[(subject, "ses-PLCB")]["metrics"].keys()
        }
        for subject in paired_subjects
    ]

    group_overview = {
        "subjects": subjects,
        "runs": runs,
        "default_subject": subjects[0],
        "module_names": list(modules),
        "conditions": {
            session: _aggregate_condition_views(condition_views, modules)
            for session, condition_views in grouped_by_session.items()
        },
        "paired_subject_count": len(paired_subjects),
        "delta_metrics": _mean_metric_dict(delta_metrics_rows) if delta_metrics_rows else {},
        "delta_metrics_std": _std_metric_dict(delta_metrics_rows) if delta_metrics_rows else {},
        "gallery": gallery or [],
    }

    subject_index: dict[str, list[str]] = {}
    subject_views: dict[str, dict[str, Any]] = {}
    for subject in subjects:
        paired_views = [view for view in run_views if view["subject"] == subject]
        available_runs = sorted({str(view["run"]) for view in paired_views})
        subject_index[subject] = available_runs
        subject_views[subject] = {}
        for run in available_runs:
            run_pair = {
                str(view["session"]): view
                for view in paired_views
                if str(view["run"]) == run
            }
            if "ses-PLCB" not in run_pair or "ses-LSD" not in run_pair:
                continue

            plc_metrics = dict(run_pair["ses-PLCB"]["metrics"])
            lsd_metrics = dict(run_pair["ses-LSD"]["metrics"])
            metric_names = plc_metrics.keys()
            window_count = int(run_pair["ses-PLCB"]["window_count"])
            window_deltas = []
            for index in range(window_count):
                plc_window = run_pair["ses-PLCB"]["windows"][index]
                lsd_window = run_pair["ses-LSD"]["windows"][index]
                window_deltas.append(
                    {
                        "index": index,
                        "metrics": {
                            name: float(lsd_window["metrics"][name] - plc_window["metrics"][name])
                            for name in metric_names
                        },
                        "fc_matrix": (
                            np.asarray(lsd_window["fc_matrix"], dtype=float)
                            - np.asarray(plc_window["fc_matrix"], dtype=float)
                        ).tolist(),
                    }
                )

            subject_views[subject][run] = {
                "subject": subject,
                "run": run,
                "conditions": run_pair,
                "delta_metrics": {
                    name: float(lsd_metrics[name] - plc_metrics[name]) for name in metric_names
                },
                "window_deltas": window_deltas,
            }

    return {
        "group_overview": group_overview,
        "subject_index": subject_index,
        "subject_views": subject_views,
    }


def write_empirical_viewer_cache(
    payloads: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, str]:
    root = Path(output_dir)
    subject_views_dir = root / "subject_views"
    subject_views_dir.mkdir(parents=True, exist_ok=True)

    group_overview_path = root / "group_overview.json"
    subject_index_path = root / "subject_index.json"
    group_overview_path.write_text(
        json.dumps(payloads["group_overview"], indent=2),
        encoding="utf-8",
    )
    subject_index_path.write_text(
        json.dumps(payloads["subject_index"], indent=2),
        encoding="utf-8",
    )

    for subject, runs in payloads["subject_views"].items():
        for run, detail in runs.items():
            detail_path = subject_views_dir / f"{subject}_{run}.json"
            detail_path.write_text(json.dumps(detail, indent=2), encoding="utf-8")

    return {
        "group_overview_path": str(group_overview_path),
        "subject_index_path": str(subject_index_path),
        "subject_views_dir": str(subject_views_dir),
    }


def build_empirical_run_views_from_records(
    run_records: list[Any] | tuple[Any, ...],
    dataset_dir: str | Path,
    output_dir: str | Path | None = None,
    modules: tuple[str, ...] = MODULE_NAMES,
    window_count: int = 6,
    preview_size: int = 24,
) -> list[dict[str, Any]]:
    dataset_root = Path(dataset_dir)
    output_root = Path(output_dir) if output_dir is not None else None
    run_views: list[dict[str, Any]] = []
    for record in run_records:
        run_path = dataset_root / str(record.relative_path)
        loaded_image = nib.load(str(run_path))
        if not isinstance(loaded_image, nib.Nifti1Image):
            raise TypeError(f"Expected a NIfTI image for {run_path}.")
        time_series_path = Path(str(record.time_series_path))
        if not time_series_path.is_absolute() and output_root is not None:
            time_series_path = output_root / time_series_path
        time_series = np.load(str(time_series_path))
        run_views.append(
            build_run_empirical_view(
                subject=str(record.subject),
                session=str(record.session),
                run=str(record.run),
                relative_path=str(record.relative_path),
                time_series=np.asarray(time_series, dtype=float),
                bold_image=cast(nib.Nifti1Image, loaded_image),
                modules=modules,
                window_count=window_count,
                preview_size=preview_size,
            )
        )
    return run_views


def _metric_delta_figure(delta_metrics: dict[str, float]) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Bar(
                x=list(delta_metrics.keys()),
                y=list(delta_metrics.values()),
                marker_color="#0ea5e9",
            )
        ]
    )
    figure.update_layout(
        title="Empirical LSD Minus Placebo Metric Deltas",
        template="plotly_white",
    )
    return figure


def _group_trace_figure(group_overview: dict[str, Any]) -> go.Figure:
    figure = go.Figure()
    modules = group_overview["module_names"]
    for session, condition in group_overview["conditions"].items():
        traces = np.asarray(condition["module_time_series"], dtype=float)
        for index, module in enumerate(modules):
            figure.add_trace(
                go.Scatter(
                    x=list(range(traces.shape[0])),
                    y=traces[:, index],
                    mode="lines",
                    name=f"{session}:{module}",
                    line={"width": 1.2},
                )
            )
    figure.update_layout(
        title="Empirical Group-Average Module Traces",
        template="plotly_white",
        xaxis_title="Normalized time",
        yaxis_title="Module signal",
    )
    return figure


def _fc_figure(fc_matrix: list[list[float]], title: str) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Heatmap(
                z=fc_matrix,
                x=list(MODULE_NAMES),
                y=list(MODULE_NAMES),
                colorscale="RdBu",
                zmin=-1.0,
                zmax=1.0,
            )
        ]
    )
    figure.update_layout(title=title, template="plotly_white")
    return figure


def generate_empirical_gallery(
    group_overview: dict[str, Any],
    figures_dir: str | Path,
) -> list[dict[str, str]]:
    figures_root = Path(figures_dir)
    figures_root.mkdir(parents=True, exist_ok=True)

    placebo_fc = group_overview["conditions"]["ses-PLCB"]["fc_matrix"]
    lsd_fc = group_overview["conditions"]["ses-LSD"]["fc_matrix"]
    delta_metrics = {
        name: float(
            group_overview["conditions"]["ses-LSD"]["metrics"][name]
            - group_overview["conditions"]["ses-PLCB"]["metrics"][name]
        )
        for name in group_overview["conditions"]["ses-PLCB"]["metrics"].keys()
    }
    fc_delta = (
        np.asarray(lsd_fc, dtype=float) - np.asarray(placebo_fc, dtype=float)
    ).tolist()

    gallery = [
        (
            "Empirical group traces",
            figures_root / "empirical_group_traces.html",
            _group_trace_figure(group_overview),
        ),
        (
            "Empirical placebo FC",
            figures_root / "empirical_placebo_fc.html",
            _fc_figure(placebo_fc, "Empirical Placebo FC"),
        ),
        (
            "Empirical LSD FC",
            figures_root / "empirical_lsd_fc.html",
            _fc_figure(lsd_fc, "Empirical LSD FC"),
        ),
        (
            "Empirical FC delta",
            figures_root / "empirical_fc_delta.html",
            _fc_figure(fc_delta, "Empirical FC Delta (LSD - Placebo)"),
        ),
        (
            "Empirical metric deltas",
            figures_root / "empirical_metric_deltas.html",
            _metric_delta_figure(delta_metrics),
        ),
    ]

    outputs: list[dict[str, str]] = []
    for label, path, figure in gallery:
        _save_figure(figure, path)
        outputs.append({"label": label, "path": str(path)})
    return outputs
