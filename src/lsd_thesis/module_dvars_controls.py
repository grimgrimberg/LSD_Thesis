from __future__ import annotations

import csv
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "module_dvars_control.v1"
MIN_OVERLAP = 4
ROBUST_Z_SPIKE_THRESHOLD = 2.5
HIGH_BURDEN_QUANTILE = 0.75


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(raw).__name__}.")
    return raw


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _finite_2d(values: Any) -> np.ndarray | None:
    try:
        array = np.asarray(values, dtype=float)
    except (TypeError, ValueError):
        return None
    if array.ndim != 2 or array.shape[0] < 3 or array.shape[1] < 1:
        return None
    finite = np.where(np.isfinite(array), array, np.nan)
    means = np.nanmean(finite, axis=0)
    means = np.where(np.isfinite(means), means, 0.0)
    row_idx, col_idx = np.where(~np.isfinite(array))
    if len(row_idx):
        array = array.copy()
        array[row_idx, col_idx] = means[col_idx]
    return array


def _module_dvars_series(module_time_series: Any) -> np.ndarray | None:
    array = _finite_2d(module_time_series)
    if array is None:
        return None
    diffs = np.diff(array, axis=0)
    return np.sqrt(np.mean(diffs * diffs, axis=1))


def _robust_z(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = 1.4826 * mad
    if scale <= 1e-12:
        scale = float(np.std(values))
    if scale <= 1e-12:
        return np.zeros_like(values, dtype=float)
    return (values - median) / scale


def _condition_summary(values: Any) -> dict[str, float] | None:
    series = _module_dvars_series(values)
    if series is None or series.size == 0:
        return None
    robust_z = _robust_z(series)
    return {
        "mean": float(np.mean(series)),
        "median": float(np.median(series)),
        "max": float(np.max(series)),
        "p95": float(np.percentile(series, 95)),
        "spike_fraction": float(np.mean(robust_z >= ROBUST_Z_SPIKE_THRESHOLD)),
        "volume_count": int(series.size + 1),
        "dvars_count": int(series.size),
    }


def _load_rows(viewer_root: Path) -> list[dict[str, Any]]:
    subject_views = viewer_root / "subject_views"
    if not subject_views.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(subject_views.glob("*.json")):
        detail = _read_json(path)
        if not detail:
            continue
        conditions = detail.get("conditions", {})
        delta_metrics = detail.get("delta_metrics", {})
        if not isinstance(conditions, dict) or not isinstance(delta_metrics, dict):
            continue
        lsd = conditions.get("ses-LSD")
        placebo = conditions.get("ses-PLCB")
        if not isinstance(lsd, dict) or not isinstance(placebo, dict):
            continue
        lsd_summary = _condition_summary(lsd.get("module_time_series"))
        placebo_summary = _condition_summary(placebo.get("module_time_series"))
        if lsd_summary is None or placebo_summary is None:
            continue
        row: dict[str, Any] = {
            "subject": str(detail.get("subject") or path.stem.rsplit("_", 1)[0]),
            "run": str(detail.get("run") or path.stem.rsplit("_", 1)[-1]),
            "source_path": path.as_posix(),
        }
        for metric in ("mean", "median", "max", "p95", "spike_fraction"):
            row[f"module_dvars_{metric}_lsd"] = lsd_summary[metric]
            row[f"module_dvars_{metric}_placebo"] = placebo_summary[metric]
            row[f"module_dvars_{metric}_delta_lsd_minus_placebo"] = lsd_summary[metric] - placebo_summary[metric]
            row[f"module_dvars_{metric}_mean_abs"] = (abs(lsd_summary[metric]) + abs(placebo_summary[metric])) / 2.0
        row["module_dvars_volume_count_lsd"] = lsd_summary["volume_count"]
        row["module_dvars_volume_count_placebo"] = placebo_summary["volume_count"]
        row["module_dvars_volume_count_balanced"] = lsd_summary["volume_count"] == placebo_summary["volume_count"]
        for metric, value in delta_metrics.items():
            number = _as_float(value)
            if number is not None:
                row[str(metric)] = number
        rows.append(row)
    return rows


def _bh_q_values(p_values: list[float]) -> list[float]:
    q_values = [float("nan")] * len(p_values)
    valid = [(idx, value) for idx, value in enumerate(p_values) if math.isfinite(value)]
    if not valid:
        return q_values
    running = 1.0
    total = float(len(valid))
    for rank_from_end, (idx, p_value) in enumerate(reversed(sorted(valid, key=lambda item: item[1])), start=1):
        rank = len(valid) - rank_from_end + 1
        running = min(running, p_value * total / rank)
        q_values[idx] = float(min(max(running, 0.0), 1.0))
    return q_values


def _association_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dvars_features = sorted(
        key
        for key in rows[0]
        if key.startswith("module_dvars_") and key.endswith(("_delta_lsd_minus_placebo", "_mean_abs"))
    )
    dynamic_metrics = sorted(
        key
        for key in rows[0]
        if key not in {"subject", "run", "source_path"}
        and not key.startswith("module_dvars_")
        and any(_as_float(row.get(key)) is not None for row in rows)
    )
    output: list[dict[str, Any]] = []
    for feature in dvars_features:
        for metric in dynamic_metrics:
            pairs = [
                (_as_float(row.get(feature)), _as_float(row.get(metric)))
                for row in rows
                if _as_float(row.get(feature)) is not None and _as_float(row.get(metric)) is not None
            ]
            clean = [(float(x), float(y)) for x, y in pairs if x is not None and y is not None]
            if len(clean) < MIN_OVERLAP:
                continue
            x = np.asarray([pair[0] for pair in clean], dtype=float)
            y = np.asarray([pair[1] for pair in clean], dtype=float)
            if np.isclose(np.std(x), 0.0) or np.isclose(np.std(y), 0.0):
                continue
            pearson = stats.pearsonr(x, y)
            spearman = stats.spearmanr(x, y)
            output.append(
                {
                    "module_dvars_feature": feature,
                    "dynamic_metric": metric,
                    "n": len(clean),
                    "pearson_r": float(pearson.statistic),
                    "pearson_p": float(pearson.pvalue),
                    "spearman_rho": float(spearman.statistic),
                    "spearman_p": float(spearman.pvalue),
                }
            )
    q_values = _bh_q_values([float(row["pearson_p"]) for row in output])
    for row, q_value in zip(output, q_values, strict=True):
        row["pearson_q"] = q_value
        row["module_dvars_sensitivity_flag"] = bool(math.isfinite(q_value) and q_value <= 0.05 and abs(float(row["pearson_r"])) >= 0.5)
    return output


def _exclusion_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    burden_key = "module_dvars_mean_mean_abs"
    burdens = np.asarray([_as_float(row.get(burden_key)) for row in rows], dtype=float)
    burdens = burdens[np.isfinite(burdens)]
    if burdens.size == 0:
        return []
    threshold = float(np.quantile(burdens, HIGH_BURDEN_QUANTILE))
    low_rows = [row for row in rows if (_as_float(row.get(burden_key)) or 0.0) <= threshold]
    high_rows = [row for row in rows if (_as_float(row.get(burden_key)) or 0.0) > threshold]
    dynamic_metrics = sorted(
        key
        for key in rows[0]
        if key not in {"subject", "run", "source_path"}
        and not key.startswith("module_dvars_")
        and any(_as_float(row.get(key)) is not None for row in rows)
    )
    output: list[dict[str, Any]] = []
    for metric in dynamic_metrics:
        all_values = np.asarray([_as_float(row.get(metric)) for row in rows], dtype=float)
        low_values = np.asarray([_as_float(row.get(metric)) for row in low_rows], dtype=float)
        high_values = np.asarray([_as_float(row.get(metric)) for row in high_rows], dtype=float)
        all_values = all_values[np.isfinite(all_values)]
        low_values = low_values[np.isfinite(low_values)]
        high_values = high_values[np.isfinite(high_values)]
        if all_values.size == 0 or low_values.size == 0:
            continue
        all_mean = float(np.mean(all_values))
        retained_mean = float(np.mean(low_values))
        output.append(
            {
                "dynamic_metric": metric,
                "burden_feature": burden_key,
                "high_burden_quantile": HIGH_BURDEN_QUANTILE,
                "high_burden_threshold": threshold,
                "n_all": int(all_values.size),
                "n_retained_after_high_burden_exclusion": int(low_values.size),
                "n_excluded_high_burden": int(high_values.size),
                "mean_all": all_mean,
                "mean_after_exclusion": retained_mean,
                "mean_high_burden_only": float(np.mean(high_values)) if high_values.size else None,
                "direction_preserved_after_exclusion": bool(
                    np.sign(all_mean) == np.sign(retained_mean) or np.isclose(all_mean, 0.0) or np.isclose(retained_mean, 0.0)
                ),
                "relative_change_abs": abs(retained_mean - all_mean) / max(abs(all_mean), 1e-12),
            }
        )
    return output


def _blocked(repo_root: Path, status: str, blocker: str, viewer_root: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": status,
        "module_dvars_control_ready": False,
        "source_paths": {"subject_dynamic_views": _rel(viewer_root / "subject_views", repo_root)},
        "blocker": blocker,
        "subject_run_count": 0,
        "association_rows": [],
        "high_risk_module_dvars_association_count": 0,
        "high_burden_exclusion_rows": [],
        "unstable_high_burden_exclusion_count": 0,
        "claim_status": "not_proven_module_dvars_control_missing",
        "claim_guardrail": "Module-DVARS sensitivity is unavailable until subject/run module time series exist.",
    }


def build_module_dvars_control_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    rows = _load_rows(viewer_root)
    if not rows:
        return _blocked(
            repo_root,
            "blocked_missing_subject_run_module_time_series",
            "No subject/run records with both ses-LSD and ses-PLCB module_time_series were found.",
            viewer_root,
        )
    association_rows = _association_rows(rows)
    exclusion_rows = _exclusion_rows(rows)
    high_risk_count = sum(1 for row in association_rows if row["module_dvars_sensitivity_flag"])
    unstable_exclusions = sum(
        1
        for row in exclusion_rows
        if not row["direction_preserved_after_exclusion"] or float(row["relative_change_abs"]) >= 0.5
    )
    balanced_records = sum(1 for row in rows if row.get("module_dvars_volume_count_balanced"))
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": "implemented_module_dvars_censoring_sensitivity",
        "module_dvars_control_ready": True,
        "source_paths": {"subject_dynamic_views": _rel(viewer_root / "subject_views", repo_root)},
        "subject_run_count": len(rows),
        "subject_count": len({str(row["subject"]) for row in rows}),
        "run_count": len({str(row["run"]) for row in rows}),
        "balanced_condition_volume_records": balanced_records,
        "unbalanced_condition_volume_records": len(rows) - balanced_records,
        "robust_z_spike_threshold": ROBUST_Z_SPIKE_THRESHOLD,
        "high_burden_quantile": HIGH_BURDEN_QUANTILE,
        "association_rows": association_rows,
        "high_risk_module_dvars_association_count": high_risk_count,
        "high_burden_exclusion_rows": exclusion_rows,
        "unstable_high_burden_exclusion_count": unstable_exclusions,
        "claim_status": (
            "module_dvars_sensitive_downgrade_required"
            if high_risk_count or unstable_exclusions
            else "no_module_dvars_or_censoring_sensitivity_detected"
        ),
        "limitations": [
            "Derived from module-level time series, not voxel-level fMRIPrep confounds.",
            "Does not include framewise displacement, motion parameters, or fMRIPrep censor columns.",
            "Useful as an internal signal-quality sensitivity layer while the real FD/DVARS gate remains fail-closed.",
        ],
        "claim_guardrail": (
            "This is a module-derived DVARS/censoring sensitivity layer. It strengthens confound handling but does "
            "not replace real fMRIPrep FD, DVARS, and censoring confounds."
        ),
    }


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _markdown(status: dict[str, Any]) -> str:
    lines = [
        "# Module-DVARS / Censoring Sensitivity Status",
        "",
        status["claim_guardrail"],
        "",
        f"- Status: `{status['analysis_status']}`",
        f"- Claim status: `{status['claim_status']}`",
        f"- Subject/run rows: `{status['subject_run_count']}`",
        f"- High-risk module-DVARS associations: `{status['high_risk_module_dvars_association_count']}`",
        f"- Unstable high-burden exclusions: `{status['unstable_high_burden_exclusion_count']}`",
        "",
    ]
    if status.get("association_rows"):
        lines.extend(["## Strongest module-DVARS associations", "", "| Feature | Metric | n | r | q | Flag |", "| --- | --- | ---: | ---: | ---: | --- |"])
        ranked = sorted(status["association_rows"], key=lambda row: abs(float(row["pearson_r"])), reverse=True)
        for row in ranked[:12]:
            lines.append(
                "| {feature} | {metric} | {n} | {r:.3f} | {q:.3f} | {flag} |".format(
                    feature=row["module_dvars_feature"],
                    metric=row["dynamic_metric"],
                    n=row["n"],
                    r=float(row["pearson_r"]),
                    q=float(row["pearson_q"]),
                    flag="yes" if row["module_dvars_sensitivity_flag"] else "no",
                )
            )
    else:
        lines.extend(["## Blocker", "", str(status.get("blocker") or "No module-DVARS association rows were available."), ""])
    return "\n".join(lines) + "\n"


def write_module_dvars_control_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "confound_controls"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_module_dvars_control_status(repo_root)
    status_path = output_dir / "module_dvars_control_status.json"
    report_path = output_dir / "module_dvars_control_status.md"
    association_csv = output_dir / "module_dvars_dynamic_associations.csv"
    exclusion_csv = output_dir / "module_dvars_high_burden_exclusion.csv"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    _write_csv(status["association_rows"], association_csv)
    _write_csv(status["high_burden_exclusion_rows"], exclusion_csv)
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    status["association_csv_path"] = _rel(association_csv, repo_root)
    status["exclusion_csv_path"] = _rel(exclusion_csv, repo_root)
    return status
