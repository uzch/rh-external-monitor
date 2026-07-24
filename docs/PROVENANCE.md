# Provenance

Every delivered fact must retain its source, retrieval or publication date when available, time window, and relevant caveat. The artifact distinguishes:

- Enterprise Accounts registry data;
- People.ai Query API metrics and records;
- Backstory MCP context;
- external public evidence;
- agent-derived ranking, relevance hypotheses, and actions.

The People.ai skills under `skills/people-ai/` are preserved as authoritative vendor-provided guidance. Do not rewrite their API behavior, catalogs, authentication, windows, or MCP limitations in the orchestration layer.

Never silently merge ambiguous accounts. Never present missing data as negative behavior. Never claim MCP coverage beyond the accounts actually enriched. Never commit credentials, raw customer responses, or generated customer intelligence.

## Modification policy

The People.ai directories under `skills/people-ai/` should be updated independently when People.ai provides newer versions. Avoid editing them merely to fit the External Monitor workflow; adapt behavior in `skills/external-monitor-account-intelligence/` instead.
