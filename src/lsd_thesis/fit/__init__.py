from __future__ import annotations

from typing import Any

from lsd_thesis.data.ds003059 import (
    DS003059_DATASET_ID,
    DS003059_VERSION,
    build_atlas_mapping_audit,
    build_empirical_data_quality_payload,
    generate_empirical_targets,
)
from lsd_thesis.data.empirical_viewer import (
    build_empirical_run_views_from_records,
    build_empirical_viewer_payloads,
    generate_empirical_gallery,
    write_empirical_viewer_cache,
)
from lsd_thesis.data.openneuro import build_openneuro_download_command, ds003059_subset_spec
from lsd_thesis.data.targets import load_perturbation_target_set, load_sober_target_set
from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import multi_seed_summary
from lsd_thesis.simulator import load_regime_config
from lsd_thesis.subject_split import load_subject_split_file
from lsd_thesis.utils import get_version_stamp

from . import scoring as _scoring
from . import stage2 as _stage2
from .figures import _fc_figure, _history_figure, _metric_comparison_figure, _save_figure
from .models import FitResult, FitSeedPlan
from .scoring import (
    LEGACY_METRIC_ALIASES,
    _candidate_from_initial,
    _evaluate_regime_seed_panel,
    _metric_panel_mean_std,
    _score_against_targets,
    _selection_seeds_for_candidate,
    _with_legacy_aliases,
    summarize_regime,
)
from .seeds import _coerce_seed_tuple, build_fit_seed_plan
from .stage2 import (
    _build_empirical_provenance,
    _build_empirical_validation_boundary,
    _default_stage2_selection_seeds,
    _default_stage2_validation_seeds,
    _infer_repo_root,
)


def fit_sober_regime(*args: Any, **kwargs: Any) -> FitResult:
    replacements = {
        "_candidate_from_initial": _candidate_from_initial,
        "_evaluate_regime_seed_panel": _evaluate_regime_seed_panel,
        "_score_against_targets": _score_against_targets,
        "_selection_seeds_for_candidate": _selection_seeds_for_candidate,
        "build_fit_seed_plan": build_fit_seed_plan,
        "summarize_regime": summarize_regime,
    }
    previous = {name: getattr(_scoring, name) for name in replacements}
    for name, value in replacements.items():
        setattr(_scoring, name, value)
    try:
        return _scoring.fit_sober_regime(*args, **kwargs)
    finally:
        for name, value in previous.items():
            setattr(_scoring, name, value)


def generate_stage_2_outputs(*args: Any, **kwargs: Any) -> dict[str, Any]:
    replacements = {
        "_build_empirical_provenance": _build_empirical_provenance,
        "_build_empirical_validation_boundary": _build_empirical_validation_boundary,
        "_default_stage2_selection_seeds": _default_stage2_selection_seeds,
        "_default_stage2_validation_seeds": _default_stage2_validation_seeds,
        "_fc_figure": _fc_figure,
        "_history_figure": _history_figure,
        "_infer_repo_root": _infer_repo_root,
        "_metric_comparison_figure": _metric_comparison_figure,
        "_save_figure": _save_figure,
        "build_atlas_mapping_audit": build_atlas_mapping_audit,
        "build_empirical_data_quality_payload": build_empirical_data_quality_payload,
        "build_empirical_run_views_from_records": build_empirical_run_views_from_records,
        "build_empirical_viewer_payloads": build_empirical_viewer_payloads,
        "build_fit_seed_plan": build_fit_seed_plan,
        "build_openneuro_download_command": build_openneuro_download_command,
        "ds003059_subset_spec": ds003059_subset_spec,
        "fit_sober_regime": fit_sober_regime,
        "generate_empirical_gallery": generate_empirical_gallery,
        "generate_empirical_targets": generate_empirical_targets,
        "get_version_stamp": get_version_stamp,
        "load_graph_config": load_graph_config,
        "load_perturbation_target_set": load_perturbation_target_set,
        "load_regime_config": load_regime_config,
        "load_sober_target_set": load_sober_target_set,
        "load_subject_split_file": load_subject_split_file,
        "multi_seed_summary": multi_seed_summary,
        "write_empirical_viewer_cache": write_empirical_viewer_cache,
    }
    previous = {name: getattr(_stage2, name) for name in replacements}
    for name, value in replacements.items():
        setattr(_stage2, name, value)
    try:
        return _stage2.generate_stage_2_outputs(*args, **kwargs)
    finally:
        for name, value in previous.items():
            setattr(_stage2, name, value)


__all__ = [
    "DS003059_DATASET_ID",
    "DS003059_VERSION",
    "FitResult",
    "FitSeedPlan",
    "LEGACY_METRIC_ALIASES",
    "_build_empirical_provenance",
    "_build_empirical_validation_boundary",
    "_candidate_from_initial",
    "_coerce_seed_tuple",
    "_default_stage2_selection_seeds",
    "_default_stage2_validation_seeds",
    "_evaluate_regime_seed_panel",
    "_fc_figure",
    "_history_figure",
    "_infer_repo_root",
    "_metric_comparison_figure",
    "_metric_panel_mean_std",
    "_save_figure",
    "_score_against_targets",
    "_selection_seeds_for_candidate",
    "_with_legacy_aliases",
    "build_atlas_mapping_audit",
    "build_empirical_data_quality_payload",
    "build_empirical_run_views_from_records",
    "build_empirical_viewer_payloads",
    "build_fit_seed_plan",
    "build_openneuro_download_command",
    "ds003059_subset_spec",
    "fit_sober_regime",
    "generate_empirical_gallery",
    "generate_empirical_targets",
    "generate_stage_2_outputs",
    "get_version_stamp",
    "load_graph_config",
    "load_perturbation_target_set",
    "load_regime_config",
    "load_sober_target_set",
    "load_subject_split_file",
    "multi_seed_summary",
    "summarize_regime",
    "write_empirical_viewer_cache",
]
