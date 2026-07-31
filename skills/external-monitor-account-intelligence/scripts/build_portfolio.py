#!/usr/bin/env python
"""Assemble a base portfolio.json from registry, identity, and activity data.

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

SCOPE_TYPES = ("geo", "region", "territory", "account")

MATCH_STATUS_MAP = {
    "confirmed": "matched",
    "resolved_alias": "matched",
    "ambiguous": "ambiguous",
    "not_found": "not_found",
}


def slugify(name):
    """Lowercase, replace & with 'and', collapse non-alphanumeric runs to '-'."""
    s = name.lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def load_registry_accounts(args):
    """Load registry accounts from a JSON file or by shelling out to load_registry.py."""
    if args.registry_json:
        with open(args.registry_json, encoding="utf-8") as f:
            return json.load(f)
    cmd = [sys.executable, os.path.join(HERE, "load_registry.py")]
    if args.territory:
        cmd += ["--territory", args.territory]
    if args.geo:
        cmd += ["--geo", args.geo]
    if args.region:
        cmd += ["--region", args.region]
    if args.account:
        cmd += ["--account", args.account]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"load_registry.py failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def load_identities(path):
    """Read identity JSON array and return dict keyed by registry_account_name."""
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    by_name = {}
    for e in entries:
        by_name[e["registry_account_name"]] = e
    return by_name


def load_metrics(path):
    """Read metrics JSON envelope and return dict keyed by registry_account_name."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if "metrics" not in data:
        sys.exit(f"Metrics file missing 'metrics' key: {path}")
    by_name = {}
    for m in data["metrics"]:
        opp_names = m.get("linked_opportunity_names")
        m["linked_opportunity_count"] = len(opp_names) if isinstance(opp_names, list) else 0
        by_name[m["registry_account_name"]] = m
    return by_name


def map_match_status(identity_status):
    """Map an identity_status string to a portfolio match_status value."""
    if identity_status is None:
        return "unresolved"
    return MATCH_STATUS_MAP.get(identity_status, "unresolved")


def compute_priority(metrics, max_activities):
    """Compute a priority score (0-100) and reasons list from account metrics.

    Returns (score, reasons).
    """
    status = metrics.get("metrics_status")
    if status != "available":
        return (0, [f"Metrics unavailable: {status}"])

    reasons = []

    # Volume component (0-25)
    total = metrics.get("total_activities", 0) or 0
    if max_activities > 0:
        volume = round(25 * total / max_activities)
    else:
        volume = 0
    volume = max(0, min(25, volume))
    reasons.append(f"volume={volume} (activities={total})")

    # Opportunities component (0-25)
    opp_count = metrics.get("linked_opportunity_count", 0) or 0
    if opp_count == 0:
        opps = 0
    elif opp_count == 1:
        opps = 10
    elif opp_count <= 5:
        opps = 15
    elif opp_count <= 20:
        opps = 20
    else:
        opps = 25
    reasons.append(f"opportunities={opps} (count={opp_count})")

    # Momentum component (0-25)
    trend = metrics.get("activity_trend")
    momentum_map = {"increasing": 25, "stable": 15, "declining": 10}
    momentum = momentum_map.get(trend, 0)
    reasons.append(f"momentum={momentum} (trend={trend})")

    # Recency component (0-25)
    recency = 0
    recent_date = metrics.get("most_recent_activity_date")
    if recent_date:
        try:
            d = datetime.date.fromisoformat(recent_date)
            days_ago = (datetime.date.today() - d).days
            if days_ago <= 7:
                recency = 25
            elif days_ago <= 14:
                recency = 20
            elif days_ago <= 30:
                recency = 15
            elif days_ago <= 60:
                recency = 10
            elif days_ago <= 90:
                recency = 5
            else:
                recency = 0
        except (ValueError, TypeError):
            recency = 0
    reasons.append(f"recency={recency} (date={recent_date})")

    # Caveat for unavailable fields
    unavailable = metrics.get("unavailable_fields")
    if unavailable:
        reasons.append(f"caveat: {len(unavailable)} field(s) unavailable")

    score = volume + opps + momentum + recency
    return (score, reasons)


def build_account(registry, identity, metrics, max_activities):
    """Build a single account record for the portfolio."""
    account_name = registry["account_name"]
    score, reasons = compute_priority(metrics, max_activities)

    return {
        "account_id": slugify(account_name),
        "account_name": account_name,
        "hierarchy": {
            "geo": registry.get("geo"),
            "region": registry.get("region"),
            "pod": None,
            "territory_name": registry.get("territory_name"),
            "segment": registry.get("segment"),
        },
        "identity": {
            "crm_id": None,
            "peopleai_account_id": identity.get("peopleai_account_id"),
            "match_status": map_match_status(identity.get("identity_status")),
            "query_account_name": identity.get("query_account_name"),
            "identity_status": identity.get("identity_status"),
            "identity_notes": identity.get("identity_notes"),
        },
        "signal_score": None,
        "internal_priority_score": score,
        "priority_reasons": reasons,
        "internal": {
            "metrics": metrics,
            "risks": [],
            "next_steps": [],
            "topics": [],
        },
        "summary": None,
        "recommended_next_move": None,
        "signals": [],
    }


