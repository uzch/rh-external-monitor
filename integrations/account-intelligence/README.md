# External Monitor Account Intelligence Bundle

A self-contained, agent-agnostic skill bundle for producing portfolio-level and account-level intelligence from:

- an enterprise account registry organized by GEO, region, pod, territory, and account;
- People.ai Query API data;
- Backstory MCP account intelligence;
- optional external signals added later.

## Included skills

### People.ai-provided source skills

- `skills/people-ai/sales-data-explorer`
  - flexible Query API and REST querying;
  - validated field catalogs;
  - batch export support.
- `skills/people-ai/sales-data-pull`
  - seller-oriented reference workflow;
  - packet definitions;
  - JSON and HTML output examples.
- `skills/people-ai/sales-insights`
  - Backstory MCP account intelligence;
  - account status, risks, next steps, activity, people, and news.

These source skills are preserved rather than rewritten. Their API behavior, authentication guidance, catalogs, and limits remain authoritative for People.ai-specific operations.

### External Monitor orchestration skill

- `skills/external-monitor-account-intelligence`
  - resolves a selected GEO, region, pod, territory, or account into an account set;
  - batch-pulls Query API metrics;
  - ranks accounts;
  - enriches a limited subset through Backstory MCP;
  - emits one validated JSON artifact for Portfolio View and Account View;
  - renders a reusable HTML interface.

## Agent compatibility

- `AGENTS.md` provides neutral instructions for Codex and other coding agents.
- `CLAUDE.md` provides Claude CLI entry guidance without changing the underlying workflow.
- Each skill retains its own `SKILL.md`.

No agent-specific runtime is required by the data contract. Any agent can execute the workflow if it can:

1. read local files;
2. run Python;
3. call the authorized People.ai Query API;
4. access Backstory MCP when enrichment is requested;
5. write JSON and HTML artifacts.

## Recommended repository placement

Copy this entire directory into the External Monitor repository, preserving the structure. Do not flatten the skills.

## Credentials

Store credentials only in `.env`, which is ignored by the included `.gitignore.example`.

Expected variables are documented in the original People.ai `INSTALL.md` files. Do not commit `.env`, OAuth tokens, API responses containing sensitive data, or generated customer intelligence.

## Workflow

```text
scope request
    -> resolve accounts from Enterprise Accounts
    -> batch People.ai Query API pull
    -> normalize and rank accounts
    -> Backstory MCP enrichment for selected accounts
    -> validate portfolio JSON
    -> render Portfolio View and Account View
```

## Start here

1. Read `AGENTS.md` or `CLAUDE.md`.
2. Read `skills/external-monitor-account-intelligence/SKILL.md`.
3. Read the referenced People.ai skill files only when executing their specific capability.
4. Validate example output:

```bash
python skills/external-monitor-account-intelligence/scripts/validate_portfolio.py \
  skills/external-monitor-account-intelligence/examples/portfolio-output.example.json
```

5. Render example output:

```bash
python skills/external-monitor-account-intelligence/scripts/render_portfolio.py \
  skills/external-monitor-account-intelligence/examples/portfolio-output.example.json \
  --out portfolio.html
```
