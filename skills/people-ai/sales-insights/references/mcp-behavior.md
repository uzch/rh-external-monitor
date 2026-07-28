# Backstory MCP endpoint and documented behavior

The tool behavior below was verified live on 2026-07-02. The current connection endpoint is
`https://mcp.backstory.ai/mcp`. Full tool contracts were captured from an authenticated
`tools/list`; this file distills what the skill relies on.

## Connection

- URL: **`https://mcp.backstory.ai/mcp`** (Streamable HTTP).
- Auth: OAuth 2.1 + PKCE, per-user interactive login only. No API-key or client-credentials path
  exists — Query API bearer tokens are rejected (`401 non_jwt_token`). This is why each end user
  connects individually and why the companion skill (API-key based) is a separate artifact.
- The server operates statelessly (verified: `tools/call` works without a session id).

## Tool surface (13 tools, all read-only)

Entry points — the ONLY ways in (`peopleai_*_id` integers come from these; there is **no
list/filter/enumeration tool**):

| Tool | In | Out |
|---|---|---|
| `find_account` | `account_name` | account details + `peopleai_account_id` + its opportunities |
| `find_record_by_crm_id` | `crm_id` | internal ids for a CRM/SFDC id |
| `top_records` | — | ~20 accounts+opps relevant to the logged-in user; **not exhaustive**; max once per interaction |

Account-scoped (`peopleai_account_id: int`): `get_account_status` (risks/next steps/topics),
`get_recent_account_activity` (importance-classified activity), `get_engaged_people`
(external/internal split with counts), `account_company_news` (public cos only), `get_scorecard`
(MEDDIC/MEDDPICC/SPICED if configured), `ask_sales_ai_about_account` (+`question`).
Opportunity-scoped (`peopleai_opportunity_id: int`): `get_opportunity_status`,
`get_recent_opportunity_activity`, `ask_sales_ai_about_opportunity`, `situation_search`
(similar historical deals, ≤4 matches >70%; NOTE its param is named `opportunity_id`).

## Windows (the load-bearing facts)

- Status/activity/engaged-people tools: **30 days, hard**. Zero credits.
- `ask_sales_ai_*`: reaches **90 days** when the question *explicitly* requests it — e.g. "review
  activity older than 30 days, up to 90 days ago". Product-confirmed 2026-07-02 (the 30d in the
  tool descriptions is a doc bug pending fix — harnesses that read descriptions may warn; proceed)
  and live-verified the same day (explicit-window question returned dated items 60–90 days back).
- ≥90 days: **no MCP source.** A 1-year MCP lookback is a logged product GAP, not a feature.
  Long-window counts/activity come from the Query API (`sales-data-pull`).

## Credits

`ask_sales_ai_*` calls consume SalesAI credits (tenant-metered); everything else is free. House
rules: free tier first, ≤10 credit calls per run, announce before spending, report the count after.
Never loop credit calls over an unsegmented account list.

## Output shapes

Most tools return `{"result": string|object}` (FastMCP wrap) — unwrap `.result` and accept either
markdown text or a structured object. `find_account`, `find_record_by_crm_id`, `ask_sales_ai_*`,
`situation_search` return bare objects. Do not build schema-strict parsers; check for the fields you
need at runtime.

## §Signals — dashboard interop contract

The engagement-dashboard blob (from `sales-data-pull`) reserves `peopleai_signals` for this skill.
Contract (the client's own template/build consumes exactly this shape):

```json
[{"account_name": "...", "peopleai_id": 123, "engaged_people": <get_engaged_people output>,
  "account_status": <get_account_status output>}]
```

Additive keys (`risks`, `next_steps`, `topics`, `window`) are permitted — consumers ignore what
they don't know. `scripts/merge_signals.py` injects the array, recomputes
`summary.pai_accounts_with_data`, and optionally re-renders the HTML.

## §News + situations — verified shapes (probed 2026-07-07)

**`account_company_news(peopleai_account_id)`** → `{"result": [{eureka, source, category}, …]}`
(wrapped array). `eureka` = one dated fact sentence (dates INSIDE the text, no date field;
speaker/role/quarter attribution on earnings quotes); `source` ∈ earnings_call / 10-K / 8-K
(filings monitor — not a press clipper); `category` ∈ vision / finance / risks / hires and
departures / m&a / organizational changes / other. Public companies only — private → empty
list (an answer, not an error). Volume: 200+ items (~70KB) on a mega-cap — select the few
items relevant to the question; never inline the feed (Output contract).

**`situation_search(query, opportunity_id)`** → bare object (no `result` wrap):
`{situation, candidates[≤4, >70% similarity]}`; candidate = `{situation_summary, match_score,
opportunity_{id,name,crm_id,owner_name,amount,close_date,is_closed,is_won}, account_name,
actions_taken[] ("[date][seller|buyer] …"), outcome, resolution_status
(resolved|partially_resolved|…), resolution_explanation}`. The `situation` is re-derived from
the deal's recent activity, anonymized to buyer/seller roles. Param name is `opportunity_id`
(NOT `peopleai_opportunity_id`). It's a precedent finder over historical deals — coverage is
similarity-gated, so absence of candidates means "no similar situations found", never "no
such discussions happened". Both tools: no credit notice — free tier.
