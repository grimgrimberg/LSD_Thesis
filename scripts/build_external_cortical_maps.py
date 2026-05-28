from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lsd_thesis.cortical_maps import write_cortical_map_alignment_status  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build module-level external receptor, myelin, functional-gradient, and transcriptomic map alignments."
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    payload = write_cortical_map_alignment_status(repo_root=args.repo_root, output_dir=args.output_dir)
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
