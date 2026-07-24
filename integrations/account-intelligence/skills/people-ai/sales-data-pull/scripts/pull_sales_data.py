#!/usr/bin/env python3
"""sales-data-pull — seller-centric 360 from the Backstory (formerly People.ai) Query API.

Resolves a seller by (fuzzy) name or email, runs four validated Query API
packets (user metrics, accounts owned, activities <= 365d, opportunities
closing this + next quarter), and emits a data blob in the engagement-dashboard
schema so the existing template.html renders it directly.

Stdlib only. Credentials: PEOPLEAI_CLIENT_ID / PEOPLEAI_CLIENT_SECRET env vars,
or a peopleai-key.local.json / peopleai-key.json file next to this script:
    {"client_id": "...", "client_secret": "..."}
Verify a freshly wired-in key with --check-key (auth-only, then exit).

Usage:
    python3 pull_sales_data.py "<seller name or email>"
        [--window-days 120] [--out DIR] [--template template.html]
        [--include-future-meetings] [--base https://api.people.ai]
    python3 pull_sales_data.py --check-key
"""
import argparse
import csv
import datetime as dt
import difflib
import http.client
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PACKETS = os.path.join(HERE, "packets")
MAX_WINDOW_DAYS = 365          # hard cap
ACCOUNT_CHUNK = 100            # account names per activities request ($in size kept modest)
UTC = dt.timezone.utc


# ---------- API plumbing ----------

def load_credentials():
    cid, sec = os.environ.get("PEOPLEAI_CLIENT_ID"), os.environ.get("PEOPLEAI_CLIENT_SECRET")
    if cid and sec:
        return cid, sec
    for name in ("peopleai-key.local.json", "peopleai-key.json"):
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            k = json.load(open(path))
            return k["client_id"], k["client_secret"]
    sys.exit('No credentials. Create peopleai-key.local.json next to this script containing '
             '{"client_id": "...", "client_secret": "..."} (Query API key pair from your Backstory '
             'admin), or set PEOPLEAI_CLIENT_ID/PEOPLEAI_CLIENT_SECRET. Check with --check-key.')


