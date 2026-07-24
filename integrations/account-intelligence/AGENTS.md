# Agent Instructions

This bundle is agent-agnostic. Treat the files in this repository as the source of truth.

## Objective

Produce a scope-level portfolio and account drill-down from an enterprise account registry, People.ai Query API data, and optional Backstory MCP enrichment.

## Required reading order

1. `README.md`
2. `skills/external-monitor-account-intelligence/SKILL.md`
3. `skills/external-monitor-account-intelligence/references/output-contract.md`
4. Only then, read the relevant source skill:
   - Query API: `skills/people-ai/sales-data-explorer/SKILL.md`
   - canned seller pull reference: `skills/people-ai/sales-data-pull/SKILL.md`
   - Backstory MCP: `skills/people-ai/sales-insights/SKILL.md`

## Authority boundaries

- Preserve the People.ai-provided skills as authoritative for People.ai-specific API behavior, authentication, field catalogs, filters, time windows, and MCP limitations.
- Use the External Monitor skill as authoritative for scope resolution, account ranking, enrichment selection, output normalization, and interface rendering.
- Do not silently infer account identity matches.
- Do not convert missing metrics into zero unless the source explicitly reports zero.
- Keep source provenance separate from derived conclusions.

## Implementation principles

- Prefer one batch Query API request over one request per account.
- Enrich only the highest-priority accounts through Backstory MCP unless explicitly instructed otherwise.
- Keep the workflow usable when MCP is unavailable.
- Emit schema-valid JSON before rendering HTML or writing Google Sheets.
- Never place credentials, tokens, or customer outputs in version control.

## Validation

Before claiming completion:

- compile all Python scripts;
- parse all JSON files;
- validate the example portfolio output;
- render the HTML example;
- report any unavailable API or MCP capability honestly.
