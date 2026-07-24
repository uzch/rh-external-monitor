# Changelog — sales-insights

## 0.1.3 — 2026-07-07

- **Two MCP lanes added, both probed live 2026-07-07 and both free-tier** (no credit notice;
  evidence: workbench `engagements/nvidia/evidence/mcp-2026-07-07-news-situation-probe.md`):
  - `account_company_news` — outside-in filings/earnings signals on a named account (public
    companies only; 200+ items on a mega-cap → synthesize, never dump).
  - `situation_search` — deal-precedent finder: ≤4 historical deals >70% similar, with dated
    actions and resolution outcomes. **Verified contract correction:** this is per-opportunity
    precedent lookup, NOT a cross-account topic search — the no-enumeration honesty rule
    stands (new eval case-013 pins it).
- Windows table gains an "Own windows" free row for both tools; procedure step 3 (free pass)
  covers when to reach for each. Description triggers extended (news / "have we handled a
  deal situation like this before").

## 0.1.2 — 2026-07-07

- **Output contract (hard rule)** — fixes an observed failure in a customer session (Codex,
  2026-07-02): the reply was one big JSON dump instead of an answer. The user-facing reply is
  always written prose in the rollup shape; MCP tool responses are input to synthesize from,
  never output to show; script-written files are handed over by path. Verification now checks
  for it; new eval case-010-no-raw-json guards the regression. No tool-use or credit-discipline
  changes.

## 0.1.1 — 2026-07-02

- Backstory branding across display copy (docs and merged-signal provenance note). The MCP URL
  is unchanged — `https://mcp.people.ai/mcp` remains the working endpoint, and the INSTALL
  warning about the `backstory.ai` URL stays.
- `merge_signals.py` escapes `</` in the embedded JSON when re-rendering the dashboard.

## 0.1.0 — 2026-07-02

- Initial release, companion to `sales-data-pull`.
- Three-tier window model, each tier verified against the live service: 30-day free MCP tools;
  90-day reach through `ask_sales_ai_*` when the question explicitly requests the window
  (provider-confirmed 2026-07-02 — the 30d in those tool descriptions is a known doc bug);
  longer windows via the Query API companion skill. A 1-year MCP lookback is a logged product
  gap, not promised.
- Scope selection comes from the companion skill's data blob or explicit account names — the MCP
  has no account/opportunity/user enumeration, and the skill says so rather than implying full
  coverage.
- Credit discipline: free tools first, at most 10 credit-consuming calls per run, announced
  before spending and reported after; default segmentation is top-10 accounts by activity.
- `scripts/merge_signals.py` fills the engagement-dashboard blob's reserved `peopleai_signals`
  key and re-renders the offline HTML.
- No credentials of any kind ship in this skill — it runs entirely under the user's own
  People.ai MCP login.
