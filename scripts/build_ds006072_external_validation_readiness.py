from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lsd_thesis.ds006072_validation import build_ds006072_external_validation_readiness  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build ds006072 drug-order, CIFTI availability, and unchanged-scoring readiness artifacts."
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()

    payload = build_ds006072_external_validation_readiness(args.repo_root)
    print(json.dumps(payload, indent=2), flush=True)


if __name__ == "__main__":
    main()
