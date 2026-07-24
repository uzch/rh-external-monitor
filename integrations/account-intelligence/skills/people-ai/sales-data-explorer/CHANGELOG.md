# Changelog — sales-data-explorer

## 0.2.0 — 2026-07-07

- **REST raw-records lane** (`scripts/rest_query.py` + `references/rest-catalog.json`):
  record-level reads the metric export can't answer, over the same key (different token
  endpoint `/auth/v1/tokens` handled inside the runner). 12 endpoints live-validated
  2026-07-07 on the served OpenAPI spec (`assets/api-specs/peopleai-rest-api/`):
  activities (all + email/call/meeting), participants (title/seniority/department,
  join on `activity_uid` ↔ `uid` proven), CRM reads (accounts, contacts, **leads** — absent
  from the Query API entirely, opportunities, teams, team-members), and per-contact weekly
  engagement history (`contact-id` + `last-n-days`, 0–100 scores).
- Same gate discipline as the export lane: unvalidated endpoints and params are refused
  before any call; FIELD DROP (validated field absent in tenant) aborts delivery.
- Params are strictly live-proven: `account-id`/`contact-id` take the long People.ai `id`
  (string/crm_id → 400); `last-n-days` on activities/participants/engagement;
  `activity-uid` on participants. Everything else: pull + filter client-side.
- Cross-lane consistency verified: one meeting's `uid` from the REST lane found in a
  Query API export scoped to the same timestamp window.
- query-guide trap #5 recorded: range filters go in one clause node (`$and` of two nodes
  on the same attribute → HTTP 500).

## 0.1.1 — 2026-07-07

- Bring-your-own-key bootstrap alignment: the missing-credentials error now carries the
  key-file schema and points at the installed `sales-data-pull/scripts/` location (one key
  serves the bundle); INSTALL.md and SKILL.md point key-less users at the sales-data-pull
  Key setup flow. No query or gate changes.

## 0.1.0 — 2026-07-02

- Initial release: ad-hoc questions and custom tables/reports over the Backstory Query API,
  gated end-to-end on the firm's live-verified column vocabulary.
- `references/catalog.json` — 75 verified columns across user / account / opportunity /
  activity / person objects, with the validated period vocabulary (retrospective +
  future/upcoming windows) and known multi-column expansions. Known-bad columns are excluded
  by name with reasons (unpopulated AI summary columns; a tenant row-killer metric).
- `scripts/run_query.py` — two deterministic gates: refuses any slug/variation outside the
  catalog *before* calling (the API drops unknown columns silently), and refuses to deliver
  results when the returned column count falls short *after*. Emits CSV always; `--html`
  renders a single-file styled table (light/dark/print) in the Engagement 360 design language.
- `references/query-guide.md` — validated filter shapes and the four traps (object-shaped
  attribute nodes, epoch-ms values, silently-ignored unsupported filters, silent column drops),
  plus worked examples.
- Credentials: reuses the bundle's single pilot key (found in sales-data-pull automatically);
  env vars override.
