# Repository instructions

This repository contains the Red Hat External Monitor account-intelligence bundle. The root `skills/`, `docs/`, and `archive/` directories are authoritative.

## Working rules

- Never use em dash punctuation. Use plain hyphens.
- Never add an agent as a commit co-author.
- Never manually modify `CHANGELOG.md` or files marked as auto-generated.
- Prefer readable, concise Markdown and follow the existing file style.
- Prefer quality, simplicity, robustness, scalability, and long-term maintainability over development cost.
- Keep internal data, external public evidence, and agent interpretation separate.
- Never silently merge ambiguous accounts or convert missing values to zero.
- Never commit credentials, tokens, customer outputs, or generated intelligence.

The External Monitor skill governs orchestration. People.ai-provided skills under `skills/people-ai/` remain authoritative for People.ai-specific behavior. Do not rewrite connector behavior to fit this repository; adapt the orchestration layer when needed.

## Validation

Before claiming completion:

- Read the root README before changing behavior or documentation.
- Compile all Python scripts and parse all JSON files.
- Run the bundled portfolio validator and renderer for artifact checks.
- Report unavailable API or MCP capabilities honestly.

When fixing a bug, reproduce it in an end-to-end flow close to the user experience before changing code. When validating UI, check the rendered result carefully and address clear related defects.
