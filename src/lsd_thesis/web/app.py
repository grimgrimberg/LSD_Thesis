from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Literal, cast

import networkx as nx
import numpy as np
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from lsd_thesis.core import MODULE_GROUPS, GraphConfig, RegimeConfig
from lsd_thesis.data.ds003059 import atlas_label_overlap_rows
from lsd_thesis.data.targets import load_perturbation_target_set, load_sober_target_set
from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import compute_observable_summary
from lsd_thesis.simulator import load_regime_config, run_simulation
from lsd_thesis.subject_split import build_no_subject_validation_boundary

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = Jinja2Templates(directory=str(REPO_ROOT / "src" / "lsd_thesis" / "templates"))
SAFE_EMPIRICAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
RUN02_VIEWER_RELATIVE_PARTS = (
    "results",
    "setting_seed",
    "run02_extraction",
    "stage_2_music",
    "empirical_viewer",
)
RUN02_DATA_AUDIT_RELATIVE_PARTS = (
    "results",
    "setting_seed",
    "run02_extraction",
    "data_audit",
    "data_audit.json",
)
RUN02_EXPLORATORY_CAVEAT = (
    "Run-02 is the music run from the guarded extraction. Motion summaries are unavailable, "
    "so use it for exploratory inspection only, not primary or motion-sensitive claims."
)
ALLOWED_ARTIFACT_ROOTS: tuple[tuple[str, ...], ...] = (
    ("docs", "stage_reports"),
    ("output", "doc"),
    ("results", "stage_1", "figures"),
    ("results", "stage_2", "figures"),
    ("results", "stage_3", "figures"),
    ("results", "stage_4", "figures"),
    ("results", "stage_2b", "figures"),
    ("results", "stage_5", "figures"),
    ("results", "dynamic_mechanism_ranking", "figures"),
    ("results", "dynamic_mechanism_ranking", "exports"),
    ("results", "dynamic_mechanism_ranking", "robustness"),
    ("results", "external_ingestion"),
    ("results", "literature_benchmark"),
    ("results", "parcellation_sensitivity"),
    ("results", "psilocybin_ds006072"),
    ("results", "receptor_priors"),
    ("results", "setting_seed", "dashboard"),
    ("results", "structural_connectome"),
    ("results", "thesis_evidence_loop"),
    ("results", "thesis_upgrade"),
    ("results", "reproducible_archive"),
)
TEMP_ARTIFACT_SUFFIXES = (".bak", ".log", ".old", ".part", ".tmp")
_plotly_js_cache: str | None = None


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    regime: Literal["baseline", "perturbed"] = "baseline"
    within_group_scale: float | None = None
    cross_group_scale: float | None = None
    constraint_scale: float | None = None
    rigidity: float | None = None
    barrier: float | None = None
    temperature: float | None = None
    tau: float | None = None

    @field_validator(
        "within_group_scale", "cross_group_scale", "constraint_scale",
        "rigidity", "barrier", "temperature", "tau",
        mode="before",
    )
    @classmethod
    def _validate_numeric_parameter(cls, value: float | None, info: ValidationInfo) -> float | None:
        if value is None:
            return None
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Parameter must be finite.")
        field_name = str(info.field_name)
        if field_name == "constraint_scale":
            if number < 0.0:
                raise ValueError("constraint_scale must be non-negative.")
        elif number <= 0.0:
            raise ValueError("Parameter must be positive.")
        if field_name == "tau" and number < 0.05:
            raise ValueError("tau is too small for stable interactive simulation (min 0.05).")
        if number > 100.0:
            raise ValueError("Parameter too large (max 100).")
        return number


def _graph_payload(graph: GraphConfig) -> dict[str, Any]:
    network = nx.Graph()
    for module in graph.modules:
        network.add_node(module)
    for i, source in enumerate(graph.modules):
        for j, target in enumerate(graph.modules):
            if i < j and graph.adjacency[i, j] != 0:
                network.add_edge(source, target, weight=float(graph.adjacency[i, j]))
    positions = nx.spring_layout(network, seed=9, weight="weight")

    return {
        "nodes": [
            {
                "name": module,
                "x": float(positions[module][0]),
                "y": float(positions[module][1]),
                "group": MODULE_GROUPS[module],
            }
            for module in graph.modules
        ],
        "edges": [
            {"source": source, "target": target, "weight": float(data["weight"])}
            for source, target, data in network.edges(data=True)
        ],
    }


def build_simulation_payload(graph: GraphConfig, regime: RegimeConfig) -> dict[str, Any]:
    result = run_simulation(graph, regime)
    if not np.all(np.isfinite(result.time_series)):
        raise ValueError("Simulation produced non-finite values; check regime parameters.")
    observable = compute_observable_summary(result.time_series, graph.modules)
    return {
        "time": result.time.tolist(),
        "modules": list(graph.modules),
        "time_series": result.time_series.tolist(),
        "fc_matrix": observable.fc_matrix.tolist(),
        "metrics": observable.metric_map(),
    }


def load_empirical_viewer_overview(viewer_root: Path) -> dict[str, Any] | None:
    group_overview_path = viewer_root / "group_overview.json"
    subject_index_path = viewer_root / "subject_index.json"
    if not group_overview_path.exists():
        return None
    overview = cast(dict[str, Any], json.loads(group_overview_path.read_text(encoding="utf-8")))
    if subject_index_path.exists():
        overview["subject_index"] = cast(
            dict[str, Any], json.loads(subject_index_path.read_text(encoding="utf-8"))
        )
    paired_run_index = _paired_subject_run_index(viewer_root)
    if paired_run_index:
        paired_subjects = sorted(paired_run_index)
        paired_runs = sorted({run for runs in paired_run_index.values() for run in runs})
        overview["subjects"] = paired_subjects
        overview["runs"] = paired_runs
        overview["subject_index"] = paired_run_index
        overview["paired_run_index"] = paired_run_index
        overview["available_pair_count"] = sum(len(runs) for runs in paired_run_index.values())
        if overview.get("default_subject") not in paired_run_index:
            overview["default_subject"] = paired_subjects[0]
    overview.setdefault(
        "display_metadata",
        {
            "preview_kind": "window_averaged_downsampled_slice_preview",
            "preview_normalization": "plane-wise min-max display normalization",
            "window_aggregation": "mean over the selected time window",
            "time_axis_units": "resampled index",
            "claim_guardrail": (
                "Empirical viewer panels are descriptive within-dataset proxy summaries, "
                "not diagnostic images or subjective-state validation."
            ),
        },
    )
    overview.setdefault("condition_labels", {"ses-PLCB": "Placebo", "ses-LSD": "LSD"})
    return overview


