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
  -> resolve accounts from the Enterprise Accounts registry
  -> batch People.ai Query API metrics
  -> normalize identity and preserve unresolved/ambiguous matches
  -> compute deterministic internal priority
  -> enrich selected accounts through Backstory MCP
  -> optionally attach external public signals
  -> validate portfolio.json
  -> render HTML or write the same data to Sheets
```

## Evidence boundaries

| Source | Provides | Must not be confused with |
|---|---|---|
| Enterprise Accounts | authoritative scope, hierarchy, and local account identity | People.ai identity confirmation |
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
- External public-signal collection is an optional workflow boundary, not an implemented connector in this repository.
- Google Sheets writing is an output target, not an included Sheets client.
- Portfolio prioritization is deterministic triage. It is not proof of opportunity, intent, fit, demand, renewal, deployment, or ownership.

## Start here

1. Read this README and [`AGENTS.md`](AGENTS.md) or [`CLAUDE.md`](CLAUDE.md).
2. Read the orchestration skill at [`skills/external-monitor-account-intelligence/SKILL.md`](skills/external-monitor-account-intelligence/SKILL.md).
3. Read the People.ai source skill only for the capability being run. Those files are authoritative for API behavior, catalogs, authentication, windows, and MCP limits.

## Validate the included example

From the repository root:

```powershell
python skills/external-monitor-account-intelligence/scripts/validate_portfolio.py skills/external-monitor-account-intelligence/examples/portfolio-output.example.json
python skills/external-monitor-account-intelligence/scripts/render_portfolio.py skills/external-monitor-account-intelligence/examples/portfolio-output.example.json --out portfolio.html
```

The renderer creates a local generated artifact. Do not commit customer intelligence, tokens, or generated outputs.

## Repository map

| Need | Start here |
|---|---|
| Product scope and workflow | [`docs/PRODUCT.md`](docs/PRODUCT.md), [`docs/WORKFLOW.md`](docs/WORKFLOW.md) |
| Architecture and boundaries | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) |
| Evidence and provenance | [`docs/PROVENANCE.md`](docs/PROVENANCE.md) |
| Planned direction | [`docs/ROADMAP.md`](docs/ROADMAP.md) |
| Orchestration contract | [`skills/external-monitor-account-intelligence/`](skills/external-monitor-account-intelligence/) |
| People.ai authoritative skills | [`skills/people-ai/`](skills/people-ai/) |
| Shared documentation | [`docs/`](docs/) |
| Archived planning and PoC material | [`archive/`](archive/) |
