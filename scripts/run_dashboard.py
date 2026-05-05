from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


if __name__ == "__main__":
    from lsd_thesis.web.app import app

    uvicorn.run(app, host="127.0.0.1", port=8000)
