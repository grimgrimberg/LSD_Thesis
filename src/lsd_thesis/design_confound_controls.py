from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "design_confound_control.v1"
MIN_PAIRED_RUN_SUBJECTS = 4
RUN_CONTROL_SET = ("run-01", "run-03")


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


def _bh_q_values(p_values: list[float]) -> list[float]:
    if not p_values:
        return []
    valid = [(index, value) for index, value in enumerate(p_values) if math.isfinite(value)]
    q_values = [float("nan")] * len(p_values)
    running = 1.0
    total = float(len(valid))
    for rank_from_end, (index, p_value) in enumerate(reversed(sorted(valid, key=lambda item: item[1])), start=1):
        rank = len(valid) - rank_from_end + 1
        running = min(running, p_value * total / rank)
        q_values[index] = float(min(max(running, 0.0), 1.0))
    return q_values


def _condition_window_counts(detail: dict[str, Any]) -> dict[str, int]:
    conditions = detail.get("conditions", {})
    if not isinstance(conditions, dict):
        return {}
    counts: dict[str, int] = {}
    for condition, payload in conditions.items():
        if not isinstance(payload, dict):
            continue
        window_count = _as_float(payload.get("window_count"))
        if window_count is None:
            series = payload.get("module_time_series")
            if isinstance(series, list):
                window_count = float(len(series))
        if window_count is not None:
            counts[str(condition)] = int(window_count)
    return counts


def _global_signal_summary(detail: dict[str, Any]) -> dict[str, float]:
    conditions = detail.get("conditions", {})
    if not isinstance(conditions, dict):
        return {}
    means: dict[str, float] = {}
    for condition, payload in conditions.items():
        if not isinstance(payload, dict):
            continue
        values = payload.get("global_signal")
        if not isinstance(values, list) or not values:
            continue
        array = np.asarray([_as_float(item) for item in values], dtype=float)
        array = array[np.isfinite(array)]
        if array.size:
            means[str(condition)] = float(np.mean(array))
    output: dict[str, float] = {f"{condition}_global_signal_mean": value for condition, value in means.items()}
    if "ses-LSD" in means and "ses-PLCB" in means:
        output["global_signal_delta_lsd_minus_placebo"] = means["ses-LSD"] - means["ses-PLCB"]
    return output


def _load_subject_run_rows(viewer_root: Path) -> list[dict[str, Any]]:
    subject_views = viewer_root / "subject_views"
    if not subject_views.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(subject_views.glob("*.json")):
        detail = _read_json(path)
        if not detail:
            continue
        subject = str(detail.get("subject") or path.stem.rsplit("_", 1)[0])
        run = str(detail.get("run") or path.stem.rsplit("_", 1)[-1])
        delta_metrics = detail.get("delta_metrics", {})
        if not isinstance(delta_metrics, dict):
            continue
        row: dict[str, Any] = {
            "subject": subject,
            "run": run,
            "source_path": path.as_posix(),
            "condition_window_counts": _condition_window_counts(detail),
            **_global_signal_summary(detail),
        }
        for metric, value in delta_metrics.items():
            number = _as_float(value)
            if number is not None:
                row[str(metric)] = number
        if len(row) > 4:
            rows.append(row)
    return rows


def _metric_keys(rows: list[dict[str, Any]]) -> list[str]:
    excluded = {
        "subject",
        "run",
        "source_path",
        "condition_window_counts",
        "ses-LSD_global_signal_mean",
        "ses-PLCB_global_signal_mean",
        "global_signal_delta_lsd_minus_placebo",
    }
    keys = sorted({key for row in rows for key in row if key not in excluded})
    return [key for key in keys if any(_as_float(row.get(key)) is not None for row in rows)]


