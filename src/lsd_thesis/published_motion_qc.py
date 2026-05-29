from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "published_motion_qc.v1"

SOURCE_SNIPPETS = {
    "excluded_high_motion_subjects": "four others were discarded from the group analyses due to excessive head movement",
    "fd_exclusion_threshold": "subjects with >15%  scrubbed volumes when the scrubbing threshold is FD = 0.5",
    "retained_mean_fd_difference": "for the 15 subjects that were used in the analysis the difference in mean FD was 0.046",
    "condition_fd_difference": "mean FD of placebo = 0.074",
    "scrubbed_volume_percentages": "mean percentage of volumes scrubbed for placebo and LSD was 0.4",
    "distance_related_motion_qc": "distance to FD-RSFC correlation was very close to zero",
}

PUBLISHED_QC_ROWS: list[dict[str, Any]] = [
    {
        "measure": "subjects_excluded_for_excessive_head_motion",
        "value": 4,
        "unit": "subjects",
        "interpretation": "The original dataset excluded high-motion subjects before group BOLD analyses.",
    },
    {
        "measure": "retained_bold_subject_count",
        "value": 15,
        "unit": "subjects",
        "interpretation": "The local empirical anchor uses the retained BOLD-analysis sample.",
    },
    {
        "measure": "initial_scrubbing_exclusion_threshold",
        "value": 15.0,
        "unit": "percent_scrubbed_volumes_at_fd_0_5_mm",
        "interpretation": "Subjects above this threshold were excluded in the original analysis.",
    },
    {
        "measure": "post_exclusion_scrubbing_fd_threshold",
        "value": 0.4,
        "unit": "mm_fd",
        "interpretation": "The retained analysis used a stricter scrubbing threshold after high-motion exclusions.",
    },
    {
        "measure": "retained_placebo_mean_fd",
        "value": 0.074,
        "sd": 0.032,
        "unit": "mm_fd",
        "interpretation": "Published retained-sample placebo mean FD.",
    },
    {
        "measure": "retained_lsd_mean_fd",
        "value": 0.12,
        "sd": 0.05,
        "unit": "mm_fd",
        "interpretation": "Published retained-sample LSD mean FD.",
    },
    {
        "measure": "retained_between_condition_mean_fd_difference",
        "value": 0.046,
        "sd": 0.032,
        "p": 0.0002,
        "unit": "mm_fd",
        "interpretation": "Published retained-sample LSD/placebo motion difference; this remains a serious confound risk.",
    },
    {
        "measure": "placebo_scrubbed_volume_percent",
        "value": 0.4,
        "sd": 0.8,
        "unit": "percent_volumes",
        "interpretation": "Published retained-sample placebo scrubbing burden.",
    },
    {
        "measure": "lsd_scrubbed_volume_percent",
        "value": 1.7,
        "sd": 2.3,
        "unit": "percent_volumes",
        "interpretation": "Published retained-sample LSD scrubbing burden.",
    },
    {
        "measure": "maximum_scrubbed_volume_percent_per_scan",
        "value": 7.1,
        "unit": "percent_volumes",
        "interpretation": "Published maximum retained-scan scrubbing burden.",
    },
    {
        "measure": "distance_fd_rsfc_correlation_lsd",
        "r": -0.0009,
        "p": 0.089,
        "unit": "correlation",
        "interpretation": "Published distance-dependent motion QC was approximately null for LSD.",
    },
    {
        "measure": "distance_fd_rsfc_correlation_placebo",
        "r": -0.025,
        "p_less_than": 0.001,
        "unit": "correlation",
        "interpretation": "Published placebo distance-dependent motion QC was small but statistically nonzero.",
    },
]


def _rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def build_published_motion_qc_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    readme_path = repo_root / "data" / "ds003059" / "README"
    readme = _read_text(readme_path)
    snippet_checks = {key: snippet in readme for key, snippet in SOURCE_SNIPPETS.items()}
    ready = bool(readme and all(snippet_checks.values()))
    missing = [key for key, present in snippet_checks.items() if not present]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": "implemented_published_ds003059_motion_qc_context" if ready else "blocked_missing_published_motion_qc_source",
        "published_motion_qc_ready": ready,
        "source_path": _rel(readme_path, repo_root),
        "source_basis": "Local ds003059 README motion/preprocessing notes from the OpenNeuro derivative dataset.",
        "source_snippet_checks": snippet_checks,
        "missing_source_snippets": missing,
        "published_qc_rows": PUBLISHED_QC_ROWS if ready else [],
        "high_risk_motion_context": {
            "retained_lsd_fd_exceeds_placebo": ready,
            "condition_fd_difference_p": 0.0002 if ready else None,
            "original_analysis_excluded_high_motion_subjects": ready,
            "strict_subject_level_fd_gate_complete": False,
        },
        "claim_status": (
            "published_fd_context_available_not_subject_level_confound_control"
            if ready
            else "not_proven_motion_qc_context_missing"
        ),
        "limitations": [
            "This is published aggregate QC context, not subject/run confound data.",
            "It cannot join framewise displacement, DVARS, or censoring burden to each empirical dynamic delta.",
            "It strengthens the motion defense slide but does not complete the strict motion/confound gate.",
        ],
        "next_action": (
            "Add subject/session/run confound TSV/CSV files with FD, DVARS, and censoring columns, then rerun "
            "scripts/build_motion_confound_controls.py."
        ),
        "claim_guardrail": (
            "Use this as motion-context evidence only. Do not claim motion confounds are controlled until the "
            "dedicated subject-level FD/DVARS/censoring gate passes."
        ),
    }


def _markdown(status: dict[str, Any]) -> str:
    lines = [
        "# Published ds003059 Motion QC Context",
        "",
        status["claim_guardrail"],
        "",
        f"- Status: `{status['analysis_status']}`",
        f"- Claim status: `{status['claim_status']}`",
        f"- Source: `{status['source_path']}`",
        "",
    ]
    if status["published_qc_rows"]:
        lines.extend(["## Published QC facts", "", "| Measure | Value | Unit | Interpretation |", "| --- | ---: | --- | --- |"])
        for row in status["published_qc_rows"]:
            value = row.get("value", row.get("r", ""))
            extra = ""
            if row.get("sd") is not None:
                extra += f" +/- {row['sd']}"
            if row.get("p") is not None:
                extra += f"; p={row['p']}"
            if row.get("p_less_than") is not None:
                extra += f"; p<{row['p_less_than']}"
            lines.append(
                "| {measure} | {value}{extra} | {unit} | {interpretation} |".format(
                    measure=row["measure"],
                    value=value,
                    extra=extra,
                    unit=row.get("unit", ""),
                    interpretation=str(row.get("interpretation", "")).replace("|", "/"),
                )
            )
    else:
        lines.extend(
            [
                "## Blocker",
                "",
                "The local ds003059 README did not contain all expected motion QC snippets.",
                "",
                f"- Missing snippets: `{', '.join(status['missing_source_snippets'])}`",
            ]
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in status["limitations"])
    lines.extend(["", "## Next action", "", status["next_action"], ""])
    return "\n".join(lines)


def write_published_motion_qc_status(repo_root: Path = REPO_ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "confound_controls"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_published_motion_qc_status(repo_root)
    status_path = output_dir / "published_motion_qc_status.json"
    report_path = output_dir / "published_motion_qc_status.md"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    status["status_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    return status
