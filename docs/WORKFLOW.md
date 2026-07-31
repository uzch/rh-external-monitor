# Technical workflow walkthrough

This walkthrough follows the detailed flow in [`ARCHITECTURE.md`](ARCHITECTURE.md). It explains how a requested scope becomes a validated `portfolio.json` without treating any single source as complete account intelligence.

The workflow is file based. A skill directs the agent through the sequence, connected tools supply information that scripts cannot determine alone, and scripts make the durable state changes. Each output belongs in a distinct, named subfolder under `output/`; do not flatten run artifacts or commit customer data.

## The run inputs and authorities

| Input or authority | Role in the run |
|---|---|
| User request | Supplies a scope type and value, optional Query API lookback, optional research objective, and any explicit accounts to include. |
| Enterprise Accounts registry | Establishes the authoritative account population and organizational assignment. It is not intelligence. |
| External Monitor skill | Defines sequence, selection bounds, evidence rules, and fallbacks. It is a guide for the agent runtime, not a program or service. |
| People.ai source skills | Define validated Query API behavior, authentication, rate limits, and MCP capabilities. |
| Agent | Performs connected identity lookup, MCP collection and synthesis, and public-source research where authorized. |
| Python scripts | Filter, aggregate, join, score, merge, validate, and render files deterministically. |

The normal artifact chain is:

```text
scoped-accounts.json
  -> identities.json
  -> metrics.json
  -> portfolio-base.json
  -> mcp-enrichment.json and research-batch-*.json
  -> portfolio.json
  -> portfolio.html and portfolio.xlsx
```

Artifact names are conventional, not hard-coded contracts. `portfolio.json` is the canonical downstream contract; the prior JSON files make a run inspectable and recoverable.

## 1. Interpret the request

The agent translates a request into a supported registry scope and run options:

- Scope: GEO, region, territory, or account are implemented by the registry scripts.
- Lookback: Query API activity window, default 120 days and capped at 365 days by the orchestration guidance.
- Deep enrichment: default 5 accounts and maximum 10.
- External research: enabled by default unless the user explicitly opts out.
- Research objective: an optional lens for relevance, not permission to override evidence rules.

The schema and HTML template understand `pod`, but the current registry loader and base-portfolio builder do not implement pod selection. A request for pod scope is an implementation gap, not an alternate spelling of segment or territory.

## 2. Establish registry scope

`scripts/load_registry.py` reads `data/local/Enterprise Accounts.csv`, verifies the required source columns, normalizes them into the five canonical fields, and filters by the supplied scope:

| Registry source column | Output field |
|---|---|
| `account_sales_group_name` | `account_name` |
| `geo` | `geo` |
| `region` | `region` |
| `segment` | `segment` |
| `ACCOUNT_TERRITORY_NAME` | `territory_name` |

The output is usually saved as `scoped-accounts.json`. An empty result is a stop condition. Do not replace a missing registry with MCP output or an unfiltered Query API request: both would change the account population and conceal accounts with no recent activity.

## 3. Prepare and resolve identities

Registry naming and People.ai naming are not interchangeable. In particular, the Query API uses case-sensitive account-name matching, while registry names can be all caps. Passing an unresolved all-caps registry name to the Query API can return an incorrect silent zero.

`scripts/resolve_identities.py` is cache aware:

1. It reads `scoped-accounts.json` and optional `data/local/identity-cache.json`.
2. It emits cached identities immediately.
3. For uncached accounts, it generates title-cased, legal-suffix, and regional-suffix variations and marks the record `needs_resolution`.
4. After a connected lookup has confirmed an identity, its update mode merges confirmed records back into the cache.

The script does **not** call People.ai remotely. The authenticated main agent uses the available People.ai identity capability, normally `find_account`, to populate:

- `query_account_name`: canonical People.ai name used by Query API filters.
- `peopleai_account_id`: identifier used by account-specific Backstory MCP tools.
- `identity_status`: confirmed, resolved alias, ambiguous, or not found.

Ambiguous identities remain ambiguous. They are not deeply enriched or silently merged. MCP OAuth is bound to the main agent process, so spawned subagents cannot perform `find_account` calls. If MCP is unavailable, use the documented People.ai API fallback only when it is available and authorized; otherwise preserve the unresolved status and continue with explicit missing-data caveats.

## 4. Prepare and execute bounded Query API packets

