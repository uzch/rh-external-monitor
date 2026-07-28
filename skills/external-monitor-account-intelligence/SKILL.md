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

- `scope_type`: `geo | region | pod | territory | account` (pod is defined in the schema but not yet implemented in registry scripts)
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

#### Large scopes and MCP access

For every scope, resolve cached identities first. `find_account` requires the OAuth session in the main agent process, so subagents must not make identity-resolution MCP calls. The main agent resolves uncached accounts sequentially, using the `name_variations` emitted by `resolve_identities.py` to minimize attempts.

For a large region or GEO, divide the unresolved account list into review batches of about 20 so progress and failures are easy to track. This is an operational grouping only, not permission to parallelize MCP calls. If MCP is unavailable, a runner may use a supported People.ai REST or Query API fallback and parallelize only work that does not rely on the session-bound MCP connection.

#### Identity cache

Before calling `find_account`, always check the persistent identity cache:

```bash
python scripts/resolve_identities.py \
  --accounts scoped-accounts.json \
  --cache data/local/identity-cache.json \
  --out identities.json
```

The script emits cached identities immediately and marks uncached accounts as `needs_resolution` with normalized name variations to try. Only accounts needing resolution require `find_account` calls.

After resolving new identities, persist them back to the cache:

```bash
python scripts/resolve_identities.py \
  --update-cache data/local/identity-cache.json \
  --resolved identities.json
```

#### MCP unavailable fallback

Backstory MCP tools (`find_account`, etc.) require an authenticated OAuth session bound to the main Claude Code process. They are **not available to subagents** and may be lost when sessions are continued.

When MCP is unavailable for identity resolution:

1. Run `resolve_identities.py` with the cache -- this resolves all previously seen accounts without any MCP calls.
2. For uncached accounts, use the People.ai Query API `accounts` endpoint as a fallback: query by name variations from the script output.
3. After resolution, always update the cache so the next run skips MCP entirely for these accounts.

When MCP is available but only in the main session:

1. Resolve uncached accounts sequentially from the main session (not via subagents). Use the `name_variations` array from `resolve_identities.py` output to minimize `find_account` attempts.
2. Update the cache after resolution.

### 3. Run the batch Query API pass

**Always use `scripts/aggregate_activity_metrics.py`.** This script queries the `activity` object with a server-side `ootb_activity_account_name $in [...]` filter, scoped to only the accounts in your identity map. It then aggregates per-account metrics client-side. The script handles any scope size internally -- it batches the `$in` filter into groups of 50 account names, runs one Query API call per batch (2 HTTP requests each against the ~100/hr rate limit), and merges the results before aggregation.