def build_portfolio(accounts, scope_type, scope_value, lookback):
    """Build the complete portfolio envelope."""
    now = datetime.datetime.now(datetime.timezone.utc)
    run_id = f"{slugify(scope_value)}-{now.strftime('%Y%m%d')}-base"

    accounts_sorted = sorted(
        accounts, key=lambda a: a["internal_priority_score"], reverse=True
    )

    enriched_count = sum(
        1 for a in accounts_sorted
        if a.get("internal", {}).get("metrics", {}).get("metrics_status") == "available"
    )

    summary_text = (
        f"{scope_type.title()} {scope_value} contains {len(accounts_sorted)} accounts. "
        f"{enriched_count} have internal activity data across a {lookback}-day window."
    )

    # Compute caveat counts
    unavail_identity = sum(
        1 for a in accounts_sorted
        if a.get("internal", {}).get("metrics", {}).get("metrics_status")
        == "unavailable_identity"
    )
    query_failed = sum(
        1 for a in accounts_sorted
        if a.get("internal", {}).get("metrics", {}).get("metrics_status")
        == "query_failed"
    )
    no_activity = sum(
        1 for a in accounts_sorted
        if a.get("internal", {}).get("metrics", {}).get("metrics_status")
        == "no_activity"
    )

    caveats = [
        "This is a base portfolio with internal activity data only. "
        "External signals, MCP insights, and AI summaries have not been applied.",
        "Priority scores are computed from volume, opportunity count, momentum, "
        "and recency. They do not reflect deal quality, revenue, or strategic importance.",
    ]
    if unavail_identity > 0:
        caveats.append(
            f"{unavail_identity} account(s) have unavailable identity and no metrics."
        )
    if query_failed > 0:
        caveats.append(
            f"{query_failed} account(s) had query failures and no metrics."
        )
    if no_activity > 0:
        caveats.append(
            f"{no_activity} account(s) returned zero activities in the lookback window."
        )

    return {
        "run": {
            "run_id": run_id,
            "status": "partial",
            "generated_at": now.isoformat(),
        },
        "scope": {
            "type": scope_type,
            "value": scope_value,
        },
        "summary": {
            "account_count": len(accounts_sorted),
            "accounts_with_internal_data": enriched_count + no_activity,
            "text": summary_text,
            "accounts_enriched": 0,
            "act_count": 0,
            "watch_count": 0,
            "highest_signal_score": None,
        },
        "accounts": accounts_sorted,
        "_meta": {
            "query_window_days": lookback,
            "accounts_in_scope": len(accounts_sorted),
            "accounts_enriched": 0,
            "mcp_status": "not_requested",
            "caveats": caveats,
        },
    }


def infer_scope(args):
    """Infer scope_type and scope_value from CLI arguments."""
    if args.scope_type and args.scope_value:
        return args.scope_type, args.scope_value
    if args.territory:
        return "territory", args.territory
    if args.region:
        return "region", args.region
    if args.geo:
        return "geo", args.geo
    if args.account:
        return "account", args.account
    sys.exit(
        "Cannot infer scope. Provide --scope-type and --scope-value, "
        "or one of --territory, --region, --geo, --account."
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry-json", help="Pre-filtered registry JSON file")
    ap.add_argument("--territory", help="Territory name to scope from registry")
    ap.add_argument("--geo", help="GEO to scope from registry")
    ap.add_argument("--region", help="Region to scope from registry")
    ap.add_argument("--account", help="Account name substring to scope from registry")
    ap.add_argument("--metrics", required=True, help="Activity metrics JSON file")
    ap.add_argument("--identities", required=True, help="Identity map JSON file")
    ap.add_argument(
        "--scope-type", choices=SCOPE_TYPES,
        help="Scope type (geo, region, territory, account)",
    )
    ap.add_argument("--scope-value", help="Scope value matching --scope-type")
    ap.add_argument(
        "--lookback", type=int, default=120,
        help="Lookback window in days (default 120)",
    )
    ap.add_argument("--out", help="Output JSON file path (default: stdout)")
    args = ap.parse_args()

    scope_type, scope_value = infer_scope(args)

    registry_accounts = load_registry_accounts(args)
    if not registry_accounts:
        sys.exit("No accounts found for the specified scope.")
    print(f"Registry accounts in scope: {len(registry_accounts)}", file=sys.stderr)

    identity_map = load_identities(args.identities)
    metrics_map = load_metrics(args.metrics)

    # Compute max_activities across all available metrics
    max_activities = 0
    for m in metrics_map.values():
        if m.get("metrics_status") == "available":
            total = m.get("total_activities", 0) or 0
            if total > max_activities:
                max_activities = total

    # Build per-account records
    account_records = []
    for reg in registry_accounts:
        name = reg["account_name"]

        identity = identity_map.get(name, {
            "registry_account_name": name,
            "query_account_name": None,
            "identity_status": "unresolved",
            "identity_notes": None,
        })

        metrics = metrics_map.get(name, {
            "registry_account_name": name,
            "metrics_status": "not_in_metrics_run",
            "total_activities": None,
        })

        record = build_account(reg, identity, metrics, max_activities)
        account_records.append(record)

    portfolio = build_portfolio(account_records, scope_type, scope_value, args.lookback)

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
