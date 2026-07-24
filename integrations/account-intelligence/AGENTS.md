# Account-intelligence bundle instructions

These instructions apply to this bundle and supplement the repository rules in [`../../AGENTS.md`](../../AGENTS.md). Treat this directory as the implementation source of truth.

## Objective

Produce a scope-level portfolio and account drill-down from an enterprise account registry, People.ai Query API data, and optional Backstory MCP enrichment.

## Authority boundaries

- Use the External Monitor skill for scope resolution, ranking, enrichment selection, output normalization, and rendering.
- Preserve the People.ai-provided skills as authoritative for API behavior, authentication, catalogs, time windows, and MCP limitations.
- Do not silently infer account identity matches or deeply enrich ambiguous accounts.
- Do not convert missing metrics into zero unless the source explicitly reports zero.
- Keep source evidence, provenance, missing values, ambiguity, and derived conclusions explicit.

## Required reading order

1. `README.md`
2. `skills/external-monitor-account-intelligence/SKILL.md`
3. `skills/external-monitor-account-intelligence/references/output-contract.md`
4. The relevant People.ai skill and references for the capability being run.

## Implementation principles

- Resolve scope from the enterprise account registry.
- Prefer one batch Query API request over one request per account.
- Enrich only the highest-priority accounts through Backstory MCP unless explicitly instructed otherwise.
- Keep the workflow usable when MCP is unavailable.
- Emit schema-valid portfolio JSON before rendering HTML or writing Sheets.

Use the bundled validator and renderer when checking artifacts. Do not commit generated outputs.
