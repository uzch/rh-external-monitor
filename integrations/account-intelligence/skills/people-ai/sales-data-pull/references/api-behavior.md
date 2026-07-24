# Query API — validated behavior this skill depends on

All facts verified live against `https://api.people.ai` (validation window 2026-06-03 → 2026-07-02,
including the production tenant). Every slug/variation in `scripts/packets/` was individually
validated; re-check any packet in a new tenant with `scripts/verify-packet.sh`.

## Endpoint

`POST /v3/beta/insights/export` — auth `POST /v3/auth/tokens` (client-credentials; token lifetime
observed 2h live at validation, vendor docs state 1h — treat as ≥1h and re-auth on 401).
Response is CSV; **header names are display labels, not slugs**; quoted headers may contain
newlines/commas (parse with a real CSV parser, never `split(',')`).

## The two silent traps

1. **Unknown columns are silently dropped** — a 5-column request can return 3 with HTTP 200.
   The runtime compares returned column counts against the validated count and warns.
2. **Unsupported *filter attributes* are silently ignored** — the filter validates shape and
   datatype, then skips attributes it can't filter on, returning the UNFILTERED set.
   Validated filterable: `ootb_user_email` (string), `ootb_account_original_owner` (numeric id),
   `ootb_activity_account_name` (string, `$in` ok), `ootb_activity_timestamp` (int epoch-ms),
   `ootb_opportunity_close_date` (int epoch-ms).
   Validated **ignored**: `ootb_activity_owner`, `ootb_opportunity_owner` (both value types) —
   hence client-side owner filtering in this skill.
   Typed rejections: `ootb_activity_account` (datatype `account`) errors on string values;
   date attributes error on ISO strings ("use compatible datatypes such as: int").

## Formats

- Filters on date/timestamp attributes take **epoch milliseconds (int)**.
- Returned dates are ISO: `YYYY-MM-DD HH:MM:SS+00:00`.
- Booleans return as `True`/`False` strings.
- Some slugs expand to multiple columns: `ootb_user`/`ootb_user_team`/`ootb_account_original_owner`/
  `ootb_opportunity_owner` → `(id)` + `(name)`; `ootb_opportunity_amount` → amount + currency.
- `limit` is NOT honored on the public export; the only volume controls are server-side filters.
- Activity `$gte` windows include **future-scheduled meetings** (calendar data) — the runtime trims
  them by default.
- Join key: user `User (id)` / `User Identification` values match `ootb_account_original_owner`
  numeric ids (verified by count contrast).
- Rate limit: 100 req/hr/client (vendor-documented cap; validation runs sustained 77–80/hr with
  zero throttling, enforcement behavior never observed). Separately, a tenant key can carry a lower
  administrative cap — a Backstory admin can raise it. The runtime makes ≈5 calls + 1 per 100
  owned accounts and self-reports the count.

## Packet inventory (`scripts/packets/`)

| Packet | Object | Filter | Validated columns |
|---|---|---|---|
| `roster.json` | user | none | 7 |
| `user-metrics.json` | user | email `$eq` | 22 |
| `accounts-owned.json` | account | original_owner `$eq` int | 16 |
| `activities.json` | activity | account_name `$in` + timestamp `$gte` ms | 10 |
| `opportunities.json` | opportunity | close_date `$gte`/`$lt` ms | 11 |

Re-validate any packet in a new tenant with `scripts/verify-packet.sh` before first use —
tenant configuration can disable metrics that are valid elsewhere.

## Tenant-validated behavior (production tenant, 2026-07-02)

- **All 5 packets' headers survive 100%** with the current packet set; an end-to-end pull for a
  1,000+-account book completed in 16 API calls with no throttling.
- **`ootb_user_total_activity` (bare slug) is a row-killer in this tenant**: requested alone it
  is silently dropped from the header; combined with any other metric column the export returns
  **0 rows** (HTTP 200, full header echoed). It is valid in other tenants — tenant-specific
  drift. Removed from `user-metrics.json` in 0.1.1; `Total External Activities (Last 30 Days)`
  covers the need.
- **Metric universe ⊂ roster**: metric-bearing user packets return rows only for
  metric-computed users (601 rows vs 958 in the roster packet at validation). A resolved seller
  can legitimately have an empty metrics row; the runtime warns instead of passing silently.
- No throttling observed at 25+ calls within an hour on a tenant key.
