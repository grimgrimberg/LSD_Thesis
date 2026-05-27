from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def main() -> None:
    from lsd_thesis.cv5_validation import (
        refresh_cv5_aggregate_from_existing_outputs,
        run_cv5_validation,
    )

    parser = argparse.ArgumentParser(description="Run approved CV5 subject-disjoint validation.")
    parser.add_argument("--manifest", type=Path, required=True, help="Approved CV5 manifest JSON.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Fold-isolated output directory.")
    parser.add_argument("--fit-iterations", type=int, default=64, help="Stage 2/3 fitting iterations.")
    parser.add_argument("--seed", type=int, default=11, help="Stage 2/3 deterministic seed.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Refresh cv5_aggregate_validation.json from existing fold metadata without rerunning Stage 2/3.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_dir = repo_root / args.output_dir if not args.output_dir.is_absolute() else args.output_dir
    try:
        if args.aggregate_only:
            aggregate = refresh_cv5_aggregate_from_existing_outputs(
                manifest_path=args.manifest,
                output_dir=output_dir,
                repo_root=repo_root,
                fit_iterations=args.fit_iterations,
                seed=args.seed,
            )
        else:
            aggregate = run_cv5_validation(
                manifest_path=args.manifest,
                output_dir=output_dir,
                repo_root=repo_root,
                fit_iterations=args.fit_iterations,
                seed=args.seed,
            )
    except Exception as exc:
        print(f"CV5 validation failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(
        json.dumps(
            {
                "aggregate_path": str(output_dir / "cv5_aggregate_validation.json"),
                "completed_folds": aggregate["completed_folds"],
                "total_folds": aggregate["total_folds"],
                "held_out_validation_completed": aggregate["held_out_validation_completed"],
                "all_subjects_held_out_once": aggregate["all_subjects_held_out_once"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