def _paired_subject_run_index(viewer_root: Path) -> dict[str, list[str]]:
    subject_views_dir = viewer_root / "subject_views"
    if not subject_views_dir.exists():
        return {}
    subject_index: dict[str, list[str]] = {}
    for detail_path in sorted(subject_views_dir.glob("*.json")):
        if not detail_path.is_file() or "_" not in detail_path.stem:
            continue
        subject, run = detail_path.stem.rsplit("_", 1)
        if not (_is_safe_empirical_selector(subject) and _is_safe_empirical_selector(run)):
            continue
        subject_index.setdefault(subject, []).append(run)
    return {subject: sorted(runs) for subject, runs in sorted(subject_index.items())}


def load_empirical_viewer_detail(
    viewer_root: Path,
    subject: str,
    run: str,
) -> dict[str, Any] | None:
    if not _is_safe_empirical_selector(subject) or not _is_safe_empirical_selector(run):
        return None
    subject_views_dir = (viewer_root / "subject_views").resolve()
    detail_path = (subject_views_dir / f"{subject}_{run}.json").resolve()
    try:
        detail_path.relative_to(subject_views_dir)
    except ValueError:
        return None
    if not detail_path.exists():
        return None
    return cast(dict[str, Any], json.loads(detail_path.read_text(encoding="utf-8")))


def _run02_viewer_root(repo_root: Path) -> Path:
    return repo_root.joinpath(*RUN02_VIEWER_RELATIVE_PARTS)


def _run02_data_audit_path(repo_root: Path) -> Path:
    return repo_root.joinpath(*RUN02_DATA_AUDIT_RELATIVE_PARTS)


def _run_sort_key(run: str) -> tuple[int, int, str]:
    match = re.fullmatch(r"run-(\d+)", run)
    if match:
        return (0, int(match.group(1)), run)
    return (1, 0, run)


def _sorted_runs(runs: list[str] | set[str]) -> list[str]:
    return sorted(set(runs), key=_run_sort_key)


def _load_run02_data_audit(repo_root: Path) -> dict[str, Any]:
    data_audit_path = _run02_data_audit_path(repo_root)
    if not data_audit_path.exists():
        return {}
    return cast(dict[str, Any], json.loads(data_audit_path.read_text(encoding="utf-8")))


def _friendly_run_label(label: Any, run: str) -> str:
    if not isinstance(label, str) or not label:
        return run
    label_map = {
        "Rest1": "Rest 1",
        "Rest3": "Rest 3",
        "Music": "Music (exploratory)",
    }
    return label_map.get(label, label)


def _run02_status(repo_root: Path, run02_viewer_root: Path) -> dict[str, Any]:
    audit = _load_run02_data_audit(repo_root)
    analysis_status = cast(dict[str, Any], audit.get("analysis_status") or {})
    return {
        "available": run02_viewer_root.exists(),
        "analysis_ready": audit.get("run_02_analysis_ready"),
        "files_present": audit.get("run_02_files_present"),
        "valid_file_count": audit.get("run_02_valid_file_count"),
        "expected_file_count": audit.get("run_02_expected_file_count"),
        "record_count": audit.get("record_count"),
        "subject_count": audit.get("subject_count"),
        "music_control": analysis_status.get("music_control"),
        "motion_summaries_available": audit.get("motion_summaries_available"),
        "motion_analysis_ready": audit.get("motion_analysis_ready"),
        "source_path": run02_viewer_root.relative_to(repo_root).as_posix(),
        "data_audit_path": _run02_data_audit_path(repo_root).relative_to(repo_root).as_posix(),
        "claim_guardrail": audit.get("claim_guardrail") or RUN02_EXPLORATORY_CAVEAT,
    }


def _augment_empirical_viewer_with_run02(
    overview: dict[str, Any] | None,
    repo_root: Path,
) -> dict[str, Any] | None:
    if overview is None:
        return None
    run02_viewer_root = _run02_viewer_root(repo_root)
    run02_overview = load_empirical_viewer_overview(run02_viewer_root)
    if run02_overview is None:
        return overview

    run02_subject_index = cast(dict[str, Any], run02_overview.get("subject_index") or {})
    subjects_with_run02 = {
        str(subject)
        for subject, runs in run02_subject_index.items()
        if isinstance(runs, list) and "run-02" in runs
    }
    if not subjects_with_run02:
        return overview

    merged = dict(overview)
    primary_subject_index = cast(dict[str, Any], merged.get("subject_index") or {})
    subject_index: dict[str, list[str]] = {}
    for subject, runs in primary_subject_index.items():
        if not isinstance(runs, list):
            continue
        subject_index[str(subject)] = _sorted_runs([str(run) for run in runs])

    for subject in subjects_with_run02:
        subject_index.setdefault(subject, [])
        if "run-02" not in subject_index[subject]:
            subject_index[subject].append("run-02")
        subject_index[subject] = _sorted_runs(subject_index[subject])

    merged["subjects"] = sorted(subject_index)
    merged["runs"] = _sorted_runs([str(run) for run in merged.get("runs", [])] + ["run-02"])
    merged["default_run"] = "run-02"
    merged["subject_index"] = subject_index
    merged["paired_run_index"] = subject_index
    merged["available_pair_count"] = sum(len(runs) for runs in subject_index.values())
    if merged.get("default_subject") not in subject_index and subject_index:
        merged["default_subject"] = sorted(subject_index)[0]

    audit = _load_run02_data_audit(repo_root)
    audit_run_labels = cast(dict[str, Any], audit.get("run_labels") or {})
    existing_labels = cast(dict[str, Any], merged.get("run_labels") or {})
    run_labels = {str(run): _friendly_run_label(label, str(run)) for run, label in audit_run_labels.items()}
    run_labels.update({str(run): str(label) for run, label in existing_labels.items()})
    run_labels["run-02"] = "Music (exploratory)"
    merged["run_labels"] = run_labels

    run_caveats = {str(run): str(caveat) for run, caveat in cast(dict[str, Any], merged.get("run_caveats") or {}).items()}
    run_caveats["run-02"] = RUN02_EXPLORATORY_CAVEAT
    merged["run_caveats"] = run_caveats
    merged["secondary_viewer_source"] = run02_viewer_root.relative_to(repo_root).as_posix()
    merged["run_02_status"] = _run02_status(repo_root, run02_viewer_root)
    return merged


