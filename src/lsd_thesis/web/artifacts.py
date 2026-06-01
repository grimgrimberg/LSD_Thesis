from __future__ import annotations

from pathlib import Path

ALLOWED_ARTIFACT_ROOTS: tuple[tuple[str, ...], ...] = (
    ("docs", "stage_reports"),
    ("output", "doc"),
    ("results", "stage_1", "figures"),
    ("results", "stage_2", "figures"),
    ("results", "stage_3", "figures"),
    ("results", "stage_4", "figures"),
    ("results", "stage_2b", "figures"),
    ("results", "stage_5", "figures"),
    ("results", "dynamic_mechanism_ranking", "figures"),
    ("results", "dynamic_mechanism_ranking", "exports"),
    ("results", "dynamic_mechanism_ranking", "robustness"),
    ("results", "confound_controls"),
    ("results", "external_ingestion"),
    ("results", "literature_benchmark"),
    ("results", "parcellation_sensitivity"),
    ("results", "psilocybin_ds006072"),
    ("results", "receptor_priors"),
    ("results", "setting_seed", "dashboard"),
    ("results", "structural_connectome"),
    ("results", "thesis_evidence_loop"),
    ("results", "thesis_upgrade"),
    ("results", "reproducible_archive"),
)
TEMP_ARTIFACT_SUFFIXES = (".bak", ".log", ".old", ".part", ".tmp")
SAFE_ARTIFACT_EXTENSIONS = frozenset(
    {".csv", ".docx", ".html", ".json", ".md", ".pdf", ".pptx", ".svg", ".txt", ".xlsx", ".yaml", ".yml", ".png"}
)


def resolve_artifact_path(artifact_path: str, repo_root: Path) -> Path | None:
    relative = Path(artifact_path)
    if not is_allowed_artifact_relative_path(relative):
        return None
    resolved_root = repo_root.resolve()
    candidate = (resolved_root / relative).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError:
        return None
    return candidate


def is_allowed_artifact_relative_path(relative_path: Path) -> bool:
    parts = relative_path.parts
    if not parts or relative_path.is_absolute():
        return False
    if any(part.startswith(".") for part in parts):
        return False
    if relative_path.name.startswith("~$") or relative_path.suffix.lower() in TEMP_ARTIFACT_SUFFIXES:
        return False
    return any(parts[: len(root)] == root for root in ALLOWED_ARTIFACT_ROOTS)


def candidate_artifact_relative_paths(raw_path: str) -> list[str]:
    normalized = raw_path.replace("\\", "/").strip()
    candidates: list[str] = []
    for root in ALLOWED_ARTIFACT_ROOTS:
        marker = "/".join(root)
        if normalized == marker or normalized.startswith(f"{marker}/"):
            candidates.append(normalized)
        marker_with_prefix = f"/{marker}/"
        marker_index = normalized.find(marker_with_prefix)
        if marker_index >= 0:
            candidates.append(normalized[marker_index + 1 :])
    if normalized not in candidates:
        candidates.append(normalized)
    return candidates


def artifact_href_from_raw_path(raw_path: str, repo_root: Path) -> str | None:
    for candidate_path in candidate_artifact_relative_paths(raw_path):
        resolved = resolve_artifact_path(candidate_path, repo_root)
        if resolved is None or not resolved.exists():
            continue
        relative_path = resolved.relative_to(repo_root.resolve())
        return f"/artifacts/{relative_path.as_posix()}"
    return None


def artifact_href_from_path(path: Path, repo_root: Path) -> str | None:
    resolved_root = repo_root.resolve()
    try:
        relative_path = path.resolve().relative_to(resolved_root)
    except ValueError:
        return artifact_href_from_raw_path(str(path), repo_root)
    return artifact_href_from_raw_path(relative_path.as_posix(), repo_root)


