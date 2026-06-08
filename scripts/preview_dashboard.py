from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class PreviewReport(NamedTuple):
    local_url: str
    launch_command: tuple[str, ...]
    routes: tuple[str, ...]
    route_descriptions: tuple[tuple[str, str], ...]
    required_paths: tuple[str, ...]
    missing_required_paths: tuple[str, ...]
    optional_data_paths: tuple[str, ...]
    missing_optional_data_paths: tuple[str, ...]
    held_out_validation_status: str
    thesis_gate_contract_status: str
    thesis_gate_contract_violations: tuple[str, ...]


ROUTE_DESCRIPTIONS: tuple[tuple[str, str], ...] = (
    ("/", "overview dashboard page"),
    ("/ranking", "mechanism-ranking dashboard page"),
    ("/robustness", "robustness and strict-gate dashboard page"),
    ("/prior-art", "prior-art reproducibility inventory page"),
    ("/empirical", "paired subject/run empirical viewer page"),
    ("/simulator", "interactive surrogate simulator page"),
    ("/api/dashboard-data", "dashboard payload with simulation, evidence, provenance, and artifact links"),
    ("/api/prior-art-data", "prior-art repository and runbook payload"),
    ("/api/empirical-view", "paired subject/run empirical viewer payload"),
    ("/api/simulate", "interactive surrogate simulation endpoint"),
    ("/static", "dashboard stylesheet and JavaScript assets"),
    ("/assets/plotly.min.js", "local Plotly runtime used by the interactive dashboard"),
    ("/artifacts/{artifact_path:path}", "allowlisted generated artifact files with security headers"),
    ("/favicon.ico", "empty favicon response"),
)
REQUIRED_PATHS: tuple[str, ...] = (
    "src/lsd_thesis/templates/base.html",
    "src/lsd_thesis/templates/components/sidebar.html",
    "src/lsd_thesis/templates/pages/overview.html",
    "src/lsd_thesis/templates/pages/mechanism_ranking.html",
    "src/lsd_thesis/templates/pages/robustness.html",
    "src/lsd_thesis/templates/pages/prior_art.html",
    "src/lsd_thesis/templates/pages/empirical.html",
    "src/lsd_thesis/templates/pages/simulator.html",
    "src/lsd_thesis/static/dashboard.css",
    "src/lsd_thesis/static/dashboard.js",
    "configs/graphs/macro_modules.yaml",
    "configs/regimes/baseline.yaml",
    "configs/regimes/perturbed.yaml",
)
OPTIONAL_DATA_PATHS: tuple[str, ...] = (
    "results/stage_1/stage_1_summary.json",
    "results/stage_2/stage_2_summary.json",
    "results/stage_2/empirical_sober_targets.yaml",
    "results/stage_2/empirical_perturbation_targets.yaml",
    "results/stage_2/empirical_viewer/group_overview.json",
    "results/stage_2/empirical_viewer/subject_index.json",
    "results/stage_2b/target_reliability_summary.json",
    "results/stage_3/stage_3_summary.json",
    "results/stage_4/stage_4_summary.json",
    "results/stage_5/literature_weighted_fit_summary.json",
    "output/validation/cv5_subject_disjoint/results/cv5_aggregate_validation.json",
    "output/doc/defense_presentation.json",
)
EXPECTED_CURRENT_STRICT_MISSING_REQUIREMENT_IDS = ("motion_confound_control_result", "project_phase")
EXPECTED_CURRENT_PROJECT_STATUS = "research_demo_ready_not_completed_thesis"


def _available_dashboard_routes() -> set[str]:
    from lsd_thesis.web.app import app

    return {str(route.path) for route in app.routes}