class Api:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.calls = 0
        cid, sec = load_credentials()
        body = (f"grant_type=client_credentials&client_id={urllib.parse.quote(cid)}"
                f"&client_secret={urllib.parse.quote(sec)}").encode()
        req = urllib.request.Request(self.base + "/v3/auth/tokens", data=body,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            self.token = json.load(urllib.request.urlopen(req, timeout=60))["access_token"]
        except urllib.error.HTTPError as e:
            sys.exit(f"Auth failed (HTTP {e.code}) — check the API key. Server said: {e.read()[:200].decode(errors='replace')}")
        self.calls += 1

    def export(self, payload, timeout=600):
        req = urllib.request.Request(self.base + "/v3/beta/insights/export",
                                     data=json.dumps(payload).encode(),
                                     headers={"Authorization": "Bearer " + self.token,
                                              "Content-Type": "application/json"})
        self.calls += 1
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                try:
                    return resp.read().decode()
                except http.client.IncompleteRead as e:
                    # Server sometimes omits the terminating chunk on small responses;
                    # the payload itself is complete — use what arrived.
                    return e.partial.decode()
        except urllib.error.HTTPError as e:
            msg = e.read()[:400].decode(errors="replace")
            if e.code == 429 or "rate" in msg.lower():
                sys.exit(f"Rate-limited (HTTP {e.code}). Observed capacity is ~100 req/hr/client, but a "
                         f"tenant key can carry a lower administrative cap (your Backstory admin can raise it). "
                         f"A run makes ~5 calls + 1 per 100 owned accounts; wait or ask the admin.\n{msg}")
            sys.exit(f"Export failed (HTTP {e.code}): {msg}")


def norm_key(k):
    return re.sub(r"\s+", " ", (k or "")).strip()


def parse_csv(text):
    rows = []
    for row in csv.DictReader(io.StringIO(text)):
        rows.append({norm_key(k): (v or "").strip() for k, v in row.items()})
    return rows


def check_columns(name, rows, expected):
    """The export SILENTLY drops slugs/variations the tenant doesn't recognize.
    Compare returned header count to the validated expectation and warn loudly."""
    got = len(rows[0]) if rows else None
    if rows and got < expected:
        print(f"  ⚠ {name}: {got} columns returned, {expected} validated — some fields were "
              f"silently dropped in this tenant. Re-validate with scripts/verify-packet.sh.", file=sys.stderr)


def packet(name, subs=None):
    p = json.load(open(os.path.join(PACKETS, name)))
    if not subs:
        return p

    def walk(node):
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            out = []
            for v in node:
                w = walk(v)
                out.extend(w) if isinstance(w, list) and isinstance(v, str) else out.append(w)
            return out
        if isinstance(node, str) and node in subs:
            return subs[node]
        return node
    return walk(p)


# ---------- date helpers ----------

def parse_when(v):
    """Activity/close dates arrive as ISO ('2026-06-30 14:00:00+00:00'); tolerate epoch digits."""
    if not v:
        return None
    if re.fullmatch(r"\d{12,14}", v):
        return dt.datetime.fromtimestamp(int(v) / 1000, UTC)
    if re.fullmatch(r"\d{9,11}", v):
        return dt.datetime.fromtimestamp(int(v), UTC)
    try:
        return dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None


def quarter_bounds(today):
    qm = 3 * ((today.month - 1) // 3) + 1
    q0 = dt.datetime(today.year, qm, 1, tzinfo=UTC)
    y, m = (today.year + 1, qm - 6) if qm > 6 else (today.year, qm + 6)
    return q0, dt.datetime(y, m, 1, tzinfo=UTC)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("seller", nargs="?", help="Seller name (fuzzy ok) or email")
    ap.add_argument("--window-days", type=int, default=120,
                    help="Activity lookback, default 120 (4 months), max 365")
    ap.add_argument("--out", default=".", help="Output directory")
    ap.add_argument("--template", help="Alternate dashboard template.html (default: the bundled one; 'none' skips HTML)")
    ap.add_argument("--include-future-meetings", action="store_true",
                    help="Keep calendar meetings scheduled after today (default: trimmed)")
    ap.add_argument("--base", default="https://api.people.ai")
    ap.add_argument("--check-key", action="store_true",
                    help="Only verify the API key authenticates, then exit (key-setup check)")
    args = ap.parse_args()

    if args.check_key:
        Api(args.base)
        print(f"✓ API key works — authenticated against {args.base}")
        return
    if not args.seller:
        ap.error("seller is required (or use --check-key)")

    window = min(args.window_days, MAX_WINDOW_DAYS)
    if args.window_days > MAX_WINDOW_DAYS:
        print(f"  ⚠ window capped at {MAX_WINDOW_DAYS} days.", file=sys.stderr)
    now = dt.datetime.now(UTC)
    window_start = now - dt.timedelta(days=window)

    api = Api(args.base)

    # 1. Roster + fuzzy resolution -------------------------------------------------
    roster = parse_csv(api.export(packet("roster.json")))
    check_columns("roster", roster, 7)
    want = args.seller.strip().lower()
    by_email = [u for u in roster if u.get("Email", "").lower() == want]
    exact = [u for u in roster if u.get("User (name)", "").lower() == want]
    hits = by_email or exact
    if not hits:
        names = {u.get("User (name)", ""): u for u in roster if u.get("User (name)")}
        close = difflib.get_close_matches(args.seller.strip(), list(names), n=5, cutoff=0.55)
        sub = [n for n in names if want in n.lower()]
        cand = list(dict.fromkeys(close + sub))
        if len(cand) == 1:
            hits = [names[cand[0]]]
        elif cand:
            print(f"Ambiguous seller '{args.seller}'. Candidates:", file=sys.stderr)
            for n in cand:
                print(f"  - {n} <{names[n].get('Email','')}>", file=sys.stderr)
            sys.exit(2)
        else:
            sys.exit(f"No user matching '{args.seller}' in the tenant roster ({len(roster)} users).")
    seller = hits[0]
    s_name, s_email = seller.get("User (name)", ""), seller.get("Email", "")
    s_id = seller.get("User (id)") or seller.get("User Identification")
    print(f"Seller resolved: {s_name} <{s_email}> (id {s_id})")

    # 2. User metrics ---------------------------------------------------------------
    metrics_rows = parse_csv(api.export(packet("user-metrics.json", {"{{seller_email}}": s_email})))
    check_columns("user-metrics", metrics_rows, 23)
    metrics = metrics_rows[0] if metrics_rows else {}
    if not metrics_rows:
        print("  ⚠ user-metrics: no metric row for this seller — user metrics are computed for a "
              "subset of the roster. The user-metrics section will be empty.",
              file=sys.stderr)

    # 3. Accounts owned -------------------------------------------------------------
    acct_rows = parse_csv(api.export(packet("accounts-owned.json", {"{{owner_id_int}}": int(s_id)})))
    check_columns("accounts-owned", acct_rows, 17)
    if not acct_rows:
        sys.exit(f"{s_name} owns no accounts in Backstory — this skill targets sellers/AMs who own accounts.")
    owned_names = [a["Account Name"] for a in acct_rows if a.get("Account Name")]
    print(f"Accounts owned: {len(acct_rows)}")

    # 4. Activities on owned accounts (server-side name filter + window) ------------
    activities = []
    ms = int(window_start.timestamp() * 1000)
    for i in range(0, len(owned_names), ACCOUNT_CHUNK):
        chunk = owned_names[i:i + ACCOUNT_CHUNK]
        pl = packet("activities.json")
        pl["filter"]["$and"][0]["clause"]["$in"] = chunk
        pl["filter"]["$and"][1]["clause"]["$gte"] = ms
        rows = parse_csv(api.export(pl))
        check_columns(f"activities[{i}:{i+len(chunk)}]", rows, 10)
        activities.extend(rows)
    print(f"Activities in window ({window}d): {len(activities)}")

    # 5. Opportunities closing this + next quarter ----------------------------------
    q0, q2 = quarter_bounds(now)
    opp_rows = parse_csv(api.export(packet("opportunities.json", {
        "{{q_start_epoch_ms_int}}": int(q0.timestamp() * 1000),
        "{{q_plus2_start_epoch_ms_int}}": int(q2.timestamp() * 1000)})))
    check_columns("opportunities", opp_rows, 11)
    # Owner filters are IGNORED server-side on this object (validated 2026-07-02) — filter here.
    owned_set = {n.lower() for n in owned_names}
    opps = []
    for o in opp_rows:
        mine = o.get("Opportunity Owner (id)") == str(s_id) or o.get("Opportunity Owner (name)", "").lower() == s_name.lower()
        on_owned = o.get("Account Name", "").lower() in owned_set
        if mine or on_owned:
            close = parse_when(o.get("Close Date"))
            opps.append({
                "name": o.get("Opportunity Name"), "account": o.get("Account Name"),
                "amount": o.get("Amount (amount)"), "currency": o.get("Amount (currency_iso_code)"),
                "amount_converted": o.get("Amount (Converted)"),
                "close_date": close.date().isoformat() if close else o.get("Close Date"),
                "stage": o.get("Stage"), "engagement_level": o.get("Opportunity Engagement Level"),
                "owner": o.get("Opportunity Owner (name)"), "owner_id": o.get("Opportunity Owner (id)"),
                "id": o.get("People.ai Internal ID"),
                "relation": "owned_by_seller" if mine and not on_owned else
                            "on_owned_account" if on_owned and not mine else "both"})
    print(f"Opportunities (this+next quarter, seller-linked): {len(opps)} of {len(opp_rows)} in range")

    # 6. Build the dashboard blob ----------------------------------------------------
    events, emails = [], []
    per_acct = {}
    d30 = now - dt.timedelta(days=30)
    for a in activities:
        when = parse_when(a.get("Activity date"))
        typ = (a.get("Activity Type") or "").lower()
        is_meeting = "meeting" in typ or "call" in typ
        is_email = "email" in typ
        if is_meeting and when and when > now and not args.include_future_meetings:
            continue
        acct = a.get("Account Name", "")
        st = per_acct.setdefault(acct, {"meetings": 0, "in_emails": 0, "out_emails": 0,
                                        "other": 0, "latest": None, "m30": 0, "e30": 0})
        outb = a.get("Outbound") == "True"
        date_s = when.date().isoformat() if when else ""
        if when and (st["latest"] is None or date_s > st["latest"]):
            st["latest"] = date_s
        rec = {"id": a.get("Activity"), "date": date_s,
               "datetime": when.isoformat() if when else "",
               "account": acct, "subject": a.get("Subject", ""),
               "who": a.get("Activity Originator") or a.get("Email of Sender") or "",
               "external": a.get("External") == "True",
               "opportunity": a.get("Opportunity Name") or None}
        if is_meeting:
            st["meetings"] += 1
            if when and when >= d30:
                st["m30"] += 1
            events.append({**rec, "kind": "meeting", "duration": None, "what": "",
                           "description": "", "next_steps": [], "is_recurring": False})
        elif is_email:
            st["out_emails" if outb else "in_emails"] += 1
            if when and when >= d30:
                st["e30"] += 1
            emails.append({**rec, "kind": "email",
                           "direction": "Outbound" if outb else "Inbound",
                           "owner": a.get("Activity Originator", ""),
                           "body": "", "body_truncated": False})
        else:
            st["other"] += 1

    def num(v, cast=int):
        try:
            return cast(float(v))
        except (TypeError, ValueError):
            return None

    owned_accounts = []
    for a in acct_rows:
        lm = parse_when(a.get("Last Meeting Date"))
        owned_accounts.append({
            "id": a.get("People.ai Internal ID"), "name": a.get("Account Name"),
            "industry": None, "region": None, "country": None, "created": None,
            # API-canonical per-account columns (People.ai display labels preserved in comments)
            "domain": a.get("Domain") or None,
            "type": a.get("Account Type") or None,
            "engagement_level": a.get("Account Engagement Level") or None,
            "last_meeting_date": lm.date().isoformat() if lm else None,
            "open_opportunities": num(a.get("# of Open Opportunities (Any Time)")),
            "open_opp_amount_this_quarter": num(a.get("Sum of Open Opportunities Closing (This Quarter)"), float),
            "api_meetings_30d": num(a.get("Meetings (Last 30 Days)")),
            "api_meetings_90d": num(a.get("Meetings (Last 90 Days)")),
            "api_emails_sent_30d": num(a.get("Emails Sent (Last 30 Days)")),
            "pct_emails_inbound_90d": num(a.get("% of Emails that are Inbound"), float),
            "time_spent_90d": a.get("Total Time Spent (Last 90 Days)") or None,
            "exec_activities_30d": num(a.get("Activities with Executives (C-Level) (Last 30 Days)")),
            "upcoming_meetings_14d": num(a.get("Upcoming Meetings (Next 14 Days)")),
        })
    acct_api = {a["name"]: a for a in owned_accounts}
    account_rollup = []
    for a in acct_rows:
        n = a.get("Account Name", "")
        st = per_acct.get(n, {"meetings": 0, "in_emails": 0, "out_emails": 0, "latest": None,
                              "m30": 0, "e30": 0, "other": 0})
        acct_cols = acct_api.get(n, {})
        account_rollup.append({
            "name": n, "meetings": st["meetings"], "in_emails": st["in_emails"],
            "out_emails": st["out_emails"],
            "total": st["meetings"] + st["in_emails"] + st["out_emails"] + st["other"],
            "latest": st["latest"], "is_owned": True,
            "pai_meetings_30d": st["m30"], "pai_emails_30d": st["e30"],
            "engagement_level": acct_cols.get("engagement_level"),
            "exec_activities_30d": acct_cols.get("exec_activities_30d"),
            "upcoming_meetings_14d": acct_cols.get("upcoming_meetings_14d"),
            "open_opportunities": acct_cols.get("open_opportunities"),
            "open_opp_amount_this_quarter": acct_cols.get("open_opp_amount_this_quarter"),
            "api_meetings_30d": acct_cols.get("api_meetings_30d"),
            "api_meetings_90d": acct_cols.get("api_meetings_90d"),
            "last_meeting_date": acct_cols.get("last_meeting_date")})

    inbound = sum(1 for e in emails if e["direction"] == "Inbound")
    data = {
        "summary": {
            "owner": s_name, "owner_email": s_email,
            "owner_title": metrics.get("Permission") or seller.get("Permission") or "",
            "owner_id": str(s_id),
            "owned_accounts_count": len(acct_rows), "meetings_count": len(events),
            "emails_count": len(emails), "emails_inbound": inbound,
            "emails_outbound": len(emails) - inbound, "emails_with_body": 0,
            "email_messages_count": 0, "manual_tasks_count": 0, "auto_tasks_count": 0,
            "accounts_with_engagement": sum(1 for r in account_rollup if r["total"]),
            "owned_accounts_engaged": sum(1 for r in account_rollup if r["total"]),
            "upcoming_meetings_14d": num(metrics.get("Upcoming Meetings (Next 14 Days)")),
            "transcripts_count": 0, "pai_accounts_with_data": 0},
        "owned_accounts": owned_accounts,
        "account_rollup": account_rollup,
        "events": sorted(events, key=lambda e: e["date"], reverse=True),
        "emails": sorted(emails, key=lambda e: e["date"], reverse=True),
        "email_messages": [],
        "eliot_owned_tasks": [],
        "peopleai_signals": [],
        "opportunities": sorted(opps, key=lambda o: o["close_date"] or ""),
        "user_metrics": {k: v for k, v in metrics.items()},
        "_meta": {
            "generated_at": now.isoformat(),
            "source": "Backstory (formerly People.ai) Query API — /v3/beta/insights/export at api.people.ai",
            "window_days": window, "api_calls": api.calls,
            "quarters": [q0.date().isoformat(), q2.date().isoformat()],
            "caveats": [
                f"Activity window: last {window} days (max 365). Future-scheduled meetings "
                + ("included." if args.include_future_meetings else "excluded (rerun with --include-future-meetings to keep them)."),
                "Two meeting semantics, both real: user_metrics 'External Meetings' = this seller's own "
                "matched meetings (the headline engagement KPI); events/meetings_count = all meetings on "
                "owned accounts, any participant (book coverage). Labeled accordingly — do not compare "
                "one against a reference built on the other.",
                "Email/meeting bodies are never exposed by the Query API — Backstory permanently deletes "
                "body content shortly after ingestion (15-day product default, shorter where the tenant "
                "tightens it) and keeps only metadata; raw content lives in the CRM.",
                "Upcoming Meetings = future-dated matched meetings already on the calendar, next 14 days. "
                "Seller KPI = meetings involving the seller; per-account column = any participant.",
                "industry/region/country/created on accounts are not in the Query API surface — blank by design.",
                "peopleai_signals (risks/next steps) are filled by the companion insights skill (MCP), not this pull.",
            ]},
    }

    os.makedirs(args.out, exist_ok=True)
    safe = re.sub(r"[/\\:]", " ", s_name)
    out_json = os.path.join(args.out, f"{safe} — Sales Data.json")
    json.dump(data, open(out_json, "w"), indent=1, ensure_ascii=False)
    print(f"Wrote {out_json}  ({api.calls} API calls)")

    tpl_path = None if args.template == "none" else (args.template or os.path.join(HERE, "template.html"))
    if tpl_path and os.path.exists(tpl_path):
        tpl = open(tpl_path).read()
        # "</" must not appear raw inside the inline <script> data block ("</script>" in a
        # subject line would truncate the document); "<\/" is the same string per JSON.
        html = (tpl.replace("__DATA_JSON__", json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"))
                   .replace("__OWNER_NAME__", s_name).replace("__OWNER_TITLE__", data["summary"]["owner_title"])
                   .replace("__OWNER_ID__", str(s_id)).replace("__OWNER_EMAIL__", s_email)
                   .replace("__EMAIL_COUNT__", str(len(emails))).replace("__EMAIL_WITH_BODY__", "0")
                   .replace("__EMAIL_MESSAGE_COUNT__", "0").replace("__MEETING_COUNT__", str(len(events)))
                   .replace("__TASK_COUNT__", "0")
                   .replace("__EM_NOTE__", "Not available via Query API")
                   .replace("__TASK_NOTE__", "Not available via Query API")
                   .replace("__BUILD_DATE__", now.strftime("%Y-%m-%d %H:%M")))
        out_html = os.path.join(args.out, f"{safe} — Engagement 360.html")
        open(out_html, "w").write(html)
        print(f"Wrote {out_html}")


if __name__ == "__main__":
    main()
