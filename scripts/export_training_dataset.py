from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"


def main() -> None:
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))

    from lsd_thesis.training import build_window_dataset

    parser = argparse.ArgumentParser(description="Export Stage 2 module time series as a windowed training dataset.")
    parser.add_argument("--stage2-dir", default=str(REPO_ROOT / "results" / "stage_2"))
    parser.add_argument("--output", default=str(REPO_ROOT / "results" / "training" / "ds003059_windows.npz"))
    parser.add_argument("--window-length", type=int, default=64)
    parser.add_argument("--stride", type=int, default=16)
    args = parser.parse_args()

    dataset = build_window_dataset(
        stage_2_dir=args.stage2_dir,
        window_length=args.window_length,
        stride=args.stride,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, **dataset)
    print(output_path)
    print(dataset["windows"].shape[0])


if __name__ == "__main__":
    main()
