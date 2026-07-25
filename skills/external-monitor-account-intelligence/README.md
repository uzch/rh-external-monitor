# External Monitor Account Intelligence Skill

This package adapts the uploaded People.ai/Backstory skills to the External Monitor use case.

It intentionally leaves the vendor-authored skills intact and adds an orchestration layer for:

- GEO / region / pod / territory / account scope selection
- batch People.ai Query API metrics
- selective Backstory MCP enrichment
- portfolio prioritization
- one reusable Portfolio View and Account View

## Setup

The authoritative skill lives at `skills/external-monitor-account-intelligence/`. Claude CLI discovers it through the shim at `.claude/skills/external-monitor-account-intelligence/SKILL.md`.

Keep credentials outside source control. Set in `.env` or as environment variables:

```text
PEOPLEAI_CLIENT_ID=
PEOPLEAI_CLIENT_SECRET=
```

Backstory MCP requires the user's interactive OAuth connection at `https://mcp.backstory.ai/mcp`.

## Validate the example

```bash
python scripts/validate_portfolio.py examples/portfolio-output.example.json
```

## Render the example

```bash
python scripts/render_portfolio.py examples/portfolio-output.example.json --out demo.html
```
