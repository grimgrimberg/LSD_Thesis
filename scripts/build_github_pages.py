from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs

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
from lsd_thesis.fmriprep_motion_proof import write_fmriprep_motion_proof_plan
from lsd_thesis.image_motion_qc import write_image_motion_qc_status
from lsd_thesis.map_prior_falsification import write_map_prior_falsification_status
from lsd_thesis.module_dvars_controls import write_module_dvars_control_status
from lsd_thesis.motion_source_availability import write_motion_source_availability
from lsd_thesis.neuromaps_spatial_nulls import write_neuromaps_spatial_null_status
from lsd_thesis.published_motion_qc import write_published_motion_qc_status
from lsd_thesis.reproducible_archive import existing_publication_metadata_args, write_archive_manifest
from lsd_thesis.setting_seed.motion import write_motion_outputs
from lsd_thesis.thesis_loop import build_thesis_evidence_loop
from lsd_thesis.thesis_upgrade import write_thesis_upgrade_status
from lsd_thesis.web.app import DASHBOARD_NAV, build_dashboard_payload
from lsd_thesis.web.artifacts import SAFE_ARTIFACT_EXTENSIONS, is_allowed_artifact_relative_path
from lsd_thesis.web.prior_art_payload import build_prior_art_payload

STATIC_FAVICON_TAG = '<link rel="icon" href="data:,">'
PAGES_ARTIFACT_MAX_BYTES = 20 * 1024 * 1024
PUBLISH_TEMP_SUFFIXES = (".bak", ".log", ".old", ".part", ".tmp")


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

    def _ignore_publish_temp(_directory: str, names: list[str]) -> list[str]:
        return [
            name
            for name in names
            if name.startswith("~$") or name.lower().endswith(PUBLISH_TEMP_SUFFIXES)
        ]

    shutil.copytree(source, destination, ignore=_ignore_publish_temp)
    return destination


def _is_publishable_artifact_file(path: Path) -> bool:
    if path.suffix.lower() not in SAFE_ARTIFACT_EXTENSIONS:
        return False
    return path.stat().st_size <= PAGES_ARTIFACT_MAX_BYTES


def _copy_curated_tree(repo_root: Path, source: Path, destination: Path) -> Path | None:
    if not source.exists() or not source.is_dir():
        return None
    if destination.exists():
        _remove_tree(destination)
    copied_any = False
    resolved_root = repo_root.resolve()
    for child in source.rglob("*"):
        if not child.is_file() or not _is_publishable_artifact_file(child):
            continue
        try:
            repo_relative = child.resolve().relative_to(resolved_root)
        except ValueError:
            continue
        if not is_allowed_artifact_relative_path(repo_relative):
            continue
        relative = child.relative_to(source)
        copied = _copy_file(child, destination / relative)
        copied_any = copied_any or copied is not None
    return destination if copied_any else None


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
    normalized = unquote(href).replace("\\", "/").split("#", 1)[0].split("?", 1)[0]
    for prefix in ("/artifacts/", "../artifacts/"):
        if normalized.startswith(prefix):
            return normalized.removeprefix(prefix)
    return None


def _resolve_dashboard_artifact_source(repo_root: Path, raw_relative: str, allowed_prefixes: tuple[str, ...]) -> tuple[Path, str] | None:
    relative_path = Path(raw_relative)
    if relative_path.is_absolute() or any(part in {"", ".", ".."} for part in relative_path.parts):
        return None
    relative_posix = relative_path.as_posix()
    if not relative_posix.startswith(allowed_prefixes):
        return None
    resolved_root = repo_root.resolve()
    source = (resolved_root / relative_path).resolve()
    try:
        canonical_relative = source.relative_to(resolved_root).as_posix()
    except ValueError:
        return None
    if not canonical_relative.startswith(allowed_prefixes):
        return None
    if not is_allowed_artifact_relative_path(Path(canonical_relative)):
        return None
    return source, canonical_relative


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
        raw_relative = _dashboard_artifact_path_from_href(str(link.get("href", "")))
        if raw_relative is None:
            continue
        resolved = _resolve_dashboard_artifact_source(repo_root, raw_relative, allowed_prefixes)
        if resolved is None:
            continue
        source, relative = resolved
        if not source.exists() or not source.is_file() or not _is_publishable_artifact_file(source):
            continue
        destination = site / "artifacts" / relative
        if _copy_file(source, destination) is not None:
            copied.append(destination.relative_to(site).as_posix())
    return sorted(set(copied))


