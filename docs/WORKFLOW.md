# Workflow

1. Accept an exact scope type and value.
2. Resolve matching Enterprise Accounts records without inferring missing hierarchy values.
3. Normalize identity and record match status.
4. Pull shared People.ai Query API fields in batches using the installed validated catalog. Fail on silent column drops.
5. Compute an explainable internal priority score. Missing fields reduce confidence and are not treated as negative evidence.
6. Enrich the highest-priority accounts, normally five and never more than ten, through Backstory MCP. Keep the in-scope and enriched counts separate.
7. If requested, attach external public signals with URL, publisher, date, and a distinct source type.
8. Write and validate `portfolio.json`.
9. Render HTML or map the same artifact to Google Sheets tabs.

The result must label windows, source types, match status, coverage, caveats, and the difference between evidence and agent interpretation.
