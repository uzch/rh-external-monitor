---
name: external-monitor-account-intelligence
description: Build External Monitor portfolio and account intelligence for a selected GEO, region, pod, territory, or account. Use when the user asks to research enterprise accounts, generate a portfolio briefing, identify accounts needing attention, or refresh the External Monitor interface.
---

Read and follow the authoritative skill instructions at `skills/external-monitor-account-intelligence/SKILL.md`.

That file contains the complete procedure, inputs, output rules, failure modes, and verification checklist. The supporting references, schemas, scripts, templates, and examples are in the same directory.

Key paths from the repository root:

- Procedure and contract: `skills/external-monitor-account-intelligence/SKILL.md`
- Registry loader: `skills/external-monitor-account-intelligence/scripts/load_registry.py`
- Enterprise Accounts CSV: `data/local/Enterprise Accounts.csv`
- Output schema: `skills/external-monitor-account-intelligence/schemas/portfolio-output.schema.json`
- Portfolio validator: `skills/external-monitor-account-intelligence/scripts/validate_portfolio.py`
- Portfolio renderer: `skills/external-monitor-account-intelligence/scripts/render_portfolio.py`
- Example output: `skills/external-monitor-account-intelligence/examples/portfolio-output.example.json`
- Query plan: `skills/external-monitor-account-intelligence/references/query-plan.md`
- Output contract: `skills/external-monitor-account-intelligence/references/output-contract.md`

This skill composes the People.ai source skills. Load only the one needed for each step:

- `sales-data-explorer` for batch Query API metrics
- `sales-insights` for Backstory MCP enrichment
- `sales-data-pull` for authentication reference and API behavior details
