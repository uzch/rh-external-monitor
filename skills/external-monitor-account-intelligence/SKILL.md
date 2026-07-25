---
name: external-monitor-account-intelligence
description: Build External Monitor portfolio and account intelligence for a selected GEO, region, pod, territory, or account. Resolve the account population from the Enterprise Accounts registry, batch-pull validated People.ai Query API metrics, selectively enrich priority accounts through Backstory MCP, and produce a strict JSON artifact for the External Monitor Portfolio View and Account View. Use when the user asks to research enterprise accounts, generate a portfolio briefing, identify accounts needing attention, or refresh the External Monitor interface.
license: Internal
metadata:
  version: 0.1.0
---

# External Monitor Account Intelligence

This skill is the orchestration layer for the External Monitor MVP. It does not replace the People.ai-provided skills. It composes them:

- `sales-data-explorer` — validated People.ai Query API requests and batch metrics.
- `sales-insights` — account-level Backstory MCP narratives and engaged-people context.
- `sales-data-pull` — reference implementation for authentication, API behavior, and rendering patterns; do not use its seller-centric workflow as the primary product flow.

## Product outcome

Given a scope such as:

- GEO = NAPS
- Region = Federal Civilian
- Pod = Healthcare
- Territory = `<territory_name>`
- Account = `<account_name>`

produce one portfolio JSON artifact that drives both:

1. **Portfolio View** — prioritize accounts within the selected scope.
2. **Account View** — drill into one account's internal context, external signals, risks, next steps, people, and evidence.

Never create one tab or one HTML page per account. The same reusable interface filters and renders the selected scope/account.

## Inputs

Required:

- `scope_type`: `geo | region | territory | account`
- `scope_value`: exact value from the Enterprise Accounts registry
- Enterprise Accounts registry at `data/local/Enterprise Accounts.csv` containing:
  - `account_sales_group_name` (canonical account name)
  - `geo`
  - `region`
  - `segment`
  - `ACCOUNT_TERRITORY_NAME`

The registry establishes the account population and organizational assignment. It is not an intelligence source. It provides no activity, engagement, risks, opportunities, next steps, or external signals.

Optional:

- `lookback_days` for Query API metrics, default `120`, maximum `365`
- `deep_enrichment_limit`, default `5`, maximum `10`
- `external_research`: boolean, default `true`. Set to `false` only when the user explicitly opts out of web research.
- `research_objective`: user-specific prioritization objective

## Procedure

### 1. Resolve the account population

Load the Enterprise Accounts registry using `scripts/load_registry.py`:

```bash
python scripts/load_registry.py --geo NAPS --region CIVILIAN --out scoped-accounts.json
```

Or load it directly from `data/local/Enterprise Accounts.csv` and filter by scope:

- GEO -> `geo == scope_value`
- Region -> `region == scope_value`
- Territory -> `territory_name == scope_value`
- Account -> exact or substring match on `account_name`

The registry provides five fields per account: `account_name`, `geo`, `region`, `segment`, `territory_name`. These are organizational assignments, not intelligence. Do not infer values not present in the registry.

To list available scopes:

```bash
python scripts/load_registry.py --list-geos
python scripts/load_registry.py --list-regions --geo NAPS
python scripts/load_registry.py --list-territories --geo NAPS --region CIVILIAN
```

If no accounts match, stop and report the exact scope used.

### 2. Normalize account identity

For each account in scope, call `find_account` (or `find_record_by_crm_id` when a CRM ID is available) to resolve the People.ai identity. Create an identity record per account:

```json
{
  "registry_account_name": "ALL-CAPS name from registry",
  "query_account_name": "People.ai canonical name from find_account",
  "peopleai_account_id": 12345678,
  "identity_status": "confirmed",
  "identity_notes": "matched via find_account"
}
```

**Critical: `query_account_name` must be the `name` field returned by People.ai `find_account`, not the registry name.** The People.ai Query API uses case-sensitive account name matching. The registry stores names in ALL CAPS (e.g., `DEFENSE INTELLIGENCE AGENCY`) but People.ai stores them in title case (e.g., `Defense Intelligence Agency`). Using the registry name in queries returns zero results.

Identity status values:

- `confirmed` — exact match found in People.ai
- `resolved_alias` — matched under a different name (e.g., subsidiary or trade name)
- `ambiguous` — multiple possible matches; do not enrich until resolved
- `not_found` — no match in People.ai

