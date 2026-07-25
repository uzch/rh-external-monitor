# External Research Guidance

This document guides external web research for the External Monitor portfolio. It is referenced by SKILL.md step 6.

External research is additive intelligence that layers on top of People.ai Query API metrics and Backstory MCP context. It uses Claude's web search and fetch capabilities to find publicly available signals relevant to account prioritization.

## When external research runs

External research runs by default (`external_research=true`). It is skipped only when the user explicitly opts out.

It runs AFTER:

1. Registry account population is resolved.
2. Query API activity metrics are collected.
3. Deterministic priority scoring is computed.
4. Backstory MCP enrichment is complete for selected accounts.

External research is the last intelligence step before portfolio synthesis.

## Scope behavior

**Default:** Research only the accounts selected for Backstory MCP enrichment (top N by priority, controlled by `deep_enrichment_limit`).

**User override:** If the user names specific accounts for research, include them regardless of priority rank.

**Pre-resolved list:** If the caller provides a list of accounts with resolved identities, research those directly.

**Large scopes (region, GEO):** Do not research all accounts. Use the enrichment limit. The priority ranking determines which accounts receive research.

## What to look for

Search for publicly available events that would affect how Red Hat should engage with the account. Useful signal categories include but are not limited to:

- Leadership changes (CTO, CIO, VP Engineering, CISO appointments or departures)
- Mergers, acquisitions, divestitures, or spinoffs
- Partnerships or strategic alliances (especially technology partnerships)
- Competitive wins or losses (especially involving Red Hat competitors or adjacent platforms)
- Technology adoption announcements (cloud migration, containerization, automation, AI/ML infrastructure)
- Financial events not covered by Backstory company news (funding rounds for private companies, restructuring, cost-cutting)
- Regulatory, legal, or compliance developments affecting IT strategy
- Major contract awards (especially government/defense for relevant accounts)
- Layoffs or hiring surges in technology roles

This is guidance, not a checklist. Follow leads. If a search reveals an unexpected but relevant signal, include it.

## Interaction with People.ai company news

Backstory's `account_company_news` tool covers SEC filings (8-K, 10-K) and earnings calls for publicly traded companies. It is a `backstory_mcp` source.

Before searching for financial events on a public company, check whether `account_company_news` already returned that information during MCP enrichment. Do not create an `external_public` signal that duplicates a `backstory_mcp` signal for the same event.

External research adds value when it covers:

- Events Backstory does not monitor (press coverage, blog posts, analyst reports, product launches, partnership announcements)
- Private companies (Backstory company news returns nothing for private companies)
- Recent events not yet reflected in SEC filings
- Industry context that affects the account but is not account-specific in Backstory

## Source quality and provenance

Every external signal must have:

- `source_type: "external_public"`
- `source_url`: the URL of the primary source (required, non-null)
- `published_at`: publication date when available (ISO 8601)

Set `confidence` based on source reliability:

- **high**: primary source (company press release, SEC filing, official announcement) with a working URL
- **medium**: secondary reporting (trade press, analyst coverage, reputable news outlet) with a working URL
- **low**: indirect evidence (social media, forum posts, inference from job postings or patent filings)

Do not fabricate URLs. If you cannot find a working source URL for a claim, do not create a signal for it.

Preserve the distinction between evidence and interpretation:

- `headline` and `what_changed`: factual description of the event
- `why_it_matters` and `red_hat_relevance`: your assessment of impact and relevance
- `recommended_action`: what the account team should consider doing

## Relevance judgment

A signal is worth including if it would change how the account team prioritizes or engages with the account. Ask:

- Does this event create or threaten a technology buying decision?
- Does this affect the account's IT strategy, budget, or organizational structure?
- Does this change who Red Hat should be talking to at the account?
- Would the account team want to know this before their next meeting?

If the answer to all of these is no, do not include it.

Prefer recent signals (last 90 days). Older events are relevant only if their impact is ongoing or not yet reflected in internal data.

## When to stop

- If the first 2-3 searches for an account yield nothing relevant, stop researching that account. Not every account has newsworthy events.
- Do not pad results. Zero external signals for an account is a valid outcome.
- Do not generate signals from generic industry trends unless they specifically name or directly affect the account.

## Output structure

External research produces signal objects that conform to the portfolio schema (`schemas/portfolio-output.schema.json`). Each signal includes:

```json
{
  "signal_id": "ext-<account_id>-<sequential>",
  "disposition": "KEEP or WATCH",
  "score": 0-100,
  "headline": "Concise factual headline",
  "what_changed": "What happened",
  "why_it_matters": "Why this matters for the account relationship",
  "red_hat_relevance": "Specific relevance to Red Hat products or engagement",
  "recommended_action": "What the account team should consider",
  "source_type": "external_public",
  "source_url": "https://...",
  "published_at": "2026-07-15",
  "confidence": "high or medium or low"
}
```

Signals attach to the account's `signals` array in `portfolio.json`. They are validated by the same schema as all other signals.

## Parallelization

When the orchestrator researches more than one account, it should spawn one subagent per account. Each subagent receives the account name, identity record, research objective (if any), and follows this research guidance independently. The orchestrator merges all returned signals into the portfolio after all subagents complete.

This reduces wall-clock time from O(N * search_time) to O(max_search_time) and is the expected execution model for multi-account research.

## Research objective

If the user provides a `research_objective`, use it to focus the research. For example, if the objective is "identify accounts evaluating container platforms," weight container and Kubernetes-related signals higher. The objective guides relevance judgment, not search terms.
