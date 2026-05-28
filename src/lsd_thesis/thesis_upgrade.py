from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "thesis_upgrade_status.v1"
STRICT_REQUIREMENT_IDS = (
    "schaefer_yeo_high_resolution",
    "neuromaps_spatial_autocorrelation_nulls",
    "ds006072_external_validation",
    "motion_confound_control_result",
    "receptor_myelin_gradient_claim",
    "project_phase",
)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(raw).__name__}.")
    return raw


def _rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _gate(label: str, status: str, ready: bool, evidence: str, blocker: str, score: float) -> dict[str, Any]:
    return {
        "label": label,
        "status": status,
        "ready": ready,
        "evidence": evidence,
        "blocker": blocker,
        "score": float(score),
    }


def _requirement(
    requirement_id: str,
    label: str,
    status: str,
    complete: bool,
    evidence: str,
    missing: str,
    next_action: str,
    claim_effect: str,
) -> dict[str, Any]:
    if requirement_id not in STRICT_REQUIREMENT_IDS:
        raise ValueError(f"Unknown strict requirement id: {requirement_id}")
    return {
        "requirement_id": requirement_id,
        "label": label,
        "status": status,
        "complete": bool(complete),
        "evidence": evidence,
        "missing": missing,
        "next_action": next_action,
        "claim_effect": claim_effect,
    }


def _status_is_implemented(status: str) -> bool:
    return status.startswith(("implemented", "validated", "passed", "complete"))


def _motion_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "setting_seed" / "motion" / "motion_summary.json"
    control_path = repo_root / "results" / "confound_controls" / "motion_confound_control_status.json"
    payload = _read_json(path) or {}
    control_payload = _read_json(control_path) or {}
    motion_ready = bool(payload.get("motion_analysis_ready"))
    control_status = str(control_payload.get("analysis_status") or "")
    control_ready = motion_ready and _status_is_implemented(control_status)
    files_present = bool(payload.get("motion_files_present"))
    motion_status = str(payload.get("status") or ("ready" if motion_ready else "blocked_missing_motion_summaries"))
    status = (
        control_status
        if control_ready
        else "blocked_missing_dedicated_motion_confound_control_result"
        if motion_ready
        else motion_status
    )
    blocker = (
        "Subject/session/run motion summaries and a confound-control sensitivity result are available."
        if control_ready
        else "No dedicated result proves that LSD-placebo dynamic effects survive FD/DVARS/censoring sensitivity controls."
        if motion_ready
        else "No structured subject/session/run confounds with FD/DVARS/censoring coverage are available locally."
    )
    return {
        "gate": _gate(
            "Motion and confounds",
            status,
            control_ready,
            f"{_rel(path, repo_root)}; {_rel(control_path, repo_root)}",
            blocker,
            1.0 if control_ready else 0.45 if motion_ready else 0.25 if files_present else 0.0,
        ),
        "strict_requirement": _requirement(
            "motion_confound_control_result",
            "Motion/confound control result",
            status,
            control_ready,
            f"{_rel(path, repo_root)}; {_rel(control_path, repo_root)}",
            "A dedicated confound-control result layer with motion/outlier sensitivity outcomes is missing.",
            "Parse confounds for every subject/session/run, then report whether dynamic effects survive FD, DVARS, censoring, and run/order controls.",
            "Until this passes, motion/confound handling is a framed limitation rather than a proven control.",
        ),
        "motion_summary_ready": motion_ready,
        "control_layer_ready": control_ready,
        "control_layer_path": _rel(control_path, repo_root),
        "required_columns": [
            "framewise_displacement",
            "dvars or std_dvars",
            "motion_outlier_* or censor/scrub indicators",
        ],
        "required_controls": [
            "FD mean/max/spike burden association with each dynamic metric",
            "DVARS mean/max/spike burden association with each dynamic metric",
            "leave-high-motion-subjects-out sensitivity",
            "session/run/order covariate sensitivity",
            "negative-control table showing which claims are downgraded",
        ],
        "recommended_thresholds": {
            "fd_spike_threshold_mm": 0.5,
            "dvars_spike_threshold": 1.5,
            "reporting_unit": "subject/session/run",
        },
        "claim_guardrail": "Motion sensitivity is not complete until structured confounds are present and parsed.",
    }


