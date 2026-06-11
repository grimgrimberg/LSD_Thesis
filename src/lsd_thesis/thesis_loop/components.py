from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.ds006072_validation import build_ds006072_comparable_validation_status
from lsd_thesis.dynamic_mechanism.core import build_dynamic_mechanism_summary, load_empirical_pairs, summarize_network_control_energy
from lsd_thesis.dynamic_robustness import build_dynamic_robustness_summary, literature_benchmark_from_summary
from lsd_thesis.external_source_plan import (
    EXTERNAL_SOURCE_PLAN_COLUMNS,
    external_source_by_id,
    external_source_plan_rows,
    external_source_reference_by_id,
)
from lsd_thesis.graph import load_graph_config

from .claims import _build_claim_evidence_matrix
from .controls import (
    _build_proxy_graph_control_rows,
    _build_structural_graph_control_rows,
    _coarse_receptor_null_rows,
    _matrix_from_csv,
    _prior_vector_from_csv,
)
from .status import (
    CLAIM_EVIDENCE_COLUMNS,
    DS006072_DATASET_ID,
    REPO_ROOT,
    _external_source_component_status,
    _load_json,
    _now,
    _status_row,
    _write_csv,
    _write_json,
    _write_markdown_table,
)


def build_psilocybin_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "psilocybin_ds006072"
    viewer_root = output_dir / "empirical_viewer"
    readiness_path = output_dir / "external_validation_readiness.json"
    local_data_root = repo_root / "data" / DS006072_DATASET_ID
    metadata_manifest_path = local_data_root / "ds006072_metadata_manifest.json"
    func_manifest_path = local_data_root / "ds006072_func_manifest.json"
    metadata_manifest = _load_json(metadata_manifest_path)
    func_manifest = _load_json(func_manifest_path)
    comparable_validation = build_ds006072_comparable_validation_status(repo_root)
    readiness = _load_json(readiness_path)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "dataset_id": DS006072_DATASET_ID,
        "source": (
            "Dosenbach/Siegel group Scientific Data 2025; OpenNeuro ds006072 psilocybin precision "
            "functional mapping dataset with raw, minimally processed, and fully processed imaging"
        ),
        "source_reference": external_source_by_id("dosenbach_siegel_ds006072_2025"),
        "local_data_root": local_data_root.relative_to(repo_root).as_posix(),
        "viewer_root": viewer_root.relative_to(repo_root).as_posix(),
        "metadata_manifest": metadata_manifest_path.relative_to(repo_root).as_posix() if metadata_manifest_path.exists() else None,
        "metadata_snapshot_tag": metadata_manifest.get("snapshot_tag") if isinstance(metadata_manifest, dict) else None,
        "functional_manifest": func_manifest_path.relative_to(repo_root).as_posix() if func_manifest_path.exists() else None,
        "functional_manifest_rest_bold_nifti_count": (
            func_manifest.get("rest_bold_nifti_count") if isinstance(func_manifest, dict) else None
        ),
        "functional_manifest_rest_bold_total_size_bytes": (
            func_manifest.get("rest_bold_total_size_bytes") if isinstance(func_manifest, dict) else None
        ),
        "functional_manifest_processed_rest_cifti_count": (
            func_manifest.get("processed_rest_cifti_count") if isinstance(func_manifest, dict) else None
        ),
        "functional_manifest_processed_cifti_total_size_bytes": (
            func_manifest.get("processed_cifti_total_size_bytes") if isinstance(func_manifest, dict) else None
        ),
        "external_validation_readiness": readiness if isinstance(readiness, dict) else None,
        "external_validation_readiness_path": (
            readiness_path.relative_to(repo_root).as_posix() if readiness_path.exists() else None
        ),
        "claim_guardrail": (
            "Comparable paired drug/control empirical viewer records only establish a cross-drug stress test; "
            "a replication interpretation would require the unchanged-scoring result itself to support that "
            "stronger claim."
        ),
    }
    if comparable_validation.get("unchanged_scoring_applied"):
        summary = comparable_validation.get("summary", {}) if isinstance(comparable_validation.get("summary"), dict) else {}
        if isinstance(payload.get("external_validation_readiness"), dict):
            readiness_snapshot = dict(payload["external_validation_readiness"])
            readiness_snapshot["readiness_context"] = "pre_extraction_source_availability_snapshot"
            readiness_snapshot["blocker"] = (
                "Superseded by comparable empirical validation summary; retained as source-availability context."
            )
            readiness_snapshot["claim_guardrail"] = (
                "Superseded by comparable empirical validation summary; this nested readiness snapshot is "
                "not the current validation verdict."
            )
            payload["external_validation_readiness"] = readiness_snapshot
        payload.update(
            {
                "analysis_status": comparable_validation["analysis_status"],
                "pair_count": summary.get("pair_count", 0),
                "subject_count": summary.get("subject_count", 0),
                "mechanism_ranking": summary.get("mechanism_ranking", []),
                "summary": summary,
                "comparable_empirical_validation": comparable_validation,
                "comparable_empirical_validation_path": comparable_validation["source_path"],
                "unchanged_scoring_applied": True,
                "replication_status": comparable_validation.get("replication_status"),
                "validation_scope": comparable_validation.get("validation_scope"),
                "stronger_external_validation_ready": comparable_validation.get("stronger_external_validation_ready"),
                "schaefer100_empirical_viewer_ready": comparable_validation.get("schaefer100_empirical_viewer_ready"),
                "ds006072_top_layer": comparable_validation.get("ds006072_top_layer"),
                "lsd_reference_top_layer": comparable_validation.get("lsd_reference_top_layer"),
                "claim_guardrail": (
                    "Comparable ds006072 Schaefer100/Yeo7 scoring is implemented as a small-subject "
                    "cross-drug stress test. It is not population, clinical, or subjective-state validation, "
                    "and a top-layer mismatch must be reported as negative/partial external evidence."
                ),
            }
        )
    else:
        schema_path = output_dir / "required_empirical_viewer_schema.json"
        _write_json(
            schema_path,
            {
                "subject_views_pattern": "subject_views/{subject}_{run}.json",
                "required_conditions": ["control_or_placebo_session", "psilocybin_session"],
                "required_fields": [
                    "subject",
                    "run",
                    "conditions.<control>.module_time_series",
                    "conditions.<psilocybin>.module_time_series",
                ],
                "note": "The condition names must be harmonized before running the dynamic mechanism summary.",
            },
        )
        readiness_status = readiness.get("analysis_status") if isinstance(readiness, dict) else None
        readiness_blocker = readiness.get("blocker") if isinstance(readiness, dict) else None
        payload.update(
            {
                "analysis_status": (
                    comparable_validation.get("analysis_status")
                    or readiness_status
                    or (
                        "metadata_and_file_manifest_ready_missing_empirical_viewer"
                        if func_manifest_path.exists()
                        else "blocked_missing_local_ds006072_empirical_viewer"
                    )
                ),
                "pair_count": comparable_validation.get("pair_count", 0),
                "subject_count": comparable_validation.get("subject_count", 0),
                "blocker": (
                    comparable_validation.get("blocker")
                    or readiness_blocker
                    or (
                        "Expected comparable paired psilocybin/control empirical viewer records under "
                        f"{viewer_root.relative_to(repo_root).as_posix()}."
                    )
                ),
                "schema_template": schema_path.relative_to(repo_root).as_posix(),
                "comparable_empirical_validation": comparable_validation,
                "comparable_empirical_validation_path": comparable_validation["source_path"],
                "unchanged_scoring_applied": False,
                "replication_status": comparable_validation.get("replication_status"),
                "validation_scope": comparable_validation.get("validation_scope"),
                "stronger_external_validation_ready": comparable_validation.get("stronger_external_validation_ready"),
                "schaefer100_empirical_viewer_ready": comparable_validation.get("schaefer100_empirical_viewer_ready"),
                "ds006072_top_layer": comparable_validation.get("ds006072_top_layer"),
                "lsd_reference_top_layer": comparable_validation.get("lsd_reference_top_layer"),
                "next_commands": [
                    "Build extraction readiness: .venv\\Scripts\\python.exe scripts\\build_ds006072_external_validation_readiness.py",
                    "Acquire or derive ds006072 paired psilocybin/control module time series under data/ds006072/.",
                    "Run metadata provenance first if missing: .venv\\Scripts\\python.exe scripts\\download_ds006072_metadata.py",
                    "Write subject-level JSON records matching results/stage_2/empirical_viewer/subject_views/*.json.",
                    "Then rerun: .venv\\Scripts\\python.exe scripts\\run_thesis_evidence_loop.py",
                ],
            }
        )
    payload["source_reference"] = external_source_reference_by_id(
        "dosenbach_siegel_ds006072_2025",
        payload.get("analysis_status"),
    )
    payload["source_path"] = _write_json(output_dir / "psilocybin_ds006072_status.json", payload)
    return payload

