from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, cast

import numpy as np
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from lsd_thesis.data.targets import load_perturbation_target_set, load_sober_target_set
from lsd_thesis.external_source_plan import external_source_plan_rows
from lsd_thesis.graph import load_graph_config
from lsd_thesis.simulator import load_regime_config
from lsd_thesis.web import artifacts as web_artifacts
from lsd_thesis.web import empirical_viewer, status_payload
from lsd_thesis.web.simulation_payload import (
    SimulationRequest,
    build_simulation_payload,
    graph_payload,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = Jinja2Templates(directory=str(REPO_ROOT / "src" / "lsd_thesis" / "templates"))
_plotly_js_cache: str | None = None

_augment_empirical_viewer_with_run02 = empirical_viewer.augment_empirical_viewer_with_run02
_empirical_selector_is_invalid = empirical_viewer.empirical_selector_is_invalid
_load_dashboard_empirical_detail = empirical_viewer.load_dashboard_empirical_detail
load_empirical_viewer_detail = empirical_viewer.load_empirical_viewer_detail
load_empirical_viewer_overview = empirical_viewer.load_empirical_viewer_overview


def _load_set_setting_seed_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    payload_path = repo_root / "results" / "setting_seed" / "dashboard" / "dashboard_payload.json"
    if not payload_path.exists():
        return {
            "status": "missing",
            "source_path": str(payload_path.relative_to(repo_root)),
            "claim_guardrail": "Set, setting, and seed panels are unavailable until PASS 2A artifacts are built.",
        }
    payload = cast(dict[str, Any], json.loads(payload_path.read_text(encoding="utf-8")))
    payload.setdefault(
        "claim_guardrail",
        "Exploratory macro-dynamics proxy summaries, not subjective-experience simulation or biological proof.",
    )
    payload["source_path"] = str(payload_path.relative_to(repo_root))
    return payload


def _load_dynamic_mechanism_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    payload_path = repo_root / "results" / "dynamic_mechanism_ranking" / "summary.json"
    if not payload_path.exists():
        return {
            "analysis_status": "missing",
            "source_path": payload_path.relative_to(repo_root).as_posix(),
            "claim_guardrail": "A+B+C+D+E dynamic mechanism ranking artifacts have not been generated yet.",
        }
    payload = cast(dict[str, Any], json.loads(payload_path.read_text(encoding="utf-8")))
    payload.setdefault(
        "claim_guardrail",
        "First-pass AI/ML surrogate results only; not receptor-level, clinical, external-validity, or subjective-experience evidence.",
    )
    payload["source_path"] = payload_path.relative_to(repo_root).as_posix()
    return payload


def _load_thesis_loop_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    payload_path = repo_root / "results" / "thesis_evidence_loop" / "thesis_evidence_loop_status.json"
    if not payload_path.exists():
        return {
            "analysis_status": "missing",
            "source_path": payload_path.relative_to(repo_root).as_posix(),
            "status_rows": [],
            "claim_guardrail": "Run scripts/run_thesis_evidence_loop.py to populate the full evidence-loop status matrix.",
        }
    payload = cast(dict[str, Any], json.loads(payload_path.read_text(encoding="utf-8")))
    payload["source_path"] = payload_path.relative_to(repo_root).as_posix()
    return payload


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_structural_dti_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    status_path = repo_root / "results" / "structural_connectome" / "structural_connectome_status.json"
    matrix_path = repo_root / "results" / "structural_connectome" / "hcp_macro_modules.csv"
    fallback_matrix_path = repo_root / "data" / "hcp_structural_connectome" / "macro_modules.csv"
    if not matrix_path.exists() and fallback_matrix_path.exists():
        matrix_path = fallback_matrix_path
    status = cast(dict[str, Any], json.loads(status_path.read_text(encoding="utf-8"))) if status_path.exists() else {}
    rows = _read_csv_rows(matrix_path)
    modules = [str(row.get("module", "")).strip() for row in rows if str(row.get("module", "")).strip()]
    if not rows or not modules:
        return {
            "analysis_status": status.get("analysis_status", "missing_structural_connectome_matrix"),
            "source_path": status_path.relative_to(repo_root).as_posix() if status_path.exists() else None,
            "matrix_path": matrix_path.relative_to(repo_root).as_posix(),
            "modules": [],
            "matrix": [],
            "edges": [],
            "nodes": [],
            "claim_guardrail": (
                "A DTI/tractography dynamics panel requires a macro-module structural-connectome matrix. "
                "It should be interpreted as anatomical coupling context, not drug-effect proof."
            ),
        }

    matrix = []
    for row in rows:
        matrix_row = []
        for module in modules:
            try:
                value = float(row.get(module, 0.0))
            except (TypeError, ValueError):
                value = 0.0
            matrix_row.append(value if math.isfinite(value) else 0.0)
        matrix.append(matrix_row)

    matrix_array = np.asarray(matrix, dtype=float)
    matrix_array = (matrix_array + matrix_array.T) / 2.0
    np.fill_diagonal(matrix_array, 0.0)
    max_weight = float(np.max(matrix_array)) if matrix_array.size else 0.0
    node_strengths = matrix_array.sum(axis=1) if matrix_array.size else np.zeros(len(modules))
    max_strength = float(np.max(node_strengths)) if node_strengths.size else 0.0
    edge_rows: list[dict[str, Any]] = []
    for source_index, source in enumerate(modules):
        for target_index, target in enumerate(modules):
            if source_index >= target_index:
                continue
            weight = float(matrix_array[source_index, target_index])
            if weight <= 0.0:
                continue
            edge_rows.append(
                {
                    "source": source,
                    "target": target,
                    "weight": weight,
                    "normalized_weight": weight / max_weight if max_weight > 0 else 0.0,
                }
            )
    edge_rows = sorted(edge_rows, key=lambda row: float(row["weight"]), reverse=True)
    nodes = []
    for index, module in enumerate(modules):
        angle = 2.0 * math.pi * index / max(len(modules), 1)
        strength = float(node_strengths[index])
        nodes.append(
            {
                "name": module,
                "x": math.cos(angle),
                "y": math.sin(angle),
                "strength": strength,
                "normalized_strength": strength / max_strength if max_strength > 0 else 0.0,
            }
        )
    return {
        "analysis_status": status.get("analysis_status", "structural_matrix_loaded"),
        "source_path": status_path.relative_to(repo_root).as_posix() if status_path.exists() else None,
        "matrix_path": matrix_path.relative_to(repo_root).as_posix(),
        "modules": modules,
        "matrix": matrix_array.tolist(),
        "nodes": nodes,
        "edges": edge_rows,
        "top_edges": edge_rows[:10],
        "module_count": len(modules),
        "edge_count": len(edge_rows),
        "density": len(edge_rows) / max((len(modules) * (len(modules) - 1)) / 2.0, 1.0),
        "strongest_edge": edge_rows[0] if edge_rows else None,
        "claim_guardrail": (
            "DTI/tractography-derived structural connectivity is used here as a dynamics prior: it constrains "
            "which macro-module transitions are anatomically plausible. It is not a raw DTI scan, not a receptor "
            "model, and not evidence by itself that LSD or psilocybin caused the observed dynamics."
        ),
        "dynamic_interpretation": (
            "Read this panel as the structural substrate for network-control and transition-energy questions. "
            "Strong edges are candidate low-cost anatomical routes; weak edges are candidate high-cost routes."
        ),
    }


def _load_external_cortical_maps_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    status_path = repo_root / "results" / "cortical_maps" / "cortical_map_alignment_status.json"
    markdown_path = repo_root / "results" / "cortical_maps" / "cortical_map_alignment.md"
    if not status_path.exists():
        return {
            "analysis_status": "missing_external_cortical_map_alignment",
            "source_path": status_path.relative_to(repo_root).as_posix(),
            "markdown_path": markdown_path.relative_to(repo_root).as_posix(),
            "maps": [],
            "dynamic_targets": [],
            "alignment_rows": [],
            "claim_guardrail": (
                "External receptor, myelin, functional-gradient, and transcriptomic map alignment has not been generated yet. "
                "Run scripts/build_external_cortical_maps.py after dynamic-mechanism outputs exist."
            ),
        }
    payload = cast(dict[str, Any], json.loads(status_path.read_text(encoding="utf-8")))
    payload.setdefault("source_path", status_path.relative_to(repo_root).as_posix())
    if markdown_path.exists():
        payload.setdefault("markdown_path", markdown_path.relative_to(repo_root).as_posix())
    return payload


def _load_claim_status_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    claim_ladder_path = repo_root / "CLAIM_LADDER.md"
    pi_pitch_path = repo_root / "PI_PITCH.md"
    return {
        "analysis_status": "pi_pitch_claim_ladder_ready" if claim_ladder_path.exists() and pi_pitch_path.exists() else "missing_pitch_or_claim_ladder",
        "source_path": claim_ladder_path.relative_to(repo_root).as_posix(),
        "pi_pitch_path": pi_pitch_path.relative_to(repo_root).as_posix(),
        "audience": "prospective Master's PI",
        "one_sentence_pitch": (
            "This project uses AI, control theory, and interactive visualization to study how psychedelic-state datasets can be "
            "turned into testable macro-dynamic models of perception, while keeping biological claims conservative and falsifiable."
        ),
        "falsifiable_thesis_claim": (
            "This project tests whether empirical LSD-placebo macro-dynamics are better explained by altered transition/control "
            "dynamics than by generic noise, motion, run effects, or static connectivity changes."
        ),
        "fit_statement": (
            "The thesis value is not prior neuroscience specialization; it is engineering rigor applied to perception, AI, and "
            "psychedelic neuroimaging as a high-signal perturbation domain."
        ),
        "methods_pipeline": [
            "raw fMRI / empirical cache",
            "preprocessing and quality metadata",
            "8-module summary plus Schaefer/Yeo parcel layers",
            "dynamic features and DMDC/control metrics",
            "AI/ML benchmarks with subject-disjoint validation",
            "uncertainty gates: CI, p, q, FDR, nulls",
            "public dashboard and PI pitch artifacts",
        ],
        "external_validation_status": [
            {
                "source": "ds003059 LSD-placebo",
                "role": "current empirical anchor",
                "status": "implemented",
                "claim_boundary": "Supports macro-dynamic proxy claims only; not subjective or receptor-level validation.",
            },
            {
                "source": "ds006072 psilocybin",
                "role": "external stress-test dataset",
                "status": "scored_when_comparable_viewer_present",
                "claim_boundary": (
                    "Schaefer100/Yeo7 unchanged scoring is an external stress test; "
                    "a top-layer mismatch is negative/partial evidence, not LSD replication."
                ),
            },
            {
                "source": "Lyons et al. 2026 Nature Communications",
                "role": "recent human psilocybin context",
                "status": "external_plausibility_anchor",
                "claim_boundary": "Not LSD replication and not direct model validation.",
            },
            {
                "source": "PsiConnect 2026 Scientific Data",
                "role": "future multimodal dataset context",
                "status": "candidate_future_dataset",
                "claim_boundary": "Not evidence until authorized access and unchanged scoring exist.",
            },
        ],
        "null_controls": [
            {
                "control": "placebo baseline",
                "purpose": "separate condition effect from generic dynamics",
                "status": "implemented_empirical_anchor",
            },
            {
                "control": "subject-disjoint CV",
                "purpose": "prevent window-level leakage in AI benchmarks",
                "status": "required_reporting_standard",
            },
            {
                "control": "random receptor priors",
                "purpose": "test whether receptor-prior control beats random receptor assignments",
                "status": "implemented_proxy_control",
            },
            {
                "control": "degree/control priors",
                "purpose": "separate receptor claims from graph topology or generic controllability",
                "status": "implemented_proxy_control",
            },
            {
                "control": "motion, run/music, preprocessing, and signal-quality gates",
                "purpose": "block confounded empirical claims",
                "status": "must_remain_first_class_limitation",
            },
            {
                "control": "future Schaefer/Yeo spatial nulls",
                "purpose": "replace weak 8-label permutation with spatial-autocorrelation-aware inference",
                "status": "next_required_upgrade",
            },
        ],
        "uncertainty_gate_rows": [
            {
                "effect": "PET 5-HT2A prior vs DMDC condition input",
                "ci": "overlaps zero",
                "p": "0.0719",
                "q": "0.8628",
                "fdr_pass": "no",
                "ci_crosses_zero": "yes",
                "claim_status": "exploratory_not_supported_yet",
            },
            {
                "effect": "Receptor/myelin/gradient family claim",
                "ci": "not consistently away from zero",
                "p": "mixed",
                "q": "not significant",
                "fdr_pass": "no",
                "ci_crosses_zero": "yes",
                "claim_status": "do_not_strengthen_mechanism_claim",
            },
            {
                "effect": "High-resolution spatial-map claim",
                "ci": "not run",
                "p": "not run",
                "q": "not run",
                "fdr_pass": "no",
                "ci_crosses_zero": "unknown",
                "claim_status": "blocked_until_schaefer_yeo_neuromaps",
            },
        ],
        "claim_tiers": [
            {
                "tier": "A",
                "claim": "Reproducible empirical LSD-placebo macro-dynamics dashboard",
                "status": "supported",
                "evidence": "Implemented code, generated artifacts, provenance, and static dashboard snapshot.",
                "pi_framing": "Shows research-engineering maturity and reproducibility.",
            },
            {
                "tier": "B",
                "claim": "Macro-dynamic transition, integration, and control-like effects are measurable",
                "status": "supported_proxy",
                "evidence": "Empirical dynamic summaries and mechanism-ranking outputs.",
                "pi_framing": "A defensible computational-perception question, not a subjective-experience claim.",
            },
            {
                "tier": "C",
                "claim": "AI/ML benchmarks can test condition information without leakage",
                "status": "internal_validation",
                "evidence": "Subject-disjoint CV and no window-random reporting are the required standard.",
                "pi_framing": "Connects AI methodology with human neuroimaging rigor.",
            },
            {
                "tier": "D",
                "claim": "Receptor, DTI, myelin, gradient, and AHBA maps are useful priors",
                "status": "exploratory",
                "evidence": "Module-level p/q/CI-gated alignments are displayed, but not significant enough for strong mechanism claims.",
                "pi_framing": "Shows honesty: the system reports weak evidence instead of hiding it.",
            },
            {
                "tier": "E",
                "claim": "Strong receptor/myelin/gradient mechanism",
                "status": "not_supported_yet",
                "evidence": "Needs Schaefer/Yeo or Glasser parcel-level inference plus spatial nulls.",
                "pi_framing": "Clear Master's work package rather than overclaiming.",
            },
            {
                "tier": "F",
                "claim": "External psilocybin validation",
                "status": "blocked_future_work",
                "evidence": (
                    "Lyons 2026 and PsiConnect 2026 are context/planning anchors until "
                    "comparable data are ingested and scored unchanged."
                ),
                "pi_framing": "A concrete future collaboration/data-access target.",
            },
        ],
        "methods_limitations": [
            {
                "topic": "Motion and run/music confounds",
                "message": (
                    "Must be shown as a first-class limitation and control target before "
                    "strengthening empirical claims; include preprocessing, signal quality, "
                    "and fixed-order/session risks."
                ),
                "slide_takeaway": "The project treats confounds as engineering tests, not footnotes.",
            },
            {
                "topic": "Parcellation",
                "message": "The 8-module layer is an interpretable public summary, not a canonical network definition.",
                "slide_takeaway": "Next inference layer should be Schaefer-100/200 with Yeo labels and optional Glasser sensitivity.",
            },
            {
                "topic": "External validation",
                "message": "Current psilocybin papers are external context, not validation of this score until data are ingested and scored unchanged.",
                "slide_takeaway": "The dashboard separates plausibility anchors from replication.",
            },
            {
                "topic": "Negative results",
                "message": "Weak receptor/myelin/gradient alignment is a useful result because it blocks overclaiming.",
                "slide_takeaway": "A PI should see this as scientific maturity, not failure.",
            },
        ],
        "next_90_days": [
            "Freeze the 8-module layer as an interpretable macro-summary.",
            "Add Schaefer-100/200 plus Yeo-7/Yeo-17 as the primary inference layer.",
            "Project receptor, DTI/SC, myelin, gradient, and AHBA maps into the same parcel contract.",
            "Run neuromaps-style spatial nulls and report q-values plus CI-zero gates.",
            "Turn leak-proof ML benchmarks into a compact AI contribution slide.",
            "Prepare authorized psilocybin external-scoring contracts without claiming validation early.",
        ],
        "falsification_checks": [
            "Downgrade the mechanism claim if subject-disjoint CV collapses.",
            "Downgrade the mechanism claim if motion, run/music, preprocessing, or signal-quality controls remove the effect.",
            "Downgrade receptor/myelin/gradient claims if Schaefer/Yeo spatial nulls fail.",
            "Downgrade external-validity claims if psilocybin data fail under unchanged scoring.",
            "Downgrade map-prior claims if random, degree, or uniform controls explain the result as well.",
        ],
        "claim_guardrail": (
            "This is a PI pitch for an AI/engineering Master's project in perception and "
            "psychedelic-state dynamics. It should sell research potential, reproducibility, "
            "and rigorous uncertainty gates without pretending to be a completed neuroscience "
            "mechanism thesis."
        ),
    }


def _build_thesis_expansion_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    loop_status = _load_thesis_loop_status(repo_root)
    loop_status_by_label = {
        str(row.get("label")): row
        for row in loop_status.get("status_rows", [])
        if isinstance(row, dict)
    }
    raw_source_plan = loop_status.get("external_source_plan")
    source_plan: list[dict[str, Any]] = (
        [row for row in raw_source_plan if isinstance(row, dict)]
        if isinstance(raw_source_plan, list)
        else external_source_plan_rows()
    )
    scholarly_anchors = [
        {
            "source": row.get("source"),
            "claim": row.get("key_evidence"),
            "use_in_project": row.get("use_in_project"),
            "status": row.get("status"),
            "url": row.get("url"),
            "current_component_status": row.get("current_component_status"),
        }
        for row in source_plan
        if isinstance(row, dict)
    ]
    payload: dict[str, Any] = {
        "thesis_goal": (
            "Build a reproducible explainable AI framework that ranks transparent "
            "control-theoretic and graph-dynamic surrogate mechanisms across LSD and "
            "psilocybin fMRI, then tests whether the strongest claims survive "
            "structural-connectome, receptor-map, atlas, and literature-benchmark checks."
        ),
        "research_question": (
            "Which interpretable macro-dynamic mechanisms best explain psychedelic "
            "drug-vs-control fMRI changes, and which claims fail under robustness, "
            "cross-dataset, and biological-prior tests?"
        ),
        "status_summary": (
            "The LSD A+B+C+D+E ranking is implemented. The next loop upgrades the "
            "evidence base with robustness, a ds006072 psilocybin cross-drug stress test, HCP "
            "structural connectivity, neuromaps/FS5ht receptor priors, Schaefer/Yeo "
            "sensitivity, and comparison to the 2026 Nature Medicine mega-analysis."
        ),
        "claim_guardrail": (
            "Dashboard status labels separate implemented evidence from planned tests. "
            "Implemented cross-dataset stress tests are not shown as replication or population validation."
        ),
        "loop_steps": [
            {
                "step": "1",
                "label": "LSD robustness",
                "status": "next",
                "artifact_target": "results/dynamic_mechanism_ranking/robustness/",
                "scientific_question": "Do C and E survive subject/bootstrap, run, horizon, state-label, and window-size sensitivity?",
                "dashboard_output": "Robustness bands, pass/fail badges, and failure-case slices.",
            },
            {
                "step": "2",
                "label": "Psilocybin ds006072",
                "status": "planned",
                "artifact_target": "results/psilocybin_ds006072/",
                "scientific_question": "Does the LSD ranking generalize to psilocybin precision functional mapping data, or fail under unchanged scoring?",
                "dashboard_output": "LSD-vs-psilocybin mechanism ranking comparison with negative/partial outcomes retained.",
            },
            {
                "step": "3",
                "label": "HCP structural graph",
                "status": "planned",
                "artifact_target": "results/structural_connectome/",
                "scientific_question": "Does E remain plausible when the macro proxy graph is replaced by a normative structural connectome?",
                "dashboard_output": "Control-energy comparison across proxy, structural, uniform, degree, and graph-rewire controls.",
            },
            {
                "step": "4",
                "label": "PET receptor priors",
                "status": "planned",
                "artifact_target": "results/receptor_priors/",
                "scientific_question": "Do neuromaps/FS5ht 5-HT2A priors outperform uniform, random, degree, and spatial nulls?",
                "dashboard_output": "Receptor-prior null board and claim-status split for E.",
            },
            {
                "step": "5",
                "label": "Schaefer/Yeo sensitivity",
                "status": "planned",
                "artifact_target": "results/parcellation_sensitivity/",
                "scientific_question": "Are C/D/E findings stable beyond the current 8-module proxy representation?",
                "dashboard_output": "Schaefer 100/200 and Yeo 7/17 result matrix.",
            },
            {
                "step": "6",
                "label": "Mega-analysis comparison",
                "status": "planned",
                "artifact_target": "results/literature_benchmark/",
                "scientific_question": "Do final patterns align with transmodal-unimodal and striatal-unimodal effects reported in the 2026 mega-analysis?",
                "dashboard_output": "Scholarly benchmark agreement table with explicit mismatches.",
            },
        ],
        "scholarly_anchors": scholarly_anchors
        + [
            {
                "source": "Singleton et al., Nature Communications 2022",
                "claim": "Receptor-informed network control links LSD and psilocybin to lower control-energy landscape estimates.",
                "use_in_project": "Primary mathematical benchmark for E, but not proof that the local proxy implementation is valid.",
                "status": "method benchmark",
                "url": "https://www.nature.com/articles/s41467-022-33578-1",
            },
        ],
        "external_source_plan": source_plan,
        "success_criteria": [
            "C and/or E remain defensible under LSD robustness checks.",
            "At least one cross-dataset psilocybin analysis runs without changing the scoring rules after seeing results.",
            "E is explicitly split into landscape-flattening support versus receptor-specific control-placement support.",
            "Schaefer/Yeo sensitivity either preserves C/D/E patterns or reports the failure plainly.",
            "The final dashboard shows evidence, nulls, failures, citations, commands, and export paths.",
        ],
        "failure_modes": [
            "C/E collapse under bootstrap or run sensitivity.",
            "ds006072 preprocessing or metadata incompatibility blocks a fair LSD-psilocybin comparison.",
            "HCP structural graph weakens the current E result.",
            "PET receptor maps do not outperform spatial/null controls.",
            "Schaefer/Yeo extraction changes the sign or rank of C/D/E.",
        ],
    }
    for step in payload["loop_steps"]:
        status_row = loop_status_by_label.get(str(step["label"]))
        if not status_row:
            continue
        step["status"] = status_row.get("status", step["status"])
        step["implementation_evidence"] = status_row.get("evidence")
        step["implementation_blocker"] = status_row.get("blocker")
    payload["loop_status"] = loop_status
    if loop_status.get("analysis_status") != "missing":
        component_statuses = {
            name: component.get("analysis_status")
            for name, component in dict(loop_status.get("components", {})).items()
            if isinstance(component, dict)
        }
        payload["status_summary"] = (
            "The evidence-loop artifact contract is implemented. LSD robustness, Schaefer/Yeo sensitivity, "
            "literature benchmarking, ds006072 Schaefer100/Yeo7 scoring, proxy graph nulls, and coarse receptor-prior nulls "
            "are populated from current results. The ds006072 top-layer mismatch is negative/partial cross-drug "
            "evidence rather than replication; HCP structural graph claims and PET receptor-map claims remain "
            "blocked until their required local data artifacts exist. "
            f"Component statuses: {component_statuses}."
        )
        payload["claim_guardrail"] = loop_status.get("claim_guardrail", payload["claim_guardrail"])
    return payload




_dashboard_cache: dict[str, Any] | None = None


def build_dashboard_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    from lsd_thesis.thesis_upgrade import build_thesis_upgrade_status

    graph = load_graph_config(repo_root / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(repo_root / "configs" / "regimes" / "baseline.yaml")
    perturbed = load_regime_config(repo_root / "configs" / "regimes" / "perturbed.yaml")

    stage_summaries: dict[str, Any] = {}
    stage_summary_paths = {
        "stage_1": repo_root / "results" / "stage_1" / "stage_1_summary.json",
        "stage_2": repo_root / "results" / "stage_2" / "stage_2_summary.json",
        "stage_2b": repo_root / "results" / "stage_2b" / "target_reliability_summary.json",
        "stage_3": repo_root / "results" / "stage_3" / "stage_3_summary.json",
        "stage_4": repo_root / "results" / "stage_4" / "stage_4_summary.json",
        "stage_5": repo_root / "results" / "stage_5" / "literature_weighted_fit_summary.json",
    }
    for stage_name, summary_path in stage_summary_paths.items():
        if summary_path.exists():
            stage_summaries[stage_name] = json.loads(summary_path.read_text(encoding="utf-8"))
    provenance = status_payload.build_provenance_payload(stage_summaries)

    empirical: dict[str, Any] = {}
    sober_target_path = repo_root / "results" / "stage_2" / "empirical_sober_targets.yaml"
    perturbation_target_path = repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml"
    literature_target_path = repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml"
    if sober_target_path.exists():
        sober_target = load_sober_target_set(sober_target_path)
        empirical["sober_metrics"] = {
            name: target.target for name, target in sober_target.metrics.items()
        }
        empirical["sober_fc_matrix"] = sober_target.fc_matrix.tolist()
        empirical["dataset_anchor"] = sober_target.dataset_anchor
    if perturbation_target_path.exists():
        perturbation_target = load_perturbation_target_set(perturbation_target_path)
        empirical["target_deltas"] = perturbation_target.target_deltas
    if literature_target_path.exists():
        literature_target = load_perturbation_target_set(literature_target_path)
        empirical["literature_deltas"] = literature_target.target_deltas
    if provenance["dataset_anchor"] and "dataset_anchor" not in empirical:
        empirical["dataset_anchor"] = provenance["dataset_anchor"]
    atlas_audit_path = repo_root / "results" / "stage_2" / "atlas_mapping_audit.json"
    atlas_audit = (
        cast(dict[str, Any], json.loads(atlas_audit_path.read_text(encoding="utf-8")))
        if atlas_audit_path.exists()
        else None
    )
    empirical_data_quality_path = repo_root / "results" / "stage_2" / "empirical_data_quality.json"
    empirical_data_quality = (
        cast(dict[str, Any], json.loads(empirical_data_quality_path.read_text(encoding="utf-8")))
        if empirical_data_quality_path.exists()
        else None
    )
    audit_status = status_payload.build_audit_status(
        stage_summaries,
        empirical,
        provenance,
        atlas_audit,
        empirical_data_quality,
        repo_root,
    )
    cv5_validation = status_payload.load_cv5_validation_payload(repo_root)

    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    empirical_viewer = load_empirical_viewer_overview(viewer_root)
    empirical_viewer = _augment_empirical_viewer_with_run02(empirical_viewer, repo_root)
    artifact_links = web_artifacts.artifact_links(repo_root)
    if empirical_viewer is not None:
        empirical_viewer["reports"] = artifact_links["reports"]
        gallery_items = []
        for item in empirical_viewer.get("gallery", []):
            href = web_artifacts.artifact_href_from_raw_path(str(item["path"]), repo_root)
            if href is not None:
                gallery_items.append({**item, "href": href})
        empirical_viewer["gallery"] = gallery_items

    return {
        "graph": graph_payload(graph),
        "baseline": build_simulation_payload(graph, baseline),
        "perturbed": build_simulation_payload(graph, perturbed),
        "stage_summaries": stage_summaries,
        "provenance": provenance,
        "audit_status": audit_status,
        "model_selection": status_payload.build_model_selection_payload(stage_summaries),
        "empirical_validation": status_payload.build_empirical_validation_payload(stage_summaries),
        "cv5_validation": cv5_validation,
        "empirical": empirical,
        "empirical_viewer": empirical_viewer,
        "set_setting_seed": _load_set_setting_seed_payload(repo_root),
        "dynamic_mechanism": _load_dynamic_mechanism_payload(repo_root),
        "structural_dti": _load_structural_dti_payload(repo_root),
        "external_cortical_maps": _load_external_cortical_maps_payload(repo_root),
        "claim_status": _load_claim_status_payload(repo_root),
        "thesis_expansion": _build_thesis_expansion_payload(repo_root),
        "thesis_upgrade": build_thesis_upgrade_status(repo_root),
        "artifact_links": artifact_links,
        "baseline_parameters": {
            "within_group_scale": baseline.global_parameters.within_group_scale,
            "cross_group_scale": baseline.global_parameters.cross_group_scale,
            "constraint_scale": baseline.global_parameters.constraint_scale,
            "rigidity": baseline.module_defaults.rigidity,
            "barrier": baseline.module_defaults.barrier,
            "temperature": baseline.module_defaults.temperature,
            "tau": baseline.module_defaults.tau,
        },
    }


def create_app() -> FastAPI:
    app = FastAPI(title="Whole-Brain Surrogate Dashboard")

    @app.get("/assets/plotly.min.js")
    async def plotly_asset() -> Response:
        global _plotly_js_cache
        if _plotly_js_cache is None:
            from plotly.offline import get_plotlyjs

            _plotly_js_cache = get_plotlyjs()
        return Response(
            content=_plotly_js_cache,
            media_type="application/javascript",
            headers={
                "Cache-Control": "public, max-age=86400",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        html = (REPO_ROOT / "src" / "lsd_thesis" / "templates" / "dashboard.html").read_text(
            encoding="utf-8"
        )
        return HTMLResponse(html, headers=web_artifacts.dashboard_security_headers())

    @app.get("/favicon.ico")
    async def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/artifacts/{artifact_path:path}")
    async def artifacts(artifact_path: str) -> Response:
        candidate = web_artifacts.resolve_artifact_path(artifact_path, repo_root=REPO_ROOT)
        if candidate is None:
            return Response(status_code=403)
        if not candidate.exists() or not candidate.is_file():
            return Response(status_code=404)
        if candidate.suffix.lower() not in web_artifacts.SAFE_ARTIFACT_EXTENSIONS:
            return Response(status_code=403)
        return FileResponse(candidate, headers=web_artifacts.artifact_security_headers(candidate, REPO_ROOT))

    @app.get("/api/dashboard-data")
    async def dashboard_data() -> dict[str, Any]:
        global _dashboard_cache
        if _dashboard_cache is None:
            _dashboard_cache = build_dashboard_payload(REPO_ROOT)
        return _dashboard_cache

    @app.get("/api/empirical-view")
    async def empirical_view(subject: str, run: str) -> dict[str, Any]:
        if _empirical_selector_is_invalid(subject, run):
            raise HTTPException(status_code=400, detail="Invalid empirical subject or run identifier.")
        detail = _load_dashboard_empirical_detail(REPO_ROOT, subject=subject, run=run)
        if detail is None:
            raise HTTPException(status_code=404, detail="Empirical view not found.")
        return detail

    @app.post("/api/simulate")
    async def simulate(request: SimulationRequest) -> dict[str, Any]:
        graph = load_graph_config(REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml")
        regime_path = (
            REPO_ROOT
            / "configs"
            / "regimes"
            / ("perturbed.yaml" if request.regime == "perturbed" else "baseline.yaml")
        )
        regime = load_regime_config(regime_path)

        if request.within_group_scale is not None:
            regime.global_parameters.within_group_scale = request.within_group_scale
        if request.cross_group_scale is not None:
            regime.global_parameters.cross_group_scale = request.cross_group_scale
        if request.constraint_scale is not None:
            regime.global_parameters.constraint_scale = request.constraint_scale
        if request.rigidity is not None:
            regime.module_defaults.rigidity = request.rigidity
        if request.barrier is not None:
            regime.module_defaults.barrier = request.barrier
        if request.temperature is not None:
            regime.module_defaults.temperature = request.temperature
        if request.tau is not None:
            regime.module_defaults.tau = request.tau

        return build_simulation_payload(graph, regime)

    return app


app = create_app()
