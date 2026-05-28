from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

FD_COLUMNS = ("framewise_displacement", "fd", "FD", "FramewiseDisplacement")
DVARS_COLUMNS = ("std_dvars", "dvars", "DVARS", "stdDVARS", "standardized_dvars")
MOTION_FILE_PATTERN = re.compile(r"(confound|motion|fd|dvars|censor|scrub|desc-confounds|regress)", re.IGNORECASE)
MOTION_FILE_GLOBS = (
    "*desc-confounds_timeseries.tsv",
    "*confounds*.tsv",
    "*confounds*.csv",
    "*motion*.tsv",
    "*motion*.csv",
    "*fd*.tsv",
    "*dvars*.tsv",
    "*censor*.tsv",
    "*scrub*.tsv",
)
REQUIRED_CONFOUND_COLUMNS = (
    "framewise_displacement or fd",
    "std_dvars or dvars",
    "motion_outlier*, scrub*, censor*, or non_steady_state* columns when available",
)
MINIMUM_PAIRING_CONTRACT = (
    "subject id",
    "session/condition label containing LSD and placebo/PLCB",
    "run id",
    "one confound table per subject/session/run or an equivalent long-form table",
)
DEFAULT_FD_THRESHOLD = 0.5


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _first_existing_column(frame: pd.DataFrame, candidates: Sequence[str]) -> str | None:
    lower_map = {column.lower(): column for column in frame.columns}
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
        if candidate.lower() in lower_map:
            return str(lower_map[candidate.lower()])
    return None


def _default_search_roots(root: Path, stage_2_dir: str | Path | None) -> tuple[Path, ...]:
    candidates = (
        root / "data" / "ds003059",
        root / "data",
        Path(stage_2_dir) if stage_2_dir is not None else root / "results" / "stage_2",
        root / "results" / "external_data",
        root / "results" / "psilocybin_ds006072",
    )
    deduped: list[Path] = []
    for candidate in candidates:
        path = candidate.resolve() if candidate.exists() else candidate
        if path not in deduped:
            deduped.append(path)
    return tuple(deduped)


def _motion_input_contract(root: Path, search_roots: Sequence[Path]) -> dict[str, Any]:
    return {
        "search_roots": [_relative_path(path, root) for path in search_roots],
        "expected_file_patterns": list(MOTION_FILE_GLOBS),
        "required_columns": list(REQUIRED_CONFOUND_COLUMNS),
        "minimum_pairing_contract": list(MINIMUM_PAIRING_CONTRACT),
        "example_fmriprep_path": "data/ds003059/derivatives/fmriprep/sub-*/ses-*/func/*desc-confounds_timeseries.tsv",
        "claim_guardrail": "The motion gate can only pass when structured confounds are present locally and join to subject/run dynamic deltas.",
    }


def _parse_subject_session_run(path: Path) -> dict[str, str | None]:
    text = path.as_posix()
    subject = re.search(r"sub-\d+", text)
    session = re.search(r"ses-[A-Za-z0-9]+", text)
    run = re.search(r"run-\d+", text)
    return {
        "subject": subject.group(0) if subject else None,
        "session": session.group(0) if session else None,
        "run": run.group(0) if run else None,
    }


def discover_motion_files(
    repo_root: str | Path | None = None,
    stage_2_dir: str | Path | None = None,
    roots: Sequence[str | Path] | None = None,
) -> tuple[Path, ...]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    search_roots = tuple(Path(item) for item in roots) if roots is not None else _default_search_roots(root, stage_2_dir)
    found: list[Path] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        try:
            for path in search_root.rglob("*"):
                if path.is_file() and MOTION_FILE_PATTERN.search(path.name) and path.suffix.lower() in {".tsv", ".csv", ".txt"}:
                    found.append(path)
        except OSError:
            continue
    return tuple(sorted(found, key=lambda item: item.as_posix()))


