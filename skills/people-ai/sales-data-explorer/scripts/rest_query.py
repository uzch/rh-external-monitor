#!/usr/bin/env python3
"""sales-data-explorer REST lane — validated raw-record reads from the Backstory
(formerly People.ai) Public REST API: activities + participants, CRM entity reads,
contact engagement history. Endpoint vocabulary: references/rest-catalog.json
(live-validated; the runner refuses anything outside it).

Stdlib only. Same credentials as the export lane (peopleai-key.local.json /
PEOPLEAI_CLIENT_ID+SECRET) — the REST token endpoint differs and is handled here.

Usage: python3 rest_query.py activities --param activity-uid=... --html --out ~/Desktop
"""
import argparse, csv, json, os, re, sys, urllib.parse, urllib.request, urllib.error
from run_query import load_credentials, render_html

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, "..", "references", "rest-catalog.json")
BASE_DEFAULT = "https://api.people.ai"
PAGE_SIZE = 200

def rest_token(base):
    cid, sec = load_credentials()
    body = (f"grant_type=client_credentials&client_id={urllib.parse.quote(cid)}"
            f"&client_secret={urllib.parse.quote(sec)}").encode()
    req = urllib.request.Request(base + "/auth/v1/tokens", data=body,
          headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"REST auth failed (HTTP {e.code}) — same key as the export lane; if the "
                 f"export lane works, this key may not be REST-enabled. Server said: "
                 f"{e.read()[:200].decode(errors='replace')}")

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("endpoint", help="Catalog key from references/rest-catalog.json")
    ap.add_argument("--param", action="append", default=[], metavar="K=V")
    ap.add_argument("--title", default=None)
    ap.add_argument("--out", default=".")
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--max-rows", type=int, default=5000)
    ap.add_argument("--base", default=BASE_DEFAULT)
    args = ap.parse_args()

    catalog = json.load(open(CATALOG))
    if args.endpoint not in catalog:
        sys.exit(f"'{args.endpoint}' is not in the validated REST catalog "
                 f"({', '.join(sorted(catalog))}). Unvalidated endpoints are refused by design.")
    entry = catalog[args.endpoint]
    params = {}
    for kv in args.param:
        k, _, v = kv.partition("=")
        if k not in entry["params_allowed"]:
            sys.exit(f"Param '{k}' is not validated for '{args.endpoint}' "
                     f"(allowed: {', '.join(entry['params_allowed']) or 'none'}).")
        params[k] = v

    tok = rest_token(args.base.rstrip("/"))
    rows, offset, calls, total = [], 0, 1, None  # calls counts the token
    while len(rows) < args.max_rows:
        q = dict(params)
        q["limit"] = min(PAGE_SIZE, args.max_rows - len(rows))
        if entry["pagination"] == "limit-offset":
            q["offset"] = offset
        url = f"{args.base.rstrip('/')}{entry['path']}?{urllib.parse.urlencode(q)}"
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=120)); calls += 1
        except urllib.error.HTTPError as e:
            sys.exit(f"REST read failed (HTTP {e.code}): {e.read()[:300].decode(errors='replace')}")
        batch = r.get("data", r if isinstance(r, list) else [])
        rows.extend(batch)
        total = (r.get("meta") or {}).get("total")
        offset += len(batch)
        if not batch or entry["pagination"] != "limit-offset" or (total is not None and offset >= total):
            break

    if rows and isinstance(rows[0], dict):
        missing = [f for f in entry["required_fields"] if f not in rows[0]]
        if missing:
            sys.exit(f"FIELD DROP: validated fields absent in this tenant: {', '.join(missing)}. "
                     "Do NOT present these results; re-validate the catalog entry.")
    header = entry["fields"]
    data = [[("" if row.get(f) is None else str(row.get(f))) for f in header] for row in rows]

    print(f"Endpoint {args.endpoint} ({entry['path']}) — rows: {len(data)}"
          + (f" of {total}" if total else ""))
    os.makedirs(args.out, exist_ok=True)
    title = args.title or args.endpoint
    safe = re.sub(r"[/\\:]", " ", title).strip() or "rest-query"
    out_csv = os.path.join(args.out, f"{safe}.csv")
    with open(out_csv, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(header); w.writerows(data)
    print(f"Wrote {out_csv}")
    if args.html:
        out_html = os.path.join(args.out, f"{safe}.html")
        open(out_html, "w").write(render_html(title, header, data, {"object": f"{args.endpoint} (REST)"}))
        print(f"Wrote {out_html}")
    print(f"API calls: {calls} (token + {calls-1} page reads)")

if __name__ == "__main__":
    main()
