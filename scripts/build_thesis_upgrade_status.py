from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.fmriprep_motion_proof import write_fmriprep_motion_proof_plan
from lsd_thesis.thesis_upgrade import REPO_ROOT, write_thesis_upgrade_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Build thesis upgrade status artifacts.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--fetch-motion-remote", action="store_true", help="Query OpenNeuro snapshot metadata for the fMRIPrep motion-proof preflight.")
    args = parser.parse_args()
    write_fmriprep_motion_proof_plan(args.repo_root, fetch_remote=args.fetch_motion_remote)
    status = write_thesis_upgrade_status(args.repo_root)
    source_path = status.get("source_path", "results/thesis_upgrade/thesis_upgrade_status.json")
    report_path = status.get("report_path", "results/thesis_upgrade/thesis_upgrade_status.md")
    print(f"Wrote {Path(source_path).as_posix()}")
    print(f"Wrote {Path(report_path).as_posix()}")


if __name__ == "__main__":
    main()
