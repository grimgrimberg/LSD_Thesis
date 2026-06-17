# /// script
# dependencies = [
#   "numpy>=2.2.4",
#   "scikit-learn>=1.6.1",
# ]
# ///

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lsd_thesis.condition_models import load_window_dataset  # noqa: E402
from lsd_thesis.rocket_benchmark import evaluate_rocket_condition_model, write_rocket_outputs  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark LSD vs placebo classification with ROCKET-style random convolutional features "
            "under subject-disjoint folds and subject/session/run aggregation."
        )
    )
    parser.add_argument("--dataset", default=str(REPO_ROOT / "results" / "training" / "ds003059_windows.npz"))
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "results" / "training" / "rocket_condition_benchmark"))
    parser.add_argument("--n-kernels", type=int, default=128)
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=0,
        help=(
            "Optional post-hoc subject/run prediction label-permutation count. "
            "This is a diagnostic null, not a fold-refit permutation benchmark."
        ),
    )
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument(
        "--cv5-manifest",
        default=None,
        help=(
            "Optional approved CV5 manifest such as "
            "output/validation/cv5_subject_disjoint/approved/subject_split_cv5_manifest_approved.json. "
            "When omitted, LeaveOneGroupOut(subject) is used."
        ),
    )
    parser.add_argument(
        "--allow-candidate-cv5",
        action="store_true",
        help="Allow a candidate CV5 manifest for development runs. Do not use this for thesis evidence.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_dir = Path(args.output_dir)
    dataset = load_window_dataset(dataset_path)
    summary = evaluate_rocket_condition_model(
        dataset,
        n_kernels=args.n_kernels,
        random_state=args.seed,
        cv5_manifest_path=args.cv5_manifest,
        repo_root=REPO_ROOT,
        allow_candidate_cv5=args.allow_candidate_cv5,
        n_permutations=args.n_permutations,
    )
    summary["dataset_path"] = str(dataset_path)
    summary["output_dir"] = str(output_dir)
    write_rocket_outputs(summary, output_dir)

    print(
        json.dumps(
            {
                "model": summary["model"],
                "cv_strategy": summary["cv_strategy"],
                "primary_evaluation_unit": summary["primary_evaluation_unit"],
                "balanced_accuracy_mean": summary["aggregate"]["balanced_accuracy_mean"],
                "roc_auc_mean": summary["aggregate"]["roc_auc_mean"],
                "output_dir": str(output_dir),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
