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

Backstory MCP requires the user's interactive OAuth connection at `https://mcp.people.ai/mcp`.

## Validate the example

```bash
python scripts/validate_portfolio.py examples/portfolio-output.example.json
```

## Render the example

```bash
python scripts/render_portfolio.py examples/portfolio-output.example.json --out demo.html
```

## UI testing

The HTML template has an automated headless browser test that clicks through every view and verifies the interface renders correctly. See [UI Testing](../../docs/UI_TESTING.md) for the full procedure.

Quick start:

```bash
# Install Playwright (one-time)
npm install
npx playwright install chromium

# Generate fixture, render, test
python examples/generate-geo-fixture.py
python scripts/render_portfolio.py examples/portfolio-geo-test.json --out tests/test-output.html
node tests/test-template-ui.js
```

Run the UI test after any change to `templates/portfolio.html` or the portfolio JSON schema.

## Template design

The template uses Red Hat Design System styling with scope-aware drill-down navigation. See [Template Design](../../docs/TEMPLATE_DESIGN.md) for the full design specification.
