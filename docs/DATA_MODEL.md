# Data model

The primary artifact is `portfolio.json`, validated by [`portfolio-output.schema.json`](../skills/external-monitor-account-intelligence/schemas/portfolio-output.schema.json).

At the top level it records scope, summary, accounts, run metadata, and caveats. Each account retains:

- stable local identity and match status;
- GEO, region, pod, territory, and segment;
- People.ai identifiers and metrics;
- deterministic internal priority and reasons;
- Backstory status, risks, next steps, topics, and engaged people when enriched;
- optional external signals;
- provenance and time windows.

Use `null` for unavailable values. `0` means the source explicitly returned zero. `KEEP`, `WATCH`, and `REJECT` are output dispositions, not claims about customer intent.
