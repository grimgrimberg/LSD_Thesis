from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.setting_seed.reliability import write_reliability_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Set / Setting / Seed reliability-gated target table.")
    parser.add_argument("--stage-2-dir", default="results/stage_2", help="Cached Stage 2 artifact directory.")
    parser.add_argument("--output-dir", default="results/setting_seed/reliability", help="Output directory for reliability artifacts.")
    parser.add_argument("--seed", type=int, default=20260512, help="Deterministic bootstrap seed.")
    args = parser.parse_args()

    table = write_reliability_outputs(stage_2_dir=Path(args.stage_2_dir), output_dir=Path(args.output_dir), seed=args.seed)
    tier_counts: dict[str, int] = {}
    for row in table:
        tier_counts[str(row["tier"])] = tier_counts.get(str(row["tier"]), 0) + 1
    print(f"wrote {args.output_dir}/reliability_table.json")
    print(f"metrics={len(table)} tiers={tier_counts}")


if __name__ == "__main__":
    main()