def _run_summary_rows(rows: list[dict[str, Any]], metric_keys: list[str]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for metric in metric_keys:
        all_values = np.asarray([_as_float(row.get(metric)) for row in rows], dtype=float)
        all_values = all_values[np.isfinite(all_values)]
        if all_values.size == 0:
            continue
        overall_mean = float(np.mean(all_values))
        for run in sorted({str(row["run"]) for row in rows}):
            values = np.asarray([_as_float(row.get(metric)) for row in rows if row["run"] == run], dtype=float)
            values = values[np.isfinite(values)]
            if values.size == 0:
                continue
            run_mean = float(np.mean(values))
            output.append(
                {
                    "dynamic_metric": metric,
                    "run": run,
                    "n": int(values.size),
                    "mean_delta": run_mean,
                    "std_delta": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
                    "overall_mean_delta": overall_mean,
                    "direction_matches_overall": bool(
                        np.sign(run_mean) == np.sign(overall_mean) or np.isclose(run_mean, 0.0) or np.isclose(overall_mean, 0.0)
                    ),
                }
            )
    return output


def _paired_run_tests(rows: list[dict[str, Any]], metric_keys: list[str]) -> list[dict[str, Any]]:
    by_subject_run = {(str(row["subject"]), str(row["run"])): row for row in rows}
    subjects = sorted({str(row["subject"]) for row in rows})
    output: list[dict[str, Any]] = []
    for metric in metric_keys:
        pairs: list[tuple[str, float, float]] = []
        for subject in subjects:
            first = by_subject_run.get((subject, RUN_CONTROL_SET[0]))
            second = by_subject_run.get((subject, RUN_CONTROL_SET[1]))
            if first is None or second is None:
                continue
            first_value = _as_float(first.get(metric))
            second_value = _as_float(second.get(metric))
            if first_value is not None and second_value is not None:
                pairs.append((subject, first_value, second_value))
        if len(pairs) < MIN_PAIRED_RUN_SUBJECTS:
            continue
        first_values = np.asarray([pair[1] for pair in pairs], dtype=float)
        second_values = np.asarray([pair[2] for pair in pairs], dtype=float)
        diff = second_values - first_values
        if np.isclose(np.std(diff), 0.0):
            p_value = 1.0
            statistic = 0.0
        else:
            test = stats.ttest_1samp(diff, 0.0)
            statistic = float(test.statistic)
            p_value = float(test.pvalue)
        pooled = float(np.std(np.concatenate([first_values, second_values]), ddof=1))
        standardized = float(np.mean(diff) / pooled) if pooled > 1e-12 else 0.0
        output.append(
            {
                "dynamic_metric": metric,
                "contrast": f"{RUN_CONTROL_SET[1]}_minus_{RUN_CONTROL_SET[0]}",
                "n_subjects": len(pairs),
                "run_01_mean": float(np.mean(first_values)),
                "run_03_mean": float(np.mean(second_values)),
                "mean_difference": float(np.mean(diff)),
                "standardized_difference": standardized,
                "t_statistic": statistic,
                "p": p_value,
            }
        )
    q_values = _bh_q_values([float(row["p"]) for row in output])
    for row, q_value in zip(output, q_values, strict=True):
        row["q"] = q_value
        row["run_design_sensitivity_flag"] = bool(math.isfinite(q_value) and q_value <= 0.05 and abs(float(row["standardized_difference"])) >= 0.5)
    return output


def _window_count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    for row in rows:
        counts = row.get("condition_window_counts", {})
        if not isinstance(counts, dict) or not counts:
            continue
        values = [int(value) for value in counts.values()]
        pairs.append(
            {
                "subject": row["subject"],
                "run": row["run"],
                "condition_window_counts": counts,
                "min_window_count": min(values),
                "max_window_count": max(values),
                "balanced_within_record": min(values) == max(values),
            }
        )
    return {
        "record_count": len(pairs),
        "unbalanced_record_count": sum(1 for row in pairs if not row["balanced_within_record"]),
        "rows": pairs[:20],
    }


def _global_signal_tests(rows: list[dict[str, Any]], metric_keys: list[str]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    feature = "global_signal_delta_lsd_minus_placebo"
    if not any(_as_float(row.get(feature)) is not None for row in rows):
        return output
    for metric in metric_keys:
        pairs = [
            (_as_float(row.get(feature)), _as_float(row.get(metric)))
            for row in rows
            if _as_float(row.get(feature)) is not None and _as_float(row.get(metric)) is not None
        ]
        clean = [(float(x), float(y)) for x, y in pairs if x is not None and y is not None]
        if len(clean) < MIN_PAIRED_RUN_SUBJECTS:
            continue
        x = np.asarray([pair[0] for pair in clean], dtype=float)
        y = np.asarray([pair[1] for pair in clean], dtype=float)
        if np.isclose(np.std(x), 0.0) or np.isclose(np.std(y), 0.0):
            continue
        pearson = stats.pearsonr(x, y)
        output.append(
            {
                "signal_feature": feature,
                "dynamic_metric": metric,
                "n": len(clean),
                "pearson_r": float(pearson.statistic),
                "p": float(pearson.pvalue),
            }
        )
    q_values = _bh_q_values([float(row["p"]) for row in output])
    for row, q_value in zip(output, q_values, strict=True):
        row["q"] = q_value
        row["signal_sensitivity_flag"] = bool(math.isfinite(q_value) and q_value <= 0.05 and abs(float(row["pearson_r"])) >= 0.5)
    return output


def _blocked(repo_root: Path, status: str, blocker: str, viewer_root: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": status,
        "design_confound_control_ready": False,
        "source_paths": {"subject_dynamic_views": _rel(viewer_root / "subject_views", repo_root)},
        "blocker": blocker,
        "claim_status": "not_proven_design_confound_control_missing",
        "subject_run_count": 0,
        "subject_count": 0,
        "run_count": 0,
        "run_summary_rows": [],
        "paired_run_tests": [],
        "global_signal_tests": [],
        "window_count_summary": {"record_count": 0, "unbalanced_record_count": 0, "rows": []},
        "claim_guardrail": "Design-confound controls are unavailable until subject/run empirical views exist.",
    }


def build_design_confound_control_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    rows = _load_subject_run_rows(viewer_root)
    if not rows:
        return _blocked(
            repo_root,
            "blocked_missing_primary_empirical_viewer_subject_views",
            "No primary ds003059 subject/run empirical views were found.",
            viewer_root,
        )
    metric_keys = _metric_keys(rows)
    if not metric_keys:
        return _blocked(
            repo_root,
            "blocked_missing_dynamic_delta_metrics",
            "Subject/run empirical views exist but do not contain numeric delta_metrics.",
            viewer_root,
        )
    run_summary = _run_summary_rows(rows, metric_keys)
    paired_tests = _paired_run_tests(rows, metric_keys)
    signal_tests = _global_signal_tests(rows, metric_keys)
    high_risk_count = sum(1 for row in paired_tests if row["run_design_sensitivity_flag"]) + sum(
        1 for row in signal_tests if row["signal_sensitivity_flag"]
    )
    available_runs = sorted({str(row["run"]) for row in rows})
    run_pair_ready = any(row["contrast"] == f"{RUN_CONTROL_SET[1]}_minus_{RUN_CONTROL_SET[0]}" for row in paired_tests)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": "implemented_design_confound_control_result" if run_pair_ready else "implemented_partial_design_confound_control_result",
        "design_confound_control_ready": True,
        "source_paths": {"subject_dynamic_views": _rel(viewer_root / "subject_views", repo_root)},
        "subject_run_count": len(rows),
        "subject_count": len({str(row["subject"]) for row in rows}),
        "run_count": len(available_runs),
        "available_runs": available_runs,
        "primary_run_contrast": list(RUN_CONTROL_SET),
        "metric_count": len(metric_keys),
        "run_summary_rows": run_summary,
        "paired_run_tests": paired_tests,
        "global_signal_tests": signal_tests,
        "window_count_summary": _window_count_summary(rows),
        "high_risk_design_confound_count": high_risk_count,
        "claim_status": "design_sensitive_downgrade_required" if high_risk_count else "no_fdr_design_confound_signal_detected",
        "limitations": [
            "This controls run/session design and global-signal proxy features available in the empirical viewer.",
            "This is not an FD/DVARS/censoring motion-control result.",
            "Run-02/music remains excluded from primary claims unless motion/context checks pass.",
        ],
        "claim_guardrail": (
            "This artifact strengthens run/session/signal-quality confound handling from existing empirical records. "
            "It does not complete the separate motion gate, which still requires structured FD, DVARS, and censoring confounds."
        ),
    }


def write_design_confound_control_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "confound_controls"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_design_confound_control_status(repo_root)
    status_path = output_dir / "design_confound_control_status.json"
    report_path = output_dir / "design_confound_control_status.md"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    return status


def _markdown(status: dict[str, Any]) -> str:
    lines = [
        "# Design Confound Control Status",
        "",
        status["claim_guardrail"],
        "",
        f"- Status: `{status['analysis_status']}`",
        f"- Claim status: `{status['claim_status']}`",
        f"- Subject/run rows: `{status['subject_run_count']}`",
        f"- High-risk design-confound flags: `{status.get('high_risk_design_confound_count', 0)}`",
        "",
    ]
    if status.get("paired_run_tests"):
        lines.extend(["## Paired run tests", "", "| Metric | n | difference | q | Flag |", "| --- | ---: | ---: | ---: | --- |"])
        ranked = sorted(status["paired_run_tests"], key=lambda row: abs(float(row["standardized_difference"])), reverse=True)
        for row in ranked[:12]:
            lines.append(
                "| {metric} | {n} | {diff:.3f} | {q:.3f} | {flag} |".format(
                    metric=row["dynamic_metric"],
                    n=row["n_subjects"],
                    diff=float(row["mean_difference"]),
                    q=float(row["q"]),
                    flag="yes" if row["run_design_sensitivity_flag"] else "no",
                )
            )
    else:
        lines.extend(["## Blocker", "", str(status.get("blocker") or "No paired run-control tests were available."), ""])
    return "\n".join(lines) + "\n"
