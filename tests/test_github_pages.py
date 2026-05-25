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


def test_build_github_pages_site_copies_microsite_and_claim_matrix_artifacts(tmp_path: Path) -> None:
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

    module.build_publication_package = lambda repo_root: {
        "thesis_microsite_html": output_dir / "thesis_microsite.html",
        "defense_presentation_html": output_dir / "defense_presentation.html",
        "thesis_report_markdown": output_dir / "thesis_report_revised.md",
    }
    module.build_thesis_evidence_loop = lambda repo_root: {}
    module.export_thesis_loop_tables = lambda repo_root, export_dir: {
        "workbook_path": (export_dir / "thesis_evidence_loop_tables.xlsx").as_posix(),
        "claim_matrix_csv": (export_dir / "claim_evidence_matrix.csv").as_posix(),
    }
    export_dir = claim_dir / "exports"
    export_dir.mkdir()
    (export_dir / "claim_evidence_matrix.csv").write_text("claim,status\nC,ready\n", encoding="utf-8")
    (export_dir / "thesis_evidence_loop_tables.xlsx").write_bytes(b"xlsx")

    outputs = module.build_github_pages_site(tmp_path, tmp_path / "_site")

    assert outputs["index"] == tmp_path / "_site" / "index.html"
    assert (tmp_path / "_site" / "index.html").read_text(encoding="utf-8") == "<html><title>Thesis</title></html>"
    assert (tmp_path / "_site" / "defense.html").exists()
    assert (tmp_path / "_site" / "artifacts" / "claim_evidence_matrix.csv").exists()
    assert (tmp_path / "_site" / "artifacts" / "claim_evidence_matrix.md").exists()
    assert (tmp_path / "_site" / "artifacts" / "thesis_evidence_loop_tables.xlsx").exists()
    manifest = json.loads((tmp_path / "_site" / "pages_manifest.json").read_text(encoding="utf-8"))
    assert manifest["claim_guardrail"].startswith("GitHub Pages is a static presentation")
    assert "artifacts/claim_evidence_matrix.csv" in manifest["artifacts"]
