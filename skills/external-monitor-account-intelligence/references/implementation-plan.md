# Implementation Plan

## Keep unchanged

Preserve the uploaded People.ai skills as vendor-authored source behavior:

- `sales-data-explorer`
- `sales-data-pull`
- `sales-insights`

Do not rewrite their authentication, validated filter rules, column-drop checks, MCP windows, or credit behavior.

## Add to the project

```text
.claude/skills/
  sales-data-explorer/                 # vendor skill
  sales-data-pull/                     # vendor skill
  sales-insights/                      # vendor skill
  external-monitor-account-intelligence/
    SKILL.md
    references/
    schemas/
    scripts/
    templates/
```

## Runtime flow

```text
Enterprise Accounts
    -> resolve selected scope
    -> generate Query API packets
    -> run batch People.ai pulls
    -> normalize account metrics
    -> rank accounts deterministically
    -> enrich top accounts through Backstory MCP
    -> optional external web research
    -> validate portfolio.json
    -> render reusable HTML
```

## First demo target

- One NAPS pod or territory.
- 5–15 accounts in scope.
- Query API metrics for all accounts.
- MCP enrichment for top 5.
- One HTML artifact with working portfolio filters and account drill-down.

## Environment

Expected variables:

```text
PEOPLEAI_CLIENT_ID=
PEOPLEAI_CLIENT_SECRET=
```

Backstory MCP uses interactive OAuth and is not configured through `.env`.

Add to `.gitignore`:

```text
.env
*.local.json
peopleai-key.local.json
data/runs/
```