def build_structural_connectome_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "structural_connectome"
    graph_candidates = [
        output_dir / "hcp_macro_modules.csv",
        repo_root / "data" / "hcp_structural_connectome" / "macro_modules.csv",
    ]
    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    pairs = load_empirical_pairs(viewer_root)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "artifact_target": output_dir.relative_to(repo_root).as_posix(),
        "source_reference": external_source_by_id("hcp_young_adult"),
        "expected_graph_files": [path.relative_to(repo_root).as_posix() for path in graph_candidates],
        "claim_guardrail": "HCP structural-control claims require a documented structural-connectome graph, not the macro-module proxy graph.",
    }
    graph_path = next((path for path in graph_candidates if path.exists()), None)
    if graph_path is None or not pairs:
        template_path = output_dir / "required_hcp_macro_modules_template.csv"
        proxy_graph_rows: list[dict[str, Any]] = []
        if pairs and (repo_root / "configs" / "graphs" / "macro_modules.yaml").exists():
            macro_graph = load_graph_config(repo_root / "configs" / "graphs" / "macro_modules.yaml")
            proxy_graph_rows = _build_proxy_graph_control_rows(pairs, np.asarray(macro_graph.adjacency, dtype=float))
            _write_csv(output_dir / "proxy_graph_control_nulls.csv", proxy_graph_rows)
        if graph_path is None:
            template_rows = [
                {"source": source, "target": target, "weight": ""}
                for idx, source in enumerate(MODULE_NAMES)
                for target in MODULE_NAMES[idx + 1 :]
            ]
            _write_csv(template_path, template_rows)
        payload.update(
            {
                "analysis_status": "blocked_missing_hcp_structural_graph" if graph_path is None else "blocked_missing_lsd_pairs",
                "blocker": "No local HCP/normative structural graph CSV was found." if graph_path is None else "No LSD empirical pairs were found.",
                "required_schema": "CSV edge list with source,target,weight or square matrix with module plus module columns.",
                "schema_template": template_path.relative_to(repo_root).as_posix() if graph_path is None else None,
                "proxy_graph_control_status": (
                    "implemented_macro_proxy_graph_controls_not_hcp" if proxy_graph_rows else "not_run"
                ),
                "proxy_graph_control_rows": proxy_graph_rows,
                "proxy_graph_control_path": (
                    (output_dir / "proxy_graph_control_nulls.csv").relative_to(repo_root).as_posix()
                    if proxy_graph_rows
                    else None
                ),
            }
        )
    else:
        graph_matrix, graph_kind = _matrix_from_csv(graph_path, pairs[0].modules)
        control = summarize_network_control_energy(
            pairs,
            graph_matrix_override=graph_matrix,
            graph_source_override=f"{graph_path.relative_to(repo_root).as_posix()} ({graph_kind})",
            graph_is_structural_connectome=True,
        )
        graph_rewire_rows = _build_structural_graph_control_rows(
            pairs,
            graph_matrix,
            graph_path=graph_path.relative_to(repo_root),
        )
        graph_rewire_path = output_dir / "structural_graph_rewire_nulls.csv"
        _write_csv(graph_rewire_path, graph_rewire_rows)
        payload.update(
            {
                "analysis_status": "implemented_hcp_structural_graph_sensitivity",
                "graph_path": graph_path.relative_to(repo_root).as_posix(),
                "graph_kind": graph_kind,
                "pair_count": len(pairs),
                "network_control_energy": control,
                "graph_rewire_null_status": "implemented_hcp_structural_graph_rewire_nulls",
                "graph_rewire_null_path": graph_rewire_path.relative_to(repo_root).as_posix(),
                "graph_rewire_null_rows": graph_rewire_rows,
            }
        )
        _write_csv(output_dir / "structural_network_control_metrics.csv", control.get("metric_deltas", []))
    payload["source_reference"] = external_source_reference_by_id(
        "hcp_young_adult",
        payload.get("analysis_status"),
    )
    payload["source_path"] = _write_json(output_dir / "structural_connectome_status.json", payload)
    return payload