def summarize_motion_tsv(path: str | Path, fd_threshold: float = DEFAULT_FD_THRESHOLD) -> dict[str, Any]:
    motion_path = Path(path)
    try:
        frame = pd.read_csv(motion_path, sep="\t" if motion_path.suffix.lower() == ".tsv" else None, engine="python")
    except Exception as error:
        parsed = _parse_subject_session_run(motion_path)
        return {
            **parsed,
            "path": motion_path.as_posix(),
            "status": "found_unusable",
            "reason": f"could_not_read_motion_file: {error}",
        }

    fd_column = _first_existing_column(frame, FD_COLUMNS)
    dvars_column = _first_existing_column(frame, DVARS_COLUMNS)
    scrub_columns = [column for column in frame.columns if re.search(r"(scrub|censor|motion_outlier|non_steady_state)", column, re.IGNORECASE)]
    parsed = _parse_subject_session_run(motion_path)
    if fd_column is None and dvars_column is None and not scrub_columns:
        return {
            **parsed,
            "path": motion_path.as_posix(),
            "status": "found_unusable",
            "reason": "no_fd_dvars_or_scrub_columns",
        }

    fd_values = pd.to_numeric(frame[fd_column], errors="coerce").dropna().to_numpy(dtype=float) if fd_column is not None else np.asarray([], dtype=float)
    dvars_values = (
        pd.to_numeric(frame[dvars_column], errors="coerce").dropna().to_numpy(dtype=float)
        if dvars_column is not None
        else np.asarray([], dtype=float)
    )
    scrub_count = 0
    for column in scrub_columns:
        values = pd.to_numeric(frame[column], errors="coerce").fillna(0).to_numpy(dtype=float)
        scrub_count += int(np.count_nonzero(values > 0))
    volume_count = int(len(frame))
    return {
        **parsed,
        "path": motion_path.as_posix(),
        "status": "available_parsed",
        "volume_count": volume_count,
        "fd_column": fd_column,
        "mean_fd": float(np.mean(fd_values)) if len(fd_values) else None,
        "median_fd": float(np.median(fd_values)) if len(fd_values) else None,
        "max_fd": float(np.max(fd_values)) if len(fd_values) else None,
        "percent_fd_above_threshold": float(np.mean(fd_values > fd_threshold) * 100.0) if len(fd_values) else None,
        "dvars_column": dvars_column,
        "mean_dvars": float(np.mean(dvars_values)) if len(dvars_values) else None,
        "median_dvars": float(np.median(dvars_values)) if len(dvars_values) else None,
        "max_dvars": float(np.max(dvars_values)) if len(dvars_values) else None,
        "scrub_columns": scrub_columns,
        "scrubbed_volume_count": scrub_count,
        "scrubbed_volume_proportion": float(scrub_count / volume_count) if volume_count else None,
    }


