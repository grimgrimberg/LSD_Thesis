from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
for path in (SRC_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# ruff: noqa: E402
from build_publication_package import build_publication_package
from export_thesis_loop_tables import export_thesis_loop_tables

from lsd_thesis.thesis_loop import build_thesis_evidence_loop


def _prepare_site_dir(repo_root: Path, site_dir: Path) -> Path:
    resolved_root = repo_root.resolve()
    resolved_site = site_dir.resolve()
    if resolved_site == resolved_root or resolved_root not in resolved_site.parents:
        raise ValueError(f"Refusing to build GitHub Pages outside the repository: {resolved_site}")
    if resolved_site.exists():
        shutil.rmtree(resolved_site)
    resolved_site.mkdir(parents=True, exist_ok=True)
    return resolved_site


def _copy_file(source: Path, destination: Path) -> Path | None:
    if not source.exists() or not source.is_file():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _copy_tree(source: Path, destination: Path) -> Path | None:
    if not source.exists() or not source.is_dir():
        return None
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return destination


def build_github_pages_site(repo_root: Path = REPO_ROOT, site_dir: Path | None = None) -> dict[str, Path]:
    repo_root = repo_root.resolve()
    site = _prepare_site_dir(repo_root, site_dir or repo_root / "_site")

    build_thesis_evidence_loop(repo_root)
    export_thesis_loop_tables(repo_root, repo_root / "results" / "thesis_evidence_loop" / "exports")
    publication_outputs = build_publication_package(repo_root)

    outputs: dict[str, Path] = {}
    index = _copy_file(Path(publication_outputs["thesis_microsite_html"]), site / "index.html")
    if index is None:
        raise FileNotFoundError("Publication package did not produce thesis_microsite.html.")
    outputs["index"] = index

    optional_files = {
        "defense": (Path(publication_outputs["defense_presentation_html"]), site / "defense.html"),
        "report_markdown": (Path(publication_outputs["thesis_report_markdown"]), site / "artifacts" / "thesis_report_revised.md"),
        "claim_matrix_csv": (
            repo_root / "results" / "thesis_evidence_loop" / "claim_evidence_matrix.csv",
            site / "artifacts" / "claim_evidence_matrix.csv",
        ),
        "claim_matrix_markdown": (
            repo_root / "results" / "thesis_evidence_loop" / "claim_evidence_matrix.md",
            site / "artifacts" / "claim_evidence_matrix.md",
        ),
        "claim_workbook": (
            repo_root / "results" / "thesis_evidence_loop" / "exports" / "thesis_evidence_loop_tables.xlsx",
            site / "artifacts" / "thesis_evidence_loop_tables.xlsx",
        ),
    }
    for name, (source, destination) in optional_files.items():
        copied = _copy_file(source, destination)
        if copied is not None:
            outputs[name] = copied

    figures = _copy_tree(repo_root / "output" / "doc" / "figures", site / "figures")
    if figures is not None:
        outputs["figures"] = figures

    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "claim_guardrail": (
            "GitHub Pages is a static presentation artifact. Treat blocked rows in the claim matrix as unresolved thesis work, "
            "not as completed scientific evidence."
        ),
        "entrypoints": {
            "index": "index.html",
            "defense": "defense.html" if "defense" in outputs else None,
        },
        "artifacts": sorted(
            path.relative_to(site).as_posix()
            for key, path in outputs.items()
            if key not in {"index", "figures"} and path.is_file()
        ),
    }
    manifest_path = site / "pages_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    outputs["manifest"] = manifest_path
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static GitHub Pages site for the thesis repo.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--site-dir", type=Path, default=REPO_ROOT / "_site")
    args = parser.parse_args()

    outputs = build_github_pages_site(args.repo_root, args.site_dir)
    print(json.dumps({name: path.as_posix() for name, path in outputs.items()}, indent=2), flush=True)


if __name__ == "__main__":
    main()