def build_receptor_prior_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "receptor_priors"
    prior_candidates = [
        output_dir / "fs5ht_5ht2a_macro_modules.csv",
        repo_root / "data" / "receptor_priors" / "fs5ht_5ht2a_macro_modules.csv",
        repo_root / "data" / "neuromaps" / "fs5ht_5ht2a_macro_modules.csv",
    ]
    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    pairs = load_empirical_pairs(viewer_root)
    spatial_null_path = repo_root / "results" / "cortical_maps" / "neuromaps_spatial_null_status.json"
    map_falsification_path = repo_root / "results" / "cortical_maps" / "map_prior_falsification_status.json"
    spatial_nulls = _load_json(spatial_null_path) or {}
    map_falsification = _load_json(map_falsification_path) or {}
    receptor_moran = spatial_nulls.get("receptor_moran_nulls", {})
    receptor_moran = receptor_moran if isinstance(receptor_moran, dict) else {}
    receptor_spatial_ready = bool(spatial_nulls.get("receptor_spatial_nulls_complete"))
    fdr_supported_count = int(receptor_moran.get("fdr_supported_count") or 0)
    best_spatial = receptor_moran.get("best_result", {})
    best_spatial = best_spatial if isinstance(best_spatial, dict) else {}
    if receptor_spatial_ready and fdr_supported_count == 0:
        claim_promotion_status = "not_supported_after_pet_spatial_nulls"
    elif receptor_spatial_ready:
        claim_promotion_status = "requires_manual_review_pet_spatial_null_support"
    else:
        claim_promotion_status = "blocked_missing_receptor_spatial_nulls"
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "artifact_target": output_dir.relative_to(repo_root).as_posix(),
        "source_reference": external_source_by_id("markello_neuromaps_2022"),
        "expected_prior_files": [path.relative_to(repo_root).as_posix() for path in prior_candidates],
        "claim_guardrail": "Receptor-specific claims require PET-derived 5-HT2A/FS5ht priors and spatial nulls.",
        "spatial_null_control_status": spatial_nulls.get("analysis_status", "missing_spatial_null_status"),
        "spatial_null_control_path": (
            spatial_null_path.relative_to(repo_root).as_posix() if spatial_null_path.exists() else None
        ),
        "map_prior_falsification_path": (
            map_falsification_path.relative_to(repo_root).as_posix() if map_falsification_path.exists() else None
        ),
        "receptor_spatial_nulls_complete": receptor_spatial_ready,
        "receptor_spatial_null_fdr_supported_count": fdr_supported_count,
        "best_receptor_spatial_null_result": best_spatial,
        "claim_promotion_status": claim_promotion_status,
        "claim_resolution": map_falsification.get("claim_readiness")
        if isinstance(map_falsification.get("claim_readiness"), dict)
        else map_falsification.get("spatial_nulls", {}),
    }
    prior_path = next((path for path in prior_candidates if path.exists()), None)
    if prior_path is None or not pairs:
        template_path = output_dir / "required_fs5ht_5ht2a_macro_modules_template.csv"
        proxy_null_rows = _coarse_receptor_null_rows(repo_root, pairs) if pairs else []
        if proxy_null_rows:
            _write_csv(output_dir / "proxy_receptor_null_board.csv", proxy_null_rows)
        if prior_path is None:
            _write_csv(
                template_path,
                [
                    {"module": module, "receptor_weight": "", "source": "PET-derived 5-HT2A map projected to this module"}
                    for module in MODULE_NAMES
                ],
            )
        payload.update(
            {
                "analysis_status": "blocked_missing_pet_receptor_prior" if prior_path is None else "blocked_missing_lsd_pairs",
                "blocker": "No local PET-derived receptor-prior CSV was found." if prior_path is None else "No LSD empirical pairs were found.",
                "required_schema": "CSV with module,receptor_weight and optional source columns.",
                "schema_template": template_path.relative_to(repo_root).as_posix() if prior_path is None else None,
                "proxy_null_board_status": (
                    "implemented_coarse_prior_null_board_not_pet" if proxy_null_rows else "not_run"
                ),
                "proxy_null_board_path": (
                    (output_dir / "proxy_receptor_null_board.csv").relative_to(repo_root).as_posix()
                    if proxy_null_rows
                    else None
                ),
                "proxy_null_board_rows": proxy_null_rows,
            }
        )
    else:
        receptor_vector, source = _prior_vector_from_csv(prior_path, pairs[0].modules)
        control = summarize_network_control_energy(
            pairs,
            prior_vectors_override={"receptor": receptor_vector},
            receptor_prior_source_override=f"PET-derived prior from {source}",
        )
        payload.update(
            {
                "analysis_status": "implemented_pet_receptor_prior_sensitivity",
                "prior_path": prior_path.relative_to(repo_root).as_posix(),
                "pair_count": len(pairs),
                "network_control_energy": control,
            }
        )
        _write_csv(output_dir / "receptor_prior_network_control_metrics.csv", control.get("metric_deltas", []))
    payload["source_reference"] = external_source_reference_by_id(
        "markello_neuromaps_2022",
        payload.get("analysis_status"),
    )
    payload["source_path"] = _write_json(output_dir / "receptor_prior_status.json", payload)
    return payload

