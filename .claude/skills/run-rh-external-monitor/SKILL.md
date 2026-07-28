---
name: run-rh-external-monitor
description: Run, test, validate, and smoke-check the rh-external-monitor skill bundle. Use when asked to run, test, validate, or check the External Monitor setup, verify credentials, or confirm the portfolio pipeline works.
---

The rh-external-monitor repository is a skill bundle, not a standalone application. There is no build step, no server, and no GUI to launch. The "app" is Claude CLI invoking the skills against live People.ai APIs and Backstory MCP.

All paths below are relative to the repository root.

## Smoke test (agent path)

Run the bundled smoke script to verify everything is wired up:

```bash
bash .claude/skills/run-rh-external-monitor/smoke.sh
```

The smoke test:

- Compiles all Python scripts
- Validates the example portfolio JSON against the schema
- Renders the example portfolio to HTML
- Checks that credentials are configured
- Confirms all four skills are discoverable via `.claude/skills/`

## Prerequisites

- Python 3.9+ available as `python`
- `jsonschema` package: `python -m pip install jsonschema`

## Validate a portfolio artifact

```bash
python skills/external-monitor-account-intelligence/scripts/validate_portfolio.py <portfolio.json>
```

## Render a portfolio to HTML

```bash
python skills/external-monitor-account-intelligence/scripts/render_portfolio.py <portfolio.json> --out output.html
```

The output directory must exist. The renderer uses `templates/portfolio.html` by default.

## Check API credentials

```bash
python skills/people-ai/sales-data-pull/scripts/pull_sales_data.py --check-key
```

Credentials come from `PEOPLEAI_CLIENT_ID` / `PEOPLEAI_CLIENT_SECRET` env vars, or `peopleai-key.local.json` next to the pull script.

## Gotchas

- Use `python` not `python3` on this machine.
- The renderer's `--out` path must point to an existing directory or a full file path whose parent directory exists.
- `validate_portfolio.py` requires `jsonschema` (`python -m pip install jsonschema`). All other scripts are stdlib only.
- The `.env` file sets environment variables for the Query API key. Backstory MCP is configured separately through `claude mcp add`.
- The smoke test does not call any live APIs.
