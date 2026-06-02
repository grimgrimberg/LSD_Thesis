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
    module.build_public_site_payload = lambda repo_root, dashboard_payload=None: {
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
    module.export_thesis_loop_tables = lambda repo_root, export_dir: {
        "workbook_path": (export_dir / "thesis_evidence_loop_tables.xlsx").as_posix(),
        "claim_matrix_csv": (export_dir / "claim_evidence_matrix.csv").as_posix(),
    }
    module.get_plotlyjs = lambda: "window.Plotly={newPlot:function(){}};"
    motion_root = tmp_path / "author_confounds"
    motion_events = []
    module.write_motion_outputs = lambda repo_root, roots=None: motion_events.append(
        ("summary", Path(repo_root), tuple(Path(item) for item in roots or ()))
    )
    module.write_motion_source_availability = lambda repo_root, roots=None, fetch_remote=False: motion_events.append(
        ("source", Path(repo_root), tuple(Path(item) for item in roots or ()), fetch_remote)
    )
    module.write_fmriprep_motion_proof_plan = lambda repo_root, roots=None, fetch_remote=False: motion_events.append(
        ("preflight", Path(repo_root), tuple(Path(item) for item in roots or ()), fetch_remote)
    )
    export_dir = claim_dir / "exports"
    export_dir.mkdir()
    (export_dir / "thesis_evidence_loop_tables.xlsx").write_bytes(b"xlsx")

    outputs = module.build_github_pages_site(
        tmp_path,
        tmp_path / "_site",
        motion_roots=(motion_root,),
        fetch_motion_remote=True,
    )

    assert outputs["index"] == tmp_path / "_site" / "index.html"
    assert motion_events == [
        ("summary", tmp_path, (motion_root,)),
        ("source", tmp_path, (motion_root,), True),
        ("preflight", tmp_path, (motion_root,), True),
    ]
    assert outputs["thesis"] == tmp_path / "_site" / "thesis.html"
    assert outputs["dashboard"] == tmp_path / "_site" / "dashboard" / "index.html"
    assert outputs["methods"] == tmp_path / "_site" / "methods.html"
    assert outputs["appendix"] == tmp_path / "_site" / "appendix.html"
    assert (tmp_path / "_site" / "dashboard" / "dashboard-data.json").exists()
    assert (tmp_path / "_site" / ".nojekyll").exists()
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


def test_build_github_pages_rejects_traversal_dashboard_artifact_links(tmp_path: Path) -> None:
    module = _load_build_github_pages_module()
    allowed_dir = tmp_path / "results" / "stage_2" / "figures"
    allowed_dir.mkdir(parents=True)
    (allowed_dir / "safe.html").write_text("<html>safe</html>", encoding="utf-8")
    secret_path = tmp_path / "secret.txt"
    secret_path.write_text("do not copy\n", encoding="utf-8")
    site = tmp_path / "_site"
    site.mkdir()

    copied = module._copy_dashboard_linked_artifacts(
        tmp_path,
        site,
        {
            "artifact_links": {
                "figures": [
                    {"href": "/artifacts/results/stage_2/figures/safe.html"},
                    {"href": "/artifacts/results/stage_2/figures/../../../secret.txt"},
                    {"href": "/artifacts/results/stage_2/figures/%2E%2E/%2E%2E/%2E%2E/secret.txt"},
                ]
            }
        },
    )

    assert copied == ["artifacts/results/stage_2/figures/safe.html"]
    assert (site / "artifacts" / "results" / "stage_2" / "figures" / "safe.html").exists()
    assert not (site / "artifacts" / "secret.txt").exists()


def test_build_github_pages_curated_tree_filters_raw_and_large_artifacts(tmp_path: Path) -> None:
    module = _load_build_github_pages_module()
    result_dir = tmp_path / "results" / "confound_controls"
    result_dir.mkdir(parents=True)
    (result_dir / "motion_confound_control_status.json").write_text("{}", encoding="utf-8")
    (result_dir / "raw_volume.nii.gz").write_bytes(b"raw")
    (result_dir / "too_large.json").write_text("12345", encoding="utf-8")
    module.PAGES_ARTIFACT_MAX_BYTES = 4

    copied = module._copy_curated_tree(
        tmp_path,
        result_dir,
        tmp_path / "_site" / "artifacts" / "results" / "confound_controls",
    )

    assert copied == tmp_path / "_site" / "artifacts" / "results" / "confound_controls"
    assert (copied / "motion_confound_control_status.json").exists()
    assert not (copied / "raw_volume.nii.gz").exists()
    assert not (copied / "too_large.json").exists()


def test_build_github_pages_preserves_copied_ds006072_extraction_details(tmp_path: Path) -> None:
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
    export_dir = claim_dir / "exports"
    export_dir.mkdir()
    (export_dir / "claim_evidence_matrix.csv").write_text("claim,status\nC,ready\n", encoding="utf-8")
    (export_dir / "thesis_evidence_loop_tables.xlsx").write_bytes(b"xlsx")
    template_dir = tmp_path / "src" / "lsd_thesis" / "templates"
    _write_template_fixture(template_dir)
    result_dir = tmp_path / "results" / "psilocybin_ds006072"
    subject_views = result_dir / "empirical_viewer" / "subject_views"
    schaefer_views = result_dir / "parcellations" / "schaefer_100_yeo_7" / "empirical_viewer" / "subject_views"
    subject_views.mkdir(parents=True)
    schaefer_views.mkdir(parents=True)
    (result_dir / "minimum_payload_plan.json").write_text(
        json.dumps(
            {
                "minimum_subjects_required": 3,
                "minimum_payloads_local_ready": True,
                "minimum_payload_plan_ready": True,
            }
        ),
        encoding="utf-8",
    )
    for index in range(3):
        (subject_views / f"P{index + 1}_run-01.json").write_text("{}", encoding="utf-8")
        (schaefer_views / f"P{index + 1}_run-01.json").write_text("{}", encoding="utf-8")
    (result_dir / "cifti_empirical_extraction_status.json").write_text(
        json.dumps(
            {
                "execute_requested": True,
                "extraction_result": {"subjects_written": ["P1", "P2", "P3"]},
                "schaefer100_extraction_result": {
                    "subjects_written": ["P1", "P2", "P3"],
                    "parcellation_id": "schaefer_100_yeo_7",
                },
            }
        ),
        encoding="utf-8",
    )

    module.build_publication_package = lambda repo_root: {
        "thesis_microsite_html": output_dir / "thesis_microsite.html",
        "defense_presentation_html": output_dir / "defense_presentation.html",
        "thesis_report_markdown": output_dir / "thesis_report_revised.md",
    }
    module.build_thesis_evidence_loop = lambda repo_root: {}
    module.build_public_site_payload = lambda repo_root, dashboard_payload=None: {
        "project": {"title": "Fixture pitch"},
        "claim_ladder": {"primary_claim": "Fixture claim"},
        "methods": {"pipeline_steps": ["Raw fMRI"]},
        "appendix": {"all_artifacts": []},
        "artifact_links": {"reports": [], "figures": []},
    }
    module.export_thesis_loop_tables = lambda repo_root, export_dir: {
        "workbook_path": (export_dir / "thesis_evidence_loop_tables.xlsx").as_posix(),
        "claim_matrix_csv": (export_dir / "claim_evidence_matrix.csv").as_posix(),
    }
    module.get_plotlyjs = lambda: "window.Plotly={newPlot:function(){}};"

    module.build_github_pages_site(tmp_path, tmp_path / "_site")

    copied_status = json.loads(
        (
            tmp_path
            / "_site"
            / "artifacts"
            / "results"
            / "psilocybin_ds006072"
            / "cifti_empirical_extraction_status.json"
        ).read_text(encoding="utf-8")
    )
    assert copied_status["extraction_result"] == {"subjects_written": ["P1", "P2", "P3"]}
    assert copied_status["schaefer100_extraction_result"]["parcellation_id"] == "schaefer_100_yeo_7"
    assert copied_status["extraction_result_source"] == "existing_status_cache"
    assert copied_status["schaefer100_extraction_result_source"] == "existing_status_cache"
