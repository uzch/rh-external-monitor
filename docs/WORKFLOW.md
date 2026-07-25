# Workflow

A pipeline run takes a scope (GEO, region, territory, or account name), pulls internal data from People.ai, enriches priority accounts with MCP and web research, and produces a portfolio JSON that drives the HTML view and spreadsheet export.

## Steps

1. **Scope** — Accept an exact scope type and value (e.g., region = INTEL).

2. **Registry** — Load accounts from the Enterprise Accounts CSV. The registry provides org assignments (GEO, region, territory, segment) — it is not an intelligence source.

3. **Identity resolution** — For each account, call People.ai `find_account` and store the returned canonical name as `query_account_name`. This is important: the registry uses ALL CAPS, People.ai uses title case, and the Query API is case-sensitive. Using the registry name directly returns zero results.

4. **Activity metrics** — Run `aggregate_activity_metrics.py` with the identity file. The script queries People.ai using `query_account_name` for the API filter. If it detects ALL CAPS names, it warns before the query runs.

5. **Base portfolio** — Run `build_portfolio.py` with registry, identity, and metrics inputs. This produces a schema-valid portfolio with deterministic priority scores and empty signals. No model reasoning needed — runs in seconds.

6. **MCP enrichment** — Enrich the highest-priority accounts (default 5, max 10) through Backstory MCP: account status, recent activity, and optionally engaged people and company news.

7. **External research** — If requested, search for public signals (contracts, earnings, leadership changes) and attach them with source URLs, publish dates, and a distinct source type.

8. **Merge and validate** — Merge enrichment into the base portfolio, update summary counts, set status to `completed`, and validate against the schema.

9. **Render** — Run `render_portfolio.py` for the interactive HTML view and `export_sheets.py` for a formatted `.xlsx` workbook. Both consume the same `portfolio.json`.

## What the result must include

- Scope and account count
- Which accounts were enriched vs. only scoped
- Time windows for each data source
- Source types on every signal (Query API, MCP, external, derived)
- Match status for every identity
- Caveats for missing or partial data
- The difference between evidence and model interpretation
