from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from lsd_thesis.data.ds003059 import atlas_label_overlap_rows
from lsd_thesis.subject_split import build_no_subject_validation_boundary

REPO_ROOT = Path(__file__).resolve().parents[3]


def build_provenance_payload(stage_summaries: dict[str, Any]) -> dict[str, Any]:
    stage_2 = cast(dict[str, Any], stage_summaries.get("stage_2", {}))
    empirical_provenance = cast(dict[str, Any], stage_2.get("empirical_provenance", {}))
    cache_fingerprint = empirical_provenance.get("cache_fingerprint")
    version_stamp = cast(dict[str, Any], stage_2.get("version_stamp", {}))
    git = cast(
        dict[str, Any],
        version_stamp.get(
            "git",
            {
                "repo_present": False,
                "branch": None,
                "head_present": False,
                "commit_hash": None,
                "worktree_status": "not_repo",
            },
        ),
    )
    target_paths = cast(dict[str, Any], empirical_provenance.get("target_paths", {}))
    return {
        "dataset_anchor": empirical_provenance.get("dataset_anchor") or stage_2.get("dataset_anchor"),
        "subject_count": empirical_provenance.get("subject_count"),
        "run_count": empirical_provenance.get("run_count"),
        "sessions": empirical_provenance.get("sessions", []),
        "target_filenames": {
            "sober": Path(str(target_paths["sober"])).name if target_paths.get("sober") else None,
            "perturbation": Path(str(target_paths["perturbation"])).name if target_paths.get("perturbation") else None,
        },
        "git": git,
        "timestamp": version_stamp.get("timestamp"),
        "cache_fingerprint": cache_fingerprint,
        "cache_schema_version": empirical_provenance.get("cache_schema_version"),
        "cache_created_at_utc": empirical_provenance.get("cache_created_at_utc"),
        "preprocessing_qc": empirical_provenance.get("preprocessing_qc", {}),
    }


def build_model_selection_payload(stage_summaries: dict[str, Any]) -> dict[str, Any]:
    stage_2 = cast(dict[str, Any], stage_summaries.get("stage_2", {}))
    seed_plan = cast(dict[str, Any], stage_2.get("fit_seed_plan", {}))
    multi_seed_summary = cast(dict[str, Any], stage_2.get("multi_seed_summary", {}))
    selection_seeds = list(seed_plan.get("selection_seeds", []))
    validation_seeds = list(seed_plan.get("validation_seeds", []))
    return {
        "selection_mode": seed_plan.get("selection_mode", "unknown"),
        "selection_seeds": selection_seeds,
        "selection_seed_count": len(selection_seeds),
        "validation_mode": seed_plan.get("validation_mode", "unknown"),
        "validation_seeds": validation_seeds,
        "validation_seed_count": len(validation_seeds),
        "selected_iteration": stage_2.get("selected_iteration"),
        "selection_score_mean": stage_2.get("best_score"),
        "selection_score_std": stage_2.get("selection_score_std"),
        "validation_score_mean": multi_seed_summary.get("score_mean"),
        "validation_score_std": multi_seed_summary.get("score_std"),
        "uncertainty_available": bool(multi_seed_summary.get("std_metrics")),
        "claim_guardrail": (
            "Multi-seed selection/validation reduces single-realization dependence, "
            "but does not imply held-out empirical validation."
        ),
    }


def build_empirical_validation_payload(stage_summaries: dict[str, Any]) -> dict[str, Any]:
    stage_2 = cast(dict[str, Any], stage_summaries.get("stage_2", {}))
    stage_3 = cast(dict[str, Any], stage_summaries.get("stage_3", {}))
    stage_3_boundary = stage_3.get("empirical_validation_boundary")
    boundary: Any
    if (
        isinstance(stage_3_boundary, dict)
        and stage_3_boundary.get("held_out_validation_completed") is True
    ):
        boundary = stage_3_boundary
        source_stage = "stage_3"
    else:
        boundary = stage_2.get("empirical_validation_boundary")
        source_stage = "stage_2"
    if isinstance(boundary, dict):
        payload = dict(boundary)
        configured = bool(payload.get("held_out_validation_configured", payload.get("held_out") is True))
        completed = bool(payload.get("held_out_validation_completed", payload.get("held_out") is True))
        payload.setdefault("held_out_validation_configured", configured)
        payload.setdefault("held_out_validation_completed", completed)
        payload.setdefault("held_out", completed)
        payload.setdefault(
            "approval_status",
            "approved" if completed else "candidate" if configured else "none",
        )
        payload.setdefault("overlap_count", 0)
        payload.setdefault("warnings", [])
        payload.setdefault("limitations", [])
        payload.setdefault("source_stage", source_stage)
        return payload
    return build_no_subject_validation_boundary(
        selection_data_source=stage_2.get("dataset_anchor"),
        selection_subject_count=None,
    )


