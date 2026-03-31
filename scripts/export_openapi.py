#!/usr/bin/env python3
"""Export the FastAPI OpenAPI specification to a JSON file.

Usage:
    python scripts/export_openapi.py              # writes to docs/openapi.json
    python scripts/export_openapi.py -o api.json   # writes to custom path
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))


def main():
    parser = argparse.ArgumentParser(description="Export OpenAPI spec from FastAPI app")
    parser.add_argument(
        "-o",
        "--output",
        default="docs/openapi.json",
        help="Output file path (default: docs/openapi.json)",
    )
    args = parser.parse_args()

    from app.main import app

    spec = app.openapi()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(f"OpenAPI spec written to {output} ({len(json.dumps(spec))} bytes)")


if __name__ == "__main__":
    main()
