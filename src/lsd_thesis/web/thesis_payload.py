from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from lsd_thesis.external_source_plan import external_source_plan_rows


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _thesis_upgrade_component(status: dict[str, Any], component_id: str) -> dict[str, Any]:
    components = status.get("components", {}) if isinstance(status.get("components"), dict) else {}
    component = components.get(component_id)
    return component if isinstance(component, dict) else {}


def _strict_requirement(component: dict[str, Any]) -> dict[str, Any]:
    requirement = component.get("strict_requirement")
    return requirement if isinstance(requirement, dict) else {}


def _gate_status(component: dict[str, Any], default: str) -> str:
    requirement = _strict_requirement(component)
    raw_gate = component.get("gate")
    gate = raw_gate if isinstance(raw_gate, dict) else {}
    return str(requirement.get("status") or gate.get("status") or default)


def load_thesis_loop_status(repo_root: Path) -> dict[str, Any]:
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


def load_claim_status_payload(repo_root: Path) -> dict[str, Any]:
    claim_ladder_path = repo_root / "CLAIM_LADDER.md"
    pi_pitch_path = repo_root / "PI_PITCH.md"
    thesis_upgrade = _load_json_object(repo_root / "results" / "thesis_upgrade" / "thesis_upgrade_status.json")
    external_component = _thesis_upgrade_component(thesis_upgrade, "external_validation")
    neuromaps_component = _thesis_upgrade_component(thesis_upgrade, "neuromaps_spatial_nulls")
    map_claim_component = _thesis_upgrade_component(thesis_upgrade, "receptor_myelin_gradient_claim")

    external_status = _gate_status(external_component, "scored_when_comparable_viewer_present")
    external_ready = bool(_strict_requirement(external_component).get("complete"))
    external_boundary = (
        "Schaefer100/Yeo7 unchanged scoring is implemented as an external stress test; "
        "a top-layer mismatch remains negative/partial evidence, not LSD replication."
        if external_ready
        else "Schaefer100/Yeo7 unchanged scoring is planned as an external stress test; it is not LSD replication."
    )
    spatial_status = _gate_status(neuromaps_component, "next_required_upgrade")
    spatial_ready = bool(_strict_requirement(neuromaps_component).get("complete"))
    map_claim_status = _gate_status(map_claim_component, "do_not_strengthen_mechanism_claim")
    map_claim_ready = bool(_strict_requirement(map_claim_component).get("complete"))
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
                "status": external_status,
                "claim_boundary": external_boundary,
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
                "control": "Schaefer/Yeo spatial nulls",
                "purpose": "test map-prior claims with spatial-autocorrelation-aware inference",
                "status": spatial_status if spatial_ready else "next_required_upgrade",
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
                "ci": "reported in spatial-null rows" if spatial_ready else "not run",
                "p": "Moran spatial-null p-values reported" if spatial_ready else "not run",
                "q": "no FDR support" if spatial_ready else "not run",
                "fdr_pass": "no",
                "ci_crosses_zero": "mixed" if spatial_ready else "unknown",
                "claim_status": map_claim_status if spatial_ready else "blocked_until_schaefer_yeo_neuromaps",
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
                "status": "resolved_negative_control" if map_claim_ready else "exploratory",
                "evidence": "Module-level p/q/CI-gated alignments are displayed, but not significant enough for strong mechanism claims.",
                "pi_framing": "Shows honesty: the system reports weak evidence instead of hiding it.",
            },
            {
                "tier": "E",
                "claim": "Strong receptor/myelin/gradient mechanism",
                "status": map_claim_status,
                "evidence": (
                    "Completed Schaefer/Yeo spatial-null evidence resolves this as a negative/control result."
                    if map_claim_ready
                    else "Needs Schaefer/Yeo or Glasser parcel-level inference plus spatial nulls."
                ),
                "pi_framing": "Clear Master's work package rather than overclaiming.",
            },
            {
                "tier": "F",
                "claim": "External psilocybin validation",
                "status": external_status if external_ready else "blocked_future_work",
                "evidence": (
                    "ds006072 Schaefer100/Yeo7 unchanged scoring is implemented as a stress test; "
                    "literature and future multimodal datasets remain context/planning anchors."
                    if external_ready
                    else (
                        "External literature and future multimodal datasets are context/planning anchors until "
                        "comparable data are ingested and scored unchanged."
                    )
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
                "message": (
                    "ds006072 unchanged scoring is implemented as an external stress test; "
                    "literature-only psilocybin papers remain context, not validation of this score."
                    if external_ready
                    else "Current psilocybin papers are external context, not validation of this score until data are ingested and scored unchanged."
                ),
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
            "Keep Schaefer-100/Yeo-7 as the primary inference layer and reserve Schaefer-200/Yeo-17 or Glasser for scoped sensitivity upgrades.",
            "Keep receptor, DTI/SC, myelin, gradient, and AHBA maps in the same parcel contract before promoting any biological-prior claim.",
            "Maintain the spatial-null/FDR/CI-zero gate as the map-prior promotion rule.",
            "Turn leak-proof ML benchmarks into a compact AI contribution slide.",
            "Resolve authorized fMRIPrep FD/DVARS/censoring confounds before calling the thesis complete.",
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


def build_thesis_expansion_payload(repo_root: Path) -> dict[str, Any]:
    loop_status = load_thesis_loop_status(repo_root)
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
                "label": "Motion-sensitive C gate",
                "status": "blocked",
                "artifact_target": "results/confound_controls/",
                "scientific_question": (
                    "Does C remain defensible after subject/run FD, DVARS, censoring/outlier, "
                    "image-QC, and high-burden exclusion checks?"
                ),
                "dashboard_output": "Motion-sensitive exclusion gate with explicit blocker text.",
            },
            {
                "step": "3",
                "label": "Psilocybin ds006072",
                "status": "planned",
                "artifact_target": "results/psilocybin_ds006072/",
                "scientific_question": "Does the LSD ranking generalize to psilocybin precision functional mapping data, or fail under unchanged scoring?",
                "dashboard_output": "LSD-vs-psilocybin mechanism ranking comparison with negative/partial outcomes retained.",
            },
            {
                "step": "4",
                "label": "HCP structural graph",
                "status": "planned",
                "artifact_target": "results/structural_connectome/",
                "scientific_question": "Does E remain plausible when the macro proxy graph is replaced by a normative structural connectome?",
                "dashboard_output": "Control-energy comparison across proxy, structural, uniform, degree, and graph-rewire controls.",
            },
            {
                "step": "5",
                "label": "PET receptor priors",
                "status": "planned",
                "artifact_target": "results/receptor_priors/",
                "scientific_question": "Do neuromaps/FS5ht 5-HT2A priors outperform uniform, random, degree, and spatial nulls?",
                "dashboard_output": "Receptor-prior null board and claim-status split for E.",
            },
            {
                "step": "6",
                "label": "Schaefer/Yeo sensitivity",
                "status": "planned",
                "artifact_target": "results/parcellation_sensitivity/",
                "scientific_question": "Are C/D/E findings stable beyond the current 8-module proxy representation?",
                "dashboard_output": "Schaefer 100/200 and Yeo 7/17 result matrix.",
            },
            {
                "step": "7",
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
            "The evidence-loop artifact contract is implemented. LSD robustness, motion-sensitive C gating, "
            "Schaefer/Yeo sensitivity, literature benchmarking, ds006072 Schaefer100/Yeo7 scoring, HCP structural "
            "graph rewires, PET 5-HT2A priors, and spatial-null claim gates are populated from current results. "
            "The ds006072 top-layer mismatch is negative/partial cross-drug evidence rather than replication; "
            "the motion-sensitive C gate remains blocked until authorized subject/run confounds exist; "
            "the striatal-unimodal benchmark is now measurable only as a bilateral Harvard-Oxford proxy row. "
            f"Component statuses: {component_statuses}."
        )
        payload["claim_guardrail"] = loop_status.get("claim_guardrail", payload["claim_guardrail"])
    return payload
