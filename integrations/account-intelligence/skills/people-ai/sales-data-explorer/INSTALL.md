# Install — sales-data-explorer

Zero-config for end users: unzip, upload/copy into your AI tool, ask. Fastest path: the README
at the bundle root (Codex: upload the zip as-is; Claude Code: drag into `~/.claude/skills/`;
one project: `sh install.sh`).

| Path | Read by |
|---|---|
| `.claude/skills/sales-data-explorer/` | Claude Code |
| `.agents/skills/sales-data-explorer/` | Codex, GitHub Copilot / VS Code, Gemini CLI |

From the target project root:

```bash
SKILL=sales-data-explorer
mkdir -p ".claude/skills/$SKILL" ".agents/skills/$SKILL"
cp -R sales-data-explorer/. ".claude/skills/$SKILL/"
cp -R sales-data-explorer/. ".agents/skills/$SKILL/"
```

## API key

Uses the **same key as sales-data-pull** — the runner finds
`sales-data-pull/scripts/peopleai-key.local.json` automatically when both skills are installed
side by side (that is the bundle layout). A `peopleai-key.local.json` next to
`scripts/run_query.py`, or `PEOPLEAI_CLIENT_ID`/`PEOPLEAI_CLIENT_SECRET` env vars, also work.
No key wired in yet? The bundle README covers the one-time setup — or just tell your AI
assistant "wire in my Backstory API key". The REST lane uses the same key; its different
token endpoint is handled inside the runner.

## Requirements

Python 3.9+ (macOS ships it). Nothing to install — stdlib only. No MCP connection needed.

## What it can and cannot answer

Any validated metric column on accounts, opportunities, sellers/teams, activities, and people —
the full vocabulary is `references/catalog.json` (75 live-verified columns, including
forward-looking upcoming-meetings windows). AI narratives (risks / next steps / topics) are not
in this API — that's the `sales-insights` skill over your own Backstory MCP login.