def _parcellation_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "parcellation_sensitivity" / "parcellation_sensitivity_status.json"
    payload = _read_json(path) or {}
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    implemented = {
        str(row.get("parcellation_id")): str(row.get("analysis_status") or row.get("status") or "")
        for row in rows
        if isinstance(row, dict)
    }
    canonical = "schaefer_100_yeo_7"
    canonical_status = implemented.get(canonical, "")
    candidate_outputs = [
        repo_root
        / "results"
        / "stage_2"
        / "parcellations"
        / canonical
        / "parcellation_extraction_summary.json",
        repo_root
        / "results"
        / "stage_2"
        / "parcellations"
        / canonical
        / "empirical_viewer"
        / "group_overview.json",
        repo_root
        / "results"
        / "stage_2"
        / "empirical_viewer"
        / "parcellations"
        / canonical
        / "overview.json",
        repo_root / "results" / "parcellation_sensitivity" / canonical / "summary.json",
    ]
    observed_outputs = [_rel(candidate, repo_root) for candidate in candidate_outputs if candidate.exists()]
    has_extraction = (repo_root / "results" / "stage_2" / "parcellations" / canonical / "parcellation_extraction_summary.json").exists()
    has_viewer = (repo_root / "results" / "stage_2" / "parcellations" / canonical / "empirical_viewer" / "group_overview.json").exists()
    has_ranking = (repo_root / "results" / "parcellation_sensitivity" / canonical / "summary.json").exists()
    ready = _status_is_implemented(canonical_status) and has_extraction and has_viewer and has_ranking
    blocker = (
        "Canonical Schaefer/Yeo extraction, empirical viewer, and mechanism ranking are available."
        if ready
        else "Canonical Schaefer/Yeo extraction is not yet a completed empirical result with dashboard-visible outputs."
    )
    missing = (
        "None: Schaefer 100/Yeo 7 extraction, empirical viewer, and ranking summary are present."
        if ready
        else "The high-resolution layer is not fully dashboard-visible until extraction, viewer, and ranking outputs all exist."
    )
    next_action = (
        "Use this as the primary high-resolution inference layer and keep Schaefer 200/Yeo 7 plus Yeo 17 variants as sensitivity checks."
        if ready
        else "Run the ds003059 extraction/ranking contract for Schaefer 100/Yeo 7, then repeat sensitivity for Schaefer 200 and Yeo 17."
    )
    claim_effect = (
        "The Schaefer/Yeo parcellation gate is implemented for ds003059; remaining anatomical upgrades now depend on spatial nulls and external validation."
        if ready
        else "Anatomical claims remain explanatory/proxy-level until the Schaefer/Yeo layer is complete."
    )
    return {
        "gate": _gate(
            "Canonical parcellation",
            canonical_status or str(payload.get("analysis_status") or "planned_schaefer_yeo"),
            ready,
            _rel(path, repo_root),
            blocker,
            1.0 if ready else 0.45 if canonical_status else 0.35 if implemented else 0.15,
        ),
        "strict_requirement": _requirement(
            "schaefer_yeo_high_resolution",
            "Schaefer/Yeo high-resolution parcellation layer",
            canonical_status or str(payload.get("analysis_status") or "planned_schaefer_yeo"),
            ready,
            f"{_rel(path, repo_root)}; observed outputs: {', '.join(observed_outputs) if observed_outputs else 'none'}",
            missing,
            next_action,
            claim_effect,
        ),
        "current_baseline": "harvard_oxford_8_module_proxy",
        "recommended_primary": canonical,
        "recommended_sensitivity": ["schaefer_200_yeo_7", "schaefer_100_yeo_17", "schaefer_200_yeo_17"],
        "observed_high_resolution_outputs": observed_outputs,
        "completion_checks": {
            "has_extraction_summary": has_extraction,
            "has_empirical_viewer": has_viewer,
            "has_mechanism_ranking": has_ranking,
        },
        "engineering_logic": (
            "Use Schaefer parcels as state nodes and Yeo networks as interpretable macro-supernodes; "
            "then test whether mechanism rankings survive the refined state-space."
        ),
        "claim_guardrail": (
            "Schaefer/Yeo is implemented for ds003059 high-resolution sensitivity. This resolves the coarse-parcellation gate, "
            "but does not by itself establish receptor, myelin, gradient, psilocybin, or spatial-null claims."
            if ready
            else "The 8-module Harvard-Oxford mapping remains a transparent proxy until Schaefer/Yeo extraction is run."
        ),
    }