def build_parcellation_sensitivity_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "parcellation_sensitivity"
    stage2_parcellation_root = repo_root / "results" / "stage_2" / "parcellations"
    candidates = {
        "schaefer_100_yeo_7": stage2_parcellation_root / "schaefer_100_yeo_7",
        "schaefer_100_yeo_7_striatal": stage2_parcellation_root / "schaefer_100_yeo_7_striatal",
        "schaefer_200_yeo_7": stage2_parcellation_root / "schaefer_200_yeo_7",
        "schaefer_100_yeo_17": stage2_parcellation_root / "schaefer_100_yeo_17",
        "schaefer_200_yeo_17": stage2_parcellation_root / "schaefer_200_yeo_17",
    }
    rows: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for parcellation_id, root in candidates.items():
        viewer_root = root / "empirical_viewer"
        metadata_path = root / "node_metadata.json"
        precomputed_summary_path = output_dir / parcellation_id / "summary.json"
        if precomputed_summary_path.exists():
            summary = _load_json(precomputed_summary_path) or {}
            rows.append(
                {
                    "parcellation_id": parcellation_id,
                    "status": "implemented_mechanism_ranking",
                    "pair_count": summary.get("pair_count", 0),
                    "subject_count": summary.get("subject_count", 0),
                    "top_layer": summary.get("mechanism_ranking", [{}])[0].get("layer"),
                    "summary_path": precomputed_summary_path.relative_to(repo_root).as_posix(),
                }
            )
            comparisons.extend(
                {
                    "parcellation_id": parcellation_id,
                    "rank": row.get("rank"),
                    "layer": row.get("layer"),
                    "score": row.get("score"),
                    "status": row.get("status"),
                }
                for row in summary.get("mechanism_ranking", [])
            )
        elif viewer_root.exists():
            summary = build_dynamic_mechanism_summary(viewer_root, network_control_kwargs={"random_null_count": 16})
            rows.append(
                {
                    "parcellation_id": parcellation_id,
                    "status": "implemented_mechanism_ranking" if summary.get("pair_count", 0) else "blocked_empty_viewer",
                    "pair_count": summary.get("pair_count", 0),
                    "subject_count": summary.get("subject_count", 0),
                    "top_layer": summary.get("mechanism_ranking", [{}])[0].get("layer"),
                    "summary_path": None,
                }
            )
            comparisons.extend(
                {
                    "parcellation_id": parcellation_id,
                    "rank": row.get("rank"),
                    "layer": row.get("layer"),
                    "score": row.get("score"),
                    "status": row.get("status"),
                }
                for row in summary.get("mechanism_ranking", [])
            )
        else:
            rows.append(
                {
                    "parcellation_id": parcellation_id,
                    "status": "metadata_ready_extraction_not_run" if metadata_path.exists() else "blocked_missing_metadata_and_viewer",
                    "pair_count": 0,
                    "subject_count": 0,
                    "top_layer": None,
                    "blocker": f"No empirical_viewer found at {viewer_root.relative_to(repo_root).as_posix()}",
                }
            )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "analysis_status": "implemented_status_matrix",
        "source_reference": external_source_by_id("schaefer_2018_local_global"),
        "rows": rows,
        "ranking_comparison_rows": comparisons,
        "claim_guardrail": "Parcellation sensitivity is not a completed empirical result unless a parcellation-specific empirical_viewer exists.",
    }
    _write_csv(output_dir / "parcellation_status.csv", rows)
    if comparisons:
        _write_csv(output_dir / "parcellation_ranking_comparison.csv", comparisons)
    payload["source_reference"] = external_source_reference_by_id(
        "schaefer_2018_local_global",
        _external_source_component_status("parcellation_sensitivity", payload),
    )
    payload["source_path"] = _write_json(output_dir / "parcellation_sensitivity_status.json", payload)
    return payload

