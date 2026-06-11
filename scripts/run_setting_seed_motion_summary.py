from __future__ import annotations

import argparse
import json
from pathlib import Path

from lsd_thesis.setting_seed.motion import DEFAULT_FD_THRESHOLD, write_motion_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build setting/seed subject-run motion summaries.")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--stage-2-dir", type=Path, default=None)
    parser.add_argument("--fd-threshold", type=float, default=DEFAULT_FD_THRESHOLD)
    parser.add_argument(
        "--motion-root",
        "--root",
        action="append",
        dest="motion_roots",
        help="Additional authorized fMRIPrep/confounds root. Can be supplied more than once.",
    )
    args = parser.parse_args()
    payload = write_motion_outputs(
        output_dir=args.output_dir,
        repo_root=args.repo_root,
        stage_2_dir=args.stage_2_dir,
        roots=[Path(item) for item in args.motion_roots] if args.motion_roots else None,
        fd_threshold=args.fd_threshold,
    )
    print(
        json.dumps(
            {
                "status": payload.get("status"),
                "motion_analysis_ready": payload.get("motion_analysis_ready"),
                "motion_pairing_ready": payload.get("motion_pairing_ready"),
                "paired_subject_run_count": payload.get("paired_subject_run_count"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