def _neuromaps_spatial_null_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "cortical_maps" / "neuromaps_spatial_null_status.json"
    cortical_path = repo_root / "results" / "cortical_maps" / "cortical_map_alignment_status.json"
    payload = _read_json(path) or {}
    cortical_payload = _read_json(cortical_path) or {}
    dependency_available = importlib.util.find_spec("neuromaps") is not None
    runtime = payload.get("neuromaps_runtime", {}) if isinstance(payload.get("neuromaps_runtime"), dict) else {}
    null_api_importable = bool(payload.get("null_api_importable") or runtime.get("null_api_importable"))
    status = str(
        payload.get("analysis_status")
        or (
            "dependency_available_missing_surface_spatial_null_run"
            if dependency_available
            else "blocked_missing_neuromaps_dependency_and_surface_spatial_nulls"
        )
    )
    ready = _status_is_implemented(status) and bool(payload.get("spatial_autocorrelation_nulls_complete"))
    rows = cortical_payload.get("alignment_rows", []) if isinstance(cortical_payload.get("alignment_rows"), list) else []
    first_row = rows[0] if rows and isinstance(rows[0], dict) else {}
    current_method = str(first_row.get("method") or "not_run")
    return {
        "gate": _gate(
            "Neuromaps spatial nulls",
            status,
            ready,
            f"{_rel(path, repo_root)}; {_rel(cortical_path, repo_root)}",
            "Full surface/parcellation spatial-autocorrelation null testing has not been run.",
            1.0 if ready else 0.55 if null_api_importable else 0.35 if dependency_available else 0.15,
        ),
        "strict_requirement": _requirement(
            "neuromaps_spatial_autocorrelation_nulls",
            "Full neuromaps spatial-autocorrelation nulls",
            status,
            ready,
            f"{_rel(path, repo_root)}; current map method: {current_method}",
            (
                "neuromaps is installed and its null API imports, but the surface/high-resolution map input manifest and executed null results are missing."
                if null_api_importable
                else "Current map statistics use exact 8-module label permutation, not neuromaps spatial-autocorrelation nulls."
            ),
            (
                "Create results/cortical_maps/neuromaps_surface_inputs.json, project receptor/myelin/gradient maps to Schaefer/Yeo or surface space, run neuromaps nulls, and FDR-correct the family."
                if null_api_importable
                else "Install/use neuromaps, project maps to the active Schaefer/Yeo or surface space, run spatial nulls, and FDR-correct the resulting family."
            ),
            "Receptor/myelin/gradient alignment cannot be promoted beyond exploratory until this passes.",
        ),
        "dependency_available": dependency_available,
        "null_api_importable": null_api_importable,
        "neuromaps_runtime": runtime,
        "current_map_statistic": current_method,
        "required_nulls": [
            "surface spin/null model where applicable",
            "Moran or variogram-preserving null for parcellated maps",
            "same null family applied before FDR correction",
            "report q-value, FDR pass, and CI overlap with zero",
        ],
        "claim_guardrail": "Exact 8-module permutation is transparent, but it is not a full spatial-autocorrelation null model.",
    }


