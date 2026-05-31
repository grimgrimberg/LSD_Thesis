from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import stat
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
for path in (SRC_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# ruff: noqa: E402
from build_publication_package import build_publication_package
from export_thesis_loop_tables import export_thesis_loop_tables

from lsd_thesis.confound_controls import write_motion_confound_control_status
from lsd_thesis.cortical_maps import write_cortical_map_alignment_status
from lsd_thesis.design_confound_controls import write_design_confound_control_status
from lsd_thesis.ds006072_cifti_extraction import write_ds006072_cifti_extraction_status
from lsd_thesis.ds006072_payload_plan import write_ds006072_payload_plan_status
from lsd_thesis.image_motion_qc import write_image_motion_qc_status
from lsd_thesis.module_dvars_controls import write_module_dvars_control_status
from lsd_thesis.map_prior_falsification import write_map_prior_falsification_status
from lsd_thesis.neuromaps_spatial_nulls import write_neuromaps_spatial_null_status
from lsd_thesis.published_motion_qc import write_published_motion_qc_status
from lsd_thesis.setting_seed.motion import write_motion_outputs
from lsd_thesis.thesis_upgrade import write_thesis_upgrade_status
from lsd_thesis.thesis_loop import build_thesis_evidence_loop
from lsd_thesis.web.site_payload import build_public_site_payload, build_route_links

STATIC_FAVICON_TAG = '<link rel="icon" href="data:,">'


def _remove_tree(path: Path) -> None:
    def _make_writable_and_retry(function: Any, target: str, _exc_info: Any) -> None:
        os.chmod(target, stat.S_IWRITE)
        function(target)

    shutil.rmtree(path, onerror=_make_writable_and_retry)


def _prepare_site_dir(repo_root: Path, site_dir: Path) -> Path:
    resolved_root = repo_root.resolve()
    resolved_site = site_dir.resolve()
    if resolved_site == resolved_root or resolved_root not in resolved_site.parents:
        raise ValueError(f"Refusing to build GitHub Pages outside the repository: {resolved_site}")
    if resolved_site.exists():
        _remove_tree(resolved_site)
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
        _remove_tree(destination)
    shutil.copytree(source, destination)
    return destination


def _with_static_favicon(html: str) -> str:
    if STATIC_FAVICON_TAG in html:
        return html
    if "<head>" in html:
        return html.replace("<head>", f"<head>\n  {STATIC_FAVICON_TAG}", 1)
    return html


def _inject_static_favicon(path: Path) -> None:
    if path.suffix.lower() != ".html" or not path.exists():
        return
    path.write_text(_with_static_favicon(path.read_text(encoding="utf-8")), encoding="utf-8")


def _static_dashboard_html(
    template_path: Path,
    *,
    plotly_src: str = "assets/plotly.min.js",
    dashboard_data_src: str = "dashboard-data.json",
    artifact_prefix: str = "../artifacts/",
) -> str:
    html = template_path.read_text(encoding="utf-8")
    replacements = {
        'src="/assets/plotly.min.js"': f'src="{plotly_src}"',
        'href="/artifacts/': f'href="{artifact_prefix}',
        "fetchJson('/api/dashboard-data')": f"fetchJson('{dashboard_data_src}')",
        "subjectDetail = await fetchJson(`/api/empirical-view?subject=${encodeURIComponent(subject)}&run=${encodeURIComponent(run)}`);": (
            "subjectDetail = { error: 'Static GitHub Pages build: subject-level fMRI previews require the local FastAPI dashboard.' };"
        ),
        "return `/artifacts/${path}`;": f"return `{artifact_prefix}${{path}}`;",
        "href.startsWith('/artifacts/')": f"(href.startsWith('/artifacts/') || href.startsWith('{artifact_prefix}'))",
        "document.getElementById('simulate').addEventListener('click', async () => {": (
            "const simulateButton = document.getElementById('simulate');\n"
            "      simulateButton.disabled = true;\n"
            "      simulateButton.title = 'Static GitHub Pages build: simulation controls require the local FastAPI dashboard.';\n"
            "      simulateButton.addEventListener('click', async () => {"
        ),
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    return _with_static_favicon(html)


def _dashboard_artifact_path_from_href(href: str) -> str | None:
    for prefix in ("/artifacts/", "../artifacts/"):
        if href.startswith(prefix):
            return href.removeprefix(prefix)
    return None


def _copy_dashboard_linked_artifacts(repo_root: Path, site: Path, dashboard_payload: dict[str, Any]) -> list[str]:
    copied: list[str] = []
    allowed_prefixes = (
        "docs/",
        "output/doc/",
        "results/confound_controls/",
        "results/cortical_maps/",
        "results/dynamic_mechanism_ranking/",
        "results/external_ingestion/",
        "results/literature_benchmark/",
        "results/parcellation_sensitivity/",
        "results/psilocybin_ds006072/",
        "results/receptor_priors/",
        "results/stage_2/figures/",
        "results/structural_connectome/",
        "results/thesis_evidence_loop/",
        "results/thesis_upgrade/",
        "results/training/rocket_condition_benchmark/",
        "results/reproducible_archive/",
    )
    links: list[dict[str, Any]] = []
    artifact_links = dashboard_payload.get("artifact_links", {})
    if isinstance(artifact_links, dict):
        for bucket in artifact_links.values():
            if isinstance(bucket, list):
                links.extend(link for link in bucket if isinstance(link, dict))
    empirical_viewer = dashboard_payload.get("empirical_viewer", {})
    if isinstance(empirical_viewer, dict):
        links.extend(link for link in empirical_viewer.get("gallery", []) if isinstance(link, dict))
        links.extend(link for link in empirical_viewer.get("reports", []) if isinstance(link, dict))

    for link in links:
        relative = _dashboard_artifact_path_from_href(str(link.get("href", "")))
        if relative is None or not relative.startswith(allowed_prefixes):
            continue
        source = repo_root / relative
        if not source.exists() or not source.is_file():
            continue
        destination = site / "artifacts" / relative
        if _copy_file(source, destination) is not None:
            copied.append(destination.relative_to(site).as_posix())
    return sorted(set(copied))


def _published_artifact_paths(outputs: dict[str, Path], site: Path) -> list[str]:
    excluded = {"index", "thesis", "dashboard", "methods", "appendix", "dashboard_data"}
    paths: list[str] = []
    for key, path in outputs.items():
        if key in excluded:
            continue
        if path.is_file():
            paths.append(path.relative_to(site).as_posix())
        elif path.is_dir():
            paths.extend(child.relative_to(site).as_posix() for child in path.rglob("*") if child.is_file())
    return sorted(set(paths))


def _template_environment(repo_root: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(repo_root / "src" / "lsd_thesis" / "templates")),
        autoescape=select_autoescape(("html", "xml")),
    )


def _render_static_template(
    environment: Environment,
    template_name: str,
    payload: dict[str, Any],
    *,
    depth: int,
    artifact_prefix: str,
    data_url: str = "dashboard/dashboard-data.json",
) -> str:
    html = environment.get_template(template_name).render(
        payload=payload,
        links=build_route_links(static=True, depth=depth),
        artifact_prefix=artifact_prefix,
        data_url=data_url,
    )
    return _with_static_favicon(html)


def _write_static_public_site(repo_root: Path, site: Path) -> dict[str, Path | list[str]]:
    dashboard_dir = site / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    payload = build_public_site_payload(repo_root)
    environment = _template_environment(repo_root)

    dashboard_data = dashboard_dir / "dashboard-data.json"
    dashboard_data.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    root_html = site / "index.html"
    thesis_html = site / "thesis.html"
    dashboard_html = dashboard_dir / "index.html"
    methods_html = site / "methods.html"
    appendix_html = site / "appendix.html"

    root_html.write_text(
        _render_static_template(environment, "public_site.html", payload, depth=0, artifact_prefix="artifacts/"),
        encoding="utf-8",
    )
    thesis_html.write_text(
        _render_static_template(environment, "thesis_story.html", payload, depth=0, artifact_prefix="artifacts/"),
        encoding="utf-8",
    )
    dashboard_html.write_text(
        _render_static_template(
            environment,
            "evidence_dashboard.html",
            payload,
            depth=1,
            artifact_prefix="../artifacts/",
            data_url="dashboard-data.json",
        ),
        encoding="utf-8",
    )
    methods_html.write_text(
        _render_static_template(environment, "methods_reproducibility.html", payload, depth=0, artifact_prefix="artifacts/"),
        encoding="utf-8",
    )
    appendix_html.write_text(
        _render_static_template(environment, "appendix.html", payload, depth=0, artifact_prefix="artifacts/"),
        encoding="utf-8",
    )

    copied_artifacts = _copy_dashboard_linked_artifacts(repo_root, site, payload)
    return {
        "index": root_html,
        "thesis": thesis_html,
        "dashboard": dashboard_html,
        "dashboard_data": dashboard_data,
        "methods": methods_html,
        "appendix": appendix_html,
        "dashboard_artifacts": copied_artifacts,
    }


def build_github_pages_site(repo_root: Path = REPO_ROOT, site_dir: Path | None = None) -> dict[str, Path]:
    repo_root = repo_root.resolve()
    site = _prepare_site_dir(repo_root, site_dir or repo_root / "_site")

    build_thesis_evidence_loop(repo_root)
    export_thesis_loop_tables(repo_root, repo_root / "results" / "thesis_evidence_loop" / "exports")
    write_cortical_map_alignment_status(repo_root)
    write_motion_outputs(repo_root=repo_root)
    write_motion_confound_control_status(repo_root)
    write_design_confound_control_status(repo_root)
    write_module_dvars_control_status(repo_root)
    write_published_motion_qc_status(repo_root)
    write_image_motion_qc_status(repo_root, force=False)
    publication_outputs = build_publication_package(repo_root)
    write_neuromaps_spatial_null_status(repo_root)
    write_map_prior_falsification_status(repo_root)
    write_ds006072_payload_plan_status(repo_root)
    write_ds006072_cifti_extraction_status(repo_root)
    write_thesis_upgrade_status(repo_root)

    outputs: dict[str, Path] = {}

    optional_files = {
        "thesis_microsite": (Path(publication_outputs["thesis_microsite_html"]), site / "artifacts" / "thesis_microsite.html"),
        "defense": (Path(publication_outputs["defense_presentation_html"]), site / "artifacts" / "defense_presentation.html"),
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
        "claim_ladder": (
            repo_root / "CLAIM_LADDER.md",
            site / "artifacts" / "CLAIM_LADDER.md",
        ),
        "pi_pitch": (
            repo_root / "PI_PITCH.md",
            site / "artifacts" / "PI_PITCH.md",
        ),
    }
    for name, (source, destination) in optional_files.items():
        copied = _copy_file(source, destination)
        if copied is not None:
            _inject_static_favicon(copied)
            outputs[name] = copied

    figures = _copy_tree(repo_root / "output" / "doc" / "figures", site / "figures")
    if figures is not None:
        outputs["figures"] = figures
    cortical_maps = _copy_tree(repo_root / "results" / "cortical_maps", site / "artifacts" / "results" / "cortical_maps")
    if cortical_maps is not None:
        outputs["cortical_maps"] = cortical_maps
    confound_controls = _copy_tree(
        repo_root / "results" / "confound_controls", site / "artifacts" / "results" / "confound_controls"
    )
    if confound_controls is not None:
        outputs["confound_controls"] = confound_controls
    thesis_upgrade = _copy_tree(
        repo_root / "results" / "thesis_upgrade", site / "artifacts" / "results" / "thesis_upgrade"
    )
    if thesis_upgrade is not None:
        outputs["thesis_upgrade"] = thesis_upgrade
    psilocybin_ds006072 = _copy_tree(
        repo_root / "results" / "psilocybin_ds006072", site / "artifacts" / "results" / "psilocybin_ds006072"
    )
    if psilocybin_ds006072 is not None:
        outputs["psilocybin_ds006072"] = psilocybin_ds006072
    public_site_outputs = _write_static_public_site(repo_root, site)
    outputs.update({key: value for key, value in public_site_outputs.items() if isinstance(value, Path)})
    dashboard_artifacts = public_site_outputs.get("dashboard_artifacts", [])

    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "claim_guardrail": (
            "GitHub Pages is a static presentation and dashboard snapshot. Treat blocked rows in the claim matrix as unresolved thesis work, "
            "not as completed scientific evidence. Interactive FastAPI-only controls are available only in the local dashboard."
        ),
        "entrypoints": {
            "index": "index.html",
            "thesis": "thesis.html",
            "dashboard": "dashboard/index.html",
            "methods": "methods.html",
            "appendix": "appendix.html",
        },
        "artifacts": sorted(
            set(_published_artifact_paths(outputs, site))
            | set(dashboard_artifacts if isinstance(dashboard_artifacts, list) else [])
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
