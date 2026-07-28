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

**URL verification rules:**

- The `source_url` must be the URL of a specific article, press release, filing, or post -- not a topic index, tag archive, search results page, or site homepage. A URL like `example.com/guides/topic/` that lists hundreds of articles is not a source for any specific claim.
- You must have actually loaded the page (via WebFetch or equivalent) and confirmed it contains the claim before citing it. Constructing a URL from a search snippet without visiting it produces 404s and fabricated citations.
- If a search result describes a real event but the linked page is a 404, a paywall with no content, or an archive/index page, do not create a signal for that event. The information may be real but you cannot cite it.
- Never reuse the same URL across multiple signals unless the page genuinely contains both claims.

Preserve the distinction between evidence and interpretation:

- `headline` and `what_changed`: factual description of the event
- `why_it_matters` and `red_hat_relevance`: your assessment of impact and relevance
- `recommended_action`: what the account team should consider doing

## Internal relationship context

Research subagents receive internal metrics context alongside the account name. This context comes from the portfolio base (People.ai Query API data) and represents Red Hat's existing relationship with the account. **Use it to ground every signal's `red_hat_relevance` and `recommended_action` in the actual relationship, not generic advice.**

The orchestrator provides:

- **Product footprint** -- linked opportunity names showing which Red Hat products the account uses or is evaluating (Ansible, OpenShift, RHEL, Lightwell, etc.)
- **Renewal pipeline** -- opportunities starting with "Renewal -" that represent upcoming contract renewals
- **Activity volumes** -- total activities, meetings last 30d, emails last 30d
- **Engagement direction** -- outbound vs inbound counts. High outbound with low inbound means Red Hat is chasing; high inbound means the account is engaged
- **Activity trend** -- "increasing", "stable", or "declining"
- **Opportunity count** -- total open opportunities

### How to use internal context

The internal data should shape your thinking, not be the content. The reader can already see the activity numbers and opportunity count in the sidebar. Do not restate them. Instead, use them to arrive at a sharper insight that the reader could not reach on their own.

**The anti-pattern (do not do this):**

> `why_it_matters`: "With 24 open opportunities, 7 approaching renewals, and a declining/outbound-heavy engagement pattern, this transition creates both risk and opportunity."

This restates the metrics with the event bolted on. It tells the reader nothing new.

> `recommended_action`: "Prepare renewal defense briefs for all 7 approaching renewals before the Sept 1 transition."

This is generic account management advice. You would say this regardless of the external signal.

**The correct pattern:**

> `why_it_matters`: "Ternus comes from hardware engineering with no public track record on enterprise IT vendor strategy. Apple's IS&T organization -- where the OpenShift Virtualization and Ansible deals live -- may lose whatever executive air cover it had under Cook."

> `recommended_action`: "The Crypto Services renewal (Chait/Noll) is the most exposed -- it's a niche engagement unlikely to survive a vendor consolidation review. Get it signed before Sept 1. For the IS&T deals, identify who in Ternus's new org inherits infrastructure vendor decisions."

The difference: internal data was used to reason about which specific deals are at risk and why, not to recite the numbers.

**Rules:**

- Never quote activity counts, opportunity counts, or outbound/inbound ratios in signal text. The reader sees these in the sidebar. Restating them is noise.
- Never write "with X opportunities and Y renewals" as a framing clause. Get to the insight.
- Use opportunity names to identify *which* deals are specifically affected by the external event, not to list them.
- Use engagement direction and trend to shape the *type* of recommended action (e.g., change approach vs. capitalize on momentum), not to describe the current state.
- If the recommended action would be the same without the external signal, it is not signal-driven. Rewrite it to explain what the external event specifically changes about what the team should do.

### When internal context is absent

If the orchestrator does not provide internal metrics context (e.g., the account has `metrics_status: unavailable_identity`), fall back to generic assessments. Mark these with lower confidence when the signal's relevance depends on knowing the existing relationship.

## Relevance judgment

A signal is worth including if it would change how the account team prioritizes or engages with the account. Ask:

- Does this event create or threaten a technology buying decision?
- Does this affect the account's IT strategy, budget, or organizational structure?
- Does this change who Red Hat should be talking to at the account?
- Would the account team want to know this before their next meeting?
- **Does this event interact with the account's existing Red Hat product footprint or renewal pipeline?**

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
  "disposition": "ACT or WATCH",
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
