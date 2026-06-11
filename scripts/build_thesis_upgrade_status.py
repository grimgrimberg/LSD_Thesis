from __future__ import annotations

import argparse
import json
from pathlib import Path

from lsd_thesis.confound_controls import write_motion_confound_control_status
from lsd_thesis.fmriprep_motion_proof import write_fmriprep_motion_proof_plan
from lsd_thesis.setting_seed.motion import write_motion_outputs
from lsd_thesis.thesis_upgrade import REPO_ROOT, write_thesis_upgrade_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the thesis-readiness status artifact.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--fetch-motion-remote", action="store_true", help="Query public motion-source metadata first.")
    parser.add_argument(
        "--motion-root",
        action="append",
        dest="motion_roots",
        help="Additional authorized fMRIPrep/confounds root. Can be supplied more than once.",
    )
    args = parser.parse_args()
    motion_roots = [Path(item) for item in args.motion_roots] if args.motion_roots else None
    if args.fetch_motion_remote or motion_roots:
        write_fmriprep_motion_proof_plan(args.repo_root, roots=motion_roots, fetch_remote=args.fetch_motion_remote)
        write_motion_outputs(repo_root=args.repo_root, roots=motion_roots)
        write_motion_confound_control_status(args.repo_root)
    payload = write_thesis_upgrade_status(args.repo_root, output_dir=args.output_dir)
    print(
        json.dumps(
            {
                "thesis_status": payload.get("readiness_summary", {}).get("thesis_status"),
                "strict_complete_gates": payload.get("readiness_summary", {}).get("strict_complete_gates"),
                "strict_total_gates": payload.get("readiness_summary", {}).get("strict_total_gates"),
                "source_path": payload.get("source_path"),
                "report_path": payload.get("report_path"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
