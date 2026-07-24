# Output contract — engagement-dashboard blob

The JSON emitted by `pull_sales_data.py` conforms to the schema of the existing
`engagement-dashboard` skill (SKILL.md §Schema reference in that artifact), so its
`template.html` renders this output unchanged: inject the blob at `__DATA_JSON__` inside
`<script id="data" type="application/json">` (the `--template` flag does this, plus the
`__OWNER_*__` / count placeholders).

## Keys (schema-compatible)

- `summary` — all 17 fields the template reads, plus `upcoming_meetings_14d` (seller's own
  upcoming matched meetings, next 14 days; null when the seller has no user-metrics row).
  SFDC-only counters (`emails_with_body`,
  `email_messages_count`, `manual_tasks_count`, `auto_tasks_count`, `transcripts_count`,
  `pai_accounts_with_data`) are `0` in API-only mode.
- `owned_accounts[]` — `industry`/`region`/`country`/`created` are `null`: not in the Query API
  surface (legacy-template compat keys). Each entry also carries the API-canonical account
  columns: `domain`, `type`, `engagement_level` (0–100), `last_meeting_date`,
  `open_opportunities`, `open_opp_amount_this_quarter`, `api_meetings_30d`/`_90d`,
  `api_emails_sent_30d`, `pct_emails_inbound_90d`, `time_spent_90d`, `exec_activities_30d`,
  `upcoming_meetings_14d` (future-dated matched meetings on the calendar, any participant).
- `account_rollup[]` — computed from activity rows at the requested window (not fixed 12mo/90d);
  `pai_meetings_30d`/`pai_emails_30d` are computed from the same API rows (30-day slice) rather
  than the MCP connector — by design (better provenance, no MCP dependency). Rollup rows also
  join the account columns above (`engagement_level`, `exec_activities_30d`,
  `open_opportunities`, `open_opp_amount_this_quarter`, `api_meetings_30d`/`_90d`,
  `last_meeting_date`, `upcoming_meetings_14d`). The computed book numbers reproduce the API's
  account meeting metrics exactly at matching windows.
- `events[]` / `emails[]` — from activity rows, each with `external` (bool) and `opportunity`
  (matched opportunity name or null). `description`/`body` are always empty: the Query API never
  exposes raw bodies — Backstory deletes body content shortly after ingestion (15-day product
  default, shorter where the tenant tightens it) and keeps only metadata. `duration`,
  `is_recurring`, `next_steps` are not in the API surface — emitted as null/empty defaults.
- `email_messages[]`, `eliot_owned_tasks[]` — always `[]` (Salesforce-sourced tabs; the key name
  `eliot_owned_tasks` is the template's own compat name).
- `peopleai_signals[]` — always `[]` here; the companion insights skill (MCP) fills it.

## Additive keys (ignored by the template, consumed by the insights skill / users)

- `opportunities[]` — this + next quarter, each with `relation`:
  `owned_by_seller` | `on_owned_account` | `both`.
- `user_metrics{}` — the seller's validated metric columns verbatim (display-name keys).
- `_meta{}` — provenance: timestamp, window, API-call count, quarter bounds, and `caveats[]`
  (surfaced in the dashboard behind the footer's "Data notes" disclosure; mention them to the
  user with the result).
