from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_build_github_pages_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_github_pages.py"
    spec = importlib.util.spec_from_file_location("build_github_pages", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_github_pages_site_makes_root_the_static_dashboard_and_links_thesis_artifacts(tmp_path: Path) -> None:
    module = _load_build_github_pages_module()
    output_dir = tmp_path / "output" / "doc"
    output_dir.mkdir(parents=True)
    (output_dir / "thesis_microsite.html").write_text("<html><title>Thesis</title></html>", encoding="utf-8")
    (output_dir / "defense_presentation.html").write_text("<html><title>Defense</title></html>", encoding="utf-8")
    (output_dir / "thesis_report_revised.md").write_text("# Report\n", encoding="utf-8")
    claim_dir = tmp_path / "results" / "thesis_evidence_loop"
    claim_dir.mkdir(parents=True)
    (claim_dir / "claim_evidence_matrix.csv").write_text("claim,status\nC,ready\n", encoding="utf-8")
    (claim_dir / "claim_evidence_matrix.md").write_text("| claim | status |\n| --- | --- |\n", encoding="utf-8")
    rocket_dir = tmp_path / "results" / "training" / "rocket_condition_benchmark"
    rocket_dir.mkdir(parents=True)
    (rocket_dir / "benchmark_report.md").write_text("# ROCKET Condition Benchmark\n", encoding="utf-8")
    (rocket_dir / "comparison_summary.json").write_text('{"schema_version":"rocket_condition_benchmark.v1"}\n', encoding="utf-8")
    template_dir = tmp_path / "src" / "lsd_thesis" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / "dashboard.html").write_text(
        '<html><head><script src="/assets/plotly.min.js"></script></head>'
        "<script>"
        "dashboardState = await fetchJson('/api/dashboard-data');"
        "subjectDetail = await fetchJson(`/api/empirical-view?subject=${encodeURIComponent(subject)}&run=${encodeURIComponent(run)}`);"
        "document.getElementById('simulate').addEventListener('click', async () => {"
        "return `/artifacts/${path}`;"
        "if (!href.startsWith('/artifacts/')) return;"
        "</script></html>",
        encoding="utf-8",
    )

    module.build_publication_package = lambda repo_root: {
        "thesis_microsite_html": output_dir / "thesis_microsite.html",
        "defense_presentation_html": output_dir / "defense_presentation.html",
        "thesis_report_markdown": output_dir / "thesis_report_revised.md",
    }
    module.build_thesis_evidence_loop = lambda repo_root: {}
    module.build_dashboard_payload = lambda repo_root: {
        "artifact_links": {
            "reports": [
                {
                    "label": "Claim matrix",
                    "href": "/artifacts/results/thesis_evidence_loop/claim_evidence_matrix.csv",
                },
                {
                    "label": "ROCKET report",
                    "href": "/artifacts/results/training/rocket_condition_benchmark/benchmark_report.md",
                }
            ],
            "figures": [],
        }
    }
    module.export_thesis_loop_tables = lambda repo_root, export_dir: {
        "workbook_path": (export_dir / "thesis_evidence_loop_tables.xlsx").as_posix(),
        "claim_matrix_csv": (export_dir / "claim_evidence_matrix.csv").as_posix(),
    }
    module.get_plotlyjs = lambda: "window.Plotly={newPlot:function(){}};"
    export_dir = claim_dir / "exports"
    export_dir.mkdir()
    (export_dir / "claim_evidence_matrix.csv").write_text("claim,status\nC,ready\n", encoding="utf-8")
    (export_dir / "thesis_evidence_loop_tables.xlsx").write_bytes(b"xlsx")

    outputs = module.build_github_pages_site(tmp_path, tmp_path / "_site")

    assert outputs["index"] == tmp_path / "_site" / "index.html"
    index_html = (tmp_path / "_site" / "index.html").read_text(encoding="utf-8")
    assert "fetchJson('dashboard/dashboard-data.json')" in index_html
    assert 'src="dashboard/assets/plotly.min.js"' in index_html
    assert "artifacts/${path}" in index_html
    assert (tmp_path / "_site" / "thesis.html").read_text(encoding="utf-8") == "<html><title>Thesis</title></html>"
    assert (tmp_path / "_site" / "defense.html").exists()
    assert (tmp_path / "_site" / "artifacts" / "claim_evidence_matrix.csv").exists()
    assert (tmp_path / "_site" / "artifacts" / "claim_evidence_matrix.md").exists()
    assert (tmp_path / "_site" / "artifacts" / "thesis_evidence_loop_tables.xlsx").exists()
    assert (
        tmp_path / "_site" / "artifacts" / "results" / "training" / "rocket_condition_benchmark" / "benchmark_report.md"
    ).exists()
    assert (tmp_path / "_site" / "dashboard" / "index.html").exists()
    assert (tmp_path / "_site" / "dashboard" / "dashboard-data.json").exists()
    assert (tmp_path / "_site" / "dashboard" / "assets" / "plotly.min.js").exists()
    dashboard_html = (tmp_path / "_site" / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert 'src="assets/plotly.min.js"' in dashboard_html
    assert '<link rel="icon" href="data:,">' in dashboard_html
    assert "fetchJson('dashboard-data.json')" in dashboard_html
    assert "/api/empirical-view" not in dashboard_html
    assert "simulateButton.disabled = true" in dashboard_html
    assert "../artifacts/${path}" in dashboard_html
    manifest = json.loads((tmp_path / "_site" / "pages_manifest.json").read_text(encoding="utf-8"))
    assert manifest["claim_guardrail"].startswith("GitHub Pages is a static presentation")
    assert manifest["entrypoints"]["index"] == "index.html"
    assert manifest["entrypoints"]["thesis"] == "thesis.html"
    assert manifest["entrypoints"]["dashboard"] == "dashboard/index.html"
    assert "thesis.html" in manifest["artifacts"]
    assert "artifacts/claim_evidence_matrix.csv" in manifest["artifacts"]
    assert "artifacts/results/training/rocket_condition_benchmark/benchmark_report.md" in manifest["artifacts"]
