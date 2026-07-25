# Claude CLI entry point

Follow the repository-wide instructions in [`AGENTS.md`](AGENTS.md). Start with [`README.md`](README.md), then read [`skills/external-monitor-account-intelligence/SKILL.md`](skills/external-monitor-account-intelligence/SKILL.md) and its output contract. Load People.ai source skills under [`skills/people-ai/`](skills/people-ai/) only for the capability being executed.

Use `python` (not `python3`) for all script invocations. Credentials come from `PEOPLEAI_CLIENT_ID` / `PEOPLEAI_CLIENT_SECRET` environment variables or `peopleai-key.local.json`.
