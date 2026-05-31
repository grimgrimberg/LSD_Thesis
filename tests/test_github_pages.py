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


def _write_template_fixture(template_dir: Path) -> None:
    template_dir.mkdir(parents=True)
    (template_dir / "site_styles.html").write_text("<style>body{font-family:sans-serif}</style>", encoding="utf-8")
    (template_dir / "public_site.html").write_text(
        "<html><head></head><body>Pitch {{ payload.project.title }} {{ links.dashboard }}</body></html>",
        encoding="utf-8",
    )
    (template_dir / "thesis_story.html").write_text(
        "<html><head></head><body>Thesis {{ payload.claim_ladder.primary_claim }}</body></html>",
        encoding="utf-8",
    )
    (template_dir / "evidence_dashboard.html").write_text(
        "<html><head></head><body>Dashboard {{ data_url }} {{ artifact_prefix }}</body></html>",
        encoding="utf-8",
    )
    (template_dir / "methods_reproducibility.html").write_text(
        "<html><head></head><body>Methods {{ payload.methods.pipeline_steps[0] }}</body></html>",
        encoding="utf-8",
    )
    (template_dir / "appendix.html").write_text(
        "<html><head></head><body>Appendix {{ payload.appendix.all_artifacts|length }}</body></html>",
        encoding="utf-8",
    )


def test_build_github_pages_site_makes_pitch_story_dashboard_methods_and_appendix(tmp_path: Path) -> None:
    module = _load_build_github_pages_module()
    output_dir = tmp_path / "output" / "doc"
    output_dir.mkdir(parents=True)
    (output_dir / "thesis_microsite.html").write_text("<html><title>Old thesis artifact</title></html>", encoding="utf-8")
    (output_dir / "defense_presentation.html").write_text("<html><title>Defense artifact</title></html>", encoding="utf-8")
    (output_dir / "thesis_report_revised.md").write_text("# Report\n", encoding="utf-8")
    claim_dir = tmp_path / "results" / "thesis_evidence_loop"
    claim_dir.mkdir(parents=True)
    (claim_dir / "claim_evidence_matrix.csv").write_text("claim,status\nC,ready\n", encoding="utf-8")
    (claim_dir / "claim_evidence_matrix.md").write_text("| claim | status |\n| --- | --- |\n", encoding="utf-8")
    rocket_dir = tmp_path / "results" / "training" / "rocket_condition_benchmark"
    rocket_dir.mkdir(parents=True)
    (rocket_dir / "benchmark_report.md").write_text("# ROCKET Condition Benchmark\n", encoding="utf-8")
    _write_template_fixture(tmp_path / "src" / "lsd_thesis" / "templates")

    module.build_publication_package = lambda repo_root: {
        "thesis_microsite_html": output_dir / "thesis_microsite.html",
        "defense_presentation_html": output_dir / "defense_presentation.html",
        "thesis_report_markdown": output_dir / "thesis_report_revised.md",
    }
    module.build_thesis_evidence_loop = lambda repo_root: {}
    module.build_public_site_payload = lambda repo_root: {
        "project": {"title": "Fixture pitch"},
        "claim_ladder": {"primary_claim": "Fixture claim"},
        "methods": {"pipeline_steps": ["Raw fMRI"]},
        "appendix": {
            "all_artifacts": [
                {
                    "kind": "reports",
                    "label": "ROCKET report",
                    "href": "/artifacts/results/training/rocket_condition_benchmark/benchmark_report.md",
                }
            ]
        },
        "artifact_links": {
            "reports": [
                {
                    "label": "ROCKET report",
                    "href": "/artifacts/results/training/rocket_condition_benchmark/benchmark_report.md",
                }
            ],
            "figures": [],
        },
    }
    module.export_thesis_loop_tables = lambda repo_root, export_dir: {}
    export_dir = claim_dir / "exports"
    export_dir.mkdir()
    (export_dir / "thesis_evidence_loop_tables.xlsx").write_bytes(b"xlsx")

    outputs = module.build_github_pages_site(tmp_path, tmp_path / "_site")

    assert outputs["index"] == tmp_path / "_site" / "index.html"
    assert outputs["thesis"] == tmp_path / "_site" / "thesis.html"
    assert outputs["dashboard"] == tmp_path / "_site" / "dashboard" / "index.html"
    assert outputs["methods"] == tmp_path / "_site" / "methods.html"
    assert outputs["appendix"] == tmp_path / "_site" / "appendix.html"
    assert (tmp_path / "_site" / "dashboard" / "dashboard-data.json").exists()
    assert "dashboard-data.json" in (tmp_path / "_site" / "dashboard" / "index.html").read_text(encoding="utf-8")
    assert '<link rel="icon" href="data:,">' in (tmp_path / "_site" / "index.html").read_text(encoding="utf-8")
    assert (tmp_path / "_site" / "artifacts" / "claim_evidence_matrix.csv").exists()
    assert (tmp_path / "_site" / "artifacts" / "claim_evidence_matrix.md").exists()
    assert (tmp_path / "_site" / "artifacts" / "thesis_evidence_loop_tables.xlsx").exists()
    assert (tmp_path / "_site" / "artifacts" / "thesis_microsite.html").exists()
    assert (tmp_path / "_site" / "artifacts" / "defense_presentation.html").exists()
    assert (
        tmp_path / "_site" / "artifacts" / "results" / "training" / "rocket_condition_benchmark" / "benchmark_report.md"
    ).exists()
    manifest = json.loads((tmp_path / "_site" / "pages_manifest.json").read_text(encoding="utf-8"))
    assert manifest["claim_guardrail"].startswith("GitHub Pages is a static presentation")
    assert manifest["entrypoints"] == {
        "index": "index.html",
        "thesis": "thesis.html",
        "dashboard": "dashboard/index.html",
        "methods": "methods.html",
        "appendix": "appendix.html",
    }
    assert "artifacts/results/training/rocket_condition_benchmark/benchmark_report.md" in manifest["artifacts"]
