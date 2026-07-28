#!/usr/bin/env python
"""Aggregate People.ai activity records into per-account metrics.

Queries the People.ai Query API via run_query.py using bounded activity-object
queries filtered by confirmed account names. Produces one metrics record per
registry account with explicit identity and metrics status fields.

Only accounts with identity_status="confirmed" are sent to the API. Ambiguous,
unmatched, and unresolved accounts appear in the output with null metrics and
a clear metrics_status explaining why.

Stdlib only.

Usage:
    python aggregate_activity_metrics.py --territory TERR_NAME --identities ids.json
    python aggregate_activity_metrics.py --registry-json accounts.json --identities ids.json
    python aggregate_activity_metrics.py --geo NAPS --identities ids.json --out metrics.json
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY_SCRIPT = os.path.join(HERE, "load_registry.py")
RUNNER_SCRIPT = os.path.join(
    HERE, "..", "..", "people-ai", "sales-data-explorer", "scripts", "run_query.py"
)

BATCH_SIZE = 50

ACTIVITY_COLUMNS = [
    {"slug": "ootb_activity_uid"},
    {"slug": "ootb_activity_account_name"},
    {"slug": "ootb_activity_type"},
    {"slug": "ootb_activity_timestamp"},
    {"slug": "ootb_activity_opportunity_name"},
    {"slug": "ootb_activity_external"},
    {"slug": "ootb_activity_outbound"},
]

UNAVAILABLE_FIELDS = [
    "engagement_level",
    "opportunity_amount",
    "opportunity_stage",
    "executive_activity",
    "account_owner",
]


def load_registry_accounts(args):
    if args.registry_json:
        with open(args.registry_json, encoding="utf-8") as f:
            return json.load(f)
    cmd = [sys.executable, REGISTRY_SCRIPT]
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
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    by_registry_name = {}
    for e in entries:
        by_registry_name[e["registry_account_name"]] = e
    return by_registry_name


def build_packet(confirmed_names, window_start_ms):
    return {
        "object": "activity",
        "columns": list(ACTIVITY_COLUMNS),
        "filter": {
            "$and": [
                {
                    "attribute": {"slug": "ootb_activity_account_name"},
                    "clause": {"$in": list(confirmed_names)},
                },
                {
                    "attribute": {"slug": "ootb_activity_timestamp"},
                    "clause": {"$gte": window_start_ms},
                },
            ]
        },
    }


_PERMANENT_ERRORS = ("Auth failed", "Rate-limited", "COLUMN DROP", "not in the validated catalog")
_MAX_RETRIES = 2
_RETRY_DELAY = 5


def run_query(packet, out_dir):
    fd, packet_path = tempfile.mkstemp(
        suffix=".json", prefix="activity-packet-", dir=out_dir
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(packet, f, indent=2, ensure_ascii=False)
        cmd = [
            sys.executable, RUNNER_SCRIPT, packet_path,
            "--title", "Activity Metrics",
            "--out", out_dir,
        ]
        print(f"Running: {' '.join(cmd)}", file=sys.stderr)

        last_err = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            except subprocess.TimeoutExpired:
                last_err = "subprocess timed out after 120s"
                if attempt < _MAX_RETRIES:
                    print(f"  Retry {attempt + 1}/{_MAX_RETRIES}: {last_err}", file=sys.stderr)
                    time.sleep(_RETRY_DELAY)
                continue

            if result.returncode == 0:
                csv_path = os.path.join(out_dir, "Activity Metrics.csv")
                if not os.path.exists(csv_path):
                    return None, f"Expected CSV not found at {csv_path}"
                return csv_path, result.stdout.strip()

            err = result.stderr.strip()
            if any(marker in err for marker in _PERMANENT_ERRORS):
                return None, err

            last_err = err
            if attempt < _MAX_RETRIES:
                print(f"  Retry {attempt + 1}/{_MAX_RETRIES}: {err[:120]}", file=sys.stderr)
                time.sleep(_RETRY_DELAY)

        return None, last_err or "unknown error after retries"
    finally:
        if os.path.exists(packet_path):
            os.remove(packet_path)


def parse_activities(csv_path):
    with open(csv_path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_timestamp(s):
    """Parse an API timestamp to a timezone-aware UTC datetime.

    Handles ISO 8601 with offset (+00:00), trailing Z, and naive timestamps
    (treated as UTC). Returns (datetime, None) on success or (None, warning)
    for unparseable values.
    """
    if not s or not s.strip():
        return None, None
    s = s.strip()
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(s)
    except ValueError:
        return None, f"malformed timestamp: {s!r}"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    else:
        parsed = parsed.astimezone(dt.timezone.utc)
    return parsed, None


def dedup_by_uid(rows):
    seen = set()
    unique = []
    for r in rows:
        uid = r.get("Activity", "")
        if uid and uid in seen:
            continue
        if uid:
            seen.add(uid)
        unique.append(r)
    return unique


def aggregate_account(rows, now):
    d30 = now - dt.timedelta(days=30)
    d60 = now - dt.timedelta(days=60)
    d90 = now - dt.timedelta(days=90)

    total = 0
    meeting_30 = 0
    meeting_90 = 0
    meeting_all = 0
    email_30 = 0
    email_90 = 0
    email_all = 0
    outbound = 0
    inbound = 0
    external = 0
    internal = 0
    activity_30d = 0
    activity_31_60d = 0
    latest_ts = None
    latest_type = None
    types = {}
    opportunities = set()
    ts_warnings = []

    for r in rows:
        ts, warn = parse_timestamp(r.get("Activity date"))
        if warn:
            ts_warnings.append(warn)
            continue
        if ts is None:
            continue
        if ts > now:
            continue

        total += 1
        typ = (r.get("Activity Type") or "unknown").lower()
        types[typ] = types.get(typ, 0) + 1

        is_meeting = "meeting" in typ or "call" in typ
        is_email = "email" in typ

        if latest_ts is None or ts > latest_ts:
            latest_ts = ts
            latest_type = typ

        if ts >= d30:
            activity_30d += 1
            if is_meeting:
                meeting_30 += 1
            if is_email:
                email_30 += 1
        if d60 <= ts < d30:
            activity_31_60d += 1
        if ts >= d90:
            if is_meeting:
                meeting_90 += 1
            if is_email:
                email_90 += 1
        if is_meeting:
            meeting_all += 1
        if is_email:
            email_all += 1

        if r.get("Outbound", "").lower() in ("true", "1"):
            outbound += 1
        else:
            inbound += 1
        if r.get("External", "").lower() in ("true", "1"):
            external += 1
        else:
            internal += 1

        opp = (r.get("Opportunity Name") or "").strip()
        if opp:
            opportunities.add(opp)

    if activity_30d > 0 or activity_31_60d > 0:
        if activity_30d > activity_31_60d:
            trend = "increasing"
        elif activity_30d < activity_31_60d:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = None

    if ts_warnings:
        for w in ts_warnings:
            print(f"  WARNING: {w}", file=sys.stderr)

    return {
        "total_activities": total,
        "meeting_count_30d": meeting_30,
        "meeting_count_90d": meeting_90,
        "meeting_count_all": meeting_all,
        "email_count_30d": email_30,
        "email_count_90d": email_90,
        "email_count_all": email_all,
        "outbound_count": outbound,
        "inbound_count": inbound,
        "external_count": external,
        "internal_count": internal,
        "most_recent_activity_date": latest_ts.strftime("%Y-%m-%d") if latest_ts else None,
        "most_recent_activity_type": latest_type,
        "activity_types": types,
        "linked_opportunity_names": sorted(opportunities),
        "activity_trend": trend,
        "timestamp_warnings": ts_warnings if ts_warnings else None,
    }


def make_confirmed_record(
    registry_name, query_name, identity, metrics, window_days, run_timestamp
):
    status = "available" if metrics["total_activities"] > 0 else "no_activity"
    return {
        "registry_account_name": registry_name,
        "query_account_name": query_name,
        "identity_status": identity.get("identity_status", "confirmed"),
        "identity_notes": identity.get("identity_notes"),
        "metrics_status": status,
        "source": "peopleai_query_activity",
        "query_window_days": window_days,
        "query_timestamp": run_timestamp,
        **metrics,
        "engagement_level": None,
        "opportunity_amount": None,
        "opportunity_stage": None,
        "executive_activity": None,
        "account_owner": None,
        "unavailable_fields": list(UNAVAILABLE_FIELDS),
    }


def make_unavailable_record(registry_name, identity):
    status = identity.get("identity_status", "unresolved")
    notes = identity.get("identity_notes")
    if status == "ambiguous":
        caveat = (
            "Identity not confirmed - metrics cannot be retrieved "
            "until People.ai identity is resolved"
        )
    elif status == "unresolved":
        caveat = "Identity not yet resolved against People.ai"
    elif status == "not_found":
        caveat = "Account not found in People.ai"
    else:
        caveat = f"Metrics unavailable due to identity status: {status}"

    return {
        "registry_account_name": registry_name,
        "query_account_name": identity.get("query_account_name"),
        "identity_status": status,
        "identity_notes": notes,
        "metrics_status": "unavailable_identity",
        "source": None,
        "query_window_days": None,
        "query_timestamp": None,
        "total_activities": None,
        "meeting_count_30d": None,
        "meeting_count_90d": None,
        "meeting_count_all": None,
        "email_count_30d": None,
        "email_count_90d": None,
        "email_count_all": None,
        "outbound_count": None,
        "inbound_count": None,
        "external_count": None,
        "internal_count": None,
        "most_recent_activity_date": None,
        "most_recent_activity_type": None,
        "activity_types": None,
        "linked_opportunity_names": None,
        "activity_trend": None,
        "engagement_level": None,
        "opportunity_amount": None,
        "opportunity_stage": None,
        "executive_activity": None,
        "account_owner": None,
        "unavailable_fields": [f"all fields unavailable due to {status} identity"],
        "caveats": [caveat],
    }


def make_query_failed_record(registry_name, query_name, identity, error_msg):
    return {
        "registry_account_name": registry_name,
        "query_account_name": query_name,
        "identity_status": identity.get("identity_status", "confirmed"),
        "identity_notes": identity.get("identity_notes"),
        "metrics_status": "query_failed",
        "source": None,
        "query_window_days": None,
        "query_timestamp": None,
        "total_activities": None,
        "meeting_count_30d": None,
        "meeting_count_90d": None,
        "meeting_count_all": None,
        "email_count_30d": None,
        "email_count_90d": None,
        "email_count_all": None,
        "outbound_count": None,
        "inbound_count": None,
        "external_count": None,
        "internal_count": None,
        "most_recent_activity_date": None,
        "most_recent_activity_type": None,
        "activity_types": None,
        "linked_opportunity_names": None,
        "activity_trend": None,
        "engagement_level": None,
        "opportunity_amount": None,
        "opportunity_stage": None,
        "executive_activity": None,
        "account_owner": None,
        "unavailable_fields": ["all fields unavailable due to query failure"],
        "caveats": [f"Query API call failed: {error_msg}"],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--territory", help="Territory name to scope from registry")
    ap.add_argument("--geo", help="GEO to scope from registry")
    ap.add_argument("--region", help="Region to scope from registry")
    ap.add_argument("--account", help="Account name substring to scope from registry")
    ap.add_argument("--registry-json", help="Pre-filtered registry JSON file")
    ap.add_argument("--identities", required=True, help="Identity map JSON file")
    ap.add_argument(
        "--lookback", type=int, default=120,
        help="Lookback window in days (default 120)",
    )
    ap.add_argument("--out", help="Output JSON file path")
    ap.add_argument(
        "--allow-uppercase", action="store_true",
        help="Skip the ALL CAPS query name check (not recommended)",
    )
    args = ap.parse_args()

    if not any([args.territory, args.geo, args.region, args.account, args.registry_json]):
        sys.exit(
            "Specify a scope: --territory, --geo, --region, --account, or --registry-json"
        )

    accounts = load_registry_accounts(args)
    if not accounts:
        sys.exit("No accounts found for the specified scope.")
    print(f"Registry accounts in scope: {len(accounts)}", file=sys.stderr)

    identity_map = load_identities(args.identities)

    now = dt.datetime.now(dt.timezone.utc)
    run_timestamp = now.isoformat()
    window_start = now - dt.timedelta(days=args.lookback)
    window_start_ms = int(window_start.timestamp() * 1000)

    QUERYABLE = ("confirmed", "resolved_alias")
    queryable = []
    for acct in accounts:
        name = acct["account_name"]
        identity = identity_map.get(name, {})
        if identity.get("identity_status") in QUERYABLE:
            qname = identity.get("query_account_name") or name
            queryable.append((name, qname, identity))

    print(
        f"Queryable identities: {len(queryable)} of {len(accounts)}",
        file=sys.stderr,
    )

    out_dir = (
        os.path.dirname(os.path.abspath(args.out))
        if args.out
        else os.path.join(os.getcwd(), "output")
    )
    os.makedirs(out_dir, exist_ok=True)

    query_names = [qn for _, qn, _ in queryable]

    unresolved_names = [
        (reg, qn) for reg, qn, _ in queryable
        if qn == reg and qn == qn.upper() and len(qn) > 3
    ]
    if unresolved_names and not args.allow_uppercase:
        print(
            f"ERROR: {len(unresolved_names)} of {len(query_names)} query name(s) "
            f"appear unresolved (query_account_name == registry name in ALL CAPS):",
            file=sys.stderr,
        )
        for reg, qn in unresolved_names[:5]:
            print(f"  - {qn!r}", file=sys.stderr)
        sys.exit(
            "People.ai Query API uses case-sensitive account name matching. "
            "ALL CAPS names (from the registry) will return zero results. "
            "Identity resolution must store the People.ai canonical name "
            "(the 'name' field from find_account) as query_account_name.\n"
            "Pass --allow-uppercase to override this check."
        )

    genuine_uppercase = [
        qn for reg, qn, _ in queryable
        if qn != reg and qn == qn.upper() and len(qn) > 3
    ]
    if genuine_uppercase:
        print(
            f"NOTE: {len(genuine_uppercase)} query name(s) are ALL CAPS but "
            f"differ from the registry name (People.ai stores them this way):",
            file=sys.stderr,
        )
        for n in genuine_uppercase[:5]:
            print(f"  - {n!r}", file=sys.stderr)

    rows_raw = []
    query_error = None
    failed_names = set()

    if query_names:
        total_batches = (len(query_names) + BATCH_SIZE - 1) // BATCH_SIZE
        print(
            f"Querying {len(query_names)} accounts in {total_batches} "
            f"batch(es) of up to {BATCH_SIZE}",
            file=sys.stderr,
        )

        for i in range(0, len(query_names), BATCH_SIZE):
            chunk = query_names[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            print(
                f"Batch {batch_num}/{total_batches}: {len(chunk)} accounts",
                file=sys.stderr,
            )

            packet = build_packet(chunk, window_start_ms)
            if batch_num == 1:
                packet_json = json.dumps(packet, indent=2)
                print(f"Packet:\n{packet_json}", file=sys.stderr)

            and_clauses = packet.get("filter", {}).get("$and", [])
            has_name_filter = any(
                c.get("attribute", {}).get("slug") == "ootb_activity_account_name"
                for c in and_clauses
            )
            has_ts_filter = any(
                c.get("attribute", {}).get("slug") == "ootb_activity_timestamp"
                for c in and_clauses
            )
            if not has_name_filter or not has_ts_filter:
                sys.exit(
                    f"Packet integrity check failed: "
                    f"name_filter={has_name_filter}, ts_filter={has_ts_filter}. "
                    f"Both are required."
                )

            csv_path, output = run_query(packet, out_dir)
            if csv_path is None:
                query_error = output
                failed_names.update(chunk)
                print(
                    f"  Batch {batch_num} failed: {output}", file=sys.stderr
                )
                continue

            batch_rows = parse_activities(csv_path)
            rows_raw.extend(batch_rows)
            print(
                f"  Batch {batch_num}: {len(batch_rows)} rows", file=sys.stderr
            )
    else:
        print("No queryable identities -- skipping Query API call.", file=sys.stderr)

    rows_deduped = dedup_by_uid(rows_raw)
    print(f"Rows returned: {len(rows_raw)}", file=sys.stderr)
    print(f"Rows after dedup: {len(rows_deduped)}", file=sys.stderr)

    rows_by_account = {}
    for r in rows_deduped:
        acct_name = r.get("Account Name", "")
        rows_by_account.setdefault(acct_name, []).append(r)

    results = []
    for acct in accounts:
        reg_name = acct["account_name"]
        identity = identity_map.get(reg_name, {
            "registry_account_name": reg_name,
            "query_account_name": None,
            "identity_status": "unresolved",
            "identity_notes": None,
        })
        id_status = identity.get("identity_status", "unresolved")

        if id_status not in QUERYABLE:
            results.append(make_unavailable_record(reg_name, identity))
            continue

        q_name = identity.get("query_account_name") or reg_name
        if q_name in failed_names:
            results.append(make_query_failed_record(
                reg_name,
                q_name,
                identity,
                query_error or "batch failed",
            ))
            continue

        acct_rows = rows_by_account.get(q_name, [])
        metrics = aggregate_account(acct_rows, now)
        results.append(make_confirmed_record(
            reg_name, q_name, identity, metrics, args.lookback, run_timestamp,
        ))

    envelope = {
        "generated_at": run_timestamp,
        "lookback_days": args.lookback,
        "window_start_epoch_ms": window_start_ms,
        "accounts_in_scope": len(accounts),
        "accounts_queryable": len(queryable),
        "accounts_queried": len(query_names),
        "rows_returned": len(rows_raw),
        "rows_after_dedup": len(rows_deduped),
        "query_error": query_error,
        "metrics": results,
    }

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        json.dump(envelope, sys.stdout, indent=2, ensure_ascii=False)
        print(file=sys.stdout)


if __name__ == "__main__":
    main()
