#!/usr/bin/env python
"""Merge Backstory MCP enrichment data into a base portfolio.

Reads portfolio-base.json (from build_portfolio.py) and an
mcp-enrichment.json file containing pre-synthesized structured
enrichment per account, merges them, updates envelope metadata,
and writes the enriched portfolio.

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys


def load_json(path):
    """Load a JSON file with UTF-8 encoding."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def merge_account(account, enrichment, signal_counter):
    """Merge enrichment data into a single account record.

    Returns the updated signal_counter.
    """
    status = enrichment.get("status", {})
    account["internal"]["risks"] = status.get("risks", [])
    account["internal"]["next_steps"] = status.get("next_steps", [])
    account["internal"]["topics"] = status.get("topics", [])

    if "raw_status" in enrichment:
        account["internal"]["account_status"] = enrichment["raw_status"]
    if "raw_activity" in enrichment:
        account["internal"]["recent_activity"] = enrichment["raw_activity"]

    if "summary" in enrichment:
        account["summary"] = enrichment["summary"]
    if "recommended_next_move" in enrichment:
        account["recommended_next_move"] = enrichment["recommended_next_move"]

    for sig in enrichment.get("signals", []):
        signal_counter += 1
        sig["signal_id"] = f"sig-{signal_counter:03d}"
        sig.setdefault("source_url", None)
        sig.setdefault("published_at", None)
        sig.setdefault("source_type", "backstory_mcp")
        account["signals"].append(sig)

    return signal_counter


def update_envelope(portfolio, enriched_count):
    """Update portfolio envelope metadata after enrichment."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    portfolio["run"]["generated_at"] = now
    if "-base" in portfolio["run"].get("run_id", ""):
        portfolio["run"]["run_id"] = portfolio["run"]["run_id"].replace(
            "-base", "-enriched"
        )

    matched_count = sum(
        1 for a in portfolio["accounts"]
        if a.get("identity", {}).get("match_status") == "matched"
    )
    if enriched_count >= matched_count and matched_count > 0:
        portfolio["run"]["status"] = "completed"
    else:
        portfolio["run"]["status"] = "partial"

    keep = 0
    watch = 0
    highest = None
    for acct in portfolio["accounts"]:
        for s in acct.get("signals", []):
            disp = s.get("disposition")
            score = s.get("score", 0)
            if disp == "KEEP":
                keep += 1
            elif disp == "WATCH":
                watch += 1
            if highest is None or score > highest:
                highest = score

    portfolio["summary"]["accounts_enriched"] = enriched_count
    portfolio["summary"]["keep_count"] = keep
    portfolio["summary"]["watch_count"] = watch
    portfolio["summary"]["highest_signal_score"] = highest

    portfolio["_meta"]["accounts_enriched"] = enriched_count
    portfolio["_meta"]["mcp_status"] = "connected" if enriched_count > 0 else "unavailable"

    base_caveats = [c for c in portfolio["_meta"].get("caveats", [])
                    if "Backstory MCP" not in c]
    if enriched_count > 0:
        base_caveats.insert(0,
            "Backstory MCP status and activity data covers the last 30 days."
        )
    portfolio["_meta"]["caveats"] = base_caveats


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--portfolio", required=True,
        help="Path to portfolio-base.json from build_portfolio.py",
    )
    parser.add_argument(
        "--mcp-data", required=True,
        help="Path to mcp-enrichment.json with synthesized MCP data",
    )
    parser.add_argument(
        "--out",
        help="Output path for enriched portfolio (default: stdout)",
    )
    args = parser.parse_args()

    portfolio = load_json(args.portfolio)
    mcp_data = load_json(args.mcp_data)

    print(
        f"Loaded portfolio with {len(portfolio.get('accounts', []))} accounts "
        f"and MCP data for {len(mcp_data)} accounts",
        file=sys.stderr,
    )

    signal_counter = 0
    enriched_count = 0

    for acct in portfolio.get("accounts", []):
        pid = acct.get("identity", {}).get("peopleai_account_id")
        if pid is None:
            continue

        key = str(pid)
        if key not in mcp_data:
            continue

        signal_counter = merge_account(acct, mcp_data[key], signal_counter)
        enriched_count += 1
        print(
            f"  Enriched: {acct['account_name']} "
            f"({len(acct['signals'])} signals)",
            file=sys.stderr,
        )

    for acct in portfolio.get("accounts", []):
        scores = [s.get("score", 0) for s in acct.get("signals", [])]
        if scores:
            acct["signal_score"] = round(sum(scores) / len(scores))
        else:
            acct["signal_score"] = None

    update_envelope(portfolio, enriched_count)

    print(
        f"Enriched {enriched_count} accounts, "
        f"{signal_counter} signals total",
        file=sys.stderr,
    )

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(portfolio, f, indent=2, ensure_ascii=False)
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        json.dump(portfolio, sys.stdout, indent=2, ensure_ascii=False)
        print(file=sys.stdout)


if __name__ == "__main__":
    main()
