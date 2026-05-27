from __future__ import annotations

import json
import random
import re
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

SUBJECT_SPLIT_SCHEMA_VERSION = 1
SUBJECT_ID_RE = re.compile(r"^sub-[a-z0-9][a-z0-9_.-]{0,63}$")
DEFAULT_CANDIDATE_VALIDATION_FRACTION = 0.2
DEFAULT_CANDIDATE_SPLIT_SEED = 20260510
DEFAULT_CV5_SPLIT_SEED = 20260510
CV5_SPLIT_SET_ID = "thesis_subject_disjoint_cv5_v1_candidate"
CV5_SPLIT_STRATEGY = "subject_disjoint_cv5"
CV5_FOLD_SPLIT_STRATEGY = "subject_disjoint_cv5_fold"
SUBJECT_SPLIT_STRATEGIES = frozenset({"subject_disjoint", CV5_FOLD_SPLIT_STRATEGY})
ApprovalStatus = Literal["candidate", "approved"]


class SubjectSplit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    split_id: str
    strategy: str
    selection_subjects: tuple[str, ...]
    validation_subjects: tuple[str, ...]
    split_seed: int | None = None
    notes: str | None = None
    created_by: str | None = None
    created_at: str | None = None
    dataset_id: str | None = None
    dataset_version: str | None = None
    approval_status: ApprovalStatus = "candidate"
    approved_by: str | None = None
    approved_at: str | None = None
    approval_rationale: str | None = None
    source_candidate_manifest: str | None = None
    source_candidate_split: str | None = None
    validation_claim_scope: str | None = None
    policy_notes: str | None = None
    holdout_policy: dict[str, Any] | None = None
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: int) -> int:
        if int(value) != SUBJECT_SPLIT_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {SUBJECT_SPLIT_SCHEMA_VERSION}; got {value}."
            )
        return int(value)

    @field_validator("split_id", "strategy")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        clean = str(value).strip()
        if not clean:
            raise ValueError("field must not be empty.")
        return clean

    @field_validator("selection_subjects", "validation_subjects", mode="before")
    @classmethod
    def _validate_subject_role(cls, value: object, info: Any) -> tuple[str, ...]:
        if not isinstance(value, list | tuple):
            raise ValueError(f"{info.field_name} must be a non-empty array of subject IDs.")
        subjects = tuple(normalize_subject_id(item) for item in value)
        if not subjects:
            raise ValueError(f"{info.field_name} must not be empty.")
        duplicates = sorted({subject for subject in subjects if subjects.count(subject) > 1})
        if duplicates:
            raise ValueError(
                f"{info.field_name} contains duplicate subject IDs: {', '.join(duplicates)}."
            )
        return subjects

    @field_validator("warnings", "limitations", mode="before")
    @classmethod
    def _coerce_text_tuple(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            return (value.strip(),) if value.strip() else ()
        if not isinstance(value, list | tuple):
            raise ValueError("warnings and limitations must be arrays of strings.")
        return tuple(str(item).strip() for item in value if str(item).strip())

    @field_validator("split_seed")
    @classmethod
    def _validate_seed(cls, value: int | None) -> int | None:
        if value is None:
            return None
        seed = int(value)
        if seed < 0:
            raise ValueError("split_seed must be non-negative when provided.")
        return seed

    @model_validator(mode="after")
    def _validate_disjoint_subjects(self) -> Self:
        if self.strategy not in SUBJECT_SPLIT_STRATEGIES:
            allowed = ", ".join(sorted(SUBJECT_SPLIT_STRATEGIES))
            raise ValueError(f"strategy must be one of: {allowed}.")
        overlap = sorted(set(self.selection_subjects).intersection(self.validation_subjects))
        if overlap:
            raise ValueError(
                "selection_subjects and validation_subjects must be subject-disjoint; "
                f"overlap detected: {', '.join(overlap)}."
            )
        if self.approval_status == "approved" and (
            not str(self.approved_by or "").strip() or not str(self.approved_at or "").strip()
        ):
            raise ValueError("approved subject splits must include approved_by and approved_at.")
        if self.approval_status == "candidate" and (
            str(self.approved_by or "").strip() or str(self.approved_at or "").strip()
        ):
            raise ValueError("candidate subject splits must not include approved_by or approved_at.")
        return self

    @property
    def is_approved(self) -> bool:
        return self.approval_status == "approved"


def normalize_subject_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("subject IDs must be strings.")
    subject = value.strip().lower()
    if not subject:
        raise ValueError("subject IDs must not be empty.")
    if not SUBJECT_ID_RE.fullmatch(subject):
        raise ValueError(f"invalid subject ID: {value!r}. Expected a BIDS-style 'sub-*' identifier.")
    return subject


def resolve_subject_split_path(path: str | Path, *, repo_root: Path) -> Path:
    raw_path = Path(path)
    if not str(raw_path).strip():
        raise ValueError("Subject split path must not be empty.")
    resolved_root = repo_root.resolve()
    resolved_path = raw_path.resolve() if raw_path.is_absolute() else (resolved_root / raw_path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("Subject split path must resolve inside the repository.") from exc
    if resolved_path.suffix.lower() != ".json":
        raise ValueError("Subject split path must be a JSON file.")
    return resolved_path


def load_subject_split_file(path: str | Path, *, repo_root: Path | None = None) -> SubjectSplit:
    resolved_path = (
        resolve_subject_split_path(path, repo_root=repo_root)
        if repo_root is not None
        else Path(path).expanduser().resolve()
    )
    raw = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Subject split file must contain a JSON object: {resolved_path}.")
    return SubjectSplit.model_validate(raw)


def validate_subject_split_against_available_subjects(
    split: SubjectSplit,
    available_subjects: tuple[str, ...] | list[str] | set[str],
) -> None:
    available = {normalize_subject_id(subject) for subject in available_subjects}
    requested = set(split.selection_subjects).union(split.validation_subjects)
    missing = sorted(requested.difference(available))
    if missing:
        raise ValueError(
            "Subject split references subject IDs that are not available in the manifest/provenance: "
            f"{', '.join(missing)}."
        )


def create_candidate_subject_split(
    available_subjects: Sequence[str],
    *,
    split_id: str,
    seed: int = DEFAULT_CANDIDATE_SPLIT_SEED,
    validation_fraction: float = DEFAULT_CANDIDATE_VALIDATION_FRACTION,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    created_by: str | None = None,
    source_label: str | None = None,
    qc_filter: str | None = None,
    warnings: Sequence[str] = (),
    limitations: Sequence[str] = (),
) -> SubjectSplit:
    subjects = tuple(sorted({normalize_subject_id(subject) for subject in available_subjects}))
    if len(subjects) < 2:
        raise ValueError("At least two available subjects are required to create a subject-disjoint split.")
    if not 0.0 < float(validation_fraction) < 1.0:
        raise ValueError("validation_fraction must be greater than 0 and less than 1.")

    validation_count = int(round(len(subjects) * float(validation_fraction)))
    validation_count = max(1, min(validation_count, len(subjects) - 1))
    shuffled = list(subjects)
    random.Random(int(seed)).shuffle(shuffled)
    validation_subjects = tuple(sorted(shuffled[:validation_count]))
    validation_set = set(validation_subjects)
    selection_subjects = tuple(subject for subject in subjects if subject not in validation_set)
    if not selection_subjects or not validation_subjects:
        raise ValueError("Candidate split generation produced an empty selection or validation role.")

    default_limitations = (
        "Candidate split is not approved thesis evidence until human scientific review records approval.",
        "The candidate uses cached subject/run completeness only; no motion, FD/DVARS, confound-regression, or censoring strata are available in the repo.",
        "Stage 3 does not yet run a real subject-held-out empirical evaluation.",
    )
    return SubjectSplit(
        schema_version=SUBJECT_SPLIT_SCHEMA_VERSION,
        split_id=split_id,
        strategy="subject_disjoint",
        selection_subjects=selection_subjects,
        validation_subjects=validation_subjects,
        split_seed=int(seed),
        notes=(
            "Deterministic candidate split generated from cached complete paired subjects. "
            "It must be reviewed and explicitly approved before use as thesis evidence."
        ),
        created_by=created_by,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        approval_status="candidate",
        policy_notes=(
            "Default candidate policy: fixed subject-disjoint holdout with deterministic seeded assignment. "
            "Holdout size and final subject IDs remain human scientific decisions."
        ),
        holdout_policy={
            "policy": "fixed_subject_disjoint_holdout_candidate",
            "source": source_label,
            "qc_filter": qc_filter,
            "subject_ordering": "normalize BIDS subject IDs, sort lexicographically, shuffle with split_seed, then sort each role list",
            "validation_fraction": float(validation_fraction),
            "validation_subject_count": len(validation_subjects),
            "selection_subject_count": len(selection_subjects),
            "split_seed": int(seed),
        },
        warnings=tuple(warnings),
        limitations=tuple(default_limitations) + tuple(str(item) for item in limitations if str(item).strip()),
    )


def create_cv5_subject_split_package(
    available_subjects: Sequence[str],
    *,
    split_set_id: str = CV5_SPLIT_SET_ID,
    seed: int = DEFAULT_CV5_SPLIT_SEED,
    number_of_folds: int = 5,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    created_by: str | None = None,
    created_at: str | None = None,
    source_label: str | None = None,
    qc_filter: str | None = None,
    fold_file_paths: Sequence[str] | None = None,
    warnings: Sequence[str] = (),
    limitations: Sequence[str] = (),
) -> tuple[tuple[SubjectSplit, ...], dict[str, Any]]:
    subjects = tuple(sorted({normalize_subject_id(subject) for subject in available_subjects}))
    if number_of_folds <= 1:
        raise ValueError("number_of_folds must be greater than 1.")
    if len(subjects) < number_of_folds:
        raise ValueError("At least one validation subject per fold is required.")
    if len(subjects) % number_of_folds != 0:
        raise ValueError("Subject count must be evenly divisible by number_of_folds.")

    validation_subjects_per_fold = len(subjects) // number_of_folds
    if validation_subjects_per_fold <= 0:
        raise ValueError("CV5 generation produced an empty validation fold.")

    expected_paths = tuple(
        fold_file_paths
        if fold_file_paths is not None
        else (
            f"subject_split_fold_{fold_index:02d}_candidate.json"
            for fold_index in range(1, number_of_folds + 1)
        )
    )
    if len(expected_paths) != number_of_folds:
        raise ValueError("fold_file_paths must include exactly one path per fold.")

    shuffled = list(subjects)
    random.Random(int(seed)).shuffle(shuffled)
    default_limitations = (
        "Candidate CV5 split set is not approved thesis evidence until human scientific review records approval.",
        "Small n=15 subject universe with n=3 held out per fold limits precision and interpretability.",
        "Cached QC does not include subject-level motion, FD/DVARS, confound-regression, or censoring strata.",
        "This is internal subject-disjoint validation, not external cohort validation.",
    )
    policy_notes = (
        "Candidate five-fold subject-disjoint internal validation policy: deterministic seeded assignment over "
        "cached complete paired subjects, with every subject held out exactly once across folds. Human approval "
        "is required before thesis-evidence Stage 2/3 runs."
    )

    folds: list[SubjectSplit] = []
    validation_counts: Counter[str] = Counter()
    for fold_number in range(1, number_of_folds + 1):
        start = (fold_number - 1) * validation_subjects_per_fold
        stop = start + validation_subjects_per_fold
        validation_subjects = tuple(sorted(shuffled[start:stop]))
        validation_set = set(validation_subjects)
        selection_subjects = tuple(subject for subject in subjects if subject not in validation_set)
        validation_counts.update(validation_subjects)
        folds.append(
            SubjectSplit(
                schema_version=SUBJECT_SPLIT_SCHEMA_VERSION,
                split_id=f"{split_set_id}_fold_{fold_number:02d}",
                strategy=CV5_FOLD_SPLIT_STRATEGY,
                selection_subjects=selection_subjects,
                validation_subjects=validation_subjects,
                split_seed=int(seed),
                notes=(
                    "Deterministic candidate CV5 fold generated from cached complete paired subjects. "
                    "It must be reviewed and explicitly approved before use as thesis evidence."
                ),
                created_by=created_by,
                created_at=created_at,
                dataset_id=dataset_id,
                dataset_version=dataset_version,
                approval_status="candidate",
                policy_notes=policy_notes,
                holdout_policy={
                    "policy": CV5_SPLIT_STRATEGY,
                    "split_set_id": split_set_id,
                    "fold_index": fold_number,
                    "number_of_folds": number_of_folds,
                    "source": source_label,
                    "qc_filter": qc_filter,
                    "subject_ordering": (
                        "normalize BIDS subject IDs, sort lexicographically, shuffle with split_seed, "
                        "chunk into folds, then sort selection and validation role lists"
                    ),
                    "validation_subject_count": len(validation_subjects),
                    "selection_subject_count": len(selection_subjects),
                    "split_seed": int(seed),
                },
                warnings=tuple(warnings),
                limitations=tuple(default_limitations)
                + tuple(str(item) for item in limitations if str(item).strip()),
            )
        )

    missing = sorted(subject for subject in subjects if validation_counts[subject] != 1)
    repeated = sorted(subject for subject, count in validation_counts.items() if count > 1)
    manifest = {
        "schema_version": SUBJECT_SPLIT_SCHEMA_VERSION,
        "split_set_id": split_set_id,
        "strategy": CV5_SPLIT_STRATEGY,
        "approval_status": "candidate",
        "split_seed": int(seed),
        "created_by": created_by,
        "created_at": created_at,
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "source": source_label,
        "qc_filter": qc_filter,
        "number_of_subjects": len(subjects),
        "number_of_folds": number_of_folds,
        "selection_subjects_per_fold": len(subjects) - validation_subjects_per_fold,
        "validation_subjects_per_fold": validation_subjects_per_fold,
        "subjects": list(subjects),
        "fold_file_paths": list(expected_paths),
        "held_out_validation_configured": True,
        "held_out_validation_completed": False,
        "validation_coverage_summary": {
            "held_out_counts": dict(sorted(validation_counts.items())),
            "subjects_held_out_once_count": sum(1 for subject in subjects if validation_counts[subject] == 1),
            "subjects_missing_from_validation": missing,
            "subjects_repeated_in_validation": repeated,
            "every_subject_held_out_exactly_once": not missing and not repeated,
        },
        "policy_notes": policy_notes,
        "warnings": [str(item) for item in warnings if str(item).strip()],
        "limitations": list(default_limitations)
        + [str(item) for item in limitations if str(item).strip()],
    }
    return tuple(folds), {key: value for key, value in manifest.items() if value is not None}


def _resolve_manifest_relative_path(
    path: str | Path,
    *,
    manifest_path: Path,
    repo_root: Path | None,
) -> Path:
    raw_path = Path(path)
    if raw_path.is_absolute():
        resolved = raw_path.resolve()
    elif repo_root is not None and (repo_root / raw_path).exists():
        resolved = (repo_root / raw_path).resolve()
    else:
        resolved = (manifest_path.parent / raw_path).resolve()
    if repo_root is not None:
        try:
            resolved.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError("CV5 fold file path must resolve inside the repository.") from exc
    return resolved


def validate_cv5_subject_split_manifest(
    manifest_file: str | Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    manifest_path = (
        resolve_subject_split_path(manifest_file, repo_root=repo_root)
        if repo_root is not None
        else Path(manifest_file).expanduser().resolve()
    )
    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw_manifest, dict):
        raise ValueError(f"CV5 manifest must contain a JSON object: {manifest_path}.")

    if int(raw_manifest.get("schema_version", -1)) != SUBJECT_SPLIT_SCHEMA_VERSION:
        raise ValueError(f"CV5 manifest schema_version must be {SUBJECT_SPLIT_SCHEMA_VERSION}.")
    if raw_manifest.get("strategy") != CV5_SPLIT_STRATEGY:
        raise ValueError(f"CV5 manifest strategy must be {CV5_SPLIT_STRATEGY!r}.")
    approval_status = str(raw_manifest.get("approval_status") or "")
    if approval_status not in {"candidate", "approved"}:
        raise ValueError("CV5 manifest approval_status must be 'candidate' or 'approved'.")
    if approval_status == "candidate" and (
        str(raw_manifest.get("approved_by") or "").strip()
        or str(raw_manifest.get("approved_at") or "").strip()
    ):
        raise ValueError("Candidate CV5 manifests must not include approved_by or approved_at.")
    if approval_status == "approved" and (
        not str(raw_manifest.get("approved_by") or "").strip()
        or not str(raw_manifest.get("approved_at") or "").strip()
    ):
        raise ValueError("Approved CV5 manifests must include approved_by and approved_at.")
    if raw_manifest.get("held_out_validation_completed") is not False:
        raise ValueError("CV5 split manifests must not mark held_out_validation_completed true.")

    number_of_folds = int(raw_manifest.get("number_of_folds", 0))
    number_of_subjects = int(raw_manifest.get("number_of_subjects", 0))
    selection_per_fold = int(raw_manifest.get("selection_subjects_per_fold", 0))
    validation_per_fold = int(raw_manifest.get("validation_subjects_per_fold", 0))
    if number_of_folds <= 1:
        raise ValueError("CV5 manifest number_of_folds must be greater than 1.")
    subjects_payload = raw_manifest.get("subjects")
    if not isinstance(subjects_payload, list) or not subjects_payload:
        raise ValueError("CV5 manifest must include a non-empty subjects list.")
    subjects = tuple(sorted({normalize_subject_id(subject) for subject in subjects_payload}))
    if len(subjects) != number_of_subjects:
        raise ValueError("CV5 manifest number_of_subjects does not match the unique subjects list.")
    if selection_per_fold + validation_per_fold != number_of_subjects:
        raise ValueError("CV5 manifest per-fold role counts do not sum to number_of_subjects.")

    fold_file_paths = raw_manifest.get("fold_file_paths")
    if not isinstance(fold_file_paths, list) or len(fold_file_paths) != number_of_folds:
        raise ValueError("CV5 manifest fold_file_paths must include exactly one path per fold.")

    fold_summaries: list[dict[str, Any]] = []
    validation_counts: Counter[str] = Counter()
    for fold_index, fold_file_path in enumerate(fold_file_paths, start=1):
        resolved_fold_path = _resolve_manifest_relative_path(
            str(fold_file_path),
            manifest_path=manifest_path,
            repo_root=repo_root,
        )
        split = load_subject_split_file(resolved_fold_path, repo_root=None)
        if split.strategy != CV5_FOLD_SPLIT_STRATEGY:
            raise ValueError(f"CV5 fold {fold_index} strategy must be {CV5_FOLD_SPLIT_STRATEGY!r}.")
        if split.approval_status != approval_status:
            raise ValueError(
                f"CV5 fold {fold_index} approval_status must match the manifest approval_status."
            )
        if split.split_seed != raw_manifest.get("split_seed"):
            raise ValueError(f"CV5 fold {fold_index} split_seed does not match the manifest.")
        fold_subjects = set(split.selection_subjects).union(split.validation_subjects)
        if fold_subjects != set(subjects):
            raise ValueError(f"CV5 fold {fold_index} does not cover exactly the manifest subject universe.")
        if len(split.selection_subjects) != selection_per_fold:
            raise ValueError(f"CV5 fold {fold_index} selection subject count does not match the manifest.")
        if len(split.validation_subjects) != validation_per_fold:
            raise ValueError(f"CV5 fold {fold_index} validation subject count does not match the manifest.")
        overlap = sorted(set(split.selection_subjects).intersection(split.validation_subjects))
        if overlap:
            raise ValueError(f"CV5 fold {fold_index} has selection/validation overlap: {', '.join(overlap)}.")
        validation_counts.update(split.validation_subjects)
        fold_summaries.append(
            {
                "fold_index": fold_index,
                "split_id": split.split_id,
                "file_path": str(fold_file_path),
                "selection_subject_count": len(split.selection_subjects),
                "validation_subject_count": len(split.validation_subjects),
                "overlap_count": len(overlap),
                "approval_status": split.approval_status,
            }
        )

    missing = sorted(subject for subject in subjects if validation_counts[subject] != 1)
    repeated = sorted(subject for subject, count in validation_counts.items() if count > 1)
    if missing or repeated:
        details = []
        if missing:
            details.append(f"missing held-out coverage: {', '.join(missing)}")
        if repeated:
            details.append(f"repeated held-out coverage: {', '.join(repeated)}")
        raise ValueError("CV5 validation coverage must hold out every subject exactly once; " + "; ".join(details))

    return {
        "split_set_id": raw_manifest.get("split_set_id"),
        "strategy": raw_manifest.get("strategy"),
        "approval_status": approval_status,
        "approved_by": raw_manifest.get("approved_by"),
        "approved_at": raw_manifest.get("approved_at"),
        "validation_claim_scope": raw_manifest.get("validation_claim_scope"),
        "split_seed": raw_manifest.get("split_seed"),
        "number_of_subjects": number_of_subjects,
        "number_of_folds": number_of_folds,
        "selection_subjects_per_fold": selection_per_fold,
        "validation_subjects_per_fold": validation_per_fold,
        "held_out_validation_configured": bool(raw_manifest.get("held_out_validation_configured")),
        "held_out_validation_completed": bool(raw_manifest.get("held_out_validation_completed")),
        "validation_coverage_summary": {
            "held_out_counts": dict(sorted(validation_counts.items())),
            "every_subject_held_out_exactly_once": True,
        },
        "fold_summaries": fold_summaries,
        "limitations": raw_manifest.get("limitations", []),
    }


def subject_split_json_payload(split: SubjectSplit) -> dict[str, Any]:
    return split.model_dump(mode="json", exclude_none=True)


def build_no_subject_validation_boundary(
    *,
    selection_data_source: str | None,
    selection_subject_count: int | None,
    selection_random_seed: int | None = None,
) -> dict[str, Any]:
    return {
        "held_out": False,
        "held_out_validation_configured": False,
        "held_out_validation_completed": False,
        "boundary_type": "not_configured",
        "split_file_path": None,
        "split_schema_version": None,
        "split_id": None,
        "split_strategy": "none_all_available_targets_used_for_selection",
        "split_seed": None,
        "approval_status": "none",
        "approved_by": None,
        "approved_at": None,
        "policy_notes": None,
        "holdout_policy": None,
        "selection_data_source": selection_data_source,
        "validation_data_source": None,
        "selection_subjects": [],
        "validation_subjects": [],
        "selection_subject_count": selection_subject_count,
        "validation_subject_count": 0,
        "overlap_count": 0,
        "selection_random_seed": selection_random_seed,
        "claim_guardrail": (
            "No subject-disjoint held-out empirical validation is configured for Stage 2/3; "
            "current outputs report calibration and stochastic diagnostics, not independent validation."
        ),
        "warnings": [],
        "limitations": [
            "Absence of a split file must not be interpreted as evidence of held-out validation.",
            "Seed-disjoint stochastic diagnostics are not subject-disjoint empirical validation.",
        ],
    }


def build_subject_validation_boundary(
    split: SubjectSplit,
    *,
    split_file_path: str | Path | None = None,
    held_out_validation_completed: bool = False,
    selection_data_source: str | None = "Stage 2 calibration subject subset",
    validation_data_source: str | None = "Held-out validation subject subset",
    selection_random_seed: int | None = None,
) -> dict[str, Any]:
    overlap = sorted(set(split.selection_subjects).intersection(split.validation_subjects))
    overlap_count = len(overlap)
    if held_out_validation_completed and (overlap_count or not split.validation_subjects):
        raise ValueError("Cannot mark held-out validation completed with overlap or empty validation subjects.")
    if held_out_validation_completed and not split.is_approved:
        raise ValueError("Cannot mark held-out validation completed for a candidate or unapproved split.")
    status = "completed" if held_out_validation_completed else "configured_not_completed"
    limitations = [
        *split.limitations,
        "A configured split is only a boundary scaffold until Stage 2 calibration and Stage 3 validation are rerun on disjoint subject targets.",
    ]
    if split.approval_status == "candidate":
        limitations.append("Candidate split status means the split has not been approved as thesis evidence.")
    if held_out_validation_completed:
        claim_guardrail = "Subject-disjoint held-out validation has been completed and recorded."
    elif split.approval_status == "approved":
        claim_guardrail = "Approved subject-disjoint split is configured, but held-out validation has not yet been completed."
    else:
        claim_guardrail = (
            "Candidate subject-disjoint split is configured, but it is not approved and held-out validation has not yet been completed."
        )
    return {
        "held_out": bool(held_out_validation_completed),
        "held_out_validation_configured": True,
        "held_out_validation_completed": bool(held_out_validation_completed),
        "boundary_type": f"subject_disjoint_{split.approval_status}_{status}",
        "split_file_path": str(split_file_path) if split_file_path is not None else None,
        "split_schema_version": split.schema_version,
        "split_id": split.split_id,
        "split_strategy": split.strategy,
        "split_seed": split.split_seed,
        "approval_status": split.approval_status,
        "approved_by": split.approved_by,
        "approved_at": split.approved_at,
        "policy_notes": split.policy_notes,
        "holdout_policy": split.holdout_policy,
        "selection_data_source": selection_data_source,
        "validation_data_source": validation_data_source,
        "selection_subjects": list(split.selection_subjects),
        "validation_subjects": list(split.validation_subjects),
        "selection_subject_count": len(split.selection_subjects),
        "validation_subject_count": len(split.validation_subjects),
        "overlap_count": overlap_count,
        "selection_random_seed": selection_random_seed,
        "claim_guardrail": claim_guardrail,
        "warnings": list(split.warnings),
        "limitations": limitations,
    }


def format_subject_split_summary(
    split: SubjectSplit,
    *,
    held_out_validation_completed: bool = False,
    next_command: str | None = None,
) -> str:
    boundary = build_subject_validation_boundary(
        split,
        held_out_validation_completed=held_out_validation_completed,
    )
    lines = [
        "Subject split valid",
        f"Split ID: {split.split_id}",
        f"Approval status: {split.approval_status}",
        f"Strategy: {split.strategy}",
        f"Schema version: {split.schema_version}",
        f"Split seed: {split.split_seed if split.split_seed is not None else 'not recorded'}",
        f"Selection subjects: {boundary['selection_subject_count']}",
        f"Held-out validation subjects: {boundary['validation_subject_count']}",
        "Held-out validation configured: yes",
        f"Held-out validation completed: {'yes' if held_out_validation_completed else 'no'}",
        f"Overlap count: {boundary['overlap_count']}",
        "Duplicate count: 0",
        f"Boundary type: {boundary['boundary_type']}",
        f"Claim guardrail: {boundary['claim_guardrail']}",
    ]
    if split.policy_notes:
        lines.append(f"Policy notes: {split.policy_notes}")
    if split.limitations:
        lines.append("Limitations:")
        lines.extend(f"- {item}" for item in split.limitations)
    if next_command:
        lines.append(f"Next command: {next_command}")
    return "\n".join(lines)


def format_cv5_subject_split_summary(summary: dict[str, Any]) -> str:
    lines = [
        "CV5 subject split package valid",
        f"Split set ID: {summary['split_set_id']}",
        f"Approval status: {summary['approval_status']}",
        f"Strategy: {summary['strategy']}",
        f"Split seed: {summary['split_seed']}",
        f"Subjects: {summary['number_of_subjects']}",
        f"Folds: {summary['number_of_folds']}",
        f"Selection subjects per fold: {summary['selection_subjects_per_fold']}",
        f"Held-out validation subjects per fold: {summary['validation_subjects_per_fold']}",
        f"Held-out validation configured: {'yes' if summary['held_out_validation_configured'] else 'no'}",
        f"Held-out validation completed: {'yes' if summary['held_out_validation_completed'] else 'no'}",
        "Every subject held out exactly once: yes",
        "Fold summaries:",
    ]
    if summary.get("approved_by"):
        lines.insert(3, f"Approved by: {summary['approved_by']}")
    if summary.get("approved_at"):
        lines.insert(4, f"Approved at: {summary['approved_at']}")
    if summary.get("validation_claim_scope"):
        lines.insert(5, f"Validation claim scope: {summary['validation_claim_scope']}")
    for fold in summary["fold_summaries"]:
        lines.append(
            "- fold "
            f"{int(fold['fold_index']):02d}: "
            f"selection={fold['selection_subject_count']} "
            f"validation={fold['validation_subject_count']} "
            f"overlap={fold['overlap_count']} "
            f"approval_status={fold['approval_status']} "
            f"path={fold['file_path']}"
        )
    if summary.get("limitations"):
        lines.append("Limitations:")
        lines.extend(f"- {item}" for item in summary["limitations"])
    return "\n".join(lines)
