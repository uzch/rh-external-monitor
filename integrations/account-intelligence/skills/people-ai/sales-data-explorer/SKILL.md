---
name: sales-data-explorer
description: Answer ad-hoc questions and build custom tables/dashboards from Backstory (formerly People.ai) data — any validated metric on accounts, opportunities, sellers, teams, activities, or people. Use when the user asks a specific metric question ("how many VP+ meetings did <seller> have last quarter", "which accounts have no upcoming meetings", "emails sent by team last month"), wants a custom report/table/dashboard the canned skills don't produce, or asks "what else can I pull from Backstory / People.ai". Also covers raw-record questions from Backstory / People.ai — individual activities and who attended (participants with title/seniority), contact engagement history over time, and lead records. Companion to sales-data-pull (canned seller 360) and sales-insights (AI narratives).
license: Proprietary
metadata:
  version: 0.2.0
---

# Sales Data Explorer (Backstory Query API)

Turns a question into a validated Query API request and delivers the answer as a number, a
table (CSV), or a styled single-file HTML report. Every column comes from
`references/catalog.json` — a live-verified vocabulary — because the API **silently drops**
any column it doesn't recognize; the runner refuses unvalidated slugs before the call and
fails loudly if the tenant drops one after.

## When to use

- Metric questions and custom views over accounts / opportunities / users (sellers) / teams /
  activities / people — including forward-looking "upcoming meetings" windows.
- NOT for: the canned seller 360 (`sales-data-pull` does it in one step); AI narratives —
  risks, next steps, topics, themes, engaged-people-at-an-account (`sales-insights` via MCP;
  those fields do not exist in the export API).

## Procedure

1. **Map the question** to one object (`user`, `account`, `opportunity`, `activity`, `person`)
   and pick columns from that object's list in `references/catalog.json`. Grain check: "activities
   by seller" is usually the `account` object grouped by owner, not `user` — ask when ambiguous.
2. **Windows.** `variation_id = <slug>_<period>`. Retrospective: `last_7/14/30/60/90_days`,
   `last_month`, `last_quarter`, `this_quarter`, `any_time`. Future (upcoming-meetings metrics):
   `next_7/14/30_days`, `this_week`, `this_month`. Percentage metrics DOUBLE the suffix
   (`…_last_30_days_last_30_days`). A bare windowed slug means the 7-day default — usually not
   what the user asked; set the window explicitly.
3. **Filter server-side only where validated** (`references/query-guide.md` has shapes and the
   full trap list). Everything else: pull the column and filter client-side — owner filters on
   activity/opportunity objects are silently ignored by the API.
4. **Write the packet** (`{"object": …, "columns": [...], "filter": …}`) to a file and run:
   ```bash
   python3 scripts/run_query.py packet.json --title "Accounts with no upcoming meetings" \
       --out ~/Desktop --html
   ```
   Credentials are found automatically (same key as sales-data-pull; if none is wired in yet, that skill's Key setup section covers it). `--html` renders the
   styled table; the CSV always has every row.
5. **Deliver.** Answer the actual question first (a number is a number — don't ship a table for
   a scalar). State the window and the object grain with the answer, exactly as the column names
   do. For "which accounts have zero/low X": pull the column for all rows, filter client-side,
   present the shortlist.

## Raw-records lane (REST)

For record-level questions the metric export can't answer — "list the meetings and who
attended", "this contact's engagement trend", "lead records" — use the REST runner over the
same key: `python3 scripts/rest_query.py <endpoint> --param k=v --html`. Vocabulary =
`references/rest-catalog.json` (live-validated; runner refuses anything outside it, and
FIELD DROP aborts delivery — same honesty rule as the export lane). Join meetings to
attendees on activities `uid` ↔ participants `activity_uid`; id params take the long
People.ai `id`, never `crm_id`. Metric aggregates stay on the export lane; **no
email/meeting bodies exist on any lane** (deleted by design).

## Verification

The runner enforces both gates (catalog membership before the call; returned-column count
after). If it exits with COLUMN DROP, present nothing — a field isn't enabled in this tenant;
say so instead. Cross-check one row against a number the user already trusts when the result
drives a decision.

## Failure modes

- **COLUMN DROP** → a slug isn't enabled in this tenant. Report which packet failed and offer
  the nearest catalog alternative; never hand over partial columns.
- **400 report.filter.invalid / HTTP 500** → filter node malformed (a bare-string attribute
  crashes the server) — shapes are in `references/query-guide.md`; when in doubt, drop the
  filter and select client-side.
- **Rate limit** (~100 requests/hour/key) → each run costs 2 calls (token + export); batch
  questions into one packet where columns share an object.
- **Person-object questions scoped to an account** → not answerable here (person filters are
  unvalidated); hand off to `sales-insights`.
- Column vocabulary: `references/catalog.json` · shapes, filters, traps: `references/query-guide.md`.
