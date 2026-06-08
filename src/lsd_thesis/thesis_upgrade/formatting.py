from __future__ import annotations

from typing import Any


def _markdown(status: dict[str, Any]) -> str:
    lines = [
        "# Thesis Upgrade Status",
        "",
        status["claim_guardrail"],
        "",
        "## Gate Summary",
        "",
        "- Strict completion: {complete}/{total} gates complete.".format(
            complete=status["readiness_summary"]["strict_complete_gates"],
            total=status["readiness_summary"]["strict_total_gates"],
        ),
        "- Package readiness: {complete}/{total} gates complete.".format(
            complete=status["readiness_summary"]["package_complete_gates"],
            total=status["readiness_summary"]["package_total_gates"],
        ),
        "- Missing strict requirement IDs: {missing}.".format(
            missing=", ".join(status["readiness_summary"]["strict_missing_requirement_ids"]) or "none",
        ),
        "- Missing package requirement IDs: {missing}.".format(
            missing=", ".join(status["readiness_summary"]["package_missing_requirement_ids"]) or "none",
        ),
        "- Remaining hard requirements: {requirements}.".format(
            requirements=", ".join(status["readiness_summary"]["remaining_hard_requirements"]) or "none",
        ),
        "- Remaining packaging requirements: {requirements}.".format(
            requirements=", ".join(status["readiness_summary"]["remaining_packaging_requirements"]) or "none",
        ),
        "",
        "| Gate | Status | Ready | Score | Blocker / next action |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for gate in status["gates"]:
        lines.append(
            "| {label} | {status} | {ready} | {score:.2f} | {blocker} |".format(
                label=gate["label"],
                status=gate["status"],
                ready=str(gate["ready"]).lower(),
                score=float(gate["score"]),
                blocker=str(gate["blocker"]).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Package Readiness Audit",
            "",
            "| Requirement | Status | Complete | Missing | Next action |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for requirement in status["package_readiness_requirements"]:
        lines.append(
            "| {label} | {status} | {complete} | {missing} | {next_action} |".format(
                label=requirement["label"],
                status=requirement["status"],
                complete=str(requirement["complete"]).lower(),
                missing=str(requirement["missing"]).replace("|", "/"),
                next_action=str(requirement["next_action"]).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Strict Completion Audit",
            "",
            "| Requirement | Status | Complete | Missing | Next action |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for requirement in status["strict_completion_requirements"]:
        lines.append(
            "| {label} | {status} | {complete} | {missing} | {next_action} |".format(
                label=requirement["label"],
                status=requirement["status"],
                complete=str(requirement["complete"]).lower(),
                missing=str(requirement["missing"]).replace("|", "/"),
                next_action=str(requirement["next_action"]).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Canonical Next State",
            "",
            "- Primary canonical parcellation target: `schaefer_100_yeo_7`.",
            "- Sensitivity targets: `schaefer_200_yeo_7`, `schaefer_100_yeo_17`, `schaefer_200_yeo_17`.",
            "- External validation target: OpenNeuro `ds006072` psilocybin precision functional mapping.",
            "- Receptor/structural target: PET-derived receptor priors plus documented structural-connectome graph in the active parcellation.",
            "- Archive target: GitHub release plus Zenodo DOI, with raw OpenNeuro files cited rather than bundled.",
            "",
        ]
    )
    return "\n".join(lines)
