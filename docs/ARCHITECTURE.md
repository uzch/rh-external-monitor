# Architecture

The repository is a portable skill and artifact bundle with four boundaries:

1. **Registry boundary** - Enterprise Accounts supplies the selected NAPS hierarchy scope and stable local identity.
2. **Internal data boundary** - People.ai Query API supplies batch metrics and records. Backstory MCP supplies deeper context for selected accounts.
3. **Orchestration boundary** - the External Monitor skill resolves scope, matches identity, ranks accounts, selects enrichment, and produces schema-valid JSON.
4. **Presentation boundary** - generated HTML and a future or external Google Sheets writer consume the same JSON artifact.

The agent can be Codex, Claude CLI, or another compatible runner. The contract is file-based and does not require a specific agent runtime.

Identity is resolved in stages. Stable CRM identifiers are preferred, then exact normalized names, then explicit provider confirmation or user aliases. Ambiguous matches are marked and excluded from silent enrichment.

The system is intentionally usable when MCP is unavailable: the Query API portfolio can still be produced with enrichment marked unavailable.

## Source and implementation boundaries

The authoritative People.ai source skills are preserved under `skills/people-ai/`. The External Monitor orchestration layer lives under `skills/external-monitor-account-intelligence/`. These skills are portable and agent-agnostic, so Codex, Claude CLI, or another compatible runner can execute the file-based workflow.