def _copy_prior_art_documents(repo_root: Path, site: Path, prior_art_payload: dict[str, Any]) -> list[str]:
    copied: list[str] = []
    documents = prior_art_payload.get("documents", [])
    if not isinstance(documents, list):
        return copied
    for document in documents:
        if not isinstance(document, dict):
            continue
        raw_relative = _dashboard_artifact_path_from_href(str(document.get("href", "")))
        if raw_relative is None:
            continue
        resolved = _resolve_dashboard_artifact_source(repo_root, raw_relative, ("prior_art/",))
        if resolved is None:
            continue
        source, relative = resolved
        if not source.exists() or not source.is_file() or not _is_publishable_artifact_file(source):
            continue
        destination = site / "artifacts" / relative
        if _copy_file(source, destination) is not None:
            copied.append(destination.relative_to(site).as_posix())
    return sorted(set(copied))


def _published_artifact_paths(outputs: dict[str, Path], site: Path) -> list[str]:
    excluded = {
        "index",
        "ranking",
        "robustness",
        "prior_art",
        "empirical",
        "simulator",
        "thesis",
        "methods",
        "appendix",
        "dashboard",
        "dashboard_data",
        "prior_art_data",
    }
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


def _static_nav_items(depth: int) -> list[dict[str, str]]:
    prefix = "../" * max(depth, 0)
    href_by_id = {
        "overview": f"{prefix}index.html",
        "mechanism_ranking": f"{prefix}ranking.html",
        "robustness": f"{prefix}robustness.html",
        "prior_art": f"{prefix}prior-art.html",
        "empirical": f"{prefix}empirical.html",
        "simulator": f"{prefix}simulator.html",
        "thesis": f"{prefix}thesis.html",
    }
    return [{**item, "href": href_by_id.get(str(item["id"]), str(item["href"]))} for item in DASHBOARD_NAV]


def _render_static_template(
    environment: Environment,
    template_name: str,
    *,
    page_id: str,
    page_title: str,
    depth: int,
    data_url: str,
    prior_art_data_url: str,
) -> str:
    prefix = "../" * max(depth, 0)
    html = environment.get_template(template_name).render(
        page_title=page_title,
        active_page=page_id,
        nav_items=_static_nav_items(depth),
        home_href=f"{prefix}index.html",
        artifact_prefix=f"{prefix}artifacts/",
        data_url=data_url,
        prior_art_data_url=prior_art_data_url,
        static_prefix=f"{prefix}static/",
        plotly_src=f"{prefix}assets/plotly.min.js",
        deployment_mode="static",
    )
    return _with_static_favicon(html)


