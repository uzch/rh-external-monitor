# UI Testing

The portfolio HTML template is tested with an automated headless browser click-through using [Playwright](https://playwright.dev/). The test simulates a real user navigating every view in the interface and verifies that the output renders correctly.

This is presentation regression coverage for the file-based workflow described in [`ARCHITECTURE.md`](ARCHITECTURE.md). It uses generated or committed fixtures and does not exercise live People.ai, Backstory MCP, or public-research connections.

## Why automated

The template supports multiple scope types (GEO, region, territory, account), each producing different drill-down paths. A single GEO portfolio can have dozens of click paths — regions, territories, accounts, breadcrumbs, tabs, edge cases. Manual verification misses regressions. The automated test covers all paths in under 10 seconds.

## Prerequisites

From the skill directory (`skills/external-monitor-account-intelligence/`):

```bash
npm install
npx playwright install chromium
```

This installs Playwright as a dev dependency. The `node_modules/` and `package-lock.json` are gitignored.

## Running the test

Three steps: generate fixture data, render it to HTML, run the test.

```bash
# 1. Generate synthetic GEO fixture (25 accounts, 3 regions, 9 territories)
python examples/generate-geo-fixture.py

# 2. Render the fixture into HTML using the real template
python scripts/render_portfolio.py examples/portfolio-geo-test.json --out tests/test-output.html

# 3. Run the automated click-through
node tests/test-template-ui.js
```

Exit code 0 means all assertions passed. Exit code 1 means at least one failed — the output shows which.

Both `portfolio-geo-test.json` and `test-output.html` are gitignored generated artifacts.

## What the test covers

The test runs **57 assertions** across 8 sections:

### GEO overview
- Title matches the GEO name
- Tab bar shows dynamic scope label and Guide
- Subtitle includes region, territory, and account counts
- 5 KPI cards render with correct values (Accounts, Internal Data, Enriched, Act/Watch, Highest Score)
- Executive Summary card present with signal-focused text (not a restatement of KPI numbers)
- 5 activity stat cards (Total Activities, Meetings 30d, Emails 30d, Opportunities, Trend)
- Region table has correct row count with "Open →" links

### Drill into region
- New tab appears for the region level
- Breadcrumb shows full navigation path
- KPI and activity stats render at the region level (aggregated from child accounts)
- Territory table rows present with numeric average scores

### Drill into territory
- Account list table with signal score pills and match status badges
- First column (account name) constrained to 280px max-width to prevent layout overflow
- Match badges render on a single line (`white-space: nowrap`)

### Account detail
- Two-column layout (main content + sidebar)
- 30-Second Summary card
- Recommended Next Move card
- Signal cards rendered and sorted by score descending
- Disposition pills (ACT/WATCH) on each signal card
- Collapsible `<details>` sections open to show detail grids
- Sidebar cards: Account Details, Activity, Caveats
- Priority Score displayed in sidebar

### Breadcrumb navigation
- Clickable breadcrumb links navigate back up the hierarchy
- Clicking the GEO breadcrumb returns to the top-level overview with all regions

### Guide tab
- Page title is "Guide"
- At least 8 content sections covering all interface concepts
- Specific sections verified: signal score, match status, activity trend, navigation, Act/Watch/Reject
- At least 5 definition tables
- Styled status pills (ACT, WATCH, REJECT) and match badges rendered in-context

### Edge cases
- Navigate to an account with `not_found` or `ambiguous` match status
- Verify it renders without JavaScript errors — null metrics show dashes, missing fields degrade gracefully

### Responsive breakpoints
- At 920px: account layout grid collapses (sidebar stacks below main)
- At 600px: heading font-size shrinks to 28px

## Test fixture

The synthetic data generator (`examples/generate-geo-fixture.py`) creates a GEO-scope portfolio with:

- **NAPS** GEO with 3 regions (INTEL, CIVILIAN, DEFENSE)
- 9 territories across those regions
- 25 accounts with varied match statuses (matched, ambiguous, not_found, unresolved)
- Full activity metrics on matched accounts, null metrics on unmatched
- Multiple signals per account (ACT and WATCH dispositions) with varied scores
- Deterministic output (`random.seed(42)`) so the test assertions are stable

The generator is **not** part of the tool pipeline. It is only used for UI testing when explicitly requested. See the warning header in the script.

## Region-scope test

A second test (`tests/test-intel-ui.js`) covers region-level rendering using a pre-built fixture with real INTEL region data (9 accounts across 6 territories).

```bash
node tests/test-intel-ui.js
```

Unlike the GEO test, this test does not require fixture generation — the HTML fixture at `tests/fixtures/intel-portfolio-preview.html` is committed. It covers:

- Region overview: title, tabs, KPIs, summary, activity stats, territory table with numeric average scores
- Territory drill-down: account list with signal pills, match badges, signal score columns
- Account detail: summary, next move, signal cards sorted descending, collapsible details, sidebar cards
- Breadcrumb navigation back to region
- Guide tab: sections, definition tables, styled pills/badges
- Multi-territory drill: second territory drill to verify consistent rendering
- Responsive breakpoints: 920px grid collapse, 600px heading font-size

## Adding new test assertions

The test script at `tests/test-template-ui.js` uses a simple `assert(condition, msg)` helper. To add a new check:

1. Navigate to the view you want to test (use `page.click()` to drill down, `page.waitForTimeout(100)` after navigation)
2. Query the DOM with Playwright selectors (`page.$eval`, `page.$$eval`, `page.$$`)
3. Call `assert(condition, 'description of what should be true')`

The test runs sequentially through the interface — later assertions depend on the navigation state set up by earlier ones. Add new checks in the appropriate section or at the end.

## When to run

Run the UI test after any change to:

- `templates/portfolio.html` — the template itself
- `examples/generate-geo-fixture.py` — the test fixture generator
- Any pipeline script that changes the shape of the portfolio JSON (`build_portfolio.py`, `enrich_portfolio.py`)
- `schemas/portfolio-output.schema.json` — the output schema
