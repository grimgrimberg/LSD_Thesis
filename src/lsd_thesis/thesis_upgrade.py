from __future__ import annotations

import importlib.util
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "thesis_upgrade_status.v1"
MINIMUM_PAIRED_MOTION_CONTROL_ROWS = 4
REQUIRED_MOTION_CONTROL_FEATURE_FAMILIES = ("fd", "dvars", "censoring")
REQUIRED_NEUROMAPS_MAP_FAMILIES = ("receptor", "myelin", "functional_gradient", "gene_expression")
STRICT_REQUIREMENT_IDS = (
    "schaefer_yeo_high_resolution",
    "neuromaps_spatial_autocorrelation_nulls",
    "ds006072_external_validation",
    "motion_confound_control_result",
    "receptor_myelin_gradient_claim",
    "project_phase",
)
PACKAGE_REQUIREMENT_IDS = (
    "public_dashboard_static_snapshot",
    "reproducible_archive_publication",
)
READINESS_SNAPSHOT_SUMMARY_KEYS = (
    "strict_complete_gates",
    "strict_total_gates",
    "strict_missing_requirement_ids",
    "remaining_hard_requirements",
    "completion_status",
    "thesis_status",
)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(raw).__name__}.")
    return raw


def _readiness_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    raw_summary = payload.get("readiness_summary")
    summary = raw_summary if isinstance(raw_summary, dict) else {}

    def _rows(key: str, fields: Iterable[str]) -> list[dict[str, Any]]:
        raw_rows = payload.get(key)
        rows = raw_rows if isinstance(raw_rows, list) else []
        return [
            {field: row.get(field) for field in fields}
            for row in rows
            if isinstance(row, dict)
        ]

    gates = [
        row
        for row in _rows("gates", ("label", "status", "ready"))
        if row.get("label") != "Public dashboard"
    ]
    package_requirements = [
        row
        for row in _rows("package_readiness_requirements", ("requirement_id", "status", "complete"))
        if row.get("requirement_id") != "public_dashboard_static_snapshot"
    ]
    return {
        "schema_version": payload.get("schema_version"),
        "readiness_summary": {key: summary.get(key) for key in READINESS_SNAPSHOT_SUMMARY_KEYS},
        "gates": gates,
        "strict_completion_requirements": _rows(
            "strict_completion_requirements",
            ("requirement_id", "status", "complete"),
        ),
        "package_readiness_requirements": package_requirements,
    }


def _rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _evidence_paths(repo_root: Path, *paths: Path) -> str:
    return "; ".join(_rel(path, repo_root) for path in paths)


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


def _package_requirement(
    requirement_id: str,
    label: str,
    status: str,
    complete: bool,
    evidence: str,
    missing: str,
    next_action: str,
    claim_effect: str,
) -> dict[str, Any]:
    if requirement_id not in PACKAGE_REQUIREMENT_IDS:
        raise ValueError(f"Unknown package requirement id: {requirement_id}")
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