def _annotate_run02_detail(detail: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    detail["run_label"] = "Music (exploratory)"
    detail["run_caveat"] = RUN02_EXPLORATORY_CAVEAT
    detail["viewer_source"] = _run02_viewer_root(repo_root).relative_to(repo_root).as_posix()
    detail["run_02_status"] = _run02_status(repo_root, _run02_viewer_root(repo_root))
    return detail


def _load_dashboard_empirical_detail(repo_root: Path, subject: str, run: str) -> dict[str, Any] | None:
    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    detail = load_empirical_viewer_detail(viewer_root, subject=subject, run=run)
    if detail is None and run == "run-02":
        detail = load_empirical_viewer_detail(_run02_viewer_root(repo_root), subject=subject, run=run)
    if detail is not None and run == "run-02":
        return _annotate_run02_detail(detail, repo_root)
    return detail


def _is_safe_empirical_selector(value: str) -> bool:
    return bool(SAFE_EMPIRICAL_ID_RE.fullmatch(value))


def _artifact_links(repo_root: Path) -> dict[str, list[dict[str, str]]]:
    report_specs = [
        ("Stage 2", repo_root / "docs" / "stage_reports" / "stage_2.md"),
        ("Dynamic Mechanism Ranking", repo_root / "docs" / "stage_reports" / "dynamic_mechanism_ranking.md"),
        ("Stage 3", repo_root / "docs" / "stage_reports" / "stage_3.md"),
        ("Stage 4", repo_root / "docs" / "stage_reports" / "stage_4.md"),
        ("Thesis Report Revised", repo_root / "output" / "doc" / "thesis_report_revised.md"),
        ("Thesis Report Revised DOCX", repo_root / "output" / "doc" / "thesis_report_revised.docx"),
        ("Defense Outline", repo_root / "output" / "doc" / "defense_outline.md"),
        ("Defense Outline DOCX", repo_root / "output" / "doc" / "defense_outline.docx"),
        ("Thesis Microsite", repo_root / "output" / "doc" / "thesis_microsite.html"),
        ("Set / Setting / Seed Microsite", repo_root / "output" / "doc" / "set_setting_seed_microsite.html"),
        ("Defense Presentation", repo_root / "output" / "doc" / "defense_presentation.html"),
        ("Defense Presentation PPTX", repo_root / "output" / "doc" / "defense_presentation.pptx"),
        ("Thesis Report Revised PDF", repo_root / "output" / "doc" / "thesis_report_revised.pdf"),
        ("Dynamic Mechanism Results XLSX", repo_root / "results" / "dynamic_mechanism_ranking" / "exports" / "dynamic_mechanism_results.xlsx"),
        ("Dynamic Mechanism Export Manifest", repo_root / "results" / "dynamic_mechanism_ranking" / "exports" / "export_manifest.json"),
        ("Dynamic Robustness Summary", repo_root / "results" / "dynamic_mechanism_ranking" / "robustness" / "robustness_summary.json"),
        ("ROCKET Condition Benchmark Report", repo_root / "results" / "training" / "rocket_condition_benchmark" / "benchmark_report.md"),
        (
            "ROCKET Condition Benchmark Summary",
            repo_root / "results" / "training" / "rocket_condition_benchmark" / "comparison_summary.json",
        ),
        ("Thesis Upgrade Status", repo_root / "results" / "thesis_upgrade" / "thesis_upgrade_status.json"),
        ("Thesis Upgrade Report", repo_root / "results" / "thesis_upgrade" / "thesis_upgrade_status.md"),
        ("Reproducible Archive Manifest", repo_root / "results" / "reproducible_archive" / "ARCHIVE_MANIFEST.json"),
        ("Reproducible Archive Checksums", repo_root / "results" / "reproducible_archive" / "CHECKSUMS.sha256"),
        ("External Ingestion Status", repo_root / "results" / "external_ingestion" / "external_ingestion_status.json"),
        ("Thesis Evidence Loop Status", repo_root / "results" / "thesis_evidence_loop" / "thesis_evidence_loop_status.json"),
        ("Thesis Evidence Loop Table", repo_root / "results" / "thesis_evidence_loop" / "status_rows.csv"),
        ("Claim Evidence Matrix CSV", repo_root / "results" / "thesis_evidence_loop" / "claim_evidence_matrix.csv"),
        ("Claim Evidence Matrix Markdown", repo_root / "results" / "thesis_evidence_loop" / "claim_evidence_matrix.md"),
        (
            "Thesis Evidence Loop Workbook",
            repo_root / "results" / "thesis_evidence_loop" / "exports" / "thesis_evidence_loop_tables.xlsx",
        ),
        ("Psilocybin ds006072 Status", repo_root / "results" / "psilocybin_ds006072" / "psilocybin_ds006072_status.json"),
        ("Structural Connectome Status", repo_root / "results" / "structural_connectome" / "structural_connectome_status.json"),
        ("Receptor Prior Status", repo_root / "results" / "receptor_priors" / "receptor_prior_status.json"),
        ("Parcellation Sensitivity Status", repo_root / "results" / "parcellation_sensitivity" / "parcellation_sensitivity_status.json"),
        ("Literature Benchmark Status", repo_root / "results" / "literature_benchmark" / "literature_benchmark_status.json"),
    ]
    reports = [
        {
            "label": label,
            "href": href,
        }
        for label, path in report_specs
        if path.exists()
        for href in [_artifact_href_from_path(path, repo_root)]
        if href is not None
    ]
    figure_dir = repo_root / "output" / "doc" / "figures"
    figures = [
        {
            "label": path.stem.replace("_", " ").title(),
            "href": href,
        }
        for path in sorted(figure_dir.glob("*.png"))
        if path.is_file()
        for href in [_artifact_href_from_path(path, repo_root)]
        if href is not None
    ]
    dynamic_figure_dir = repo_root / "results" / "dynamic_mechanism_ranking" / "figures"
    figures.extend(
        [
            {
                "label": f"Dynamic Mechanism: {path.stem.replace('_', ' ').title()}",
                "href": href,
            }
            for path in sorted(dynamic_figure_dir.glob("*.html"))
            if path.is_file()
            for href in [_artifact_href_from_path(path, repo_root)]
            if href is not None
        ]
    )
    return {"reports": reports, "figures": figures}


def _build_provenance_payload(stage_summaries: dict[str, Any]) -> dict[str, Any]:
    stage_2 = cast(dict[str, Any], stage_summaries.get("stage_2", {}))
    empirical_provenance = cast(dict[str, Any], stage_2.get("empirical_provenance", {}))
    cache_fingerprint = empirical_provenance.get("cache_fingerprint")
    version_stamp = cast(dict[str, Any], stage_2.get("version_stamp", {}))
    git = cast(
        dict[str, Any],
        version_stamp.get(
            "git",
            {
                "repo_present": False,
                "branch": None,
                "head_present": False,
                "commit_hash": None,
                "worktree_status": "not_repo",
            },
        ),
    )
    target_paths = cast(dict[str, Any], empirical_provenance.get("target_paths", {}))
    return {
        "dataset_anchor": empirical_provenance.get("dataset_anchor") or stage_2.get("dataset_anchor"),
        "subject_count": empirical_provenance.get("subject_count"),
        "run_count": empirical_provenance.get("run_count"),
        "sessions": empirical_provenance.get("sessions", []),
        "target_filenames": {
            "sober": Path(str(target_paths["sober"])).name if target_paths.get("sober") else None,
            "perturbation": Path(str(target_paths["perturbation"])).name if target_paths.get("perturbation") else None,
        },
        "git": git,
        "timestamp": version_stamp.get("timestamp"),
        "cache_fingerprint": cache_fingerprint,
        "cache_schema_version": empirical_provenance.get("cache_schema_version"),
        "cache_created_at_utc": empirical_provenance.get("cache_created_at_utc"),
        "preprocessing_qc": empirical_provenance.get("preprocessing_qc", {}),
    }


def _build_model_selection_payload(stage_summaries: dict[str, Any]) -> dict[str, Any]:
    stage_2 = cast(dict[str, Any], stage_summaries.get("stage_2", {}))
    seed_plan = cast(dict[str, Any], stage_2.get("fit_seed_plan", {}))
    multi_seed_summary = cast(dict[str, Any], stage_2.get("multi_seed_summary", {}))
    selection_seeds = list(seed_plan.get("selection_seeds", []))
    validation_seeds = list(seed_plan.get("validation_seeds", []))
    return {
        "selection_mode": seed_plan.get("selection_mode", "unknown"),
        "selection_seeds": selection_seeds,
        "selection_seed_count": len(selection_seeds),
        "validation_mode": seed_plan.get("validation_mode", "unknown"),
        "validation_seeds": validation_seeds,
        "validation_seed_count": len(validation_seeds),
        "selected_iteration": stage_2.get("selected_iteration"),
        "selection_score_mean": stage_2.get("best_score"),
        "selection_score_std": stage_2.get("selection_score_std"),
        "validation_score_mean": multi_seed_summary.get("score_mean"),
        "validation_score_std": multi_seed_summary.get("score_std"),
        "uncertainty_available": bool(multi_seed_summary.get("std_metrics")),
        "claim_guardrail": (
            "Multi-seed selection/validation reduces single-realization dependence, "
            "but does not imply held-out empirical validation."
        ),
    }


def _build_empirical_validation_payload(stage_summaries: dict[str, Any]) -> dict[str, Any]:
    stage_2 = cast(dict[str, Any], stage_summaries.get("stage_2", {}))
    stage_3 = cast(dict[str, Any], stage_summaries.get("stage_3", {}))
    stage_3_boundary = stage_3.get("empirical_validation_boundary")
    boundary: Any
    if (
        isinstance(stage_3_boundary, dict)
        and stage_3_boundary.get("held_out_validation_completed") is True
    ):
        boundary = stage_3_boundary
        source_stage = "stage_3"
    else:
        boundary = stage_2.get("empirical_validation_boundary")
        source_stage = "stage_2"
    if isinstance(boundary, dict):
        payload = dict(boundary)
        configured = bool(payload.get("held_out_validation_configured", payload.get("held_out") is True))
        completed = bool(payload.get("held_out_validation_completed", payload.get("held_out") is True))
        payload.setdefault("held_out_validation_configured", configured)
        payload.setdefault("held_out_validation_completed", completed)
        payload.setdefault("held_out", completed)
        payload.setdefault(
            "approval_status",
            "approved" if completed else "candidate" if configured else "none",
        )
        payload.setdefault("overlap_count", 0)
        payload.setdefault("warnings", [])
        payload.setdefault("limitations", [])
        payload.setdefault("source_stage", source_stage)
        return payload
    return build_no_subject_validation_boundary(
        selection_data_source=stage_2.get("dataset_anchor"),
        selection_subject_count=None,
    )


def _load_cv5_validation_payload(repo_root: Path) -> dict[str, Any] | None:
    aggregate_path = (
        repo_root
        / "output"
        / "validation"
        / "cv5_subject_disjoint"
        / "results"
        / "cv5_aggregate_validation.json"
    )
    if not aggregate_path.exists():
        return None
    payload = cast(dict[str, Any], json.loads(aggregate_path.read_text(encoding="utf-8")))
    payload.setdefault("source_path", aggregate_path.relative_to(repo_root).as_posix())
    payload.setdefault(
        "claim_guardrail",
        "CV5 subject-disjoint validation is internal validation only, not external or clinical validation.",
    )
    return payload


def _sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def _build_audit_status(
    stage_summaries: dict[str, Any],
    empirical: dict[str, Any],
    provenance: dict[str, Any],
    atlas_audit: dict[str, Any] | None = None,
    empirical_data_quality: dict[str, Any] | None = None,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    empirical_deltas = cast(dict[str, float], empirical.get("target_deltas", {}))
    literature_deltas = cast(dict[str, float], empirical.get("literature_deltas", {}))
    sign_mismatches: list[dict[str, Any]] = []
    sign_aligned: list[dict[str, Any]] = []
    for metric_name in sorted(set(empirical_deltas).intersection(literature_deltas)):
        empirical_delta = float(empirical_deltas[metric_name])
        literature_delta = float(literature_deltas[metric_name])
        empirical_sign = _sign(empirical_delta)
        literature_sign = _sign(literature_delta)
        row = {
            "metric": metric_name,
            "empirical_delta": empirical_delta,
            "literature_delta": literature_delta,
        }
        if empirical_sign != 0 and literature_sign != 0 and empirical_sign != literature_sign:
            sign_mismatches.append(row)
        else:
            sign_aligned.append(row)

    git = cast(dict[str, Any], provenance.get("git", {}))
    stage_3 = cast(dict[str, Any], stage_summaries.get("stage_3", {}))
    atlas_payload = atlas_audit or {}
    quality_payload = empirical_data_quality or {}
    model_selection = _build_model_selection_payload(stage_summaries)
    empirical_validation = _build_empirical_validation_payload(stage_summaries)
    cv5_validation = _load_cv5_validation_payload(repo_root)
    cache_fingerprint = provenance.get("cache_fingerprint")
    return {
        "defensible_claim": "Transparent surrogate and mismatch analysis, not a mechanistic psychedelic simulator.",
        "claim_guardrail": "Use the dashboard to compare empirical ds003059 deltas, literature-style targets, and model deltas side by side.",
        "sign_mismatches": sign_mismatches,
        "sign_aligned": sign_aligned,
        "atlas_overlaps": atlas_payload.get("overlaps", atlas_label_overlap_rows()),
        "atlas_voxel_counts": atlas_payload.get("module_voxel_counts", {}),
        "atlas_assigned_voxels": atlas_payload.get("assigned_voxels"),
        "empirical_record_count": quality_payload.get("record_count"),
        "empirical_paired_subject_count": quality_payload.get("paired_subject_count"),
        "empirical_complete_subject_count": quality_payload.get("complete_subject_count"),
        "empirical_timepoints": quality_payload.get("timepoints", {}),
        "preprocessing_qc": quality_payload.get("preprocessing_qc") or provenance.get("preprocessing_qc", {}),
        "model_selection": model_selection,
        "empirical_validation": empirical_validation,
        "cv5_validation": cv5_validation,
        "cache_status": {
            "status": "fingerprinted" if cache_fingerprint else "unknown",
            "fingerprint": cache_fingerprint,
            "schema_version": provenance.get("cache_schema_version"),
            "created_at_utc": provenance.get("cache_created_at_utc"),
            "claim_guardrail": (
                "A fingerprinted cache means generated targets match recorded metadata; "
                "it is not independent biological validation."
                if cache_fingerprint
                else "No cache fingerprint is recorded for the current Stage 2 artifacts."
            ),
        },
        "stage3_best_mechanism": stage_3.get("robust_best_mechanism") or stage_3.get("best_mechanism"),
        "stage3_score": stage_3.get("robust_best_score_mean") or stage_3.get("best_score"),
        "stage3_score_std": stage_3.get("robust_best_score_std"),
        "stage3_sign_agreement_fraction": stage_3.get("robust_best_sign_agreement_fraction"),
        "provenance_warning": (
            "No git HEAD is recorded for the current artifacts; commit a baseline before treating outputs as thesis provenance."
            if not git.get("head_present")
            else ""
        ),
        "validation_badges": [
            {"label": "ruff", "status": "documented passing", "command": "uv run ruff check ."},
            {"label": "mypy", "status": "documented passing", "command": "uv run mypy src"},
            {
                "label": "fast smoke",
                "status": "preferred iteration gate",
                "command": "uv run pytest tests/test_simulator.py tests/test_ds003059.py tests/test_perturbation.py tests/test_web.py -q -o addopts=",
            },
            {"label": "full pytest", "status": "currently slow", "command": "uv run pytest"},
        ],
    }


def _resolve_artifact_path(artifact_path: str, repo_root: Path = REPO_ROOT) -> Path | None:
    relative = Path(artifact_path)
    if not _is_allowed_artifact_relative_path(relative):
        return None
    resolved_root = repo_root.resolve()
    candidate = (resolved_root / relative).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError:
        return None
    return candidate


def _is_allowed_artifact_relative_path(relative_path: Path) -> bool:
    parts = relative_path.parts
    if not parts or relative_path.is_absolute():
        return False
    if any(part.startswith(".") for part in parts):
        return False
    if relative_path.name.startswith("~$") or relative_path.suffix.lower() in TEMP_ARTIFACT_SUFFIXES:
        return False
    return any(parts[: len(root)] == root for root in ALLOWED_ARTIFACT_ROOTS)


def _candidate_artifact_relative_paths(raw_path: str) -> list[str]:
    normalized = raw_path.replace("\\", "/").strip()
    candidates: list[str] = []
    for root in ALLOWED_ARTIFACT_ROOTS:
        marker = "/".join(root)
        if normalized == marker or normalized.startswith(f"{marker}/"):
            candidates.append(normalized)
        marker_with_prefix = f"/{marker}/"
        marker_index = normalized.find(marker_with_prefix)
        if marker_index >= 0:
            candidates.append(normalized[marker_index + 1 :])
    if normalized not in candidates:
        candidates.append(normalized)
    return candidates


def _artifact_href_from_raw_path(raw_path: str, repo_root: Path) -> str | None:
    for candidate_path in _candidate_artifact_relative_paths(raw_path):
        resolved = _resolve_artifact_path(candidate_path, repo_root)
        if resolved is None or not resolved.exists():
            continue
        relative_path = resolved.relative_to(repo_root.resolve())
        return f"/artifacts/{relative_path.as_posix()}"
    return None


def _artifact_href_from_path(path: Path, repo_root: Path) -> str | None:
    resolved_root = repo_root.resolve()
    try:
        relative_path = path.resolve().relative_to(resolved_root)
    except ValueError:
        return _artifact_href_from_raw_path(str(path), repo_root)
    return _artifact_href_from_raw_path(relative_path.as_posix(), repo_root)


def _empirical_selector_is_invalid(subject: str, run: str) -> bool:
    return not (_is_safe_empirical_selector(subject) and _is_safe_empirical_selector(run))


def _artifact_security_headers(candidate: Path, repo_root: Path = REPO_ROOT) -> dict[str, str]:
    headers = {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "Cross-Origin-Resource-Policy": "same-origin",
    }
    suffix = candidate.suffix.lower()
    if suffix == ".html":
        relative = candidate.resolve().relative_to(repo_root.resolve())
        if "figures" in relative.parts and relative.parts[0] == "results":
            headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "script-src 'unsafe-inline' https://cdn.plot.ly; "
                "style-src 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "connect-src 'none'; "
                "object-src 'none'; "
                "base-uri 'none'; "
                "form-action 'none'; "
                "frame-ancestors 'none'; "
                "sandbox allow-scripts"
            )
        else:
            headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "style-src 'unsafe-inline'; "
                "img-src 'self' data:; "
                "script-src 'none'; "
                "object-src 'none'; "
                "base-uri 'none'; "
                "form-action 'none'; "
                "frame-ancestors 'none'; "
                "sandbox allow-same-origin"
            )
    elif suffix == ".svg":
        headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'none'; object-src 'none'; "
            "base-uri 'none'; form-action 'none'; frame-ancestors 'none'; sandbox"
        )
        headers["Content-Disposition"] = f'attachment; filename="{candidate.name}"'
    return headers