def _rocket_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "training" / "rocket_condition_benchmark" / "comparison_summary.json"
    payload = _read_json(path) or {}
    aggregate = payload.get("aggregate", {})
    dataset = payload.get("dataset", {})
    rocket = payload.get("rocket", {})
    if not isinstance(aggregate, dict):
        aggregate = {}
    if not isinstance(dataset, dict):
        dataset = {}
    if not isinstance(rocket, dict):
        rocket = {}
    has_subject_disjoint = "subject" in str(payload.get("cv_strategy", "")).lower()
    has_run_aggregation = str(payload.get("primary_evaluation_unit", "")) == "subject_session_run_aggregated_windows"
    has_no_window_random = payload.get("window_random_reporting") is False
    ba = aggregate.get("balanced_accuracy_mean")
    auc = aggregate.get("roc_auc_mean")
    ready = bool(has_subject_disjoint and has_run_aggregation and has_no_window_random and ba is not None)
    score = (
        0.35 * float(has_subject_disjoint)
        + 0.25 * float(has_run_aggregation)
        + 0.15 * float(has_no_window_random)
        + 0.25 * float((float(ba) if ba is not None else 0.5) > 0.6)
    )
    return {
        "gate": _gate(
            "ROCKET benchmark",
            "supporting_internal_signal" if ready else "blocked_or_not_run",
            ready,
            _rel(path, repo_root),
            "Add permutation-null, calibration, and MiniRocket/MultiRocket gates before treating this as strong ML evidence.",
            score,
        ),
        "current_metrics": {
            "balanced_accuracy_mean": ba,
            "balanced_accuracy_std": aggregate.get("balanced_accuracy_std"),
            "roc_auc_mean": auc,
            "roc_auc_std": aggregate.get("roc_auc_std"),
            "subject_count": dataset.get("subject_count"),
            "sample_count": dataset.get("sample_count"),
            "n_kernels": rocket.get("n_kernels"),
            "feature_count": rocket.get("feature_count"),
        },
        "strengthening_requirements": [
            "MiniRocket or MultiRocket transform mode",
            "first-difference channels",
            "fold-internal calibration and feature selection only",
            "label-permutation null distribution",
            "subject/session/run confidence intervals",
            "Brier score and calibration curve",
            "external ds006072 run without score retuning",
        ],
        "claim_guardrail": "ROCKET remains supporting internal proxy evidence until null, calibration, and external gates pass.",
    }


def _external_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "psilocybin_ds006072" / "psilocybin_ds006072_status.json"
    readiness_path = repo_root / "results" / "psilocybin_ds006072" / "external_validation_readiness.json"
    comparable_result_path = repo_root / "results" / "psilocybin_ds006072" / "comparable_empirical_validation_summary.json"
    ingestion_path = repo_root / "results" / "external_ingestion" / "external_ingestion_status.json"
    payload = _read_json(path) or {}
    readiness_payload = _read_json(readiness_path) or {}
    comparable_payload = _read_json(comparable_result_path) or {}
    ingestion = _read_json(ingestion_path) or {}
    ingestion_status = ingestion.get("analysis_status", {}) if isinstance(ingestion.get("analysis_status"), dict) else {}
    status = str(
        comparable_payload.get("analysis_status")
        or payload.get("analysis_status")
        or readiness_payload.get("analysis_status")
        or "blocked_missing_local_ds006072_empirical_viewer"
    )
    ready = _status_is_implemented(status) and bool(comparable_payload.get("unchanged_scoring_applied"))
    manifest_ready = ingestion_status.get("ds006072_metadata") == "ready" and ingestion_status.get("ds006072_func_manifest") == "ready"
    extraction_contract_ready = status.startswith("extraction_contract_ready")
    return {
        "gate": _gate(
            "External validation",
            status,
            ready,
            f"{_rel(path, repo_root)}; {_rel(readiness_path, repo_root)}; {_rel(comparable_result_path, repo_root)}; {_rel(ingestion_path, repo_root)}",
            str(
                comparable_payload.get("blocker")
                or payload.get("blocker")
                or readiness_payload.get("blocker")
                or "Comparable ds006072 psilocybin/control empirical viewer is not complete."
            ),
            1.0 if ready else 0.6 if extraction_contract_ready else 0.45 if manifest_ready else 0.35 if payload else 0.1,
        ),
        "strict_requirement": _requirement(
            "ds006072_external_validation",
            "ds006072 psilocybin external validation",
            status,
            ready,
            f"{_rel(path, repo_root)}; {_rel(readiness_path, repo_root)}; {_rel(comparable_result_path, repo_root)}",
            "The repo has readiness/provenance, but not comparable psilocybin/control dynamic extraction scored unchanged.",
            "Supply or derive authorized ds006072 processed rest payloads, build paired empirical viewer records, then apply the locked LSD scoring spec without retuning.",
            "External validation remains absent until comparable ds006072 scoring exists.",
        ),
        "recommended_external_dataset": "OpenNeuro ds006072 psilocybin precision functional mapping",
        "ingestion_status": ingestion_status,
        "primary_subjects_local_ready": readiness_payload.get("primary_subjects_local_ready"),
        "primary_subject_count": readiness_payload.get("primary_subject_count"),
        "comparable_result_path": _rel(comparable_result_path, repo_root),
        "fixed_rule": "Run the same LSD scoring rules on psilocybin/control data without retuning after seeing results.",
        "claim_guardrail": "Metadata and manifests are not external validation; comparable empirical target extraction is required.",
    }


