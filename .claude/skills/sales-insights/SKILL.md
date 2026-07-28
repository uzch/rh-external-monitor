---
name: sales-insights
description: AI insight layer over Backstory (People.ai) via the user's MCP connection - per-account and per-opportunity risks, next steps, topics, and cross-account rollup. Use when the user asks to summarize risks or next steps on an account, roll up insights across a seller's book, or wants narrative insight on top of sales data.
---

Read and follow the authoritative skill instructions at `skills/people-ai/sales-insights/SKILL.md`.

That file contains the complete procedure, output contract, window rules, credit caps, and failure modes. The MCP behavior reference and merge script are in the same directory.

Key paths from the repository root:

- Procedure: `skills/people-ai/sales-insights/SKILL.md`
- MCP behavior reference: `skills/people-ai/sales-insights/references/mcp-behavior.md`
- Signal merge script: `skills/people-ai/sales-insights/scripts/merge_signals.py`

Prerequisite: Backstory MCP connected at `https://mcp.people.ai/mcp` (NOT backstory.ai).

Configure in Claude CLI: `claude mcp add --transport http peopleai https://mcp.people.ai/mcp`

No API key needed - this skill uses interactive OAuth under your Backstory identity. SalesAI credit consumption is tenant-metered.

Use `python` (not `python3`) to run scripts.