def _dashboard_security_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "form-action 'none'; "
            "frame-ancestors 'none'"
        ),
    }


def _load_set_setting_seed_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    payload_path = repo_root / "results" / "setting_seed" / "dashboard" / "dashboard_payload.json"
    if not payload_path.exists():
        return {
            "status": "missing",
            "source_path": str(payload_path.relative_to(repo_root)),
            "claim_guardrail": "Set, setting, and seed panels are unavailable until PASS 2A artifacts are built.",
        }
    payload = cast(dict[str, Any], json.loads(payload_path.read_text(encoding="utf-8")))
    payload.setdefault(
        "claim_guardrail",
        "Exploratory macro-dynamics proxy summaries, not subjective-experience simulation or biological proof.",
    )
    payload["source_path"] = str(payload_path.relative_to(repo_root))
    return payload


def _load_dynamic_mechanism_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    payload_path = repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json"
    if not payload_path.exists():
        return {
            "analysis_status": "missing",
            "source_path": payload_path.relative_to(repo_root).as_posix(),
            "claim_guardrail": "A+B+C+D+E dynamic mechanism ranking artifacts have not been generated yet.",
        }
    payload = cast(dict[str, Any], json.loads(payload_path.read_text(encoding="utf-8")))
    payload.setdefault(
        "claim_guardrail",
        "First-pass AI/ML surrogate results only; not receptor-level, clinical, external-validity, or subjective-experience evidence.",
    )
    payload["source_path"] = payload_path.relative_to(repo_root).as_posix()
    return payload


