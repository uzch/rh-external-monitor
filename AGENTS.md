# Repository instructions

This repository contains the Red Hat External Monitor account-intelligence bundle. The implementation source of truth is `integrations/account-intelligence`.

## Working rules

- Never use em dash punctuation. Use plain hyphens.
- Never add an agent as a commit co-author.
- Never manually modify `CHANGELOG.md` or files marked as auto-generated.
- Prefer readable, concise Markdown and follow the existing file style.
- Prefer quality, simplicity, robustness, scalability, and long-term maintainability over development cost.
- Keep internal data, external public evidence, and agent interpretation separate.
- Never silently merge ambiguous accounts or convert missing values to zero.
- Never commit credentials, tokens, customer outputs, or generated intelligence.

For changes within `integrations/account-intelligence`, also follow its scoped `AGENTS.md`. People.ai-provided skills remain authoritative for People.ai-specific behavior.

## Validation

Before claiming completion:

- Read the root README and `integrations/account-intelligence/README.md` before changing behavior or documentation.
- Compile all Python scripts and parse all JSON files.
- Run the bundled portfolio validator and renderer for artifact checks.
- Report unavailable API or MCP capabilities honestly.

When fixing a bug, reproduce it in an end-to-end flow close to the user experience before changing code. When validating UI, check the rendered result carefully and address clear related defects.
