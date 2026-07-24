# Portfolio Output Contract

One `portfolio.json` drives both Portfolio View and Account View.

## Portfolio View fields

- `scope.type`
- `scope.value`
- `summary.account_count`
- `summary.accounts_with_internal_data`
- `summary.accounts_enriched`
- `summary.keep_count`
- `summary.watch_count`
- `summary.highest_signal_score`
- `summary.text`
- `accounts[]`

Each account row exposes:

- hierarchy fields
- deterministic internal priority score
- engagement and activity metrics
- highest signal score
- KEEP/WATCH counts
- top reason for attention
- enrichment status

## Account View fields

The selected account exposes:

- identity and hierarchy
- 30-second summary
- recommended next move
- People.ai metrics
- Backstory status, risks, next steps, topics, engaged people
- external signals when enabled
- provenance and time windows

## Disposition semantics

- `KEEP`: actionable now; enough evidence and relevance for account-team attention.
- `WATCH`: meaningful but timing, evidence, or actionability is not yet sufficient.
- `REJECT`: retained only in raw run artifacts, not shown by default in the portfolio.

## Missing data

Use null and caveats. Never convert unavailable fields to zero unless the source explicitly returned zero.
