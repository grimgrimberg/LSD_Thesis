from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from lsd_thesis.data.parcellations import (
    available_parcellations,
    extract_schaefer_empirical_viewer,
)
from lsd_thesis.thesis_loop import build_thesis_evidence_loop

REPO_ROOT = Path(__file__).resolve().parents[1]


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _print_summary(summary: dict[str, Any]) -> None:
    print(
        "[parcellation] "
        f"{summary['parcellation_id']} {summary['analysis_status']}: "
        f"{summary['subject_count']} subjects, {summary['record_count']} runs, "
        f"top layer={summary.get('ranking_top_layer')}",
        flush=True,
    )
    print(f"[parcellation] viewer: {summary['viewer_root']}", flush=True)
    print(f"[parcellation] ranking: {summary['ranking_summary_path']}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract Schaefer/Yeo ds003059 parcellation sensitivity artifacts and refresh the thesis evidence loop."
    )
    parser.add_argument(
        "--parcellation",
        choices=[item for item in available_parcellations() if item.startswith("schaefer_")],
        default="schaefer_100_yeo_7",
        help="Schaefer/Yeo target to extract.",
    )
    parser.add_argument("--dataset-dir", default=str(REPO_ROOT / "data" / "ds003059"))
    parser.add_argument("--stage2-dir", default=str(REPO_ROOT / "results" / "stage_2"))
    parser.add_argument("--runs", nargs="+", default=None, choices=["run-01", "run-02", "run-03"])
    parser.add_argument("--include-music", action="store_true", help="Allow ds003059 run-02 music extraction.")
    parser.add_argument("--subjects", nargs="+", default=None, help="Optional explicit subject IDs such as sub-001 sub-002.")
    parser.add_argument("--max-subjects", type=_positive_int, default=None, help="Development/smoke limit; omit for all paired subjects.")
    parser.add_argument(
        "--nilearn-data-dir",
        default=str(REPO_ROOT / "results" / "nilearn_data"),
        help="Nilearn atlas cache directory. Defaults inside this repo so atlas downloads do not go to C:\\Users.",
    )
    parser.add_argument("--force", action="store_true", help="Re-extract even when a parcellation extraction summary already exists.")
    parser.add_argument(
        "--control-null-count",
        type=int,
        default=16,
        help="Receptor-prior permutation nulls for E. Lower than the 8-module default because Schaefer runs are larger.",
    )
    parser.add_argument("--skip-loop-refresh", action="store_true", help="Do not refresh results/thesis_evidence_loop after extraction.")
    args = parser.parse_args()
    os.environ["NILEARN_DATA"] = str(Path(args.nilearn_data_dir).resolve())

    summary = extract_schaefer_empirical_viewer(
        dataset_dir=args.dataset_dir,
        stage_2_dir=args.stage2_dir,
        parcellation_id=args.parcellation,
        runs=args.runs,
        include_music=args.include_music,
        subjects=args.subjects,
        max_subjects=args.max_subjects,
        nilearn_data_dir=args.nilearn_data_dir,
        force=args.force,
        control_null_count=args.control_null_count,
    )
    _print_summary(summary)

    if not args.skip_loop_refresh:
        loop = build_thesis_evidence_loop(REPO_ROOT)
        print("[parcellation] thesis loop refreshed:", loop["source_path"], flush=True)
        parcellation_row = next(
            row for row in loop["status_rows"] if row["label"] == "Schaefer/Yeo sensitivity"
        )
        print(json.dumps(parcellation_row, indent=2), flush=True)


if __name__ == "__main__":
    main()
