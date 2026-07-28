# Workflow

A pipeline run takes a scope (GEO, region, territory, or account name), pulls internal data from People.ai, enriches priority accounts with MCP and web research, and produces a portfolio JSON that drives the HTML view and spreadsheet export.

## Steps

1. **Scope** — Accept an exact scope type and value (e.g., region = INTEL).

2. **Registry** — Load accounts from the Enterprise Accounts CSV. The registry provides org assignments (GEO, region, territory, segment) — it is not an intelligence source.

3. **Identity resolution** — Always start by running `resolve_identities.py` with the identity cache (`data/local/identity-cache.json`). Cached accounts resolve instantly without any API calls. For uncached accounts, call People.ai `find_account` and store the returned canonical name as `query_account_name`. The registry uses ALL CAPS, People.ai uses title case, and the Query API is case-sensitive. For region or GEO scope (20+ accounts), split uncached accounts into chunks of ~20 and resolve them in parallel subagents. After resolution, update the cache. **MCP fallback:** `find_account` requires MCP OAuth in the main session — it is not available to subagents. If MCP is unavailable, use the People.ai REST API or Query API as a fallback for uncached accounts.

4. **Activity metrics** — Run `aggregate_activity_metrics.py` with the identity file. The script queries People.ai using `query_account_name` for the API filter and handles any scope size internally by batching the `$in` filter (groups of 50 account names, one Query API call per batch). If it detects ALL CAPS names, it warns before the query runs.

5. **Base portfolio** — Run `build_portfolio.py` with registry, identity, and metrics inputs. This produces a schema-valid portfolio with deterministic priority scores and empty signals. No model reasoning needed — runs in seconds.

6. **MCP enrichment** — Enrich the highest-priority accounts (default 5, max 10) through Backstory MCP: account status, recent activity, and company news. MCP tools require OAuth bound to the main session and are **not available to subagents**. Preferred pattern: the orchestrator makes all MCP calls sequentially from the main session, then passes raw responses to parallel subagents for synthesis. If MCP is entirely unavailable, skip this step (set `mcp_status = "unavailable"`) and proceed to external research. Credit calls (`ask_sales_ai_about_account`) stay orchestrator-controlled.

7. **External research** — Runs by default. Search for public signals (contracts, earnings, leadership changes) and attach them with source URLs, publish dates, and a distinct source type. Skipped only when the user explicitly opts out.

8. **Validate** — Validate the enriched portfolio against the schema. Status is `completed` when all matched accounts are enriched, `partial` otherwise.

9. **Render** — Run `render_portfolio.py` for the interactive HTML view and `export_sheets.py` for a formatted `.xlsx` workbook. Both consume the same `portfolio.json`.

## What the result must include

- Scope and account count
- Which accounts were enriched vs. only scoped
- Time windows for each data source
- Source types on every signal (Query API, MCP, external, derived)
- Match status for every identity
- Caveats for missing or partial data
- The difference between evidence and model interpretation