def load_cv5_validation_payload(repo_root: Path) -> dict[str, Any] | None:
    aggregate_path = (
        repo_root
        / "output"
        / "validation"
        / "cv5_subject_disjoint"
        / "results"
        / "cv5_aggregate_validation.json"
    )
    if not aggregate_path.exists():
        return None
    payload = cast(dict[str, Any], json.loads(aggregate_path.read_text(encoding="utf-8")))
    payload.setdefault("source_path", aggregate_path.relative_to(repo_root).as_posix())
    payload.setdefault(
        "claim_guardrail",
        "CV5 subject-disjoint validation is internal validation only, not external or clinical validation.",
    )
    return payload


def _sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def build_audit_status(
    stage_summaries: dict[str, Any],
    empirical: dict[str, Any],
    provenance: dict[str, Any],
    atlas_audit: dict[str, Any] | None = None,
    empirical_data_quality: dict[str, Any] | None = None,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    empirical_deltas = cast(dict[str, float], empirical.get("target_deltas", {}))
    literature_deltas = cast(dict[str, float], empirical.get("literature_deltas", {}))
    sign_mismatches: list[dict[str, Any]] = []
    sign_aligned: list[dict[str, Any]] = []
    for metric_name in sorted(set(empirical_deltas).intersection(literature_deltas)):
        empirical_delta = float(empirical_deltas[metric_name])
        literature_delta = float(literature_deltas[metric_name])
        empirical_sign = _sign(empirical_delta)
        literature_sign = _sign(literature_delta)
        row = {
            "metric": metric_name,
            "empirical_delta": empirical_delta,
            "literature_delta": literature_delta,
        }
        if empirical_sign != 0 and literature_sign != 0 and empirical_sign != literature_sign:
            sign_mismatches.append(row)
        else:
            sign_aligned.append(row)

    git = cast(dict[str, Any], provenance.get("git", {}))
    stage_3 = cast(dict[str, Any], stage_summaries.get("stage_3", {}))
    atlas_payload = atlas_audit or {}
    quality_payload = empirical_data_quality or {}
    model_selection = build_model_selection_payload(stage_summaries)
    empirical_validation = build_empirical_validation_payload(stage_summaries)
    cv5_validation = load_cv5_validation_payload(repo_root)
    cache_fingerprint = provenance.get("cache_fingerprint")
    return {
        "defensible_claim": "Transparent surrogate and mismatch analysis, not a mechanistic psychedelic simulator.",
        "claim_guardrail": "Use the dashboard to compare empirical ds003059 deltas, literature-style targets, and model deltas side by side.",
        "sign_mismatches": sign_mismatches,
        "sign_aligned": sign_aligned,
        "atlas_overlaps": atlas_payload.get("overlaps", atlas_label_overlap_rows()),
        "atlas_voxel_counts": atlas_payload.get("module_voxel_counts", {}),
        "atlas_assigned_voxels": atlas_payload.get("assigned_voxels"),
        "empirical_record_count": quality_payload.get("record_count"),
        "empirical_paired_subject_count": quality_payload.get("paired_subject_count"),
        "empirical_complete_subject_count": quality_payload.get("complete_subject_count"),
        "empirical_timepoints": quality_payload.get("timepoints", {}),
        "preprocessing_qc": quality_payload.get("preprocessing_qc") or provenance.get("preprocessing_qc", {}),
        "model_selection": model_selection,
        "empirical_validation": empirical_validation,
        "cv5_validation": cv5_validation,
        "cache_status": {
            "status": "fingerprinted" if cache_fingerprint else "unknown",
            "fingerprint": cache_fingerprint,
            "schema_version": provenance.get("cache_schema_version"),
            "created_at_utc": provenance.get("cache_created_at_utc"),
            "claim_guardrail": (
                "A fingerprinted cache means generated targets match recorded metadata; "
                "it is not independent biological validation."
                if cache_fingerprint
                else "No cache fingerprint is recorded for the current Stage 2 artifacts."
            ),
        },
        "stage3_best_mechanism": stage_3.get("robust_best_mechanism") or stage_3.get("best_mechanism"),
        "stage3_score": stage_3.get("robust_best_score_mean") or stage_3.get("best_score"),
        "stage3_score_std": stage_3.get("robust_best_score_std"),
        "stage3_sign_agreement_fraction": stage_3.get("robust_best_sign_agreement_fraction"),
        "provenance_warning": (
            "No git HEAD is recorded for the current artifacts; commit a baseline before treating outputs as thesis provenance."
            if not git.get("head_present")
            else ""
        ),
        "validation_badges": [
            {"label": "ruff", "status": "documented passing", "command": "uv run ruff check ."},
            {"label": "mypy", "status": "documented passing", "command": "uv run mypy src"},
            {
                "label": "fast smoke",
                "status": "preferred iteration gate",
                "command": "uv run pytest tests/test_simulator.py tests/test_ds003059.py tests/test_perturbation.py tests/test_web.py -q -o addopts=",
            },
            {"label": "full pytest", "status": "currently slow", "command": "uv run pytest"},
        ],
    }