def _missing_paths(repo_root: Path, relative_paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(path for path in relative_paths if not (repo_root / path).exists())


def _held_out_validation_status(repo_root: Path) -> str:
    cv5_aggregate_path = (
        repo_root
        / "output"
        / "validation"
        / "cv5_subject_disjoint"
        / "results"
        / "cv5_aggregate_validation.json"
    )
    if cv5_aggregate_path.exists():
        try:
            import json

            cv5 = json.loads(cv5_aggregate_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cv5 = {}
        if isinstance(cv5, dict) and cv5.get("held_out_validation_completed") is True:
            return (
                "completed CV5 internal validation "
                f"({cv5.get('completed_folds', 0)}/{cv5.get('total_folds', 0)} folds; not external validation)"
            )
        if isinstance(cv5, dict):
            return (
                "CV5 internal validation configured or partial "
                f"({cv5.get('completed_folds', 0)}/{cv5.get('total_folds', 0)} folds)"
            )
    summary_path = repo_root / "results" / "stage_2" / "stage_2_summary.json"
    stage3_summary_path = repo_root / "results" / "stage_3" / "stage_3_summary.json"
    if not summary_path.exists() and not stage3_summary_path.exists():
        return "not configured"
    stage3_boundary = None
    if stage3_summary_path.exists():
        try:
            import json

            stage3_summary = json.loads(stage3_summary_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            stage3_summary = {}
        stage3_boundary = stage3_summary.get("empirical_validation_boundary")
    if isinstance(stage3_boundary, dict) and (
        stage3_boundary.get("held_out_validation_completed") is True
        or stage3_boundary.get("held_out") is True
    ):
        return "completed"
    if not summary_path.exists():
        return "not configured"
    try:
        import json

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "not configured"
    boundary = summary.get("empirical_validation_boundary")
    if not isinstance(boundary, dict):
        return "not configured"
    if boundary.get("held_out_validation_completed") is True or boundary.get("held_out") is True:
        return "completed"
    if boundary.get("held_out_validation_configured") is True:
        approval_status = str(boundary.get("approval_status") or "candidate")
        if approval_status == "candidate":
            return "candidate split prepared but not approved or completed"
        if approval_status == "approved":
            return "approved split configured but not completed"
        return "configured but not completed"
    return "not configured"


def _read_json_object(path: Path) -> dict[str, object] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _thesis_gate_contract_violations(repo_root: Path) -> tuple[str, ...]:
    status_path = repo_root / "results" / "thesis_upgrade" / "thesis_upgrade_status.json"
    source_path = repo_root / "results" / "confound_controls" / "ds003059_motion_source_availability.json"
    status = _read_json_object(status_path)
    source = _read_json_object(source_path)
    if status is None:
        return (f"missing or invalid {status_path.relative_to(repo_root).as_posix()}",)

    violations: list[str] = []
    summary = status.get("readiness_summary") if isinstance(status.get("readiness_summary"), dict) else {}
    components = status.get("components") if isinstance(status.get("components"), dict) else {}
    motion = components.get("motion_confound") if isinstance(components.get("motion_confound"), dict) else {}
    archive = components.get("reproducible_archive") if isinstance(components.get("reproducible_archive"), dict) else {}
    motion_gate = motion.get("gate") if isinstance(motion.get("gate"), dict) else {}
    motion_requirement = motion.get("strict_requirement") if isinstance(motion.get("strict_requirement"), dict) else {}
    archive_gate = archive.get("gate") if isinstance(archive.get("gate"), dict) else {}

    missing_ids = tuple(str(item) for item in summary.get("strict_missing_requirement_ids", ()))
    if missing_ids != EXPECTED_CURRENT_STRICT_MISSING_REQUIREMENT_IDS:
        violations.append(
            "strict_missing_requirement_ids should remain "
            f"{EXPECTED_CURRENT_STRICT_MISSING_REQUIREMENT_IDS!r} until real motion proof changes the contract"
        )
    if summary.get("completion_status") != EXPECTED_CURRENT_PROJECT_STATUS:
        violations.append(f"completion_status should be {EXPECTED_CURRENT_PROJECT_STATUS}")
    if motion.get("fmriprep_motion_control_ready") is not False:
        violations.append("fmriprep_motion_control_ready must be false without FD/DVARS/censoring proof")
    if motion_requirement.get("complete") is not False:
        violations.append("motion strict requirement must fail closed")
    if motion_gate.get("ready") is not False:
        violations.append("motion gate.ready must not be true for proxy/image-QC-only evidence")
    if motion.get("motion_source_confounds_available") is not False:
        violations.append("motion_source_confounds_available must remain false without parsed subject/run confounds")
    if archive.get("archive_manifest_ready") is True and archive.get("archive_publication_ready") is not True:
        if archive_gate.get("ready") is not False:
            violations.append("archive gate.ready must not be true before a release URL and DOI are recorded")
    if source is None:
        violations.append(f"missing or invalid {source_path.relative_to(repo_root).as_posix()}")
    else:
        if source.get("source_confounds_available") is not False:
            violations.append("source_confounds_available must be false without parseable authorized confounds")
        raw_snapshot = source.get("openneuro_raw_snapshot") if isinstance(source.get("openneuro_raw_snapshot"), dict) else {}
        derivative = (
            source.get("public_derivative_repositories")
            if isinstance(source.get("public_derivative_repositories"), dict)
            else {}
        )
        if raw_snapshot.get("confound_files_verified") is not False:
            violations.append("OpenNeuro snapshot filename candidates must not be treated as verified confounds")
        if derivative.get("confound_files_verified") is not False:
            violations.append("reachable derivative repositories must not be treated as verified confounds")
    return tuple(violations)


def build_preview_report(
    repo_root: Path = REPO_ROOT,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> PreviewReport:
    available_routes = _available_dashboard_routes()
    route_descriptions = tuple(
        (route, description) for route, description in ROUTE_DESCRIPTIONS if route in available_routes
    )
    return PreviewReport(
        local_url=f"http://{host}:{port}/",
        launch_command=(
            "uv",
            "run",
            "uvicorn",
            "lsd_thesis.web.app:app",
            "--host",
            host,
            "--port",
            str(port),
        ),
        routes=tuple(route for route, _ in route_descriptions),
        route_descriptions=route_descriptions,
        required_paths=REQUIRED_PATHS,
        missing_required_paths=_missing_paths(repo_root, REQUIRED_PATHS),
        optional_data_paths=OPTIONAL_DATA_PATHS,
        missing_optional_data_paths=_missing_paths(repo_root, OPTIONAL_DATA_PATHS),
        held_out_validation_status=_held_out_validation_status(repo_root),
        thesis_gate_contract_status="passed" if not _thesis_gate_contract_violations(repo_root) else "failed",
        thesis_gate_contract_violations=_thesis_gate_contract_violations(repo_root),
    )


def format_preview_report(report: PreviewReport) -> str:
    required_state = "all present" if not report.missing_required_paths else ", ".join(report.missing_required_paths)
    optional_state = (
        "all present"
        if not report.missing_optional_data_paths
        else ", ".join(report.missing_optional_data_paths)
    )
    route_lines = "\n".join(f"- {route}: {description}" for route, description in report.route_descriptions)
    return "\n".join(
        [
            "Dashboard preview preflight",
            f"Launch command: {' '.join(report.launch_command)}",
            f"Local URL: {report.local_url}",
            "",
            "Important routes:",
            route_lines,
            "",
            f"Required app/config files: {required_state}",
            f"Optional generated data/artifacts: {optional_state}",
            f"Subject-disjoint held-out validation: {report.held_out_validation_status}",
            f"Thesis gate contract: {report.thesis_gate_contract_status}",
            *[f"- {violation}" for violation in report.thesis_gate_contract_violations],
            "",
            "Held-out empirical validation is not implied by this preview check.",
            "If optional artifacts are missing, the dashboard should render honest empty states.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview and preflight the FastAPI dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--check-only", action="store_true", help="Print routes and artifact state without starting a server.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if required dashboard files are missing.")
    args = parser.parse_args()

    report = build_preview_report(REPO_ROOT, host=args.host, port=args.port)
    print(format_preview_report(report))
    if args.strict and (report.missing_required_paths or report.thesis_gate_contract_violations):
        raise SystemExit(2)
    if args.check_only:
        return

    import uvicorn

    from lsd_thesis.web.app import app

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
