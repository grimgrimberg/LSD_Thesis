"""Set, Setting, and Seed extension utilities.

The package is intentionally additive: it reads cached Stage 2 artifacts and writes new
outputs under ``results/setting_seed`` without changing legacy Stage 1-5 semantics.
"""

from __future__ import annotations

DEFAULT_SEED = 20260512

