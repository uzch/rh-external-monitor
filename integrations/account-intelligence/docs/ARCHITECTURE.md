# Architecture

## Source layer

- Enterprise Accounts: authoritative account hierarchy and selection scope.
- People.ai Query API: batch account, activity, opportunity, user, and engagement metrics.
- Backstory MCP: deeper account narratives, risks, next steps, people, activity, and company news.

## Orchestration layer

The External Monitor skill:

1. resolves the requested hierarchy scope;
2. identifies the account set;
3. creates batch Query API requests;
4. normalizes returned metrics;
5. ranks accounts using explicit, inspectable logic;
6. selects a bounded set for MCP enrichment;
7. produces one portfolio JSON artifact.

## Presentation layer

The same JSON artifact can drive:

- a static or hosted HTML Portfolio View and Account View;
- Google Sheets output tabs and formula-driven views;
- a future React interface.

The presentation layer must not contain business logic that cannot be reproduced from the JSON artifact.
