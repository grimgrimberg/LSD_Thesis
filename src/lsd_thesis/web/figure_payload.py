from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lsd_thesis.web import artifacts as web_artifacts

FigureExplainer = dict[str, Any]


def _text(value: object, fallback: str = "not reported") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _records(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _artifact(repo_root: Path, path: str, label: str | None = None) -> dict[str, Any]:
    href = web_artifacts.artifact_href_from_raw_path(path, repo_root)
    return {
        "label": label or Path(path).name,
        "path": path,
        "href": href,
        "exists": (repo_root / path).exists(),
        "public": href is not None,
    }


def _artifacts(repo_root: Path, paths: list[tuple[str, str]]) -> list[dict[str, Any]]:
    return [_artifact(repo_root, path, label) for label, path in paths]


def _first_href(items: list[dict[str, Any]]) -> str | None:
    for item in items:
        href = item.get("href")
        if isinstance(href, str) and href:
            return href
    return None


def _explainer(
    repo_root: Path,
    *,
    plot_id: str,
    title: str,
    subtitle: str,
    input_artifacts: list[tuple[str, str]],
    metric_definition: str,
    aggregation_level: str,
    calculation: str,
    caveat: str,
    claim_status: str,
    export_target: tuple[str, str] | None = None,
    page_href: str | None = None,
) -> FigureExplainer:
    artifact_payload = _artifacts(repo_root, input_artifacts)
    export_artifact = _artifact(repo_root, export_target[1], export_target[0]) if export_target else None
    export_href = export_artifact.get("href") if export_artifact else _first_href(artifact_payload)
    return {
        "plot_id": plot_id,
        "title": title,
        "subtitle": subtitle,
        "input_artifacts": artifact_payload,
        "metric_definition": metric_definition,
        "aggregation_level": aggregation_level,
        "calculation": calculation,
        "formula_summary": calculation,
        "caveat": caveat,
        "claim_status": claim_status,
        "export_target": export_artifact,
        "export_href": export_href,
        "page_href": page_href,
    }


def _strict_gate_status(dashboard_payload: Mapping[str, Any]) -> tuple[str, str]:
    thesis_upgrade = _mapping(dashboard_payload.get("thesis_upgrade"))
    summary = _mapping(thesis_upgrade.get("readiness_summary"))
    complete = int(summary.get("strict_complete_gates") or 0)
    total = int(summary.get("strict_total_gates") or 0)
    status = _text(summary.get("thesis_status") or summary.get("completion_status"), "strict gates reported")
    claim_status = "implemented" if total and complete == total else "blocked"
    return f"{complete}/{total} strict gates complete; {status}", claim_status


def _dynamic_status(dashboard_payload: Mapping[str, Any]) -> tuple[str, str]:
    dynamic = _mapping(dashboard_payload.get("dynamic_mechanism"))
    rows = _records(dynamic.get("mechanism_ranking"))
    best = rows[0] if rows else {}
    layer = _text(best.get("layer"), "no ranked layer")
    status = _text(dynamic.get("analysis_status"), "missing")
    claim_status = "proxy-supported" if rows else "blocked"
    return f"{status}; current top proxy layer {layer}", claim_status


def _robustness_status(dashboard_payload: Mapping[str, Any]) -> tuple[str, str]:
    robustness = _mapping(_mapping(dashboard_payload.get("dynamic_mechanism")).get("robustness"))
    layer_summary = _records(_mapping(robustness.get("subject_bootstrap")).get("layer_summary"))
    run_rows = _records(_mapping(robustness.get("run_sensitivity")).get("run_rows"))
    if layer_summary or run_rows:
        return f"{len(layer_summary)} layer bootstrap rows; {len(run_rows)} run-sensitivity rows", "proxy-supported"
    return "robustness artifacts missing", "blocked"


def _cv5_status(dashboard_payload: Mapping[str, Any]) -> tuple[str, str]:
    cv5 = _mapping(dashboard_payload.get("cv5_validation"))
    completed = int(cv5.get("completed_folds") or 0)
    total = int(cv5.get("total_folds") or 0)
    if cv5.get("held_out_validation_completed") is True and total and completed == total:
        return f"internal subject-disjoint CV5 complete ({completed}/{total} folds)", "implemented"
    if total:
        return f"internal subject-disjoint CV5 partial ({completed}/{total} folds)", "mixed"
    return "internal subject-disjoint CV5 not configured", "blocked"


def _archive_status(dashboard_payload: Mapping[str, Any]) -> tuple[str, str]:
    archive = _mapping(_mapping(_mapping(dashboard_payload.get("thesis_upgrade")).get("components")).get("reproducible_archive"))
    release_ready = archive.get("publication_release_ready") is True
    doi_ready = archive.get("publication_doi_ready") is True
    if release_ready and doi_ready:
        return "release URL and DOI verified", "implemented"
    if release_ready:
        return "GitHub release verified; Zenodo DOI missing", "blocked"
    return "release publication metadata not verified", "blocked"


def _motion_status(dashboard_payload: Mapping[str, Any]) -> tuple[str, str]:
    motion = _mapping(_mapping(_mapping(dashboard_payload.get("thesis_upgrade")).get("components")).get("motion_confound"))
    if motion.get("fmriprep_motion_control_ready") is True:
        return "strict motion proof complete", "implemented"
    return "FD/DVARS/censoring proof missing", "blocked"


def build_figure_payloads(repo_root: Path, dashboard_payload: Mapping[str, Any]) -> dict[str, Any]:
    strict_status, strict_claim = _strict_gate_status(dashboard_payload)
    dynamic_status, dynamic_claim = _dynamic_status(dashboard_payload)
    robustness_status, robustness_claim = _robustness_status(dashboard_payload)
    cv5_status, cv5_claim = _cv5_status(dashboard_payload)
    archive_status, archive_claim = _archive_status(dashboard_payload)
    motion_status, motion_claim = _motion_status(dashboard_payload)

    explainers: dict[str, FigureExplainer] = {}
    for explainer in [
        _explainer(
            repo_root,
            plot_id="strict_gate_chart",
            title="Strict thesis gates",
            subtitle="Production-readiness gate chart sourced from the thesis upgrade status artifact.",
            input_artifacts=[
                ("Thesis upgrade status", "results/thesis_upgrade/thesis_upgrade_status.json"),
                ("Reproducible archive manifest", "results/reproducible_archive/ARCHIVE_MANIFEST.json"),
                ("Motion proof preflight", "results/confound_controls/fmriprep_motion_proof_plan.json"),
            ],
            metric_definition="Each gate is binary: complete only when the tracked requirement reports complete=true.",
            aggregation_level="Repository-level release and thesis-readiness requirements.",
            calculation="complete_count / total_count, with every incomplete requirement shown as blocked rather than averaged away.",
            caveat="A green gate means the artifact contract is satisfied; it is not stronger biological or clinical evidence.",
            claim_status=strict_claim,
            export_target=("Thesis upgrade status", "results/thesis_upgrade/thesis_upgrade_status.json"),
            page_href="/",
        ),
        _explainer(
            repo_root,
            plot_id="overview_literature_chart",
            title="Literature alignment snapshot",
            subtitle="Directional benchmark rows from the dynamic-mechanism summary.",
            input_artifacts=[
                ("Dynamic mechanism summary", "results/dynamic_mechanism_ranking/summary.json"),
                ("Literature benchmark CSV", "results/dynamic_mechanism_ranking/exports/literature_benchmark.csv"),
            ],
            metric_definition="Observed signed proxy effect size for each measurable literature-style benchmark row.",
            aggregation_level="Benchmark row, not a paper-level replication claim.",
            calculation="Signed effect sizes are read directly from the benchmark export and colored by row-level alignment status.",
            caveat="This is literature-alignment bookkeeping over local proxy metrics; unavailable regions and mismatches remain visible.",
            claim_status="mixed",
            export_target=("Literature benchmark CSV", "results/dynamic_mechanism_ranking/exports/literature_benchmark.csv"),
            page_href="/",
        ),
        _explainer(
            repo_root,
            plot_id="ranking_chart",
            title="A-E mechanism ranking",
            subtitle="Current macro-dynamics proxy ranking across five mechanism layers.",
            input_artifacts=[
                ("Dynamic mechanism summary", "results/dynamic_mechanism_ranking/summary.json"),
                ("Mechanism ranking CSV", "results/dynamic_mechanism_ranking/exports/mechanism_ranking.csv"),
            ],
            metric_definition="Proxy support score combining current dynamic-mechanism rows under the configured ranking rule.",
            aggregation_level="Mechanism layer A-E across cached paired ds003059 records.",
            calculation="Rows are sorted by exported rank; bar length is the exported unitless support score.",
            caveat="Ranking supports mechanism prioritization only; it is not receptor-level, subjective, or clinical validation.",
            claim_status=dynamic_claim,
            export_target=("Mechanism ranking CSV", "results/dynamic_mechanism_ranking/exports/mechanism_ranking.csv"),
            page_href="/ranking",
        ),
        _explainer(
            repo_root,
            plot_id="ranking_distribution_chart",
            title="Mechanism score spread",
            subtitle="Same ranking scores shown by layer order to expose score separation.",
            input_artifacts=[
                ("Dynamic mechanism summary", "results/dynamic_mechanism_ranking/summary.json"),
                ("Mechanism ranking CSV", "results/dynamic_mechanism_ranking/exports/mechanism_ranking.csv"),
            ],
            metric_definition="Exported unitless support score for each mechanism layer.",
            aggregation_level="Mechanism layer A-E.",
            calculation="Layer labels are plotted against exported support scores, with rank labels placed on the marks.",
            caveat="Small score gaps should be interpreted with the robustness panels, not as decisive separation.",
            claim_status=dynamic_claim,
            export_target=("Mechanism ranking CSV", "results/dynamic_mechanism_ranking/exports/mechanism_ranking.csv"),
            page_href="/ranking",
        ),
        _explainer(
            repo_root,
            plot_id="benchmark_chart",
            title="Benchmark alignment",
            subtitle="Literature-style benchmark rows next to the mechanism ranking.",
            input_artifacts=[
                ("Literature benchmark CSV", "results/dynamic_mechanism_ranking/exports/literature_benchmark.csv"),
                ("Dynamic mechanism report", "docs/stage_reports/dynamic_mechanism_ranking.md"),
            ],
            metric_definition="Signed effect size and row-level alignment status for measurable benchmark rows.",
            aggregation_level="Benchmark row.",
            calculation="Bars show exported signed effect sizes; color encodes aligned, missing, or conflicting status.",
            caveat="Prior-art wrappers and benchmark labels are not treated as original local analyses.",
            claim_status="mixed",
            export_target=("Literature benchmark CSV", "results/dynamic_mechanism_ranking/exports/literature_benchmark.csv"),
            page_href="/ranking",
        ),
        _explainer(
            repo_root,
            plot_id="robustness_chart",
            title="Robustness spread",
            subtitle="Bootstrap uncertainty around mechanism support scores.",
            input_artifacts=[
                ("Robustness summary", "results/dynamic_mechanism_ranking/robustness/robustness_summary.json"),
                ("Robust bootstrap CSV", "results/dynamic_mechanism_ranking/exports/robust_bootstrap_summary.csv"),
            ],
            metric_definition="Bootstrap score mean with confidence interval for each mechanism layer.",
            aggregation_level="Layer summary over subject-level resamples.",
            calculation="Mean support score is drawn with exported lower and upper interval bounds.",
            caveat="Bootstrap stability is internal robustness evidence, not external validation.",
            claim_status=robustness_claim,
            export_target=("Robust bootstrap CSV", "results/dynamic_mechanism_ranking/exports/robust_bootstrap_summary.csv"),
            page_href="/robustness",
        ),
        _explainer(
            repo_root,
            plot_id="run_sensitivity_chart",
            title="Run sensitivity",
            subtitle="Mechanism scores compared across available paired runs.",
            input_artifacts=[
                ("Robustness summary", "results/dynamic_mechanism_ranking/robustness/robustness_summary.json"),
                ("Run sensitivity CSV", "results/dynamic_mechanism_ranking/exports/robust_run_sensitivity.csv"),
            ],
            metric_definition="Support score by mechanism layer and run label.",
            aggregation_level="Run-level sensitivity rows.",
            calculation="Grouped bars show exported support scores for each layer/run combination.",
            caveat="Run differences flag uncertainty; they do not complete the motion-confound proof.",
            claim_status=robustness_claim,
            export_target=("Run sensitivity CSV", "results/dynamic_mechanism_ranking/exports/robust_run_sensitivity.csv"),
            page_href="/robustness",
        ),
        _explainer(
            repo_root,
            plot_id="e_horizon_chart",
            title="E horizon sensitivity",
            subtitle="Network-control proxy sensitivity to the finite horizon setting.",
            input_artifacts=[
                ("Robustness summary", "results/dynamic_mechanism_ranking/robustness/robustness_summary.json"),
                ("E horizon CSV", "results/dynamic_mechanism_ranking/exports/robust_e_horizon.csv"),
            ],
            metric_definition="Support score and receptor-vs-random energy reduction percent by horizon.",
            aggregation_level="Horizon sensitivity row.",
            calculation="Two exported series share the x-axis; energy reduction uses the right axis.",
            caveat="The E layer remains a landscape/control proxy and cannot promote receptor-placement claims by itself.",
            claim_status="mixed",
            export_target=("E horizon CSV", "results/dynamic_mechanism_ranking/exports/robust_e_horizon.csv"),
            page_href="/robustness",
        ),
        _explainer(
            repo_root,
            plot_id="d_window_chart",
            title="D window sensitivity",
            subtitle="Dynamic-FC proxy sensitivity to window size.",
            input_artifacts=[
                ("Robustness summary", "results/dynamic_mechanism_ranking/robustness/robustness_summary.json"),
                ("D windows CSV", "results/dynamic_mechanism_ranking/exports/robust_d_windows.csv"),
            ],
            metric_definition="Support score by dynamic-FC window size.",
            aggregation_level="Window-size sensitivity row.",
            calculation="The line connects exported support scores across tested TR window sizes.",
            caveat="Window stability is internal sensitivity evidence; unresolved motion confounds remain separate.",
            claim_status=robustness_claim,
            export_target=("D windows CSV", "results/dynamic_mechanism_ranking/exports/robust_d_windows.csv"),
            page_href="/robustness",
        ),
        _explainer(
            repo_root,
            plot_id="empirical_delta_chart",
            title="Empirical delta summary",
            subtitle="Group-level LSD minus placebo macro-dynamic deltas.",
            input_artifacts=[
                ("Empirical viewer overview", "results/stage_2/empirical_viewer/group_overview.json"),
                ("Perturbation targets", "results/stage_2/empirical_perturbation_targets.yaml"),
            ],
            metric_definition="Group-level condition delta for each macro-dynamic summary metric.",
            aggregation_level="Cached paired ds003059 summary records.",
            calculation="Bars show LSD minus placebo deltas from the viewer overview or perturbation target artifact.",
            caveat="These are derived aggregate summaries; subject-level cache rows are not published through the static site.",
            claim_status="proxy-supported",
            export_target=("Empirical viewer overview", "results/stage_2/empirical_viewer/group_overview.json"),
            page_href="/empirical",
        ),
        _explainer(
            repo_root,
            plot_id="empirical_fc_heatmap",
            title="Subject-window FC delta matrix",
            subtitle="Local-only heatmap for an authorized cached subject/run/window record.",
            input_artifacts=[
                ("Empirical viewer overview", "results/stage_2/empirical_viewer/group_overview.json"),
                ("Subject-view cache path pattern", "results/stage_2/empirical_viewer/subject_views/{subject}_{run}.json"),
            ],
            metric_definition="Window-level functional-connectivity delta matrix for selected macro modules.",
            aggregation_level="One selected subject, run, and window in the local FastAPI dashboard.",
            calculation="The heatmap uses the selected cached matrix directly; no static Pages subject-level export is exposed.",
            caveat="The public static dashboard intentionally withholds subject-level cache files; use aggregate plots for public review.",
            claim_status="proxy-supported",
            page_href="/empirical",
        ),
        _explainer(
            repo_root,
            plot_id="thesis_mechanism_chart",
            title="Mechanism thesis summary",
            subtitle="Compact defense-view version of the mechanism ranking.",
            input_artifacts=[
                ("Dynamic mechanism summary", "results/dynamic_mechanism_ranking/summary.json"),
                ("Claim evidence matrix", "results/thesis_evidence_loop/claim_evidence_matrix.csv"),
            ],
            metric_definition="Exported mechanism support score by layer.",
            aggregation_level="Mechanism layer A-E.",
            calculation="The chart reuses the mechanism-ranking scores and preserves the same claim boundaries.",
            caveat="This summary is for review navigation; the ranking page and exports remain the inspectable source.",
            claim_status=dynamic_claim,
            export_target=("Claim evidence matrix", "results/thesis_evidence_loop/claim_evidence_matrix.csv"),
            page_href="/thesis",
        ),
        _explainer(
            repo_root,
            plot_id="cv5_validation_summary",
            title="CV5 validation summary",
            subtitle="Internal subject-disjoint held-out stress test status.",
            input_artifacts=[
                ("CV5 aggregate validation", "results/validation/cv5_subject_disjoint/cv5_aggregate_validation.json"),
                ("Approved CV5 manifest", "output/validation/cv5_subject_disjoint/approved/subject_split_cv5_manifest_approved.json"),
            ],
            metric_definition="Completed folds, subject-disjoint coverage, and aggregate held-out metrics.",
            aggregation_level="Internal five-fold subject-disjoint split.",
            calculation="The figure-deck card reports the aggregate validation status and fold count from the approved payload.",
            caveat="CV5 is internal validation; ds006072 remains a small-subject unchanged-scoring external stress test unless stronger evidence is added.",
            claim_status=cv5_claim,
            export_target=("CV5 aggregate validation", "results/validation/cv5_subject_disjoint/cv5_aggregate_validation.json"),
            page_href="/figures",
        ),
        _explainer(
            repo_root,
            plot_id="archive_readiness_summary",
            title="Archive readiness summary",
            subtitle="Release URL and DOI verification state for publication packaging.",
            input_artifacts=[
                ("Archive manifest", "results/reproducible_archive/ARCHIVE_MANIFEST.json"),
                ("Zenodo metadata", ".zenodo.json"),
            ],
            metric_definition="Publication-ready only when both release URL and DOI verify.",
            aggregation_level="Repository archive package.",
            calculation="The card reads archive_publication_ready plus release_url_verified and doi_verified from the manifest.",
            caveat="The archive gate stays blocked until a real Zenodo DOI is recorded and verified.",
            claim_status=archive_claim,
            export_target=("Archive manifest", "results/reproducible_archive/ARCHIVE_MANIFEST.json"),
            page_href="/figures",
        ),
        _explainer(
            repo_root,
            plot_id="motion_proof_summary",
            title="Motion proof summary",
            subtitle="Strict FD/DVARS/censoring gate for subject/run confounds.",
            input_artifacts=[
                ("Motion proof preflight", "results/confound_controls/fmriprep_motion_proof_plan.json"),
                ("Motion source availability", "results/confound_controls/ds003059_motion_source_availability.json"),
                ("Motion confound control", "results/confound_controls/motion_confound_control_status.json"),
            ],
            metric_definition="Strict readiness requires paired rows covering FD, DVARS, and censor/outlier families.",
            aggregation_level="Subject/session/run confound rows.",
            calculation="The status card reads fMRIPrep motion proof and downstream confound-control gates.",
            caveat="Image-level or proxy QC cannot close this gate; authorized confounds or raw preprocessing outputs are required.",
            claim_status=motion_claim,
            export_target=("Motion proof preflight", "results/confound_controls/fmriprep_motion_proof_plan.json"),
            page_href="/figures",
        ),
    ]:
        explainers[explainer["plot_id"]] = explainer

    flow_nodes = [
        {
            "id": "data",
            "label": "Data",
            "title": "Paired psychedelic/control fMRI summaries",
            "status": _text(
                _mapping(_mapping(dashboard_payload.get("empirical_viewer")).get("display_metadata")).get("status"),
                "cached paired summaries",
            ),
            "claim_status": "proxy-supported",
            "detail": "Aggregate ds003059-derived summaries anchor the dashboard; subject-level cache files remain local-only.",
            "artifacts": _artifacts(repo_root, [("Empirical viewer overview", "results/stage_2/empirical_viewer/group_overview.json")]),
        },
        {
            "id": "modules",
            "label": "8 modules",
            "title": "Transparent macro-scale modules",
            "status": "implemented",
            "claim_status": "implemented",
            "detail": "The graph config maps evidence into eight coarse proxy modules for readable mechanism comparisons.",
            "artifacts": _artifacts(repo_root, [("Macro module config", "configs/graphs/macro_modules.yaml")]),
        },
        {
            "id": "mechanisms",
            "label": "A-E mechanisms",
            "title": "Mechanism proxy ranking",
            "status": dynamic_status,
            "claim_status": dynamic_claim,
            "detail": "Five mathematical mechanism proxies are ranked from the current exported support scores.",
            "artifacts": _artifacts(repo_root, [("Mechanism ranking CSV", "results/dynamic_mechanism_ranking/exports/mechanism_ranking.csv")]),
        },
        {
            "id": "robustness",
            "label": "Robustness",
            "title": "Internal sensitivity checks",
            "status": robustness_status,
            "claim_status": robustness_claim,
            "detail": "Bootstrap, run, horizon, and window checks keep uncertainty visible.",
            "artifacts": _artifacts(repo_root, [("Robustness summary", "results/dynamic_mechanism_ranking/robustness/robustness_summary.json")]),
        },
        {
            "id": "claim_gates",
            "label": "Claim gates",
            "title": "Strict claim readiness",
            "status": strict_status,
            "claim_status": strict_claim,
            "detail": "Motion and archive gates remain blocked until their evidence contracts verify.",
            "artifacts": _artifacts(repo_root, [("Thesis upgrade status", "results/thesis_upgrade/thesis_upgrade_status.json")]),
        },
    ]

    deck_ids = [
        "strict_gate_chart",
        "ranking_chart",
        "robustness_chart",
        "overview_literature_chart",
        "empirical_delta_chart",
        "cv5_validation_summary",
        "archive_readiness_summary",
        "motion_proof_summary",
    ]
    figure_deck = {
        "title": "Publication Figure Deck",
        "subtitle": "Export-ready registry for the public evidence platform. Each card links back to source artifacts and caveats.",
        "status_cards": [
            {"label": "Motion proof", "value": motion_status, "claim_status": motion_claim},
            {"label": "Archive DOI", "value": archive_status, "claim_status": archive_claim},
            {"label": "CV5 validation", "value": cv5_status, "claim_status": cv5_claim},
        ],
        "figures": [
            {
                **explainers[plot_id],
                "source_paths": [item["path"] for item in explainers[plot_id]["input_artifacts"]],
            }
            for plot_id in deck_ids
        ],
    }

    return {
        "figure_explainers": explainers,
        "evidence_flow": {
            "title": "Data -> 8 modules -> A-E mechanisms -> robustness -> claim gates",
            "nodes": flow_nodes,
            "edges": [["data", "modules"], ["modules", "mechanisms"], ["mechanisms", "robustness"], ["robustness", "claim_gates"]],
            "guardrail": "Every node is an artifact-backed macro-dynamics proxy step; blocked gates stay blocked until verified artifacts change.",
        },
        "figure_deck": figure_deck,
    }
