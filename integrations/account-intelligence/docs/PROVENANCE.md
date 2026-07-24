# Provenance and modification policy

## Original source skills

The following directories came from the People.ai-provided `DataPullerSkills.zip` and are included intact except for removal of macOS metadata files such as `.DS_Store` and `__MACOSX`:

- `skills/people-ai/sales-data-explorer`
- `skills/people-ai/sales-data-pull`
- `skills/people-ai/sales-insights`

## Added External Monitor layer

The following content was added for the External Monitor use case:

- `skills/external-monitor-account-intelligence`
- root `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.env.example`
- `.gitignore.example`
- `docs/ARCHITECTURE.md`
- `docs/PROVENANCE.md`

The original People.ai skills should be updated independently when People.ai provides newer versions. Avoid editing them merely to fit the External Monitor workflow; adapt behavior in the orchestration layer instead.
