from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from lsd_thesis.setting_seed.data import DEFAULT_STAGE_2_DIR, _default_repo_root, load_run_records
from lsd_thesis.setting_seed.motion import build_motion_summary
from lsd_thesis.utils import get_version_stamp

EXPECTED_SIGNS = {
    "cross_network_communication": 1,
    "thalamic_coupling": 1,
    "hierarchical_compression": 1,
    "within_network_stability": -1,
    "entropy_diversity": 1,
    "switching_rate": 1,
    "metastability_proxy": 1,
    "effective_barrier_proxy": -1,
}


def bootstrap_ci(values: np.ndarray, seed: int = 20260512, iterations: int = 1000, alpha: float = 0.05) -> tuple[float, float]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if len(finite) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    samples = rng.choice(finite, size=(iterations, len(finite)), replace=True)
    means = np.mean(samples, axis=1)
    return (float(np.quantile(means, alpha / 2.0)), float(np.quantile(means, 1.0 - alpha / 2.0)))


def sign_consistency(values: np.ndarray, reference_delta: float) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    finite = finite[np.abs(finite) > 1e-12]
    if len(finite) == 0 or abs(reference_delta) <= 1e-12:
        return 0.0
    return float(np.mean(np.sign(finite) == np.sign(reference_delta)))


def classify_reliability_tier(
    *,
    mean_delta: float,
    ci_low: float,
    ci_high: float,
    sign_consistency_fraction: float,
    confidence: str,
    theory_sign_conflict: bool,
    missingness_fraction: float,
) -> str:
    if missingness_fraction > 0.0 or not np.isfinite(mean_delta) or not np.isfinite(ci_low) or not np.isfinite(ci_high):
        return "Tier C"
    zero_degenerate = abs(mean_delta) <= 1e-12 and abs(ci_low) <= 1e-12 and abs(ci_high) <= 1e-12
    if zero_degenerate:
        return "Tier C"
    ci_excludes_zero = (ci_low > 0.0 and ci_high > 0.0) or (ci_low < 0.0 and ci_high < 0.0)
    if theory_sign_conflict and (ci_excludes_zero or sign_consistency_fraction >= 0.60):
        return "Tier D"
    if ci_excludes_zero and sign_consistency_fraction >= 0.70 and confidence in {"strong", "moderate"}:
        return "Tier A"
    if sign_consistency_fraction >= 0.60 and not theory_sign_conflict:
        return "Tier B"
    return "Tier C"


def summarize_metric_reliability(
    metric: str,
    subject_deltas: np.ndarray,
    *,
    confidence: str = "unknown",
    expected_sign: int | None = None,
    seed: int = 20260512,
    run_stability: str = "unavailable",
    motion_sensitivity: str = "unavailable",
) -> dict[str, Any]:
    values = np.asarray(subject_deltas, dtype=float)
    finite = values[np.isfinite(values)]
    mean_delta = float(np.mean(finite)) if len(finite) else float("nan")
    std_delta = float(np.std(finite, ddof=1)) if len(finite) > 1 else 0.0
    ci_low, ci_high = bootstrap_ci(finite, seed=seed) if len(finite) else (float("nan"), float("nan"))
    expected = expected_sign if expected_sign is not None else EXPECTED_SIGNS.get(metric)
    theory_sign_conflict = bool(expected is not None and abs(mean_delta) > 1e-12 and np.sign(mean_delta) != expected)
    consistency = sign_consistency(finite, mean_delta)
    missingness = float(1.0 - (len(finite) / len(values))) if len(values) else 1.0
    tier = classify_reliability_tier(
        mean_delta=mean_delta,
        ci_low=ci_low,
        ci_high=ci_high,
        sign_consistency_fraction=consistency,
        confidence=confidence,
        theory_sign_conflict=theory_sign_conflict,
        missingness_fraction=missingness,
    )
    return {
        "metric": metric,
        "mean_delta": mean_delta,
        "std_delta": std_delta,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ci_excludes_zero": bool((ci_low > 0.0 and ci_high > 0.0) or (ci_low < 0.0 and ci_high < 0.0)),
        "subject_count": int(len(finite)),
        "missingness": missingness,
        "sign_consistency": consistency,
        "current_confidence": confidence,
        "expected_sign": expected,
        "theory_sign_conflict": theory_sign_conflict,
        "run_stability": run_stability,
        "motion_sensitivity": motion_sensitivity,
        "tier": tier,
        "eligible_for_primary_fit": bool(tier == "Tier A" and motion_sensitivity == "available"),
        "eligibility_note": (
            "requires motion sensitivity review before primary model fitting"
            if tier == "Tier A" and motion_sensitivity != "available"
            else ""
        ),
    }


