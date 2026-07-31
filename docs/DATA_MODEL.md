# Data model

Everything flows through a single `portfolio.json`, validated by [`portfolio-output.schema.json`](../skills/external-monitor-account-intelligence/schemas/portfolio-output.schema.json). The same file drives both the HTML view and the spreadsheet export. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the system boundaries and [`WORKFLOW.md`](WORKFLOW.md) for the artifact flow.

## What's in the portfolio

At the top level: scope, summary, accounts, run metadata, and caveats.

Each account carries:

- **Identity** — People.ai account ID, match status, canonical query name
- **Hierarchy** — GEO, region, territory, segment (from the registry)
- **Internal metrics** — activity counts, meetings, emails, opportunities, trend (from People.ai Query API)
- **Signal score** — user-facing 0-100 score (average of per-signal scores, rounded integer, or null)
- **Internal priority score:** deterministic 0-100 triage score with reasons. It selects enrichment order and is displayed in the account view for transparency; it is not the user-facing signal score.
- **MCP context:** risks, next steps, topics, and other account context when supplied by enrichment
- **Signals** — scored and dispositioned findings from MCP, web research, or derived analysis
- **Summary and next move** — model-generated briefing and recommended action

## Conventions

- `null` means unavailable. `0` means the source explicitly returned zero. Never convert missing data to zero without a caveat.
- `ACT`, `WATCH`, and `REJECT` are output dispositions, not claims about customer intent.

## Nested field paths

Account data is grouped by domain. Code that reads portfolio.json must use the correct nesting:

| Data | Correct path | Wrong (will return null) |
|------|-------------|--------------------------|
| GEO / Region / Territory | `account.hierarchy.geo` | `account.geo` |
| Match status | `account.identity.match_status` | `account.match_status` |
| Signal score (user-facing) | `account.signal_score` | `account.internal.signal_score` |
| Internal priority score (triage) | `account.internal_priority_score` | `account.internal.priority_score` |
| Activity metrics | `account.internal.metrics.total_activities` | `account.total_activities` |
| Signal publish date | `signal.published_at` | `signal.published` |
| Portfolio executive summary | `summary.text` or `summary.group_briefs["_top"]` | `data.summary` (the object) |
| Territory-level brief | `summary.group_briefs["TERR_NAME"]` | `account.summary` (per-account, different) |

`hierarchy`, `identity`, and `internal` are always objects, never null. Use safe access (e.g., `acct.get("hierarchy", {}).get("geo")`) to handle malformed input gracefully.
