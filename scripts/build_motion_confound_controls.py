from __future__ import annotations

import argparse
import json
from pathlib import Path

from lsd_thesis.confound_controls import REPO_ROOT, write_motion_confound_control_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the motion/confound control status artifact.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    payload = write_motion_confound_control_status(args.repo_root, output_dir=args.output_dir)
    print(
        json.dumps(
            {
                "analysis_status": payload.get("analysis_status"),
                "motion_confound_control_ready": payload.get("motion_confound_control_ready"),
                "source_path": payload.get("source_path"),
                "report_path": payload.get("report_path"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
