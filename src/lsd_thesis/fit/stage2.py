from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
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
from lsd_thesis.data.targets import SoberTargetSet, load_perturbation_target_set, load_sober_target_set
from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import multi_seed_summary
from lsd_thesis.simulator import load_regime_config
from lsd_thesis.subject_split import (
    SubjectSplit,
    build_no_subject_validation_boundary,
    build_subject_validation_boundary,
    load_subject_split_file,
)
from lsd_thesis.utils import get_version_stamp

from .figures import _fc_figure, _history_figure, _metric_comparison_figure, _save_figure
from .scoring import fit_sober_regime
from .seeds import build_fit_seed_plan


def _infer_repo_root(graph_path: str | Path) -> Path:
    return Path(graph_path).resolve().parents[2]

def _build_empirical_provenance(
    *,
    dataset_anchor: str,
    manifest: Any,
    target_paths: dict[str, str],
    viewer_cache_paths: dict[str, str] | None,
    cache_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runs = [run.relative_path for run in manifest.runs]
    sessions = sorted({run.session for run in manifest.runs})
    provenance = {
        "dataset_id": DS003059_DATASET_ID,
        "dataset_version": DS003059_VERSION,
        "dataset_anchor": dataset_anchor,
        "subjects": list(manifest.subjects),
        "subject_count": len(manifest.subjects),
        "sessions": sessions,
        "runs": runs,
        "run_count": len(runs),
        "target_paths": target_paths,
        "viewer_cache_paths": viewer_cache_paths or {},
        "notes": [
            "Canonical Stage 2 provenance reflects the full empirical cohort used to derive the fitted targets.",
            "The single-subject MVP subset helper is written separately as a convenience bootstrap artifact and is not the canonical fit provenance.",
        ],
    }
    if cache_metadata is not None:
        provenance["cache_schema_version"] = cache_metadata.get("schema_version")
        provenance["cache_fingerprint"] = cache_metadata.get("cache_fingerprint")
        provenance["cache_created_at_utc"] = cache_metadata.get("created_at_utc")
        provenance["cache_artifact_hashes"] = cache_metadata.get("artifact_hashes", {})
        provenance["preprocessing_qc"] = cache_metadata.get("preprocessing_qc", {})
    return provenance

def _default_stage2_selection_seeds(seed: int) -> tuple[int, ...]:
    return tuple(seed + 100 + index for index in range(3))

def _default_stage2_validation_seeds(seed: int) -> tuple[int, ...]:
    return tuple(seed + 1000 + index for index in range(5))

def _build_empirical_validation_boundary(
    *,
    target_set: SoberTargetSet,
    empirical_outputs: dict[str, Any] | None,
    seed: int,
    subject_split: SubjectSplit | None = None,
    subject_split_path: str | Path | None = None,
) -> dict[str, Any]:
    if subject_split is not None:
        return build_subject_validation_boundary(
            subject_split,
            split_file_path=subject_split_path,
            held_out_validation_completed=False,
            selection_data_source=f"{target_set.dataset_anchor} (selection/calibration subset)",
            validation_data_source=(
                "Held-out validation subject subset; Stage 3 held-out empirical validation has not yet been run."
            ),
            selection_random_seed=seed,
        )
    subjects = (
        list(empirical_outputs["manifest"].subjects)
        if empirical_outputs is not None and "manifest" in empirical_outputs
        else []
    )
    return build_no_subject_validation_boundary(
        selection_data_source=target_set.dataset_anchor,
        selection_subject_count=len(subjects) if subjects else None,
        selection_random_seed=seed,
    )

def generate_stage_2_outputs(
    graph_path: str | Path,
    baseline_path: str | Path,
    target_path: str | Path,
    output_dir: str | Path,
    report_path: str | Path,
    iterations: int = 24,
    seed: int = 0,
    dataset_dir: str | Path | None = None,
    subjects: tuple[str, ...] | None = None,
    selection_seeds: Sequence[int] | None = None,
    validation_seeds: Sequence[int] | None = None,
    subject_split_path: str | Path | None = None,
    build_viewer: bool = True,
    runs: Sequence[str] | None = None,
    include_music: bool = False,
) -> dict[str, Any]:
    repo_root = _infer_repo_root(graph_path)
    graph = load_graph_config(graph_path)
    regime = load_regime_config(baseline_path)
    empirical_outputs: dict[str, Any] | None = None
    heldout_empirical_outputs: dict[str, Any] | None = None
    resolved_target_path = Path(target_path)
    output_path = Path(output_dir)
    subject_split = load_subject_split_file(subject_split_path) if subject_split_path is not None else None
    if dataset_dir is not None:
        empirical_outputs = generate_empirical_targets(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            subjects=subject_split.selection_subjects if subject_split is not None else subjects,
            runs=runs,
            include_music=include_music,
        )
        resolved_target_path = Path(empirical_outputs["sober_target_path"])
        if subject_split is not None and subject_split.is_approved:
            heldout_empirical_outputs = generate_empirical_targets(
                dataset_dir=dataset_dir,
                output_dir=output_path / "heldout_validation",
                subjects=subject_split.validation_subjects,
                runs=runs,
                include_music=include_music,
            )

    target_set = load_sober_target_set(resolved_target_path)
    atlas_audit = build_atlas_mapping_audit(include_voxel_counts=True, allow_fetch=False)
    stage_selection_seeds = (
        tuple(int(item) for item in selection_seeds)
        if selection_seeds is not None
        else _default_stage2_selection_seeds(seed)
    )
    stage_validation_seeds = (
        tuple(int(item) for item in validation_seeds)
        if validation_seeds is not None
        else _default_stage2_validation_seeds(seed)
    )
    fit_result = fit_sober_regime(
        graph,
        regime,
        target_set,
        iterations=iterations,
        seed=seed,
        selection_seeds=stage_selection_seeds,
        validation_seeds=stage_validation_seeds,
    )
    subset_spec = ds003059_subset_spec()
    mvp_helper = {
        "subset_spec": subset_spec.model_dump(),
        "download_command": build_openneuro_download_command(subset_spec, "data/ds003059_mvp"),
        "notes": [
            "This is a convenience bootstrap helper for a minimal ds003059 subset.",
            "It is not the canonical provenance record for Stage 2 empirical fitting.",
        ],
    }

    figures_path = output_path / "figures"
    atlas_audit_path = output_path / "atlas_mapping_audit.json"
    figures_path.mkdir(parents=True, exist_ok=True)

    _save_figure(
        _metric_comparison_figure(fit_result.best_metrics, target_set),
        figures_path / "sober_metric_fit.html",
    )
    _save_figure(
        _fc_figure(target_set.fc_matrix, graph.modules, "Curated Sober FC Target"),
        figures_path / "target_sober_fc_matrix.html",
    )
    _save_figure(
        _fc_figure(fit_result.best_fc_matrix, graph.modules, "Fitted Sober FC Matrix"),
        figures_path / "fitted_sober_fc_matrix.html",
    )
    _save_figure(
        _history_figure(fit_result.history),
        figures_path / "sober_fit_history.html",
    )

    viewer_cache_paths: dict[str, str] | None = None
    gallery_outputs: list[dict[str, str]] = []
    empirical_data_quality: dict[str, Any] | None = None
    viewer_root = output_path / "empirical_viewer"
    existing_group_overview = viewer_root / "group_overview.json"
    existing_subject_index = viewer_root / "subject_index.json"
    existing_subject_views = viewer_root / "subject_views"
    if (
        build_viewer
        and
        empirical_outputs is not None
        and existing_group_overview.exists()
        and existing_subject_index.exists()
        and existing_subject_views.exists()
    ):
        viewer_cache_paths = {
            "group_overview_path": str(existing_group_overview),
            "subject_index_path": str(existing_subject_index),
            "subject_views_dir": str(existing_subject_views),
        }
        cached_overview = json.loads(existing_group_overview.read_text(encoding="utf-8"))
        gallery_outputs = list(cached_overview.get("gallery", []))
    elif build_viewer and empirical_outputs is not None and dataset_dir is not None:
        run_views = build_empirical_run_views_from_records(
            empirical_outputs["run_records"],
            dataset_dir=dataset_dir,
            output_dir=output_path,
            modules=graph.modules,
        )
        viewer_payloads = build_empirical_viewer_payloads(run_views, modules=graph.modules)
        gallery_outputs = generate_empirical_gallery(
            viewer_payloads["group_overview"],
            figures_dir=figures_path,
        )
        viewer_payloads["group_overview"]["gallery"] = gallery_outputs
        viewer_cache_paths = write_empirical_viewer_cache(
            viewer_payloads,
            output_dir=output_path / "empirical_viewer",
        )
    if empirical_outputs is not None:
        empirical_delta_set = load_perturbation_target_set(empirical_outputs["perturbation_target_path"])
        literature_target_path = repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml"
        literature_delta_set = (
            load_perturbation_target_set(literature_target_path)
            if literature_target_path.exists()
            else None
        )
        empirical_data_quality = build_empirical_data_quality_payload(
            records=list(empirical_outputs["run_records"]),
            empirical_deltas=empirical_delta_set.target_deltas,
            literature_deltas=literature_delta_set.target_deltas if literature_delta_set else None,
        )

    empirical_validation_boundary = _build_empirical_validation_boundary(
        target_set=target_set,
        empirical_outputs=empirical_outputs,
        seed=seed,
        subject_split=subject_split,
        subject_split_path=subject_split_path,
    )
    summary = {
        "dataset_anchor": target_set.dataset_anchor,
        "initial_score": fit_result.initial_score,
        "best_score": fit_result.best_score,
        "selection_score_std": fit_result.selection_score_std,
        "selected_iteration": fit_result.selected_iteration,
        "best_metrics": fit_result.best_metrics,
        "best_metrics_std": fit_result.best_metrics_std,
        "best_parameters": {
            "within_group_scale": fit_result.best_regime.global_parameters.within_group_scale,
            "cross_group_scale": fit_result.best_regime.global_parameters.cross_group_scale,
            "constraint_scale": fit_result.best_regime.global_parameters.constraint_scale,
            "rigidity": fit_result.best_regime.module_defaults.rigidity,
            "barrier": fit_result.best_regime.module_defaults.barrier,
            "temperature": fit_result.best_regime.module_defaults.temperature,
            "tau": fit_result.best_regime.module_defaults.tau,
        },
        "target_path": str(resolved_target_path),
        "atlas_mapping_audit_path": str(atlas_audit_path),
        "fit_seed_plan": fit_result.seed_plan
        or build_fit_seed_plan(
            seed,
            selection_seeds=stage_selection_seeds,
            validation_seeds=stage_validation_seeds,
        ).model_dump(),
        "model_selection_diagnostics": {
            "selected_iteration": fit_result.selected_iteration,
            "selection_score_mean": fit_result.best_score,
            "selection_score_std": fit_result.selection_score_std,
            "selection_seed_count": len(stage_selection_seeds),
            "candidate_count": len(fit_result.history),
            "selection_mode": (
                fit_result.seed_plan.get("selection_mode")
                if fit_result.seed_plan
                else "multi_seed_mean"
            ),
            "history": fit_result.selection_diagnostics,
        },
        "empirical_validation_boundary": empirical_validation_boundary,
    }
    if heldout_empirical_outputs is not None:
        summary["heldout_validation_target_paths"] = {
            "status": "prepared_for_stage3_not_completed",
            "sober": heldout_empirical_outputs["sober_target_path"],
            "perturbation": heldout_empirical_outputs["perturbation_target_path"],
            "subject_count": len(heldout_empirical_outputs["manifest"].subjects),
            "run_count": len(heldout_empirical_outputs["manifest"].runs),
            "subjects": list(heldout_empirical_outputs["manifest"].subjects),
            "claim_guardrail": (
                "Held-out validation target artifacts are prepared for Stage 3, but Stage 2 does not "
                "by itself complete held-out empirical validation."
            ),
        }
        empirical_validation_boundary["validation_data_source"] = (
            "Stage 2 held-out validation target cache reserved for Stage 3 empirical evaluation."
        )

    # Validation-panel uncertainty for the best regime. The fallback keeps older test doubles usable.
    if fit_result.validation_metrics_mean:
        best_mean = fit_result.validation_metrics_mean
        best_std = fit_result.validation_metrics_std
    else:
        best_mean, best_std = multi_seed_summary(
            graph,
            fit_result.best_regime,
            n_seeds=len(stage_validation_seeds),
            base_seed=stage_validation_seeds[0],
        )
    summary["best_metrics_mean"] = best_mean
    summary["best_metrics_std"] = best_std
    summary["multi_seed_summary"] = {
        "role": "validation_seed_panel",
        "seeds": list(stage_validation_seeds),
        "seed_count": len(stage_validation_seeds),
        "mean_metrics": best_mean,
        "std_metrics": best_std,
        "score_mean": fit_result.validation_score_mean,
        "score_std": fit_result.validation_score_std,
        "selection_validation_seed_overlap": bool(
            set(stage_selection_seeds).intersection(stage_validation_seeds)
        ),
    }
    summary["version_stamp"] = get_version_stamp(repo_root)

    if empirical_outputs is not None:
        summary["empirical_subjects"] = list(empirical_outputs["manifest"].subjects)
        summary["empirical_run_count"] = len(empirical_outputs["manifest"].runs)
        summary["perturbation_target_path"] = empirical_outputs["perturbation_target_path"]
        summary["empirical_provenance"] = _build_empirical_provenance(
            dataset_anchor=target_set.dataset_anchor,
            manifest=empirical_outputs["manifest"],
            target_paths={
                "sober": str(resolved_target_path),
                "perturbation": empirical_outputs["perturbation_target_path"],
            },
            viewer_cache_paths=viewer_cache_paths,
            cache_metadata=empirical_outputs.get("cache_metadata"),
        )
        if empirical_data_quality is not None:
            summary["empirical_data_quality_path"] = str(output_path / "empirical_data_quality.json")
    if viewer_cache_paths is not None:
        summary["empirical_viewer"] = viewer_cache_paths
        summary["empirical_gallery"] = gallery_outputs

    output_path.mkdir(parents=True, exist_ok=True)
    atlas_audit_path.write_text(
        json.dumps(atlas_audit, indent=2),
        encoding="utf-8",
    )
    if empirical_data_quality is not None:
        (output_path / "empirical_data_quality.json").write_text(
            json.dumps(empirical_data_quality, indent=2),
            encoding="utf-8",
        )
    (output_path / "stage_2_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (output_path / "ds003059_mvp_subset_plan.json").write_text(
        json.dumps(mvp_helper, indent=2),
        encoding="utf-8",
    )

    report_lines = [
        "# Stage 2 Report",
        "",
        "## Plan",
        "",
        "- Load actual ds003059 resting-state targets when a dataset directory is provided; otherwise fall back to the placeholder config.",
        "- Fit the sober baseline regime with a transparent random search around the baseline config.",
        "- Save the canonical full empirical cohort provenance and keep the MVP subset helper as a separate convenience bootstrap artifact.",
        "",
        "## What Is Fitted Exactly",
        "",
        "- Within-network stability",
        "- Cross-network communication",
        "- Thalamic coupling",
        "- Hierarchical compression",
        "- Entropy / diversity",
        "- Switching rate",
        "- Dynamic FC change / metastability proxy",
        "- Effective barrier proxy",
        "- The sober FC target matrix",
        "",
        "## What Is Only Qualitatively Anchored",
        "",
        "- The atlas-to-module mapping, which is a transparent coarse anatomical proxy rather than a canonical network parcellation.",
        "- The interpretation of these summary metrics as macro-level signatures rather than direct mechanistic readouts.",
        "- The sign agreement between the current 8-module ds003059 extraction and the literature-style target file.",
        "",
        "## Empirical Sign Check",
        "",
        "- The current paired ds003059 extraction supports increased cross-network communication and thalamic coupling under this proxy.",
        "- It conflicts with the literature-style target signs for `within_network_stability`, `entropy_diversity`, and `metastability_proxy`.",
        "- Stage 3 and Stage 4 should therefore be presented as mismatch analysis under one coarse anatomical proxy.",
        "",
        "## Atlas Mapping Audit",
        "",
        f"- Atlas audit artifact: `{atlas_audit_path.name}`",
        f"- Assigned atlas voxels: `{atlas_audit['assigned_voxels'] or 'not computed in cached fast run'}`",
        f"- Overlapping source labels: `{len(atlas_audit['overlaps'])}`",
        "",
        "## Empirical Data Quality",
        "",
        f"- Data quality artifact: `{'empirical_data_quality.json' if empirical_data_quality else 'not available'}`",
        f"- Paired subjects: `{empirical_data_quality['paired_subject_count'] if empirical_data_quality else 'n/a'}`",
        f"- Complete subjects: `{empirical_data_quality['complete_subject_count'] if empirical_data_quality else 'n/a'}`",
        f"- Sign conflicts: `{len(empirical_data_quality['sign_conflicts']) if empirical_data_quality else 'n/a'}`",
        "",
        "## Empirical Viewer Outputs",
        "",
        "- Group-average empirical overview cache",
        "- Subject/run paired empirical detail cache",
        "- Precomputed empirical gallery figures for traces, FC, and delta summaries",
        "",
        "## Results",
        "",
        f"- Initial score: {fit_result.initial_score:.4f}",
        f"- Best selection score: {fit_result.best_score:.4f} ± {fit_result.selection_score_std:.4f}",
        f"- Selected iteration: {fit_result.selected_iteration}",
        f"- Selection seeds: `{list(stage_selection_seeds)}`",
        f"- Validation seeds: `{list(stage_validation_seeds)}`",
        f"- Validation score: `{fit_result.validation_score_mean if fit_result.validation_score_mean is not None else 'n/a'}`",
        f"- Best within-network stability: {fit_result.best_metrics['within_network_stability']:.4f}",
        f"- Best cross-network communication: {fit_result.best_metrics['cross_network_communication']:.4f}",
        f"- Best entropy / diversity: {fit_result.best_metrics['entropy_diversity']:.4f}",
        f"- Best switching rate: {fit_result.best_metrics['switching_rate']:.4f}",
        "",
        "## Empirical Validation Boundary",
        "",
        (
            "- Held-out empirical validation: `split configured, not yet completed`"
            if subject_split is not None
            else "- Held-out empirical validation: `not configured`"
        ),
        (
            "- Stage 2 calibration uses only the split selection subjects when a split file is provided."
            if subject_split is not None
            else "- Stage 2 uses available empirical targets for calibration/selection, not for an independent held-out claim."
        ),
        "- Stage 2b reliability summaries should be presented as target stability diagnostics, not as held-out model validation.",
        "",
        "## Critical Review",
        "",
        "- The fitting loop is intentionally small and transparent, so it should be treated as calibration rather than optimization proof.",
        "- Multi-seed selection reduces single-realization dependence when configured, but it does not by itself create a held-out empirical test.",
        "- If actual ds003059 targets were used, the remaining mismatch is now a model limitation rather than a placeholder-data limitation.",
        "- The full empirical cohort provenance is the canonical reproducibility record for this run.",
        "- The saved MVP subset helper is a convenience bootstrap artifact and is not the canonical fit provenance.",
        "- The empirical viewer uses downsampled window previews for interpretability and speed; it is not a diagnostic-grade imaging viewer.",
        "- The current Harvard-Oxford macro-module mapping contains overlapping source labels; "
        "the label-image builder resolves those overlaps by assignment order.",
        "",
        "## Provenance",
        "",
        "- The canonical Stage 2 provenance comes from the full empirical cohort used to derive the fitted targets.",
        "- The MVP subset helper is stored separately as a convenience bootstrap artifact for lightweight ds003059 setup.",
        "",
    ]
    Path(report_path).write_text("\n".join(report_lines), encoding="utf-8")
    return summary
