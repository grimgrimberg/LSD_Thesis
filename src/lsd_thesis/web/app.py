from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from lsd_thesis.graph import load_graph_config
from lsd_thesis.simulator import load_regime_config
from lsd_thesis.web import artifacts as web_artifacts
from lsd_thesis.web import empirical_viewer
from lsd_thesis.web.dashboard_payload import build_dashboard_payload
from lsd_thesis.web.prior_art_payload import build_prior_art_payload
from lsd_thesis.web.simulation_payload import (
    SimulationRequest,
    build_simulation_payload,
)
from lsd_thesis.web.site_payload import build_public_site_payload

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = Jinja2Templates(directory=str(REPO_ROOT / "src" / "lsd_thesis" / "templates"))
STATIC_DIR = REPO_ROOT / "src" / "lsd_thesis" / "static"
_plotly_js_cache: str | None = None

DASHBOARD_NAV = [
    {
        "id": "overview",
        "label": "Overview",
        "href": "/",
        "icon": "M4 13h7V4H4zM13 20h7V4h-7zM4 20h7v-5H4z",
        "title": "Overview",
        "template": "pages/overview.html",
    },
    {
        "id": "mechanism_ranking",
        "label": "Mechanism Ranking",
        "href": "/ranking",
        "icon": "M4 18l5-6 4 3 7-9M4 20h16",
        "title": "Mechanism Ranking",
        "template": "pages/mechanism_ranking.html",
    },
    {
        "id": "robustness",
        "label": "Robustness",
        "href": "/robustness",
        "icon": "M12 3l7 4v5c0 5-3 8-7 10-4-2-7-5-7-10V7zM9 12l2 2 4-5",
        "title": "Robustness",
        "template": "pages/robustness.html",
    },
    {
        "id": "prior_art",
        "label": "Prior Art",
        "href": "/prior-art",
        "icon": "M5 4h11a3 3 0 0 1 3 3v13H7a2 2 0 0 1-2-2zM8 8h8M8 12h8M8 16h5",
        "title": "Prior-Art Inventory",
        "template": "pages/prior_art.html",
    },
    {
        "id": "empirical",
        "label": "Empirical",
        "href": "/empirical",
        "icon": "M4 19c4 0 4-14 8-14s4 14 8 14M4 12h16",
        "title": "Empirical Viewer",
        "template": "pages/empirical.html",
    },
    {
        "id": "simulator",
        "label": "Simulator",
        "href": "/simulator",
        "icon": "M4 7h10M4 17h10M18 5v4M18 15v4M14 7a2 2 0 1 0 4 0 2 2 0 0 0-4 0M14 17a2 2 0 1 0 4 0 2 2 0 0 0-4 0",
        "title": "Simulator",
        "template": "pages/simulator.html",
    },
    {
        "id": "thesis",
        "label": "Thesis",
        "href": "/thesis",
        "icon": "M5 4h14v16H5zM8 8h8M8 12h8M8 16h5",
        "title": "Thesis Presentation",
        "template": "pages/thesis.html",
    },
    {
        "id": "figures",
        "label": "Figure Deck",
        "href": "/figures",
        "icon": "M4 5h16v4H4zM4 11h7v8H4zM13 11h7v8h-7z",
        "title": "Figure Deck",
        "template": "pages/figures.html",
    },
]

_augment_empirical_viewer_with_run02 = empirical_viewer.augment_empirical_viewer_with_run02
_empirical_selector_is_invalid = empirical_viewer.empirical_selector_is_invalid
_load_dashboard_empirical_detail = empirical_viewer.load_dashboard_empirical_detail
load_empirical_viewer_detail = empirical_viewer.load_empirical_viewer_detail
load_empirical_viewer_overview = empirical_viewer.load_empirical_viewer_overview


_dashboard_cache: dict[str, Any] | None = None
_public_site_cache: dict[str, Any] | None = None


def _nav_item(page_id: str) -> dict[str, str]:
    for item in DASHBOARD_NAV:
        if item["id"] == page_id:
            return item
    raise KeyError(f"Unknown dashboard page: {page_id}")


def _render_dashboard_page(page_id: str) -> HTMLResponse:
    item = _nav_item(page_id)
    html = TEMPLATES.get_template(item["template"]).render(
        page_title=item["title"],
        active_page=item["id"],
        nav_items=DASHBOARD_NAV,
        home_href="/",
        artifact_prefix="/artifacts/",
        data_url="/api/dashboard-data",
        prior_art_data_url="/api/prior-art-data",
        static_prefix="/static/",
        plotly_src="/assets/plotly.min.js",
        deployment_mode="local",
    )
    return HTMLResponse(html, headers=web_artifacts.dashboard_security_headers())


def create_app() -> FastAPI:
    app = FastAPI(title="Whole-Brain Surrogate Dashboard")
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

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
    @app.get("/overview", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return _render_dashboard_page("overview")

    @app.get("/ranking", response_class=HTMLResponse)
    async def ranking() -> HTMLResponse:
        return _render_dashboard_page("mechanism_ranking")

    @app.get("/robustness", response_class=HTMLResponse)
    async def robustness() -> HTMLResponse:
        return _render_dashboard_page("robustness")

    @app.get("/prior-art", response_class=HTMLResponse)
    async def prior_art() -> HTMLResponse:
        return _render_dashboard_page("prior_art")

    @app.get("/empirical", response_class=HTMLResponse)
    async def empirical() -> HTMLResponse:
        return _render_dashboard_page("empirical")

    @app.get("/simulator", response_class=HTMLResponse)
    async def simulator() -> HTMLResponse:
        return _render_dashboard_page("simulator")

    @app.get("/thesis", response_class=HTMLResponse)
    @app.get("/thesis.html", response_class=HTMLResponse)
    async def thesis() -> HTMLResponse:
        return _render_dashboard_page("thesis")

    @app.get("/figures", response_class=HTMLResponse)
    @app.get("/figures.html", response_class=HTMLResponse)
    async def figures() -> HTMLResponse:
        return _render_dashboard_page("figures")

    @app.get("/dashboard", response_class=HTMLResponse)
    @app.get("/dashboard/", response_class=HTMLResponse)
    @app.get("/local-dashboard", response_class=HTMLResponse)
    @app.get("/local-dashboard/", response_class=HTMLResponse)
    @app.get("/dashboard/full", response_class=HTMLResponse)
    @app.get("/dashboard/full/", response_class=HTMLResponse)
    async def dashboard_alias() -> HTMLResponse:
        return _render_dashboard_page("overview")

    @app.get("/methods", response_class=HTMLResponse)
    @app.get("/methods.html", response_class=HTMLResponse)
    @app.get("/appendix", response_class=HTMLResponse)
    @app.get("/appendix.html", response_class=HTMLResponse)
    async def thesis_context_alias() -> HTMLResponse:
        return _render_dashboard_page("thesis")

    @app.get("/legacy-redirect", response_class=HTMLResponse, include_in_schema=False)
    async def legacy_redirect() -> HTMLResponse:
        return _render_dashboard_page("overview")

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

    @app.get("/api/public-site-data")
    async def public_site_data() -> dict[str, Any]:
        global _public_site_cache
        if _public_site_cache is None:
            _public_site_cache = build_public_site_payload(REPO_ROOT)
        return _public_site_cache

    @app.get("/api/prior-art-data")
    async def prior_art_data() -> dict[str, Any]:
        return build_prior_art_payload(REPO_ROOT)

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