def build_motion_sensitive_c_gate_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "confound_controls"
    motion_path = output_dir / "motion_confound_control_status.json"
    module_dvars_path = output_dir / "module_dvars_control_status.json"
    image_qc_path = output_dir / "image_motion_qc_status.json"
    published_qc_path = output_dir / "published_motion_qc_status.json"
    design_path = output_dir / "design_confound_control_status.json"
    motion = _load_json(motion_path) or {}
    module_dvars = _load_json(module_dvars_path) or {}
    image_qc = _load_json(image_qc_path) or {}
    published_qc = _load_json(published_qc_path) or {}
    design = _load_json(design_path) or {}

    strict_motion_ready = bool(
        motion.get("motion_confound_control_ready")
        or motion.get("fmriprep_motion_control_ready")
    )
    module_unstable = int(module_dvars.get("unstable_high_burden_exclusion_count") or 0)
    image_unstable = int(image_qc.get("unstable_high_burden_exclusion_count") or 0)
    if strict_motion_ready and module_unstable == 0 and image_unstable == 0:
        analysis_status = "implemented_motion_sensitive_c_exclusion_gate"
        evidence = "Structured motion controls are ready and high-burden exclusions did not destabilize C-sensitive summaries."
        blocker = ""
    else:
        analysis_status = "blocked_motion_sensitive_c_claim_requires_authorized_confound_exclusions"
        evidence = (
            "Schaefer/Yeo C sensitivity exists, but final C claims remain gated because strict subject/run "
            "FD/DVARS/censoring confounds are not proof-ready or high-burden exclusions are unstable."
        )
        blocker = str(
            motion.get("blocker")
            or "Authorized fMRIPrep FD/DVARS/censoring confounds are required before motion-sensitive final claims."
        )

    return {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "analysis_status": analysis_status,
        "artifact_target": output_dir.relative_to(repo_root).as_posix(),
        "evidence": evidence,
        "blocker": blocker,
        "strict_motion_confound_ready": strict_motion_ready,
        "motion_confound_status": motion.get("analysis_status", "missing"),
        "module_dvars_status": module_dvars.get("analysis_status", "missing"),
        "module_dvars_claim_status": module_dvars.get("claim_status"),
        "module_dvars_unstable_high_burden_exclusion_count": module_unstable,
        "image_motion_qc_status": image_qc.get("analysis_status", "missing"),
        "image_motion_qc_claim_status": image_qc.get("claim_status"),
        "image_motion_qc_unstable_high_burden_exclusion_count": image_unstable,
        "published_motion_qc_status": published_qc.get("analysis_status", "missing"),
        "design_confound_status": design.get("analysis_status", "missing"),
        "source_paths": {
            "motion_confound": motion_path.relative_to(repo_root).as_posix() if motion_path.exists() else None,
            "module_dvars": module_dvars_path.relative_to(repo_root).as_posix() if module_dvars_path.exists() else None,
            "image_motion_qc": image_qc_path.relative_to(repo_root).as_posix() if image_qc_path.exists() else None,
            "published_motion_qc": published_qc_path.relative_to(repo_root).as_posix() if published_qc_path.exists() else None,
            "design_confound": design_path.relative_to(repo_root).as_posix() if design_path.exists() else None,
        },
        "claim_guardrail": (
            "This gate is deliberately stricter than Schaefer/Yeo sensitivity. Final C claims require "
            "motion-sensitive exclusion evidence, not only parcellation stability."
        ),
        "next_action": (
            "Supply authorized subject/run fMRIPrep FD, DVARS, and censor/outlier confounds, rerun the "
            "motion-confound control, then refresh the thesis evidence loop."
        ),
    }

