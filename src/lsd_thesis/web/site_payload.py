from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

PRIMARY_CLAIM = (
    "This project tests whether LSD-like empirical macro-dynamics are better explained by altered "
    "transition/control dynamics than by generic noise, motion, or static connectivity changes."
)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _compact_text(value: Any, default: str = "not reported") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _status_from_component(component: dict[str, Any], default: str = "not available") -> str:
    strict = _as_dict(component.get("strict_requirement"))
    gate = _as_dict(component.get("gate"))
    for candidate in (
        strict.get("status"),
        gate.get("status"),
        component.get("analysis_status"),
        component.get("status"),
        component.get("claim_status"),
    ):
        if candidate:
            return str(candidate)
    return default


def _first_existing_link(links: list[dict[str, str]], keywords: tuple[str, ...]) -> dict[str, str] | None:
    normalized = tuple(keyword.lower() for keyword in keywords)
    for link in links:
        haystack = f"{link.get('label', '')} {link.get('href', '')}".lower()
        if all(keyword in haystack for keyword in normalized):
            return link
    return None


def _artifact_index(artifact_links: dict[str, Any]) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for bucket_name, bucket in artifact_links.items():
        if not isinstance(bucket, list):
            continue
        for item in bucket:
            if not isinstance(item, dict):
                continue
            href = item.get("href")
            if not href:
                continue
            artifacts.append(
                {
                    "kind": str(bucket_name),
                    "label": str(item.get("label") or href),
                    "href": str(href),
                }
            )
    return sorted(artifacts, key=lambda item: (item["kind"], item["label"].lower()))


