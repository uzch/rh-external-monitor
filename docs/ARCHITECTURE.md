# Architecture

External Monitor is a portable skill bundle that turns a list of enterprise accounts into a prioritized, enriched portfolio. It pulls internal activity data from People.ai, adds context from Backstory MCP and public web research, and produces a single JSON artifact that drives both an interactive HTML view and a Google Sheets-compatible spreadsheet.

## How it works

The pipeline has two halves: scripts handle the deterministic work (data assembly, scoring, formatting), and the model handles the parts that require reasoning (identity resolution, MCP enrichment, web research, signal composition).

```
load_registry.py → identity resolution → aggregate_activity_metrics.py
       \                  |                          /
        +--------→  build_portfolio.py  ←-----------+
                          |
                  portfolio-base.json (status: "partial")
                          |
                [MODEL: MCP calls + synthesis → mcp-enrichment.json]
                          |
                  enrich_portfolio.py  (deterministic merge + signal_score)
                          |
                [MODEL: external web research → signals]
                          |
                  enriched portfolio.json (status: "completed")
                          |
                +---------+---------+
                |                   |
        render_portfolio.py    export_sheets.py
                |                   |
          .html file          .xlsx workbook
```

This split keeps pipeline runs fast. A 9-account region completes in about 6 minutes, with the deterministic steps finishing in under 5 seconds. Before the split, the model spent ~12 minutes on a 3-account run because it was manually assembling JSON and computing scores.

## Key scripts

| Script | What it does |
|--------|-------------|
| `load_registry.py` | Filters the Enterprise Accounts CSV by GEO, region, or territory |
| `aggregate_activity_metrics.py` | Queries People.ai for activity records and computes per-account metrics |
| `build_portfolio.py` | Assembles a schema-valid base portfolio with deterministic priority scoring |
| `enrich_portfolio.py` | Merges MCP enrichment data into the base portfolio and computes signal scores |
| `render_portfolio.py` | Embeds portfolio JSON into the HTML template |
| `export_sheets.py` | Produces a formatted `.xlsx` with Portfolio and Signals tabs |

## Four boundaries

1. **Registry** — Enterprise Accounts CSV supplies account names and org assignments. It is not an intelligence source.
2. **Internal data** — People.ai Query API supplies batch metrics. Backstory MCP supplies deeper context for selected accounts.
3. **Orchestration** — The skill resolves scope, matches identity, ranks accounts, selects enrichment, and produces schema-valid JSON.
4. **Presentation** — HTML and `.xlsx` both consume the same JSON artifact. No per-account pages or tabs.

The system works without MCP: the Query API portfolio can still be produced with enrichment marked unavailable.

## Source layout

The authoritative People.ai source skills live under `skills/people-ai/`. The External Monitor orchestration layer lives under `skills/external-monitor-account-intelligence/`. Both are portable and agent-agnostic — Codex, Claude CLI, or another compatible runner can execute the file-based workflow.

---

## Technical details

### Scoring

There are two independent scores:

- **`internal_priority_score`** — deterministic 0-100 score computed by `build_portfolio.py` from four activity-metric components (volume, opportunities, momentum, recency), each worth 0-25. Used for backend triage: determines which accounts receive deep enrichment and in what order. Not shown to the end user.

- **`signal_score`** — the user-facing metric. Computed by `enrich_portfolio.py` as the average of all per-signal scores for an account, rounded to an integer. Shown in the spreadsheet, HTML view, and summary KPIs. `null` if no signals exist.

In the spreadsheet, signal score appears at every hierarchy level (GEO, region, territory, account) as the average of child account signal scores.

### Identity resolution and case sensitivity

The Enterprise Accounts registry stores account names in ALL CAPS (e.g., `DEFENSE INTELLIGENCE AGENCY`). People.ai stores them in title case (e.g., `Defense Intelligence Agency`). The People.ai Query API matches account names **case-sensitively** — querying with ALL CAPS returns zero results silently.

Identity resolution must call `find_account` and store the returned canonical `name` as `query_account_name`. The metrics script uses this field for the API filter. It also emits a warning when it detects ALL CAPS query names, catching the problem before a silent zero-result query goes unnoticed.

### Spreadsheet output

`export_sheets.py` produces a single `.xlsx` workbook with two tabs:

- **Portfolio** — hierarchical rows at GEO, Region, Territory, and Account levels. Filter the Level column to drill down. Parent rows aggregate metrics and signal scores from their children.
- **Signals** — one row per signal across all accounts, sorted by account then score. KEEP signals get green fill, WATCH gets amber. Source URLs are clickable hyperlinks.
