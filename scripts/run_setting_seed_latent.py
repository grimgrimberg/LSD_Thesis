from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.setting_seed.latent import write_latent_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build descriptive Set / Setting / Seed latent rest geometry.")
    parser.add_argument("--stage-2-dir", default="results/stage_2", help="Cached Stage 2 artifact directory.")
    parser.add_argument("--output-dir", default="results/setting_seed/latent", help="Output directory for latent artifacts.")
    parser.add_argument("--seed", type=int, default=20260512, help="Deterministic PCA seed.")
    args = parser.parse_args()

    result = write_latent_outputs(stage_2_dir=Path(args.stage_2_dir), output_dir=Path(args.output_dir), seed=args.seed)
    print(f"wrote {args.output_dir}/latent_coordinates.csv")
    print(f"coordinate_rows={len(result.coordinates)} trajectory_rows={len(result.trajectory_metrics)} run_02_available={result.run_02_available}")


if __name__ == "__main__":
    main()

