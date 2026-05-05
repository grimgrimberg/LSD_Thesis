from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


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


@dataclass(slots=True)
class Stage3Evidence:
    best_mechanism: str
    best_strength: float
    best_score: float


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


def _is_publication_sign_mismatch(empirical_value: float, literature_value: float) -> bool:
    if empirical_value == 0.0 or literature_value == 0.0:
        return False
    return (empirical_value > 0) != (literature_value > 0)


def _require_target_deltas(raw: dict[str, Any], source: Path) -> dict[str, Any]:
    target_deltas = raw.get("target_deltas")
    if not isinstance(target_deltas, dict):
        raise ValueError(f"Missing or invalid 'target_deltas' in {source}.")
    return target_deltas


def build_publication_evidence(repo_root: Path) -> PublicationEvidence:
    stage1_path = repo_root / "results" / "stage_1" / "stage_1_summary.json"
    stage2_path = repo_root / "results" / "stage_2" / "stage_2_summary.json"
    stage3_path = repo_root / "results" / "stage_3" / "stage_3_summary.json"
    stage4_path = repo_root / "results" / "stage_4" / "stage_4_summary.json"
    empirical_path = repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml"
    literature_path = repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml"
    condition_path = repo_root / "results" / "training" / "condition_benchmark" / "comparison_summary.json"
    multitask_path = repo_root / "results" / "training" / "multitask_benchmark" / "comparison_summary.json"

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
        ),
        stage3=Stage3Evidence(
            best_mechanism=str(stage3_raw["best_mechanism"]),
            best_strength=float(stage3_raw["best_strength"]),
            best_score=_score(stage3_raw["best_score"]),
        ),
        stage4=_extract_stage4_scores(stage4_raw),
        empirical_deltas=empirical_deltas,
        literature_deltas=literature_deltas,
        condition_models=_extract_models(_read_json(condition_path), condition_path),
        multitask_models=_extract_models(_read_json(multitask_path), multitask_path),
        sign_mismatches=mismatches,
    )
