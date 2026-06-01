from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from lsd_thesis.setting_seed.motion import build_motion_summary

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "motion_confound_control.v1"
MIN_OVERLAP = 4
CONFOUND_CONTROL_INPUT_CONTRACT = {
    "motion_summary_path": "results/setting_seed/motion/motion_summary.json",
    "dynamic_subject_views": "results/stage_2/empirical_viewer/subject_views/*.json",
    "minimum_overlap": MIN_OVERLAP,
    "required_motion_features": [
        "FD mean/max/spike fraction",
        "DVARS mean/max",
        "motion outlier, scrub, or censor fraction where available",
    ],
    "required_pairing": "subject + run, with LSD and placebo/PLCB sessions paired before association testing",
}

MOTION_FEATURE_ALIASES: dict[str, tuple[str, ...]] = {
    "fd_mean": ("fd_mean", "mean_fd", "framewise_displacement_mean", "mean_framewise_displacement"),
    "fd_max": ("fd_max", "max_fd", "framewise_displacement_max", "max_framewise_displacement"),
    "fd_spike_fraction": ("fd_spike_fraction", "fd_spike_rate", "framewise_displacement_spike_fraction"),
    "dvars_mean": ("dvars_mean", "std_dvars_mean", "mean_dvars", "mean_std_dvars"),
    "dvars_max": ("dvars_max", "std_dvars_max", "max_dvars", "max_std_dvars"),
    "motion_outlier_fraction": ("motion_outlier_fraction", "outlier_fraction", "scrub_fraction", "censor_fraction"),
}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(raw).__name__}.")
    return raw


def _source_availability_payload(repo_root: Path) -> dict[str, Any] | None:
    path = repo_root / "results" / "confound_controls" / "ds003059_motion_source_availability.json"
    payload = _read_json(path)
    if not payload:
        return None
    return {
        "path": _rel(path, repo_root),
        "analysis_status": payload.get("analysis_status"),
        "source_confounds_available": payload.get("source_confounds_available"),
        "local_motion_file_count": (payload.get("local_search") or {}).get("motion_file_count"),
        "openneuro_confound_like_file_count": (payload.get("openneuro_raw_snapshot") or {}).get("confound_like_file_count"),
        "public_derivative_available_count": (payload.get("public_derivative_repositories") or {}).get("available_count"),
        "conclusion": payload.get("conclusion"),
        "next_action": payload.get("next_action"),
    }


def _rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _condition_key(row: dict[str, Any]) -> str:
    raw = str(row.get("condition") or row.get("session") or row.get("ses") or row.get("task") or "").lower()
    if "lsd" in raw:
        return "lsd"
    if "plcb" in raw or "placebo" in raw:
        return "placebo"
    return "unknown"


def _feature_value(row: dict[str, Any], feature: str) -> float | None:
    for key in MOTION_FEATURE_ALIASES[feature]:
        value = _as_float(row.get(key))
        if value is not None:
            return value
    return None


def _load_motion_features(motion_payload: dict[str, Any]) -> list[dict[str, Any]]:
    summaries = motion_payload.get("summaries", [])
    if not isinstance(summaries, list):
        return []
    grouped: dict[tuple[str, str], dict[str, dict[str, float]]] = defaultdict(dict)
    for item in summaries:
        if not isinstance(item, dict):
            continue
        subject = str(item.get("subject") or item.get("participant_id") or "").strip()
        run = str(item.get("run") or "").strip()
        if not subject or not run:
            continue
        condition = _condition_key(item)
        feature_values = {
            feature: value
            for feature in MOTION_FEATURE_ALIASES
            if (value := _feature_value(item, feature)) is not None
        }
        if feature_values:
            grouped[(subject, run)][condition] = feature_values

    rows: list[dict[str, Any]] = []
    for (subject, run), by_condition in sorted(grouped.items()):
        lsd = by_condition.get("lsd", {})
        placebo = by_condition.get("placebo", {})
        unknown = by_condition.get("unknown", {})
        row: dict[str, Any] = {"subject": subject, "run": run}
        for feature in MOTION_FEATURE_ALIASES:
            if feature in lsd and feature in placebo:
                row[f"{feature}_delta_lsd_minus_placebo"] = lsd[feature] - placebo[feature]
                row[f"{feature}_mean_abs"] = (abs(lsd[feature]) + abs(placebo[feature])) / 2.0
            elif feature in unknown:
                row[f"{feature}_observed"] = unknown[feature]
        if len(row) > 2:
            rows.append(row)
    return rows


