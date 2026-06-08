from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .formatting import _markdown
from .gates import (
    _archive_gate,
    _external_gate,
    _motion_gate,
    _neuromaps_spatial_null_gate,
    _parcellation_gate,
    _public_dashboard_gate,
    _receptor_myelin_gradient_claim_gate,
    _receptor_structural_gate,
    _rocket_gate,
)
from .requirements import _package_requirement, _requirement
from .status import REPO_ROOT, SCHEMA_VERSION, _rel


def build_thesis_upgrade_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    components = {
        "motion_confound": _motion_gate(repo_root),
        "canonical_parcellation": _parcellation_gate(repo_root),
        "neuromaps_spatial_nulls": _neuromaps_spatial_null_gate(repo_root),
        "rocket_strengthening": _rocket_gate(repo_root),
        "public_dashboard": _public_dashboard_gate(repo_root),
        "external_validation": _external_gate(repo_root),
        "receptor_structural": _receptor_structural_gate(repo_root),
        "receptor_myelin_gradient_claim": _receptor_myelin_gradient_claim_gate(repo_root),
        "reproducible_archive": _archive_gate(repo_root),
    }
    gates = [component["gate"] for component in components.values()]
    public_dashboard = components["public_dashboard"]
    public_dashboard_gate = public_dashboard["gate"]
    reproducible_archive = components["reproducible_archive"]
    reproducible_archive_gate = reproducible_archive["gate"]
    package_requirements = [
        _package_requirement(
            "public_dashboard_static_snapshot",
            "Public dashboard static snapshot",
            str(public_dashboard_gate["status"]),
            bool(public_dashboard_gate["ready"]),
            str(public_dashboard_gate["evidence"]),
            (
                "None: static Pages snapshot contains the required dashboard and evidence artifacts."
                if public_dashboard_gate["ready"]
                else "Static Pages snapshot is stale: {mismatches}.".format(
                    mismatches=", ".join(str(item) for item in public_dashboard.get("snapshot_mismatches", []))
                    or "readiness snapshot mismatch"
                )
                if public_dashboard.get("snapshot_mismatches")
                else "Static Pages snapshot is missing required dashboard/evidence artifacts: {paths}.".format(
                    paths=", ".join(str(item) for item in public_dashboard.get("missing_required_paths", [])) or "unknown"
                )
            ),
            (
                "Keep rebuilding the static site after gate/status artifact changes."
                if public_dashboard_gate["ready"]
                else (
                    "Run scripts/build_github_pages.py after regenerating results/thesis_upgrade/thesis_upgrade_status.json, "
                    "then verify _site embeds the same readiness summary and requirement states."
                )
                if public_dashboard.get("snapshot_mismatches")
                else "Run scripts/build_github_pages.py and verify _site/pages_manifest.json includes the dashboard and evidence artifacts."
            ),
            (
                "The public dashboard is presentation-ready, but remains separate from citable archive publication."
                if public_dashboard_gate["ready"]
                else "Public presentation remains incomplete until the static dashboard snapshot is regenerated."
            ),
        ),
        _package_requirement(
            "reproducible_archive_publication",
            "Reproducible archive publication",
            str(reproducible_archive_gate["status"]),
            bool(reproducible_archive.get("archive_publication_ready")),
            str(reproducible_archive_gate["evidence"]),
            (
                "None: citable GitHub release URL and DOI are recorded in the archive manifest."
                if reproducible_archive.get("archive_publication_ready")
                else "Citable archive publication is missing {requirements}.".format(
                    requirements=" and ".join(
                        str(item) for item in reproducible_archive.get("missing_publication_requirements", [])
                    )
                    or "verified release/DOI metadata"
                )
            ),
            (
                "Keep the archive manifest synchronized with the release and DOI."
                if reproducible_archive.get("archive_publication_ready")
                else (
                    "Mint a Zenodo DOI for the existing GitHub release, then rebuild "
                    "scripts/build_reproducible_archive.py with --release-url and --doi."
                )
                if reproducible_archive.get("publication_release_ready")
                else (
                    "Create a GitHub release, mint a Zenodo DOI for that release, then rebuild "
                    "scripts/build_reproducible_archive.py with --release-url and --doi."
                )
            ),
            (
                "The package has a citable derived-artifact archive."
                if reproducible_archive.get("archive_publication_ready")
                else "The package is not publication-archive-ready until the release and DOI are recorded."
            ),
        ),
    ]
    strict_requirements = [
        components["canonical_parcellation"]["strict_requirement"],
        components["neuromaps_spatial_nulls"]["strict_requirement"],
        components["external_validation"]["strict_requirement"],
        components["motion_confound"]["strict_requirement"],
        components["receptor_myelin_gradient_claim"]["strict_requirement"],
    ]
    evidence_requirements_complete = all(requirement["complete"] for requirement in strict_requirements)
    non_motion_strict_requirements_complete = all(
        requirement["complete"]
        for requirement in strict_requirements
        if requirement["requirement_id"] != "motion_confound_control_result"
    )
    full_motion_control_ready = bool(components["motion_confound"].get("fmriprep_motion_control_ready"))
    external_validation = components["external_validation"]
    stronger_external_validation_ready = bool(external_validation.get("stronger_external_validation_ready"))
    project_complete = (
        evidence_requirements_complete
        and full_motion_control_ready
        and stronger_external_validation_ready
    )
    proxy_evidence_visible = evidence_requirements_complete or non_motion_strict_requirements_complete
    project_status = (
        "completed_neuroscience_thesis"
        if project_complete
        else "research_demo_ready_not_completed_thesis"
        if proxy_evidence_visible
        else "pi_pitch_ready_research_proposal_not_completed_thesis"
    )
    remaining_hard_requirements = []
    if not full_motion_control_ready:
        remaining_hard_requirements.append("fMRIPrep FD/DVARS/censoring motion proof")
    if not stronger_external_validation_ready:
        remaining_hard_requirements.append("stronger parcellation-matched external validation")
    project_missing = (
        "None: all strict science gates and hard completion requirements are satisfied."
        if project_complete
        else "Proxy/stress-test evidence gates are visible, but completion still requires {requirements}.".format(
            requirements=" and ".join(remaining_hard_requirements)
        )
        if proxy_evidence_visible and remaining_hard_requirements
        else (
            "Proxy/stress-test evidence gates are visible, but hard completion requirements are not fully resolved."
        )
        if proxy_evidence_visible
        else "One or more required scientific gates is still missing or fail-closed."
    )
    project_next_action = (
        "Proceed with final thesis packaging and archive release."
        if project_complete
        else "Keep this as a controlled research demo while upgrading {requirements}.".format(
            requirements=" and ".join(remaining_hard_requirements)
        )
        if proxy_evidence_visible and remaining_hard_requirements
        else (
            "Keep this as a controlled research demo while resolving the remaining hard completion requirements."
        )
        if proxy_evidence_visible
        else "Keep pitching this as an AI/engineering research proposal until every strict evidence gate passes."
    )
    project_claim_effect = (
        "The strict evidence package is complete under the current thesis contract."
        if project_complete
        else "This remains a controlled research demo/PI pitch until {requirements} passes.".format(
            requirements=" and ".join(remaining_hard_requirements)
        )
        if proxy_evidence_visible and remaining_hard_requirements
        else (
            "This remains a controlled research demo/PI pitch, not a completed neuroscience "
            "thesis, until hard motion and external-validation requirements pass."
        )
    )
    strict_requirements.append(
        _requirement(
            "project_phase",
            "Project phase",
            project_status,
            project_complete,
            "strict_completion_requirements",
            project_missing,
            project_next_action,
            project_claim_effect,
        )
    )
    ready_count = sum(1 for gate in gates if gate["ready"])
    strict_ready_count = sum(1 for requirement in strict_requirements if requirement["complete"])
    package_ready_count = sum(1 for requirement in package_requirements if requirement["complete"])
    strict_missing_requirement_ids = [
        str(requirement["requirement_id"]) for requirement in strict_requirements if not requirement["complete"]
    ]
    package_missing_requirement_ids = [
        str(requirement["requirement_id"]) for requirement in package_requirements if not requirement["complete"]
    ]
    completion_status = project_status
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "readiness_summary": {
            "ready_gates": ready_count,
            "total_gates": len(gates),
            "readiness_fraction": ready_count / len(gates) if gates else 0.0,
            "strict_complete_gates": strict_ready_count,
            "strict_total_gates": len(strict_requirements),
            "strict_completion_fraction": strict_ready_count / len(strict_requirements) if strict_requirements else 0.0,
            "strict_missing_gates": len(strict_missing_requirement_ids),
            "strict_missing_requirement_ids": strict_missing_requirement_ids,
            "package_complete_gates": package_ready_count,
            "package_total_gates": len(package_requirements),
            "package_completion_fraction": package_ready_count / len(package_requirements) if package_requirements else 0.0,
            "package_missing_gates": len(package_missing_requirement_ids),
            "package_missing_requirement_ids": package_missing_requirement_ids,
            "remaining_hard_requirements": remaining_hard_requirements,
            "remaining_packaging_requirements": [
                requirement["label"] for requirement in package_requirements if not requirement["complete"]
            ],
            "completion_status": completion_status,
            "thesis_status": completion_status,
        },
        "gates": gates,
        "strict_completion_requirements": strict_requirements,
        "package_readiness_requirements": package_requirements,
        "components": components,
        "visualization_plan": {
            "dashboard_panels": [
                "thesis gate bar",
                "strict completion audit",
                "ROCKET strength radar",
                "motion/QC ribbon",
                "parcellation proxy-vs-canonical board",
                "public dashboard snapshot integrity gate",
                "external/receptor/structural/archive evidence matrix",
                "3D latent and control-landscape panels when source arrays are available",
            ]
        },
        "claim_guardrail": (
            "This status file upgrades evidence visibility and fails closed on missing science. It does not convert "
            "proxy analyses into receptor-level, clinical, subjective-experience, or external-validity proof."
        ),
        "source_basis": [
            {
                "topic": "motion confounds",
                "source": "fMRIPrep outputs: framewise displacement, DVARS, motion outliers",
                "url": "https://fmriprep.org/en/23.1.2/outputs.html",
            },
            {
                "topic": "canonical parcellation",
                "source": "Schaefer et al. 2018 local-global parcellation aligned to Yeo networks",
                "url": "https://doi.org/10.1093/cercor/bhx179",
            },
            {
                "topic": "ROCKET strengthening",
                "source": "MiniRocket and MultiRocket time-series classification variants",
                "url": "https://arxiv.org/abs/2012.08791",
            },
            {
                "topic": "brain-map priors",
                "source": "neuromaps reference maps and spatial nulls",
                "url": "https://www.nature.com/articles/s41592-022-01625-w",
            },
            {
                "topic": "archive",
                "source": "GitHub and Zenodo repository DOI workflow",
                "url": "https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content",
            },
        ],
    }

def write_thesis_upgrade_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "thesis_upgrade"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_thesis_upgrade_status(repo_root)
    status_path = output_dir / "thesis_upgrade_status.json"
    report_path = output_dir / "thesis_upgrade_status.md"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    return status
