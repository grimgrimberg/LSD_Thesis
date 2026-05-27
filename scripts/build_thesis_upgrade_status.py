from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lsd_thesis.thesis_upgrade import write_thesis_upgrade_status  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build thesis upgrade readiness-gate artifacts.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "results" / "thesis_upgrade")
    args = parser.parse_args()
    status = write_thesis_upgrade_status(args.repo_root, args.output_dir)
    print(json.dumps({"source_path": status["source_path"], "report_path": status["report_path"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