```bash
python scripts/aggregate_activity_metrics.py \
  --region WEST \
  --identities west-identities.json \
  --out west-metrics.json
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

Default portfolio metrics (aggregated by `aggregate_activity_metrics.py` from the `activity` object):

- account name
- total activities
- meeting count (30d and 90d)
- email count (30d)
- most recent activity date
- outbound and inbound activity counts
- linked opportunity count and names
- activity trend (increasing, stable, declining)

The following fields are **unavailable** from the activity object and are set to null with a caveat: engagement level, executive activity, opportunity amount, opportunity stage, account owner. These would require querying different People.ai objects not currently supported.

### 4. Compute deterministic portfolio priority

Before MCP enrichment, calculate a transparent `internal_priority_score` from available metrics. Keep the score explainable.

Default components (four equal-weight buckets, 0-25 each, total 0-100):

- volume (0-25): total activities normalized to the scope maximum
- opportunities (0-25): count-based tiers (0=0, 1=10, 2-5=15, 6-20=20, 21+=25)
- momentum (0-25): activity trend (increasing=25, stable=15, declining=10)
- recency (0-25): days since most recent activity (7d=25, 14d=20, 30d=15, 60d=10, 90d=5, >90d=0)

Accounts with unavailable metrics receive a score of 0 with a caveat noting the reason.

The deterministic score is for internal triage only. It determines which accounts receive deep enrichment and in what order. It is **not** the user-facing score.

The user-facing metric is `signal_score`, computed as the integer average of all per-signal scores for each account (or `null` if no signals). Both `enrich_portfolio.py` and `merge_external_signals.py` recompute this value, so it reflects all signals regardless of source. This is the score shown in the spreadsheet, HTML view, and any summary KPIs.

### 5. Backstory MCP enrichment

Default: top `5` accounts by deterministic priority, maximum `10`. Also include any account explicitly requested by the user. Only enrich accounts with `identity.match_status == "matched"`.

#### MCP collection and synthesis

The main authenticated agent collects all MCP data. For each selected account, it receives the account identity record, base-portfolio metrics, and any research objective, then makes the free MCP calls below. OAuth does not propagate to subagents, so they must not make these calls.

After the main agent has collected raw responses, it may delegate only the offline synthesis of those responses into the structured format in 5b. The orchestrator combines those records into one `mcp-enrichment.json`, then runs `enrich_portfolio.py` in 5c.

Credit calls (`ask_sales_ai_about_account`) are never delegated. The orchestrator reviews the free-tier results, decides whether credit calls are needed, announces the cost to the user, and runs them directly. Maximum 10 credit calls per run (see `sales-insights` credit rules).

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
        "disposition": "ACT",
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

#### MCP unavailable fallback

MCP tools are bound to the main Claude Code session's OAuth and are **not available to subagents**. When MCP tools are unavailable:

**Option A (preferred when MCP is available in the main session):** The orchestrator makes all MCP calls sequentially from the main session, collects the raw responses, then passes them to parallel subagents for synthesis into the structured format (5b). This preserves parallelism for the synthesis work while working within the OAuth constraint.

**Option B (MCP entirely unavailable):** Skip MCP enrichment. Set `mcp_status = "unavailable"` in the portfolio envelope. Proceed directly to external research (step 6), which uses WebSearch and does not require MCP tools. The portfolio remains valid without MCP data -- it just lacks internal narrative context (risks, next_steps, topics, summary from Backstory).

When using Option B, `enrich_portfolio.py` should not be run with empty MCP data. Instead, proceed to external research and merge only external signals using `merge_external_signals.py`.

### 6. External research

External research runs by default (`external_research=true`). Skip only when the user explicitly opts out.

Follow the guidance in [`RESEARCH.md`](RESEARCH.md). Research runs on accounts selected for deep enrichment (step 5) unless the user explicitly requests broader scope.

**Parallelization:** When researching multiple accounts, use parallel subagents to reduce wall-clock time. Each subagent receives account names, identities, internal metrics context, research objective, and the RESEARCH.md guidance, and returns signals conforming to the portfolio schema. Each subagent writes its results to a `research-batch-NN.json` file.

For large scopes (20+ accounts), batch ~5 accounts per subagent to reduce subagent count while keeping wall-clock time reasonable. For tighter time budgets, use a focused research brief (2-3 targeted queries per account instead of open-ended exploration).

#### Internal context in research prompts

**The orchestrator must extract internal metrics context from the portfolio base and include it in every research subagent prompt.** This is what makes signal assessments relationship-aware rather than generic.

For each account in a research batch, extract and pass:

1. **Product footprint** -- the `linked_opportunity_names` array. This tells the subagent which Red Hat products the account uses or is evaluating.
2. **Renewal pipeline** -- count of opportunities starting with "Renewal -" and their names. Upcoming renewals are churn risk when paired with negative external signals.
3. **Activity summary** -- `total_activities`, `meeting_count_30d`, `email_count_30d`.
4. **Engagement direction** -- `outbound_count` vs `inbound_count`. The ratio reveals whether Red Hat is chasing the account or the account is engaged.
5. **Activity trend** -- `activity_trend` ("increasing", "stable", "declining").
6. **Opportunity count** -- `linked_opportunity_count`.

Example prompt fragment per account:

```
APPLE INC. (peopleai_account_id: 18361613631)
RH product footprint: Ansible (2 opps), OpenShift Virtualization (3 opps), RHEL (multiple + 6 renewals approaching), Lightwell, OCP, Swift language support
Activity: 1,908 total | 6 meetings last 30d | 243 emails last 30d
Engagement direction: outbound-heavy (1,654 out vs 254 in)
Trend: declining | Open opportunities: 24

Ground your red_hat_relevance and recommended_action in this context.
Reference specific products, renewals, and engagement patterns when they connect to the external signal.
```

The subagent uses this context as described in RESEARCH.md "Internal relationship context" section. Without this context, signal assessments default to generic industry advice that provides no intelligence value.

When `metrics_status` is not `available` for an account, pass only the account name and note that internal metrics are unavailable. The subagent will use generic assessments for that account.

After all subagents complete, merge signals using `merge_external_signals.py`:

```bash
python scripts/merge_external_signals.py \
  --portfolio portfolio-base.json \
  --research-dir output/run-name/ \
  --out portfolio.json
```

**Always use `merge_external_signals.py` for signal merging.** Do not merge signals with inline code. The script handles integer rounding of `signal_score`, correct envelope field names (`act_count`/`watch_count`), disposition counting, and schema-compliant `signal_id` generation.

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
