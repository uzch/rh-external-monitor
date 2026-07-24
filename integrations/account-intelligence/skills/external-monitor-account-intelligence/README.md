# External Monitor Account Intelligence Skill

This package adapts the uploaded People.ai/Backstory skills to the External Monitor use case.

It intentionally leaves the vendor-authored skills intact and adds an orchestration layer for:

- GEO / region / pod / territory / account scope selection
- batch People.ai Query API metrics
- selective Backstory MCP enrichment
- portfolio prioritization
- one reusable Portfolio View and Account View

## Install

Copy this folder alongside the three uploaded People.ai skills:

```text
.claude/skills/external-monitor-account-intelligence/
```

Keep credentials outside source control:

```text
PEOPLEAI_CLIENT_ID=
PEOPLEAI_CLIENT_SECRET=
```

Backstory MCP requires the user's interactive OAuth connection at `https://mcp.people.ai/mcp`.

## Validate the example

```bash
python3 scripts/validate_portfolio.py examples/portfolio-output.example.json
```

## Render the example

```bash
python3 scripts/render_portfolio.py examples/portfolio-output.example.json --out demo.html
```
