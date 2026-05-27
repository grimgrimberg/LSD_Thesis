from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from lsd_thesis.setting_seed.data import DEFAULT_STAGE_2_DIR, MUSIC_EXCLUDED_SUBJECTS, _default_repo_root, load_run_records


def difference_in_differences(*, plcb_rest1: float, plcb_rest3: float, lsd_rest1: float, lsd_rest3: float) -> float:
    return float((lsd_rest3 - lsd_rest1) - (plcb_rest3 - plcb_rest1))


def context_memory_trace(runs: list[str], points_per_run: int = 100, tau: float = 8.0) -> dict[str, np.ndarray]:
    if points_per_run <= 0:
        raise ValueError("points_per_run must be positive.")
    if tau <= 0:
        raise ValueError("tau must be positive.")
    u_music = np.asarray([1.0 if run == "run-02" else 0.0 for run in runs for _ in range(points_per_run)], dtype=float)
    context = np.zeros_like(u_music)
    for index in range(1, len(context)):
        context[index] = context[index - 1] + (u_music[index - 1] - context[index - 1]) / tau
    return {"u_music": u_music, "context_memory": context}


def compute_rest_carryover_effects(stage_2_dir: str | Path | None = None) -> pd.DataFrame:
    stage_2_path = DEFAULT_STAGE_2_DIR if stage_2_dir is None else Path(stage_2_dir)
    records = load_run_records(stage_2_path)
    metric_names = sorted(records[0]["metrics"]) if records else []
    values: dict[tuple[str, str, str], dict[str, float]] = {}
    for record in records:
        values[(str(record["subject"]), str(record["session"]), str(record["run"]))] = {
            metric: float(value) for metric, value in record["metrics"].items()
        }
    rows: list[dict[str, Any]] = []
    for subject in sorted({subject for subject, _, _ in values}):
        needed = [
            (subject, "ses-PLCB", "run-01"),
            (subject, "ses-PLCB", "run-03"),
            (subject, "ses-LSD", "run-01"),
            (subject, "ses-LSD", "run-03"),
        ]
        if not all(key in values for key in needed):
            continue
        for metric in metric_names:
            rows.append(
                {
                    "subject": subject,
                    "metric": metric,
                    "plcb_rest_carryover": values[(subject, "ses-PLCB", "run-03")][metric] - values[(subject, "ses-PLCB", "run-01")][metric],
                    "lsd_rest_carryover": values[(subject, "ses-LSD", "run-03")][metric] - values[(subject, "ses-LSD", "run-01")][metric],
                    "drug_carryover_interaction": difference_in_differences(
                        plcb_rest1=values[(subject, "ses-PLCB", "run-01")][metric],
                        plcb_rest3=values[(subject, "ses-PLCB", "run-03")][metric],
                        lsd_rest1=values[(subject, "ses-LSD", "run-01")][metric],
                        lsd_rest3=values[(subject, "ses-LSD", "run-03")][metric],
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_music_control_scaffold(
    run_02_available: bool,
    stage_2_dir: str | Path | None = None,
    *,
    run_02_analysis_ready: bool | None = None,
    motion_analysis_ready: bool = False,
) -> dict[str, Any]:
    run_ready = bool(run_02_available) if run_02_analysis_ready is None else run_02_analysis_ready
    if not run_02_available:
        status = "blocked_missing_run_02"
    elif not run_ready:
        status = "blocked_incomplete_run_02"
    elif not motion_analysis_ready:
        status = "blocked_missing_motion_review"
    else:
        status = "ready_descriptive_only"
    scaffold: dict[str, Any] = {
        "schema_version": "setting_seed_control_scaffold.v1",
        "status": status,
        "run_02_files_present": bool(run_02_available),
        "run_02_analysis_ready": run_ready,
        "motion_analysis_ready": motion_analysis_ready,
        "u_music_definition": "u_music(t)=0 during Rest1, 1 during Music, 0 during Rest3.",
        "context_memory_definition": "dc/dt = -c/tau + u_music(t); implemented as an explicit discrete scaffold.",
        "music_excluded_subjects": list(MUSIC_EXCLUDED_SUBJECTS),
        "available_effects": ["rest1_to_rest3_carryover_proxy", "drug_carryover_interaction"],
        "unavailable_effects": ["setting_effect", "music_to_rest3_displacement", "drug_setting_interaction"] if status != "ready_descriptive_only" else [],
        "claim_guardrail": (
            "No music-control empirical claim is made yet; future descriptive music-control comparison is not a mechanism, "
            "clinical, or subjective-experience claim."
        ),
    }
    if stage_2_dir is not None:
        carryover = compute_rest_carryover_effects(stage_2_dir)
        scaffold["rest_carryover_rows"] = int(len(carryover))
        scaffold["rest_carryover_metric_count"] = int(carryover["metric"].nunique()) if len(carryover) else 0
    return scaffold


def scaffold_report_markdown(scaffold: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Music-Control Scaffold",
            "",
            f"Status: {scaffold['status']}",
            "",
            f"- Run-02 files present: {str(scaffold.get('run_02_files_present')).lower()}",
            f"- Run-02 analysis ready: {str(scaffold.get('run_02_analysis_ready')).lower()}",
            f"- Motion analysis ready: {str(scaffold.get('motion_analysis_ready')).lower()}",
            "- Music-control analysis remains scaffolded until run-02 coverage and motion review are ready.",
            "- S03, S12, and S15 will be excluded when music analysis becomes available.",
            "- No music-control empirical claim is made yet.",
            "",
            f"Definition: {scaffold['u_music_definition']}",
            f"Context memory: {scaffold['context_memory_definition']}",
            "",
        ]
    )


def write_control_outputs(
    stage_2_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    repo_root: str | Path | None = None,
    run_02_available: bool = False,
    run_02_analysis_ready: bool | None = None,
    motion_analysis_ready: bool = False,
) -> dict[str, Any]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    out_dir = root / "results" / "setting_seed" / "control" if output_dir is None else Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scaffold = build_music_control_scaffold(
        run_02_available=run_02_available,
        stage_2_dir=stage_2_dir,
        run_02_analysis_ready=run_02_analysis_ready,
        motion_analysis_ready=motion_analysis_ready,
    )
    (out_dir / "control_scaffold.json").write_text(json.dumps(scaffold, indent=2), encoding="utf-8")
    (out_dir / "music_control_report.md").write_text(scaffold_report_markdown(scaffold), encoding="utf-8")
    carryover = compute_rest_carryover_effects(stage_2_dir)
    carryover.to_csv(out_dir / "rest_carryover_effects.csv", index=False)
    return scaffold
