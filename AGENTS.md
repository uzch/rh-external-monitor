# Repository instructions

This repository contains the Red Hat External Monitor account-intelligence bundle. The root `skills/`, `docs/`, and `archive/` directories are authoritative.

## Working rules

- Never use em dash punctuation. Use plain hyphens.
- Never add an agent as a commit co-author.
- Never manually modify changelog files under `skills/people-ai/` or files marked as auto-generated.
- Prefer readable, concise Markdown and follow the existing file style.
- Prefer quality, simplicity, robustness, scalability, and long-term maintainability over development cost.
- Keep internal data, external public evidence, and agent interpretation separate.
- Never silently merge ambiguous accounts or convert missing values to zero.
- Never commit credentials, tokens, customer outputs, or generated intelligence.
- All pipeline run outputs go into a distinct named subfolder under `output/`, never flat. Name the folder to identify the run (e.g., `intel/`, `terr03/`, `naps-2026-07-27/`).

The External Monitor skill governs orchestration. People.ai-provided skills under `skills/people-ai/` remain authoritative for People.ai-specific behavior. Do not rewrite connector behavior to fit this repository; adapt the orchestration layer when needed.

## Validation

Before claiming completion:

- Read the root README before changing behavior or documentation.
- Compile all Python scripts and parse all JSON files.
- Run the bundled portfolio validator and renderer for artifact checks.
- Report unavailable API or MCP capabilities honestly.

When fixing a bug, reproduce it in an end-to-end flow close to the user experience before changing code. When validating UI, check the rendered result carefully and address clear related defects.

## MCP tool availability

Backstory MCP tools (`find_account`, `get_account_status`, `get_recent_account_activity`, `account_company_news`, `ask_sales_ai_about_account`) require an authenticated OAuth session bound to the main Claude Code process.

Constraints:

- MCP tools are **not available to spawned subagents**. The OAuth session does not propagate.
- Continued sessions (after context compaction) may lose MCP access.
- Always verify MCP availability before delegating MCP-dependent work.

Fallback patterns:

- **Identity resolution:** Use the identity cache (`data/local/identity-cache.json`) via `resolve_identities.py` to skip MCP for previously resolved accounts. For new accounts, resolve sequentially from the main session or use the People.ai REST API.
- **MCP enrichment:** Make MCP calls sequentially from the main session, then delegate synthesis to parallel subagents. If MCP is entirely unavailable, skip enrichment and set `mcp_status = "unavailable"`.
- **External research:** WebSearch is available to subagents and does not require MCP. External research always works regardless of MCP status.