Preferred matching order for People.ai reconciliation:

1. Salesforce/CRM ID when available.
2. Backstory `find_account` with the registry account name.
3. `find_account` with variations (drop parenthetical abbreviations, try common aliases).
4. Explicit alias supplied by the user.

Never silently merge ambiguous accounts. Mark them `ambiguous` and exclude them from deep enrichment until resolved.

### 3. Run the batch Query API pass

**Always use `scripts/aggregate_activity_metrics.py`.** This script queries the `activity` object with a server-side `ootb_activity_account_name $in [...]` filter, scoped to only the accounts in your identity map. It then aggregates per-account metrics client-side.

```bash
python scripts/aggregate_activity_metrics.py \
  --territory AEROSPACE_AND_DEFENSE_ENT_POD_TERR03 \
  --identities scoped-identities.json \
  --out territory-metrics.json
```

> **Do not query the `account` object directly.** The `account` object has no validated server-side name filter. An unfiltered account query dumps metrics for every account in the tenant, causing multi-minute timeouts and wasted API quota. The `activity` object with `$in` filter is the only correct approach for scoped portfolio metrics.

Then use `scripts/build_portfolio.py` to assemble the base portfolio from registry, identities, and metrics:

```bash
python scripts/build_portfolio.py \
  --territory AEROSPACE_AND_DEFENSE_ENT_POD_TERR03 \
  --identities scoped-identities.json \
  --metrics territory-metrics.json \
  --out portfolio-base.json
```

Preserve the hard rules from `sales-data-explorer`:

- Only validated slugs from the catalog.
- Server-side filters only where explicitly supported.
- If a tenant silently drops a requested column, fail that packet rather than delivering partial data.
- Query API output is metrics and records, not AI narrative.

Default portfolio metrics (aggregated by `aggregate_activity_metrics.py`):

- account name
- engagement level
- last meeting date
- upcoming meetings next 14 days
- meetings in last 30 and 90 days
- emails sent in last 30 days
- executive activities in last 30 days
- open opportunity count
- open opportunity amount this quarter
- account owner

### 4. Compute deterministic portfolio priority

Before MCP enrichment, calculate a transparent `internal_priority_score` from available metrics. Keep the score explainable.

Default components:

- engagement level: 25%
- recent executive activity: 20%
- open opportunity presence/value: 20%
- recent meeting/activity momentum: 15%
- no upcoming meeting despite meaningful engagement: 10%
- recency of last meaningful activity: 10%

Missing fields reduce confidence; they must not be treated as zero evidence without a caveat.

The deterministic score is for internal triage only. It determines which accounts receive deep enrichment and in what order. It is **not** the user-facing score.

The user-facing metric is `signal_score`, computed by `enrich_portfolio.py` as the average of all per-signal scores for each account (or `null` if no signals). This is the score shown in the spreadsheet, HTML view, and any summary KPIs.

### 5. Backstory MCP enrichment

Default: top `5` accounts by deterministic priority, maximum `10`. Also include any account explicitly requested by the user. Only enrich accounts with `identity.match_status == "matched"`.

#### 5a. Collect MCP data

For each selected account, call MCP tools:

1. `get_account_status(peopleai_account_id)` -- returns risks, next steps, topics (30-day window, unstructured prose).
2. `get_recent_account_activity(peopleai_account_id)` -- returns summarized emails and meetings (30-day window, unstructured prose).
3. `account_company_news(peopleai_account_id)` -- for publicly traded companies only. Returns categorized filings and news (structured array).
4. `ask_sales_ai_about_account(question, peopleai_account_id)` -- only when the question cannot be answered from free calls, and only within the credit rules of `sales-insights`.

#### 5b. Synthesize into structured enrichment

MCP responses are unstructured prose. The orchestrator must synthesize each account's responses into structured enrichment data and write `mcp-enrichment.json`:

```json
{
  "<peopleai_account_id>": {
    "status": {
      "risks": ["risk statement 1", "..."],
      "next_steps": ["action item 1", "..."],
      "topics": ["topic 1", "..."]
    },
    "raw_status": "optional: raw get_account_status text",
    "raw_activity": "optional: raw get_recent_account_activity text",
    "summary": "1-3 sentence account narrative combining MCP and metrics context",
    "recommended_next_move": "single actionable next step for the account team",
    "signals": [
      {
        "disposition": "KEEP",
        "score": 80,
        "headline": "concise factual headline",
        "what_changed": "what happened",
        "why_it_matters": "business impact",
        "red_hat_relevance": "specific Red Hat relevance",
        "recommended_action": "what to do",
        "source_type": "backstory_mcp",
        "confidence": "high"
      }
    ]
  }
}
```