def _load_thesis_loop_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    payload_path = repo_root / "results" / "thesis_evidence_loop" / "thesis_evidence_loop_status.json"
    if not payload_path.exists():
        return {
            "analysis_status": "missing",
            "source_path": payload_path.relative_to(repo_root).as_posix(),
            "status_rows": [],
            "claim_guardrail": "Run scripts/run_thesis_evidence_loop.py to populate the full evidence-loop status matrix.",
        }
    payload = cast(dict[str, Any], json.loads(payload_path.read_text(encoding="utf-8")))
    payload["source_path"] = payload_path.relative_to(repo_root).as_posix()
    return payload


def _build_thesis_expansion_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    loop_status = _load_thesis_loop_status(repo_root)
    loop_status_by_label = {
        str(row.get("label")): row
        for row in loop_status.get("status_rows", [])
        if isinstance(row, dict)
    }
    payload = {
        "thesis_goal": (
            "Build a reproducible explainable AI framework that ranks transparent "
            "control-theoretic and graph-dynamic surrogate mechanisms across LSD and "
            "psilocybin fMRI, then tests whether the strongest claims survive "
            "structural-connectome, receptor-map, atlas, and literature-benchmark checks."
        ),
        "research_question": (
            "Which interpretable macro-dynamic mechanisms best explain psychedelic "
            "drug-vs-control fMRI changes, and which claims fail under robustness, "
            "cross-dataset, and biological-prior tests?"
        ),
        "status_summary": (
            "The LSD A+B+C+D+E ranking is implemented. The next loop upgrades the "
            "evidence base with robustness, ds006072 psilocybin replication, HCP "
            "structural connectivity, neuromaps/FS5ht receptor priors, Schaefer/Yeo "
            "sensitivity, and comparison to the 2026 Nature Medicine mega-analysis."
        ),
        "claim_guardrail": (
            "Dashboard status labels separate implemented evidence from planned tests. "
            "No planned dataset or literature comparison is shown as a completed result."
        ),
        "loop_steps": [
            {
                "step": "1",
                "label": "LSD robustness",
                "status": "next",
                "artifact_target": "results/dynamic_mechanism_ranking/robustness/",
                "scientific_question": "Do C and E survive subject/bootstrap, run, horizon, state-label, and window-size sensitivity?",
                "dashboard_output": "Robustness bands, pass/fail badges, and failure-case slices.",
            },
            {
                "step": "2",
                "label": "Psilocybin ds006072",
                "status": "planned",
                "artifact_target": "results/psilocybin_ds006072/",
                "scientific_question": "Does the LSD ranking generalize to psilocybin precision functional mapping data?",
                "dashboard_output": "LSD-vs-psilocybin mechanism ranking comparison.",
            },
            {
                "step": "3",
                "label": "HCP structural graph",
                "status": "planned",
                "artifact_target": "results/structural_connectome/",
                "scientific_question": "Does E remain plausible when the macro proxy graph is replaced by a normative structural connectome?",
                "dashboard_output": "Control-energy comparison across proxy, structural, uniform, degree, and graph-rewire controls.",
            },
            {
                "step": "4",
                "label": "PET receptor priors",
                "status": "planned",
                "artifact_target": "results/receptor_priors/",
                "scientific_question": "Do neuromaps/FS5ht 5-HT2A priors outperform uniform, random, degree, and spatial nulls?",
                "dashboard_output": "Receptor-prior null board and claim-status split for E.",
            },
            {
                "step": "5",
                "label": "Schaefer/Yeo sensitivity",
                "status": "planned",
                "artifact_target": "results/parcellation_sensitivity/",
                "scientific_question": "Are C/D/E findings stable beyond the current 8-module proxy representation?",
                "dashboard_output": "Schaefer 100/200 and Yeo 7/17 result matrix.",
            },
            {
                "step": "6",
                "label": "Mega-analysis comparison",
                "status": "planned",
                "artifact_target": "results/literature_benchmark/",
                "scientific_question": "Do final patterns align with transmodal-unimodal and striatal-unimodal effects reported in the 2026 mega-analysis?",
                "dashboard_output": "Scholarly benchmark agreement table with explicit mismatches.",
            },
        ],
        "scholarly_anchors": [
            {
                "source": "Girn et al., Nature Medicine 2026",
                "claim": (
                    "Common psychedelic signature: increased transmodal-unimodal functional coupling with "
                    "subnetwork specificity; striatal-unimodal effects are prominent."
                ),
                "use_in_project": "Final external benchmark for C/D/E directionality.",
                "status": "planned comparison",
                "url": "https://www.nature.com/articles/s41591-026-04287-9",
            },
            {
                "source": "Dosenbach/Siegel group, Scientific Data 2025",
                "claim": "OpenNeuro ds006072 provides psilocybin precision functional mapping data with raw, minimally processed, and fully processed imaging.",
                "use_in_project": "First cross-drug dataset expansion after LSD robustness.",
                "status": "planned dataset",
                "url": "https://www.nature.com/articles/s41597-025-05189-0",
            },
            {
                "source": "Singleton et al., Nature Communications 2022",
                "claim": "Receptor-informed network control links LSD and psilocybin to lower control-energy landscape estimates.",
                "use_in_project": "Primary mathematical benchmark for E, but not proof that the local proxy implementation is valid.",
                "status": "method benchmark",
                "url": "https://www.nature.com/articles/s41467-022-33578-1",
            },
            {
                "source": "Markello et al., Nature Methods 2022",
                "claim": "neuromaps provides standardized brain-map comparison tools and receptor PET annotations.",
                "use_in_project": "Replace hand-built receptor proxies with documented receptor-map projections.",
                "status": "planned biological prior",
                "url": "https://www.nature.com/articles/s41592-022-01625-w",
            },
            {
                "source": "Human Connectome Project Young Adult",
                "claim": "Large normative dataset with diffusion and resting-state fMRI for healthy young adults.",
                "use_in_project": "Source for structural-connectome graph and null sensitivity.",
                "status": "planned graph prior",
                "url": "https://www.humanconnectome.org/study/hcp-young-adult/overview",
            },
            {
                "source": "Schaefer et al., Cerebral Cortex 2018",
                "claim": "Multiresolution local-global cortical parcellations support network neuroscience and graph analyses.",
                "use_in_project": "Sensitivity layer for C/D/E beyond the 8-module proxy.",
                "status": "planned parcellation",
                "url": "https://academic.oup.com/cercor/article/28/9/3095/3978804",
            },
        ],
        "success_criteria": [
            "C and/or E remain defensible under LSD robustness checks.",
            "At least one cross-dataset psilocybin analysis runs without changing the scoring rules after seeing results.",
            "E is explicitly split into landscape-flattening support versus receptor-specific control-placement support.",
            "Schaefer/Yeo sensitivity either preserves C/D/E patterns or reports the failure plainly.",
            "The final dashboard shows evidence, nulls, failures, citations, commands, and export paths.",
        ],
        "failure_modes": [
            "C/E collapse under bootstrap or run sensitivity.",
            "ds006072 preprocessing or metadata incompatibility blocks a fair LSD-psilocybin comparison.",
            "HCP structural graph weakens the current E result.",
            "PET receptor maps do not outperform spatial/null controls.",
            "Schaefer/Yeo extraction changes the sign or rank of C/D/E.",
        ],
    }
    for step in payload["loop_steps"]:
        status_row = loop_status_by_label.get(str(step["label"]))
        if not status_row:
            continue
        step["status"] = status_row.get("status", step["status"])
        step["implementation_evidence"] = status_row.get("evidence")
        step["implementation_blocker"] = status_row.get("blocker")
    payload["loop_status"] = loop_status
    if loop_status.get("analysis_status") != "missing":
        component_statuses = {
            name: component.get("analysis_status")
            for name, component in dict(loop_status.get("components", {})).items()
            if isinstance(component, dict)
        }
        payload["status_summary"] = (
            "The evidence-loop artifact contract is implemented. LSD robustness, Schaefer/Yeo sensitivity, "
            "literature benchmarking, ds006072 manifests, proxy graph nulls, and coarse receptor-prior nulls "
            "are populated from current results. True psilocybin replication, HCP structural graph claims, "
            "and PET receptor-map claims remain blocked until their required local data artifacts exist. "
            f"Component statuses: {component_statuses}."
        )
        payload["claim_guardrail"] = loop_status.get("claim_guardrail", payload["claim_guardrail"])
    return payload