def _int_payload_value(payload: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(payload.get(key) or default)
    except (TypeError, ValueError):
        return default


def _motion_feature_family_coverage(rows: Any) -> dict[str, bool]:
    coverage = {family: False for family in REQUIRED_MOTION_CONTROL_FEATURE_FAMILIES}
    if not isinstance(rows, list):
        return coverage
    for row in rows:
        if not isinstance(row, dict):
            continue
        feature = str(row.get("motion_feature") or "").lower()
        if "fd" in feature or "framewise_displacement" in feature:
            coverage["fd"] = True
        if "dvars" in feature:
            coverage["dvars"] = True
        if any(token in feature for token in ("motion_outlier", "outlier", "censor", "scrub", "non_steady_state")):
            coverage["censoring"] = True
    return coverage


def _motion_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "setting_seed" / "motion" / "motion_summary.json"
    control_path = repo_root / "results" / "confound_controls" / "motion_confound_control_status.json"
    design_path = repo_root / "results" / "confound_controls" / "design_confound_control_status.json"
    module_dvars_path = repo_root / "results" / "confound_controls" / "module_dvars_control_status.json"
    published_motion_path = repo_root / "results" / "confound_controls" / "published_motion_qc_status.json"
    source_availability_path = repo_root / "results" / "confound_controls" / "ds003059_motion_source_availability.json"
    image_motion_path = repo_root / "results" / "confound_controls" / "image_motion_qc_status.json"
    fmriprep_plan_path = repo_root / "results" / "confound_controls" / "fmriprep_motion_proof_plan.json"
    payload = _read_json(path) or {}
    control_payload = _read_json(control_path) or {}
    design_payload = _read_json(design_path) or {}
    module_dvars_payload = _read_json(module_dvars_path) or {}
    published_motion_payload = _read_json(published_motion_path) or {}
    source_availability_payload = _read_json(source_availability_path) or {}
    image_motion_payload = _read_json(image_motion_path) or {}
    fmriprep_plan_payload = _read_json(fmriprep_plan_path) or {}
    motion_ready = bool(payload.get("motion_analysis_ready"))
    control_status = str(control_payload.get("analysis_status") or "")
    design_status = str(design_payload.get("analysis_status") or "")
    design_ready = bool(design_payload.get("design_confound_control_ready")) and _status_is_implemented(design_status)
    module_dvars_status = str(module_dvars_payload.get("analysis_status") or "")
    module_dvars_ready = bool(module_dvars_payload.get("module_dvars_control_ready")) and _status_is_implemented(module_dvars_status)
    published_motion_status = str(published_motion_payload.get("analysis_status") or "")
    published_motion_ready = bool(published_motion_payload.get("published_motion_qc_ready")) and _status_is_implemented(
        published_motion_status
    )
    image_motion_status = str(image_motion_payload.get("analysis_status") or "")
    image_motion_ready = bool(image_motion_payload.get("image_motion_qc_ready")) and _status_is_implemented(image_motion_status)
    motion_summary_pairing_ready = bool(payload.get("motion_pairing_ready"))
    motion_summary_paired_subject_run_count = _int_payload_value(payload, "paired_subject_run_count")
    motion_summary_minimum_paired_subject_run_count = _int_payload_value(
        payload,
        "minimum_paired_subject_run_count",
        MINIMUM_PAIRED_MOTION_CONTROL_ROWS,
    )
    motion_confound_control_ready = bool(control_payload.get("motion_confound_control_ready"))
    motion_confound_pairing_ready = bool(control_payload.get("motion_pairing_ready"))
    motion_confound_paired_subject_run_count = _int_payload_value(control_payload, "paired_subject_run_count")
    motion_confound_minimum_paired_subject_run_count = _int_payload_value(
        control_payload,
        "minimum_paired_subject_run_count",
        MINIMUM_PAIRED_MOTION_CONTROL_ROWS,
    )
    minimum_paired_motion_control_rows = max(
        motion_summary_minimum_paired_subject_run_count,
        motion_confound_minimum_paired_subject_run_count,
    )
    motion_confound_merged_subject_run_count = _int_payload_value(control_payload, "merged_subject_run_count")
    association_rows = control_payload.get("association_rows")
    motion_confound_has_association_rows = isinstance(association_rows, list) and len(association_rows) > 0
    motion_confound_feature_family_coverage = _motion_feature_family_coverage(association_rows)
    motion_confound_required_feature_families_ready = all(motion_confound_feature_family_coverage.values())
    fmriprep_control_ready = (
        motion_ready
        and motion_summary_pairing_ready
        and motion_summary_paired_subject_run_count >= minimum_paired_motion_control_rows
        and _status_is_implemented(control_status)
        and motion_confound_control_ready
        and motion_confound_pairing_ready
        and motion_confound_paired_subject_run_count >= minimum_paired_motion_control_rows
        and motion_confound_merged_subject_run_count >= minimum_paired_motion_control_rows
        and motion_confound_has_association_rows
        and motion_confound_required_feature_families_ready
    )
    strict_motion_status = (
        control_status
        if fmriprep_control_ready
        else "blocked_missing_fmriprep_fd_dvars_censoring_motion_proof"
    )
    partial_proxy_ready = design_ready and module_dvars_ready
    proxy_control_ready = image_motion_ready or partial_proxy_ready or published_motion_ready or design_ready or module_dvars_ready
    control_ready = fmriprep_control_ready
    files_present = bool(payload.get("motion_files_present"))
    source_availability_status = str(source_availability_payload.get("analysis_status") or "")
    source_availability_checked = bool(source_availability_payload.get("motion_source_availability_ready"))
    source_confounds_available = source_availability_payload.get("source_confounds_available")
    fmriprep_plan_status = str(fmriprep_plan_payload.get("analysis_status") or "")
    fmriprep_plan_ready = bool(fmriprep_plan_payload.get("fmriprep_motion_proof_ready"))
    motion_status = str(payload.get("status") or ("ready" if motion_ready else "blocked_missing_motion_summaries"))
    status = (
        control_status
        if fmriprep_control_ready
        else image_motion_status
        if image_motion_ready
        else "implemented_published_fd_context_and_proxy_controls_missing_subject_level_fd"
        if partial_proxy_ready and published_motion_ready
        else "implemented_design_and_module_dvars_controls_missing_fd_motion"
        if partial_proxy_ready
        else "implemented_published_fd_context_missing_subject_level_fd"
        if published_motion_ready
        else "implemented_design_confound_controls_missing_fd_dvars_motion"
        if design_ready
        else "implemented_module_dvars_controls_missing_fd_motion"
        if module_dvars_ready
        else "blocked_missing_dedicated_motion_confound_control_result"
        if motion_ready
        else motion_status
    )
    blocker = (
        "Subject/session/run motion summaries and a confound-control sensitivity result are available."
        if fmriprep_control_ready
        else "Raw-BOLD image-derived motion/QC sensitivity is implemented; fMRIPrep FD/DVARS/censoring remains the preferred future gold-standard control."
        if image_motion_ready
        else (
            "Published ds003059 FD/scrubbing QC context plus local run/design and "
            "module-DVARS proxy controls are implemented, but subject-level FD/DVARS "
            "confounds are unavailable."
        )
        if partial_proxy_ready and published_motion_ready
        else "Run/session/global-signal and module-DVARS/censoring proxy controls are implemented, but fMRIPrep FD motion summaries are unavailable."
        if partial_proxy_ready
        else "Published aggregate FD/scrubbing QC context is available, but no subject-level FD/DVARS/censoring motion-control result is available."
        if published_motion_ready
        else "Run/session/global-signal design controls are implemented, but no FD/DVARS/censoring motion summaries are available."
        if design_ready
        else "Module-derived DVARS/censoring controls are implemented, but no fMRIPrep FD motion summaries are available."
        if module_dvars_ready
        else "No dedicated result proves that LSD-placebo dynamic effects survive FD/DVARS/censoring sensitivity controls."
        if motion_ready
        else str(source_availability_payload.get("conclusion"))
        if source_availability_checked and source_confounds_available is False
        else "No structured subject/session/run confounds with FD/DVARS/censoring coverage are available locally."
    )
    motion_evidence = _evidence_paths(
        repo_root,
        path,
        control_path,
        design_path,
        module_dvars_path,
        published_motion_path,
        source_availability_path,
        image_motion_path,
        fmriprep_plan_path,
    )
    strict_motion_missing = (
        (
            "Motion-control status is implemented-looking, but strict completion requires "
            "motion_confound_control_ready=true, motion_pairing_ready=true, "
            f"at least {minimum_paired_motion_control_rows} paired LSD/placebo subject/run rows, "
            f"at least {minimum_paired_motion_control_rows} merged dynamic-motion rows, "
            "and association rows spanning FD, DVARS, and censor/outlier feature families."
        )
        if control_status and _status_is_implemented(control_status) and motion_ready and not fmriprep_control_ready
        else
        (
            "Raw-BOLD image-derived motion/QC sensitivity is implemented, but strict completion still requires "
            f"fMRIPrep FD/DVARS/censoring motion proof. fMRIPrep preflight status: {fmriprep_plan_status}."
        )
        if image_motion_ready and not fmriprep_control_ready and fmriprep_plan_status
        else (
            "Raw-BOLD image-derived motion/QC sensitivity is implemented, but "
            "strict completion still requires fMRIPrep FD/DVARS/censoring motion proof."
        )
        if image_motion_ready and not fmriprep_control_ready
        else
        (
            "A source-availability check found no local/OpenNeuro snapshot/public derivative subject-level FD/DVARS/censoring confounds; "
            "full motion proof requires authorized fMRIPrep outputs, author-provided confounds, or original raw BIDS plus preprocessing."
        )
        if source_availability_checked and source_confounds_available is False
        else
        (
            "Published aggregate FD/scrubbing context, run/session controls, and "
            "module-DVARS proxy controls exist, but a subject-level FD/DVARS/censoring "
            "motion-control result is still missing."
        )
        if partial_proxy_ready and published_motion_ready
        else "Run/session and module-DVARS proxy controls exist, but a dedicated fMRIPrep FD/DVARS/censoring motion-control result is still missing."
        if partial_proxy_ready
        else "Published aggregate FD/scrubbing context exists, but a subject-level FD/DVARS/censoring motion-control result is still missing."
        if published_motion_ready
        else "Module-DVARS proxy controls exist, but a dedicated fMRIPrep FD/DVARS/censoring motion-control result is still missing."
        if module_dvars_ready
        else "Run/session design controls exist, but a dedicated FD/DVARS/censoring motion-control result is still missing."
        if design_ready
        else "A dedicated confound-control result layer with motion/outlier sensitivity outcomes is missing."
    )
    strict_motion_next_action = (
        str(fmriprep_plan_payload.get("next_action"))
        if fmriprep_plan_status and not fmriprep_control_ready
        else (
            "Supply authorized fMRIPrep outputs or run preprocessing to create "
            "desc-confounds_timeseries.tsv files, then report whether dynamic "
            "effects survive FD, DVARS, censoring, and run/order controls."
        )
        if source_availability_checked and source_confounds_available is False
        else (
            "Parse confounds for every subject/session/run, then report whether dynamic effects "
            "survive FD, DVARS, censoring, and run/order controls."
        )
    )
    return {
        "gate": _gate(
            "Motion and confounds",
            status,
            control_ready,
            motion_evidence,
            blocker,
            1.0
            if fmriprep_control_ready
            else 0.82
            if image_motion_ready
            else 0.65
            if partial_proxy_ready and published_motion_ready
            else 0.55
            if partial_proxy_ready
            else 0.5
            if published_motion_ready
            else 0.45
            if motion_ready
            else 0.4
            if module_dvars_ready
            else 0.35
            if design_ready
            else 0.25
            if files_present
            else 0.0,
        ),
        "strict_requirement": _requirement(
            "motion_confound_control_result",
            "Motion/confound control result",
            strict_motion_status,
            fmriprep_control_ready,
            motion_evidence,
            strict_motion_missing,
            strict_motion_next_action,
            (
                "Motion/confound handling has an image-derived QC proxy layer, but strict thesis "
                "completion still fails without fMRIPrep FD/DVARS/censoring proof."
                if image_motion_ready and not fmriprep_control_ready
                else "Until this passes, motion/confound handling is a framed limitation rather than a proven control."
            ),
        ),
        "motion_summary_ready": motion_ready,
        "motion_summary_pairing_ready": motion_summary_pairing_ready,
        "motion_summary_paired_subject_run_count": motion_summary_paired_subject_run_count,
        "motion_summary_minimum_paired_subject_run_count": motion_summary_minimum_paired_subject_run_count,
        "control_layer_ready": control_ready,
        "proxy_control_layer_ready": proxy_control_ready,
        "fmriprep_motion_control_ready": fmriprep_control_ready,
        "motion_confound_control_ready": motion_confound_control_ready,
        "motion_confound_pairing_ready": motion_confound_pairing_ready,
        "motion_confound_paired_subject_run_count": motion_confound_paired_subject_run_count,
        "motion_confound_minimum_paired_subject_run_count": motion_confound_minimum_paired_subject_run_count,
        "motion_confound_merged_subject_run_count": motion_confound_merged_subject_run_count,
        "motion_confound_has_association_rows": motion_confound_has_association_rows,
        "motion_confound_feature_family_coverage": motion_confound_feature_family_coverage,
        "motion_confound_required_feature_families": list(REQUIRED_MOTION_CONTROL_FEATURE_FAMILIES),
        "motion_confound_required_feature_families_ready": motion_confound_required_feature_families_ready,
        "control_layer_path": _rel(control_path, repo_root),
        "design_confound_control_ready": design_ready,
        "design_confound_control_path": _rel(design_path, repo_root),
        "design_confound_claim_status": design_payload.get("claim_status"),
        "module_dvars_control_ready": module_dvars_ready,
        "module_dvars_control_path": _rel(module_dvars_path, repo_root),
        "module_dvars_claim_status": module_dvars_payload.get("claim_status"),
        "published_motion_qc_ready": published_motion_ready,
        "published_motion_qc_path": _rel(published_motion_path, repo_root),
        "published_motion_claim_status": published_motion_payload.get("claim_status"),
        "published_motion_high_risk_context": published_motion_payload.get("high_risk_motion_context"),
        "motion_source_availability_path": _rel(source_availability_path, repo_root),
        "motion_source_availability_status": source_availability_status,
        "motion_source_confounds_available": source_confounds_available,
        "fmriprep_motion_proof_plan_ready": fmriprep_plan_ready,
        "fmriprep_motion_proof_plan_path": _rel(fmriprep_plan_path, repo_root),
        "fmriprep_motion_proof_plan_status": fmriprep_plan_status or None,
        "fmriprep_motion_proof_plan_blocker": fmriprep_plan_payload.get("blocker"),
        "image_motion_qc_ready": image_motion_ready,
        "image_motion_qc_path": _rel(image_motion_path, repo_root),
        "image_motion_qc_claim_status": image_motion_payload.get("claim_status"),
        "image_motion_qc_high_risk_associations": image_motion_payload.get("high_risk_image_motion_qc_association_count"),
        "image_motion_qc_unstable_exclusions": image_motion_payload.get("unstable_high_burden_exclusion_count"),
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
        "claim_guardrail": (
            "Motion sensitivity is implemented with raw-BOLD image-derived QC proxies when fMRIPrep confounds are absent. "
            "This strengthens the control layer but does not turn the result into a full FD/DVARS/censoring proof."
            if image_motion_ready and not fmriprep_control_ready
            else "Motion sensitivity is not complete until structured confounds are present and parsed. "
            "A negative source-availability check strengthens provenance, but it does not prove motion safety."
        ),
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
    receptor_ready = bool(payload.get("receptor_spatial_nulls_complete"))
    partial_ready = bool(payload.get("partial_spatial_autocorrelation_nulls_complete"))
    receptor_nulls = payload.get("receptor_moran_nulls", {}) if isinstance(payload.get("receptor_moran_nulls"), dict) else {}
    receptor_best = receptor_nulls.get("best_result", {}) if isinstance(receptor_nulls.get("best_result"), dict) else {}
    receptor_results = receptor_nulls.get("results", []) if isinstance(receptor_nulls.get("results"), list) else []
    family_coverage = receptor_nulls.get("family_coverage", {}) if isinstance(receptor_nulls.get("family_coverage"), dict) else {}
    family_coverage_ready = all(
        family_coverage.get(family) is True for family in REQUIRED_NEUROMAPS_MAP_FAMILIES
    )
    ready = (
        _status_is_implemented(status)
        and bool(payload.get("spatial_autocorrelation_nulls_complete"))
        and family_coverage_ready
    )
    rows = cortical_payload.get("alignment_rows", []) if isinstance(cortical_payload.get("alignment_rows"), list) else []
    first_row = rows[0] if rows and isinstance(rows[0], dict) else {}
    current_method = str(first_row.get("method") or "not_run")
    missing = (
        "None: full neuromaps spatial-autocorrelation null family coverage is complete."
        if ready
        else "Required Schaefer100 map-family Moran spatial-null coverage is still incomplete."
        if receptor_ready
        else "neuromaps is installed and its null API imports, but the surface/high-resolution map input manifest and executed null results are missing."
        if null_api_importable
        else "Current map statistics use exact 8-module label permutation, not neuromaps spatial-autocorrelation nulls."
    )
    next_action = (
        "Use the completed spatial-null family as the primary map-prior evidence layer."
        if ready
        else (
            "Complete receptor, myelin, functional-gradient, and gene-expression map-family "
            "coverage in the active high-resolution/surface space, then rerun the same "
            "Moran/spatial-null plus FDR gate family."
        )
        if receptor_ready
        else (
            "Create results/cortical_maps/neuromaps_surface_inputs.json, project "
            "receptor/myelin/gradient maps to Schaefer/Yeo or surface space, run neuromaps "
            "nulls, and FDR-correct the family."
        )
        if null_api_importable
        else "Install/use neuromaps, project maps to the active Schaefer/Yeo or surface space, run spatial nulls, and FDR-correct the resulting family."
    )
    neuromaps_evidence = _evidence_paths(repo_root, path, cortical_path)
    map_family_evidence = (
        f"{_rel(path, repo_root)}; current map method: {current_method}; "
        f"family coverage: {family_coverage or 'none'}; "
        f"best map-family Moran result: {receptor_best or 'none'}"
    )
    return {
        "gate": _gate(
            "Neuromaps spatial nulls",
            status,
            ready,
            neuromaps_evidence,
            "Schaefer100 map-family Moran spatial nulls are complete across receptor, myelin, functional-gradient, and gene-expression priors."
            if ready
            else "Full surface/parcellation spatial-autocorrelation null testing has not been run."
            if not receptor_ready
            else "Partial receptor/myelin/gradient Schaefer100 Moran spatial nulls are run; full family coverage is still missing.",
            1.0
            if ready
            else 0.7
            if receptor_ready
            else 0.6
            if partial_ready
            else 0.55
            if null_api_importable
            else 0.35
            if dependency_available
            else 0.15,
        ),
        "strict_requirement": _requirement(
            "neuromaps_spatial_autocorrelation_nulls",
            "Full neuromaps spatial-autocorrelation nulls",
            status,
            ready,
            map_family_evidence,
            missing,
            next_action,
            (
                (
                    "Spatial-null family coverage is complete, but receptor/myelin/gradient "
                    "alignment remains exploratory because no map-family result passes FDR "
                    "and CI gates."
                )
                if ready
                else "Receptor/myelin/gradient alignment cannot be promoted beyond exploratory until this passes."
            ),
        ),
        "dependency_available": dependency_available,
        "null_api_importable": null_api_importable,
        "receptor_spatial_nulls_complete": receptor_ready,
        "partial_spatial_autocorrelation_nulls_complete": partial_ready,
        "required_map_families": list(REQUIRED_NEUROMAPS_MAP_FAMILIES),
        "family_coverage_ready": family_coverage_ready,
        "best_receptor_moran_result": receptor_best,
        "receptor_moran_summary": {
            "method": receptor_nulls.get("method"),
            "n_perm": receptor_nulls.get("n_perm"),
            "test_count": receptor_nulls.get("test_count"),
            "fdr_supported_count": receptor_nulls.get("fdr_supported_count"),
            "family_coverage": receptor_nulls.get("family_coverage"),
        },
        "receptor_moran_results": receptor_results,
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
    has_permutation_null = isinstance(payload.get("permutation_null"), dict)
    has_calibration = isinstance(payload.get("calibration"), dict)
    has_transform_variant = any(
        isinstance(payload.get(key), dict) for key in ("minirocket", "multirocket")
    ) or "minirocket" in str(payload.get("model", "")).lower() or "multirocket" in str(payload.get("model", "")).lower()
    ba = aggregate.get("balanced_accuracy_mean")
    auc = aggregate.get("roc_auc_mean")
    internal_integrity_ready = bool(has_subject_disjoint and has_run_aggregation and has_no_window_random and ba is not None)
    thesis_strength_ready = bool(
        internal_integrity_ready
        and has_permutation_null
        and has_calibration
        and has_transform_variant
    )
    score = (
        0.35 * float(has_subject_disjoint)
        + 0.25 * float(has_run_aggregation)
        + 0.15 * float(has_no_window_random)
        + 0.1 * float((float(ba) if ba is not None else 0.5) > 0.6)
        + 0.05 * float(has_permutation_null)
        + 0.05 * float(has_calibration)
        + 0.05 * float(has_transform_variant)
    )
    return {
        "gate": _gate(
            "ROCKET benchmark",
            "strong_ml_evidence_ready"
            if thesis_strength_ready
            else "supporting_internal_signal"
            if internal_integrity_ready
            else "blocked_or_not_run",
            thesis_strength_ready,
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
        "internal_integrity_ready": internal_integrity_ready,
        "thesis_strength_ready": thesis_strength_ready,
        "strengthening_coverage": {
            "subject_disjoint_cv": has_subject_disjoint,
            "subject_session_run_aggregation": has_run_aggregation,
            "no_window_random_reporting": has_no_window_random,
            "permutation_null": has_permutation_null,
            "calibration": has_calibration,
            "minirocket_or_multirocket_variant": has_transform_variant,
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


def _public_dashboard_gate(repo_root: Path) -> dict[str, Any]:
    site_root = repo_root / "_site"
    current_status_path = repo_root / "results" / "thesis_upgrade" / "thesis_upgrade_status.json"
    manifest_path = site_root / "pages_manifest.json"
    index_path = site_root / "index.html"
    dashboard_data_path = site_root / "dashboard" / "dashboard-data.json"
    thesis_status_path = site_root / "artifacts" / "results" / "thesis_upgrade" / "thesis_upgrade_status.json"
    archive_manifest_path = site_root / "artifacts" / "results" / "reproducible_archive" / "ARCHIVE_MANIFEST.json"
    current_status = _read_json(current_status_path) or {}
    site_status = _read_json(thesis_status_path) or {}
    dashboard_payload = _read_json(dashboard_data_path) or {}
    raw_dashboard_status = dashboard_payload.get("thesis_upgrade") if isinstance(dashboard_payload, dict) else None
    dashboard_status = raw_dashboard_status if isinstance(raw_dashboard_status, dict) else {}
    manifest = _read_json(manifest_path) or {}
    raw_entrypoints = manifest.get("entrypoints")
    entrypoints: dict[str, Any] = raw_entrypoints if isinstance(raw_entrypoints, dict) else {}
    raw_artifacts = manifest.get("artifacts")
    artifacts: list[Any] = raw_artifacts if isinstance(raw_artifacts, list) else []
    required_paths = (
        index_path,
        dashboard_data_path,
        thesis_status_path,
        archive_manifest_path,
    )
    required_paths_present = {path.relative_to(repo_root).as_posix(): path.exists() for path in required_paths}
    required_manifest_artifacts = (
        "artifacts/results/thesis_upgrade/thesis_upgrade_status.json",
        "artifacts/results/reproducible_archive/ARCHIVE_MANIFEST.json",
    )
    manifest_entrypoints_ready = entrypoints.get("index") == "index.html" and entrypoints.get("dashboard") == "dashboard/index.html"
    manifest_artifacts_ready = all(path in artifacts for path in required_manifest_artifacts)
    current_snapshot = _readiness_snapshot(current_status) if current_status else {}
    site_snapshot = _readiness_snapshot(site_status) if site_status else {}
    dashboard_snapshot = _readiness_snapshot(dashboard_status) if dashboard_status else {}
    artifact_snapshot_current = bool(current_snapshot and site_snapshot == current_snapshot)
    dashboard_snapshot_current = bool(current_snapshot and dashboard_snapshot == current_snapshot)
    snapshot_fresh = artifact_snapshot_current and dashboard_snapshot_current
    ready = bool(
        manifest
        and all(required_paths_present.values())
        and manifest_entrypoints_ready
        and manifest_artifacts_ready
        and snapshot_fresh
    )
    missing_paths = [path for path, present in required_paths_present.items() if not present]
    snapshot_mismatches = []
    if not current_status:
        snapshot_mismatches.append("current thesis status artifact is missing")
    if current_status and not artifact_snapshot_current:
        snapshot_mismatches.append("published thesis status artifact is stale")
    if current_status and not dashboard_snapshot_current:
        snapshot_mismatches.append("dashboard embedded thesis status is stale")
    status = (
        "static_snapshot_ready"
        if ready
        else "static_snapshot_stale"
        if snapshot_mismatches and all(required_paths_present.values()) and manifest_entrypoints_ready and manifest_artifacts_ready
        else "static_snapshot_missing_required_outputs"
    )
    blocker = (
        (
            "Static GitHub Pages dashboard snapshot and key gate/archive artifacts are present "
            "and synchronized with the current readiness artifact. This is presentation evidence, not a citable archive."
        )
        if ready
        else "Rebuild the static GitHub Pages snapshot so dashboard readiness data matches the current thesis status artifact."
        if snapshot_mismatches
        else "Build the static GitHub Pages snapshot with index, dashboard payload, thesis status, and archive manifest artifacts."
    )
    return {
        "gate": _gate(
            "Public dashboard",
            status,
            ready,
            _evidence_paths(repo_root, current_status_path, manifest_path, *required_paths),
            blocker,
            1.0 if ready else 0.65 if manifest and all(required_paths_present.values()) else 0.45 if manifest else 0.1,
        ),
        "static_snapshot_ready": ready,
        "static_snapshot_fresh": snapshot_fresh,
        "manifest_path": _rel(manifest_path, repo_root),
        "current_status_path": _rel(current_status_path, repo_root),
        "required_paths_present": required_paths_present,
        "missing_required_paths": missing_paths,
        "manifest_entrypoints_ready": manifest_entrypoints_ready,
        "manifest_artifacts_ready": manifest_artifacts_ready,
        "artifact_snapshot_current": artifact_snapshot_current,
        "dashboard_snapshot_current": dashboard_snapshot_current,
        "snapshot_mismatches": snapshot_mismatches,
        "claim_guardrail": "The public dashboard is a static presentation layer and does not complete motion proof, external validation, or archive DOI gates.",
    }


def _external_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "psilocybin_ds006072" / "psilocybin_ds006072_status.json"
    readiness_path = repo_root / "results" / "psilocybin_ds006072" / "external_validation_readiness.json"
    comparable_result_path = repo_root / "results" / "psilocybin_ds006072" / "comparable_empirical_validation_summary.json"
    payload_plan_path = repo_root / "results" / "psilocybin_ds006072" / "minimum_payload_plan.json"
    cifti_extraction_path = repo_root / "results" / "psilocybin_ds006072" / "cifti_empirical_extraction_status.json"
    ingestion_path = repo_root / "results" / "external_ingestion" / "external_ingestion_status.json"
    payload = _read_json(path) or {}
    readiness_payload = _read_json(readiness_path) or {}
    comparable_payload = _read_json(comparable_result_path) or {}
    payload_plan = _read_json(payload_plan_path) or {}
    cifti_extraction = _read_json(cifti_extraction_path) or {}
    ingestion = _read_json(ingestion_path) or {}
    ingestion_status = ingestion.get("analysis_status", {}) if isinstance(ingestion.get("analysis_status"), dict) else {}
    status = str(
        comparable_payload.get("analysis_status")
        or payload.get("analysis_status")
        or readiness_payload.get("analysis_status")
        or "blocked_missing_local_ds006072_empirical_viewer"
    )
    scoring_verified = bool(comparable_payload.get("scoring_lock_verified"))
    subject_count = int(comparable_payload.get("subject_count") or 0)
    minimum_subjects = int(comparable_payload.get("minimum_comparable_subjects") or 3)
    ready = (
        _status_is_implemented(status)
        and bool(comparable_payload.get("unchanged_scoring_applied"))
        and scoring_verified
        and subject_count >= minimum_subjects
    )
    manifest_ready = ingestion_status.get("ds006072_metadata") == "ready" and ingestion_status.get("ds006072_func_manifest") == "ready"
    extraction_contract_ready = status.startswith("extraction_contract_ready")
    payload_plan_ready = bool(payload_plan.get("minimum_payload_plan_ready"))
    payloads_local_ready = bool(payload_plan.get("minimum_payloads_local_ready"))
    cifti_viewer_ready = bool(cifti_extraction.get("cifti_empirical_viewer_ready"))
    schaefer100_viewer_ready = bool(
        comparable_payload.get("schaefer100_empirical_viewer_ready")
        or cifti_extraction.get("schaefer100_empirical_viewer_ready")
    )
    stronger_external_validation_ready = bool(
        comparable_payload.get("stronger_external_validation_ready")
        or cifti_extraction.get("stronger_external_validation_ready")
    )
    validation_scope = str(comparable_payload.get("validation_scope") or "")
    blocker = str(
        comparable_payload.get("blocker")
        or payload.get("blocker")
        or readiness_payload.get("blocker")
        or "Comparable ds006072 psilocybin/control empirical viewer is not complete."
    )
    if not ready and payloads_local_ready:
        blocker = (
            "Minimum ds006072 payloads are local and CIFTI extraction is ready, but unchanged comparable scoring has not passed."
            if cifti_viewer_ready
            else "Minimum ds006072 payloads are local but have not yet been extracted into empirical-viewer records or scored unchanged."
        )
    elif not ready and payload_plan_ready:
        blocker = "Minimum ds006072 payload download plan is ready; selected processed CIFTIs still need local download, extraction, and unchanged scoring."
    elif ready and stronger_external_validation_ready:
        replication_status = comparable_payload.get("replication_status") or "scored_without_replication_status"
        ds006072_top_layer = comparable_payload.get("ds006072_top_layer") or "unknown"
        lsd_reference_top_layer = comparable_payload.get("lsd_reference_top_layer") or "unknown"
        blocker = (
            "Schaefer100/Yeo7 ds006072 extraction and unchanged scoring are complete; "
            f"{replication_status}; ds006072 top={ds006072_top_layer}, LSD reference top={lsd_reference_top_layer}."
        )
    elif ready:
        blocker = "Comparable ds006072 empirical records were scored unchanged; upgrade scope if stronger parcellation matching is needed."
    external_evidence = _evidence_paths(
        repo_root,
        path,
        readiness_path,
        comparable_result_path,
        payload_plan_path,
        cifti_extraction_path,
        ingestion_path,
    )
    external_requirement_evidence = _evidence_paths(
        repo_root,
        path,
        readiness_path,
        comparable_result_path,
        payload_plan_path,
        cifti_extraction_path,
    )
    return {
        "gate": _gate(
            "External validation",
            status,
            ready,
            external_evidence,
            blocker,
            1.0
            if ready
            else 0.7
            if payloads_local_ready or cifti_viewer_ready
            else 0.62
            if payload_plan_ready
            else 0.6
            if extraction_contract_ready
            else 0.45
            if manifest_ready
            else 0.35
            if payload
            else 0.1,
        ),
        "strict_requirement": _requirement(
            "ds006072_external_validation",
            "ds006072 psilocybin external validation",
            status,
            ready,
            external_requirement_evidence,
            (
                (
                    "None: ds006072 paired psilocybin/MTP CIFTI records were extracted "
                    "through Schaefer100/Yeo7 cortex parcels and scored unchanged."
                )
                if ready and stronger_external_validation_ready
                else (
                    "None: ds006072 paired psilocybin/MTP CIFTI records were extracted "
                    "and scored unchanged; current scope is a structure-family external "
                    "stress test."
                )
                if ready and cifti_viewer_ready
                else "None: ds006072 paired psilocybin/control empirical records were scored unchanged."
                if ready
                else
                "The repo has a minimum processed-CIFTI payload plan, but not comparable psilocybin/control dynamic extraction scored unchanged."
                if payload_plan_ready
                else "The repo has readiness/provenance, but not comparable psilocybin/control dynamic extraction scored unchanged."
            ),
            (
                "Use this as the stronger parcellation-matched ds006072 evidence layer; keep the small-subject scope visible."
                if ready and stronger_external_validation_ready
                else "Upgrade this from structure-family stress test to a stronger parcellation-matched ds006072 stress test."
                if ready and cifti_viewer_ready
                else "Use the scored ds006072 result as the current external-validation evidence layer."
                if ready
                else
                (
                    "Run the minimum payload download plan, extract paired ds006072 empirical "
                    "viewer records, then apply the locked LSD scoring spec without retuning."
                )
                if payload_plan_ready
                else (
                    "Supply or derive authorized ds006072 processed rest payloads, build "
                    "paired empirical viewer records, then apply the locked LSD scoring spec "
                    "without retuning and with matching scoring hashes."
                )
            ),
            (
                "External validation is implemented as a ds006072 Schaefer100/Yeo7 parcellation-matched stress test with unchanged scoring."
                if ready and stronger_external_validation_ready
                else "External validation is implemented as a ds006072 structure-family stress test with unchanged scoring."
                if ready and cifti_viewer_ready
                else "External validation is implemented with unchanged ds006072 scoring."
                if ready
                else "External validation remains absent until comparable ds006072 scoring exists."
            ),
        ),
        "recommended_external_dataset": "OpenNeuro ds006072 psilocybin precision functional mapping",
        "ingestion_status": ingestion_status,
        "primary_subjects_local_ready": readiness_payload.get("primary_subjects_local_ready"),
        "primary_subject_count": readiness_payload.get("primary_subject_count"),
        "scoring_lock_verified": scoring_verified,
        "comparable_subject_count": subject_count,
        "minimum_comparable_subjects": minimum_subjects,
        "minimum_payload_plan_ready": payload_plan_ready,
        "minimum_payloads_local_ready": payloads_local_ready,
        "minimum_payload_plan_path": _rel(payload_plan_path, repo_root),
        "minimum_payload_selected_subject_count": payload_plan.get("selected_subject_count"),
        "minimum_payload_selected_total_size_bytes": payload_plan.get("selected_total_size_bytes"),
        "cifti_empirical_viewer_ready": cifti_viewer_ready,
        "schaefer100_empirical_viewer_ready": schaefer100_viewer_ready,
        "stronger_external_validation_ready": stronger_external_validation_ready,
        "validation_scope": validation_scope,
        "cifti_empirical_extraction_path": _rel(cifti_extraction_path, repo_root),
        "cifti_empirical_module_contract": cifti_extraction.get("module_contract"),
        "schaefer100_module_contract": cifti_extraction.get("schaefer100_module_contract"),
        "replication_status": comparable_payload.get("replication_status"),
        "ds006072_top_layer": comparable_payload.get("ds006072_top_layer"),
        "lsd_reference_top_layer": comparable_payload.get("lsd_reference_top_layer"),
        "comparable_result_path": _rel(comparable_result_path, repo_root),
        "fixed_rule": "Run the same LSD scoring rules on psilocybin/control data without retuning after seeing results.",
        "claim_guardrail": (
            "Metadata and manifests are not external validation. Comparable ds006072 scoring is an external stress "
            "test, not population or clinical validation; top-layer mismatches are negative/partial evidence."
        ),
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
    ready = structural_ready and receptor_ready and structural_ingested and receptor_ingested
    blocker = (
        (
            "Documented structural-connectome graph sensitivity and PET-derived receptor-prior "
            "sensitivity are implemented with null/control context; keep biological mechanism "
            "promotion governed by the separate receptor/myelin/gradient claim gate."
        )
        if ready
        else (
            "Need implemented and ingested structural-connectome graph plus PET-derived receptor prior "
            "with null controls."
        )
    )
    claim_guardrail = (
        (
            "Structural and receptor-prior layers are implemented sensitivity controls, not receptor-level, "
            "clinical, or subjective-experience proof."
        )
        if ready
        else "E is proxy-only until structural and receptor priors are both implemented with null controls."
    )
    return {
        "gate": _gate(
            "Receptor + structural control",
            "fully_integrated" if ready else "proxy_or_blocked",
            ready,
            f"{_rel(structural_path, repo_root)}; {_rel(receptor_path, repo_root)}; {_rel(ingestion_path, repo_root)}",
            blocker,
            0.35 * float(structural_ready)
            + 0.35 * float(receptor_ready)
            + 0.15 * float(structural_ingested)
            + 0.15 * float(receptor_ingested),
        ),
        "structural_status": structural_status,
        "receptor_status": receptor_status,
        "ingestion_status": ingestion_status,
        "structural_ingested": structural_ingested,
        "receptor_ingested": receptor_ingested,
        "required_structural_input": "CSV edge list or square matrix aligned to active parcellation nodes.",
        "required_receptor_input": "PET-derived 5-HT2A/FS5ht map projected to the active parcellation.",
        "null_controls": ["uniform", "degree", "random prior", "spatial/autocorrelation-preserving null"],
        "claim_guardrail": claim_guardrail,
    }


def _receptor_myelin_gradient_claim_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "cortical_maps" / "cortical_map_alignment_status.json"
    falsification_path = repo_root / "results" / "cortical_maps" / "map_prior_falsification_status.json"
    payload = _read_json(path) or {}
    falsification = _read_json(falsification_path) or {}
    raw_claim_readiness = payload.get("claim_readiness", {})
    claim_readiness = dict(raw_claim_readiness) if isinstance(raw_claim_readiness, dict) else {}
    raw_neuromaps_status = payload.get("neuromaps_status", {})
    neuromaps_status = dict(raw_neuromaps_status) if isinstance(raw_neuromaps_status, dict) else {}
    strong_claim_status = str(claim_readiness.get("strong_receptor_myelin_gradient_claim") or "not_supported_yet")
    fdr_supported_count = int(payload.get("fdr_supported_count") or 0)
    best = payload.get("best_alignment", {}) if isinstance(payload.get("best_alignment"), dict) else {}
    negative_result_ready = bool(falsification.get("negative_result_ready"))
    claim_resolution = falsification.get("claim_resolution", {}) if isinstance(falsification.get("claim_resolution"), dict) else {}
    spatial_nulls = falsification.get("spatial_nulls", {}) if isinstance(falsification.get("spatial_nulls"), dict) else {}
    resolved_negative = negative_result_ready and str(falsification.get("claim_status")) == "resolved_negative_not_promoted"
    ready = (strong_claim_status not in {"not_supported_yet", "exploratory_not_supported_yet"} and fdr_supported_count > 0) or resolved_negative
    status = "supported" if ready and not resolved_negative else "resolved_negative_not_promoted" if resolved_negative else strong_claim_status
    if resolved_negative:
        claim_readiness.update(
            {
                "strong_receptor_myelin_gradient_claim": status,
                "current_best_result": (
                    "The completed module-level and Schaefer100 spatial-null evidence resolves the "
                    "receptor/myelin/gradient family as a negative/control result under the current support rule."
                ),
                "required_for_stronger_claim": [
                    "Do not promote receptor/myelin/gradient mechanism claims from the current evidence.",
                    (
                        "Future promotion would require new independent evidence with FDR support and "
                        "confidence intervals excluding zero under the same spatial-null support rule."
                    ),
                ],
                "claim_boundary": (
                    "The dashboard may show these maps as tested priors, but the resolved current claim is "
                    "negative/control evidence rather than a supported biological mechanism."
                ),
            }
        )
    spatial_nulls_complete = bool(
        claim_resolution.get("spatial_autocorrelation_nulls_complete")
        or spatial_nulls.get("spatial_autocorrelation_nulls_complete")
    )
    if resolved_negative and spatial_nulls_complete:
        neuromaps_status.update(
            {
                "analysis_status": str(
                    spatial_nulls.get("analysis_status")
                    or "implemented_schaefer100_full_map_family_moran_spatial_nulls"
                ),
                "spatial_autocorrelation_nulls_complete": True,
                "family_coverage_complete": bool(claim_resolution.get("family_coverage_complete")),
                "claim_guardrail": (
                    "Schaefer100 spatial-null evidence is complete for the current map-prior family; "
                    "it resolves the claim as negative/control evidence, not as a supported mechanism."
                ),
            }
        )
    blocker = (
        "At least one receptor/myelin/gradient alignment passes the configured uncertainty gates."
        if ready and not resolved_negative
        else (
            "The map-prior claim is resolved as a negative control: do not promote "
            "receptor/myelin/gradient mechanism claims from this dataset."
        )
        if resolved_negative
        else "Map-prior negative result is formalized; the mechanism claim remains not_supported_yet."
        if negative_result_ready
        else "Current receptor/myelin/gradient alignments are exploratory priors; q-values do not pass FDR and CIs overlap zero."
    )
    claim_evidence = _evidence_paths(repo_root, path, falsification_path)
    return {
        "gate": _gate(
            "Receptor/myelin/gradient claim",
            status,
            ready,
            claim_evidence,
            blocker,
            1.0 if ready else 0.45 if payload else 0.1,
        ),
        "strict_requirement": _requirement(
            "receptor_myelin_gradient_claim",
            "Receptor/myelin/gradient claim resolution",
            status,
            ready,
            claim_evidence,
            (
                "None: the claim is resolved as a negative/control result and is not promoted as a mechanism claim."
                if resolved_negative
                else (
                    "The map-prior negative result is formalized: no module-level or "
                    "spatial-null family FDR support, and the best spatial-null CI crosses zero."
                )
                if negative_result_ready
                else "The strongest current map alignment remains exploratory: no FDR pass and CI overlap with zero."
            ),
            (
                (
                    "Use the negative map-prior result as a guardrail: keep "
                    "receptor/myelin/gradient as future hypotheses, not current claims."
                )
                if resolved_negative
                else (
                    "Promote the claim only after high-resolution parcellation, neuromaps "
                    "spatial nulls, FDR pass, and uncertainty intervals that do not cross zero."
                )
            ),
            (
                "The thesis no longer depends on an unsupported receptor/myelin/gradient claim; the result is a completed negative control."
                if resolved_negative
                else "The dashboard must keep this as not_supported_yet until those gates pass."
            ),
        ),
        "claim_readiness": claim_readiness,
        "neuromaps_status": neuromaps_status,
        "fdr_supported_count": fdr_supported_count,
        "best_alignment": best,
        "negative_result_ready": negative_result_ready,
        "negative_result_path": _rel(falsification_path, repo_root),
        "negative_result_claim_effect": falsification.get("claim_effect"),
        "claim_resolution": claim_resolution,
        "claim_guardrail": "External map priors are useful hypotheses, not proof of receptor/myelin/gradient mechanism.",
    }


def _archive_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "reproducible_archive" / "ARCHIVE_MANIFEST.json"
    payload = _read_json(path) or {}
    manifest_ready = bool(payload.get("artifact_count"))
    release_url = str(payload.get("release_url") or "")
    doi = str(payload.get("doi") or "")
    raw_publication_metadata = payload.get("publication_metadata")
    publication_metadata: dict[str, Any] = (
        raw_publication_metadata if isinstance(raw_publication_metadata, dict) else {}
    )
    release_url_valid = publication_metadata.get("release_url_valid") is True
    doi_valid = publication_metadata.get("doi_valid") is True
    metadata_publication_ready = publication_metadata.get("archive_publication_ready") is True
    publication_ready = (
        payload.get("archive_publication_ready") is True
        and metadata_publication_ready
        and release_url_valid
        and doi_valid
    )
    status = (
        "release_doi_ready"
        if publication_ready
        else "manifest_ready_release_doi_missing"
        if manifest_ready
        else "manifest_not_generated"
    )
    return {
        "gate": _gate(
            "Reproducible archive",
            status,
            publication_ready,
            _rel(path, repo_root),
            (
                "Checksum manifest exists, but thesis-readiness still requires a citable GitHub release and Zenodo DOI."
                if manifest_ready and not publication_ready
                else "Generate the archive manifest, then publish a GitHub release and Zenodo DOI."
                if not publication_ready
                else "Citable GitHub release and Zenodo DOI are recorded."
            ),
            1.0 if publication_ready else 0.55 if manifest_ready else 0.25,
        ),
        "archive_manifest_ready": manifest_ready,
        "archive_publication_ready": publication_ready,
        "archive_publication_metadata": {
            "release_url_valid": release_url_valid,
            "doi_valid": doi_valid,
            "archive_publication_ready": metadata_publication_ready,
        },
        "release_url": release_url or None,
        "doi": doi or None,
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
        "public_dashboard": _public_dashboard_gate(repo_root),
        "external_validation": _external_gate(repo_root),
        "receptor_structural": _receptor_structural_gate(repo_root),
        "receptor_myelin_gradient_claim": _receptor_myelin_gradient_claim_gate(repo_root),
        "reproducible_archive": _archive_gate(repo_root),
    }
    gates = [component["gate"] for component in components.values()]
    public_dashboard = components["public_dashboard"]
    public_dashboard_gate = public_dashboard["gate"]
    reproducible_archive = components["reproducible_archive"]
    reproducible_archive_gate = reproducible_archive["gate"]
    package_requirements = [
        _package_requirement(
            "public_dashboard_static_snapshot",
            "Public dashboard static snapshot",
            str(public_dashboard_gate["status"]),
            bool(public_dashboard_gate["ready"]),
            str(public_dashboard_gate["evidence"]),
            (
                "None: static Pages snapshot contains the required dashboard and evidence artifacts."
                if public_dashboard_gate["ready"]
                else "Static Pages snapshot is stale: {mismatches}.".format(
                    mismatches=", ".join(str(item) for item in public_dashboard.get("snapshot_mismatches", []))
                    or "readiness snapshot mismatch"
                )
                if public_dashboard.get("snapshot_mismatches")
                else "Static Pages snapshot is missing required dashboard/evidence artifacts: {paths}.".format(
                    paths=", ".join(str(item) for item in public_dashboard.get("missing_required_paths", [])) or "unknown"
                )
            ),
            (
                "Keep rebuilding the static site after gate/status artifact changes."
                if public_dashboard_gate["ready"]
                else (
                    "Run scripts/build_github_pages.py after regenerating results/thesis_upgrade/thesis_upgrade_status.json, "
                    "then verify _site embeds the same readiness summary and requirement states."
                )
                if public_dashboard.get("snapshot_mismatches")
                else "Run scripts/build_github_pages.py and verify _site/pages_manifest.json includes the dashboard and evidence artifacts."
            ),
            (
                "The public dashboard is presentation-ready, but remains separate from citable archive publication."
                if public_dashboard_gate["ready"]
                else "Public presentation remains incomplete until the static dashboard snapshot is regenerated."
            ),
        ),
        _package_requirement(
            "reproducible_archive_publication",
            "Reproducible archive publication",
            str(reproducible_archive_gate["status"]),
            bool(reproducible_archive.get("archive_publication_ready")),
            str(reproducible_archive_gate["evidence"]),
            (
                "None: citable GitHub release URL and DOI are recorded in the archive manifest."
                if reproducible_archive.get("archive_publication_ready")
                else "Citable archive publication is missing a validated GitHub release URL and Zenodo DOI."
            ),
            (
                "Keep the archive manifest synchronized with the release and DOI."
                if reproducible_archive.get("archive_publication_ready")
                else (
                    "Create a GitHub release, mint a Zenodo DOI for that release, then rebuild "
                    "scripts/build_reproducible_archive.py with --release-url and --doi."
                )
            ),
            (
                "The package has a citable derived-artifact archive."
                if reproducible_archive.get("archive_publication_ready")
                else "The package is not publication-archive-ready until the release and DOI are recorded."
            ),
        ),
    ]
    strict_requirements = [
        components["canonical_parcellation"]["strict_requirement"],
        components["neuromaps_spatial_nulls"]["strict_requirement"],
        components["external_validation"]["strict_requirement"],
        components["motion_confound"]["strict_requirement"],
        components["receptor_myelin_gradient_claim"]["strict_requirement"],
    ]
    evidence_requirements_complete = all(requirement["complete"] for requirement in strict_requirements)
    non_motion_strict_requirements_complete = all(
        requirement["complete"]
        for requirement in strict_requirements
        if requirement["requirement_id"] != "motion_confound_control_result"
    )
    full_motion_control_ready = bool(components["motion_confound"].get("fmriprep_motion_control_ready"))
    external_validation = components["external_validation"]
    stronger_external_validation_ready = bool(external_validation.get("stronger_external_validation_ready"))
    project_complete = (
        evidence_requirements_complete
        and full_motion_control_ready
        and stronger_external_validation_ready
    )
    proxy_evidence_visible = evidence_requirements_complete or non_motion_strict_requirements_complete
    project_status = (
        "completed_neuroscience_thesis"
        if project_complete
        else "research_demo_ready_not_completed_thesis"
        if proxy_evidence_visible
        else "pi_pitch_ready_research_proposal_not_completed_thesis"
    )
    remaining_hard_requirements = []
    if not full_motion_control_ready:
        remaining_hard_requirements.append("fMRIPrep FD/DVARS/censoring motion proof")
    if not stronger_external_validation_ready:
        remaining_hard_requirements.append("stronger parcellation-matched external validation")
    project_missing = (
        "None: all strict science gates and hard completion requirements are satisfied."
        if project_complete
        else "Proxy/stress-test evidence gates are visible, but completion still requires {requirements}.".format(
            requirements=" and ".join(remaining_hard_requirements)
        )
        if proxy_evidence_visible and remaining_hard_requirements
        else (
            "Proxy/stress-test evidence gates are visible, but hard completion requirements are not fully resolved."
        )
        if proxy_evidence_visible
        else "One or more required scientific gates is still missing or fail-closed."
    )
    project_next_action = (
        "Proceed with final thesis packaging and archive release."
        if project_complete
        else "Keep this as a controlled research demo while upgrading {requirements}.".format(
            requirements=" and ".join(remaining_hard_requirements)
        )
        if proxy_evidence_visible and remaining_hard_requirements
        else (
            "Keep this as a controlled research demo while resolving the remaining hard completion requirements."
        )
        if proxy_evidence_visible
        else "Keep pitching this as an AI/engineering research proposal until every strict evidence gate passes."
    )
    project_claim_effect = (
        "The strict evidence package is complete under the current thesis contract."
        if project_complete
        else "This remains a controlled research demo/PI pitch until {requirements} passes.".format(
            requirements=" and ".join(remaining_hard_requirements)
        )
        if proxy_evidence_visible and remaining_hard_requirements
        else (
            "This remains a controlled research demo/PI pitch, not a completed neuroscience "
            "thesis, until hard motion and external-validation requirements pass."
        )
    )
    strict_requirements.append(
        _requirement(
            "project_phase",
            "Project phase",
            project_status,
            project_complete,
            "strict_completion_requirements",
            project_missing,
            project_next_action,
            project_claim_effect,
        )
    )
    ready_count = sum(1 for gate in gates if gate["ready"])
    strict_ready_count = sum(1 for requirement in strict_requirements if requirement["complete"])
    package_ready_count = sum(1 for requirement in package_requirements if requirement["complete"])
    strict_missing_requirement_ids = [
        str(requirement["requirement_id"]) for requirement in strict_requirements if not requirement["complete"]
    ]
    package_missing_requirement_ids = [
        str(requirement["requirement_id"]) for requirement in package_requirements if not requirement["complete"]
    ]
    completion_status = project_status
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
            "strict_missing_gates": len(strict_missing_requirement_ids),
            "strict_missing_requirement_ids": strict_missing_requirement_ids,
            "package_complete_gates": package_ready_count,
            "package_total_gates": len(package_requirements),
            "package_completion_fraction": package_ready_count / len(package_requirements) if package_requirements else 0.0,
            "package_missing_gates": len(package_missing_requirement_ids),
            "package_missing_requirement_ids": package_missing_requirement_ids,
            "remaining_hard_requirements": remaining_hard_requirements,
            "remaining_packaging_requirements": [
                requirement["label"] for requirement in package_requirements if not requirement["complete"]
            ],
            "completion_status": completion_status,
            "thesis_status": completion_status,
        },
        "gates": gates,
        "strict_completion_requirements": strict_requirements,
        "package_readiness_requirements": package_requirements,
        "components": components,
        "visualization_plan": {
            "dashboard_panels": [
                "thesis gate bar",
                "strict completion audit",
                "ROCKET strength radar",
                "motion/QC ribbon",
                "parcellation proxy-vs-canonical board",
                "public dashboard snapshot integrity gate",
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
        "- Strict completion: {complete}/{total} gates complete.".format(
            complete=status["readiness_summary"]["strict_complete_gates"],
            total=status["readiness_summary"]["strict_total_gates"],
        ),
        "- Package readiness: {complete}/{total} gates complete.".format(
            complete=status["readiness_summary"]["package_complete_gates"],
            total=status["readiness_summary"]["package_total_gates"],
        ),
        "- Missing strict requirement IDs: {missing}.".format(
            missing=", ".join(status["readiness_summary"]["strict_missing_requirement_ids"]) or "none",
        ),
        "- Missing package requirement IDs: {missing}.".format(
            missing=", ".join(status["readiness_summary"]["package_missing_requirement_ids"]) or "none",
        ),
        "- Remaining hard requirements: {requirements}.".format(
            requirements=", ".join(status["readiness_summary"]["remaining_hard_requirements"]) or "none",
        ),
        "- Remaining packaging requirements: {requirements}.".format(
            requirements=", ".join(status["readiness_summary"]["remaining_packaging_requirements"]) or "none",
        ),
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
            "## Package Readiness Audit",
            "",
            "| Requirement | Status | Complete | Missing | Next action |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for requirement in status["package_readiness_requirements"]:
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
