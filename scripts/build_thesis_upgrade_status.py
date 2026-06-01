from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.confound_controls import write_motion_confound_control_status
from lsd_thesis.fmriprep_motion_proof import write_fmriprep_motion_proof_plan
from lsd_thesis.setting_seed.motion import DEFAULT_FD_THRESHOLD, write_motion_outputs
from lsd_thesis.thesis_upgrade import REPO_ROOT, write_thesis_upgrade_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Build thesis upgrade status artifacts.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--fetch-motion-remote", action="store_true", help="Query OpenNeuro snapshot metadata for the fMRIPrep motion-proof preflight.")
    parser.add_argument(
        "--motion-root",
        action="append",
        dest="motion_roots",
        help="Additional/local root to search for authorized fMRIPrep confounds before refreshing the strict motion gate.",
    )
    parser.add_argument("--fd-threshold", type=float, default=DEFAULT_FD_THRESHOLD, help="Framewise-displacement threshold for motion spike summaries.")
    args = parser.parse_args()
    motion_roots = [Path(item) for item in args.motion_roots] if args.motion_roots else None
    if motion_roots:
        write_motion_outputs(
            repo_root=args.repo_root,
            roots=motion_roots,
            fd_threshold=args.fd_threshold,
        )
        write_motion_confound_control_status(args.repo_root)
    write_fmriprep_motion_proof_plan(
        args.repo_root,
        roots=motion_roots,
        fetch_remote=args.fetch_motion_remote,
    )
    status = write_thesis_upgrade_status(args.repo_root)
    source_path = status.get("source_path", "results/thesis_upgrade/thesis_upgrade_status.json")
    report_path = status.get("report_path", "results/thesis_upgrade/thesis_upgrade_status.md")
    print(f"Wrote {Path(source_path).as_posix()}")
    print(f"Wrote {Path(report_path).as_posix()}")


if __name__ == "__main__":
    main()