_dashboard_cache: dict[str, Any] | None = None


def build_dashboard_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    from lsd_thesis.thesis_upgrade import build_thesis_upgrade_status

    graph = load_graph_config(repo_root / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(repo_root / "configs" / "regimes" / "baseline.yaml")
    perturbed = load_regime_config(repo_root / "configs" / "regimes" / "perturbed.yaml")

    stage_summaries: dict[str, Any] = {}
    stage_summary_paths = {
        "stage_1": repo_root / "results" / "stage_1" / "stage_1_summary.json",
        "stage_2": repo_root / "results" / "stage_2" / "stage_2_summary.json",
        "stage_2b": repo_root / "results" / "stage_2b" / "target_reliability_summary.json",
        "stage_3": repo_root / "results" / "stage_3" / "stage_3_summary.json",
        "stage_4": repo_root / "results" / "stage_4" / "stage_4_summary.json",
        "stage_5": repo_root / "results" / "stage_5" / "literature_weighted_fit_summary.json",
    }
    for stage_name, summary_path in stage_summary_paths.items():
        if summary_path.exists():
            stage_summaries[stage_name] = json.loads(summary_path.read_text(encoding="utf-8"))
    provenance = _build_provenance_payload(stage_summaries)

    empirical: dict[str, Any] = {}
    sober_target_path = repo_root / "results" / "stage_2" / "empirical_sober_targets.yaml"
    perturbation_target_path = repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml"
    literature_target_path = repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml"
    if sober_target_path.exists():
        sober_target = load_sober_target_set(sober_target_path)
        empirical["sober_metrics"] = {
            name: target.target for name, target in sober_target.metrics.items()
        }
        empirical["sober_fc_matrix"] = sober_target.fc_matrix.tolist()
        empirical["dataset_anchor"] = sober_target.dataset_anchor
    if perturbation_target_path.exists():
        perturbation_target = load_perturbation_target_set(perturbation_target_path)
        empirical["target_deltas"] = perturbation_target.target_deltas
    if literature_target_path.exists():
        literature_target = load_perturbation_target_set(literature_target_path)
        empirical["literature_deltas"] = literature_target.target_deltas
    if provenance["dataset_anchor"] and "dataset_anchor" not in empirical:
        empirical["dataset_anchor"] = provenance["dataset_anchor"]
    atlas_audit_path = repo_root / "results" / "stage_2" / "atlas_mapping_audit.json"
    atlas_audit = (
        cast(dict[str, Any], json.loads(atlas_audit_path.read_text(encoding="utf-8")))
        if atlas_audit_path.exists()
        else None
    )
    empirical_data_quality_path = repo_root / "results" / "stage_2" / "empirical_data_quality.json"
    empirical_data_quality = (
        cast(dict[str, Any], json.loads(empirical_data_quality_path.read_text(encoding="utf-8")))
        if empirical_data_quality_path.exists()
        else None
    )
    audit_status = _build_audit_status(
        stage_summaries,
        empirical,
        provenance,
        atlas_audit,
        empirical_data_quality,
        repo_root,
    )
    cv5_validation = _load_cv5_validation_payload(repo_root)

    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    empirical_viewer = load_empirical_viewer_overview(viewer_root)
    empirical_viewer = _augment_empirical_viewer_with_run02(empirical_viewer, repo_root)
    artifact_links = _artifact_links(repo_root)
    if empirical_viewer is not None:
        empirical_viewer["reports"] = artifact_links["reports"]
        gallery_items = []
        for item in empirical_viewer.get("gallery", []):
            href = _artifact_href_from_raw_path(str(item["path"]), repo_root)
            if href is not None:
                gallery_items.append({**item, "href": href})
        empirical_viewer["gallery"] = gallery_items

    return {
        "graph": _graph_payload(graph),
        "baseline": build_simulation_payload(graph, baseline),
        "perturbed": build_simulation_payload(graph, perturbed),
        "stage_summaries": stage_summaries,
        "provenance": provenance,
        "audit_status": audit_status,
        "model_selection": _build_model_selection_payload(stage_summaries),
        "empirical_validation": _build_empirical_validation_payload(stage_summaries),
        "cv5_validation": cv5_validation,
        "empirical": empirical,
        "empirical_viewer": empirical_viewer,
        "set_setting_seed": _load_set_setting_seed_payload(repo_root),
        "dynamic_mechanism": _load_dynamic_mechanism_payload(repo_root),
        "thesis_expansion": _build_thesis_expansion_payload(repo_root),
        "thesis_upgrade": build_thesis_upgrade_status(repo_root),
        "artifact_links": artifact_links,
        "baseline_parameters": {
            "within_group_scale": baseline.global_parameters.within_group_scale,
            "cross_group_scale": baseline.global_parameters.cross_group_scale,
            "constraint_scale": baseline.global_parameters.constraint_scale,
            "rigidity": baseline.module_defaults.rigidity,
            "barrier": baseline.module_defaults.barrier,
            "temperature": baseline.module_defaults.temperature,
            "tau": baseline.module_defaults.tau,
        },
    }


def create_app() -> FastAPI:
    app = FastAPI(title="Whole-Brain Surrogate Dashboard")

    @app.get("/assets/plotly.min.js")
    async def plotly_asset() -> Response:
        global _plotly_js_cache
        if _plotly_js_cache is None:
            from plotly.offline import get_plotlyjs

            _plotly_js_cache = get_plotlyjs()
        return Response(
            content=_plotly_js_cache,
            media_type="application/javascript",
            headers={
                "Cache-Control": "public, max-age=86400",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        html = (REPO_ROOT / "src" / "lsd_thesis" / "templates" / "dashboard.html").read_text(
            encoding="utf-8"
        )
        return HTMLResponse(html, headers=_dashboard_security_headers())

    @app.get("/favicon.ico")
    async def favicon() -> Response:
        return Response(status_code=204)

    _safe_extensions = frozenset(
        {".csv", ".docx", ".html", ".json", ".md", ".pdf", ".pptx", ".svg", ".txt", ".xlsx", ".yaml", ".yml", ".png"}
    )

    @app.get("/artifacts/{artifact_path:path}")
    async def artifacts(artifact_path: str) -> Response:
        candidate = _resolve_artifact_path(artifact_path, repo_root=REPO_ROOT)
        if candidate is None:
            return Response(status_code=403)
        if not candidate.exists() or not candidate.is_file():
            return Response(status_code=404)
        if candidate.suffix.lower() not in _safe_extensions:
            return Response(status_code=403)
        return FileResponse(candidate, headers=_artifact_security_headers(candidate, REPO_ROOT))

    @app.get("/api/dashboard-data")
    async def dashboard_data() -> dict[str, Any]:
        global _dashboard_cache
        if _dashboard_cache is None:
            _dashboard_cache = build_dashboard_payload(REPO_ROOT)
        return _dashboard_cache

    @app.get("/api/empirical-view")
    async def empirical_view(subject: str, run: str) -> dict[str, Any]:
        if _empirical_selector_is_invalid(subject, run):
            raise HTTPException(status_code=400, detail="Invalid empirical subject or run identifier.")
        detail = _load_dashboard_empirical_detail(REPO_ROOT, subject=subject, run=run)
        if detail is None:
            raise HTTPException(status_code=404, detail="Empirical view not found.")
        return detail

    @app.post("/api/simulate")
    async def simulate(request: SimulationRequest) -> dict[str, Any]:
        graph = load_graph_config(REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml")
        regime_path = (
            REPO_ROOT
            / "configs"
            / "regimes"
            / ("perturbed.yaml" if request.regime == "perturbed" else "baseline.yaml")
        )
        regime = load_regime_config(regime_path)

        if request.within_group_scale is not None:
            regime.global_parameters.within_group_scale = request.within_group_scale
        if request.cross_group_scale is not None:
            regime.global_parameters.cross_group_scale = request.cross_group_scale
        if request.constraint_scale is not None:
            regime.global_parameters.constraint_scale = request.constraint_scale
        if request.rigidity is not None:
            regime.module_defaults.rigidity = request.rigidity
        if request.barrier is not None:
            regime.module_defaults.barrier = request.barrier
        if request.temperature is not None:
            regime.module_defaults.temperature = request.temperature
        if request.tau is not None:
            regime.module_defaults.tau = request.tau

        return build_simulation_payload(graph, regime)

    return app


app = create_app()
