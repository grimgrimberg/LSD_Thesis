from __future__ import annotations

import csv
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "image_motion_qc.v1"
DEFAULT_STRIDE = 6
MIN_OVERLAP = 4
ROBUST_Z_SPIKE_THRESHOLD = 2.5
COM_SPIKE_THRESHOLD_MM = 0.5
HIGH_BURDEN_QUANTILE = 0.75

QC_FEATURES = (
    "image_dvars_mean",
    "image_dvars_max",
    "image_dvars_p95",
    "image_dvars_spike_fraction",
    "com_displacement_mean_mm",
    "com_displacement_max_mm",
    "com_displacement_p95_mm",
    "com_displacement_spike_fraction",
    "global_signal_derivative_rms",
    "global_signal_derivative_spike_fraction",
)


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


def _series_summary(values: np.ndarray, *, spike_threshold: float = ROBUST_Z_SPIKE_THRESHOLD, absolute_spike: bool = False) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {
            "mean": 0.0,
            "median": 0.0,
            "max": 0.0,
            "p95": 0.0,
            "spike_fraction": 0.0,
        }
    spike_values = values if absolute_spike else _robust_z(values)
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "max": float(np.max(values)),
        "p95": float(np.percentile(values, 95)),
        "spike_fraction": float(np.mean(spike_values >= spike_threshold)),
    }


def _candidate_bold_paths(repo_root: Path, condition: dict[str, Any], subject: str, session: str, run: str) -> list[Path]:
    candidates: list[Path] = []
    for key in ("relative_path", "source_path", "bold_path", "path"):
        raw = condition.get(key)
        if not raw:
            continue
        path = Path(str(raw))
        if path.is_absolute():
            candidates.append(path)
        else:
            candidates.append(repo_root / path)
            candidates.append(repo_root / "data" / "ds003059" / path)
    if subject and session and run:
        candidates.append(
            repo_root
            / "data"
            / "ds003059"
            / subject
            / session
            / "func"
            / f"{subject}_{session}_task-rest_{run}_bold.nii.gz"
        )
    return candidates


def _resolve_bold_path(repo_root: Path, condition: dict[str, Any], subject: str, session: str, run: str) -> Path | None:
    for path in _candidate_bold_paths(repo_root, condition, subject, session, run):
        if path.exists() and path.is_file():
            return path
    return None


def _sample_mask(data: np.ndarray) -> np.ndarray:
    mean_volume = np.mean(data, axis=3)
    finite_positive = mean_volume[np.isfinite(mean_volume) & (mean_volume > 0)]
    if finite_positive.size:
        threshold = float(np.percentile(finite_positive, 20))
        mask = np.isfinite(mean_volume) & (mean_volume > threshold)
    else:
        mask = np.isfinite(mean_volume)
    if int(mask.sum()) < 8:
        mask = np.isfinite(mean_volume) & (mean_volume != 0)
    if int(mask.sum()) < 8:
        mask = np.isfinite(mean_volume)
    return mask


def _masked_coordinates(img: nib.spatialimages.SpatialImage, mask: np.ndarray, stride: int) -> np.ndarray:
    grids = np.meshgrid(
        *(np.arange(size, dtype=float) * float(stride) for size in mask.shape),
        indexing="ij",
    )
    ijk = np.stack([grid[mask] for grid in grids], axis=1)
    coords = nib.affines.apply_affine(img.affine, ijk)
    return np.asarray(coords, dtype=float)


