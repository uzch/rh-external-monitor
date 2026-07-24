#!/usr/bin/env python3
"""merge_signals — inject collected Backstory MCP insights into a sales-data-pull blob.

Fills the blob's reserved `peopleai_signals` key with records shaped per the
engagement-dashboard contract ({account_name, peopleai_id, engaged_people, account_status},
additive keys allowed), recomputes summary.pai_accounts_with_data, and optionally re-renders
the offline HTML dashboard.

Stdlib only.

Usage:
    python3 merge_signals.py "<Seller> — Sales Data.json" signals.json
        [--template template.html] [--out DIR]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("blob", help="JSON blob produced by sales-data-pull")
    ap.add_argument("signals", help="JSON array of peopleai_signals records")
    ap.add_argument("--template", help="engagement-dashboard template.html to re-render")
    ap.add_argument("--out", help="Output directory (default: alongside the blob)")
    args = ap.parse_args()

    data = json.load(open(args.blob))
    signals = json.load(open(args.signals))
    if not isinstance(signals, list):
        sys.exit("signals.json must be a JSON array of {account_name, peopleai_id, engaged_people, account_status} records")
    missing = [i for i, s in enumerate(signals) if "account_name" not in s]
    if missing:
        sys.exit(f"signals records missing 'account_name' at indices {missing}")

    data["peopleai_signals"] = signals
    data.setdefault("summary", {})["pai_accounts_with_data"] = sum(
        1 for s in signals if s.get("engaged_people") or s.get("account_status"))
    data.setdefault("_meta", {}).setdefault("caveats", []).append(
        f"peopleai_signals filled by sales-insights on {dt.date.today().isoformat()}: "
        f"{len(signals)} account(s) analyzed via the user's Backstory MCP session — "
        "AI-generated narratives, windows as labeled per record.")

    out_dir = args.out or os.path.dirname(os.path.abspath(args.blob))
    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, os.path.basename(args.blob))
    json.dump(data, open(out_json, "w"), indent=1, ensure_ascii=False)
    print(f"Wrote {out_json}  (peopleai_signals: {len(signals)} records)")

    if args.template:
        s = data["summary"]
        tpl = open(args.template).read()
        # "</" must stay escaped inside the inline <script> data block ("<\/" is identical per JSON).
        html = (tpl.replace("__DATA_JSON__", json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"))
                   .replace("__OWNER_NAME__", s.get("owner", ""))
                   .replace("__OWNER_TITLE__", s.get("owner_title", ""))
                   .replace("__OWNER_ID__", str(s.get("owner_id", "")))
                   .replace("__OWNER_EMAIL__", s.get("owner_email", ""))
                   .replace("__EMAIL_COUNT__", str(s.get("emails_count", 0)))
                   .replace("__EMAIL_WITH_BODY__", str(s.get("emails_with_body", 0)))
                   .replace("__EMAIL_MESSAGE_COUNT__", str(s.get("email_messages_count", 0)))
                   .replace("__MEETING_COUNT__", str(s.get("meetings_count", 0)))
                   .replace("__TASK_COUNT__", "0")
                   .replace("__EM_NOTE__", "Not available via Query API")
                   .replace("__TASK_NOTE__", "Not available via Query API")
                   .replace("__BUILD_DATE__", dt.datetime.now().strftime("%Y-%m-%d %H:%M")))
        owner = re.sub(r"[/\\:]", " ", s.get("owner", "seller"))
        out_html = os.path.join(out_dir, f"{owner} — Engagement 360.html")
        open(out_html, "w").write(html)
        print(f"Wrote {out_html}")


if __name__ == "__main__":
    main()
