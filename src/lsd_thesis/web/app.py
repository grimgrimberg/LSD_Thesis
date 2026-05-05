from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import networkx as nx
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator

from lsd_thesis.core import MODULE_GROUPS, GraphConfig, RegimeConfig
from lsd_thesis.data.ds003059 import atlas_label_overlap_rows
from lsd_thesis.data.targets import load_perturbation_target_set, load_sober_target_set
from lsd_thesis.graph import load_graph_config
from lsd_thesis.metrics import compute_observable_summary
from lsd_thesis.simulator import load_regime_config, run_simulation

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = Jinja2Templates(directory=str(REPO_ROOT / "src" / "lsd_thesis" / "templates"))


class SimulationRequest(BaseModel):
    regime: str = "baseline"
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
    def _clamp_positive(cls, value: float | None) -> float | None:
        if value is not None and value <= 0.0:
            raise ValueError("Parameter must be positive.")
        if value is not None and value > 100.0:
            raise ValueError("Parameter too large (max 100).")
        return value


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
    return overview


def load_empirical_viewer_detail(
    viewer_root: Path,
    subject: str,
    run: str,
) -> dict[str, Any] | None:
    detail_path = viewer_root / "subject_views" / f"{subject}_{run}.json"
    if not detail_path.exists():
        return None
    return cast(dict[str, Any], json.loads(detail_path.read_text(encoding="utf-8")))


def _artifact_links(repo_root: Path) -> dict[str, list[dict[str, str]]]:
    report_specs = [
        ("Stage 2", repo_root / "docs" / "stage_reports" / "stage_2.md"),
        ("Stage 3", repo_root / "docs" / "stage_reports" / "stage_3.md"),
        ("Stage 4", repo_root / "docs" / "stage_reports" / "stage_4.md"),
        ("Thesis Report Revised", repo_root / "output" / "doc" / "thesis_report_revised.md"),
        ("Thesis Report Revised DOCX", repo_root / "output" / "doc" / "thesis_report_revised.docx"),
        ("Defense Outline", repo_root / "output" / "doc" / "defense_outline.md"),
        ("Defense Outline DOCX", repo_root / "output" / "doc" / "defense_outline.docx"),
        ("Thesis Microsite", repo_root / "output" / "doc" / "thesis_microsite.html"),
        ("Defense Presentation", repo_root / "output" / "doc" / "defense_presentation.html"),
        ("Defense Presentation PPTX", repo_root / "output" / "doc" / "defense_presentation.pptx"),
        ("Thesis Report Revised PDF", repo_root / "output" / "doc" / "thesis_report_revised.pdf"),
    ]
    reports = [
        {
            "label": label,
            "href": f"/artifacts/{path.relative_to(repo_root).as_posix()}",
        }
        for label, path in report_specs
        if path.exists()
    ]
    figure_dir = repo_root / "output" / "doc" / "figures"
    figures = [
        {
            "label": path.stem.replace("_", " ").title(),
            "href": f"/artifacts/{path.relative_to(repo_root).as_posix()}",
        }
        for path in sorted(figure_dir.glob("*.png"))
        if path.is_file()
    ]
    return {"reports": reports, "figures": figures}


def _build_provenance_payload(stage_summaries: dict[str, Any]) -> dict[str, Any]:
    stage_2 = cast(dict[str, Any], stage_summaries.get("stage_2", {}))
    empirical_provenance = cast(dict[str, Any], stage_2.get("empirical_provenance", {}))
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
    }


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
    resolved_root = repo_root.resolve()
    candidate = (resolved_root / artifact_path).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError:
        return None
    return candidate


def _artifact_href_from_path(path: Path, repo_root: Path) -> str | None:
    resolved_root = repo_root.resolve()
    try:
        relative_path = path.resolve().relative_to(resolved_root)
    except ValueError:
        return None
    return f"/artifacts/{relative_path.as_posix()}"


_dashboard_cache: dict[str, Any] | None = None


def build_dashboard_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    graph = load_graph_config(repo_root / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(repo_root / "configs" / "regimes" / "baseline.yaml")
    perturbed = load_regime_config(repo_root / "configs" / "regimes" / "perturbed.yaml")

    stage_summaries: dict[str, Any] = {}
    for stage_name in ("stage_1", "stage_2", "stage_3", "stage_4"):
        summary_path = repo_root / "results" / stage_name / f"{stage_name}_summary.json"
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
    )

    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    empirical_viewer = load_empirical_viewer_overview(viewer_root)
    artifact_links = _artifact_links(repo_root)
    if empirical_viewer is not None:
        empirical_viewer["reports"] = artifact_links["reports"]
        gallery_items = []
        for item in empirical_viewer.get("gallery", []):
            href = _artifact_href_from_path(repo_root / Path(str(item["path"])), repo_root)
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
        "empirical": empirical,
        "empirical_viewer": empirical_viewer,
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

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        html = (REPO_ROOT / "src" / "lsd_thesis" / "templates" / "dashboard.html").read_text(
            encoding="utf-8"
        )
        return HTMLResponse(html)

    @app.get("/favicon.ico")
    async def favicon() -> Response:
        return Response(status_code=204)

    _safe_extensions = frozenset(
        {".docx", ".html", ".json", ".md", ".pdf", ".pptx", ".yaml", ".yml", ".png", ".svg", ".txt"}
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
        return FileResponse(candidate, headers={"Cache-Control": "no-store"})

    @app.get("/api/dashboard-data")
    async def dashboard_data() -> dict[str, Any]:
        global _dashboard_cache
        if _dashboard_cache is None:
            _dashboard_cache = build_dashboard_payload(REPO_ROOT)
        return _dashboard_cache

    @app.get("/api/empirical-view")
    async def empirical_view(subject: str, run: str) -> dict[str, Any]:
        viewer_root = REPO_ROOT / "results" / "stage_2" / "empirical_viewer"
        detail = load_empirical_viewer_detail(viewer_root, subject=subject, run=run)
        if detail is None:
            return {"error": "Empirical view not found.", "subject": subject, "run": run}
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