def _receptor_structural_gate(repo_root: Path) -> dict[str, Any]:
    structural_path = repo_root / "results" / "structural_connectome" / "structural_connectome_status.json"
    receptor_path = repo_root / "results" / "receptor_priors" / "receptor_prior_status.json"
    ingestion_path = repo_root / "results" / "external_ingestion" / "external_ingestion_status.json"
    structural = _read_json(structural_path) or {}
    receptor = _read_json(receptor_path) or {}
    ingestion = _read_json(ingestion_path) or {}
    ingestion_status = ingestion.get("analysis_status", {}) if isinstance(ingestion.get("analysis_status"), dict) else {}
    structural_status = str(structural.get("analysis_status") or "blocked_missing_hcp_structural_graph")
    receptor_status = str(receptor.get("analysis_status") or "blocked_missing_pet_receptor_prior")
    structural_ready = structural_status.startswith("implemented")
    receptor_ready = receptor_status.startswith("implemented")
    structural_ingested = ingestion_status.get("structural_connectome") == "ready"
    receptor_ingested = ingestion_status.get("receptor_prior") == "ready"
    ready = structural_ready and receptor_ready
    return {
        "gate": _gate(
            "Receptor + structural control",
            "fully_integrated" if ready else "proxy_or_blocked",
            ready,
            f"{_rel(structural_path, repo_root)}; {_rel(receptor_path, repo_root)}; {_rel(ingestion_path, repo_root)}",
            "Need both a documented structural-connectome graph and PET-derived receptor prior with null controls.",
            0.35 * float(structural_ready)
            + 0.35 * float(receptor_ready)
            + 0.15 * float(structural_ingested)
            + 0.15 * float(receptor_ingested),
        ),
        "structural_status": structural_status,
        "receptor_status": receptor_status,
        "ingestion_status": ingestion_status,
        "required_structural_input": "CSV edge list or square matrix aligned to active parcellation nodes.",
        "required_receptor_input": "PET-derived 5-HT2A/FS5ht map projected to the active parcellation.",
        "null_controls": ["uniform", "degree", "random prior", "spatial/autocorrelation-preserving null"],
        "claim_guardrail": "E is proxy-only until structural and receptor priors are both implemented with null controls.",
    }