def summarize_bold_image(path: Path, *, repo_root: Path = REPO_ROOT, stride: int = DEFAULT_STRIDE) -> dict[str, Any]:
    if stride < 1:
        raise ValueError("stride must be >= 1")
    img = nib.load(str(path))
    if len(img.shape) != 4 or img.shape[3] < 3:
        raise ValueError(f"Expected 4D BOLD with at least 3 volumes: {path}")
    slices = (slice(None, None, stride), slice(None, None, stride), slice(None, None, stride), slice(None))
    data = np.asarray(img.dataobj[slices], dtype=np.float32)
    data = np.nan_to_num(data, copy=True)
    mask = _sample_mask(data)
    voxels = np.asarray(data[mask, :], dtype=float)
    if voxels.ndim != 2 or voxels.shape[0] < 8 or voxels.shape[1] < 3:
        raise ValueError(f"Insufficient sampled BOLD voxels/timepoints after masking: {path}")

    diffs = np.diff(voxels, axis=1)
    dvars = np.sqrt(np.mean(diffs * diffs, axis=0))
    dvars_summary = _series_summary(dvars)

    coords = _masked_coordinates(img, mask, stride)
    weights = np.maximum(voxels, 0.0)
    sums = np.sum(weights, axis=0)
    sums = np.where(sums > 1e-12, sums, 1.0)
    centers = (weights.T @ coords) / sums[:, None]
    com_displacement = np.linalg.norm(np.diff(centers, axis=0), axis=1)
    com_summary = _series_summary(com_displacement, spike_threshold=COM_SPIKE_THRESHOLD_MM, absolute_spike=True)

    global_signal = np.mean(voxels, axis=0)
    global_derivative = np.diff(global_signal)
    global_summary = _series_summary(np.abs(global_derivative))

    zooms = tuple(float(value) for value in img.header.get_zooms()[:4])
    return {
        "path": _rel(path, repo_root) if path.resolve().is_relative_to(repo_root.resolve()) else path.as_posix(),
        "shape": [int(value) for value in img.shape],
        "zooms": list(zooms),
        "sample_stride": int(stride),
        "sampled_voxel_count": int(voxels.shape[0]),
        "volume_count": int(voxels.shape[1]),
        "image_dvars_mean": dvars_summary["mean"],
        "image_dvars_median": dvars_summary["median"],
        "image_dvars_max": dvars_summary["max"],
        "image_dvars_p95": dvars_summary["p95"],
        "image_dvars_spike_fraction": dvars_summary["spike_fraction"],
        "com_displacement_mean_mm": com_summary["mean"],
        "com_displacement_median_mm": com_summary["median"],
        "com_displacement_max_mm": com_summary["max"],
        "com_displacement_p95_mm": com_summary["p95"],
        "com_displacement_spike_fraction": com_summary["spike_fraction"],
        "global_signal_derivative_rms": float(np.sqrt(np.mean(global_derivative * global_derivative))),
        "global_signal_derivative_spike_fraction": global_summary["spike_fraction"],
    }


