---
name: external-monitor-account-intelligence
description: Build External Monitor portfolio and account intelligence for a selected GEO, region, pod, territory, or account. Resolve the account population from the Enterprise Accounts dataset, batch-pull validated People.ai/Backstory Query API metrics, selectively enrich priority accounts through Backstory MCP, and produce a strict JSON artifact for the External Monitor Portfolio View and Account View. Use when the user asks to research a scope of enterprise accounts, generate a portfolio briefing, identify accounts needing attention, or refresh the External Monitor interface.
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

- `scope_type`: `geo | region | pod | territory | account`
- `scope_value`: exact value from the Enterprise Accounts dataset
- Enterprise Accounts records containing at minimum:
  - `account_id`
  - `account_name`
  - `geo`
  - `region`
  - `pod` when available
  - `territory_name`
  - `segment`

Optional:

- `lookback_days` for Query API metrics, default `120`, maximum `365`
- `deep_enrichment_limit`, default `5`, maximum `10`
- `external_research`: boolean, default `false`
- `research_objective`: user-specific prioritization objective

## Procedure

### 1. Resolve the account population

Read the Enterprise Accounts dataset and select only records matching the requested scope.

- GEO → `geo == scope_value`
- Region → `region == scope_value`
- Pod → `pod == scope_value`
- Territory → `territory_name == scope_value`
- Account → exact `account_name` or stable `account_id`

Do not infer hierarchy values. Preserve blank pod/region values as source limitations.

If no accounts match, stop and report the exact scope used.

### 2. Normalize account identity

Create an identity record per account:

```json
{
  "account_id": "local stable id",
  "account_name": "source account name",
  "crm_id": null,
  "peopleai_account_id": null,
  "match_status": "unresolved"
}
```

Preferred matching order:

1. Salesforce/CRM ID when available.
2. Exact normalized account name.
3. Backstory `find_account` confirmation.
4. Explicit alias supplied by the user.

Never silently merge ambiguous accounts. Mark them `ambiguous` and exclude them from deep enrichment until resolved.

### 3. Run the batch Query API pass

Use `sales-data-explorer` and its validated catalog. Preserve its hard rules:

- Only validated slugs.
- Server-side filters only where explicitly supported.
- Batch account names with `ootb_activity_account_name $in [...]` when pulling activity records.
- If a tenant silently drops a requested column, fail that packet rather than delivering partial data.
- Query API output is metrics and records, not AI narrative.

Default portfolio metrics should include, where tenant-enabled:

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

Use the Query API for the entire selected account set. Do not issue one request per account when fields share the same object and window.

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

The deterministic score is for triage only. It is not the final External Monitor signal score.

### 5. Select accounts for Backstory MCP enrichment

Default: top `5` accounts by deterministic priority, maximum `10`.

Also include any account explicitly requested by the user.

For each selected account:

1. `find_account(account_name)` or `find_record_by_crm_id(crm_id)`.
2. Free calls first:
   - `get_account_status`
   - `get_recent_account_activity`
   - `get_engaged_people`
   - `account_company_news` when relevant
3. Use `ask_sales_ai_about_account` only when the requested question cannot be answered from free calls and only within the documented credit rules of `sales-insights`.

Preserve source windows:

- Free MCP status/activity/people: 30 days.
- Explicit SalesAI questions: up to 90 days.
- Query API metrics: requested window up to 365 days.

Do not claim that MCP covered all accounts. Record `accounts_enriched` separately from `accounts_in_scope`.

### 6. Optional external research

When `external_research=true`, research only the accounts selected for deep enrichment unless the user explicitly requests full-scope external research.

External research must remain distinguishable from People.ai/Backstory content:

- `source_type = external_public`
- preserve URL, publisher, and published date
- separate evidence from model inference

### 7. Synthesize External Monitor outputs

Produce `portfolio.json` conforming to `schemas/portfolio-output.schema.json`.

The portfolio summary must answer:

- Which accounts need attention now?
- Why are they prioritized?
- What internal account context supports that prioritization?
- What action should the account team take next?
- What is known versus inferred?

The account view must be concise and action-oriented. Avoid long narrative dumps from MCP responses.

### 8. Render

Use `scripts/render_portfolio.py` with `templates/portfolio.html`:

```bash
python3 scripts/render_portfolio.py portfolio.json --out external-monitor-portfolio.html
```

The same JSON can also be written into Google Sheets backend tabs later. Rendering must not require one page per account.

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
