# Install — sales-data-pull

Zero-config for end users: unzip, upload/copy into your AI tool, run. Fastest path: the README
at the bundle root (Codex: upload the zip as-is; Claude Code: drag into `~/.claude/skills/`;
one project: `sh install.sh`).

| Path | Read by |
|---|---|
| `.claude/skills/sales-data-pull/` | Claude Code |
| `.agents/skills/sales-data-pull/` | Codex, GitHub Copilot / VS Code, Gemini CLI |

From the target project root:

```bash
SKILL=sales-data-pull
mkdir -p ".claude/skills/$SKILL" ".agents/skills/$SKILL"
cp -R sales-data-pull/. ".claude/skills/$SKILL/"
cp -R sales-data-pull/. ".agents/skills/$SKILL/"
```

Claude Code also accepts the folder dropped into `~/.claude/skills/`; Codex accepts the zip
uploaded directly (it lands in `.agents/skills/`).

## API key

`scripts/peopleai-key.local.json` holds your tenant's Query API key — a `client_id` +
`client_secret` pair from your Backstory admin (the key file and env-var names keep the
`peopleai` spelling). The bundle ships **without** it; wiring it in is the one-time setup
step. Easiest: paste the pair to your AI assistant and say "wire in my Backstory API key"
(the bundle README and SKILL.md carry the assistant's instructions), or create the file
yourself:

```json
{"client_id": "…", "client_secret": "…"}
```

Check it with `python scripts/pull_sales_data.py --check-key`.

It is deliberately a separate file: swap it without touching the skill, grep for it in
security review, and it never belongs in git. `PEOPLEAI_CLIENT_ID`/`PEOPLEAI_CLIENT_SECRET`
env vars override it.
**Shared-key posture** — before rolling out beyond a pilot group, switch to per-user keys or
get explicit sign-off on continuing with a shared key.

## Requirements

Python 3.9+ (macOS ships it). Nothing to install — stdlib only. No MCP connection needed.

## First run in a new tenant

Optional but recommended — confirms every validated field is enabled in this tenant (the API
drops unknown fields silently — see `references/api-behavior.md`):

```bash
export PEOPLEAI_CLIENT_ID=$(python -c "import json;print(json.load(open('scripts/peopleai-key.local.json'))['client_id'])")
export PEOPLEAI_CLIENT_SECRET=$(python -c "import json;print(json.load(open('scripts/peopleai-key.local.json'))['client_secret'])")
bash scripts/verify-packet.sh scripts/packets/user-metrics.json
```