#### 5c. Merge enrichment into portfolio

Use `scripts/enrich_portfolio.py` to merge the synthesized MCP data into the base portfolio:

```bash
python scripts/enrich_portfolio.py \
  --portfolio portfolio-base.json \
  --mcp-data mcp-enrichment.json \
  --out portfolio.json
```

The script fills each enriched account's `internal.risks`, `internal.next_steps`, `internal.topics`, `summary`, `recommended_next_move`, and `signals`. It updates the envelope metadata (`accounts_enriched`, `mcp_status`, signal counts, caveats).

Preserve source windows:

- Free MCP status/activity/people: 30 days.
- Explicit SalesAI questions: up to 90 days.
- Query API metrics: requested window up to 365 days.

Do not claim that MCP covered all accounts. Record `accounts_enriched` separately from `accounts_in_scope`.

### 6. External research

External research runs by default (`external_research=true`). Skip only when the user explicitly opts out.

Follow the guidance in [`RESEARCH.md`](RESEARCH.md). Research runs on accounts selected for deep enrichment (step 5) unless the user explicitly requests broader scope.

**Parallelization:** When researching multiple accounts, use parallel subagents (one per account) to reduce wall-clock time. Each subagent receives the account name, identity, research objective, and the RESEARCH.md guidance, and returns signals conforming to the portfolio schema. The orchestrator merges all returned signals into the portfolio after all subagents complete.

Key rules (see `RESEARCH.md` for full guidance):

- `source_type = external_public`
- Every signal must have a non-null `source_url`
- Preserve URL, publisher, and published date
- Separate evidence from model inference
- Check Backstory `account_company_news` results before searching for the same financial events
- Stop when searches yield nothing relevant; zero signals is a valid outcome

### 7. Synthesize External Monitor outputs

Produce `portfolio.json` conforming to `schemas/portfolio-output.schema.json`.

The portfolio summary must answer:

- Which accounts need attention now?
- Why are they prioritized?
- What internal account context supports that prioritization?
- What action should the account team take next?
- What is known versus inferred?

The account view must be concise and action-oriented. Avoid long narrative dumps from MCP responses.

### 8. Render and export

A complete run produces three output files from the final `portfolio.json`:

```bash
python scripts/render_portfolio.py portfolio.json --out external-monitor-portfolio.html
python scripts/export_sheets.py portfolio.json --out external-monitor-portfolio.xlsx
```

- `portfolio.json` -- machine-readable artifact, validated against the schema.
- `portfolio.html` -- single-file interactive HTML for browser viewing.
- `portfolio.xlsx` -- formatted spreadsheet with Portfolio and Signals tabs.

Rendering must not require one page per account. The same JSON drives all three outputs.

## Output rules

- Return strict JSON for automation; prose is generated only in the interface.
- Every account retains the Enterprise Accounts `account_id`.
- Every enriched account records People.ai resolution status and `peopleai_account_id` when available.
- Metrics, MCP narratives, and external signals retain separate provenance.
- Never present missing data as negative account behavior.
- Never claim complete coverage when only a subset was enriched.
- Preserve caveats and time windows in `_meta`.

## Failure modes

- **No accounts in scope** → stop; report exact scope.
- **Ambiguous account match** → mark ambiguous; do not enrich silently.
- **Query API column drop** → fail the packet; use the nearest validated alternative only when explicitly documented.
- **MCP unavailable** → still produce Query API portfolio output with `mcp_status = unavailable`.
- **MCP account not found** → preserve Query API data and mark account resolution failure.
- **Credit cap reached** → stop credit calls and finish with free data.
- **Thin 30-day MCP context** → consult longer Query API metrics before labeling the account inactive.

## Verification checklist

Before delivery:

- Scope and account count are correct.
- Query API packet used validated fields.
- No silent column-drop warning was ignored.
- Accounts in scope and accounts enriched are separately reported.
- Every deep account has resolution status.
- Time windows are explicit.
- JSON validates against the schema.
- HTML filters work for GEO, region, pod, territory, and account.
- Account drill-down uses the same data artifact as Portfolio View.
