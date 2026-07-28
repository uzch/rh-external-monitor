#!/usr/bin/env python
"""Merge external research signals into a portfolio.

Reads a base or enriched portfolio and one or more research batch JSON
files (produced by external research subagents), merges them, recomputes
signal_score per account, updates envelope metadata, and writes the
final portfolio.

This script exists so that signal merging logic (integer rounding,
correct envelope field names, disposition counting) lives in one
tested place rather than being reinvented inline by the orchestrator.

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import sys


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def merge_signals(portfolio, research_batches):
    """Merge external research signals into portfolio accounts.

    Returns (accounts_with_signals, total_signals_added).
    """
    acct_map = {a["account_name"]: a for a in portfolio["accounts"]}
    signal_counter = 0
    accounts_touched = set()

    for batch in research_batches:
        for entry in batch:
            name = entry["account_name"]
            signals = entry.get("signals", [])
            if name not in acct_map:
                print(f"  WARNING: {name} not in portfolio, skipping", file=sys.stderr)
                continue
            acct = acct_map[name]
            pid = acct.get("identity", {}).get("peopleai_account_id")
            for sig in signals:
                signal_counter += 1
                pid_slug = pid if pid else name.replace(" ", "-").lower()
                sig["signal_id"] = f"ext-{pid_slug}-{signal_counter:03d}"
                sig.setdefault("source_type", "external_public")
                sig.setdefault("source_url", None)
                sig.setdefault("published_at", None)
                acct["signals"].append(sig)
            if signals:
                accounts_touched.add(name)

    return len(accounts_touched), signal_counter


def recompute_scores(portfolio):
    """Recompute signal_score per account as integer average."""
    for acct in portfolio["accounts"]:
        scores = [s.get("score") for s in acct.get("signals", []) if s.get("score") is not None]
        if scores:
            acct["signal_score"] = round(sum(scores) / len(scores))
        else:
            acct["signal_score"] = None


def update_envelope(portfolio, accounts_with_signals, total_signals):
    """Update portfolio envelope after external signal merge."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    portfolio["run"]["generated_at"] = now

    if "-base" in portfolio["run"].get("run_id", ""):
        portfolio["run"]["run_id"] = portfolio["run"]["run_id"].replace("-base", "-enriched")

    if portfolio["run"].get("status") != "partial":
        portfolio["run"]["status"] = "completed"

    act = 0
    watch = 0
    highest = None
    for acct in portfolio["accounts"]:
        for s in acct.get("signals", []):
            disp = s.get("disposition")
            score = s.get("score")
            if disp == "ACT":
                act += 1
            elif disp == "WATCH":
                watch += 1
            if score is not None and (highest is None or score > highest):
                highest = score

    portfolio["summary"]["act_count"] = act
    portfolio["summary"]["watch_count"] = watch
    portfolio["summary"]["highest_signal_score"] = highest
    portfolio["summary"]["total_signals"] = total_signals
    existing_enriched = portfolio["summary"].get("accounts_enriched", 0)
    portfolio["summary"]["accounts_enriched"] = max(existing_enriched, accounts_with_signals)
    portfolio["summary"]["accounts_with_signals"] = accounts_with_signals

    if "_meta" not in portfolio:
        portfolio["_meta"] = {}

    mcp_status = portfolio["_meta"].get("mcp_status")
    if mcp_status in (None, "not_requested"):
        portfolio["_meta"]["mcp_status"] = "unavailable"
    portfolio["_meta"]["external_research"] = True

    caveats = portfolio["_meta"].get("caveats", [])
    caveats = [c for c in caveats if "external research" not in c.lower()]
    caveats.append(
        f"External research performed on all {len(portfolio['accounts'])} accounts."
    )
    if portfolio["_meta"].get("mcp_status") == "unavailable":
        if not any("MCP enrichment skipped" in c for c in caveats):
            caveats.append(
                "MCP enrichment skipped (unavailable). Internal context "
                "(risks, next_steps, topics) is empty for all accounts."
            )
    portfolio["_meta"]["caveats"] = caveats


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--portfolio", required=True,
        help="Path to portfolio JSON (base or enriched)",
    )
    parser.add_argument(
        "--research-dir",
        help="Directory containing research-batch-*.json files",
    )
    parser.add_argument(
        "--research-files", nargs="+",
        help="Explicit list of research batch JSON files",
    )
    parser.add_argument(
        "--out",
        help="Output path for final portfolio (default: stdout)",
    )
    args = parser.parse_args()

    if not args.research_dir and not args.research_files:
        parser.error("Provide --research-dir or --research-files")

    portfolio = load_json(args.portfolio)

    batch_files = []
    if args.research_dir:
        batch_files = sorted(glob.glob(os.path.join(args.research_dir, "research-batch-*.json")))
    if args.research_files:
        batch_files.extend(args.research_files)

    if not batch_files:
        print("No research batch files found", file=sys.stderr)
        sys.exit(1)

    batches = []
    for bf in batch_files:
        batches.append(load_json(bf))

    print(
        f"Loaded portfolio with {len(portfolio['accounts'])} accounts "
        f"and {len(batches)} research batches",
        file=sys.stderr,
    )

    accounts_with_signals, total_signals = merge_signals(portfolio, batches)
    recompute_scores(portfolio)
    update_envelope(portfolio, accounts_with_signals, total_signals)

    print(
        f"Merged {total_signals} signals across {accounts_with_signals} accounts",
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
