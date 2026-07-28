#!/usr/bin/env python
"""sales-data-explorer — run a validated Query API packet and deliver the result.

Gate order: (1) every slug/variation in the packet must appear in references/catalog.json
(the live-verified vocabulary — unknown columns would be dropped SILENTLY by the API);
(2) after the call, the returned header is diffed against the request and any shortfall
fails loudly. Only then is the result delivered, as CSV and optionally a single-file
HTML table in the Engagement 360 design language.

Stdlib only. Credentials: PEOPLEAI_CLIENT_ID / PEOPLEAI_CLIENT_SECRET env vars, or a
peopleai-key.local.json next to this script, or the sales-data-pull copy of the same file
(one pilot key serves the whole bundle).

Usage:
    python run_query.py <packet.json> [--title "Open opps by engagement"]
        [--out DIR] [--html] [--base https://api.people.ai]
"""
import argparse
import csv
import datetime as dt
import html as html_mod
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, "..", "references", "catalog.json")
HTML_ROW_CAP = 500


def _load_dotenv():
    """Load .env from repo root into os.environ (stdlib only, no overwrite)."""
    root = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
    dotenv = os.path.join(root, ".env")
    if not os.path.isfile(dotenv):
        return
    with open(dotenv, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


def load_credentials():
    _load_dotenv()
    cid, sec = os.environ.get("PEOPLEAI_CLIENT_ID"), os.environ.get("PEOPLEAI_CLIENT_SECRET")
    if cid and sec:
        return cid, sec
    candidates = [
        os.path.join(HERE, "peopleai-key.local.json"),
        os.path.join(HERE, "peopleai-key.json"),
        os.path.join(HERE, "..", "..", "sales-data-pull", "scripts", "peopleai-key.local.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            k = json.load(open(path))
            return k["client_id"], k["client_secret"]
    sys.exit('No credentials. Create peopleai-key.local.json containing '
             '{"client_id": "...", "client_secret": "..."} in the installed sales-data-pull/scripts/ '
             '(found automatically — one key serves the bundle) or next to this script, or set '
             'PEOPLEAI_CLIENT_ID/PEOPLEAI_CLIENT_SECRET.')


def check_against_catalog(packet):
    cat = json.load(open(CATALOG))
    obj = packet.get("object")
    if obj not in cat["objects"]:
        sys.exit(f"Object '{obj}' is not in the validated catalog "
                 f"(have: {', '.join(sorted(cat['objects']))}).")
    known = {c["slug"]: c for c in cat["objects"][obj]}
    future_ok = tuple("_" + p for p in cat["period_vocabulary"]["future (upcoming-meetings metrics)"])
    retro_ok = tuple("_" + p for p in cat["period_vocabulary"]["retrospective"])
    for col in packet.get("columns", []):
        slug = col.get("slug", "")
        if slug not in known:
            sys.exit(f"Column '{slug}' is not in the validated catalog for object '{obj}' — "
                     "the API would drop it SILENTLY. Pick from references/catalog.json.")
        var = col.get("variation_id")
        if var:
            entry = known[slug]
            if var in entry.get("verified_variations", []):
                continue
            # accept <slug>_<period> and the doubled percentage form; anything else is refused
            tail = var[len(slug):]
            singles = retro_ok + future_ok
            doubled = tuple(a + a for a in retro_ok)
            if not (var.startswith(slug) and (tail in singles or tail in doubled)):
                sys.exit(f"variation_id '{var}' does not follow the validated period vocabulary "
                         "(see catalog period_vocabulary; percentages double the suffix).")
    return len(packet.get("columns", []))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("packet", help="Path to the request packet JSON")
    ap.add_argument("--title", default=None, help="Human title for the result artifact")
    ap.add_argument("--out", default=".", help="Output directory")
    ap.add_argument("--html", action="store_true", help="Also render a single-file HTML table")
    ap.add_argument("--base", default="https://api.people.ai")
    args = ap.parse_args()

    packet = json.load(open(args.packet))
    requested = check_against_catalog(packet)

    cid, sec = load_credentials()
    body = (f"grant_type=client_credentials&client_id={urllib.parse.quote(cid)}"
            f"&client_secret={urllib.parse.quote(sec)}").encode()
    req = urllib.request.Request(args.base.rstrip("/") + "/v3/auth/tokens", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        token = json.load(urllib.request.urlopen(req, timeout=60))["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"Auth failed (HTTP {e.code}) — check the API key. Server said: "
                 f"{e.read()[:200].decode(errors='replace')}")

    req = urllib.request.Request(args.base.rstrip("/") + "/v3/beta/insights/export",
                                 data=json.dumps(packet).encode(),
                                 headers={"Authorization": "Bearer " + token,
                                          "Content-Type": "application/json"})
    try:
        text = urllib.request.urlopen(req, timeout=600).read().decode()
    except urllib.error.HTTPError as e:
        msg = e.read()[:400].decode(errors="replace")
        if e.code == 429 or "rate" in msg.lower():
            sys.exit(f"Rate-limited (HTTP {e.code}) — capacity is ~100 requests/hour per key; "
                     f"wait or ask the Backstory admin.\n{msg}")
        sys.exit(f"Export failed (HTTP {e.code}): {msg}\n"
                 "(A 400 report.filter.invalid means the filter shape is wrong — "
                 "see references/query-guide.md; a 500 usually means a malformed filter node.)")

    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        sys.exit("Empty response — no header returned. Do not present any result.")
    header, data = rows[0], rows[1:]

    # Header-diff gate: some slugs expand to several columns, so fewer-than-requested is the
    # only reliable failure signal (and it is fatal by design — never deliver a silently
    # incomplete result).
    if len(header) < requested:
        sys.exit(f"COLUMN DROP: requested {requested} columns, API returned {len(header)} "
                 f"({', '.join(header)}). A slug/variation is not enabled in this tenant — "
                 "do NOT present these results; check the catalog and re-validate.")

    print(f"Columns returned ({len(header)}): {', '.join(header)}")
    print(f"Rows: {len(data)}")

    os.makedirs(args.out, exist_ok=True)
    title = args.title or os.path.splitext(os.path.basename(args.packet))[0]
    safe = re.sub(r"[/\\:]", " ", title).strip() or "query"
    out_csv = os.path.join(args.out, f"{safe}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(data)
    print(f"Wrote {out_csv}")

    if args.html:
        out_html = os.path.join(args.out, f"{safe}.html")
        open(out_html, "w").write(render_html(title, header, data, packet))
        print(f"Wrote {out_html}")
    print("API calls: 2 (token + export)")


def render_html(title, header, data, packet):
    esc = html_mod.escape
    shown = data[:HTML_ROW_CAP]
    is_num = [all(re.fullmatch(r"-?[\d,]+(\.\d+)?", (r[i] or "0").strip()) for r in shown if i < len(r) and (r[i] or "").strip())
              and any(i < len(r) and (r[i] or "").strip() for r in shown)
              for i in range(len(header))]
    ths = "".join(f'<th class="{"num" if n else ""}">{esc(h)}</th>' for h, n in zip(header, is_num))
    trs = []
    for r in shown:
        tds = "".join(f'<td class="{"num" if i < len(is_num) and is_num[i] else ""}">'
                      f'{esc(r[i]) if i < len(r) else ""}</td>' for i in range(len(header)))
        trs.append(f"<tr>{tds}</tr>")
    capnote = (f"<p class='sub'>Top {HTML_ROW_CAP} rows shown — all {len(data):,} are in the CSV.</p>"
               if len(data) > HTML_ROW_CAP else "")
    when = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root {{ color-scheme: light dark; --surface-1:#fcfcfb; --page:#f9f9f7; --ink:#0b0b0b; --ink-2:#52514e;
  --muted:#898781; --grid:#e1e0d9; --border:rgba(11,11,11,0.10); --brand:#76B900; }}
@media (prefers-color-scheme: dark) {{ :root {{ --surface-1:#1a1a19; --page:#0d0d0d; --ink:#fff;
  --ink-2:#c3c2b7; --muted:#898781; --grid:#2c2c2a; --border:rgba(255,255,255,0.10); }} }}
@media print {{ :root {{ --surface-1:#fcfcfb; --page:#fff; --ink:#0b0b0b; --ink-2:#52514e;
  --muted:#898781; --grid:#e1e0d9; --border:rgba(11,11,11,0.10); }} }}
* {{ box-sizing:border-box; }} html,body {{ margin:0; }}
body {{ background:var(--page); color:var(--ink); font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;
  border-top:3px solid var(--brand); }}
.wrap {{ max-width:1120px; margin:0 auto; padding:20px 24px 64px; }}
.eyebrow {{ font-size:11px; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; color:var(--muted);
  display:flex; align-items:center; gap:8px; }}
.eyebrow::before {{ content:""; width:14px; height:3px; background:var(--brand); display:inline-block; }}
h1 {{ font-size:24px; font-weight:650; margin:8px 0 2px; }}
.provenance {{ margin:8px 0 18px; font-size:12px; color:var(--muted); display:flex; flex-wrap:wrap; gap:6px 18px; }}
.provenance b {{ color:var(--ink-2); font-weight:600; }}
.card {{ background:var(--surface-1); border:1px solid var(--border); border-radius:10px; padding:6px 8px; overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ text-align:left; font-size:11px; font-weight:650; letter-spacing:0.06em; text-transform:uppercase;
  color:var(--muted); padding:6px 10px; border-bottom:1px solid var(--grid); white-space:nowrap; }}
td {{ padding:6px 10px; border-bottom:1px solid var(--grid); }}
tr:last-child td {{ border-bottom:none; }}
td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.sub {{ color:var(--muted); font-size:12px; }}
footer {{ margin-top:22px; font-size:12px; color:var(--muted); }}
</style></head><body><div class="wrap">
<div class="eyebrow">Backstory Data Explorer</div>
<h1>{esc(title)}</h1>
<div class="provenance"><span>Generated <b>{when}</b></span><span>Object <b>{esc(packet.get("object", ""))}</b></span>
<span>Rows <b>{len(data):,}</b></span><span>Source <b>Backstory Query API — formerly People.ai</b></span></div>
<div class="card"><table><thead><tr>{ths}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>
{capnote}
<footer>Generated offline-viewable from a validated column set — window semantics are in each column name.</footer>
</div></body></html>"""


if __name__ == "__main__":
    main()
