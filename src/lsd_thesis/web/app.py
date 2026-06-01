from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from lsd_thesis.data.targets import load_perturbation_target_set, load_sober_target_set
from lsd_thesis.graph import load_graph_config
from lsd_thesis.simulator import load_regime_config
from lsd_thesis.web import artifacts as web_artifacts
from lsd_thesis.web import empirical_viewer, status_payload
from lsd_thesis.web.simulation_payload import (
    SimulationRequest,
    build_simulation_payload,
    graph_payload,
)
from lsd_thesis.web.structural_dti import load_structural_dti_payload
from lsd_thesis.web.thesis_payload import build_thesis_expansion_payload, load_claim_status_payload

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = Jinja2Templates(directory=str(REPO_ROOT / "src" / "lsd_thesis" / "templates"))
_plotly_js_cache: str | None = None

_augment_empirical_viewer_with_run02 = empirical_viewer.augment_empirical_viewer_with_run02
_empirical_selector_is_invalid = empirical_viewer.empirical_selector_is_invalid
_load_dashboard_empirical_detail = empirical_viewer.load_dashboard_empirical_detail
load_empirical_viewer_detail = empirical_viewer.load_empirical_viewer_detail
load_empirical_viewer_overview = empirical_viewer.load_empirical_viewer_overview


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


def _load_external_cortical_maps_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    status_path = repo_root / "results" / "cortical_maps" / "cortical_map_alignment_status.json"
    markdown_path = repo_root / "results" / "cortical_maps" / "cortical_map_alignment.md"
    if not status_path.exists():
        return {
            "analysis_status": "missing_external_cortical_map_alignment",
            "source_path": status_path.relative_to(repo_root).as_posix(),
            "markdown_path": markdown_path.relative_to(repo_root).as_posix(),
            "maps": [],
            "dynamic_targets": [],
            "alignment_rows": [],
            "claim_guardrail": (
                "External receptor, myelin, functional-gradient, and transcriptomic map alignment has not been generated yet. "
                "Run scripts/build_external_cortical_maps.py after dynamic-mechanism outputs exist."
            ),
        }
    payload = cast(dict[str, Any], json.loads(status_path.read_text(encoding="utf-8")))
    payload.setdefault("source_path", status_path.relative_to(repo_root).as_posix())
    if markdown_path.exists():
        payload.setdefault("markdown_path", markdown_path.relative_to(repo_root).as_posix())
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
    provenance = status_payload.build_provenance_payload(stage_summaries)

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
    audit_status = status_payload.build_audit_status(
        stage_summaries,
        empirical,
        provenance,
        atlas_audit,
        empirical_data_quality,
        repo_root,
    )
    cv5_validation = status_payload.load_cv5_validation_payload(repo_root)

    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    empirical_viewer = load_empirical_viewer_overview(viewer_root)
    empirical_viewer = _augment_empirical_viewer_with_run02(empirical_viewer, repo_root)
    artifact_links = web_artifacts.artifact_links(repo_root)
    if empirical_viewer is not None:
        empirical_viewer["reports"] = artifact_links["reports"]
        gallery_items = []
        for item in empirical_viewer.get("gallery", []):
            href = web_artifacts.artifact_href_from_raw_path(str(item["path"]), repo_root)
            if href is not None:
                gallery_items.append({**item, "href": href})
        empirical_viewer["gallery"] = gallery_items

    return {
        "graph": graph_payload(graph),
        "baseline": build_simulation_payload(graph, baseline),
        "perturbed": build_simulation_payload(graph, perturbed),
        "stage_summaries": stage_summaries,
        "provenance": provenance,
        "audit_status": audit_status,
        "model_selection": status_payload.build_model_selection_payload(stage_summaries),
        "empirical_validation": status_payload.build_empirical_validation_payload(stage_summaries),
        "cv5_validation": cv5_validation,
        "empirical": empirical,
        "empirical_viewer": empirical_viewer,
        "set_setting_seed": _load_set_setting_seed_payload(repo_root),
        "dynamic_mechanism": _load_dynamic_mechanism_payload(repo_root),
        "structural_dti": load_structural_dti_payload(repo_root),
        "external_cortical_maps": _load_external_cortical_maps_payload(repo_root),
        "claim_status": load_claim_status_payload(repo_root),
        "thesis_expansion": build_thesis_expansion_payload(repo_root),
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
        return HTMLResponse(html, headers=web_artifacts.dashboard_security_headers())

    @app.get("/favicon.ico")
    async def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/artifacts/{artifact_path:path}")
    async def artifacts(artifact_path: str) -> Response:
        candidate = web_artifacts.resolve_artifact_path(artifact_path, repo_root=REPO_ROOT)
        if candidate is None:
            return Response(status_code=403)
        if not candidate.exists() or not candidate.is_file():
            return Response(status_code=404)
        if candidate.suffix.lower() not in web_artifacts.SAFE_ARTIFACT_EXTENSIONS:
            return Response(status_code=403)
        return FileResponse(candidate, headers=web_artifacts.artifact_security_headers(candidate, REPO_ROOT))

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
