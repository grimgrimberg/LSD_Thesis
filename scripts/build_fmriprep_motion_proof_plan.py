from __future__ import annotations

import argparse
import json
from pathlib import Path

from lsd_thesis.fmriprep_motion_proof import REPO_ROOT, write_fmriprep_motion_proof_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the fMRIPrep motion-proof preflight artifact.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--fetch-remote", action="store_true", help="Query public metadata before writing the plan.")
    parser.add_argument(
        "--motion-root",
        "--root",
        action="append",
        dest="motion_roots",
        help="Additional authorized fMRIPrep/confounds root. Can be supplied more than once.",
    )
    args = parser.parse_args()
    payload = write_fmriprep_motion_proof_plan(
        args.repo_root,
        output_dir=args.output_dir,
        roots=[Path(item) for item in args.motion_roots] if args.motion_roots else None,
        fetch_remote=args.fetch_remote,
    )
    print(
        json.dumps(
            {
                "status": payload.get("status"),
                "fmriprep_motion_proof_ready": payload.get("fmriprep_motion_proof_ready"),
                "source_path": payload.get("source_path"),
                "report_path": payload.get("report_path"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
