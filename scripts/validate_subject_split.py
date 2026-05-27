from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

CANDIDATE_SPLIT_ID = "thesis_subject_disjoint_v1_candidate"
CV5_SPLIT_SET_ID = "thesis_subject_disjoint_cv5_v1_candidate"
CV5_OUTPUT_MANIFEST = "subject_split_cv5_manifest_candidate.json"
CV5_APPROVED_MANIFEST = "subject_split_cv5_manifest_approved.json"
CV5_APPROVAL_RATIONALE = (
    "Approved as the thesis five-fold subject-disjoint internal validation design. "
    "This is internal validation, not external or clinical validation."
)
CV5_APPROVED_POLICY_NOTES = (
    "Approved five-fold subject-disjoint internal validation policy: deterministic seeded assignment over "
    "cached complete paired subjects, with every subject held out exactly once across folds. "
    "Claims remain limited to internal validation and must retain the recorded limitations."
)
CV5_VALIDATION_CLAIM_SCOPE = "preliminary_internal_subject_disjoint_cv5"
CV5_APPROVAL_LIMITATIONS = (
    "n=15 complete paired subjects",
    "n=3 held-out subjects per fold",
    "No subject-level motion/FD/DVARS/confound/censoring stratification available",
    "Internal validation only; not external validation",
    "Interpret cautiously",
)


