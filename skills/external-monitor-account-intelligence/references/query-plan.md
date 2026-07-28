# External Monitor Query Plan

## Purpose

Translate an Enterprise Accounts scope into the smallest useful set of People.ai Query API requests.

## Account batch (not currently implemented)

The `account` object could provide one row per account with fields like engagement level, account owner, and opportunity amount. However, the `account` object has no validated server-side name filter -- an unfiltered query dumps metrics for every account in the tenant, causing multi-minute timeouts. The pipeline currently uses the `activity` object exclusively (see below).

If a future tenant configuration supports server-side account name filtering, the account batch could supplement the activity batch for fields unavailable from the activity object.

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

1. Activity packet for all scoped accounts within the requested lookback (primary data source -- uses `$in` filter on account name, batched in groups of 50).
2. Opportunity packet only when portfolio prioritization requires pipeline context.
3. REST participant queries only for accounts selected for drill-down.
4. Account metric packet if server-side name filtering becomes available (not currently used).

## Rate discipline

- Consolidate fields that share object and window.
- Cache raw CSV/JSON artifacts per run.
- Do not rerun the same packet during rendering.