def paired_metric_deltas(stage_2_dir: str | Path | None = None) -> pd.DataFrame:
    stage_2_path = DEFAULT_STAGE_2_DIR if stage_2_dir is None else Path(stage_2_dir)
    records = load_run_records(stage_2_path)
    rows: list[dict[str, Any]] = []
    metric_names = sorted(cast(dict[str, Any], records[0]["metrics"]).keys()) if records else []
    grouped: dict[tuple[str, str, str], dict[str, float]] = {}
    for record in records:
        key = (str(record["subject"]), str(record["session"]), str(record["run"]))
        grouped[key] = {name: float(value) for name, value in cast(dict[str, Any], record["metrics"]).items()}
    subjects = sorted({subject for subject, _, _ in grouped})
    runs = sorted({run for _, _, run in grouped})
    for subject in subjects:
        for run in runs:
            lsd = grouped.get((subject, "ses-LSD", run))
            plcb = grouped.get((subject, "ses-PLCB", run))
            if lsd is None or plcb is None:
                continue
            row: dict[str, Any] = {"subject": subject, "run": run}
            for metric in metric_names:
                row[metric] = lsd[metric] - plcb[metric]
            rows.append(row)
    return pd.DataFrame(rows)


def _load_confidence(repo_root: Path) -> dict[str, str]:
    target_path = repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml"
    if not target_path.exists():
        return {}
    try:
        import yaml

        payload = yaml.safe_load(target_path.read_text(encoding="utf-8")) or {}
        return {str(key): str(value) for key, value in payload.get("confidence", {}).items()}
    except Exception:
        return {}


def _run_stability_labels(deltas: pd.DataFrame, metric: str) -> str:
    if "run" not in deltas or metric not in deltas:
        return "unavailable"
    run_means = deltas.groupby("run")[metric].mean()
    if len(run_means) < 2:
        return "unavailable"
    finite = run_means[np.isfinite(run_means)]
    if len(finite) < 2:
        return "unavailable"
    signs = np.sign(finite[np.abs(finite) > 1e-12])
    if len(signs) == 0:
        return "zero_degenerate"
    return "stable_same_sign" if len(set(signs.astype(int).tolist())) == 1 else "unstable_sign_flip"


def _motion_sensitivity_label(repo_root: Path, stage_2_dir: str | Path | None) -> str:
    summary = build_motion_summary(repo_root=repo_root, stage_2_dir=stage_2_dir)
    if summary.get("motion_analysis_ready"):
        return "available"
    if summary.get("status") == "found_unusable":
        return "unavailable_unusable_motion_summaries"
    return "unavailable_missing_motion_summaries"


def build_reliability_table(
    stage_2_dir: str | Path | None = None,
    repo_root: str | Path | None = None,
    seed: int = 20260512,
) -> list[dict[str, Any]]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    deltas = paired_metric_deltas(stage_2_dir)
    confidence = _load_confidence(root)
    motion_sensitivity = _motion_sensitivity_label(root, stage_2_dir)
    summaries: list[dict[str, Any]] = []
    for metric in [column for column in deltas.columns if column not in {"subject", "run"}]:
        by_subject = deltas.groupby("subject")[metric].mean().to_numpy(dtype=float)
        summaries.append(
            summarize_metric_reliability(
                metric,
                by_subject,
                confidence=confidence.get(metric, "unknown"),
                seed=seed,
                run_stability=_run_stability_labels(deltas, metric),
                motion_sensitivity=motion_sensitivity,
            )
        )
    return sorted(summaries, key=lambda row: str(row["metric"]))


def reliability_report_markdown(table: list[dict[str, Any]]) -> str:
    motion_status = table[0]["motion_sensitivity"] if table else "unavailable_missing_motion_summaries"
    lines = [
        "# Set / Setting / Seed Reliability Report",
        "",
        "Status: rest-only reliability gate from cached Stage 2 records.",
        "",
        f"Motion sensitivity status: {motion_status}.",
        "Run-02 music effects are not estimated in this report.",
        "",
        "| Metric | Tier | Delta | CI | Sign consistency | Conflict | Motion |",
        "|---|---|---:|---|---:|---|---|",
    ]
    for row in table:
        lines.append(
            f"| {row['metric']} | {row['tier']} | {row['mean_delta']:.6f} | "
            f"[{row['ci_low']:.6f}, {row['ci_high']:.6f}] | {row['sign_consistency']:.2f} | "
            f"{row['theory_sign_conflict']} | {row['motion_sensitivity']} |"
        )
    lines.extend(
        [
            "",
            "Interpretation guardrail: tiers are proxy reliability labels for rest-only module metrics, not biological proof.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reliability_outputs(
    stage_2_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    repo_root: str | Path | None = None,
    seed: int = 20260512,
) -> list[dict[str, Any]]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    out_dir = root / "results" / "setting_seed" / "reliability" if output_dir is None else Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    table = build_reliability_table(stage_2_dir=stage_2_dir, repo_root=root, seed=seed)
    (out_dir / "reliability_table.json").write_text(json.dumps(table, indent=2), encoding="utf-8")
    if table:
        with (out_dir / "reliability_table.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(table[0].keys()))
            writer.writeheader()
            writer.writerows(table)
    report = reliability_report_markdown(table)
    report += f"\nVersion stamp: `{json.dumps(get_version_stamp(root), sort_keys=True)}`\n"
    (out_dir / "reliability_report.md").write_text(report, encoding="utf-8")
    return table
