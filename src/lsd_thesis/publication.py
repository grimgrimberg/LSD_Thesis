from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class SubjectValidationEvidence:
    configured: bool = False
    completed: bool = False
    approval_status: str = "none"
    split_id: str | None = None
    split_strategy: str = "none_all_available_targets_used_for_selection"
    selection_subject_count: int | None = None
    validation_subject_count: int = 0
    overlap_count: int = 0
    split_file_path: str | None = None
    split_schema_version: int | None = None
    split_seed: int | None = None
    claim_guardrail: str = "No subject-disjoint held-out validation is configured."


@dataclass(slots=True)
class Stage2Evidence:
    initial_score: float
    best_score: float
    subject_count: int
    run_count: int
    dataset_anchor: str
    best_metrics: dict[str, float]
    multi_seed_mean: dict[str, float]
    multi_seed_std: dict[str, float]
    validation_boundary: SubjectValidationEvidence = field(default_factory=SubjectValidationEvidence)


@dataclass(slots=True)
class Stage3Evidence:
    best_mechanism: str
    best_strength: float
    best_score: float
    robust_best_mechanism: str | None = None
    robust_best_strength: float | None = None
    robust_best_score_mean: float | None = None
    robust_best_score_std: float | None = None


@dataclass(slots=True)
class Stage4Evidence:
    best_single_mechanism: str
    best_single_score: float
    best_pair_name: str
    best_pair_score: float


@dataclass(slots=True)
class PublicationEvidence:
    stage1: dict[str, Any]
    stage2: Stage2Evidence
    stage3: Stage3Evidence
    stage4: Stage4Evidence
    empirical_deltas: dict[str, float]
    literature_deltas: dict[str, float]
    condition_models: list[dict[str, Any]]
    multitask_models: list[dict[str, Any]]
    sign_mismatches: list[str]
    rocket_benchmark: dict[str, Any] | None = None
    cv5_validation: dict[str, Any] | None = None


def _read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(raw).__name__}.")
    return raw


def _read_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML mapping in {path}, got {type(raw).__name__}.")
    return raw


def _score(value: Any) -> float:
    return float(value)


