# Template Design

The portfolio HTML template (`templates/portfolio.html`) is a single self-contained file that renders the portfolio JSON into an interactive drill-down report. It uses inline CSS and JavaScript with no external dependencies beyond two Google Fonts.

The template is a presentation consumer of the canonical artifact. For the upstream workflow and contract boundary, see [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`WORKFLOW.md`](WORKFLOW.md).

## Visual direction

The template follows the **Red Hat Design System** visual language:

- **Typography**: Red Hat Display (headings, 500 weight) and Red Hat Text (body, 400 weight) loaded from Google Fonts
- **Brand red**: `#EE0000` — used for KPI values, active tab indicators, card accent borders, and the logo mark
- **UX black**: `#151515` — header background and primary text
- **Links**: `#0066cc`
- **Status colors**:
  - ACT: green background `#e9f7df`, green text `#3d7317`
  - WATCH: orange background `#ffe8cc`, orange text `#9e4a06`
  - REJECT: danger-orange background `#ffe3d9`, danger text `#b1380b`
- **Match badges**: matched (green), ambiguous (orange), not_found (red), unresolved (gray)

## How it renders

`render_portfolio.py` reads the template, replaces the `__PORTFOLIO_JSON__` placeholder with serialized JSON, and writes the output HTML. The template's `<script>` block parses this JSON on load and builds all views dynamically.

```
portfolio.html  +  portfolio.json  →  render_portfolio.py  →  output.html
   (template)       (data)                                    (self-contained)
```

No changes to `render_portfolio.py` or the JSON schema were needed. The template consumes the existing schema as-is.

## Scope-aware hierarchy

The template supports five scope types, each producing a different number of drill-down levels. The levels represent what is **below** the scope, not including the scope itself:

| Scope type | Drill-down levels | Navigation path |
|---|---|---|
| `geo` | `region` → `territory_name` | GEO overview → Regions → Territories → Accounts |
| `region` | `territory_name` | Region overview → Territories → Accounts |
| `pod` | `territory_name` | Pod overview → Territories → Accounts |
| `territory` | *(none)* | Account list directly |
| `account` | *(none)* | Account detail directly |

The current registry scripts implement GEO, region, territory, and account selection. `pod` remains supported by the schema and template, but is not yet an implemented registry-loader scope.

When a group at any level contains only one child, the template skips that level and navigates directly to the child. This removes redundant clicks — a territory with one account goes straight to the account detail.

## View structure

### Hierarchy views (GEO, Region, Territory)

Every hierarchy level uses the same layout:

1. **Page header** — breadcrumb trail + title + subtitle (child counts)
2. **KPI row** — 5 cards: Accounts, With Internal Data, Enriched, Act/Watch Signals, Highest Score
3. **Executive Summary** — `data.summary.text` at top level, or aggregated description at sub-levels
4. **Activity stats bar** — 5 cards: Total Activities, Meetings (30d), Emails (30d), Opportunities, Overall Trend
5. **Data table** — rows for each child group with columns: Name, Accounts, Avg Score, ACT, WATCH, Activities, Trend, Open →

All KPIs and activity stats are aggregated from the accounts within that group. Signal scores use the average of non-null values.

### Account detail view

Two-column layout (main content + 300px sidebar):

**Main column:**
- 30-Second Summary card
- Recommended Next Move card
- Signal cards — sorted by score descending. Each card shows: headline, score, disposition pill, what changed, why it matters, Red Hat relevance, recommended action. A collapsible `<details>` section shows source type, confidence, and other audit fields.

**Sidebar:**
- Account Details (hierarchy info, match status badge)
- Priority Score (internal triage score, shown for transparency but labeled as internal)
- Activity card (metrics from People.ai)
- Caveats (from `_meta.caveats`)

### Guide tab

A plain-language reference (always the rightmost tab) covering every concept in the interface:

- How to navigate (drill-down, breadcrumbs, tabs)
- Signal score (what it means, how it's computed)
- Act / Watch / Reject (disposition definitions)
- Sources (derived, Backstory MCP, external public, People.ai)
- Confidence levels (high, medium, low)
- Match status (matched, ambiguous, not_found, unresolved)
- Activity trend (increasing, stable, declining)
- Activity numbers (what they count, what they don't)
- Enrichment (what it means, why some accounts lack it)
- Priority Score vs Signal Score (two scores, different purposes)
- Caveats (data limitations)

Written in short, direct sentences. No jargon without a definition.

## Signal score computation

The template computes signal scores from per-signal scores when the `signal_score` field is null. This handles portfolio JSON from older pipeline runs that predate `enrich_portfolio.py`'s score computation:

```javascript
function accountScore(a) {
  if (a.signal_score != null) return a.signal_score;
  var sigs = (a.signals || []).filter(function(s){ return s.score != null; });
  if (!sigs.length) return null;
  var sum = 0;
  for (var i = 0; i < sigs.length; i++) sum += sigs[i].score;
  return Math.round(sum / sigs.length);
}
```

This matches the formula in `enrich_portfolio.py` (lines 152–157): `round(sum(scores) / len(scores))`.

## Null safety

The template is defensive against missing data at every level:

- Missing `signal_score` → computed from per-signal scores or shown as "—"
- Missing `internal.metrics` → activity stats show "—" for all values
- Missing `summary` or `recommended_next_move` → card still renders with placeholder
- Missing `signals` array → no signal cards rendered
- Accounts with `not_found` or `unresolved` match status → render without errors, null metrics show dashes

## Responsive behavior

| Breakpoint | Change |
|---|---|
| ≤ 920px | Account layout collapses — sidebar stacks below main content. Signal card detail grid goes single-column. |
| ≤ 620px | Heading shrinks from 36px to 28px. KPI values shrink. |

## CSS fixes applied

- `.match-badge`: `white-space: nowrap` prevents "not found" from wrapping to two lines
- `.trend-up`, `.trend-stable`, `.trend-down`: `white-space: nowrap` keeps arrows on the same line as trend text
- `.data-table td:first-child`: `max-width: 280px; word-break: break-word` prevents long names from pushing table content off-screen
- `.status-pill`: `white-space: nowrap` keeps disposition labels on one line

## Tab bar behavior

The tab bar is dynamic, not fixed. It reflects the current navigation depth:

- At the top level: `[Scope Overview]  [Guide]`
- After drilling into a region: `[Scope Overview]  [Region Name]  [Guide]`
- After drilling into a territory: `[Scope Overview]  [Region Name]  [Territory Name]  [Guide]`
- After drilling into an account: `[Scope Overview]  [Region Name]  [Territory Name]  [Account Name]  [Guide]`

Clicking a tab navigates to that level. The Guide tab is always present as the rightmost tab.
