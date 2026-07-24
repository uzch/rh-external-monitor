# Install — sales-insights

Zero-config for end users beyond one MCP login: unzip, upload/copy into your AI tool, connect
Backstory, run. Fastest path: the README at the bundle root (Codex: upload the zip as-is;
Claude Code: drag into `~/.claude/skills/`; one project: `sh install.sh`).

| Path | Read by |
|---|---|
| `.claude/skills/sales-insights/` | Claude Code |
| `.agents/skills/sales-insights/` | Codex, GitHub Copilot / VS Code, Gemini CLI |

From the target project root:

```bash
SKILL=sales-insights
mkdir -p ".claude/skills/$SKILL" ".agents/skills/$SKILL"
cp -R sales-insights/. ".claude/skills/$SKILL/"
cp -R sales-insights/. ".agents/skills/$SKILL/"
```

Claude Code also accepts the folder dropped into `~/.claude/skills/`; Codex accepts the zip
uploaded directly (it lands in `.agents/skills/`).

## Backstory MCP connection (required, once per user)

Connect the Backstory (formerly People.ai) MCP server with URL **`https://mcp.people.ai/mcp`** —
the MCP endpoint stays on the people.ai domain — and sign in with your own Backstory login when
the browser opens.

> ⚠️ **Use the `people.ai` URL, not `backstory.ai`.** In Claude Code the `mcp.backstory.ai/mcp`
> address appears to complete the login but never stores a token — the connection stays dead with
> no error (verified 2026-07-02). claude.ai's built-in People.ai connector is unaffected.

- Claude Code: `claude mcp add --transport http peopleai https://mcp.people.ai/mcp`, then `/mcp`
  to authenticate.
- claude.ai / Claude Desktop: Settings → Connectors → People.ai (or add custom connector with the
  URL above).
- Codex: add an MCP server entry with the same URL per its MCP configuration docs.

No API key ships with this skill — insights run under **your** Backstory identity, and SalesAI
credit consumption is metered to the tenant like your normal SalesAI usage. The companion
`sales-data-pull` skill (separate zip folder) is the one that carries the pilot API key.

## Requirements

The MCP connection above. Python 3.9+ (stdlib only) — needed only for the optional
`scripts/merge_signals.py` dashboard merge.
