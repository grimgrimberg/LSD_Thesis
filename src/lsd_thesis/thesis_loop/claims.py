from __future__ import annotations

from typing import Any

from .status import _analysis_status, _claim_row, _literature_mismatch_status, _parcellation_claim_status


def _build_claim_evidence_matrix(components: dict[str, Any]) -> list[dict[str, Any]]:
    lsd = components.get("lsd_robustness", {})
    psilocybin = components.get("psilocybin_ds006072", {})
    structural = components.get("structural_connectome", {})
    receptor = components.get("receptor_priors", {})
    motion_sensitive_c = components.get("motion_sensitive_c_gate", {})
    parcellation = components.get("parcellation_sensitivity", {})
    literature = components.get("literature_benchmark", {})
    striatal_gate = (
        literature.get("striatal_unimodal_gate", {})
        if isinstance(literature.get("striatal_unimodal_gate"), dict)
        else {}
    )
    return [
        _claim_row(
            claim="C survives LSD robustness checks",
            dataset="OpenNeuro ds003059 LSD/placebo empirical viewer",
            model_layer="C hierarchy/routing",
            null_control=(
                "subject bootstrap; run sensitivity; A/E state-label sensitivity; "
                "D window and E horizon stress tests"
            ),
            figure=(
                "dynamic_hierarchy_plot; robustness_bootstrap_plot; "
                "robustness_run_plot"
            ),
            export=(
                "results/dynamic_mechanism_ranking/exports/dynamic_mechanism_results.xlsx; "
                "results/thesis_evidence_loop/claim_evidence_matrix.csv"
            ),
            citation=(
                "Girn et al. 2026 Nature Medicine https://www.nature.com/articles/s41591-026-04287-9"
            ),
            limitation="Internal LSD-only proxy evidence; not causal mechanism proof.",
            status=_analysis_status(lsd),
        ),
        _claim_row(
            claim="C final thesis claim passes motion-sensitive exclusions",
            dataset="ds003059 run-01/run-03 plus motion/confound control artifacts",
            model_layer="C hierarchy/routing",
            null_control="subject/run FD, DVARS, censoring/outlier burden, image-QC, and high-burden exclusions",
            figure="motion_confound_control_table; module_dvars_control_table; image_motion_qc_table",
            export=(
                "results/confound_controls/motion_confound_control_status.json; "
                "results/confound_controls/module_dvars_control_status.json; "
                "results/confound_controls/image_motion_qc_status.json"
            ),
            citation=(
                "Carhart-Harris et al. 2016 PNAS https://doi.org/10.1073/pnas.1518377113"
            ),
            limitation=(
                "Current local checkout lacks authorized subject/run fMRIPrep FD, DVARS, and "
                "censoring confounds; image-derived or published aggregate QC cannot complete the strict gate."
            ),
            status=_analysis_status(motion_sensitive_c),
        ),
        _claim_row(
            claim="C survives Schaefer/Yeo 100/200 and Yeo 7/17 with comparable direction",
            dataset="ds003059 parcellation sensitivity artifacts",
            model_layer="C hierarchy/routing",
            null_control="Schaefer 100/200 and Yeo 7/17 versus the current 8-module proxy",
            figure="parcellation_sensitivity_table",
            export=(
                "results/parcellation_sensitivity/parcellation_status.csv; "
                "results/parcellation_sensitivity/parcellation_ranking_comparison.csv; "
                "results/thesis_evidence_loop/exports/thesis_evidence_loop_tables.xlsx"
            ),
            citation="Schaefer et al. 2018 Cerebral Cortex https://doi.org/10.1093/cercor/bhx179",
            limitation=(
                "Status matrix is not full sensitivity evidence unless parcellation-specific "
                "empirical viewer and ranking rows exist."
            ),
            status=_parcellation_claim_status(parcellation),
        ),
        _claim_row(
            claim="E survives real structural-connectome graph",
            dataset="HCP Young Adult or local normative structural-connectome CSV",
            model_layer="E network-control energy",
            null_control="macro proxy graph; uniform graph; degree-expected graph; edge-weight rewires",
            figure="dynamic_control_plot; structural_proxy_null_table",
            export=(
                "results/structural_connectome/structural_connectome_status.json; "
                "results/structural_connectome/proxy_graph_control_nulls.csv"
            ),
            citation=(
                "HCP Young Adult https://www.humanconnectome.org/study/hcp-young-adult; "
                "Singleton et al. 2022 Nature Communications https://www.nature.com/articles/s41467-022-33578-1"
            ),
            limitation=(
                "Structural graph sensitivity is still a normative/proxy sensitivity layer; graph-rewire "
                "nulls test topology dependence but do not establish biological causality."
            ),
            status=_analysis_status(structural),
        ),
        _claim_row(
            claim="E survives PET receptor-map priors",
            dataset="neuromaps/FS5ht 5-HT2A PET receptor prior projected to modules",
            model_layer="E receptor-informed network-control energy",
            null_control="uniform; random permutation; degree control; spatial/autocorrelation null",
            figure="dynamic_control_plot; receptor_null_table",
            export=(
                "results/receptor_priors/receptor_prior_status.json; "
                "results/receptor_priors/proxy_receptor_null_board.csv"
            ),
            citation=(
                "Markello et al. 2022 Nature Methods https://www.nature.com/articles/s41592-022-01625-w; "
                "Singleton et al. 2022 Nature Communications https://www.nature.com/articles/s41467-022-33578-1"
            ),
            limitation=(
                "PET-derived 5-HT2A priors and Schaefer100 Moran spatial nulls are required together; "
                "current spatial-null/FDR evidence blocks receptor-claim promotion if support is absent."
            ),
            status=str(receptor.get("claim_promotion_status") or _analysis_status(receptor)),
        ),
        _claim_row(
            claim="ds006072 psilocybin tests the LSD A+B+C+D+E ranking",
            dataset="OpenNeuro ds006072 psilocybin precision functional mapping",
            model_layer="A+B+C+D+E mechanism ranking",
            null_control="same scoring rules as LSD; paired psilocybin/control empirical viewer",
            figure="thesis_loop_steps; LSD-vs-psilocybin ranking comparison",
            export=(
                "results/psilocybin_ds006072/psilocybin_ds006072_status.json; "
                "results/thesis_evidence_loop/exports/ds006072_summary.csv"
            ),
            citation=(
                "Dosenbach/Siegel group 2025 Scientific Data https://doi.org/10.1038/s41597-025-05189-0; "
                "OpenNeuro ds006072 https://openneuro.org/datasets/ds006072"
            ),
            limitation=(
                "Comparable Schaefer100/Yeo7 scoring is a cross-drug stress test; "
                "a differing top layer is negative/partial external evidence, not replication."
            ),
            status=_analysis_status(psilocybin),
        ),
        _claim_row(
            claim="Final C/D/E pattern aligns with psychedelic mega-analysis and NCT anchors",
            dataset="ds003059 LSD proxy deltas plus literature benchmark rows",
            model_layer="C hierarchy/routing; D dynamic repertoire; E network-control energy",
            null_control="directional proxy benchmark; explicit mismatches retained",
            figure="literature_benchmark_plot; literature_benchmark_table",
            export=(
                "results/literature_benchmark/literature_benchmark.csv; "
                "results/thesis_evidence_loop/claim_evidence_matrix.csv"
            ),
            citation=(
                "Girn et al. 2026 Nature Medicine https://www.nature.com/articles/s41591-026-04287-9; "
                "Singleton et al. 2022 Nature Communications https://www.nature.com/articles/s41467-022-33578-1"
            ),
            limitation="Directional proxy benchmark only; not a mega-analysis or full NCT reproduction.",
            status=_analysis_status(literature),
        ),
        _claim_row(
            claim="Nature Medicine striatal-unimodal benchmark is testable",
            dataset="ds003059/ds006072 high-resolution parcellation benchmark rows",
            model_layer="C/D striatal-subcortical routing",
            null_control="dedicated caudate/putamen/accumbens parcels versus cortical-only proxy rows",
            figure="literature_benchmark_table; Schaefer100/Yeo7 + Harvard-Oxford striatal sensitivity row",
            export=(
                "results/literature_benchmark/literature_benchmark.csv; "
                "results/thesis_evidence_loop/claim_evidence_matrix.csv"
            ),
            citation=(
                "Girn et al. 2026 Nature Medicine https://www.nature.com/articles/s41591-026-04287-9"
            ),
            limitation=(
                "The current implemented row uses bilateral Harvard-Oxford striatum as a proxy. It tests "
                "whether the benchmark is directionally measurable, not whether the Nature Medicine "
                "nucleus-level result is reproduced."
            ),
            status=str(striatal_gate.get("analysis_status") or "blocked_missing_striatal_or_subcortical_parcels"),
        ),
        _claim_row(
            claim="Failed literature checks are diagnosed as contradiction or proxy mismatch",
            dataset="results/literature_benchmark/literature_benchmark.csv",
            model_layer="C/D/E failure-case analysis",
            null_control="row-level mismatch review; sign/opposes/weak checks",
            figure="literature_benchmark_table",
            export=(
                "results/literature_benchmark/literature_benchmark.csv; "
                "results/thesis_evidence_loop/claim_evidence_matrix.csv"
            ),
            citation=(
                "Girn et al. 2026 Nature Medicine https://www.nature.com/articles/s41591-026-04287-9; "
                "Singleton et al. 2022 Nature Communications https://www.nature.com/articles/s41467-022-33578-1"
            ),
            limitation=(
                "Requires explicit per-row mismatch reason; unresolved mismatches stay out of "
                "final conclusions."
            ),
            status=_literature_mismatch_status(literature),
        ),
    ]