def _load_json_object(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return raw


def _candidate_subjects_from_cached_qc(repo_root: Path) -> tuple[tuple[str, ...], str, tuple[str, ...], tuple[str, ...]]:
    quality_path = repo_root / "results" / "stage_2" / "empirical_data_quality.json"
    if not quality_path.exists():
        raise ValueError(
            "Cannot generate a candidate split because results/stage_2/empirical_data_quality.json is missing. "
            "Run Stage 2 target extraction first or create an approved split manually from reviewed subject/QC metadata."
        )
    quality = _load_json_object(quality_path)
    subjects = quality.get("complete_subjects") or quality.get("paired_subjects")
    if not isinstance(subjects, list) or not subjects:
        raise ValueError(
            "Cannot generate a candidate split because empirical_data_quality.json does not contain complete or paired subjects."
        )
    warnings: list[str] = []
    limitations = [
        "Candidate generation used cached complete paired subjects from empirical_data_quality.json.",
        "Cached QC does not include subject-level motion, FD/DVARS, confound-regression, or censoring strata.",
    ]
    complete_count = quality.get("complete_subject_count")
    subject_count = quality.get("subject_count")
    if complete_count is not None and subject_count is not None and int(complete_count) < int(subject_count):
        warnings.append("Some cached subjects were not complete and were excluded from the candidate split universe.")
    return (
        tuple(str(subject) for subject in subjects),
        str(quality_path.relative_to(repo_root)),
        tuple(warnings),
        tuple(limitations),
    )


def _stage_commands(split_path: Path, repo_root: Path) -> str:
    relative_path = split_path.relative_to(repo_root) if split_path.is_relative_to(repo_root) else split_path
    return (
        "after human approval, run "
        f"uv run python scripts/run_pipeline.py stage2 --subject-split {relative_path} "
        "and then "
        f"uv run python scripts/run_pipeline.py stage3 --subject-split {relative_path}"
    )


def _resolve_output_dir(path: Path, *, repo_root: Path) -> Path:
    resolved_root = repo_root.resolve()
    raw_path = Path(path)
    resolved_path = raw_path.resolve() if raw_path.is_absolute() else (resolved_root / raw_path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("CV5 output directory must resolve inside the repository.") from exc
    return resolved_path


def _write_json_if_unchanged(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        existing = _load_json_object(path)
        if existing != payload:
            if (
                existing.get("created_by")
                == payload.get("created_by")
                == "scripts/validate_subject_split.py --approve-cv5"
            ):
                path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                return
            raise ValueError(
                f"Refusing to overwrite existing JSON with different content: {path}. "
                "Review or move the existing file first."
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_candidate_split(
    output_path: Path,
    *,
    split_id: str,
    seed: int,
    validation_fraction: float,
    repo_root: Path,
) -> str:
    from lsd_thesis.data.ds003059 import DS003059_DATASET_ID, DS003059_VERSION
    from lsd_thesis.subject_split import (
        create_candidate_subject_split,
        format_subject_split_summary,
        load_subject_split_file,
        resolve_subject_split_path,
        subject_split_json_payload,
        validate_subject_split_against_available_subjects,
    )

    resolved_output = resolve_subject_split_path(output_path, repo_root=repo_root)
    available_subjects, source_label, warnings, limitations = _candidate_subjects_from_cached_qc(repo_root)
    split = create_candidate_subject_split(
        available_subjects,
        split_id=split_id,
        seed=seed,
        validation_fraction=validation_fraction,
        dataset_id=DS003059_DATASET_ID,
        dataset_version=DS003059_VERSION,
        created_by="scripts/validate_subject_split.py --generate-candidate",
        source_label=source_label,
        qc_filter="complete_subjects from cached empirical_data_quality.json",
        warnings=warnings,
        limitations=limitations,
    )
    validate_subject_split_against_available_subjects(split, available_subjects)
    payload = subject_split_json_payload(split)
    if resolved_output.exists():
        existing = _load_json_object(resolved_output)
        if existing != payload:
            raise ValueError(
                f"Refusing to overwrite existing split file with different content: {resolved_output}. "
                "Review or move the existing file first."
            )
    else:
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        resolved_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    loaded = load_subject_split_file(resolved_output, repo_root=repo_root)
    validate_subject_split_against_available_subjects(loaded, available_subjects)
    relative_output = resolved_output.relative_to(repo_root)
    return "\n".join(
        [
            f"Candidate subject split written: {relative_output}",
            format_subject_split_summary(
                loaded,
                held_out_validation_completed=False,
                next_command=_stage_commands(resolved_output, repo_root),
            ),
        ]
    )


def _write_cv5_subject_split_package(
    output_dir: Path,
    *,
    split_set_id: str,
    seed: int,
    repo_root: Path,
) -> str:
    from lsd_thesis.data.ds003059 import DS003059_DATASET_ID, DS003059_VERSION
    from lsd_thesis.subject_split import (
        create_cv5_subject_split_package,
        format_cv5_subject_split_summary,
        subject_split_json_payload,
        validate_cv5_subject_split_manifest,
        validate_subject_split_against_available_subjects,
    )

    resolved_output_dir = _resolve_output_dir(output_dir, repo_root=repo_root)
    available_subjects, source_label, warnings, limitations = _candidate_subjects_from_cached_qc(repo_root)
    fold_paths = [
        (resolved_output_dir / f"subject_split_fold_{fold_index:02d}_candidate.json")
        .relative_to(repo_root)
        .as_posix()
        for fold_index in range(1, 6)
    ]
    folds, manifest = create_cv5_subject_split_package(
        available_subjects,
        split_set_id=split_set_id,
        seed=seed,
        number_of_folds=5,
        dataset_id=DS003059_DATASET_ID,
        dataset_version=DS003059_VERSION,
        created_by="scripts/validate_subject_split.py --generate-cv5",
        created_at="2026-05-10T00:00:00Z",
        source_label=source_label,
        qc_filter="complete_subjects from cached empirical_data_quality.json",
        fold_file_paths=fold_paths,
        warnings=warnings,
        limitations=limitations,
    )
    for split in folds:
        validate_subject_split_against_available_subjects(split, available_subjects)

    for split, relative_path in zip(folds, fold_paths, strict=True):
        _write_json_if_unchanged(repo_root / relative_path, subject_split_json_payload(split))
    manifest_path = resolved_output_dir / CV5_OUTPUT_MANIFEST
    _write_json_if_unchanged(manifest_path, manifest)

    summary = validate_cv5_subject_split_manifest(manifest_path, repo_root=repo_root)
    relative_manifest = manifest_path.relative_to(repo_root)
    return "\n".join(
        [
            f"CV5 candidate subject split package written: {relative_manifest}",
            format_cv5_subject_split_summary(summary),
        ]
    )


def _repo_relative_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _with_unique_limitations(existing: Any, additions: tuple[str, ...]) -> list[str]:
    output: list[str] = []
    for item in list(existing or []) + list(additions):
        text = str(item).strip()
        if text and text not in output:
            output.append(text)
    return output


def _approved_limitations(existing: Any) -> list[str]:
    retained = [
        str(item).strip()
        for item in list(existing or [])
        if str(item).strip()
        and "not approved thesis evidence" not in str(item)
        and "review records approval" not in str(item)
    ]
    return _with_unique_limitations(retained, CV5_APPROVAL_LIMITATIONS)


def _approved_split_set_id(candidate_split_set_id: str) -> str:
    if candidate_split_set_id.endswith("_candidate"):
        return candidate_split_set_id.removesuffix("_candidate") + "_approved"
    return candidate_split_set_id + "_approved"


def _approved_fold_split_id(candidate_split_id: str, approved_split_set_id: str, fold_index: int) -> str:
    if candidate_split_id.endswith(f"_fold_{fold_index:02d}"):
        return f"{approved_split_set_id}_fold_{fold_index:02d}"
    return candidate_split_id.replace("_candidate", "_approved")


def _approve_cv5_subject_split_package(
    candidate_manifest_path: Path,
    *,
    approved_output_dir: Path,
    approved_by: str,
    approved_at: str,
    repo_root: Path,
) -> str:
    from lsd_thesis.subject_split import (
        SubjectSplit,
        format_cv5_subject_split_summary,
        load_subject_split_file,
        subject_split_json_payload,
        validate_cv5_subject_split_manifest,
    )

    candidate_summary = validate_cv5_subject_split_manifest(candidate_manifest_path, repo_root=repo_root)
    if candidate_summary["approval_status"] != "candidate":
        raise ValueError("Only a candidate CV5 manifest can be approved by this helper.")
    if not str(approved_by).strip():
        raise ValueError("--approved-by must not be empty.")
    if not str(approved_at).strip():
        raise ValueError("--approved-at must not be empty.")

    candidate_manifest_resolved = (
        candidate_manifest_path.resolve()
        if candidate_manifest_path.is_absolute()
        else (repo_root / candidate_manifest_path).resolve()
    )
    candidate_manifest = _load_json_object(candidate_manifest_resolved)
    approved_dir = _resolve_output_dir(approved_output_dir, repo_root=repo_root)
    approved_dir.mkdir(parents=True, exist_ok=True)
    approved_split_set_id = _approved_split_set_id(str(candidate_manifest["split_set_id"]))
    source_candidate_manifest = _repo_relative_path(candidate_manifest_resolved, repo_root)

    approved_fold_paths: list[str] = []
    for fold_index, candidate_fold_path in enumerate(candidate_manifest["fold_file_paths"], start=1):
        candidate_fold_resolved = (repo_root / str(candidate_fold_path)).resolve()
        candidate_split = load_subject_split_file(candidate_fold_resolved)
        approved_fold_path = approved_dir / f"subject_split_fold_{fold_index:02d}_approved.json"
        approved_relative_path = _repo_relative_path(approved_fold_path, repo_root)
        payload = subject_split_json_payload(candidate_split)
        payload.update(
            {
                "split_id": _approved_fold_split_id(
                    candidate_split.split_id,
                    approved_split_set_id,
                    fold_index,
                ),
                "approval_status": "approved",
                "approved_by": approved_by,
                "approved_at": approved_at,
                "approval_rationale": CV5_APPROVAL_RATIONALE,
                "source_candidate_manifest": source_candidate_manifest,
                "source_candidate_split": str(candidate_fold_path),
                "validation_claim_scope": CV5_VALIDATION_CLAIM_SCOPE,
                "policy_notes": CV5_APPROVED_POLICY_NOTES,
                "created_by": "scripts/validate_subject_split.py --approve-cv5",
                "created_at": approved_at,
                "limitations": _approved_limitations(payload.get("limitations")),
            }
        )
        holdout_policy = dict(payload.get("holdout_policy") or {})
        holdout_policy["split_set_id"] = approved_split_set_id
        holdout_policy["source_candidate_manifest"] = source_candidate_manifest
        holdout_policy["source_candidate_split"] = str(candidate_fold_path)
        payload["holdout_policy"] = holdout_policy
        approved_split = SubjectSplit.model_validate(payload)
        _write_json_if_unchanged(approved_fold_path, subject_split_json_payload(approved_split))
        approved_fold_paths.append(approved_relative_path)

    approved_manifest = dict(candidate_manifest)
    approved_manifest.update(
        {
            "split_set_id": approved_split_set_id,
            "approval_status": "approved",
            "approved_by": approved_by,
            "approved_at": approved_at,
            "approval_rationale": CV5_APPROVAL_RATIONALE,
            "source_candidate_manifest": source_candidate_manifest,
            "validation_claim_scope": CV5_VALIDATION_CLAIM_SCOPE,
            "policy_notes": CV5_APPROVED_POLICY_NOTES,
            "created_by": "scripts/validate_subject_split.py --approve-cv5",
            "created_at": approved_at,
            "fold_file_paths": approved_fold_paths,
            "held_out_validation_configured": True,
            "held_out_validation_completed": False,
            "limitations": _approved_limitations(approved_manifest.get("limitations")),
        }
    )
    approved_manifest_path = approved_dir / CV5_APPROVED_MANIFEST
    _write_json_if_unchanged(approved_manifest_path, approved_manifest)
    approved_summary = validate_cv5_subject_split_manifest(approved_manifest_path, repo_root=repo_root)
    return "\n".join(
        [
            f"Approved CV5 subject split package written: {_repo_relative_path(approved_manifest_path, repo_root)}",
            format_cv5_subject_split_summary(approved_summary),
        ]
    )


def main() -> None:
    from lsd_thesis.subject_split import (
        format_cv5_subject_split_summary,
        format_subject_split_summary,
        load_subject_split_file,
        validate_cv5_subject_split_manifest,
    )

    parser = argparse.ArgumentParser(description="Validate a subject-disjoint Stage 2/3 split file.")
    parser.add_argument("split_file", nargs="?", help="Path to a JSON subject split file.")
    parser.add_argument(
        "--generate-candidate",
        type=Path,
        default=None,
        metavar="OUTPUT_JSON",
        help="Generate a deterministic candidate split from cached Stage 2 subject/QC metadata.",
    )
    parser.add_argument(
        "--generate-cv5",
        type=Path,
        default=None,
        metavar="OUTPUT_DIR",
        help="Generate a deterministic candidate five-fold subject-disjoint split package.",
    )
    parser.add_argument(
        "--validate-cv5",
        type=Path,
        default=None,
        metavar="MANIFEST_JSON",
        help="Validate a candidate five-fold subject-disjoint split package manifest.",
    )
    parser.add_argument(
        "--approve-cv5",
        type=Path,
        default=None,
        metavar="CANDIDATE_MANIFEST_JSON",
        help="Create approved CV5 split artifacts from a reviewed candidate manifest.",
    )
    parser.add_argument(
        "--approved-output-dir",
        type=Path,
        default=None,
        metavar="OUTPUT_DIR",
        help="Output directory for --approve-cv5 artifacts.",
    )
    parser.add_argument(
        "--approved-by",
        nargs="+",
        default=None,
        help="Reviewer name recorded on --approve-cv5 artifacts.",
    )
    parser.add_argument(
        "--approved-at",
        default=None,
        help="ISO timestamp recorded on --approve-cv5 artifacts; defaults to current UTC time.",
    )
    parser.add_argument("--split-id", default=CANDIDATE_SPLIT_ID, help="Split ID for --generate-candidate.")
    parser.add_argument("--split-set-id", default=CV5_SPLIT_SET_ID, help="Split set ID for --generate-cv5.")
    parser.add_argument(
        "--seed",
        type=int,
        default=20260510,
        help="Deterministic split seed for --generate-candidate or --generate-cv5.",
    )
    parser.add_argument(
        "--validation-fraction",
        type=float,
        default=0.2,
        help="Validation holdout fraction for --generate-candidate.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional repository root; when set, relative split paths must stay inside this directory.",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve() if args.repo_root is not None else REPO_ROOT

    requested_actions = sum(
        bool(action)
        for action in (
            args.generate_candidate,
            args.generate_cv5,
            args.validate_cv5,
            args.approve_cv5,
            args.split_file,
        )
    )
    if requested_actions != 1:
        parser.error(
            "Choose exactly one of split_file, --generate-candidate, --generate-cv5, "
            "--validate-cv5, or --approve-cv5."
        )

    if args.generate_candidate is not None:
        try:
            print(
                _write_candidate_split(
                    args.generate_candidate,
                    split_id=args.split_id,
                    seed=args.seed,
                    validation_fraction=args.validation_fraction,
                    repo_root=repo_root,
                )
            )
        except Exception as exc:
            print(f"Candidate subject split not generated: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        return

    if args.generate_cv5 is not None:
        try:
            print(
                _write_cv5_subject_split_package(
                    args.generate_cv5,
                    split_set_id=args.split_set_id,
                    seed=args.seed,
                    repo_root=repo_root,
                )
            )
        except Exception as exc:
            print(f"CV5 candidate subject split package not generated: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        return

    if args.validate_cv5 is not None:
        try:
            summary = validate_cv5_subject_split_manifest(args.validate_cv5, repo_root=repo_root)
        except Exception as exc:
            print(f"CV5 subject split package invalid: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        print(format_cv5_subject_split_summary(summary))
        return

    if args.approve_cv5 is not None:
        if args.approved_output_dir is None:
            parser.error("--approved-output-dir is required with --approve-cv5.")
        if args.approved_by is None:
            parser.error("--approved-by is required with --approve-cv5.")
        approved_by = " ".join(str(item) for item in args.approved_by).strip()
        approved_at = args.approved_at or datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        try:
            print(
                _approve_cv5_subject_split_package(
                    args.approve_cv5,
                    approved_output_dir=args.approved_output_dir,
                    approved_by=approved_by,
                    approved_at=approved_at,
                    repo_root=repo_root,
                )
            )
        except Exception as exc:
            print(f"Approved CV5 subject split package not generated: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        return

    try:
        split = load_subject_split_file(args.split_file, repo_root=args.repo_root)
    except Exception as exc:
        print(f"Subject split invalid: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(format_subject_split_summary(split, held_out_validation_completed=False))


if __name__ == "__main__":
    main()
