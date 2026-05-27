from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, stdev
from typing import Any

import yaml

from lsd_thesis.data.ds003059 import (
    MODULE_NAMES,
    Ds003059RestManifest,
    build_empirical_cache_metadata,
    build_empirical_target_payloads,
)
from lsd_thesis.fit import generate_stage_2_outputs
from lsd_thesis.perturbation import generate_stage_3_outputs
from lsd_thesis.subject_split import (
    load_subject_split_file,
    validate_cv5_subject_split_manifest,
)

CV5_AGGREGATE_SCHEMA_VERSION = 1
CV5_VALIDATION_CLAIM_SCOPE = "preliminary_internal_subject_disjoint_cv5"
CV5_AGGREGATE_FILENAME = "cv5_aggregate_validation.json"


def _read_json_object(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return raw


def _repo_relative_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _maybe_repo_relative_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _git_metadata(repo_root: Path) -> dict[str, Any]:
    def run_git(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    commit_hash = run_git("rev-parse", "HEAD")
    return {
        "head_present": bool(commit_hash),
        "commit_hash": commit_hash,
        "branch": run_git("branch", "--show-current"),
        "worktree_status": run_git("status", "--short"),
    }


def _cv5_run_command(
    *,
    manifest_path: Path,
    output_dir: Path,
    repo_root: Path,
    fit_iterations: int,
    seed: int,
) -> str:
    return (
        "uv run python scripts/run_cv5_validation.py "
        f"--manifest {_maybe_repo_relative_path(manifest_path, repo_root)} "
        f"--output-dir {_maybe_repo_relative_path(output_dir, repo_root)} "
        f"--fit-iterations {fit_iterations} --seed {seed}"
    )


def _ensure_no_existing_fold_outputs(output_dir: Path, fold_count: int) -> None:
    collisions: list[Path] = []
    for fold_index in range(1, fold_count + 1):
        fold_dir = output_dir / f"fold_{fold_index:02d}"
        for stage_dir in (fold_dir / "stage2", fold_dir / "stage3"):
            if stage_dir.exists() and any(stage_dir.iterdir()):
                collisions.append(stage_dir)
    aggregate_path = output_dir / CV5_AGGREGATE_FILENAME
    if aggregate_path.exists():
        try:
            existing_aggregate = _read_json_object(aggregate_path)
        except (OSError, ValueError):
            existing_aggregate = {}
        if existing_aggregate.get("completed_folds") not in {0, None} or existing_aggregate.get(
            "source_fold_output_paths"
        ):
            collisions.append(aggregate_path)
    if collisions:
        joined = ", ".join(str(path) for path in collisions)
        raise FileExistsError(
            "Refusing to run CV5 validation because fold output paths already contain files: "
            f"{joined}. Use a new output directory to preserve existing outputs."
        )


def _mean_std(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "std": None}
    return {
        "mean": float(mean(values)),
        "std": float(stdev(values)) if len(values) > 1 else 0.0,
    }


def _metric_mean_std(per_fold: list[dict[str, float]]) -> dict[str, dict[str, float | None]]:
    metric_names = sorted({name for item in per_fold for name in item})
    return {
        name: _mean_std([float(item[name]) for item in per_fold if name in item])
        for name in metric_names
    }


def _fold_id(fold_index: int) -> str:
    return f"fold_{fold_index:02d}"


def _write_empirical_cache_from_existing_stage2(
    *,
    source_stage2_dir: Path,
    output_dir: Path,
    dataset_dir: Path | None = None,
    subjects: tuple[str, ...],
) -> None:
    sober_path = output_dir / "empirical_sober_targets.yaml"
    perturbation_path = output_dir / "empirical_perturbation_targets.yaml"
    manifest_path = output_dir / "ds003059_rest_manifest.json"
    records_path = output_dir / "empirical_run_summaries.json"
    if sober_path.exists() and perturbation_path.exists() and manifest_path.exists() and records_path.exists():
        return

    source_manifest = Ds003059RestManifest.model_validate(
        _read_json_object(source_stage2_dir / "ds003059_rest_manifest.json")
    )
    source_records = json.loads((source_stage2_dir / "empirical_run_summaries.json").read_text(encoding="utf-8"))
    if not isinstance(source_records, list):
        raise ValueError(f"Expected list of empirical run summaries in {source_stage2_dir}.")
    subject_set = set(subjects)
    filtered_records = [record for record in source_records if str(record.get("subject")) in subject_set]
    if not filtered_records:
        raise ValueError(f"No cached Stage 2 records matched requested subjects: {subjects}.")
    filtered_manifest = Ds003059RestManifest(
        subjects=tuple(sorted(subject_set)),
        runs=tuple(run for run in source_manifest.runs if run.subject in subject_set),
        sidecars=source_manifest.sidecars,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for record in filtered_records:
        relative_series_path = Path(str(record["time_series_path"]))
        source_series_path = source_stage2_dir / relative_series_path
        target_series_path = output_dir / relative_series_path
        if not source_series_path.exists():
            raise FileNotFoundError(f"Cached module time-series file is missing: {source_series_path}.")
        target_series_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_series_path, target_series_path)

    sober_payload, perturbation_payload = build_empirical_target_payloads(
        records=filtered_records,
        module_names=MODULE_NAMES,
    )
    sober_path.write_text(yaml.safe_dump(sober_payload, sort_keys=False), encoding="utf-8")
    perturbation_path.write_text(
        yaml.safe_dump(perturbation_payload, sort_keys=False),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(filtered_manifest.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    records_path.write_text(json.dumps(filtered_records, indent=2), encoding="utf-8")
    cache_metadata = build_empirical_cache_metadata(
        output_path=output_dir,
        manifest=filtered_manifest,
        records=filtered_records,
        requested_subjects=subjects,
        dataset_dir=dataset_dir,
    )
    (output_dir / "empirical_cache_metadata.json").write_text(
        json.dumps(cache_metadata, indent=2),
        encoding="utf-8",
    )


def _validate_stage_2_fold_outputs(
    *,
    stage2_summary: dict[str, Any],
    split_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    split = load_subject_split_file(split_path)
    boundary = stage2_summary.get("empirical_validation_boundary")
    if not isinstance(boundary, dict):
        raise ValueError(f"Stage 2 did not write empirical_validation_boundary for {split_path}.")
    if boundary.get("approval_status") != "approved":
        raise ValueError(f"Stage 2 boundary is not approved for {split_path}.")
    if int(boundary.get("selection_subject_count") or 0) != len(split.selection_subjects):
        raise ValueError(f"Stage 2 selection count does not match split file {split_path}.")
    if int(boundary.get("validation_subject_count") or 0) != len(split.validation_subjects):
        raise ValueError(f"Stage 2 validation count does not match split file {split_path}.")
    if int(boundary.get("overlap_count") or 0) != 0:
        raise ValueError(f"Stage 2 recorded subject overlap for {split_path}.")
    empirical_subjects = tuple(stage2_summary.get("empirical_subjects") or ())
    if tuple(sorted(empirical_subjects)) != tuple(sorted(split.selection_subjects)):
        raise ValueError(f"Stage 2 empirical targets were not limited to selection subjects for {split_path}.")

    heldout_paths = stage2_summary.get("heldout_validation_target_paths")
    if not isinstance(heldout_paths, dict):
        raise ValueError(f"Stage 2 did not prepare held-out validation target artifacts for {split_path}.")
    heldout_subjects = tuple(heldout_paths.get("subjects") or ())
    if tuple(sorted(heldout_subjects)) != tuple(sorted(split.validation_subjects)):
        raise ValueError(f"Stage 2 held-out targets do not match validation subjects for {split_path}.")
    for key in ("sober", "perturbation"):
        target_path = Path(str(heldout_paths.get(key) or ""))
        if not target_path.exists():
            raise ValueError(f"Stage 2 held-out {key} target is missing for {split_path}: {target_path}.")
        try:
            target_path.resolve().relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Stage 2 held-out {key} target is outside the repo: {target_path}.") from exc
    return heldout_paths


def _validate_stage_3_fold_outputs(
    *,
    stage3_summary: dict[str, Any],
    split_path: Path,
) -> dict[str, Any]:
    boundary = stage3_summary.get("empirical_validation_boundary")
    if not isinstance(boundary, dict):
        raise ValueError(f"Stage 3 did not write empirical_validation_boundary for {split_path}.")
    if boundary.get("approval_status") != "approved":
        raise ValueError(f"Stage 3 boundary is not approved for {split_path}.")
    if boundary.get("held_out_validation_completed") is not True:
        raise ValueError(f"Stage 3 did not complete held-out validation for {split_path}.")
    heldout_eval = stage3_summary.get("heldout_validation_evaluation")
    if not isinstance(heldout_eval, dict) or heldout_eval.get("status") != "completed":
        raise ValueError(f"Stage 3 did not record a completed held-out evaluation for {split_path}.")
    return heldout_eval


def _run_one_fold(
    *,
    fold_index: int,
    split_path: Path,
    output_dir: Path,
    repo_root: Path,
    fit_iterations: int,
    seed: int,
) -> dict[str, Any]:
    split = load_subject_split_file(split_path)
    if not split.is_approved:
        raise ValueError(f"CV5 fold split is not approved: {split_path}.")

    fold_dir = output_dir / _fold_id(fold_index)
    stage2_dir = fold_dir / "stage2"
    stage3_dir = fold_dir / "stage3"
    stage2_report_path = stage2_dir / "stage_2.md"
    stage3_report_path = stage3_dir / "stage_3.md"
    source_stage2_dir = repo_root / "results" / "stage_2"
    _write_empirical_cache_from_existing_stage2(
        source_stage2_dir=source_stage2_dir,
        output_dir=stage2_dir,
        dataset_dir=repo_root / "data" / "ds003059",
        subjects=split.selection_subjects,
    )
    _write_empirical_cache_from_existing_stage2(
        source_stage2_dir=source_stage2_dir,
        output_dir=stage2_dir / "heldout_validation",
        dataset_dir=repo_root / "data" / "ds003059",
        subjects=split.validation_subjects,
    )

    stage2_summary = generate_stage_2_outputs(
        graph_path=repo_root / "configs" / "graphs" / "macro_modules.yaml",
        baseline_path=repo_root / "configs" / "regimes" / "baseline.yaml",
        target_path=repo_root / "configs" / "targets" / "sober_summary_targets.yaml",
        output_dir=stage2_dir,
        report_path=stage2_report_path,
        iterations=fit_iterations,
        seed=seed,
        dataset_dir=repo_root / "data" / "ds003059",
        subject_split_path=split_path,
        build_viewer=False,
    )
    heldout_paths = _validate_stage_2_fold_outputs(
        stage2_summary=stage2_summary,
        split_path=split_path,
        repo_root=repo_root,
    )

    stage3_summary = generate_stage_3_outputs(
        graph_path=repo_root / "configs" / "graphs" / "macro_modules.yaml",
        baseline_path=repo_root / "configs" / "regimes" / "baseline.yaml",
        sober_target_path=stage2_dir / "empirical_sober_targets.yaml",
        perturbation_target_path=stage2_dir / "empirical_perturbation_targets.yaml",
        output_dir=stage3_dir,
        report_path=stage3_report_path,
        fit_iterations=fit_iterations,
        strengths=(0.1, 0.25, 0.5, 0.75),
        seed=seed,
        subject_split_path=split_path,
        heldout_sober_target_path=heldout_paths["sober"],
        heldout_perturbation_target_path=heldout_paths["perturbation"],
    )
    heldout_eval = _validate_stage_3_fold_outputs(
        stage3_summary=stage3_summary,
        split_path=split_path,
    )

    metadata = {
        "fold_id": _fold_id(fold_index),
        "fold_index": fold_index,
        "split_id": split.split_id,
        "split_file_path": _repo_relative_path(split_path, repo_root),
        "approval_status": split.approval_status,
        "selection_subjects": list(split.selection_subjects),
        "validation_subjects": list(split.validation_subjects),
        "selection_subject_count": len(split.selection_subjects),
        "validation_subject_count": len(split.validation_subjects),
        "overlap_count": 0,
        "stage2_result": {
            "status": "completed",
            "summary_path": _repo_relative_path(stage2_dir / "stage_2_summary.json", repo_root),
            "report_path": _repo_relative_path(stage2_report_path, repo_root),
            "heldout_target_paths": heldout_paths,
        },
        "stage3_result": {
            "status": "completed",
            "summary_path": _repo_relative_path(stage3_dir / "stage_3_summary.json", repo_root),
            "report_path": _repo_relative_path(stage3_report_path, repo_root),
        },
        "held_out_validation_completed": True,
        "key_metric_outputs": {
            "selected_mechanism": heldout_eval["selected_mechanism"],
            "selected_strength": heldout_eval["selected_strength"],
            "score_mean": heldout_eval["score_mean"],
            "score_std": heldout_eval["score_std"],
            "sign_agreement_fraction": heldout_eval["sign_agreement_fraction"],
            "delta_metrics_mean": heldout_eval["delta_metrics_mean"],
            "delta_metrics_std": heldout_eval["delta_metrics_std"],
        },
    }
    fold_dir.mkdir(parents=True, exist_ok=True)
    (fold_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def build_cv5_aggregate_validation(
    *,
    manifest_path: Path,
    output_dir: Path,
    repo_root: Path,
    per_fold_metadata: list[dict[str, Any]],
    fold_errors: list[dict[str, Any]] | None = None,
    fit_iterations: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    manifest = _read_json_object(manifest_path)
    summary = validate_cv5_subject_split_manifest(manifest_path, repo_root=repo_root)
    fold_errors = fold_errors or []
    completed_folds = len(per_fold_metadata)
    total_folds = int(summary["number_of_folds"])
    all_folds_completed = completed_folds == total_folds and not fold_errors
    score_means = [float(item["key_metric_outputs"]["score_mean"]) for item in per_fold_metadata]
    sign_agreements = [
        float(item["key_metric_outputs"]["sign_agreement_fraction"])
        for item in per_fold_metadata
    ]
    delta_metric_means = [
        dict(item["key_metric_outputs"].get("delta_metrics_mean", {}))
        for item in per_fold_metadata
    ]
    selected_mechanisms = Counter(
        str(item["key_metric_outputs"]["selected_mechanism"])
        for item in per_fold_metadata
    )
    selected_strengths = Counter(
        str(item["key_metric_outputs"]["selected_strength"])
        for item in per_fold_metadata
    )
    limitations = list(dict.fromkeys(str(item) for item in manifest.get("limitations", [])))
    for limitation in (
        "n=15 complete paired subjects",
        "n=3 held-out subjects per fold",
        "No subject-level motion/FD/DVARS/confound/censoring stratification available",
        "Internal validation only; not external validation",
        "Interpret cautiously",
    ):
        if limitation not in limitations:
            limitations.append(limitation)

    aggregate_path = output_dir / CV5_AGGREGATE_FILENAME
    run_parameters: dict[str, Any] = {
        "manifest_path": _maybe_repo_relative_path(manifest_path, repo_root),
        "output_dir": _maybe_repo_relative_path(output_dir, repo_root),
        "aggregate_path": _maybe_repo_relative_path(aggregate_path, repo_root),
        "fit_iterations": fit_iterations,
        "seed": seed,
    }
    if fit_iterations is not None and seed is not None:
        run_parameters["run_command"] = _cv5_run_command(
            manifest_path=manifest_path,
            output_dir=output_dir,
            repo_root=repo_root,
            fit_iterations=fit_iterations,
            seed=seed,
        )

    aggregate = {
        "schema_version": CV5_AGGREGATE_SCHEMA_VERSION,
        "status": "complete" if all_folds_completed else "partial",
        "split_set_id": summary["split_set_id"],
        "approval_status": summary["approval_status"],
        "approved_by": summary.get("approved_by"),
        "approved_at": summary.get("approved_at"),
        "validation_claim_scope": (
            summary.get("validation_claim_scope") or CV5_VALIDATION_CLAIM_SCOPE
        ),
        "completed_folds": completed_folds,
        "total_folds": total_folds,
        "all_folds_completed": all_folds_completed,
        "all_subjects_held_out_once": bool(
            summary["validation_coverage_summary"]["every_subject_held_out_exactly_once"]
        ),
        "total_subjects": summary["number_of_subjects"],
        "per_fold_subject_counts": [
            {
                "fold_id": item["fold_id"],
                "selection_subject_count": item["selection_subject_count"],
                "validation_subject_count": item["validation_subject_count"],
                "overlap_count": item["overlap_count"],
            }
            for item in per_fold_metadata
        ],
        "per_fold_metrics": [
            {
                "fold_id": item["fold_id"],
                **item["key_metric_outputs"],
            }
            for item in per_fold_metadata
        ],
        "aggregate_metrics": {
            "score_mean": _mean_std(score_means),
            "sign_agreement_fraction": _mean_std(sign_agreements),
            "delta_metrics_mean": _metric_mean_std(delta_metric_means),
            "selected_mechanism_counts": dict(sorted(selected_mechanisms.items())),
            "selected_strength_counts": dict(sorted(selected_strengths.items())),
        },
        "uncertainty": {
            "fold_dispersion": "Sample standard deviation across the five held-out folds where available.",
            "interpretation": (
                "Fold dispersion is not an external confidence interval; n=3 held out per fold "
                "limits precision."
            ),
        },
        "warnings": [
            "This is internal subject-disjoint validation, not external or clinical validation.",
            "No subject-level motion/FD/DVARS/confound/censoring stratification is available.",
        ],
        "limitations": limitations,
        "run_parameters": run_parameters,
        "provenance": {
            "generated_by": "lsd_thesis.cv5_validation.build_cv5_aggregate_validation",
            "python_version": sys.version.split()[0],
            "git": _git_metadata(repo_root),
        },
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source_manifest_path": _repo_relative_path(manifest_path, repo_root),
        "source_candidate_manifest": manifest.get("source_candidate_manifest"),
        "approved_manifest_path": _repo_relative_path(manifest_path, repo_root),
        "aggregate_path": _maybe_repo_relative_path(aggregate_path, repo_root),
        "source_fold_output_paths": [
            {
                "fold_id": item["fold_id"],
                "metadata_path": _repo_relative_path(
                    output_dir / item["fold_id"] / "metadata.json",
                    repo_root,
                ),
                "stage2_summary_path": item["stage2_result"]["summary_path"],
                "stage3_summary_path": item["stage3_result"]["summary_path"],
            }
            for item in per_fold_metadata
        ],
        "fold_errors": fold_errors,
        "held_out_validation_completed": all_folds_completed,
    }
    return aggregate


def refresh_cv5_aggregate_from_existing_outputs(
    *,
    manifest_path: Path,
    output_dir: Path,
    repo_root: Path,
    fit_iterations: int = 64,
    seed: int = 11,
) -> dict[str, Any]:
    summary = validate_cv5_subject_split_manifest(manifest_path, repo_root=repo_root)
    per_fold_metadata: list[dict[str, Any]] = []
    for fold in summary["fold_summaries"]:
        fold_id = _fold_id(int(fold["fold_index"]))
        metadata_path = output_dir / fold_id / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"CV5 fold metadata is missing: {metadata_path}")
        per_fold_metadata.append(_read_json_object(metadata_path))
    aggregate = build_cv5_aggregate_validation(
        manifest_path=manifest_path,
        output_dir=output_dir,
        repo_root=repo_root,
        per_fold_metadata=per_fold_metadata,
        fit_iterations=fit_iterations,
        seed=seed,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / CV5_AGGREGATE_FILENAME).write_text(
        json.dumps(aggregate, indent=2),
        encoding="utf-8",
    )
    return aggregate


def run_cv5_validation(
    *,
    manifest_path: Path,
    output_dir: Path,
    repo_root: Path,
    fit_iterations: int = 64,
    seed: int = 11,
) -> dict[str, Any]:
    summary = validate_cv5_subject_split_manifest(manifest_path, repo_root=repo_root)
    if summary["approval_status"] != "approved":
        raise ValueError("CV5 validation runner requires an approved CV5 manifest.")
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    _ensure_no_existing_fold_outputs(output_dir, int(summary["number_of_folds"]))

    per_fold_metadata: list[dict[str, Any]] = []
    fold_errors: list[dict[str, Any]] = []
    try:
        for fold in summary["fold_summaries"]:
            fold_index = int(fold["fold_index"])
            split_path = (repo_root / str(fold["file_path"])).resolve()
            per_fold_metadata.append(
                _run_one_fold(
                    fold_index=fold_index,
                    split_path=split_path,
                    output_dir=output_dir,
                    repo_root=repo_root,
                    fit_iterations=fit_iterations,
                    seed=seed,
                )
            )
    except Exception as exc:
        fold_errors.append(
            {
                "fold_index": len(per_fold_metadata) + 1,
                "status": "failed",
                "error": str(exc),
            }
        )
        aggregate = build_cv5_aggregate_validation(
            manifest_path=manifest_path,
            output_dir=output_dir,
            repo_root=repo_root,
            per_fold_metadata=per_fold_metadata,
            fold_errors=fold_errors,
            fit_iterations=fit_iterations,
            seed=seed,
        )
        (output_dir / CV5_AGGREGATE_FILENAME).write_text(
            json.dumps(aggregate, indent=2),
            encoding="utf-8",
        )
        raise

    aggregate = build_cv5_aggregate_validation(
        manifest_path=manifest_path,
        output_dir=output_dir,
        repo_root=repo_root,
        per_fold_metadata=per_fold_metadata,
        fit_iterations=fit_iterations,
        seed=seed,
    )
    (output_dir / CV5_AGGREGATE_FILENAME).write_text(
        json.dumps(aggregate, indent=2),
        encoding="utf-8",
    )
    return aggregate
