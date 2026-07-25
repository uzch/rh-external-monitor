---
name: sales-data-pull
description: Pull a seller-centric sales 360 from Backstory (formerly People.ai) — user metrics, owned accounts, up to a year of activity, and opportunities closing this or next quarter — rendered as an engagement-dashboard data blob or HTML. Use when the user asks to "pull sales data for <name>", "run the sales pull", "get <seller>'s 360 / activity / book", "build the engagement data for <name>", or gives a seller name (even misspelled) and wants their Backstory / People.ai data. Also use when the user wants to set up, wire in, connect, or swap the Backstory / People.ai API key for these sales skills.
license: Proprietary
metadata:
  version: 0.4.1
---

# Sales Data Pull (Backstory Query API)

Produces a seller's 360 directly from the Backstory (formerly People.ai) Query API — no MCP connection, no Salesforce dependency, windows up to **365 days** back (beyond the 30/90-day MCP caps) plus **upcoming meetings for the next 14 days**. Output is a JSON blob in the engagement-dashboard schema; with the dashboard `template.html` it renders the full offline HTML dashboard.

## When to use

- A seller/AM name or email is given and the user wants their metrics, accounts, activity, or pipeline from Backstory.
- NOT for: AI summaries, risks, or next-steps narratives (that is the companion insights skill via MCP); raw email/meeting bodies (the Query API never exposes them — Backstory permanently deletes body content shortly after ingestion, 15-day product default and shorter where a tenant tightens it; use CRM links).

## Procedure

1. Run the pull (from this skill's directory):
   ```bash
   python scripts/pull_sales_data.py "<seller name or email>" \
       --window-days 120 --out ~/Desktop
   ```
   HTML renders automatically with the bundled dashboard template (adaptive: sections without
   data collapse to one line, never walls of zeros). `--template <path>` swaps in an alternate
   template (e.g. an existing engagement-dashboard one); `--template none` skips HTML.
   - Credentials come from `scripts/peopleai-key.local.json` or `PEOPLEAI_CLIENT_ID`/`PEOPLEAI_CLIENT_SECRET` env vars. Missing or new key → **Key setup** below.
   - `--window-days`: default 120 (≈4 months), hard cap 365. Ops users often want 365.
   - Misspelled names are fine — the resolver finds close matches. If the script exits with a candidate list (exit code 2), show the candidates to the user and re-run with their choice — never guess between candidates silently.
2. Read the script's stdout. It reports: resolved seller, accounts owned, activities in window, linked opportunities, API-call count (≈5 per run + 1 per 100 owned accounts — a 1,000+-account book takes ~16 — against an observed ~100 req/hr/client capacity; a tenant key can carry a lower administrative cap — check before looping over many sellers).
3. **Heed silent-drop warnings.** Lines starting with `⚠ … silently dropped` mean this tenant rejected some validated fields — the Query API omits unknown columns *without any error*. Report the warning to the user and run `scripts/verify-packet.sh scripts/packets/<packet>.json` (with the tenant key) to identify which fields.
4. Deliverable: `<out>/<Seller> — Sales Data.json` + `<Seller> — Engagement 360.html` (single offline file, opens anywhere, light/dark). Mention the data boundaries from `_meta.caveats` to the user with the result — in the dashboard itself they live behind the footer's "Data notes" disclosure; the visible copy discloses semantics inline (seller KPIs = activities involving the seller; book sections = all participants).

## Key setup (first run or key swap)

When the user hands over a key ("wire in my API key", "set this up for me"): it is a Query API `client_id` + `client_secret` pair from their Backstory admin.

1. Write it to `scripts/peopleai-key.local.json` in **every installed copy** of this skill (check `~/.claude/skills/` plus the project's `.claude/skills/` and `.agents/skills/` — `install.sh` creates both):
   ```json
   {"client_id": "…", "client_secret": "…"}
   ```
2. Verify, then report the result to the user:
   ```bash
   python scripts/pull_sales_data.py --check-key
   ```
   `✓ API key works` on success; auth failures name the HTTP error and the server's reason.
3. One key serves the whole bundle — sales-data-explorer finds this file automatically. Never echo the secret back in full; never commit the key file to git.

## Verification

Before declaring success: the JSON exists and parses; `summary.meetings_count` is plausible and non-zero for an active seller (a seller with obviously-many meetings returning 0 usually means their config profile has intake OFF — flag it, don't hand over a silently-empty dashboard); `_meta.caveats` is intact in the JSON.

## Failure modes

- **Zero accounts owned** → the script stops by design: this skill targets sellers/AMs who own accounts. Ops leaders should name a seller instead.
- **Zero meetings for a clearly active seller** → tenant config-profile issue (intake OFF), not an API failure. Flag to the Backstory admin.
- **Empty user-metrics for a resolved seller** → user metrics are computed for a subset of the roster; the pull still succeeds — mention the empty section, don't treat it as failure.
- **Rate-limit error** → the script self-reports; wait an hour or have the admin raise the tenant limit before batch use.
- **Filter caveat (baked into the packets — do not "fix"):** owner filters on the activity/opportunity objects are *silently ignored* by the API (validated 2026-07-02). The packets filter activities by owned-account names and opportunities by close-date, then filter by owner client-side. Do not add owner filters back.
- Details: `references/api-behavior.md` (validated API facts), `references/output-schema.md` (blob contract).
