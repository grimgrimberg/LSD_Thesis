from __future__ import annotations

from typing import Any

import numpy as np


def _to_plain_python(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_plain_python(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain_python(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.integer):
        return int(value)
    return value
