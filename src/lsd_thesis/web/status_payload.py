from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from lsd_thesis.data.ds003059 import atlas_label_overlap_rows
from lsd_thesis.subject_split import build_no_subject_validation_boundary

REPO_ROOT = Path(__file__).resolve().parents[3]
CV5_AGGREGATE_RELATIVE_PATH = Path(
    "output",
    "validation",
    "cv5_subject_disjoint",
    "results",
    "cv5_aggregate_validation.json",
)
CV5_CURATED_AGGREGATE_RELATIVE_PATH = Path(
    "results",
    "validation",
    "cv5_subject_disjoint",
    "cv5_aggregate_validation.json",
)
CV5_AGGREGATE_RELATIVE_PATHS = (
    CV5_AGGREGATE_RELATIVE_PATH,
    CV5_CURATED_AGGREGATE_RELATIVE_PATH,
)
CV5_APPROVED_MANIFEST_RELATIVE_PATH = Path(
    "output",
    "validation",
    "cv5_subject_disjoint",
    "approved",
    "subject_split_cv5_manifest_approved.json",
)


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def cv5_validation_integrity_errors(payload: dict[str, Any]) -> tuple[str, ...]:
    """Return errors that prevent a CV5 aggregate from counting as completed validation."""
    if payload.get("held_out_validation_completed") is not True:
        return ("held_out_validation_completed is not true",)

    errors: list[str] = []
    if payload.get("approval_status") != "approved":
        errors.append("completed CV5 validation requires an approved split package")
    if payload.get("all_folds_completed") is not True:
        errors.append("completed CV5 validation requires all folds to complete")
    if payload.get("all_subjects_held_out_once") is not True:
        errors.append("completed CV5 validation requires exact-once held-out subject coverage")

    completed_folds = _as_int(payload.get("completed_folds"))
    total_folds = _as_int(payload.get("total_folds"))
    if total_folds <= 1 or completed_folds != total_folds:
        errors.append("completed CV5 validation requires completed_folds == total_folds > 1")

    for row in payload.get("per_fold_subject_counts", []):
        if isinstance(row, dict) and _as_int(row.get("overlap_count")) != 0:
            errors.append("completed CV5 validation requires zero selection/validation subject overlap")
            break

    scope = str(payload.get("validation_claim_scope") or "").lower()
    if "internal" not in scope or "external" in scope:
        errors.append("CV5 validation scope must remain internal-only")

    caveats = " ".join(
        str(item)
        for item in [
            *list(payload.get("limitations", []) if isinstance(payload.get("limitations"), list) else []),
            *list(payload.get("warnings", []) if isinstance(payload.get("warnings"), list) else []),
        ]
    ).lower()
    for required in ("not external", "n=3", "motion", "fd/dvars"):
        if required not in caveats:
            errors.append(f"CV5 aggregate is missing required caveat: {required}")

    return tuple(errors)


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
    if isinstance(stage_3_boundary, dict) and (
        stage_3_boundary.get("held_out_validation_completed") is True
        and stage_3_boundary.get("approval_status") == "approved"
        and int(stage_3_boundary.get("overlap_count") or 0) == 0
    ):
        boundary = stage_3_boundary
        source_stage = "stage_3"
    else:
        boundary = stage_2.get("empirical_validation_boundary")
        source_stage = "stage_2"
    if isinstance(boundary, dict):
        payload = dict(boundary)
        legacy_held_out = payload.get("held_out") is True
        configured = bool(payload.get("held_out_validation_configured") is True)
        completed = bool(payload.get("held_out_validation_completed") is True)
        payload.setdefault("held_out_validation_configured", configured)
        payload.setdefault("held_out_validation_completed", completed)
        payload["held_out"] = completed
        payload.setdefault(
            "approval_status",
            "none" if not configured else str(payload.get("approval_status") or "candidate"),
        )
        if legacy_held_out and not completed:
            warnings = list(payload.get("warnings", []))
            warnings.append("Legacy held_out=true flag ignored without explicit held_out_validation_completed=true.")
            payload["warnings"] = warnings
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
    aggregate_path = next((repo_root / path for path in CV5_AGGREGATE_RELATIVE_PATHS if (repo_root / path).exists()), None)
    if aggregate_path is None:
        return None
    if not aggregate_path.exists():
        return None
    raw = json.loads(aggregate_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return None
    payload = cast(dict[str, Any], raw)
    payload.setdefault("source_path", aggregate_path.relative_to(repo_root).as_posix())
    payload.setdefault(
        "claim_guardrail",
        "CV5 subject-disjoint validation is internal validation only, not external or clinical validation.",
    )
    integrity_errors = cv5_validation_integrity_errors(payload)
    if integrity_errors:
        payload["validation_integrity_status"] = "invalid_or_incomplete"
        payload["validation_integrity_errors"] = list(integrity_errors)
        payload["held_out_validation_completed"] = False
        payload["status"] = "partial" if payload.get("status") != "complete" else "invalid_complete_metadata"
    else:
        payload["validation_integrity_status"] = "verified_internal_cv5"
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
                "command": (
                    "uv run pytest tests/test_simulator.py tests/test_ds003059.py "
                    "tests/test_perturbation.py tests/test_web_security.py "
                    "tests/test_dashboard_redesign_contract.py -q -o addopts="
                ),
            },
            {"label": "coverage gate", "status": "package surface gate", "command": "uv run pytest -q"},
        ],
    }
