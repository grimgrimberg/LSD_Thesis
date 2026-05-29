from __future__ import annotations

import argparse
import json
from pathlib import Path

from lsd_thesis.motion_source_availability import REPO_ROOT, write_motion_source_availability


def main() -> None:
    parser = argparse.ArgumentParser(description="Check ds003059 subject-level motion/confound source availability.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--fetch-remote", action="store_true", help="Query OpenNeuro/GitHub public metadata.")
    args = parser.parse_args()
    payload = write_motion_source_availability(args.repo_root, fetch_remote=args.fetch_remote)
    print(json.dumps({"analysis_status": payload["analysis_status"], "source_path": payload["source_path"]}, indent=2))


if __name__ == "__main__":
    main()