def build_motion_summary(
    repo_root: str | Path | None = None,
    stage_2_dir: str | Path | None = None,
    roots: Sequence[str | Path] | None = None,
    fd_threshold: float = DEFAULT_FD_THRESHOLD,
) -> dict[str, Any]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    search_roots = tuple(Path(item) for item in roots) if roots is not None else _default_search_roots(root, stage_2_dir)
    files = discover_motion_files(repo_root=root, stage_2_dir=stage_2_dir, roots=roots)
    input_contract = _motion_input_contract(root, search_roots)
    if not files:
        return {
            "schema_version": "setting_seed_motion_summary.v1",
            "status": "unavailable_not_found",
            "motion_files_present": False,
            "motion_analysis_ready": False,
            "motion_summary_schema_valid": False,
            "fd_threshold": fd_threshold,
            "motion_summary_files": [],
            "parsed_summary_count": 0,
            "unusable_file_count": 0,
            "coverage_by_run": {},
            "input_contract": input_contract,
            "next_action": "Place authorized fMRIPrep confounds TSV/CSV files under one configured search root, then rerun scripts/run_setting_seed_motion_summary.py.",
            "summaries": [],
            "claim_guardrail": "Motion sensitivity is unavailable until structured subject/session/run confounds are parsed.",
        }

    summaries = []
    for path in files:
        summary = summarize_motion_tsv(path, fd_threshold=fd_threshold)
        summary["path"] = _relative_path(path, root)
        summaries.append(summary)
    parsed = [summary for summary in summaries if summary.get("status") == "available_parsed"]
    coverage_by_run: dict[str, int] = {}
    for summary in parsed:
        run = str(summary.get("run") or "unknown")
        coverage_by_run[run] = coverage_by_run.get(run, 0) + 1
    status = "available_parsed" if parsed else "found_unusable"
    return {
        "schema_version": "setting_seed_motion_summary.v1",
        "status": status,
        "motion_files_present": True,
        "motion_analysis_ready": bool(parsed),
        "motion_summary_schema_valid": bool(parsed),
        "fd_threshold": fd_threshold,
        "motion_summary_files": [_relative_path(path, root) for path in files],
        "parsed_summary_count": len(parsed),
        "unusable_file_count": len(summaries) - len(parsed),
        "coverage_by_run": coverage_by_run,
        "input_contract": input_contract,
        "next_action": (
            "Run scripts/build_motion_confound_controls.py to join these motion summaries with subject/run dynamic deltas."
            if parsed
            else "Fix file format or add FD/DVARS/outlier columns, then rerun scripts/run_setting_seed_motion_summary.py."
        ),
        "summaries": summaries,
        "claim_guardrail": "Motion summaries are aggregate QC features only; raw traces and confound matrices are not embedded.",
    }


def motion_report_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Set / Setting / Seed Motion Summary",
        "",
        f"Status: {summary['status']}",
        "",
    ]
    if not summary.get("motion_files_present"):
        lines.append("No structured motion/confounds files were found in the configured local search roots.")
        contract = summary.get("input_contract", {}) if isinstance(summary.get("input_contract"), dict) else {}
        if contract:
            lines.extend(
                [
                    "",
                    "## Required local input contract",
                    "",
                    f"- Search roots: `{', '.join(contract.get('search_roots', []))}`",
                    f"- Expected patterns: `{', '.join(contract.get('expected_file_patterns', []))}`",
                    f"- Required columns: `{', '.join(contract.get('required_columns', []))}`",
                    f"- Example path: `{contract.get('example_fmriprep_path')}`",
                ]
            )
    else:
        lines.extend(
            [
                f"Files found: {len(summary.get('motion_summary_files', []))}",
                f"Parsed summaries: {summary.get('parsed_summary_count', 0)}",
                f"Unusable files: {summary.get('unusable_file_count', 0)}",
                f"Coverage by run: {json.dumps(summary.get('coverage_by_run', {}), sort_keys=True)}",
            ]
        )
    lines.extend(
        [
            "",
            "Guardrail: no motion sensitivity claim is made unless structured subject/session/run coverage exists.",
            "",
        ]
    )
    return "\n".join(lines)


def write_motion_outputs(
    output_dir: str | Path | None = None,
    repo_root: str | Path | None = None,
    stage_2_dir: str | Path | None = None,
    roots: Sequence[str | Path] | None = None,
    fd_threshold: float = DEFAULT_FD_THRESHOLD,
) -> dict[str, Any]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    out_dir = root / "results" / "setting_seed" / "motion" if output_dir is None else Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = build_motion_summary(repo_root=root, stage_2_dir=stage_2_dir, roots=roots, fd_threshold=fd_threshold)
    (out_dir / "motion_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if summary.get("summaries"):
        pd.DataFrame(summary["summaries"]).to_csv(out_dir / "motion_summary.csv", index=False)
    (out_dir / "motion_report.md").write_text(motion_report_markdown(summary), encoding="utf-8")
    return summary
