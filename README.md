<p align="center">
  <img src="hero-image.png" alt="External Monitor hero image showing evidence moving from noisy public signals into filtering, prioritization, and drill-down review" width="100%">
  <br>
  <sub>Account intelligence should narrow attention while preserving what is known, inferred, and still unverified.</sub>
</p>

# Red Hat External Monitor

Red Hat External Monitor is a file-based, agent-orchestrated account-intelligence workflow. Given a GEO, region, territory, or account scope, it builds a validated `portfolio.json` that separates internal activity evidence, selected People.ai narrative context, public evidence, and agent interpretation. The same contract drives the current HTML portfolio and XLSX workbook.

It is a skill bundle, not a deployed application or continuously running service. The repository contains no customer registry, credentials, or generated customer output.

## Five-stage workflow

1. Load the Enterprise Accounts registry to establish the account population and hierarchy.
2. Resolve canonical People.ai identities, then retrieve and aggregate bounded Query API activity data.
3. Build a deterministic base portfolio and internal-priority ranking.
4. Add selected Backstory MCP context and optional verified public research.
5. Merge, validate, and render the canonical `portfolio.json` as HTML and XLSX.

The registry establishes scope. Query API provides broad structured activity. Backstory MCP provides selected narrative depth. Public research is a separate evidence source. No source alone is the complete account view.

## Read in order

| Depth | Document | Use it for |
|---|---|---|
| 1 | This README | What the repository is and how to validate a clone. |
| 2 | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System boundaries, the two workflow diagrams, and the contract model. |
| 3 | [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | The detailed request, script, artifact, safeguard, and failure flow. |
| Reference | [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) and [`docs/PROVENANCE.md`](docs/PROVENANCE.md) | Field paths, score semantics, null handling, and evidence boundaries. |
| Runbook | [`skills/external-monitor-account-intelligence/SKILL.md`](skills/external-monitor-account-intelligence/SKILL.md) | Orchestration procedure and current fallback rules. |

## Product surfaces

- **Portfolio View** summarizes a selected scope, internal metrics, signal coverage, and explainable priority.
- **Account View** provides identity, hierarchy, People.ai metrics, MCP context when available, public signals, provenance, and a recommended validation action.
- **HTML and XLSX** are current presentation surfaces. Both consume the same `portfolio.json` contract.

## Local setup

1. Copy `.env.example` to `.env` and configure Query API credentials:

   ```text
   PEOPLEAI_CLIENT_ID=your_client_id
   PEOPLEAI_CLIENT_SECRET=your_client_secret
   ```

2. Install Python dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Connect Backstory MCP when identity resolution or narrative enrichment is required. This is interactive OAuth and user specific:

   ```bash
   claude mcp add --transport http peopleai https://mcp.people.ai/mcp
   ```

4. Run the offline smoke test:

   ```bash
   bash .claude/skills/run-rh-external-monitor/smoke.sh
   ```

   The smoke test does not call live APIs or MCP. On Windows, run it from Git Bash. See [`docs/WORKFLOW.md`](docs/WORKFLOW.md) for the artifact flow and current operational constraints.

## Validate the included example

From the repository root:

```bash
python skills/external-monitor-account-intelligence/scripts/validate_portfolio.py skills/external-monitor-account-intelligence/examples/portfolio-output.example.json
python skills/external-monitor-account-intelligence/scripts/render_portfolio.py skills/external-monitor-account-intelligence/examples/portfolio-output.example.json --out portfolio.html
```

The renderer creates a local artifact. Do not commit generated HTML, XLSX, credentials, local registry data, or customer intelligence.

## Skill layout

The External Monitor orchestration layer is under `skills/external-monitor-account-intelligence/`. The People.ai source skills remain authoritative for People.ai-specific behavior:

| Skill | Purpose |
|---|---|
| `external-monitor-account-intelligence` | Scope, portfolio assembly, selected enrichment, and final contract. |
| `sales-data-explorer` | Validated People.ai Query API requests and batch metrics. |
| `sales-data-pull` | Seller-centric data retrieval and authentication reference. |
| `sales-insights` | Backstory MCP narratives and account context. |

Claude CLI discovers repository shims from `.claude/skills/`; the authoritative skill sources remain under `skills/`.

## Repository map

| Need | Start here |
|---|---|
| Architecture and diagrams | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Technical walkthrough | [`docs/WORKFLOW.md`](docs/WORKFLOW.md) |
| Data contract and evidence policy | [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md), [`docs/PROVENANCE.md`](docs/PROVENANCE.md) |
| Current product scope | [`docs/PRODUCT.md`](docs/PRODUCT.md) |
| Presentation and UI verification | [`docs/TEMPLATE_DESIGN.md`](docs/TEMPLATE_DESIGN.md), [`docs/UI_TESTING.md`](docs/UI_TESTING.md) |
| Future direction | [`docs/ROADMAP.md`](docs/ROADMAP.md) |
| Local-only files | `.env`, `data/local/`, `output/`, `peopleai-key.local.json` |
