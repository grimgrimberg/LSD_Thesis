from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.setting_seed.motion import DEFAULT_FD_THRESHOLD, write_motion_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build aggregate Set / Setting / Seed motion-summary artifacts from local confounds.")
    parser.add_argument("--stage-2-dir", default="results/stage_2", help="Cached Stage 2 artifact directory.")
    parser.add_argument("--output-dir", default="results/setting_seed/motion", help="Output directory for motion artifacts.")
    parser.add_argument("--fd-threshold", type=float, default=DEFAULT_FD_THRESHOLD, help="Framewise-displacement threshold for percent-above summary.")
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        help="Additional/local root to search for fMRIPrep confounds. Can be supplied more than once.",
    )
    args = parser.parse_args()

    summary = write_motion_outputs(
        stage_2_dir=Path(args.stage_2_dir),
        output_dir=Path(args.output_dir),
        roots=[Path(item) for item in args.roots] if args.roots else None,
        fd_threshold=args.fd_threshold,
    )
    print(f"wrote {args.output_dir}/motion_summary.json")
    print(f"status={summary['status']} parsed={summary['parsed_summary_count']} files_present={summary['motion_files_present']}")


if __name__ == "__main__":
    main()
