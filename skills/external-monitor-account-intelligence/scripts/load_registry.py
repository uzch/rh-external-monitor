#!/usr/bin/env python
"""Load and normalize the Enterprise Accounts registry.

Reads the CSV at data/local/Enterprise Accounts.csv and outputs a JSON array
of account records with the five canonical fields. Supports scope filtering
by geo, region, territory, or account name.

The registry establishes the account population and organizational assignment.
It is NOT an intelligence source -- it provides no activity, engagement, risks,
opportunities, next steps, or external signals.

Stdlib only.

Usage:
    python scripts/load_registry.py
    python scripts/load_registry.py --geo NAPS
    python scripts/load_registry.py --region CIVILIAN
    python scripts/load_registry.py --territory AEROSPACE_AND_DEFENSE_ENT_POD_TERR01
    python scripts/load_registry.py --account "EXAMPLE CORP"
    python scripts/load_registry.py --geo NAPS --out scoped-accounts.json
    python scripts/load_registry.py --list-geos
    python scripts/load_registry.py --list-regions
    python scripts/load_registry.py --list-territories --geo NAPS
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(HERE, "..", "..", "..", "data", "local", "Enterprise Accounts.csv")

FIELDS = [
    "account_sales_group_name",
    "geo",
    "region",
    "segment",
    "ACCOUNT_TERRITORY_NAME",
]

CANONICAL = {
    "account_sales_group_name": "account_name",
    "geo": "geo",
    "region": "region",
    "segment": "segment",
    "ACCOUNT_TERRITORY_NAME": "territory_name",
}


def load(csv_path):
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        missing = [c for c in FIELDS if c not in header]
        if missing:
            sys.exit(f"Registry CSV missing columns: {', '.join(missing)}\nFound: {', '.join(header)}")
        rows = []
        for row in reader:
            rows.append({CANONICAL[k]: (row.get(k) or "").strip() for k in FIELDS})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", default=DEFAULT_CSV, help="Path to the Enterprise Accounts CSV")
    ap.add_argument("--geo", help="Filter by geo (exact, case-insensitive)")
    ap.add_argument("--region", help="Filter by region (exact, case-insensitive)")
    ap.add_argument("--territory", help="Filter by territory_name (exact, case-insensitive)")
    ap.add_argument("--account", help="Filter by account_name (substring, case-insensitive)")
    ap.add_argument("--out", help="Write JSON to this file instead of stdout")
    ap.add_argument("--list-geos", action="store_true", help="List unique geos and exit")
    ap.add_argument("--list-regions", action="store_true", help="List unique regions and exit")
    ap.add_argument("--list-territories", action="store_true", help="List unique territories and exit")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        sys.exit(f"Registry CSV not found: {args.csv}\n"
                 "Place the Enterprise Accounts CSV at data/local/Enterprise Accounts.csv")

    accounts = load(args.csv)

    if args.list_geos:
        for g in sorted(set(a["geo"] for a in accounts)):
            count = sum(1 for a in accounts if a["geo"] == g)
            print(f"  {g} ({count} accounts)")
        return

    if args.list_regions:
        filtered = accounts
        if args.geo:
            filtered = [a for a in filtered if a["geo"].lower() == args.geo.lower()]
        for r in sorted(set(a["region"] for a in filtered)):
            count = sum(1 for a in filtered if a["region"] == r)
            print(f"  {r} ({count} accounts)")
        return

    if args.list_territories:
        filtered = accounts
        if args.geo:
            filtered = [a for a in filtered if a["geo"].lower() == args.geo.lower()]
        if args.region:
            filtered = [a for a in filtered if a["region"].lower() == args.region.lower()]
        for t in sorted(set(a["territory_name"] for a in filtered)):
            count = sum(1 for a in filtered if a["territory_name"] == t)
            print(f"  {t} ({count} accounts)")
        return

    if args.geo:
        accounts = [a for a in accounts if a["geo"].lower() == args.geo.lower()]
    if args.region:
        accounts = [a for a in accounts if a["region"].lower() == args.region.lower()]
    if args.territory:
        accounts = [a for a in accounts if a["territory_name"].lower() == args.territory.lower()]
    if args.account:
        q = args.account.lower()
        accounts = [a for a in accounts if q in a["account_name"].lower()]

    if not accounts:
        scope_parts = []
        if args.geo:
            scope_parts.append(f"geo={args.geo}")
        if args.region:
            scope_parts.append(f"region={args.region}")
        if args.territory:
            scope_parts.append(f"territory={args.territory}")
        if args.account:
            scope_parts.append(f"account={args.account}")
        sys.exit(f"No accounts match scope: {', '.join(scope_parts)}")

    print(f"Accounts: {len(accounts)}", file=sys.stderr)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=1, ensure_ascii=False)
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        json.dump(accounts, sys.stdout, indent=1, ensure_ascii=False)
        print(file=sys.stdout)


if __name__ == "__main__":
    main()