`scripts/aggregate_activity_metrics.py` owns the External Monitor activity-metric requirements. It accepts the scoped registry and identities, chooses only `confirmed` or `resolved_alias` identities, and uses their canonical `query_account_name` values.

For each bounded batch of up to 50 account names, it builds an `activity` packet with two server-side constraints:

- `ootb_activity_account_name` is filtered with `$in` using the canonical names.
- `ootb_activity_timestamp` is filtered with `$gte` using the requested lookback start.

The script then invokes `skills/people-ai/sales-data-explorer/scripts/run_query.py`. The separation matters:

- `aggregate_activity_metrics.py` defines the External Monitor product query, batching, and per-account output behavior.
- `run_query.py` validates requested slugs against the People.ai catalog, loads credentials, authenticates, executes the export, writes CSV, and fails when the tenant silently drops a required column.

Never replace this lane with an unfiltered `account` query. The source skill documents that account-name filtering is not validated on that object, and an unrestricted request can retrieve tenant-wide data or time out.

## 5. Aggregate activity into account metrics

After each Query API batch returns, `aggregate_activity_metrics.py` reads the CSV, deduplicates activity rows by UID, and groups activities by canonical account name. It calculates metrics such as:

- Total activities.
- Meetings and emails across the configured windows.
- Inbound, outbound, internal, and external activity counts.
- Most recent activity date and type.
- Activity-type counts and linked opportunity names.
- A recent activity trend based on the 30-day and 31-to-60-day windows.

Every registry account remains represented in `metrics.json`. The script differentiates available metrics, no activity in the window, unavailable identity, and query failure. Fields unavailable from this activity-object lane remain `null` with an explicit list of unavailable fields. Missing data is never converted to zero.

## 6. Build the base portfolio

`scripts/build_portfolio.py` joins registry rows, identities, and metrics by registry account name. It creates the schema-shaped account records and saves `portfolio-base.json`.

The base artifact contains hierarchy, identity status, internal metrics, priority reasons, and empty narrative and signal collections. It is intentionally a partial portfolio: it has internal activity evidence but not agent interpretation, MCP narrative, or public signals.

### Deterministic internal priority

`build_portfolio.py` computes `internal_priority_score` from four equally weighted components:

| Component | Inputs | Purpose |
|---|---|---|
| Volume | Total activities relative to the scope maximum | Identifies relative interaction level. |
| Opportunities | Count of linked opportunity names | Adds a bounded opportunity-count signal. |
| Momentum | Activity trend | Distinguishes increasing, stable, and declining recent activity. |
| Recency | Most recent activity date | Rewards more recent internal activity. |

This score chooses the order and scope of deeper enrichment. It is deterministic triage, not a measure of deal quality, customer intent, renewal probability, strategic importance, or ownership. Accounts without available metrics receive a score of zero with a reason explaining the metric status.

`signal_score` is different. It is calculated later as the rounded average of scored signals, is used in portfolio presentation, and is `null` when an account has no scored signals. See [`DATA_MODEL.md`](DATA_MODEL.md) for the exact contract paths.

## 7. Collect and structure Backstory MCP enrichment

The skill selects the highest-priority matched accounts for deeper enrichment, normally 5 and never more than 10 unless the workflow rules are changed. The main authenticated agent makes the MCP calls because OAuth does not propagate to subagents.

The normal free MCP pass may collect account status, recent account activity, and company news where applicable. The agent turns the raw, semi-structured responses into `mcp-enrichment.json`, keyed by `peopleai_account_id`, with bounded fields such as:

- Risks, next steps, and topics.
- Short summary and recommended next move.
- MCP-derived signals with source type and confidence.

Credit-consuming `ask_sales_ai_about_account` calls are controlled by the main agent and require the workflow's explicit credit safeguards. The agent may delegate offline synthesis after raw responses have been collected, but subagents must not make MCP calls.

`scripts/enrich_portfolio.py` matches structured enrichment to the base portfolio, assigns signal IDs, recalculates each account's `signal_score`, and updates run-level counts and MCP metadata. It is the deterministic merge point for MCP material, not a place to interpret raw prose.

If MCP is unavailable, do not fabricate replacement context. The skill permits a Query API portfolio to proceed with `mcp_status = unavailable` and empty MCP fields.

## 8. Research external public evidence

External research is separate from People.ai. It normally follows internal prioritization and, when available, MCP enrichment so the agent can judge a public event against the actual Red Hat relationship rather than write generic market commentary.

