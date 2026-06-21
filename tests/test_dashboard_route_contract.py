from __future__ import annotations

from lsd_thesis.web.app import DASHBOARD_NAV, create_app
from lsd_thesis.web.site_payload import build_route_links


def test_local_dashboard_nav_and_fastapi_routes_are_stable() -> None:
    assert [item["id"] for item in DASHBOARD_NAV] == [
        "overview",
        "mechanism_ranking",
        "submission",
        "robustness",
        "prior_art",
        "empirical",
        "simulator",
        "thesis",
        "figures",
    ]

    for item in DASHBOARD_NAV:
        assert {"id", "label", "href", "icon", "title", "template"}.issubset(item)
        assert str(item["href"]).startswith("/")
        assert str(item["template"]).startswith("pages/")

    routes = {str(route.path) for route in create_app().routes}
    assert {
        "/",
        "/overview",
        "/ranking",
        "/submission",
        "/submission.html",
        "/robustness",
        "/prior-art",
        "/empirical",
        "/simulator",
        "/thesis",
        "/thesis.html",
        "/figures",
        "/figures.html",
        "/dashboard",
        "/dashboard/",
        "/local-dashboard",
        "/local-dashboard/",
        "/dashboard/full",
        "/dashboard/full/",
        "/methods",
        "/methods.html",
        "/appendix",
        "/appendix.html",
        "/api/dashboard-data",
        "/api/public-site-data",
        "/api/prior-art-data",
        "/api/empirical-view",
        "/api/simulate",
        "/artifacts/{artifact_path:path}",
    }.issubset(routes)


def test_public_site_route_links_keep_local_and_static_shapes() -> None:
    assert build_route_links(static=False) == {
        "home": "/",
        "submission": "/submission",
        "thesis": "/thesis",
        "dashboard": "/dashboard",
        "local_dashboard": "/local-dashboard",
        "methods": "/methods",
        "appendix": "/appendix",
    }
    assert build_route_links(static=True) == {
        "home": "index.html",
        "submission": "submission.html",
        "thesis": "thesis.html",
        "dashboard": "dashboard/",
        "local_dashboard": "methods.html#local-dashboard",
        "methods": "methods.html",
        "appendix": "appendix.html",
    }
    assert build_route_links(static=True, depth=1) == {
        "home": "../index.html",
        "submission": "../submission.html",
        "thesis": "../thesis.html",
        "dashboard": "../dashboard/",
        "local_dashboard": "../methods.html#local-dashboard",
        "methods": "../methods.html",
        "appendix": "../appendix.html",
    }
