from __future__ import annotations

import argparse
import json
from pathlib import Path

from lsd_thesis.fmriprep_motion_proof import REPO_ROOT, write_fmriprep_motion_proof_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the fMRIPrep motion-proof preflight artifact.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--fetch-remote", action="store_true", help="Query OpenNeuro snapshot metadata for ds003059 T1w/confound availability.")
    args = parser.parse_args()
    payload = write_fmriprep_motion_proof_plan(args.repo_root, fetch_remote=args.fetch_remote)
    print(
        json.dumps(
            {
                "analysis_status": payload["analysis_status"],
                "fmriprep_motion_proof_ready": payload["fmriprep_motion_proof_ready"],
                "fmriprep_preflight_ready": payload["fmriprep_preflight_ready"],
                "source_path": payload["source_path"],
                "report_path": payload["report_path"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
