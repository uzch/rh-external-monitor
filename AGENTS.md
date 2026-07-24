# Repository instructions

This repository contains the Red Hat External Monitor account-intelligence bundle. Treat the files under `integrations/account-intelligence` as the implementation source of truth.

## Rules

- Never use em dash punctuation. Use plain hyphen instead.
- When writing commit messages, NEVER auto-add your agent name as co-author.
- Never manually modify CHANGELOG.md files or any files that are marked as auto-generated.
- Use readable concise Markdown with plain hyphens and no em dash punctuation. Follow existing file style unless the task explicitly asks for restructuring.
- When making technical decisions, do not give much weight to development cost. Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user would experience it. This makes sure you find the real problem so your fix will actually solve it.
- When end-to-end testing a product, be picky about the UI you see and be obsessed with pixel perfection. If something clearly looks off, even if it is not directly related to what you are doing, try to get it fixed along the way.
- Apply that same high standard to engineering excellence: lint, test failures, and test flakiness. If you see one, even if it is not caused by what you are working on right now, still get it fixed.

## Source boundaries

- Preserve the People.ai-provided skills as authoritative for People.ai-specific behavior.
- Keep internal data, external public evidence, and agent interpretation separate.
- Never silently merge ambiguous accounts or convert missing values to zero.
- Never commit credentials or customer outputs.

## Validation

Read the root README and the integration bundle README before changing behavior or documentation. Use the bundled validator and renderer for artifact checks.