`RESEARCH.md` requires the agent to use account context such as linked opportunity names, activity direction, trend, and selected internal narrative to sharpen relevance and the recommended action. A public signal must keep the distinction between:

- `headline` and `what_changed`: source-backed event description.
- `why_it_matters`, `red_hat_relevance`, and `recommended_action`: agent interpretation based on the account context.

The research guide requires a loaded, specific source URL, publisher and publication date when available, and an appropriate confidence level. Search-result snippets, section indexes, and invented links are not evidence. Zero relevant signals is a valid outcome.

Research batches are saved as files such as `research-batch-01.json`. `scripts/merge_external_signals.py` matches their account names to the portfolio, assigns external signal IDs, recomputes `signal_score`, and updates portfolio totals.

## 9. Merge, validate, and render the contract

The default research-enabled path is:

```text
portfolio-base.json + mcp-enrichment.json
  -> enrich_portfolio.py
  -> MCP-enriched portfolio

MCP-enriched portfolio + research-batch-*.json
  -> merge_external_signals.py
  -> portfolio.json
```

## 10. Generate executive summaries

After the signal merge produces the final portfolio, the agent generates AI-authored executive summaries for each hierarchy level and writes them into `summary.group_briefs`. The `_top` key holds the portfolio-level brief; region and territory names hold group-level briefs. The agent also replaces `summary.text` with the `_top` brief so downstream consumers (XLSX export, external integrations) see the AI-authored summary rather than the `build_portfolio.py` placeholder.

This is an agent-driven step — like MCP synthesis and external research, it uses LLM reasoning rather than a deterministic script. See SKILL.md section 7 for the grouping logic, style guidance, and output mechanics.

The HTML template checks `summary.group_briefs` first and falls back to dynamic signal-based generation for portfolios that lack pre-authored briefs. Old portfolios continue to work without this step.

## 11. Validate and render

`scripts/validate_portfolio.py` validates the final file against `schemas/portfolio-output.schema.json`. Structural validation is necessary but not sufficient: the research procedure, not the current schema, enforces that an `external_public` signal has a non-null, verified source URL.

After successful validation:

- `scripts/render_portfolio.py` injects the JSON into `templates/portfolio.html` to produce a self-contained interactive report.
- `scripts/export_sheets.py` writes a workbook with `Portfolio` and `Signals` tabs.

Both outputs consume the same artifact. The template may compute display aggregates and a backward-compatible signal-score fallback, but it is not a second intelligence pipeline.

## Failure behavior and audit checkpoints

| Condition | Required behavior |
|---|---|
| No accounts match scope | Stop and report the exact requested scope. |
| Identity ambiguous or not found | Preserve the status, do not enrich, and retain the account with unavailable metrics. |
| Canonical name still looks unresolved | The metrics script stops unless explicitly overridden, rather than send all-caps names that can produce silent zeros. |
| Query API field is dropped | `run_query.py` fails the packet. Do not deliver a partial column set. |
| Query batch fails | Preserve the affected account as `query_failed` with caveats. |
| MCP unavailable | Continue only with the reduced Query API and optional public-research path, and report MCP coverage honestly. |
| No relevant public evidence | Emit no padded signal. Preserve the reviewed scope outside the signal count. |
| Schema validation fails | Do not render or deliver the artifact as a valid portfolio. |

## Current implementation notes to keep visible

- The orchestration guidance defaults external research to the selected deep-enrichment accounts. `merge_external_signals.py` currently adds a caveat that uses the full portfolio account count. The batch files and run notes, not that generated caveat alone, are the accurate record of research coverage.
- `source_url` is nullable in the JSON Schema and the external merge fills a missing value with `null`; the non-null URL requirement for public signals comes from `RESEARCH.md`. Follow the research rule even when the structure validates.
- `build_portfolio.py` derives `account_id` by slugifying the registry account name. It does not carry a separate registry account-ID field because `load_registry.py` does not emit one.
- The same source skill must be consulted for People.ai API behavior. This walkthrough describes the current orchestration, not a replacement API specification.

## Related documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md): system boundaries and diagrams.
- [`DATA_MODEL.md`](DATA_MODEL.md): field paths, scores, and null conventions.
- [`PROVENANCE.md`](PROVENANCE.md): source separation and evidence policy.
- [`TEMPLATE_DESIGN.md`](TEMPLATE_DESIGN.md): HTML interaction and display behavior.
- [`UI_TESTING.md`](UI_TESTING.md): offline UI regression coverage.
