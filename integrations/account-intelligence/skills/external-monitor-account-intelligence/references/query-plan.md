# External Monitor Query Plan

## Purpose

Translate an Enterprise Accounts scope into the smallest useful set of People.ai Query API requests.

## Account batch

Use the `account` object for one row per account. Requested slugs must be selected from the installed `sales-data-explorer/references/catalog.json`.

Target fields, where tenant-enabled:

- account name
- account owner
- engagement level
- last meeting date
- upcoming meetings next 14 days
- meetings last 30 days
- meetings last 90 days
- emails sent last 30 days
- executive activities last 30 days
- open opportunities
- open opportunity amount this quarter

Do not hardcode unsupported slugs in orchestration code. Resolve the actual slug from the catalog and fail clearly when unavailable.

## Activity batch

Use the `activity` object when recent record-level activity is required.

Safe server-side filters:

- account name `$in` selected account names
- activity timestamp range in one clause node
- meeting boolean when needed

Do not add owner filters to activity or opportunity packets; those are documented as silently ignored. Pull owner columns and filter client-side.

## REST lane

Use `sales-data-explorer/scripts/rest_query.py` only when the view requires individual activity records or participants. Do not expect email or meeting body content.

## Suggested batch sequence

1. Account metric packet for all scoped accounts.
2. Activity packet for all scoped accounts within the requested lookback.
3. Opportunity packet only when portfolio prioritization requires pipeline context.
4. REST participant queries only for accounts selected for drill-down.

## Rate discipline

- Consolidate fields that share object and window.
- Cache raw CSV/JSON artifacts per run.
- Do not rerun the same packet during rendering.
