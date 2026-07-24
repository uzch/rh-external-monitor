# Query guide — shapes, filters, and traps (all live-verified)

Endpoint: `POST https://api.people.ai/v3/beta/insights/export` (OAuth client-credentials via
`POST /v3/auth/tokens`; tokens last 2 hours — there is no refresh flow, request a new one).
Response is CSV; headers are human display names (with the window in the name), not slugs.

## Packet shape

```json
{
  "object": "account",
  "columns": [
    {"slug": "ootb_account_name"},
    {"slug": "ootb_account_engagement_level"},
    {"slug": "ootb_account_upcoming_meetings_standard",
     "variation_id": "ootb_account_upcoming_meetings_standard_next_14_days"}
  ],
  "filter": { ... optional ... }
}
```

## Filters — exact shapes matter

A filter is a leaf or a logical node:

```json
{"attribute": {"slug": "ootb_activity_timestamp"}, "clause": {"$gte": 1780000000000}}
{"$and": [ <node>, <node> ]}   ·   {"$or": [ <node>, <node> ]}
```

Operators: string `$eq $ne $in $nin $regex` · number `$eq $ne $gt $gte $lt $lte $in $nin` ·
boolean `$eq $ne`.

**The four traps (each cost a debugging session — believe them):**

1. `attribute` must be an **object** `{"slug": "…"}`. A bare string crashes the server
   (HTTP 500 "sorry something went wrong" — not a validation error).
2. Timestamps/close dates are **integer epoch-milliseconds**. ISO strings → 400.
3. A structurally-valid filter on an **unsupported attribute is silently ignored** — the full
   unfiltered set returns and looks like success. Validated filterable: `ootb_user_email`
   (string), `ootb_account_original_owner` (numeric id), `ootb_activity_account_name` (string,
   `$in` ok), `ootb_activity_timestamp`, `ootb_opportunity_close_date` (both epoch-ms),
   `ootb_activity_is_meeting` (boolean). **Owner filters on activity/opportunity objects are
   ignored** — select the owner column and filter client-side.
4. Unknown columns are **dropped silently** (no error, no placeholder). The runner counts
   returned columns against the request and refuses to deliver on any shortfall.
5. Time **ranges** go in ONE clause node: `{"clause": {"$gte": A, "$lte": B}}`. An `$and` of
   two nodes on the *same* attribute → HTTP 500 (validated live 2026-07-07).

## Behavior notes

- Some slugs expand to several columns (e.g. `ootb_opportunity_amount` → amount + currency;
  `ootb_activity_match_result` → 9). The catalog marks known expansions.
- Booleans come back as `"True"`/`"False"`; dates as ISO `"YYYY-MM-DD HH:MM:SS+00:00"`.
- `limit` is not honored — you get all rows; large objects (activity) can be big. Filter by
  account names + time window like the sales-data-pull packets do.
- Activity timestamp windows include future-scheduled meetings — trim client-side if you only
  want history (the canned pull does).
- Rate capacity ≈ 100 requests/hour/key; each run = 2 calls. The old "10/hour" cap was an
  administrative setting on a previous key, not a platform limit.
- AI narrative fields (`key_topics`, `next_steps`, `risks`) and per-activity AI summaries are
  **not** served by this API today (columns exist for summaries but return empty) — narratives
  come from the `sales-insights` skill over MCP.

## Worked examples

**"Which owned accounts have nothing on the calendar?"** — account object: name +
engagement level + `…upcoming_meetings_standard_next_14_days`, filter
`ootb_account_original_owner $eq <owner id>`; client-side keep rows where upcoming = 0;
present sorted by engagement level (high engagement + empty calendar = the actionable list).

**"How many meetings with VPs+ did <seller> have last quarter?"** — user object:
`ootb_user` + `ootb_user_meetings_with_director_vp_exec` with `…_last_quarter`, filter
`ootb_user_email $eq <email>`. The answer is one cell — report the number and the window.

**"Team activity table for the month"** — user object: `ootb_user`, `ootb_user_team`,
emails sent/received + external meetings, each with `…_last_month`; no server filter
(roster-wide), group client-side by the Team column.