def _write_static_public_site(
    repo_root: Path,
    site: Path,
    *,
    dashboard_payload: dict[str, Any] | None = None,
) -> dict[str, Path | list[str]]:
    dashboard_dir = site / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    if dashboard_payload is None:
        dashboard_payload = build_dashboard_payload(repo_root)
    prior_art_payload = build_prior_art_payload(repo_root)
    environment = _template_environment(repo_root)

    dashboard_data = dashboard_dir / "dashboard-data.json"
    dashboard_data.write_text(json.dumps(dashboard_payload, indent=2), encoding="utf-8")
    prior_art_data = dashboard_dir / "prior-art-data.json"
    prior_art_data.write_text(json.dumps(prior_art_payload, indent=2), encoding="utf-8")

    root_html = site / "index.html"
    ranking_html = site / "ranking.html"
    robustness_html = site / "robustness.html"
    prior_art_html = site / "prior-art.html"
    empirical_html = site / "empirical.html"
    simulator_html = site / "simulator.html"
    thesis_html = site / "thesis.html"
    methods_html = site / "methods.html"
    appendix_html = site / "appendix.html"
    dashboard_html = dashboard_dir / "index.html"

    static_dir = _copy_tree(repo_root / "src" / "lsd_thesis" / "static", site / "static")
    assets_dir = site / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    plotly_asset = assets_dir / "plotly.min.js"
    plotly_asset.write_text(get_plotlyjs(), encoding="utf-8")

    root_html.write_text(
        _render_static_template(
            environment,
            "pages/overview.html",
            page_id="overview",
            page_title="Overview",
            depth=0,
            data_url="dashboard/dashboard-data.json",
            prior_art_data_url="dashboard/prior-art-data.json",
        ),
        encoding="utf-8",
    )
    ranking_html.write_text(
        _render_static_template(
            environment,
            "pages/mechanism_ranking.html",
            page_id="mechanism_ranking",
            page_title="Mechanism Ranking",
            depth=0,
            data_url="dashboard/dashboard-data.json",
            prior_art_data_url="dashboard/prior-art-data.json",
        ),
        encoding="utf-8",
    )
    robustness_html.write_text(
        _render_static_template(
            environment,
            "pages/robustness.html",
            page_id="robustness",
            page_title="Robustness",
            depth=0,
            data_url="dashboard/dashboard-data.json",
            prior_art_data_url="dashboard/prior-art-data.json",
        ),
        encoding="utf-8",
    )
    prior_art_html.write_text(
        _render_static_template(
            environment,
            "pages/prior_art.html",
            page_id="prior_art",
            page_title="Prior-Art Inventory",
            depth=0,
            data_url="dashboard/dashboard-data.json",
            prior_art_data_url="dashboard/prior-art-data.json",
        ),
        encoding="utf-8",
    )
    empirical_html.write_text(
        _render_static_template(
            environment,
            "pages/empirical.html",
            page_id="empirical",
            page_title="Empirical Viewer",
            depth=0,
            data_url="dashboard/dashboard-data.json",
            prior_art_data_url="dashboard/prior-art-data.json",
        ),
        encoding="utf-8",
    )
    simulator_html.write_text(
        _render_static_template(
            environment,
            "pages/simulator.html",
            page_id="simulator",
            page_title="Simulator",
            depth=0,
            data_url="dashboard/dashboard-data.json",
            prior_art_data_url="dashboard/prior-art-data.json",
        ),
        encoding="utf-8",
    )
    thesis_html.write_text(
        _render_static_template(
            environment,
            "pages/thesis.html",
            page_id="thesis",
            page_title="Thesis Presentation",
            depth=0,
            data_url="dashboard/dashboard-data.json",
            prior_art_data_url="dashboard/prior-art-data.json",
        ),
        encoding="utf-8",
    )
    methods_html.write_text(
        _render_static_template(
            environment,
            "pages/thesis.html",
            page_id="thesis",
            page_title="Thesis Presentation",
            depth=0,
            data_url="dashboard/dashboard-data.json",
            prior_art_data_url="dashboard/prior-art-data.json",
        ),
        encoding="utf-8",
    )
    appendix_html.write_text(
        _render_static_template(
            environment,
            "pages/thesis.html",
            page_id="thesis",
            page_title="Thesis Presentation",
            depth=0,
            data_url="dashboard/dashboard-data.json",
            prior_art_data_url="dashboard/prior-art-data.json",
        ),
        encoding="utf-8",
    )
    dashboard_html.write_text(
        _render_static_template(
            environment,
            "pages/overview.html",
            page_id="overview",
            page_title="Overview",
            depth=1,
            data_url="dashboard-data.json",
            prior_art_data_url="prior-art-data.json",
        ),
        encoding="utf-8",
    )

    copied_artifacts = _copy_dashboard_linked_artifacts(repo_root, site, dashboard_payload)
    copied_artifacts.extend(_copy_prior_art_documents(repo_root, site, prior_art_payload))
    return {
        "index": root_html,
        "ranking": ranking_html,
        "robustness": robustness_html,
        "prior_art": prior_art_html,
        "empirical": empirical_html,
        "simulator": simulator_html,
        "thesis": thesis_html,
        "methods": methods_html,
        "appendix": appendix_html,
        "dashboard": dashboard_html,
        "dashboard_data": dashboard_data,
        "prior_art_data": prior_art_data,
        "static": static_dir if static_dir is not None else site / "static",
        "plotly": plotly_asset,
        "dashboard_artifacts": copied_artifacts,
    }


