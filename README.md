<p align="center">
  <img src="hero-image.png" alt="External Monitor hero image showing evidence moving from noisy public signals into filtering, prioritization, and drill-down review" width="100%">
  <br>
  <sub>Account intelligence should narrow attention while preserving what is known, inferred, and still unverified.</sub>
</p>

# Red Hat External Monitor

Red Hat sellers need a fast way to decide which accounts deserve attention, understand the internal context behind that priority, and choose a next validation action. This repository contains the current account-intelligence integration bundle for that workflow.

The current direction is organized around an enterprise account registry and the NAPS hierarchy: GEO, region, pod, territory, and account. It uses People.ai Query API metrics for broad batch coverage, then uses Backstory MCP for deeper context on a bounded set of prioritized accounts.

## Product surfaces

- **Portfolio View** summarizes a selected hierarchy scope, ranks accounts with explainable internal metrics, and shows coverage and enrichment status.
- **Account View** drills into one account's identity, hierarchy, People.ai metrics, Backstory context, optional external signals, provenance, and recommended next move.
- **Google Sheets and generated HTML** are current output surfaces. The shared `portfolio.json` artifact is the contract for both views. A future application may consume the same artifact.

The workflow is:

```text
scope request
  -> load Enterprise Accounts registry (account population and organizational assignment)
  -> reconcile account identities with People.ai
  -> batch People.ai Query API metrics
  -> compute deterministic internal priority
  -> enrich selected accounts through Backstory MCP
  -> attach external public signals (default on)
  -> validate portfolio.json
  -> render HTML or write the same data to Sheets
```

## Evidence boundaries

| Source | Provides | Must not be confused with |
|---|---|---|
| Enterprise Accounts registry (`data/local/`) | authoritative account population, organizational assignment (account name, geo, region, segment, territory) | activity, engagement, risks, opportunities, or intelligence of any kind |
| People.ai Query API | batch metrics and records such as activity, engagement, meetings, and opportunities | narrative insight or customer intent |
| Backstory MCP | prioritized account status, risks, next steps, topics, people, and company news where available | complete account coverage or long-window metrics |
| External public signals | optional public evidence with URL, publisher, and publication date | internal account facts |
| Agent-derived interpretation | ranking rationale, relevance hypothesis, and suggested validation action | source evidence |

The sources remain separate in output. Missing data stays null with a caveat. Ambiguous account matches are never silently merged or deeply enriched.

## Current limitations

- This repository is an agent-agnostic skill bundle, not a deployed web application or service.
- The repository does not contain a live Enterprise Accounts dataset or customer output.
- Backstory MCP requires the user's interactive OAuth connection. Query API calls require the People.ai credentials described in the source skill installation files.
- MCP cannot enumerate accounts; the registry or Query API must establish scope first.
- Backstory narrative windows are limited by the authoritative skill guidance. Query API metrics can use a requested window up to 365 days.
- External public-signal collection runs by default but can be opted out of per-run.
- Portfolio prioritization is deterministic triage. It is not proof of opportunity, intent, fit, demand, renewal, deployment, or ownership.

## Start here

1. Read this README and [`AGENTS.md`](AGENTS.md) or [`CLAUDE.md`](CLAUDE.md).
2. Read the orchestration skill at [`skills/external-monitor-account-intelligence/SKILL.md`](skills/external-monitor-account-intelligence/SKILL.md).
3. Read the People.ai source skill only for the capability being run. Those files are authoritative for API behavior, catalogs, authentication, windows, and MCP limits.

## Local setup

1. Copy `.env.example` to `.env` and fill in your People.ai Query API credentials:

   ```
   PEOPLEAI_CLIENT_ID=your_client_id
   PEOPLEAI_CLIENT_SECRET=your_client_secret
   ```

2. Install the one external Python dependency:

   ```bash
   python -m pip install jsonschema openpyxl
   ```

3. Connect Backstory MCP for the `sales-insights` skill (interactive OAuth, once per user):

   ```bash
   claude mcp add --transport http backstory https://mcp.backstory.ai/mcp
   ```

4. Run the smoke test:

   ```bash
   bash .claude/skills/run-rh-external-monitor/smoke.sh
   ```

## Validate the included example

From the repository root:

```bash
python skills/external-monitor-account-intelligence/scripts/validate_portfolio.py skills/external-monitor-account-intelligence/examples/portfolio-output.example.json
python skills/external-monitor-account-intelligence/scripts/render_portfolio.py skills/external-monitor-account-intelligence/examples/portfolio-output.example.json --out portfolio.html
```

The renderer creates a local generated artifact. Do not commit customer intelligence, tokens, or generated outputs.

## Claude CLI skill discovery

Claude CLI discovers skills from `.claude/skills/`. Each skill there is a thin shim that points to the authoritative source in `skills/`:

| Skill (slash command) | Authoritative source | Purpose |
|---|---|---|
| `/external-monitor-account-intelligence` | `skills/external-monitor-account-intelligence/` | Orchestration - portfolio and account intelligence |
| `/sales-data-explorer` | `skills/people-ai/sales-data-explorer/` | Ad-hoc Query API metrics and custom reports |
| `/sales-data-pull` | `skills/people-ai/sales-data-pull/` | Seller-centric 360 from Query API |
| `/sales-insights` | `skills/people-ai/sales-insights/` | AI narratives via Backstory MCP |
| `/run-rh-external-monitor` | `.claude/skills/run-rh-external-monitor/` | Smoke test and validation driver |

## Repository map

| Need | Start here |
|---|---|
| Product scope and workflow | [`docs/PRODUCT.md`](docs/PRODUCT.md), [`docs/WORKFLOW.md`](docs/WORKFLOW.md) |
| Architecture and boundaries | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) |
| Evidence and provenance | [`docs/PROVENANCE.md`](docs/PROVENANCE.md) |
| Planned direction | [`docs/ROADMAP.md`](docs/ROADMAP.md) |
| Orchestration contract | [`skills/external-monitor-account-intelligence/`](skills/external-monitor-account-intelligence/) |
| People.ai authoritative skills | [`skills/people-ai/`](skills/people-ai/) |
| Claude CLI skill shims | [`.claude/skills/`](.claude/skills/) |
| Shared documentation | [`docs/`](docs/) |
| Archived planning and PoC material | [`archive/`](archive/) |
| Enterprise Accounts registry | `data/local/` (untracked) |
| Local files (untracked) | `.env`, `peopleai-key.local.json`, `output/`, `data/local/` |