def _load_subject_run_rows(repo_root: Path, view_root: Path, *, stride: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not view_root.exists() or not view_root.is_dir():
        return [], [{"reason": "missing_subject_view_root", "path": _rel(view_root, repo_root)}]
    rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for path in sorted(view_root.glob("*.json")):
        detail = _read_json(path)
        if not detail:
            continue
        subject = str(detail.get("subject") or path.stem.rsplit("_", 1)[0]).strip()
        run = str(detail.get("run") or path.stem.rsplit("_", 1)[-1]).strip()
        conditions = detail.get("conditions", {})
        delta_metrics = detail.get("delta_metrics", {})
        if not isinstance(conditions, dict) or not isinstance(delta_metrics, dict):
            continue
        lsd = conditions.get("ses-LSD")
        placebo = conditions.get("ses-PLCB")
        if not isinstance(lsd, dict) or not isinstance(placebo, dict):
            missing.append({"subject": subject, "run": run, "reason": "missing_lsd_or_placebo_condition", "subject_view": _rel(path, repo_root)})
            continue
        lsd_path = _resolve_bold_path(repo_root, lsd, subject, "ses-LSD", run)
        placebo_path = _resolve_bold_path(repo_root, placebo, subject, "ses-PLCB", run)
        if lsd_path is None or placebo_path is None:
            missing.append(
                {
                    "subject": subject,
                    "run": run,
                    "reason": "missing_raw_bold_file",
                    "subject_view": _rel(path, repo_root),
                    "lsd_found": lsd_path is not None,
                    "placebo_found": placebo_path is not None,
                }
            )
            continue
        try:
            lsd_summary = summarize_bold_image(lsd_path, repo_root=repo_root, stride=stride)
            placebo_summary = summarize_bold_image(placebo_path, repo_root=repo_root, stride=stride)
        except Exception as exc:
            missing.append(
                {
                    "subject": subject,
                    "run": run,
                    "reason": "bold_qc_summary_failed",
                    "subject_view": _rel(path, repo_root),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        row: dict[str, Any] = {
            "subject": subject,
            "run": run,
            "subject_view_path": _rel(path, repo_root),
            "lsd_bold_path": lsd_summary["path"],
            "placebo_bold_path": placebo_summary["path"],
            "sample_stride": int(stride),
            "sampled_voxel_count_lsd": lsd_summary["sampled_voxel_count"],
            "sampled_voxel_count_placebo": placebo_summary["sampled_voxel_count"],
            "volume_count_lsd": lsd_summary["volume_count"],
            "volume_count_placebo": placebo_summary["volume_count"],
            "volume_count_balanced": lsd_summary["volume_count"] == placebo_summary["volume_count"],
        }
        for feature in QC_FEATURES:
            lsd_value = _as_float(lsd_summary.get(feature))
            placebo_value = _as_float(placebo_summary.get(feature))
            if lsd_value is None or placebo_value is None:
                continue
            row[f"{feature}_lsd"] = lsd_value
            row[f"{feature}_placebo"] = placebo_value
            row[f"{feature}_delta_lsd_minus_placebo"] = lsd_value - placebo_value
            row[f"{feature}_mean_abs"] = (abs(lsd_value) + abs(placebo_value)) / 2.0
        for metric, value in delta_metrics.items():
            number = _as_float(value)
            if number is not None:
                row[str(metric)] = number
        rows.append(row)
    return rows, missing


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
    qc_features = sorted(
        key
        for key in rows[0]
        if key.endswith(("_delta_lsd_minus_placebo", "_mean_abs"))
        and (
            key.startswith("image_dvars_")
            or key.startswith("com_displacement_")
            or key.startswith("global_signal_derivative_")
        )
    )
    dynamic_metrics = sorted(
        key
        for key in rows[0]
        if key
        not in {
            "subject",
            "run",
            "subject_view_path",
            "lsd_bold_path",
            "placebo_bold_path",
            "sample_stride",
            "sampled_voxel_count_lsd",
            "sampled_voxel_count_placebo",
            "volume_count_lsd",
            "volume_count_placebo",
            "volume_count_balanced",
        }
        and not any(key.startswith(f"{feature}_") for feature in QC_FEATURES)
        and any(_as_float(row.get(key)) is not None for row in rows)
    )
    output: list[dict[str, Any]] = []
    for feature in qc_features:
        for metric in dynamic_metrics:
            clean = [
                (float(x), float(y))
                for row in rows
                if (x := _as_float(row.get(feature))) is not None and (y := _as_float(row.get(metric))) is not None
            ]
            if len(clean) < MIN_OVERLAP:
                continue
            x_values = np.asarray([pair[0] for pair in clean], dtype=float)
            y_values = np.asarray([pair[1] for pair in clean], dtype=float)
            if np.isclose(np.std(x_values), 0.0) or np.isclose(np.std(y_values), 0.0):
                continue
            pearson = stats.pearsonr(x_values, y_values)
            if not math.isfinite(float(pearson.statistic)) or not math.isfinite(float(pearson.pvalue)):
                continue
            spearman = stats.spearmanr(x_values, y_values)
            spearman_rho = float(spearman.statistic) if math.isfinite(float(spearman.statistic)) else 0.0
            spearman_p = float(spearman.pvalue) if math.isfinite(float(spearman.pvalue)) else 1.0
            output.append(
                {
                    "image_motion_qc_feature": feature,
                    "dynamic_metric": metric,
                    "n": len(clean),
                    "pearson_r": float(pearson.statistic),
                    "pearson_p": float(pearson.pvalue),
                    "spearman_rho": spearman_rho,
                    "spearman_p": spearman_p,
                }
            )
    q_values = _bh_q_values([float(row["pearson_p"]) for row in output])
    for row, q_value in zip(output, q_values, strict=True):
        row["pearson_q"] = q_value
        row["image_motion_qc_sensitivity_flag"] = bool(math.isfinite(q_value) and q_value <= 0.05 and abs(float(row["pearson_r"])) >= 0.5)
    return output


def _exclusion_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    burden_features = [
        "com_displacement_mean_mm_mean_abs",
        "image_dvars_mean_mean_abs",
        "global_signal_derivative_rms_mean_abs",
    ]
    dynamic_metrics = sorted(
        key
        for key in rows[0]
        if key
        not in {
            "subject",
            "run",
            "subject_view_path",
            "lsd_bold_path",
            "placebo_bold_path",
            "sample_stride",
            "sampled_voxel_count_lsd",
            "sampled_voxel_count_placebo",
            "volume_count_lsd",
            "volume_count_placebo",
            "volume_count_balanced",
        }
        and not any(key.startswith(f"{feature}_") for feature in QC_FEATURES)
        and any(_as_float(row.get(key)) is not None for row in rows)
    )
    output: list[dict[str, Any]] = []
    for burden_key in burden_features:
        burdens = np.asarray([_as_float(row.get(burden_key)) for row in rows], dtype=float)
        burdens = burdens[np.isfinite(burdens)]
        if burdens.size < MIN_OVERLAP or np.isclose(np.std(burdens), 0.0):
            continue
        threshold = float(np.quantile(burdens, HIGH_BURDEN_QUANTILE))
        retained_rows = [row for row in rows if (_as_float(row.get(burden_key)) or 0.0) <= threshold]
        excluded_rows = [row for row in rows if (_as_float(row.get(burden_key)) or 0.0) > threshold]
        for metric in dynamic_metrics:
            all_values = np.asarray([_as_float(row.get(metric)) for row in rows], dtype=float)
            retained_values = np.asarray([_as_float(row.get(metric)) for row in retained_rows], dtype=float)
            excluded_values = np.asarray([_as_float(row.get(metric)) for row in excluded_rows], dtype=float)
            all_values = all_values[np.isfinite(all_values)]
            retained_values = retained_values[np.isfinite(retained_values)]
            excluded_values = excluded_values[np.isfinite(excluded_values)]
            if all_values.size == 0 or retained_values.size == 0:
                continue
            mean_all = float(np.mean(all_values))
            mean_retained = float(np.mean(retained_values))
            relative_change_abs = abs(mean_retained - mean_all) / max(abs(mean_all), 1e-12)
            direction_preserved = bool(
                np.sign(mean_all) == np.sign(mean_retained) or np.isclose(mean_all, 0.0) or np.isclose(mean_retained, 0.0)
            )
            output.append(
                {
                    "dynamic_metric": metric,
                    "burden_feature": burden_key,
                    "high_burden_quantile": HIGH_BURDEN_QUANTILE,
                    "high_burden_threshold": threshold,
                    "n_all": int(all_values.size),
                    "n_retained_after_high_burden_exclusion": int(retained_values.size),
                    "n_excluded_high_burden": int(excluded_values.size),
                    "mean_all": mean_all,
                    "mean_after_exclusion": mean_retained,
                    "mean_high_burden_only": float(np.mean(excluded_values)) if excluded_values.size else None,
                    "direction_preserved_after_exclusion": direction_preserved,
                    "relative_change_abs": relative_change_abs,
                    "unstable_after_high_burden_exclusion": bool((not direction_preserved) or relative_change_abs >= 0.5),
                }
            )
    return output


def _blocked(repo_root: Path, status: str, blocker: str, view_root: Path, missing: list[dict[str, Any]], *, stride: int) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": status,
        "image_motion_qc_ready": False,
        "source_paths": {
            "subject_dynamic_views": _rel(view_root, repo_root),
            "raw_bold_root": "data/ds003059",
        },
        "sample_stride": int(stride),
        "input_contract": {
            "raw_bold_files": "data/ds003059/sub-*/ses-{LSD,PLCB}/func/*_bold.nii.gz",
            "dynamic_subject_views": "results/stage_2/empirical_viewer/subject_views/*.json",
            "minimum_overlap": MIN_OVERLAP,
            "method": "downsampled raw-BOLD image DVARS, center-of-mass displacement, and global-signal derivative QC proxies",
        },
        "blocker": blocker,
        "missing_or_failed_records": missing[:40],
        "missing_or_failed_record_count": len(missing),
        "subject_run_count": 0,
        "association_rows": [],
        "high_risk_image_motion_qc_association_count": 0,
        "high_burden_exclusion_rows": [],
        "unstable_high_burden_exclusion_count": 0,
        "claim_status": "not_proven_image_motion_qc_missing",
        "claim_guardrail": (
            "Raw-BOLD image QC is unavailable. This layer is intended as a conservative sensitivity check and does not replace "
            "fMRIPrep FD, DVARS, motion-parameter, or censoring confounds."
        ),
    }


def build_image_motion_qc_status(repo_root: Path = REPO_ROOT, *, stride: int = DEFAULT_STRIDE) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    view_root = repo_root / "results" / "stage_2" / "empirical_viewer" / "subject_views"
    rows, missing = _load_subject_run_rows(repo_root, view_root, stride=stride)
    if len(rows) < MIN_OVERLAP:
        return _blocked(
            repo_root,
            "blocked_insufficient_raw_bold_subject_run_overlap",
            f"Only {len(rows)} subject/run rows had paired LSD/placebo raw BOLD QC summaries; need at least {MIN_OVERLAP}.",
            view_root,
            missing,
            stride=stride,
        )
    association_rows = _association_rows(rows)
    if not association_rows:
        return _blocked(
            repo_root,
            "blocked_insufficient_variance_for_image_motion_qc_tests",
            "Raw-BOLD QC rows exist, but no nonconstant image-QC feature/dynamic-metric associations could be estimated.",
            view_root,
            missing,
            stride=stride,
        )
    exclusion_rows = _exclusion_rows(rows)
    high_risk_count = sum(1 for row in association_rows if row["image_motion_qc_sensitivity_flag"])
    unstable_exclusions = sum(1 for row in exclusion_rows if row["unstable_after_high_burden_exclusion"])
    balanced_records = sum(1 for row in rows if row.get("volume_count_balanced"))
    unique_bolds = sorted({str(row["lsd_bold_path"]) for row in rows} | {str(row["placebo_bold_path"]) for row in rows})
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": "implemented_image_derived_motion_qc_control",
        "image_motion_qc_ready": True,
        "source_paths": {
            "subject_dynamic_views": _rel(view_root, repo_root),
            "raw_bold_root": "data/ds003059",
        },
        "sample_stride": int(stride),
        "input_contract": {
            "raw_bold_files": "data/ds003059/sub-*/ses-{LSD,PLCB}/func/*_bold.nii.gz",
            "dynamic_subject_views": "results/stage_2/empirical_viewer/subject_views/*.json",
            "minimum_overlap": MIN_OVERLAP,
            "method": "downsampled raw-BOLD image DVARS, center-of-mass displacement, and global-signal derivative QC proxies",
        },
        "method_status": "implemented_conservative_raw_bold_qc_proxy_not_fmriprep_fd",
        "subject_run_count": len(rows),
        "subject_count": len({str(row["subject"]) for row in rows}),
        "run_count": len({str(row["run"]) for row in rows}),
        "raw_bold_file_count": len(unique_bolds),
        "raw_bold_files": unique_bolds,
        "balanced_condition_volume_records": balanced_records,
        "unbalanced_condition_volume_records": len(rows) - balanced_records,
        "missing_or_failed_records": missing[:40],
        "missing_or_failed_record_count": len(missing),
        "association_rows": association_rows,
        "high_risk_image_motion_qc_association_count": high_risk_count,
        "high_burden_exclusion_rows": exclusion_rows,
        "unstable_high_burden_exclusion_count": unstable_exclusions,
        "subject_run_qc_rows": rows,
        "claim_status": (
            "image_motion_qc_sensitive_downgrade_required"
            if high_risk_count or unstable_exclusions
            else "no_image_motion_qc_sensitivity_detected"
        ),
        "limitations": [
            "This is derived directly from raw BOLD images using downsampled image summaries.",
            "It is not a rigid-body realignment estimate, not fMRIPrep framewise displacement, and not a censoring column.",
            "It provides a dedicated signal-quality/motion sensitivity layer when authorized fMRIPrep confounds are unavailable.",
        ],
        "claim_guardrail": (
            "This is a conservative image-derived motion/QC control, not a full fMRIPrep FD/DVARS/censoring proof. "
            "If high-risk associations or unstable high-burden exclusions appear, motion-sensitive mechanism claims must be downgraded."
        ),
    }


def _write_csv(rows: list[dict[str, Any]], path: Path, fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = fieldnames or sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _markdown(status: dict[str, Any]) -> str:
    lines = [
        "# Image-Derived Motion/QC Control Status",
        "",
        status["claim_guardrail"],
        "",
        f"- Status: `{status['analysis_status']}`",
        f"- Claim status: `{status['claim_status']}`",
        f"- Subject/run rows: `{status['subject_run_count']}`",
        f"- Raw BOLD files summarized: `{status.get('raw_bold_file_count', 0)}`",
        f"- High-risk image-QC associations: `{status['high_risk_image_motion_qc_association_count']}`",
        f"- Unstable high-burden exclusions: `{status['unstable_high_burden_exclusion_count']}`",
        "",
    ]
    if status.get("association_rows"):
        lines.extend(
            [
                "## Strongest image-derived motion/QC associations",
                "",
                "| Feature | Metric | n | r | q | Flag |",
                "| --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        ranked = sorted(status["association_rows"], key=lambda row: abs(float(row["pearson_r"])), reverse=True)
        for row in ranked[:12]:
            lines.append(
                "| {feature} | {metric} | {n} | {r:.3f} | {q:.3f} | {flag} |".format(
                    feature=row["image_motion_qc_feature"],
                    metric=row["dynamic_metric"],
                    n=row["n"],
                    r=float(row["pearson_r"]),
                    q=float(row["pearson_q"]),
                    flag="yes" if row["image_motion_qc_sensitivity_flag"] else "no",
                )
            )
    else:
        lines.extend(["## Blocker", "", str(status.get("blocker") or "No image-derived motion/QC result is available."), ""])
    return "\n".join(lines) + "\n"


def write_image_motion_qc_status(
    repo_root: Path = REPO_ROOT,
    output_dir: Path | None = None,
    *,
    stride: int = DEFAULT_STRIDE,
    force: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "confound_controls"
    output_dir.mkdir(parents=True, exist_ok=True)
    status_path = output_dir / "image_motion_qc_status.json"
    report_path = output_dir / "image_motion_qc_status.md"
    association_csv = output_dir / "image_motion_qc_dynamic_associations.csv"
    exclusion_csv = output_dir / "image_motion_qc_high_burden_exclusion.csv"
    subject_run_csv = output_dir / "image_motion_qc_subject_runs.csv"
    if not force and status_path.exists():
        cached = _read_json(status_path)
        if cached and cached.get("image_motion_qc_ready") and int(cached.get("sample_stride") or stride) == int(stride):
            report_path.write_text(_markdown(cached), encoding="utf-8")
            _write_csv(cached.get("association_rows", []), association_csv)
            _write_csv(cached.get("high_burden_exclusion_rows", []), exclusion_csv)
            _write_csv(cached.get("subject_run_qc_rows", []), subject_run_csv)
            cached["source_path"] = _rel(status_path, repo_root)
            cached["report_path"] = _rel(report_path, repo_root)
            cached["association_csv_path"] = _rel(association_csv, repo_root)
            cached["exclusion_csv_path"] = _rel(exclusion_csv, repo_root)
            cached["subject_run_csv_path"] = _rel(subject_run_csv, repo_root)
            return cached

    status = build_image_motion_qc_status(repo_root, stride=stride)
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    _write_csv(status["association_rows"], association_csv)
    _write_csv(status["high_burden_exclusion_rows"], exclusion_csv)
    _write_csv(status.get("subject_run_qc_rows", []), subject_run_csv)
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    status["association_csv_path"] = _rel(association_csv, repo_root)
    status["exclusion_csv_path"] = _rel(exclusion_csv, repo_root)
    status["subject_run_csv_path"] = _rel(subject_run_csv, repo_root)
    return status
