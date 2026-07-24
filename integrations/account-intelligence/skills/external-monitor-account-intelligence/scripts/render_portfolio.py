#!/usr/bin/env python3
"""Render portfolio.json into the reusable External Monitor HTML template."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("portfolio")
    parser.add_argument("--template", default=str(Path(__file__).resolve().parents[1] / "templates" / "portfolio.html"))
    parser.add_argument("--out", default="external-monitor-portfolio.html")
    args = parser.parse_args()

    data = json.loads(Path(args.portfolio).read_text(encoding="utf-8"))
    template = Path(args.template).read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output = template.replace("__PORTFOLIO_JSON__", payload)
    Path(args.out).write_text(output, encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
