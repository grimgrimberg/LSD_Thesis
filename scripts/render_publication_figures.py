from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# ruff: noqa: E402
from lsd_thesis.publication import build_publication_evidence
from lsd_thesis.publication_figures import generate_publication_figures


def render_publication_figures(
    repo_root: Path = REPO_ROOT,
    *,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    figure_dir = output_dir or repo_root / "results" / "publication_figures"
    evidence = build_publication_evidence(repo_root)
    figure_bundle = generate_publication_figures(evidence, figure_dir)
    return {figure_id: figure.path for figure_id, figure in figure_bundle.items()}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Render publication figures from cached pipeline outputs.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Render all currently implemented publication figures.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for rendered figure files. Defaults to results/publication_figures.",
    )
    args = parser.parse_args(argv)
    if not args.all:
        parser.error("pass --all to render the current publication figure bundle")

    outputs = render_publication_figures(REPO_ROOT, output_dir=args.output_dir)
    for figure_id, path in outputs.items():
        print(f"{figure_id}: {path}")


if __name__ == "__main__":
    main()
