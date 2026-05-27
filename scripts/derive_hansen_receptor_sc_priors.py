from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lsd_thesis.hansen_priors import derive_hansen_macro_priors  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Derive macro-module 5-HT2A PET and structural-connectome priors from public Hansen Schaefer-100 assets."
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--cache-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--no-fetch", action="store_true", help="Require source files to already exist in the cache.")
    args = parser.parse_args()

    manifest = derive_hansen_macro_priors(
        repo_root=args.repo_root,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        fetch_missing=not args.no_fetch,
    )
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