def _requirement_cards(thesis_upgrade: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    requirements = _as_list_of_dicts(thesis_upgrade.get("strict_completion_requirements"))
    for requirement in requirements:
        is_complete = bool(requirement.get("complete"))
        cards.append(
            {
                "id": _compact_text(requirement.get("requirement_id"), "requirement"),
                "title": _compact_text(requirement.get("label"), "Requirement"),
                "tier": "implemented" if is_complete else "blocked",
                "status": "implemented" if is_complete else "blocked",
                "evidence": _compact_text(
                    requirement.get("claim_effect")
                    or requirement.get("evidence")
                    or requirement.get("status"),
                    "Evidence gate is incomplete.",
                ),
                "next_action": _compact_text(
                    requirement.get("missing") or requirement.get("next_action"),
                    "No next action recorded in the current status artifact.",
                ),
                "q_value": _compact_text(requirement.get("q") or requirement.get("q_value")),
                "fdr_pass": _compact_text(requirement.get("fdr_pass")),
                "ci": _compact_text(requirement.get("ci") or requirement.get("confidence_interval")),
                "ci_crosses_zero": _compact_text(requirement.get("ci_crosses_zero")),
            }
        )
    return cards


def _status_cards(dashboard_payload: dict[str, Any]) -> list[dict[str, str]]:
    thesis_upgrade = _as_dict(dashboard_payload.get("thesis_upgrade"))
    summary = _as_dict(thesis_upgrade.get("readiness_summary"))
    components = _as_dict(thesis_upgrade.get("components"))
    external_maps = _as_dict(dashboard_payload.get("external_cortical_maps"))
    dynamic = _as_dict(dashboard_payload.get("dynamic_mechanism"))
    cv5 = _as_dict(dashboard_payload.get("cv5_validation"))

    strict_total = summary.get("strict_total_gates")
    strict_complete = summary.get("strict_complete_gates")
    strict_label = (
        f"{strict_complete}/{strict_total} strict gates"
        if strict_complete is not None and strict_total is not None
        else _compact_text(summary.get("completion_status"), "strict gates not reported")
    )

    return [
        {
            "label": "Thesis gate",
            "value": strict_label,
            "detail": _compact_text(summary.get("thesis_status") or summary.get("completion_status")),
        },
        {
            "label": "Motion/confounds",
            "value": _status_from_component(_as_dict(components.get("motion_confound"))),
            "detail": "Explicitly gated because motion, music/run, preprocessing, signal-quality, and session-order risks can mimic dynamics.",
        },
        {
            "label": "Subject-disjoint ML",
            "value": _compact_text(cv5.get("analysis_status") or cv5.get("status")),
            "detail": "Window-random reporting is excluded; subject-level aggregation is the defensible ML layer.",
        },
        {
            "label": "Mechanism-proxy ranking",
            "value": _compact_text(dynamic.get("analysis_status") or dynamic.get("best_family") or dynamic.get("status")),
            "detail": "A-E proxy layers are ranked from cached macro-dynamic evidence; receptor/myelin/gradient layers remain priors unless gated.",
        },
        {
            "label": "Map priors",
            "value": _compact_text(external_maps.get("analysis_status") or external_maps.get("status")),
            "detail": "Receptor, myelin, and gradient maps are displayed as exploratory priors, not proof of mechanism.",
        },
    ]


def _prior_art_cards(repo_root: Path) -> list[dict[str, str]]:
    map_path = repo_root / "docs" / "research" / "ds003059_prior_art_to_thesis_map.md"
    artifact_path = map_path.relative_to(repo_root).as_posix()
    return [
        {
            "prior_art_family": "Music + K-means brain states",
            "maps_to_layers": "A, C, D",
            "status": "blocked",
            "safe_now": "Run-02 extraction inventory exists, but music-control evidence remains blocked_missing_motion_review.",
            "gated_future": "Music-qualified masks, technical-problem exclusions, motion/context checks, and explicit music-control approval.",
            "artifact_path": artifact_path,
            "limitation": "Music/run-02 is not primary evidence in the current ranking.",
        },
        {
            "prior_art_family": "Receptor-informed network control energy",
            "maps_to_layers": "E",
            "status": "mixed",
            "safe_now": "Use E as a split claim: lower transition-energy proxy versus unsupported receptor-specific placement.",
            "gated_future": "Claim promotion requires graph-rewire/spatial-null gates and receptor/PET priors beating null controls.",
            "artifact_path": artifact_path,
            "limitation": "Current E is macro-module proxy evidence, not receptor-level network control theory.",
        },
        {
            "prior_art_family": "Ising/LZW entropy-complexity",
            "maps_to_layers": "A, D",
            "status": "future",
            "safe_now": "Plan a cached-only transparent LZW-style benchmark if module time series are present.",
            "gated_future": "Ising-temperature claims require independent implementation, tests, metric cards, and no external code copying.",
            "artifact_path": artifact_path,
            "limitation": "Entropy and complexity outputs remain proxy metrics, not thermodynamic truth claims.",
        },
        {
            "prior_art_family": "Entropy/toolbox reproducibility demos",
            "maps_to_layers": "A, D, project-wide",
            "status": "future",
            "safe_now": "Use as documentation and demo ergonomics inspiration.",
            "gated_future": "License review before any code reuse; prefer independent methods-level implementation.",
            "artifact_path": artifact_path,
            "limitation": "Toolbox-style demos are not validated local results unless implemented and tested here.",
        },
        {
            "prior_art_family": "Cross-state altered-consciousness comparisons",
            "maps_to_layers": "project-wide, C, D, E",
            "status": "blocked",
            "safe_now": "Keep as literature context while existing ds006072/HCP/PET/Schaefer artifacts remain stress-test or sensitivity evidence.",
            "gated_future": "Comparable external datasets, unchanged scoring, and explicit claim-status labels.",
            "artifact_path": artifact_path,
            "limitation": "This repo does not prove or settle consciousness-theory claims.",
        },
        {
            "prior_art_family": "Standardized derivative/evidence package",
            "maps_to_layers": "project-wide",
            "status": "implemented",
            "safe_now": "Use the claim-gated derivative package as the thesis contribution spine.",
            "gated_future": "Keep provenance, public/private artifact boundaries, and generated-output status current.",
            "artifact_path": artifact_path,
            "limitation": "Derived artifacts are reproducibility evidence, not biological ground truth.",
        },
    ]


def _claim_tiers(requirement_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    supported = [card for card in requirement_cards if card["tier"] == "supported_now"]
    blocked = [card for card in requirement_cards if card["tier"] == "blocked_future"]
    return [
        {
            "tier": "supported_now",
            "title": "Supported now",
            "claim": "The repo can defend a macro-dynamics surrogate, an empirical LSD anchor, uncertainty gates, and subject-disjoint benchmark framing.",
            "items": [card["title"] for card in supported[:4]]
            or ["Empirical anchor, evidence matrix, and static public dashboard are implemented."],
        },
        {
            "tier": "proxy_supported",
            "title": "Proxy-supported",
            "claim": (
                "Transition, control, metastability, and structural-connectome language is model-level "
                "and engineering-inspired unless external biological data closes the gate."
            ),
            "items": [
                "Control/energy language is an explanatory prior.",
                "DTI/SC layers are anatomical coupling priors, not raw scan viewers.",
                "8-module summaries are communication layers, not final anatomical inference.",
            ],
        },
        {
            "tier": "exploratory",
            "title": "Exploratory",
            "claim": "Receptor, myelin, functional-gradient, and gene-expression overlays are useful hypothesis generators only.",
            "items": [
                "Module-level map alignment is shown with uncertainty caveats.",
                "Spatial-null neuromaps upgrades remain the stricter inference target.",
                "Negative alignment results are preserved instead of hidden.",
            ],
        },
        {
            "tier": "blocked_future",
            "title": "Blocked / future work",
            "claim": (
                "A strong mechanism claim is downgraded if motion controls, Schaefer/Yeo spatial nulls, "
                "unchanged-scoring psilocybin stress tests, or subject-disjoint ML fail."
            ),
            "items": [card["title"] for card in blocked[:5]]
            or ["PET receptor priors, HCP structural priors, and full external validation still require authorized comparable data."],
        },
    ]


def build_route_links(*, static: bool, depth: int = 0) -> dict[str, str]:
    if not static:
        return {
            "home": "/",
            "submission": "/submission",
            "thesis": "/thesis",
            "dashboard": "/dashboard",
            "local_dashboard": "/local-dashboard",
            "methods": "/methods",
            "appendix": "/appendix",
        }
    prefix = "../" * max(depth, 0)
    return {
        "home": f"{prefix}index.html",
        "submission": f"{prefix}submission.html",
        "thesis": f"{prefix}thesis.html",
        "dashboard": f"{prefix}dashboard/",
        "local_dashboard": f"{prefix}methods.html#local-dashboard",
        "methods": f"{prefix}methods.html",
        "appendix": f"{prefix}appendix.html",
    }


def build_public_site_payload(
    repo_root: Path = REPO_ROOT,
    dashboard_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if dashboard_payload is None:
        from lsd_thesis.web.app import build_dashboard_payload

        dashboard_payload = build_dashboard_payload(repo_root)

    thesis_upgrade = _as_dict(dashboard_payload.get("thesis_upgrade"))
    artifact_links = _as_dict(dashboard_payload.get("artifact_links"))
    artifacts = _artifact_index(artifact_links)
    requirement_cards = _requirement_cards(thesis_upgrade)
    reports = [item for item in artifacts if item["kind"] == "reports"]

    return {
        "schema_version": "public_site.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "project": {
            "title": "LSD Thesis Macro-Dynamics Pitch",
            "subtitle": "A data-science and engineering proposal for psychedelic-inspired brain dynamics.",
            "one_sentence_claim": PRIMARY_CLAIM,
            "audience": "PI pitch, master thesis proposal, and reproducible data-science dashboard.",
            "guardrail": (
                "This is a conservative surrogate-analysis site. It does not claim subjective experience, "
                "receptor-level realism, or completed external validation."
            ),
        },
        "pitch": {
            "meeting_script": [
                "Start with the one-sentence claim: altered transition/control dynamics versus generic noise, motion, or static connectivity.",
                "Show the claim ladder so the PI sees what is supported now versus proxy, exploratory, or blocked.",
                "Open the evidence dashboard and point to q-value, FDR, CI, and claim-status fields before interpreting any mechanism.",
                (
                    "End with falsification: motion controls, Schaefer/Yeo spatial nulls, subject-disjoint CV, "
                    "or unchanged-scoring psilocybin stress tests can downgrade the claim."
                ),
            ],
            "what_to_open": [
                {"label": "Pitch homepage", "why": "sets the project frame and audience"},
                {"label": "Thesis story", "why": "separates strong claims from exploratory priors"},
                {"label": "Evidence dashboard", "why": "shows claim gates and searchable artifacts"},
                {"label": "Methods", "why": "shows confounds, parcellation limits, and local-only features"},
                {"label": "Appendix", "why": "keeps reproducible derived artifacts one click away"},
            ],
            "why_now": [
                "The project connects AI time-series benchmarking, control theory, perception, and psychedelic neuroscience in one inspectable pipeline.",
                "The defendable unit is macro-dynamics: transitions, coupling, stability, uncertainty gates, and falsification tests.",
                "The public site is a static derived snapshot, so it can be shared without raw private datasets or a live backend.",
            ],
            "pi_fit": [
                "Engineering angle: graph-modulated dynamics, control priors, subject-disjoint validation, and falsifiable model comparisons.",
                "AI/data-science angle: leak-proof benchmarks, ROCKET/MiniRocket-style baselines, uncertainty tables, and dashboard-first communication.",
                "Neuroscience humility: receptor, myelin, gradient, and SC layers are exploratory priors until stricter nulls and external data pass.",
            ],
        },
        "claim_ladder": {
            "primary_claim": PRIMARY_CLAIM,
            "tiers": _claim_tiers(requirement_cards),
            "requirements": requirement_cards,
        },
        "dashboard": {
            "status_cards": _status_cards(dashboard_payload),
            "prior_art_cards": _prior_art_cards(repo_root),
            "viewer_modes": [
                {
                    "title": "Public/static dashboard",
                    "route": "/dashboard/",
                    "works": "Claim status, q/FDR/CI fields, methods links, and derived artifact search.",
                    "does_not_work": "Live simulation, subject-level fMRI preview calls, and local artifact mutation.",
                },
                {
                    "title": "Local clean dashboard",
                    "route": "/dashboard",
                    "works": "The same clean dashboard, backed by local FastAPI JSON.",
                    "does_not_work": "Public sharing unless the server is running on your machine.",
                },
                {
                    "title": "Local full dashboard",
                    "route": "/local-dashboard",
                    "works": "Simulation controls, empirical subject/run explorer, full Plotly diagnostics, and guarded local artifact serving.",
                    "does_not_work": "GitHub Pages hosting, because it requires the FastAPI backend.",
                },
            ],
            "primary_panels": [
                {
                    "title": "What the project tests",
                    "body": PRIMARY_CLAIM,
                },
                {
                    "title": "What would weaken the claim",
                    "body": (
                        "The mechanism claim is downgraded if effects vanish under subject-disjoint CV, "
                        "motion controls, Schaefer/Yeo spatial nulls, or comparable psilocybin stress tests."
                    ),
                },
                {
                    "title": "What is intentionally not claimed",
                    "body": (
                        "The dashboard does not claim raw DTI viewing, receptor causality, subjective-state simulation, "
                        "or completed cross-drug validation."
                    ),
                },
            ],
            "source_dashboard_key_count": len(dashboard_payload),
        },
        "methods": {
            "local_runtime": {
                "title": "Local full dashboard",
                "route": "/local-dashboard",
                "command": "uv run python scripts/run_dashboard.py",
                "static_boundary": (
                    "GitHub Pages is static: it can show the pitch, claim gates, and derived artifacts, "
                    "but it cannot run simulations or subject-level API calls."
                ),
                "local_boundary": (
                    "The local FastAPI dashboard can call /api/dashboard-data, /api/simulate, "
                    "and /api/empirical-view, so backend-only simulation and empirical viewer features live there."
                ),
                "features": [
                    "Interactive perturbation simulation controls",
                    "Subject/run empirical viewer calls",
                    "Plotly-heavy model and fMRI diagnostic panels",
                    "Local artifact serving through the guarded /artifacts route",
                ],
            },
            "pipeline_steps": [
                "Raw/derived fMRI inputs and provenance manifests",
                "Preprocessing/cache and quality-control gates",
                "Module/parcellation summaries",
                "Dynamic features and mechanism-ranking candidates",
                "Subject-disjoint ML benchmarks and null controls",
                "Uncertainty gates: CI, p, q, FDR status, and claim tier",
                "Static dashboard snapshot plus artifact appendix",
            ],
            "limitations": [
                "Motion/confound handling remains a central vulnerability and is displayed as an explicit gate.",
                "The 8-module layer is for explanation; Schaefer/Yeo or other high-resolution parcellations are the next inference layer.",
                "ds003059 LSD is the current empirical anchor; ds006072 psilocybin status is readiness/provenance unless comparable extraction is completed.",
                "Receptor, structural-connectome, myelin, and gradient layers are priors/status layers unless fully integrated with spatial-null testing.",
                "Negative and not-supported-yet results are part of the pitch because they prevent overclaiming.",
            ],
            "controls": [
                "Placebo comparison",
                "Random labels and random priors",
                "Degree/control priors",
                "Motion/confound controls",
                "Subject-disjoint CV and subject-level aggregation",
                "Future neuromaps surface-level spatial autocorrelation nulls",
            ],
        },
        "appendix": {
            "artifact_links": artifact_links,
            "all_artifacts": artifacts,
            "priority_reports": [
                link
                for link in (
                    _first_existing_link(reports, ("claim", "matrix")),
                    _first_existing_link(reports, ("claim", "ladder")),
                    _first_existing_link(reports, ("rocket",)),
                    _first_existing_link(reports, ("motion", "confound")),
                    _first_existing_link(reports, ("neuromaps",)),
                )
                if link is not None
            ],
        },
        "artifact_links": artifact_links,
        "empirical_viewer": dashboard_payload.get("empirical_viewer", {}),
        "source_dashboard": dashboard_payload,
    }
