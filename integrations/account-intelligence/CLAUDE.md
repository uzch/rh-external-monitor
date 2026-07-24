# Claude CLI Instructions

Use this bundle exactly as an agent-neutral workflow. Do not replace the People.ai source skills with improvised API behavior.

## Entry point

Read:

1. `README.md`
2. `AGENTS.md`
3. `skills/external-monitor-account-intelligence/SKILL.md`

When a task requires People.ai Query API behavior, load `skills/people-ai/sales-data-explorer/SKILL.md` and its referenced catalogs. When a task requires Backstory MCP, load `skills/people-ai/sales-insights/SKILL.md` and its MCP behavior reference.

## Output discipline

- Produce the portfolio JSON contract first.
- Validate it before rendering.
- Preserve evidence, provenance, missing values, and ambiguity.
- Do not expose secrets in command output or generated files.
