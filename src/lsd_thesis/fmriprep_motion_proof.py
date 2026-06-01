from __future__ import annotations

import json
import re
import shutil
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lsd_thesis.motion_source_availability import DS003059_DATASET_ID, DS003059_VERSION, query_openneuro_snapshot_files
from lsd_thesis.setting_seed.motion import build_motion_summary, discover_motion_files

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "fmriprep_motion_proof_plan.v1"
SUBJECT_PATTERN = re.compile(r"sub-\d+")
MOTION_LIKE_PATTERN = re.compile(
    r"(desc-confounds|confounds|framewise_displacement|std_dvars|dvars|motion_outlier|motion|fd|censor|scrub|regress)",
    re.IGNORECASE,
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _is_appledouble(path_or_name: str | Path) -> bool:
    return Path(path_or_name).name.startswith("._")


def _subject_id(path_or_name: str | Path) -> str | None:
    match = SUBJECT_PATTERN.search(str(path_or_name).replace("\\", "/"))
    return match.group(0) if match else None


def _runtime_availability(overrides: Mapping[str, bool] | None = None) -> dict[str, bool]:
    if overrides is not None:
        return {
            "docker": bool(overrides.get("docker", False)),
            "apptainer": bool(overrides.get("apptainer", False)),
            "singularity": bool(overrides.get("singularity", False)),
            "fmriprep": bool(overrides.get("fmriprep", False)),
        }
    return {
        "docker": shutil.which("docker") is not None,
        "apptainer": shutil.which("apptainer") is not None,
        "singularity": shutil.which("singularity") is not None,
        "fmriprep": shutil.which("fmriprep") is not None,
    }


def _local_nifti_state(repo_root: Path) -> dict[str, Any]:
    dataset_root = repo_root / "data" / DS003059_DATASET_ID
    bold_files = tuple(
        path
        for path in sorted(dataset_root.glob("sub-*/ses-*/func/*_bold.nii.gz"))
        if path.is_file() and not _is_appledouble(path)
    )
    t1w_files = tuple(
        path
        for path in sorted(dataset_root.glob("sub-*/anat/*_T1w.nii.gz"))
        if path.is_file() and not _is_appledouble(path)
    )
    appledouble_t1w_files = tuple(
        path
        for path in sorted(dataset_root.glob("sub-*/anat/._*_T1w.nii.gz"))
        if path.is_file()
    )
    bold_subjects = sorted({subject for path in bold_files if (subject := _subject_id(path))})
    t1w_subjects = sorted({subject for path in t1w_files if (subject := _subject_id(path))})
    return {
        "dataset_root": _rel(dataset_root, repo_root),
        "local_bold_run_count": len(bold_files),
        "local_bold_subject_count": len(bold_subjects),
        "local_bold_subjects": bold_subjects,
        "local_t1w_count": len(t1w_files),
        "local_t1w_subject_count": len(t1w_subjects),
        "local_t1w_subjects": t1w_subjects,
        "appledouble_t1w_placeholder_count": len(appledouble_t1w_files),
        "missing_t1w_subjects_for_local_bold": sorted(set(bold_subjects) - set(t1w_subjects)),
    }


def _remote_snapshot_state(openneuro_files: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    t1w_files = [
        str(item.get("filename") or "")
        for item in openneuro_files
        if not bool(item.get("directory"))
        and not _is_appledouble(str(item.get("filename") or ""))
        and str(item.get("filename") or "").endswith("_T1w.nii.gz")
    ]
    motion_like_files = [
        str(item.get("filename") or "")
        for item in openneuro_files
        if not bool(item.get("directory"))
        and MOTION_LIKE_PATTERN.search(str(item.get("filename") or ""))
        and not _is_appledouble(str(item.get("filename") or ""))
    ]
    return {
        "checked": bool(openneuro_files),
        "file_count": len(openneuro_files),
        "t1w_file_count": len(t1w_files),
        "t1w_subject_count": len({subject for filename in t1w_files if (subject := _subject_id(filename))}),
        "confound_like_file_count": len(motion_like_files),
        "confound_like_files": motion_like_files[:50],
    }


def build_fmriprep_motion_proof_plan(
    repo_root: str | Path = REPO_ROOT,
    *,
    roots: Sequence[str | Path] | None = None,
    openneuro_files: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    fetch_remote: bool = False,
    runtime_availability: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    motion_roots = tuple(Path(item) for item in roots) if roots is not None else None
    dataset_description_path = root / "data" / DS003059_DATASET_ID / "dataset_description.json"
    dataset_description = _read_json(dataset_description_path)
    dataset_type = str(dataset_description.get("DatasetType") or "unknown").lower()
    local_state = _local_nifti_state(root)
    existing_motion_files = discover_motion_files(repo_root=root, roots=motion_roots)
    existing_motion_summary = build_motion_summary(repo_root=root, roots=motion_roots)
    runtime = _runtime_availability(runtime_availability)
    remote_error: str | None = None
    if openneuro_files is None and fetch_remote:
        try:
            openneuro_files = query_openneuro_snapshot_files()
        except Exception as error:
            openneuro_files = []
            remote_error = str(error)
    remote_state = _remote_snapshot_state(tuple(openneuro_files or ()))
    remote_state["error"] = remote_error

    has_parsed_confounds = bool(existing_motion_summary.get("motion_analysis_ready"))
    has_structured_confounds = bool(existing_motion_summary.get("motion_pairing_ready"))
    has_container_or_runtime = any(runtime.values())
    dataset_is_derivative = dataset_type == "derivative"
    local_t1w_complete = not local_state["missing_t1w_subjects_for_local_bold"] and local_state["local_t1w_subject_count"] > 0
    local_bold_present = local_state["local_bold_run_count"] > 0

    if has_structured_confounds:
        analysis_status = "structured_subject_level_confounds_available"
        blocker = ""
        preflight_ready = True
        next_action = "Run scripts/run_setting_seed_motion_summary.py, then scripts/build_motion_confound_controls.py."
    elif has_parsed_confounds:
        analysis_status = "structured_confounds_present_but_insufficient_pairing"
        blocker = (
            "Structured FD/DVARS/censoring confounds were found, but they do not yet cover enough paired "
            "LSD and placebo/PLCB subject/run rows for the strict motion-control association test."
        )
        preflight_ready = False
        next_action = str(
            existing_motion_summary.get("next_action")
            or "Supply paired LSD and placebo/PLCB subject/run confounds, then rerun the motion gate."
        )
    elif dataset_is_derivative:
        analysis_status = "blocked_derivative_snapshot_not_valid_raw_fmriprep_input"
        blocker = (
            "The local ds003059 dataset_description declares DatasetType=derivative and no subject/run FD, DVARS, or censoring tables are present. "
            "Do not run fMRIPrep on this derivative snapshot as if it were original raw BIDS."
        )
        preflight_ready = False
        next_action = (
            "Obtain author-provided subject/run motion confounds or the original raw BIDS inputs that preceded this derivative release; "
            "then run fMRIPrep/MRIQC in a container or HPC environment and ingest desc-confounds_timeseries.tsv files."
        )
    elif not local_bold_present:
        analysis_status = "blocked_missing_local_bold_inputs"
        blocker = "No local ds003059 BOLD NIfTI files were found for fMRIPrep preprocessing."
        preflight_ready = False
        next_action = "Download authorized original raw BIDS BOLD and T1w inputs before running fMRIPrep."
    elif not local_t1w_complete:
        analysis_status = "blocked_missing_local_t1w_inputs"
        blocker = "Local BOLD files exist, but matching non-AppleDouble T1w files are missing for at least one BOLD subject."
        preflight_ready = False
        next_action = "Download matching non-AppleDouble T1w files for every local BOLD subject, then rerun this preflight."
    elif not has_container_or_runtime:
        analysis_status = "blocked_missing_fmriprep_runtime"
        blocker = "BIDS-like inputs are present, but no docker, apptainer, singularity, or fmriprep executable is available on PATH."
        preflight_ready = False
        next_action = (
            "Run preprocessing on a machine with a supported fMRIPrep runtime, then copy desc-confounds_timeseries.tsv "
            "outputs into data/ds003059/derivatives/fmriprep/."
        )
    else:
        analysis_status = "ready_to_run_fmriprep_preprocessing"
        blocker = ""
        preflight_ready = True
        next_action = (
            "Run fMRIPrep on original raw BIDS inputs, then ingest desc-confounds_timeseries.tsv files with "
            "scripts/run_setting_seed_motion_summary.py."
        )

    expected_confound_glob = "data/ds003059/derivatives/fmriprep/sub-*/ses-*/func/*desc-confounds_timeseries.tsv"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": analysis_status,
        "fmriprep_motion_proof_ready": has_structured_confounds,
        "fmriprep_preflight_ready": preflight_ready,
        "dataset": {
            "id": DS003059_DATASET_ID,
            "version": DS003059_VERSION,
            "dataset_type": dataset_type,
            "dataset_description_path": _rel(dataset_description_path, root),
        },
        "local_nifti_state": local_state,
        "existing_motion_confounds": {
            "motion_file_count": len(existing_motion_files),
            "motion_analysis_ready": has_parsed_confounds,
            "motion_pairing_ready": has_structured_confounds,
            "motion_summary_status": existing_motion_summary.get("status"),
            "parsed_summary_count": existing_motion_summary.get("parsed_summary_count", 0),
            "paired_subject_run_count": existing_motion_summary.get("paired_subject_run_count", 0),
            "minimum_paired_subject_run_count": existing_motion_summary.get("minimum_paired_subject_run_count"),
            "expected_confound_glob": expected_confound_glob,
            "configured_motion_roots": [_rel(path, root) for path in motion_roots] if motion_roots else [],
        },
        "remote_openneuro_snapshot": remote_state,
        "runtime_availability": runtime,
        "blocker": blocker,
        "next_action": next_action,
        "required_outputs": [
            expected_confound_glob,
            "results/setting_seed/motion/motion_summary.json",
            "results/confound_controls/motion_confound_control_status.json",
        ],
        "minimum_required_columns": [
            "framewise_displacement",
            "std_dvars or dvars",
            "motion_outlier_* or censor/scrub/non_steady_state columns where available",
        ],
        "claim_guardrail": (
            "This is a preprocessing/acquisition preflight, not a motion-safety result. The strict motion gate only passes after real "
            "subject/session/run confounds are parsed and joined to dynamic deltas."
        ),
    }


def _markdown(payload: dict[str, Any]) -> str:
    local_state = payload.get("local_nifti_state", {}) if isinstance(payload.get("local_nifti_state"), dict) else {}
    remote_state = payload.get("remote_openneuro_snapshot", {}) if isinstance(payload.get("remote_openneuro_snapshot"), dict) else {}
    runtime = payload.get("runtime_availability", {}) if isinstance(payload.get("runtime_availability"), dict) else {}
    existing_confounds = payload.get("existing_motion_confounds", {}) if isinstance(payload.get("existing_motion_confounds"), dict) else {}
    lines = [
        "# fMRIPrep Motion-Proof Preflight",
        "",
        str(payload["claim_guardrail"]),
        "",
        f"- Status: `{payload['analysis_status']}`",
        f"- Strict proof ready: `{payload['fmriprep_motion_proof_ready']}`",
        f"- Preflight ready: `{payload['fmriprep_preflight_ready']}`",
        f"- Dataset type: `{(payload.get('dataset') or {}).get('dataset_type', 'unknown')}`",
        f"- Local BOLD runs: `{local_state.get('local_bold_run_count', 0)}`",
        f"- Local non-AppleDouble T1w subjects: `{local_state.get('local_t1w_subject_count', 0)}`",
        f"- Missing T1w subjects: `{', '.join(local_state.get('missing_t1w_subjects_for_local_bold', [])) or 'none'}`",
        f"- Parsed local confound summaries: `{existing_confounds.get('parsed_summary_count', 0)}`",
        f"- Paired LSD/placebo subject-run confound rows: `{existing_confounds.get('paired_subject_run_count', 0)}`",
        f"- OpenNeuro snapshot T1w files: `{remote_state.get('t1w_file_count', 0)}`",
        f"- OpenNeuro snapshot confound-like files: `{remote_state.get('confound_like_file_count', 0)}`",
        f"- Runtime availability: `{json.dumps(runtime, sort_keys=True)}`",
        "",
        "## Blocker",
        "",
        str(payload.get("blocker") or "No blocker recorded."),
        "",
        "## Next Action",
        "",
        str(payload.get("next_action") or "No next action recorded."),
        "",
    ]
    return "\n".join(lines)


def write_fmriprep_motion_proof_plan(
    repo_root: str | Path = REPO_ROOT,
    output_dir: str | Path | None = None,
    *,
    roots: Sequence[str | Path] | None = None,
    fetch_remote: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out_dir = root / "results" / "confound_controls" if output_dir is None else Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_fmriprep_motion_proof_plan(root, roots=roots, fetch_remote=fetch_remote)
    status_path = out_dir / "fmriprep_motion_proof_plan.json"
    report_path = out_dir / "fmriprep_motion_proof_plan.md"
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(payload), encoding="utf-8")
    payload["source_path"] = _rel(status_path, root)
    payload["report_path"] = _rel(report_path, root)
    return payload
