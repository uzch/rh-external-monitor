---
name: sales-insights
description: AI insight layer over Backstory (formerly People.ai) via the user's own MCP connection — per-account and per-opportunity risks, next steps, and topics, plus a cross-account rollup ("which of my accounts need attention"). Use when the user asks to "summarize risks / next steps on <account or seller's book>", "what's going on with <account>", "roll up insights across <seller>'s accounts", "top themes in my accounts", "any news about <account>", "have we handled a deal situation like this before", or wants narrative insight on top of pulled sales data. Companion to sales-data-pull (which supplies the raw data and account list).
license: Proprietary
metadata:
  version: 0.1.3
---

# Sales Insights (Backstory MCP)

Produces narrative insight — risks, next steps, topics, themes — from Backstory's SalesAI over the
user's **own** MCP connection. No API key, no scripts to run for the core flow; the depth comes from
disciplined tool use and honest windows. Companion skill: `sales-data-pull` (Query API) supplies
counts, activity, and — critically — the *account list*, because **the Backstory MCP cannot
enumerate accounts, opportunities, or users** (no list/filter entry point; verified 2026-07-02).

## Output contract (hard rule)

The answer the user reads is **written prose** in the rollup shape of Procedure step 5 — never raw
JSON, never a pasted tool response, never a code block of tool output. MCP tools return
JSON/markdown wrapped in `result`: that is *input to synthesize from*, not output to show. Files
the scripts write (blob JSON, dashboard HTML) are artifacts to hand over **by path**; the reply
itself is always the narrative. If the user wants the underlying data, point at the
`sales-data-pull` JSON file — don't inline it.

## Prerequisite

A connected Backstory MCP at **`https://mcp.people.ai/mcp`** (the MCP endpoint stays on the
people.ai domain) — never the `backstory.ai` URL, which silently fails OAuth in Claude Code (see
INSTALL.md). Each user connects with their own Backstory login; there is no shared-key mode.

## The honest windows (say them, don't blur them)

| Window | Source | Cost |
|---|---|---|
| Last 30 days | `get_account_status`, `get_recent_*_activity`, `get_engaged_people` | Free |
| 30–90 days | `ask_sales_ai_about_*` — **only if the question explicitly asks** ("review activity older than 30 days, up to 90 days ago") | **SalesAI credits** |
| Up to 365 days | Query API via `sales-data-pull` — counts and activity rows, not narratives | API calls |
| Own windows | `account_company_news` (filings/earnings, ≈ trailing year; public companies only) · `situation_search` (historical similar deals, any age) | Free (probed 2026-07-07) |

The `ask_sales_ai_*` tool descriptions still say 30 days — that is a confirmed doc bug (product,
2026-07-02; verified live same day). Phrase the window explicitly and the 90-day reach works.
Beyond 90 days there is no narrative source: offer the data pull, never fabricate.

## Procedure

1. **Scope.** Prefer the `sales-data-pull` JSON blob (`<Seller> — Sales Data.json`): its
   `account_rollup` ranks accounts by real activity and carries opportunity linkage. No blob? Ask
   for account/opportunity names and resolve each via `find_account` (CRM IDs via
   `find_record_by_crm_id`). `top_records` is a last resort — ~20 records, not exhaustive, max once.
   Never claim to have covered "all accounts" from MCP alone — it cannot list them.
2. **Segment before you spend.** Default scope: **top 10 accounts by in-window activity** (from the
   blob's rollup) or exactly the accounts the user named. A big book (some owners hold 1,000+
   accounts) is never fanned out in full — say what you selected and why.
3. **Free pass first.** Per selected account: `get_account_status` (risks / next steps / topics,
   30d). Add `get_recent_account_activity` when detail is needed, `get_engaged_people` for
   who-is-talking-to-whom, opportunity-scoped variants for named opps. `account_company_news` for
   outside-in signals on a named account — public companies only (private → empty), sourced from
   filings/earnings calls, and big (200+ items on a mega-cap): synthesize the handful relevant to
   the question, never dump the feed. `situation_search` for "have we handled this before" on a
   chosen opportunity — it returns ≤4 historical deals >70% similar with dated actions and
   resolution outcomes; it is a precedent finder, NOT a cross-account topic search (same
   no-enumeration honesty applies), and "no similar situations found" is a valid answer. Show
   this picture before spending anything.
4. **Escalate deliberately.** `ask_sales_ai_about_account`/`_opportunity` only for questions the
   free tier can't answer — history past 30d (explicit window phrasing!), "why", cross-cutting
   analysis. **Credit cap: ≤10 credit-consuming calls per run, and only after telling the user**
   ("this needs N SalesAI credit questions — proceed?"). Report credits used in the output.
5. **Deliver the rollup.** Lead with the cross-account synthesis: "N of M analyzed accounts carry
   outstanding risks: …", then per-account sections (risks / next steps / topics, each traceable to
   a tool response), then **top themes across the book** (recurring topics, exec-engagement
   signals). Close with a **Caveats** block: windows used, accounts analyzed vs owned, credits
   consumed, generated-by-AI provenance note.
6. **Optional — feed the dashboard.** `python scripts/merge_signals.py <blob.json> <signals.json>
   [--template template.html]` writes the collected `{account_name, peopleai_id, engaged_people,
   account_status}` records into the blob's `peopleai_signals` and re-renders the HTML — the same
   dashboard, now with the insight layer filled in. See `references/mcp-behavior.md` §Signals.

## Verification

Before declaring success: the reply is prose — it contains no raw JSON and no verbatim tool dumps
(the Output contract); every per-account claim traces to a specific tool response (no invented
accounts — MCP can't enumerate, so any account not in scope simply isn't covered); windows are
labeled; credit count reported; the Caveats block is present. Meeting/email *counts* belong to
`sales-data-pull` — don't quote MCP narrative numbers as counts.

## Failure modes

- **MCP not connected / auth dead** → INSTALL.md; in Claude Code the usual cause is the
  `backstory.ai` URL (connection *looks* configured but no token is stored).
- **`find_account` misses** → try the CRM/SFDC ID via `find_record_by_crm_id`; else the account may
  not be matched in Backstory — check the data-pull blob before concluding anything.
- **Empty/thin 30d status** → a quiet month, not a dead account: check the blob's longer-window
  activity before labeling it disengaged.
- **`get_scorecard` empty** → scorecards not configured/ingested for that account — omit the
  section silently, don't ask the user about it.
- **Tool output shape varies** (markdown string or object, most wrapped in `result`) — treat as
  semi-structured; extract what's present, never schema-error at the user.
- Details: `references/mcp-behavior.md`.
