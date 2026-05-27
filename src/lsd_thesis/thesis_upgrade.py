from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "thesis_upgrade_status.v1"


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


def _motion_gate(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "results" / "setting_seed" / "motion" / "motion_summary.json"
    payload = _read_json(path) or {}
    ready = bool(payload.get("motion_analysis_ready"))
    files_present = bool(payload.get("motion_files_present"))
    status = str(payload.get("status") or ("ready" if ready else "blocked_missing_motion_summaries"))
    blocker = (
        "Subject/session/run motion summaries are parsed and ready."
        if ready
        else "No structured subject/session/run confounds with FD/DVARS/censoring coverage are available locally."
    )
    return {
        "gate": _gate(
            "Motion and confounds",
            status,
            ready,
            _rel(path, repo_root),
            blocker,
            1.0 if ready else 0.25 if files_present else 0.0,
        ),
        "required_columns": [
            "framewise_displacement",
            "dvars or std_dvars",
            "motion_outlier_* or censor/scrub indicators",
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
    ready = canonical_status.startswith("implemented")
    blocker = (
        "Canonical Schaefer/Yeo extraction and ranking are available."
        if ready
        else "Canonical Schaefer/Yeo extraction is not yet a completed empirical result."
    )
    return {
        "gate": _gate(
            "Canonical parcellation",
            canonical_status or str(payload.get("analysis_status") or "planned_schaefer_yeo"),
            ready,
            _rel(path, repo_root),
            blocker,
            1.0 if ready else 0.35 if implemented else 0.15,
        ),
        "current_baseline": "harvard_oxford_8_module_proxy",
        "recommended_primary": canonical,
        "recommended_sensitivity": ["schaefer_200_yeo_7", "schaefer_100_yeo_17", "schaefer_200_yeo_17"],
        "engineering_logic": (
            "Use Schaefer parcels as state nodes and Yeo networks as interpretable macro-supernodes; "
            "then test whether mechanism rankings survive the refined state-space."
        ),
        "claim_guardrail": "The 8-module Harvard-Oxford mapping remains a transparent proxy until Schaefer/Yeo extraction is run.",
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
    ingestion_path = repo_root / "results" / "external_ingestion" / "external_ingestion_status.json"
    payload = _read_json(path) or {}
    ingestion = _read_json(ingestion_path) or {}
    ingestion_status = ingestion.get("analysis_status", {}) if isinstance(ingestion.get("analysis_status"), dict) else {}
    status = str(payload.get("analysis_status") or "blocked_missing_local_ds006072_empirical_viewer")
    ready = status.startswith("implemented")
    manifest_ready = ingestion_status.get("ds006072_metadata") == "ready" and ingestion_status.get("ds006072_func_manifest") == "ready"
    extraction_contract_ready = status.startswith("extraction_contract_ready")
    return {
        "gate": _gate(
            "External validation",
            status,
            ready,
            f"{_rel(path, repo_root)}; {_rel(ingestion_path, repo_root)}",
            str(payload.get("blocker") or "Comparable ds006072 psilocybin/control empirical viewer is not complete."),
            1.0 if ready else 0.6 if extraction_contract_ready else 0.45 if manifest_ready else 0.35 if payload else 0.1,
        ),
        "recommended_external_dataset": "OpenNeuro ds006072 psilocybin precision functional mapping",
        "ingestion_status": ingestion_status,
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
        "rocket_strengthening": _rocket_gate(repo_root),
        "external_validation": _external_gate(repo_root),
        "receptor_structural": _receptor_structural_gate(repo_root),
        "reproducible_archive": _archive_gate(repo_root),
    }
    gates = [component["gate"] for component in components.values()]
    ready_count = sum(1 for gate in gates if gate["ready"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "readiness_summary": {
            "ready_gates": ready_count,
            "total_gates": len(gates),
            "readiness_fraction": ready_count / len(gates) if gates else 0.0,
            "thesis_status": "draft_ready_not_final_defense_ready" if ready_count < len(gates) else "final_claim_gates_ready",
        },
        "gates": gates,
        "components": components,
        "visualization_plan": {
            "dashboard_panels": [
                "readiness gate bar",
                "ROCKET strength radar",
                "motion/QC ribbon",
                "parcellation proxy-vs-canonical board",
                "external/receptor/structural/archive evidence matrix",
                "3D latent and control-landscape panels when source arrays are available",
            ]
        },
        "claim_guardrail": (
            "This status file upgrades evidence visibility. It does not convert proxy analyses into receptor-level, "
            "clinical, subjective-experience, or external-validity proof."
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