def _receptor_myelin_gradient_claim_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "cortical_maps" / "cortical_map_alignment_status.json"
    payload = _read_json(path) or {}
    claim_readiness = payload.get("claim_readiness", {}) if isinstance(payload.get("claim_readiness"), dict) else {}
    neuromaps_status = payload.get("neuromaps_status", {}) if isinstance(payload.get("neuromaps_status"), dict) else {}
    strong_claim_status = str(claim_readiness.get("strong_receptor_myelin_gradient_claim") or "not_supported_yet")
    fdr_supported_count = int(payload.get("fdr_supported_count") or 0)
    best = payload.get("best_alignment", {}) if isinstance(payload.get("best_alignment"), dict) else {}
    ready = strong_claim_status not in {"not_supported_yet", "exploratory_not_supported_yet"} and fdr_supported_count > 0
    status = "supported" if ready else strong_claim_status
    blocker = (
        "At least one receptor/myelin/gradient alignment passes the configured uncertainty gates."
        if ready
        else "Current receptor/myelin/gradient alignments are exploratory priors; q-values do not pass FDR and CIs overlap zero."
    )
    return {
        "gate": _gate(
            "Receptor/myelin/gradient claim",
            status,
            ready,
            _rel(path, repo_root),
            blocker,
            1.0 if ready else 0.45 if payload else 0.1,
        ),
        "strict_requirement": _requirement(
            "receptor_myelin_gradient_claim",
            "Receptor/myelin/gradient claim support",
            status,
            ready,
            _rel(path, repo_root),
            "The strongest current map alignment remains exploratory: no FDR pass and CI overlap with zero.",
            "Promote the claim only after high-resolution parcellation, neuromaps spatial nulls, FDR pass, and uncertainty intervals that do not cross zero.",
            "The dashboard must keep this as not_supported_yet until those gates pass.",
        ),
        "claim_readiness": claim_readiness,
        "neuromaps_status": neuromaps_status,
        "fdr_supported_count": fdr_supported_count,
        "best_alignment": best,
        "claim_guardrail": "External map priors are useful hypotheses, not proof of receptor/myelin/gradient mechanism.",
    }


def _archive_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "reproducible_archive" / "ARCHIVE_MANIFEST.json"
    payload = _read_json(path) or {}
    ready = bool(payload.get("artifact_count"))
    return {
        "gate": _gate(
            "Reproducible archive",
            "manifest_ready" if ready else "manifest_not_generated",
            ready,
            _rel(path, repo_root),
            "Generate the archive manifest, then publish a GitHub release and Zenodo DOI.",
            0.75 if ready else 0.25,
        ),
        "recommended_publication_stack": ["GitHub repository", "GitHub Pages static snapshot", "GitHub release", "Zenodo DOI"],
        "raw_data_policy": "Do not bundle raw OpenNeuro imaging data; cite dataset IDs and archive derived aggregate artifacts only.",
        "claim_guardrail": "GitHub Pages is a presentation snapshot, not the citable reproducibility archive.",
    }


