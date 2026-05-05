from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# ruff: noqa: E402
from lsd_thesis.docx_export import markdown_to_docx


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/generate_report_docx.py <source.md> <output.docx>")
    source_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    markdown_to_docx(source_path, output_path)
    print(output_path)


if __name__ == "__main__":
    main()
