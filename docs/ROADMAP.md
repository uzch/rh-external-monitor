# Roadmap

## Current

- Enterprise Accounts registry connected (`data/local/Enterprise Accounts.csv`) with loader script.
- Account registry and NAPS scope model defined.
- People.ai batch metric lane and Backstory enrichment lane specified.
- Shared portfolio JSON contract, example, validator, and HTML renderer present.
- Spreadsheet exporter (`export_sheets.py`) producing formatted `.xlsx` with Portfolio and Signals tabs.
- MCP enrichment merge script (`enrich_portfolio.py`) with `signal_score` computation.
- External research runs by default with parallel subagent support.
- `signal_score` (average of per-signal scores, rounded integer) is the user-facing metric at all hierarchy levels. `internal_priority_score` is backend triage only.
- Codex- and Claude-compatible agent guidance present.

## Next

- External research Phase 2: Add source-type badges or color coding to the HTML portfolio template so external signals are visually distinct from internal signals. Add a source-type filter to the portfolio view.
- External research Phase 3: Add a lightweight research cache or "last researched" timestamp to avoid redundant searches across runs. Add batch research queue management for larger scopes.
- Add end-to-end evaluation with representative, non-sensitive fixtures.

## Later

- Provide a hosted interactive Portfolio View and Account View.
- Add refresh, caching, and run history without weakening provenance or ambiguity controls.
- Measure prioritization usefulness with seller feedback while keeping agent interpretation distinct from source facts.
