from __future__ import annotations

from typing import Any

EXTERNAL_SOURCE_PLAN_COLUMNS = [
    "source_id",
    "source",
    "source_type",
    "key_evidence",
    "use_in_project",
    "status",
    "component",
    "current_component_status",
    "target_layers",
    "artifact_target",
    "next_artifact",
    "claim_boundary",
    "url",
    "doi",
]

EXTERNAL_SOURCE_PLAN: tuple[dict[str, str], ...] = (
    {
        "source_id": "girn_2026_mega_analysis",
        "source": "Girn et al., Nature Medicine 2026",
        "source_type": "external benchmark",
        "key_evidence": (
            "Common psychedelic signature: increased transmodal-unimodal functional coupling "
            "with subnetwork specificity; striatal-unimodal effects are prominent."
        ),
        "use_in_project": "Final external benchmark for C/D/E directionality.",
        "status": "planned comparison",
        "component": "literature_benchmark",
        "target_layers": "C/D/E",
        "artifact_target": "results/literature_benchmark/",
        "next_artifact": "results/literature_benchmark/literature_benchmark_status.json",
        "claim_boundary": (
            "Directionality benchmark only; it is not a reproduction of the mega-analysis "
            "and the current 8-module proxy cannot test striatal effects."
        ),
        "url": "https://www.nature.com/articles/s41591-026-04287-9",
        "doi": "10.1038/s41591-026-04287-9",
    },
    {
        "source_id": "dosenbach_siegel_ds006072_2025",
        "source": "Dosenbach/Siegel group, Scientific Data 2025",
        "source_type": "cross-drug dataset",
        "key_evidence": (
            "OpenNeuro ds006072 provides psilocybin precision functional mapping data "
            "with raw, minimally processed, and fully processed imaging."
        ),
        "use_in_project": "First cross-drug stress-test dataset after LSD robustness.",
        "status": "implemented external stress test",
        "component": "psilocybin_ds006072",
        "target_layers": "A/B/C/D/E",
        "artifact_target": "results/psilocybin_ds006072/",
        "next_artifact": "results/psilocybin_ds006072/psilocybin_ds006072_status.json",
        "claim_boundary": (
            "Schaefer100/Yeo7 paired psilocybin/control scoring is external stress-test "
            "evidence, not replication when the top layer differs from the LSD reference."
        ),
        "url": "https://www.nature.com/articles/s41597-025-05189-0",
        "doi": "10.1038/s41597-025-05189-0",
    },
    {
        "source_id": "markello_neuromaps_2022",
        "source": "Markello et al., Nature Methods 2022",
        "source_type": "biological prior",
        "key_evidence": (
            "neuromaps provides standardized brain-map comparison tools and receptor PET annotations."
        ),
        "use_in_project": "Replace hand-built receptor proxies with documented receptor-map projections.",
        "status": "planned biological prior",
        "component": "receptor_priors",
        "target_layers": "E",
        "artifact_target": "results/receptor_priors/",
        "next_artifact": "results/receptor_priors/receptor_prior_status.json",
        "claim_boundary": (
            "Current coarse receptor weights are proxy-only; receptor claims need PET-derived "
            "maps and spatial-autocorrelation-preserving nulls."
        ),
        "url": "https://www.nature.com/articles/s41592-022-01625-w",
        "doi": "10.1038/s41592-022-01625-w",
    },
    {
        "source_id": "hcp_young_adult",
        "source": "Human Connectome Project Young Adult",
        "source_type": "graph prior",
        "key_evidence": (
            "Large normative dataset with diffusion and resting-state fMRI for healthy young adults."
        ),
        "use_in_project": "Source for structural-connectome graph and null sensitivity.",
        "status": "planned graph prior",
        "component": "structural_connectome",
        "target_layers": "E",
        "artifact_target": "results/structural_connectome/",
        "next_artifact": "results/structural_connectome/structural_connectome_status.json",
        "claim_boundary": (
            "Proxy graph controls are not structural-connectome evidence; an HCP/normative "
            "module graph is required for the stronger E claim."
        ),
        "url": "https://www.humanconnectome.org/study/hcp-young-adult/overview",
        "doi": "",
    },
    {
        "source_id": "schaefer_2018_local_global",
        "source": "Schaefer et al., Cerebral Cortex 2018",
        "source_type": "parcellation",
        "key_evidence": (
            "Multiresolution local-global cortical parcellations support network neuroscience "
            "and graph analyses."
        ),
        "use_in_project": "Sensitivity layer for C/D/E beyond the 8-module proxy.",
        "status": "planned parcellation",
        "component": "parcellation_sensitivity",
        "target_layers": "C/D/E",
        "artifact_target": "results/parcellation_sensitivity/",
        "next_artifact": "results/parcellation_sensitivity/parcellation_sensitivity_status.json",
        "claim_boundary": (
            "The 8-module layer stays a transparent summary; C/D/E claims need Schaefer/Yeo "
            "sensitivity rows before promotion."
        ),
        "url": "https://academic.oup.com/cercor/article/28/9/3095/3978804",
        "doi": "10.1093/cercor/bhx179",
    },
)


IMPLEMENTED_SOURCE_STATUS_LABELS = {
    "literature_benchmark": "implemented directional proxy benchmark",
    "psilocybin_ds006072": "implemented external stress test",
    "receptor_priors": "implemented PET receptor-prior sensitivity",
    "structural_connectome": "implemented HCP structural graph sensitivity",
    "parcellation_sensitivity": "implemented Schaefer/Yeo sensitivity",
}


def external_source_by_id(source_id: str) -> dict[str, str]:
    for row in EXTERNAL_SOURCE_PLAN:
        if row["source_id"] == source_id:
            return dict(row)
    raise KeyError(f"Unknown external source id: {source_id}")


def external_source_plan_rows(component_statuses: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in EXTERNAL_SOURCE_PLAN:
        row: dict[str, Any] = dict(source)
        component = row["component"]
        current_component_status = (
            str(component_statuses.get(component) or "missing") if component_statuses else "unverified"
        )
        row["current_component_status"] = current_component_status
        if current_component_status.startswith("implemented"):
            row["status"] = IMPLEMENTED_SOURCE_STATUS_LABELS.get(component, current_component_status)
        rows.append(row)
    return rows
