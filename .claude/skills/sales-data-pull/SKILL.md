---
name: sales-data-pull
description: Pull a seller-centric sales 360 from Backstory (People.ai) - user metrics, owned accounts, activity up to a year, and opportunities. Use when the user asks to pull sales data for a seller, run the sales pull, get a seller's 360 or book, or wants to set up the Backstory API key.
---

Read and follow the authoritative skill instructions at `skills/people-ai/sales-data-pull/SKILL.md`.

That file contains the complete procedure, key setup, verification rules, and failure modes. The API behavior reference, output schema, packets, and scripts are in the same directory.

Key paths from the repository root:

- Procedure: `skills/people-ai/sales-data-pull/SKILL.md`
- Pull script: `skills/people-ai/sales-data-pull/scripts/pull_sales_data.py`
- API behavior reference: `skills/people-ai/sales-data-pull/references/api-behavior.md`
- Output schema: `skills/people-ai/sales-data-pull/references/output-schema.md`
- Dashboard template: `skills/people-ai/sales-data-pull/scripts/template.html`
- Packet verification: `skills/people-ai/sales-data-pull/scripts/verify-packet.sh`

Credentials: `PEOPLEAI_CLIENT_ID` / `PEOPLEAI_CLIENT_SECRET` env vars, or `peopleai-key.local.json` next to the pull script.

Key setup check: `python skills/people-ai/sales-data-pull/scripts/pull_sales_data.py --check-key`

Use `python` (not `python3`) to run scripts.