def _best_of(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        raise ValueError("expected at least one scored entry")
    return min(entries, key=lambda item: float(item["score"]))


def _extract_stage4_scores(raw: dict[str, Any]) -> Stage4Evidence:
    if "best_single" in raw and "best_pair" in raw:
        best_single = raw["best_single"]
        best_pair = raw["best_pair"]
        if not isinstance(best_single, dict):
            raise ValueError(f"Expected 'best_single' in Stage 4 summary to be an object, got {type(best_single).__name__}.")
        if not isinstance(best_pair, dict):
            raise ValueError(f"Expected 'best_pair' in Stage 4 summary to be an object, got {type(best_pair).__name__}.")
        return Stage4Evidence(
            best_single_mechanism=str(
                best_single.get("mechanism") or best_single.get("label") or best_single.get("name") or ""
            ),
            best_single_score=_score(best_single["score"]),
            best_pair_name=str(
                best_pair.get("mechanism_pair") or best_pair.get("label") or best_pair.get("name") or ""
            ),
            best_pair_score=_score(best_pair["score"]),
        )

    single_entries = list(raw.get("single_mechanisms", []))
    pair_entries = list(raw.get("pairwise_mechanisms", []))
    if not single_entries or not pair_entries:
        raise ValueError("stage 4 summary must include single and pairwise mechanism scores")

    best_single = _best_of(single_entries)
    best_pair = _best_of(pair_entries)
    return Stage4Evidence(
        best_single_mechanism=str(best_single.get("mechanism") or best_single.get("label") or best_single.get("name") or ""),
        best_single_score=_score(best_single["score"]),
        best_pair_name=str(best_pair.get("mechanism_pair") or best_pair.get("label") or best_pair.get("name") or ""),
        best_pair_score=_score(best_pair["score"]),
    )


def _extract_models(raw: Any, source: Path) -> list[dict[str, Any]]:
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {source}, got {type(raw).__name__}.")
    if "models" not in raw:
        raise ValueError(f"Missing 'models' field in {source}.")

    models = raw["models"]
    if isinstance(models, list):
        normalized_models: list[dict[str, Any]] = []
        for index, model in enumerate(models):
            if not isinstance(model, dict):
                raise ValueError(
                    f"Expected 'models[{index}]' in {source} to be an object, got {type(model).__name__}."
                )
            normalized_models.append(dict(model))
        return normalized_models
    if isinstance(models, dict):
        normalized_models = []
        for name, payload in models.items():
            if not isinstance(payload, dict):
                raise ValueError(
                    f"Expected model '{name}' in {source} to be an object, got {type(payload).__name__}."
                )
            model = dict(payload)
            model.setdefault("name", str(name))
            normalized_models.append(model)
        return normalized_models
    raise ValueError(f"Expected 'models' in {source} to be a list or object, got {type(models).__name__}.")


def _optional_float(raw: dict[str, Any], key: str) -> float | None:
    value = raw.get(key)
    return None if value is None else float(value)


def _extract_rocket_benchmark(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    raw = _read_json(path)
    aggregate = raw.get("aggregate")
    dataset = raw.get("dataset")
    rocket = raw.get("rocket")
    if not isinstance(aggregate, dict):
        raise ValueError(f"Missing or invalid 'aggregate' in {path}.")
    if not isinstance(dataset, dict):
        raise ValueError(f"Missing or invalid 'dataset' in {path}.")
    if not isinstance(rocket, dict):
        raise ValueError(f"Missing or invalid 'rocket' in {path}.")
    return {
        "schema_version": str(raw.get("schema_version") or ""),
        "model": str(raw.get("model") or ""),
        "cv_strategy": str(raw.get("cv_strategy") or ""),
        "primary_evaluation_unit": str(raw.get("primary_evaluation_unit") or ""),
        "primary_metric_source": str(raw.get("primary_metric_source") or ""),
        "window_random_reporting": bool(raw.get("window_random_reporting")),
        "sample_count": int(dataset.get("sample_count", 0)),
        "subject_count": int(dataset.get("subject_count", 0)),
        "fold_count": int(dataset.get("fold_count", 0)),
        "n_kernels": int(rocket.get("n_kernels", 0)),
        "feature_count": int(rocket.get("feature_count", 0)),
        "accuracy_mean": _optional_float(aggregate, "accuracy_mean"),
        "accuracy_std": _optional_float(aggregate, "accuracy_std"),
        "balanced_accuracy_mean": _optional_float(aggregate, "balanced_accuracy_mean"),
        "balanced_accuracy_std": _optional_float(aggregate, "balanced_accuracy_std"),
        "roc_auc_mean": _optional_float(aggregate, "roc_auc_mean"),
        "roc_auc_std": _optional_float(aggregate, "roc_auc_std"),
        "claim_guardrail": str(raw.get("claim_guardrail") or ""),
        "comparison_summary_path": "results/training/rocket_condition_benchmark/comparison_summary.json",
        "benchmark_report_path": "results/training/rocket_condition_benchmark/benchmark_report.md",
    }


def _is_publication_sign_mismatch(empirical_value: float, literature_value: float) -> bool:
    if empirical_value == 0.0 or literature_value == 0.0:
        return False
    return (empirical_value > 0) != (literature_value > 0)


def _require_target_deltas(raw: dict[str, Any], source: Path) -> dict[str, Any]:
    target_deltas = raw.get("target_deltas")
    if not isinstance(target_deltas, dict):
        raise ValueError(f"Missing or invalid 'target_deltas' in {source}.")
    return target_deltas


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _extract_subject_validation_evidence(
    raw: dict[str, Any],
    source: Path,
) -> SubjectValidationEvidence:
    boundary = raw.get("empirical_validation_boundary")
    if boundary is None:
        return SubjectValidationEvidence()
    if not isinstance(boundary, dict):
        raise ValueError(f"Expected 'empirical_validation_boundary' in {source} to be an object.")

    legacy_held_out = boundary.get("held_out")
    configured = bool(boundary.get("held_out_validation_configured", legacy_held_out is True))
    completed = bool(boundary.get("held_out_validation_completed", legacy_held_out is True))
    validation_count = int(boundary.get("validation_subject_count") or 0)
    overlap_count = int(boundary.get("overlap_count") or 0)

    if legacy_held_out is True and not completed:
        raise ValueError(
            f"Inconsistent held-out validation metadata in {source}: legacy held_out is true but completion is false."
        )
    if completed and not configured:
        raise ValueError(f"Inconsistent held-out validation metadata in {source}: completed without configured split.")
    if completed and validation_count <= 0:
        raise ValueError(f"Inconsistent held-out validation metadata in {source}: held-out validation completed with no validation subjects.")
    if completed and overlap_count != 0:
        raise ValueError(f"Inconsistent held-out validation metadata in {source}: held-out validation completed with subject overlap.")
    approval_status = str(
        boundary.get("approval_status")
        or ("approved" if completed else "candidate" if configured else "none")
    )
    if completed and approval_status != "approved":
        raise ValueError(
            f"Inconsistent held-out validation metadata in {source}: completed validation requires an approved split."
        )

    return SubjectValidationEvidence(
        configured=configured,
        completed=completed,
        approval_status=approval_status,
        split_id=(
            str(boundary["split_id"])
            if boundary.get("split_id") is not None
            else None
        ),
        split_strategy=str(boundary.get("split_strategy") or "unknown"),
        selection_subject_count=_optional_int(boundary.get("selection_subject_count")),
        validation_subject_count=validation_count,
        overlap_count=overlap_count,
        split_file_path=(
            str(boundary["split_file_path"])
            if boundary.get("split_file_path") is not None
            else None
        ),
        split_schema_version=_optional_int(boundary.get("split_schema_version")),
        split_seed=_optional_int(boundary.get("split_seed")),
        claim_guardrail=str(
            boundary.get("claim_guardrail")
            or "No subject-disjoint held-out validation is configured."
        ),
    )


def _validation_boundary_source(
    stage2_raw: dict[str, Any],
    stage2_path: Path,
    stage3_raw: dict[str, Any],
    stage3_path: Path,
) -> tuple[dict[str, Any], Path]:
    stage3_boundary = stage3_raw.get("empirical_validation_boundary")
    if (
        isinstance(stage3_boundary, dict)
        and stage3_boundary.get("held_out_validation_completed") is True
    ):
        return stage3_raw, stage3_path
    return stage2_raw, stage2_path


def _extract_cv5_validation(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    raw = _read_json(path)
    completed = raw.get("held_out_validation_completed") is True
    if completed:
        if raw.get("approval_status") != "approved":
            raise ValueError(f"Inconsistent CV5 validation metadata in {path}: completed validation requires approval.")
        if raw.get("all_folds_completed") is not True:
            raise ValueError(f"Inconsistent CV5 validation metadata in {path}: completed validation requires all folds.")
        if raw.get("all_subjects_held_out_once") is not True:
            raise ValueError(
                f"Inconsistent CV5 validation metadata in {path}: completed validation requires exact-once held-out coverage."
            )
        scope = str(raw.get("validation_claim_scope") or "")
        if "internal" not in scope or "external" in scope:
            raise ValueError(f"Inconsistent CV5 validation metadata in {path}: scope must remain internal-only.")
        limitations = " ".join(str(item) for item in raw.get("limitations", []))
        warnings = " ".join(str(item) for item in raw.get("warnings", []))
        caveats = f"{limitations} {warnings}".lower()
        for required in ("not external", "n=3", "motion", "fd/dvars"):
            if required not in caveats:
                raise ValueError(
                    f"Inconsistent CV5 validation metadata in {path}: missing required caveat {required!r}."
                )
    return raw


def build_publication_evidence(repo_root: Path) -> PublicationEvidence:
    stage1_path = repo_root / "results" / "stage_1" / "stage_1_summary.json"
    stage2_path = repo_root / "results" / "stage_2" / "stage_2_summary.json"
    stage3_path = repo_root / "results" / "stage_3" / "stage_3_summary.json"
    stage4_path = repo_root / "results" / "stage_4" / "stage_4_summary.json"
    empirical_path = repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml"
    literature_path = repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml"
    condition_path = repo_root / "results" / "training" / "condition_benchmark" / "comparison_summary.json"
    multitask_path = repo_root / "results" / "training" / "multitask_benchmark" / "comparison_summary.json"
    rocket_path = repo_root / "results" / "training" / "rocket_condition_benchmark" / "comparison_summary.json"
    cv5_validation_path = (
        repo_root
        / "output"
        / "validation"
        / "cv5_subject_disjoint"
        / "results"
        / "cv5_aggregate_validation.json"
    )

    stage1 = _read_json(stage1_path)
    stage2_raw = _read_json(stage2_path)
    stage3_raw = _read_json(stage3_path)
    stage4_raw = _read_json(stage4_path)
    empirical_raw = _read_yaml(empirical_path)
    literature_raw = _read_yaml(literature_path)

    empirical_deltas = {str(name): float(value) for name, value in _require_target_deltas(empirical_raw, empirical_path).items()}
    literature_deltas = {str(name): float(value) for name, value in _require_target_deltas(literature_raw, literature_path).items()}

    stage2_provenance_raw = stage2_raw.get("empirical_provenance")
    if not isinstance(stage2_provenance_raw, dict):
        raise ValueError(f"Expected 'empirical_provenance' in {stage2_path} to be an object.")
    required_stage2_fields = ("subject_count", "run_count", "dataset_anchor")
    missing_stage2_fields = [field for field in required_stage2_fields if field not in stage2_provenance_raw]
    if missing_stage2_fields:
        missing = ", ".join(missing_stage2_fields)
        raise ValueError(f"Missing required Stage 2 provenance field(s) in {stage2_path}: {missing}.")
    multi_seed_raw = stage2_raw.get("multi_seed_summary", {})

    mismatches = [
        metric_name
        for metric_name, empirical_value in empirical_deltas.items()
        if metric_name in literature_deltas
        and _is_publication_sign_mismatch(empirical_value, literature_deltas[metric_name])
    ]
    validation_raw, validation_source = _validation_boundary_source(
        stage2_raw,
        stage2_path,
        stage3_raw,
        stage3_path,
    )

    return PublicationEvidence(
        stage1=stage1,
        stage2=Stage2Evidence(
            initial_score=float(stage2_raw["initial_score"]),
            best_score=_score(stage2_raw["best_score"]),
            subject_count=int(stage2_provenance_raw["subject_count"]),
            run_count=int(stage2_provenance_raw["run_count"]),
            dataset_anchor=str(stage2_provenance_raw["dataset_anchor"]),
            best_metrics={str(name): float(value) for name, value in dict(stage2_raw.get("best_metrics", {})).items()},
            multi_seed_mean={
                str(name): float(value)
                for name, value in dict(
                    multi_seed_raw.get("mean_metrics")
                    or stage2_raw.get("best_metrics_mean", {})
                    or {}
                ).items()
            },
            multi_seed_std={
                str(name): float(value)
                for name, value in dict(
                    multi_seed_raw.get("std_metrics")
                    or stage2_raw.get("best_metrics_std", {})
                    or {}
                ).items()
            },
            validation_boundary=_extract_subject_validation_evidence(validation_raw, validation_source),
        ),
        stage3=Stage3Evidence(
            best_mechanism=str(stage3_raw["best_mechanism"]),
            best_strength=float(stage3_raw["best_strength"]),
            best_score=_score(stage3_raw["best_score"]),
            robust_best_mechanism=(
                str(stage3_raw["robust_best_mechanism"])
                if stage3_raw.get("robust_best_mechanism") is not None
                else None
            ),
            robust_best_strength=(
                float(stage3_raw["robust_best_strength"])
                if stage3_raw.get("robust_best_strength") is not None
                else None
            ),
            robust_best_score_mean=(
                float(stage3_raw["robust_best_score_mean"])
                if stage3_raw.get("robust_best_score_mean") is not None
                else None
            ),
            robust_best_score_std=(
                float(stage3_raw["robust_best_score_std"])
                if stage3_raw.get("robust_best_score_std") is not None
                else None
            ),
        ),
        stage4=_extract_stage4_scores(stage4_raw),
        empirical_deltas=empirical_deltas,
        literature_deltas=literature_deltas,
        condition_models=_extract_models(_read_json(condition_path), condition_path),
        multitask_models=_extract_models(_read_json(multitask_path), multitask_path),
        rocket_benchmark=_extract_rocket_benchmark(rocket_path),
        sign_mismatches=mismatches,
        cv5_validation=_extract_cv5_validation(cv5_validation_path),
    )