def artifact_links(repo_root: Path) -> dict[str, list[dict[str, str]]]:
    report_specs = [
        ("PI Pitch", repo_root / "PI_PITCH.md"),
        ("PI Claim Ladder", repo_root / "CLAIM_LADDER.md"),
        ("Stage 2", repo_root / "docs" / "stage_reports" / "stage_2.md"),
        ("Dynamic Mechanism Ranking", repo_root / "docs" / "stage_reports" / "dynamic_mechanism_ranking.md"),
        ("Stage 3", repo_root / "docs" / "stage_reports" / "stage_3.md"),
        ("Stage 4", repo_root / "docs" / "stage_reports" / "stage_4.md"),
        ("Thesis Report Revised", repo_root / "output" / "doc" / "thesis_report_revised.md"),
        ("Thesis Report Revised DOCX", repo_root / "output" / "doc" / "thesis_report_revised.docx"),
        ("Defense Outline", repo_root / "output" / "doc" / "defense_outline.md"),
        ("Defense Outline DOCX", repo_root / "output" / "doc" / "defense_outline.docx"),
        ("Thesis Microsite", repo_root / "output" / "doc" / "thesis_microsite.html"),
        ("Set / Setting / Seed Microsite", repo_root / "output" / "doc" / "set_setting_seed_microsite.html"),
        ("Defense Presentation", repo_root / "output" / "doc" / "defense_presentation.html"),
        ("Defense Presentation PPTX", repo_root / "output" / "doc" / "defense_presentation.pptx"),
        ("Thesis Report Revised PDF", repo_root / "output" / "doc" / "thesis_report_revised.pdf"),
        (
            "Dynamic Mechanism Results XLSX",
            repo_root / "results" / "dynamic_mechanism_ranking" / "exports" / "dynamic_mechanism_results.xlsx",
        ),
        (
            "Dynamic Mechanism Export Manifest",
            repo_root / "results" / "dynamic_mechanism_ranking" / "exports" / "export_manifest.json",
        ),
        (
            "Dynamic Robustness Summary",
            repo_root / "results" / "dynamic_mechanism_ranking" / "robustness" / "robustness_summary.json",
        ),
        ("ROCKET Condition Benchmark Report", repo_root / "results" / "training" / "rocket_condition_benchmark" / "benchmark_report.md"),
        (
            "ROCKET Condition Benchmark Summary",
            repo_root / "results" / "training" / "rocket_condition_benchmark" / "comparison_summary.json",
        ),
        ("Motion Confound Control Status", repo_root / "results" / "confound_controls" / "motion_confound_control_status.json"),
        ("Motion Confound Control Report", repo_root / "results" / "confound_controls" / "motion_confound_control_status.md"),
        ("fMRIPrep Motion-Proof Preflight", repo_root / "results" / "confound_controls" / "fmriprep_motion_proof_plan.json"),
        (
            "fMRIPrep Motion-Proof Preflight Report",
            repo_root / "results" / "confound_controls" / "fmriprep_motion_proof_plan.md",
        ),
        ("Image-Derived Motion/QC Status", repo_root / "results" / "confound_controls" / "image_motion_qc_status.json"),
        ("Image-Derived Motion/QC Report", repo_root / "results" / "confound_controls" / "image_motion_qc_status.md"),
        (
            "Image-Derived Motion/QC Associations",
            repo_root / "results" / "confound_controls" / "image_motion_qc_dynamic_associations.csv",
        ),
        ("Thesis Upgrade Status", repo_root / "results" / "thesis_upgrade" / "thesis_upgrade_status.json"),
        ("Thesis Upgrade Report", repo_root / "results" / "thesis_upgrade" / "thesis_upgrade_status.md"),
        ("Reproducible Archive Manifest", repo_root / "results" / "reproducible_archive" / "ARCHIVE_MANIFEST.json"),
        ("Reproducible Archive Checksums", repo_root / "results" / "reproducible_archive" / "CHECKSUMS.sha256"),
        ("External Ingestion Status", repo_root / "results" / "external_ingestion" / "external_ingestion_status.json"),
        ("Thesis Evidence Loop Status", repo_root / "results" / "thesis_evidence_loop" / "thesis_evidence_loop_status.json"),
        ("Thesis Evidence Loop Table", repo_root / "results" / "thesis_evidence_loop" / "status_rows.csv"),
        ("Claim Evidence Matrix CSV", repo_root / "results" / "thesis_evidence_loop" / "claim_evidence_matrix.csv"),
        ("Claim Evidence Matrix Markdown", repo_root / "results" / "thesis_evidence_loop" / "claim_evidence_matrix.md"),
        (
            "Thesis Evidence Loop Workbook",
            repo_root / "results" / "thesis_evidence_loop" / "exports" / "thesis_evidence_loop_tables.xlsx",
        ),
        ("Psilocybin ds006072 Status", repo_root / "results" / "psilocybin_ds006072" / "psilocybin_ds006072_status.json"),
        ("Structural Connectome Status", repo_root / "results" / "structural_connectome" / "structural_connectome_status.json"),
        ("External Cortical Map Alignment", repo_root / "results" / "cortical_maps" / "cortical_map_alignment_status.json"),
        ("External Cortical Map Alignment Summary", repo_root / "results" / "cortical_maps" / "cortical_map_alignment.md"),
        ("Neuromaps Spatial Null Status", repo_root / "results" / "cortical_maps" / "neuromaps_spatial_null_status.json"),
        ("Neuromaps Spatial Null Report", repo_root / "results" / "cortical_maps" / "neuromaps_spatial_null_status.md"),
        ("Receptor Prior Status", repo_root / "results" / "receptor_priors" / "receptor_prior_status.json"),
        ("Parcellation Sensitivity Status", repo_root / "results" / "parcellation_sensitivity" / "parcellation_sensitivity_status.json"),
        ("Literature Benchmark Status", repo_root / "results" / "literature_benchmark" / "literature_benchmark_status.json"),
    ]
    reports = [
        {
            "label": label,
            "href": href,
        }
        for label, path in report_specs
        if path.exists()
        for href in [artifact_href_from_path(path, repo_root)]
        if href is not None
    ]
    figure_dir = repo_root / "output" / "doc" / "figures"
    figures = [
        {
            "label": path.stem.replace("_", " ").title(),
            "href": href,
        }
        for path in sorted(figure_dir.glob("*.png"))
        if path.is_file()
        for href in [artifact_href_from_path(path, repo_root)]
        if href is not None
    ]
    dynamic_figure_dir = repo_root / "results" / "dynamic_mechanism_ranking" / "figures"
    figures.extend(
        [
            {
                "label": f"Dynamic Mechanism: {path.stem.replace('_', ' ').title()}",
                "href": href,
            }
            for path in sorted(dynamic_figure_dir.glob("*.html"))
            if path.is_file()
            for href in [artifact_href_from_path(path, repo_root)]
            if href is not None
        ]
    )
    return {"reports": reports, "figures": figures}


