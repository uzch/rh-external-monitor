# Changelog — sales-data-pull

## 0.4.1 — 2026-07-07

- **Bring-your-own-key bootstrap.** The bundle now ships keyless by design; the customer's
  tenant key (Query API `client_id` + `client_secret`) is wired in once at setup — typically
  by the user's AI assistant ("wire in my Backstory API key"). In support of that flow:
  `--check-key` on `pull_sales_data.py` (auth-only verification: `✓ API key works` or the
  named failure), a **Key setup** section in SKILL.md plus key-setup trigger phrases in the
  description, agent-facing wiring steps in the bundle README and INSTALL.md (exact path,
  exact JSON, every-installed-copy rule), and a missing-credentials error that carries the
  key-file schema so a cold run is self-explanatory. No API surface or blob changes.

## 0.4.0 — 2026-07-02

- **Upcoming meetings (next 14 days)** — the product's own forward-looking dashboard column,
  now in the pull (validated in-tenant 2026-07-02, incl. the future window vocabulary):
  a seller KPI tile ("involving the seller", from user metrics), a per-account "Upcoming 14d"
  column in the engaged-accounts table (any participant), and an "N upcoming" line in the
  book-strip tooltip for accounts with future meetings. Blob keys (additive):
  `summary.upcoming_meetings_14d`, `owned_accounts[].upcoming_meetings_14d`,
  `account_rollup[].upcoming_meetings_14d`. Packet expectations: user-metrics 23 columns,
  accounts-owned 17.
- Zero-state rules unchanged: no metrics row → no fabricated tile; upcoming = 0 renders as a
  real 0 (a forward-looking signal, per the product's own dashboard idiom).
- Considered and **rejected** for this release: per-activity AI summary columns
  (`ootb_activity_summary_ai`) — the API returns the 4 columns but every sampled cell is empty
  in this tenant and in a control tenant (2026-07-02). Re-evaluate when the pipeline populates it.

## 0.3.0 — 2026-07-02

- Backstory branding across display copy (dashboard eyebrow, section copy, source line
  "Backstory Query API — formerly People.ai", skill docs). Technical surface unchanged:
  `api.people.ai` base URL, packet slugs, key-file and env-var names.
- Disclosure moved to the point of reading: the "Data notes & provenance" list is gone; metric
  semantics are inline (seller KPIs say "involving <seller>", book sections say "all
  participants", every tile keeps its window sublabel) and machine-level notes sit behind a
  one-line footer plus a "Data notes" disclosure. `_meta.caveats` in the JSON is unchanged.
- Honest-zero handling: when every windowed user metric reads 0 (e.g. aggregates lagging an
  intake fix), the KPI board collapses those tiles to one sentence backed by the book's real
  activity counts, and the verbatim metrics table collapses the zero wall the same way.
- Quality pass: print stylesheet (light palette, no split cards), `color-scheme` declared,
  forced-colors support on data marks, keyboard support on the book strip (single tab stop,
  arrow keys, focus tooltip identical to hover), focus-visible outlines, horizontal-scroll
  guard on tables at mobile widths, chart marks now follow live theme changes.
- Hardening: embedded JSON escapes `</` so activity subjects can never truncate the document.

## 0.2.0 — 2026-07-02

- Bundled dashboard template (`scripts/template.html`) is now the default HTML render — a
  single offline file, light + dark, no flags needed. `--template <path>` still swaps in an
  alternate template; `--template none` skips HTML. Output name: `<Seller> — Engagement 360.html`.
- The dashboard is adaptive: sections without data collapse to one line — no empty tabs, no
  zero-filled tiles. Includes seller KPI tiles with window-exact trend deltas, the full book as
  an engagement-sorted strip, weekly activity small-multiples with a table view, an engaged-
  accounts table with per-row drill-in, opportunities by amount, all user metrics verbatim, and
  the data-notes block.
- Blob enriched (additive, template-schema-compatible): account rows now carry engagement
  level, exec activities, open-opp counts and amounts, last meeting date, and API-canonical
  30/90-day counts; activity rows carry `external` and `opportunity`.
- Meeting-count semantics made explicit and labeled: user-metric "External Meetings" = meetings
  involving the seller (headline KPI); book counts = all participants on owned accounts
  (account rows). The computed book numbers reproduce the API's account metrics exactly.

## 0.1.1 — 2026-07-02

- Validated end-to-end in the production tenant: all five packets return 100% of expected columns.
- Removed `ootb_user_total_activity` from `user-metrics.json` (22 columns now): in this tenant it
  returns 0 rows when combined with other metric columns. `Total External Activities (Last 30 Days)`
  covers the need.
- New warning when a resolved seller has no metric row — user metrics are computed for a subset of
  the roster, so an empty metrics row is a real, non-error case.
- API-call-count guidance now scales with book size (≈5 + 1 per 100 owned accounts).

## 0.1.0 — 2026-07-02

- Initial release: five validated Query API packets (roster, user metrics, accounts owned,
  activities, opportunities); fuzzy seller-name resolution with candidate lists; output as an
  engagement-dashboard JSON blob with optional single-file HTML render.
- Owner filters on the activity/opportunity objects are ignored server-side (validated) — packets
  filter activities by owned-account names + time window and opportunities by close-date range,
  with owner matching client-side.
- No credentials inside the skill: the API key ships as a separate `peopleai-key.local.json`,
  swappable without re-authoring.