def build_thesis_upgrade_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    components = {
        "motion_confound": _motion_gate(repo_root),
        "canonical_parcellation": _parcellation_gate(repo_root),
        "neuromaps_spatial_nulls": _neuromaps_spatial_null_gate(repo_root),
        "rocket_strengthening": _rocket_gate(repo_root),
        "external_validation": _external_gate(repo_root),
        "receptor_structural": _receptor_structural_gate(repo_root),
        "receptor_myelin_gradient_claim": _receptor_myelin_gradient_claim_gate(repo_root),
        "reproducible_archive": _archive_gate(repo_root),
    }
    gates = [component["gate"] for component in components.values()]
    strict_requirements = [
        components["canonical_parcellation"]["strict_requirement"],
        components["neuromaps_spatial_nulls"]["strict_requirement"],
        components["external_validation"]["strict_requirement"],
        components["motion_confound"]["strict_requirement"],
        components["receptor_myelin_gradient_claim"]["strict_requirement"],
    ]
    evidence_requirements_complete = all(requirement["complete"] for requirement in strict_requirements)
    strict_requirements.append(
        _requirement(
            "project_phase",
            "Project phase",
            "completed_neuroscience_thesis"
            if evidence_requirements_complete
            else "pi_pitch_ready_research_proposal_not_completed_thesis",
            evidence_requirements_complete,
            "strict_completion_requirements",
            "One or more required scientific gates is still missing or fail-closed.",
            "Keep pitching this as an AI/engineering research proposal until every strict evidence gate passes.",
            "This remains a strong PI pitch, not a completed neuroscience thesis, until all strict gates are true.",
        )
    )
    ready_count = sum(1 for gate in gates if gate["ready"])
    strict_ready_count = sum(1 for requirement in strict_requirements if requirement["complete"])
    completion_status = (
        "completed_neuroscience_thesis"
        if strict_ready_count == len(strict_requirements)
        else "pi_pitch_ready_research_proposal_not_completed_thesis"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "readiness_summary": {
            "ready_gates": ready_count,
            "total_gates": len(gates),
            "readiness_fraction": ready_count / len(gates) if gates else 0.0,
            "strict_complete_gates": strict_ready_count,
            "strict_total_gates": len(strict_requirements),
            "strict_completion_fraction": strict_ready_count / len(strict_requirements) if strict_requirements else 0.0,
            "completion_status": completion_status,
            "thesis_status": completion_status,
        },
        "gates": gates,
        "strict_completion_requirements": strict_requirements,
        "components": components,
        "visualization_plan": {
            "dashboard_panels": [
                "readiness gate bar",
                "strict completion audit",
                "ROCKET strength radar",
                "motion/QC ribbon",
                "parcellation proxy-vs-canonical board",
                "external/receptor/structural/archive evidence matrix",
                "3D latent and control-landscape panels when source arrays are available",
            ]
        },
        "claim_guardrail": (
            "This status file upgrades evidence visibility and fails closed on missing science. It does not convert "
            "proxy analyses into receptor-level, clinical, subjective-experience, or external-validity proof."
        ),
        "source_basis": [
            {
                "topic": "motion confounds",
                "source": "fMRIPrep outputs: framewise displacement, DVARS, motion outliers",
                "url": "https://fmriprep.org/en/23.1.2/outputs.html",
            },
            {
                "topic": "canonical parcellation",
                "source": "Schaefer et al. 2018 local-global parcellation aligned to Yeo networks",
                "url": "https://doi.org/10.1093/cercor/bhx179",
            },
            {
                "topic": "ROCKET strengthening",
                "source": "MiniRocket and MultiRocket time-series classification variants",
                "url": "https://arxiv.org/abs/2012.08791",
            },
            {
                "topic": "brain-map priors",
                "source": "neuromaps reference maps and spatial nulls",
                "url": "https://www.nature.com/articles/s41592-022-01625-w",
            },
            {
                "topic": "archive",
                "source": "GitHub and Zenodo repository DOI workflow",
                "url": "https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content",
            },
        ],
    }


def _markdown(status: dict[str, Any]) -> str:
    lines = [
        "# Thesis Upgrade Status",
        "",
        status["claim_guardrail"],
        "",
        "## Gate Summary",
        "",
        "| Gate | Status | Ready | Score | Blocker / next action |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for gate in status["gates"]:
        lines.append(
            "| {label} | {status} | {ready} | {score:.2f} | {blocker} |".format(
                label=gate["label"],
                status=gate["status"],
                ready=str(gate["ready"]).lower(),
                score=float(gate["score"]),
                blocker=str(gate["blocker"]).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Strict Completion Audit",
            "",
            "| Requirement | Status | Complete | Missing | Next action |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for requirement in status["strict_completion_requirements"]:
        lines.append(
            "| {label} | {status} | {complete} | {missing} | {next_action} |".format(
                label=requirement["label"],
                status=requirement["status"],
                complete=str(requirement["complete"]).lower(),
                missing=str(requirement["missing"]).replace("|", "/"),
                next_action=str(requirement["next_action"]).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Canonical Next State",
            "",
            "- Primary canonical parcellation target: `schaefer_100_yeo_7`.",
            "- Sensitivity targets: `schaefer_200_yeo_7`, `schaefer_100_yeo_17`, `schaefer_200_yeo_17`.",
            "- External validation target: OpenNeuro `ds006072` psilocybin precision functional mapping.",
            "- Receptor/structural target: PET-derived receptor priors plus documented structural-connectome graph in the active parcellation.",
            "- Archive target: GitHub release plus Zenodo DOI, with raw OpenNeuro files cited rather than bundled.",
            "",
        ]
    )
    return "\n".join(lines)


def write_thesis_upgrade_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "thesis_upgrade"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_thesis_upgrade_status(repo_root)
    status_path = output_dir / "thesis_upgrade_status.json"
    report_path = output_dir / "thesis_upgrade_status.md"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    return status