def artifact_security_headers(candidate: Path, repo_root: Path) -> dict[str, str]:
    headers = {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "Cross-Origin-Resource-Policy": "same-origin",
    }
    suffix = candidate.suffix.lower()
    if suffix == ".html":
        relative = candidate.resolve().relative_to(repo_root.resolve())
        if "figures" in relative.parts and relative.parts[0] == "results":
            headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "script-src 'unsafe-inline' https://cdn.plot.ly; "
                "style-src 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "connect-src 'none'; "
                "object-src 'none'; "
                "base-uri 'none'; "
                "form-action 'none'; "
                "frame-ancestors 'none'; "
                "sandbox allow-scripts"
            )
        else:
            headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "style-src 'unsafe-inline'; "
                "img-src 'self' data:; "
                "script-src 'none'; "
                "object-src 'none'; "
                "base-uri 'none'; "
                "form-action 'none'; "
                "frame-ancestors 'none'; "
                "sandbox allow-same-origin"
            )
    elif suffix == ".svg":
        headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'none'; object-src 'none'; "
            "base-uri 'none'; form-action 'none'; frame-ancestors 'none'; sandbox"
        )
        headers["Content-Disposition"] = f'attachment; filename="{candidate.name}"'
    return headers


def dashboard_security_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "form-action 'none'; "
            "frame-ancestors 'none'"
        ),
    }
