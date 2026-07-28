---
name: sales-data-explorer
description: Answer ad-hoc questions and build custom tables from Backstory (People.ai) data - any validated metric on accounts, opportunities, sellers, teams, activities, or people. Use when the user asks a specific metric question, wants a custom report, or asks what else can be pulled from Backstory / People.ai.
---

Read and follow the authoritative skill instructions at `skills/people-ai/sales-data-explorer/SKILL.md`.

That file contains the complete procedure, verification rules, and failure modes. The catalog, query guide, and scripts are in the same directory.

Key paths from the repository root:

- Procedure: `skills/people-ai/sales-data-explorer/SKILL.md`
- Validated column catalog: `skills/people-ai/sales-data-explorer/references/catalog.json`
- Query guide and filter shapes: `skills/people-ai/sales-data-explorer/references/query-guide.md`
- REST endpoint catalog: `skills/people-ai/sales-data-explorer/references/rest-catalog.json`
- Export runner: `skills/people-ai/sales-data-explorer/scripts/run_query.py`
- REST runner: `skills/people-ai/sales-data-explorer/scripts/rest_query.py`

Credentials: `PEOPLEAI_CLIENT_ID` / `PEOPLEAI_CLIENT_SECRET` env vars, or `peopleai-key.local.json` in the scripts directory, or auto-found from `sales-data-pull/scripts/peopleai-key.local.json`.

Use `python` (not `python3`) to run scripts.
