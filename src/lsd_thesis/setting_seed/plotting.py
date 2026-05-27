from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_placeholder_plot_manifest(output_dir: str | Path, *, reason: str) -> Path:
    """Record why PASS 2A did not create heavy interactive plots."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "plot_manifest.csv"
    pd.DataFrame([{"artifact": "none", "status": "not_generated", "reason": reason}]).to_csv(manifest, index=False)
    return manifest

