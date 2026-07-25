#!/usr/bin/env python
"""Validate an External Monitor portfolio JSON against the bundled schema."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("Install jsonschema: python -m pip install jsonschema")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("portfolio")
    parser.add_argument("--schema", default=str(Path(__file__).resolve().parents[1] / "schemas" / "portfolio-output.schema.json"))
    args = parser.parse_args()

    portfolio = json.loads(Path(args.portfolio).read_text(encoding="utf-8"))
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(portfolio), key=lambda e: list(e.path))
    if errors:
        for error in errors:
            location = ".".join(str(x) for x in error.path) or "<root>"
            print(f"{location}: {error.message}")
        sys.exit(1)
    print("Portfolio JSON is valid.")


if __name__ == "__main__":
    main()