def _write_pages_manifest(site: Path, outputs: dict[str, Path], dashboard_artifacts: list[Any]) -> Path:
    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "claim_guardrail": (
            "GitHub Pages is a static presentation and dashboard snapshot. Treat blocked rows in the claim matrix as unresolved thesis work, "
            "not as completed scientific evidence. Interactive FastAPI-only controls are available only in the local dashboard."
        ),
        "entrypoints": {
            "index": "index.html",
            "dashboard": "dashboard/index.html",
            "ranking": "ranking.html",
            "robustness": "robustness.html",
            "prior_art": "prior-art.html",
            "empirical": "empirical.html",
            "simulator": "simulator.html",
            "thesis": "thesis.html",
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
    return manifest_path


def _dashboard_payload_with_refreshed_thesis_status(
    site: Path,
    refreshed_status: dict[str, Any],
) -> dict[str, Any] | None:
    dashboard_data_path = site / "dashboard" / "dashboard-data.json"
    if not dashboard_data_path.exists():
        return None
    dashboard_payload = json.loads(dashboard_data_path.read_text(encoding="utf-8"))
    if not isinstance(dashboard_payload, dict):
        return None
    dashboard_payload = dict(dashboard_payload)
    dashboard_payload["thesis_upgrade"] = refreshed_status
    return dashboard_payload


def build_github_pages_site(
    repo_root: Path = REPO_ROOT,
    site_dir: Path | None = None,
    *,
    motion_roots: Sequence[str | Path] | None = None,
    fetch_motion_remote: bool = False,
) -> dict[str, Path]:
    repo_root = repo_root.resolve()
    site = _prepare_site_dir(repo_root, site_dir or repo_root / "_site")
    resolved_motion_roots = [Path(item) for item in motion_roots] if motion_roots else None

    build_thesis_evidence_loop(repo_root)
    export_thesis_loop_tables(repo_root, repo_root / "results" / "thesis_evidence_loop" / "exports")
    write_cortical_map_alignment_status(repo_root)
    write_motion_outputs(repo_root=repo_root, roots=resolved_motion_roots)
    if resolved_motion_roots or fetch_motion_remote:
        write_motion_source_availability(
            repo_root=repo_root,
            roots=resolved_motion_roots,
            fetch_remote=fetch_motion_remote,
        )
    write_fmriprep_motion_proof_plan(
        repo_root,
        roots=resolved_motion_roots,
        fetch_remote=fetch_motion_remote,
    )
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
    nojekyll = site / ".nojekyll"
    nojekyll.write_text("", encoding="utf-8")
    outputs["nojekyll"] = nojekyll

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
    doc_bundle = _copy_curated_tree(repo_root, repo_root / "output" / "doc", site / "artifacts" / "output" / "doc")
    if doc_bundle is not None:
        outputs["doc_bundle"] = doc_bundle
    dynamic_mechanism = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "dynamic_mechanism_ranking",
        site / "artifacts" / "results" / "dynamic_mechanism_ranking",
    )
    if dynamic_mechanism is not None:
        outputs["dynamic_mechanism"] = dynamic_mechanism
    stage2_figures = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "stage_2" / "figures",
        site / "artifacts" / "results" / "stage_2" / "figures",
    )
    if stage2_figures is not None:
        outputs["stage2_figures"] = stage2_figures
    cortical_maps = _copy_curated_tree(
        repo_root, repo_root / "results" / "cortical_maps", site / "artifacts" / "results" / "cortical_maps"
    )
    if cortical_maps is not None:
        outputs["cortical_maps"] = cortical_maps
    confound_controls = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "confound_controls",
        site / "artifacts" / "results" / "confound_controls",
    )
    if confound_controls is not None:
        outputs["confound_controls"] = confound_controls
    thesis_upgrade = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "thesis_upgrade",
        site / "artifacts" / "results" / "thesis_upgrade",
    )
    if thesis_upgrade is not None:
        outputs["thesis_upgrade"] = thesis_upgrade
    psilocybin_ds006072 = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "psilocybin_ds006072",
        site / "artifacts" / "results" / "psilocybin_ds006072",
    )
    if psilocybin_ds006072 is not None:
        outputs["psilocybin_ds006072"] = psilocybin_ds006072
    receptor_priors = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "receptor_priors",
        site / "artifacts" / "results" / "receptor_priors",
    )
    if receptor_priors is not None:
        outputs["receptor_priors"] = receptor_priors
    structural_connectome = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "structural_connectome",
        site / "artifacts" / "results" / "structural_connectome",
    )
    if structural_connectome is not None:
        outputs["structural_connectome"] = structural_connectome
    parcellation_sensitivity = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "parcellation_sensitivity",
        site / "artifacts" / "results" / "parcellation_sensitivity",
    )
    if parcellation_sensitivity is not None:
        outputs["parcellation_sensitivity"] = parcellation_sensitivity
    literature_benchmark = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "literature_benchmark",
        site / "artifacts" / "results" / "literature_benchmark",
    )
    if literature_benchmark is not None:
        outputs["literature_benchmark"] = literature_benchmark
    reproducible_archive = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "reproducible_archive",
        site / "artifacts" / "results" / "reproducible_archive",
    )
    if reproducible_archive is not None:
        outputs["reproducible_archive"] = reproducible_archive
    public_site_outputs = _write_static_public_site(repo_root, site)
    outputs.update({key: value for key, value in public_site_outputs.items() if isinstance(value, Path)})
    dashboard_artifacts = public_site_outputs.get("dashboard_artifacts", [])
    outputs["manifest"] = _write_pages_manifest(site, outputs, dashboard_artifacts if isinstance(dashboard_artifacts, list) else [])

    refreshed_status = write_thesis_upgrade_status(repo_root)
    thesis_upgrade = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "thesis_upgrade",
        site / "artifacts" / "results" / "thesis_upgrade",
    )
    if thesis_upgrade is not None:
        outputs["thesis_upgrade"] = thesis_upgrade
    refreshed_dashboard_payload = _dashboard_payload_with_refreshed_thesis_status(site, refreshed_status)
    public_site_outputs = _write_static_public_site(
        repo_root,
        site,
        dashboard_payload=refreshed_dashboard_payload,
    )
    outputs.update({key: value for key, value in public_site_outputs.items() if isinstance(value, Path)})
    dashboard_artifacts = public_site_outputs.get("dashboard_artifacts", [])
    outputs["manifest"] = _write_pages_manifest(site, outputs, dashboard_artifacts if isinstance(dashboard_artifacts, list) else [])

    final_status = write_thesis_upgrade_status(repo_root)
    thesis_upgrade = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "thesis_upgrade",
        site / "artifacts" / "results" / "thesis_upgrade",
    )
    if thesis_upgrade is not None:
        outputs["thesis_upgrade"] = thesis_upgrade
    final_dashboard_payload = _dashboard_payload_with_refreshed_thesis_status(site, final_status)
    public_site_outputs = _write_static_public_site(
        repo_root,
        site,
        dashboard_payload=final_dashboard_payload,
    )
    outputs.update({key: value for key, value in public_site_outputs.items() if isinstance(value, Path)})
    dashboard_artifacts = public_site_outputs.get("dashboard_artifacts", [])
    write_archive_manifest(repo_root, **existing_publication_metadata_args(repo_root))
    reproducible_archive = _copy_curated_tree(
        repo_root,
        repo_root / "results" / "reproducible_archive",
        site / "artifacts" / "results" / "reproducible_archive",
    )
    if reproducible_archive is not None:
        outputs["reproducible_archive"] = reproducible_archive
    outputs["manifest"] = _write_pages_manifest(site, outputs, dashboard_artifacts if isinstance(dashboard_artifacts, list) else [])
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static GitHub Pages site for the thesis repo.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--site-dir", type=Path, default=REPO_ROOT / "_site")
    parser.add_argument(
        "--motion-root",
        action="append",
        dest="motion_roots",
        help="Additional/local root to search for authorized fMRIPrep confounds before publishing motion artifacts.",
    )
    parser.add_argument(
        "--fetch-motion-remote",
        action="store_true",
        help="Query OpenNeuro snapshot metadata before publishing motion-proof artifacts.",
    )
    args = parser.parse_args()

    outputs = build_github_pages_site(
        args.repo_root,
        args.site_dir,
        motion_roots=[Path(item) for item in args.motion_roots] if args.motion_roots else None,
        fetch_motion_remote=args.fetch_motion_remote,
    )
    print(json.dumps({name: path.as_posix() for name, path in outputs.items()}, indent=2), flush=True)


if __name__ == "__main__":
    main()