def _load_subject_dynamic_deltas(view_root: Path) -> list[dict[str, Any]]:
    if not view_root.exists() or not view_root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(view_root.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        subject = str(payload.get("subject") or "").strip()
        run = str(payload.get("run") or "").strip()
        delta_metrics = payload.get("delta_metrics", {})
        if not subject or not run or not isinstance(delta_metrics, dict):
            continue
        row: dict[str, Any] = {"subject": subject, "run": run}
        for metric, value in delta_metrics.items():
            number = _as_float(value)
            if number is not None:
                row[str(metric)] = number
        if len(row) > 2:
            rows.append(row)
    return rows


def _merge_rows(dynamic_rows: list[dict[str, Any]], motion_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    motion_by_key = {(row["subject"], row["run"]): row for row in motion_rows}
    merged: list[dict[str, Any]] = []
    for dynamic in dynamic_rows:
        key = (dynamic["subject"], dynamic["run"])
        motion = motion_by_key.get(key)
        if motion is None:
            continue
        merged.append({**dynamic, **{key: value for key, value in motion.items() if key not in {"subject", "run"}}})
    return merged


def _bh_q_values(p_values: list[float]) -> list[float]:
    if not p_values:
        return []
    order = np.argsort(np.asarray(p_values, dtype=float))
    q_values = np.empty(len(p_values), dtype=float)
    running = 1.0
    total = float(len(p_values))
    for rank_from_end, index in enumerate(reversed(order), start=1):
        rank = len(p_values) - rank_from_end + 1
        running = min(running, p_values[int(index)] * total / rank)
        q_values[int(index)] = running
    return [float(min(max(value, 0.0), 1.0)) for value in q_values]


def _association_rows(merged: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not merged:
        return []
    motion_features = sorted(key for key in merged[0] if key not in {"subject", "run"} and key.endswith(("_delta_lsd_minus_placebo", "_mean_abs", "_observed")))
    dynamic_metrics = sorted(key for key in merged[0] if key not in {"subject", "run"} and key not in motion_features)
    rows: list[dict[str, Any]] = []
    for motion_feature in motion_features:
        for metric in dynamic_metrics:
            pairs = [
                (float(row[motion_feature]), float(row[metric]))
                for row in merged
                if _as_float(row.get(motion_feature)) is not None and _as_float(row.get(metric)) is not None
            ]
            if len(pairs) < MIN_OVERLAP:
                continue
            x = np.asarray([pair[0] for pair in pairs], dtype=float)
            y = np.asarray([pair[1] for pair in pairs], dtype=float)
            if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
                continue
            pearson = stats.pearsonr(x, y)
            spearman = stats.spearmanr(x, y)
            rows.append(
                {
                    "motion_feature": motion_feature,
                    "dynamic_metric": metric,
                    "n": len(pairs),
                    "pearson_r": float(pearson.statistic),
                    "pearson_p": float(pearson.pvalue),
                    "spearman_rho": float(spearman.statistic),
                    "spearman_p": float(spearman.pvalue),
                }
            )
    q_values = _bh_q_values([float(row["pearson_p"]) for row in rows])
    for row, q_value in zip(rows, q_values, strict=True):
        row["pearson_q"] = q_value
        row["motion_sensitivity_flag"] = bool(q_value <= 0.05 and abs(float(row["pearson_r"])) >= 0.5)
    return rows


def _blocked_status(
    repo_root: Path,
    status: str,
    blocker: str,
    motion_path: Path,
    view_root: Path,
    motion_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = motion_payload or {}
    source_availability = _source_availability_payload(repo_root)
    if source_availability and source_availability.get("source_confounds_available") is False:
        status = "blocked_absent_authorized_subject_level_motion_confounds"
        blocker = str(source_availability.get("conclusion") or blocker)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": status,
        "motion_confound_control_ready": False,
        "source_paths": {
            "motion_summary": _rel(motion_path, repo_root),
            "subject_dynamic_views": _rel(view_root, repo_root),
        },
        "motion_summary_status": payload.get("status", "missing"),
        "motion_files_present": bool(payload.get("motion_files_present")),
        "parsed_summary_count": int(payload.get("parsed_summary_count") or 0),
        "motion_summary_files": payload.get("motion_summary_files", []),
        "input_contract": {
            **CONFOUND_CONTROL_INPUT_CONTRACT,
            "motion_input_contract": payload.get("input_contract"),
        },
        "next_action": payload.get(
            "next_action",
            "Generate a motion summary from authorized fMRIPrep confounds, then rerun scripts/build_motion_confound_controls.py.",
        ),
        "blocker": blocker,
        "source_availability": source_availability,
        "merged_subject_run_count": 0,
        "association_rows": [],
        "high_risk_motion_association_count": 0,
        "claim_status": "not_proven_motion_confound_control_missing",
        "claim_guardrail": (
            "Motion/confound handling remains a limitation until this artifact contains implemented FD/DVARS/censoring sensitivity results. "
            "If source availability is false, the correct academic action is to downgrade motion-sensitive claims rather than infer safety from proxies."
        ),
    }


def build_motion_confound_control_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    motion_path = repo_root / "results" / "setting_seed" / "motion" / "motion_summary.json"
    view_root = repo_root / "results" / "stage_2" / "empirical_viewer" / "subject_views"
    motion_payload = _read_json(motion_path) or {}
    if not motion_payload.get("motion_analysis_ready"):
        discovered_payload = build_motion_summary(repo_root=repo_root)
        if discovered_payload.get("motion_analysis_ready"):
            motion_payload = discovered_payload
        elif not motion_payload.get("motion_files_present") and discovered_payload:
            motion_payload = discovered_payload

    if not motion_payload.get("motion_analysis_ready"):
        return _blocked_status(
            repo_root,
            str(motion_payload.get("status") or "blocked_missing_motion_summaries"),
            "No parsed subject/session/run motion summaries are available.",
            motion_path,
            view_root,
            motion_payload,
        )

    motion_rows = _load_motion_features(motion_payload)
    if not motion_rows:
        return _blocked_status(
            repo_root,
            "blocked_missing_usable_motion_features",
            "Motion summary is marked ready but no FD/DVARS/outlier features could be joined by subject/run.",
            motion_path,
            view_root,
            motion_payload,
        )
    dynamic_rows = _load_subject_dynamic_deltas(view_root)
    if not dynamic_rows:
        return _blocked_status(
            repo_root,
            "blocked_missing_subject_dynamic_deltas",
            "Subject/run empirical dynamic delta views are missing.",
            motion_path,
            view_root,
            motion_payload,
        )
    merged = _merge_rows(dynamic_rows, motion_rows)
    if len(merged) < MIN_OVERLAP:
        return _blocked_status(
            repo_root,
            "blocked_insufficient_subject_run_overlap",
            f"Only {len(merged)} subject/run rows overlap between motion and dynamic evidence; need at least {MIN_OVERLAP}.",
            motion_path,
            view_root,
            motion_payload,
        )

    rows = _association_rows(merged)
    if not rows:
        return _blocked_status(
            repo_root,
            "blocked_insufficient_variance_for_motion_tests",
            "Joined rows do not contain enough nonconstant motion and dynamic features for correlation tests.",
            motion_path,
            view_root,
            motion_payload,
        )
    high_risk_count = sum(1 for row in rows if row["motion_sensitivity_flag"])
    motion_suffixes = ("_delta_lsd_minus_placebo", "_mean_abs", "_observed")
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": "implemented_dedicated_motion_confound_control_result",
        "motion_confound_control_ready": True,
        "source_paths": {
            "motion_summary": _rel(motion_path, repo_root),
            "subject_dynamic_views": _rel(view_root, repo_root),
        },
        "motion_summary_status": motion_payload.get("status", "available_parsed"),
        "motion_files_present": bool(motion_payload.get("motion_files_present")),
        "parsed_summary_count": int(
            motion_payload.get("parsed_summary_count") or len(motion_payload.get("summaries", []))
        ),
        "input_contract": {
            **CONFOUND_CONTROL_INPUT_CONTRACT,
            "motion_input_contract": motion_payload.get("input_contract"),
        },
        "merged_subject_run_count": len(merged),
        "motion_feature_count": len([key for key in merged[0] if key.endswith(motion_suffixes)]),
        "dynamic_metric_count": len(
            [
                key
                for key in merged[0]
                if key not in {"subject", "run"} and not key.endswith(motion_suffixes)
            ]
        ),
        "association_rows": rows,
        "high_risk_motion_association_count": high_risk_count,
        "claim_status": "motion_sensitive_downgrade_required" if high_risk_count else "no_fdr_motion_association_detected",
        "claim_guardrail": (
            "This tests subject/run motion-feature associations with empirical dynamic deltas. It is a confound-control layer, "
            "not proof that all preprocessing, order, music, or signal-quality confounds are eliminated."
        ),
    }


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "motion_feature",
        "dynamic_metric",
        "n",
        "pearson_r",
        "pearson_p",
        "pearson_q",
        "spearman_rho",
        "spearman_p",
        "motion_sensitivity_flag",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _markdown(status: dict[str, Any]) -> str:
    lines = [
        "# Motion/Confound Control Status",
        "",
        status["claim_guardrail"],
        "",
        f"- Status: `{status['analysis_status']}`",
        f"- Claim status: `{status['claim_status']}`",
        f"- Merged subject/run rows: `{status['merged_subject_run_count']}`",
        f"- High-risk FDR motion associations: `{status['high_risk_motion_association_count']}`",
        "",
    ]
    if status["association_rows"]:
        lines.extend(
            [
                "## Strongest associations",
                "",
                "| Motion feature | Dynamic metric | n | r | q | Flag |",
                "| --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        ranked = sorted(status["association_rows"], key=lambda row: abs(float(row["pearson_r"])), reverse=True)
        for row in ranked[:12]:
            lines.append(
                "| {motion_feature} | {dynamic_metric} | {n} | {pearson_r:.3f} | {pearson_q:.3f} | {flag} |".format(
                    motion_feature=row["motion_feature"],
                    dynamic_metric=row["dynamic_metric"],
                    n=row["n"],
                    pearson_r=float(row["pearson_r"]),
                    pearson_q=float(row["pearson_q"]),
                    flag="yes" if row["motion_sensitivity_flag"] else "no",
                )
            )
    else:
        contract = status.get("input_contract", {}) if isinstance(status.get("input_contract"), dict) else {}
        lines.extend(
            [
                "## Blocker",
                "",
                str(status.get("blocker") or "No implemented confound-control result is available."),
                "",
                "## Required local input contract",
                "",
                f"- Motion summary: `{contract.get('motion_summary_path', 'results/setting_seed/motion/motion_summary.json')}`",
                f"- Dynamic subject views: `{contract.get('dynamic_subject_views', 'results/stage_2/empirical_viewer/subject_views/*.json')}`",
                f"- Minimum overlap: `{contract.get('minimum_overlap', MIN_OVERLAP)}` subject/run rows",
                f"- Next action: {status.get('next_action', 'Generate motion summaries, then rerun this control layer.')}",
            ]
        )
    return "\n".join(lines) + "\n"


def write_motion_confound_control_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "confound_controls"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_motion_confound_control_status(repo_root)
    status_path = output_dir / "motion_confound_control_status.json"
    report_path = output_dir / "motion_confound_control_status.md"
    csv_path = output_dir / "motion_dynamic_associations.csv"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    _write_csv(status["association_rows"], csv_path)
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    status["association_csv_path"] = _rel(csv_path, repo_root)
    return status