def build_literature_benchmark_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    output_dir = repo_root / "results" / "literature_benchmark"
    summary = _load_json(repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json")
    if summary is None:
        payload = {
            "schema_version": 1,
            "generated_at_utc": _now(),
            "analysis_status": "blocked_missing_dynamic_summary",
            "blocker": "Run scripts/run_dynamic_mechanism_ranking.py first.",
            "source_reference": external_source_by_id("girn_2026_mega_analysis"),
        }
    else:
        robustness = build_dynamic_robustness_summary(summary, repo_root / "results" / "stage_2" / "empirical_viewer")
        benchmark = robustness.get("literature_benchmark", {})
        rows = list(benchmark.get("rows", []))

        def _is_striatal_row(row: dict[str, Any]) -> bool:
            return (
                "striatal" in str(row.get("benchmark", "")).lower()
                or "striat" in str(row.get("project_metric", "")).lower()
            )

        striatal_context: dict[str, Any] | None = None
        striatal_summary_path = (
            repo_root
            / "results"
            / "parcellation_sensitivity"
            / "schaefer_100_yeo_7_striatal"
            / "summary.json"
        )
        if striatal_summary_path.exists():
            striatal_summary = _load_json(striatal_summary_path) or {}
            striatal_benchmark = literature_benchmark_from_summary(striatal_summary)
            measurable_striatal_rows = [
                {
                    **row,
                    "benchmark_context": "schaefer_100_yeo_7_striatal",
                    "summary_path": striatal_summary_path.relative_to(repo_root).as_posix(),
                }
                for row in striatal_benchmark.get("rows", [])
                if isinstance(row, dict)
                and _is_striatal_row(row)
                and row.get("observed_mean_delta") is not None
            ]
            if measurable_striatal_rows:
                rows = [row for row in rows if not _is_striatal_row(row)] + measurable_striatal_rows
                striatal_context = {
                    "parcellation_id": "schaefer_100_yeo_7_striatal",
                    "summary_path": striatal_summary_path.relative_to(repo_root).as_posix(),
                    "row_statuses": [row.get("status") for row in measurable_striatal_rows],
                }
        striatal_rows = [
            row
            for row in rows
            if _is_striatal_row(row)
        ]
        striatal_testable = any(row.get("observed_mean_delta") is not None for row in striatal_rows)
        aligned_count = sum(row.get("sign_match") is True for row in rows)
        measurable_count = sum(row.get("sign_match") is not None for row in rows)
        payload = {
            "schema_version": 1,
            "generated_at_utc": _now(),
            "analysis_status": "implemented_directional_proxy_benchmark",
            "source_reference": external_source_by_id("girn_2026_mega_analysis"),
            "aligned_count": aligned_count,
            "measurable_count": measurable_count,
            "alignment_fraction": float(aligned_count / measurable_count) if measurable_count else 0.0,
            "rows": rows,
            "claim_guardrail": benchmark.get("claim_guardrail"),
            "striatal_unimodal_gate": {
                "analysis_status": (
                    "implemented_striatal_unimodal_proxy_benchmark"
                    if striatal_testable
                    else "blocked_missing_striatal_or_subcortical_parcels"
                ),
                "row_count": len(striatal_rows),
                "parcellation_context": striatal_context,
                "required_regions": ["caudate", "putamen", "nucleus_accumbens_or_striatum"],
                "current_status": (
                    "A Schaefer100/Yeo7 + Harvard-Oxford striatal proxy benchmark row is measurable."
                    if striatal_testable
                    else (
                        "Current 8-module and cortical Schaefer/Yeo proxy layers do not provide a dedicated "
                        "striatal parcel for this benchmark."
                    )
                ),
                "next_action": (
                    "Interpret the striatal row as a bilateral proxy benchmark, not a nucleus-level Nature Medicine reproduction."
                    if striatal_testable
                    else "Add stable striatal parcels before comparing this part of the Nature Medicine result."
                ),
            },
        }
        _write_csv(output_dir / "literature_benchmark.csv", rows)
    payload["source_reference"] = external_source_reference_by_id(
        "girn_2026_mega_analysis",
        payload.get("analysis_status"),
    )
    payload["source_path"] = _write_json(output_dir / "literature_benchmark_status.json", payload)
    return payload

def build_thesis_evidence_loop(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    dynamic_summary = _load_json(repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json")
    c_bootstrap = None
    if dynamic_summary and dynamic_summary.get("robustness", {}).get("subject_bootstrap"):
        for row in dynamic_summary["robustness"]["subject_bootstrap"].get("layer_summary", []):
            if row.get("layer") == "C":
                c_bootstrap = row.get("rank_1_fraction")
                break
    lsd_status = {
        "analysis_status": "implemented_lsd_robustness"
        if dynamic_summary and dynamic_summary.get("robustness", {}).get("analysis_status")
        else "blocked_missing_dynamic_robustness",
        "source_path": "results/dynamic_mechanism_ranking/summary.json",
        "evidence": (
            f"C rank-1 fraction={c_bootstrap}"
            if c_bootstrap is not None
            else "Run scripts/run_dynamic_mechanism_ranking.py first."
        ),
    }
    psilocybin = build_psilocybin_status(repo_root)
    structural = build_structural_connectome_status(repo_root)
    receptor = build_receptor_prior_status(repo_root)
    motion_sensitive_c = build_motion_sensitive_c_gate_status(repo_root)
    parcellation = build_parcellation_sensitivity_status(repo_root)
    literature = build_literature_benchmark_status(repo_root)
    literature_evidence = (
        f"{literature.get('aligned_count', 0)}/{literature.get('measurable_count', 0)} "
        "measurable proxy checks aligned."
    )
    psilocybin_evidence = str(psilocybin.get("blocker") or "Comparable ranking generated.")
    if psilocybin.get("unchanged_scoring_applied"):
        psilocybin_evidence = (
            f"{psilocybin.get('validation_scope', 'validation_scope_unknown')}; "
            f"{psilocybin.get('replication_status', 'replication_status_unknown')}; "
            f"ds006072 top={psilocybin.get('ds006072_top_layer')}, "
            f"LSD reference top={psilocybin.get('lsd_reference_top_layer')}."
        )
    status_rows = [
        _status_row(
            "1",
            "LSD robustness",
            lsd_status["analysis_status"],
            "results/dynamic_mechanism_ranking/robustness/",
            lsd_status["evidence"],
        ),
        _status_row(
            "2",
            "Motion-sensitive C gate",
            motion_sensitive_c["analysis_status"],
            "results/confound_controls/",
            str(motion_sensitive_c.get("evidence", "")),
            str(motion_sensitive_c.get("blocker", "")),
        ),
        _status_row(
            "3",
            "Psilocybin ds006072",
            psilocybin["analysis_status"],
            "results/psilocybin_ds006072/",
            psilocybin_evidence,
        ),
        _status_row(
            "4",
            "HCP structural graph",
            structural["analysis_status"],
            "results/structural_connectome/",
            structural.get(
                "blocker",
                f"Structural graph sensitivity generated; rewires={structural.get('graph_rewire_null_status', 'not_run')}.",
            ),
        ),
        _status_row(
            "5",
            "PET receptor priors",
            receptor["analysis_status"],
            "results/receptor_priors/",
            receptor.get(
                "blocker",
                f"PET receptor sensitivity generated; claim gate={receptor.get('claim_promotion_status', 'unknown')}.",
            ),
        ),
        _status_row(
            "6",
            "Schaefer/Yeo sensitivity",
            parcellation["analysis_status"],
            "results/parcellation_sensitivity/",
            "Status matrix generated; see per-parcellation rows.",
        ),
        _status_row(
            "7",
            "Mega-analysis comparison",
            literature["analysis_status"],
            "results/literature_benchmark/",
            f"{literature_evidence} Striatal gate={literature.get('striatal_unimodal_gate', {}).get('analysis_status', 'missing')}.",
        ),
    ]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "analysis_status": "implemented_loop_status_artifacts",
        "status_rows": status_rows,
        "components": {
            "lsd_robustness": lsd_status,
            "psilocybin_ds006072": psilocybin,
            "structural_connectome": structural,
            "receptor_priors": receptor,
            "motion_sensitive_c_gate": motion_sensitive_c,
            "parcellation_sensitivity": parcellation,
            "literature_benchmark": literature,
        },
        "claim_guardrail": (
            "Implemented/blocked statuses are evidence. A blocked status means the code path and artifact contract exist, "
            "but the raw local data required for the scientific claim are absent."
        ),
    }
    component_statuses = {
        name: _external_source_component_status(name, component)
        for name, component in payload["components"].items()
        if isinstance(component, dict)
    }
    external_plan = external_source_plan_rows(component_statuses)
    claim_evidence_matrix = _build_claim_evidence_matrix(payload["components"])
    output_dir = repo_root / "results" / "thesis_evidence_loop"
    claim_csv_path = output_dir / "claim_evidence_matrix.csv"
    claim_markdown_path = output_dir / "claim_evidence_matrix.md"
    source_plan_csv_path = output_dir / "external_source_plan.csv"
    source_plan_markdown_path = output_dir / "external_source_plan.md"
    _write_csv(output_dir / "status_rows.csv", status_rows)
    payload["external_source_plan"] = external_plan
    payload["external_source_plan_columns"] = EXTERNAL_SOURCE_PLAN_COLUMNS
    payload["external_source_plan_paths"] = {
        "csv": source_plan_csv_path.relative_to(repo_root).as_posix(),
        "markdown": source_plan_markdown_path.relative_to(repo_root).as_posix(),
    }
    payload["claim_evidence_matrix"] = claim_evidence_matrix
    payload["claim_evidence_matrix_columns"] = CLAIM_EVIDENCE_COLUMNS
    payload["claim_evidence_matrix_paths"] = {
        "csv": claim_csv_path.relative_to(repo_root).as_posix(),
        "markdown": claim_markdown_path.relative_to(repo_root).as_posix(),
    }
    _write_csv(
        claim_csv_path,
        claim_evidence_matrix,
        CLAIM_EVIDENCE_COLUMNS,
    )
    _write_markdown_table(
        claim_markdown_path,
        claim_evidence_matrix,
        CLAIM_EVIDENCE_COLUMNS,
    )
    _write_csv(
        source_plan_csv_path,
        external_plan,
        EXTERNAL_SOURCE_PLAN_COLUMNS,
    )
    _write_markdown_table(
        source_plan_markdown_path,
        external_plan,
        EXTERNAL_SOURCE_PLAN_COLUMNS,
    )
    payload["source_path"] = _write_json(output_dir / "thesis_evidence_loop_status.json", payload)
    return payload
