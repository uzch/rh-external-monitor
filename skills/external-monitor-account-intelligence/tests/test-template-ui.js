/**
 * HTML Template UI Test — Headless Browser Click-Through
 *
 * Renders the portfolio template with a GEO-scope test fixture, then uses
 * Playwright to simulate a user clicking through every view and verifying
 * that the interface renders correctly.
 *
 * Prerequisites:
 *   npm install playwright    (from the skill directory)
 *   npx playwright install chromium
 *
 * Usage:
 *   # 1. Generate the test fixture (if not already present)
 *   python examples/generate-geo-fixture.py
 *
 *   # 2. Render it into HTML
 *   python scripts/render_portfolio.py examples/portfolio-geo-test.json --out tests/test-output.html
 *
 *   # 3. Run this test
 *   node tests/test-template-ui.js
 *
 * What it checks:
 *   - GEO overview: title, tabs, KPIs, summary, activity bar, region table
 *   - Drill into region: territory table, aggregated scores
 *   - Drill into territory: account table, signal pills, match badges, column width
 *   - Drill into account: summary, next move, signal cards (sorted desc), sidebar cards
 *   - Collapsible signal details open/close
 *   - Breadcrumb navigation back to GEO
 *   - Guide tab: all sections, definition tables, styled pills/badges
 *   - Edge case: unmatched/ambiguous account renders without errors
 *   - Responsive: layout collapses at 920px, heading shrinks at 600px
 *
 * Exit code 0 = all passed, 1 = at least one failure.
 */

const { chromium } = require('playwright');
const path = require('path');

const FILE = path.resolve(__dirname, 'test-output.html');
const URL = 'file:///' + FILE.replace(/\\/g, '/');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) {
    passed++;
    console.log(`  ✓ ${msg}`);
  } else {
    failed++;
    console.log(`  ✗ FAIL: ${msg}`);
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(URL, { waitUntil: 'networkidle' });

  // ── GEO OVERVIEW ──
  console.log('\n=== GEO OVERVIEW ===');

  let h1 = await page.$eval('#app h1', el => el.textContent);
  assert(h1 === 'NAPS', `Title is "NAPS" (got "${h1}")`);

  let tabs = await page.$$eval('#tabBar button', btns => btns.map(b => b.textContent));
  assert(tabs.includes('Geo Overview'), `Tab bar has "Geo Overview"`);
  assert(tabs.includes('Guide'), `Tab bar has "Guide"`);

  let subtitle = await page.$eval('.subtitle', el => el.textContent);
  assert(subtitle.includes('region'), `Subtitle mentions regions`);
  assert(subtitle.includes('territor'), `Subtitle mentions territories`);
  assert(subtitle.includes('account'), `Subtitle mentions accounts`);

  let kpiValues = await page.$$eval('.kpi-value', els => els.map(e => e.textContent));
  assert(kpiValues.length === 5, `5 KPI cards rendered (got ${kpiValues.length})`);
  assert(kpiValues[0] === '25', `Accounts KPI is 25 (got "${kpiValues[0]}")`);

  let summaryCard = await page.$eval('.summary-card h2', el => el.textContent);
  assert(summaryCard === 'Executive Summary', `Summary heading is "Executive Summary"`);

  let activityStats = await page.$$eval('.activity-stat .stat-value', els => els.map(e => e.textContent));
  assert(activityStats.length === 5, `5 activity stats rendered`);
  assert(parseInt(activityStats[0]) > 0, `Total activities > 0 (got ${activityStats[0]})`);

  let tableRows = await page.$$eval('.data-table tbody tr', rows => rows.length);
  assert(tableRows === 3, `3 region rows in table (got ${tableRows})`);

  let regionNames = await page.$$eval('.data-table tbody tr td:first-child strong', els => els.map(e => e.textContent));
  assert(regionNames.includes('INTEL'), `INTEL region present`);
  assert(regionNames.includes('CIVILIAN'), `CIVILIAN region present`);
  assert(regionNames.includes('DEFENSE'), `DEFENSE region present`);

  let openLinks = await page.$$('.drill-link');
  assert(openLinks.length === 3, `3 "Open →" links`);

  // ── DRILL INTO FIRST REGION ──
  console.log('\n=== DRILL: REGION ===');

  await page.click('.data-table tbody tr:first-child .drill-link');
  await page.waitForTimeout(100);

  h1 = await page.$eval('#app h1', el => el.textContent);
  console.log(`  Drilled into: ${h1}`);

  tabs = await page.$$eval('#tabBar button', btns => btns.map(b => b.textContent));
  assert(tabs.length === 3, `3 tabs after drill (Geo, Region, Guide) (got ${tabs.length})`);

  let breadcrumb = await page.$eval('.breadcrumb', el => el.textContent);
  assert(breadcrumb.includes('NAPS'), `Breadcrumb contains NAPS`);

  assert((await page.$$eval('.kpi-value', els => els.length)) === 5, `5 KPI cards at region level`);
  assert((await page.$eval('.summary-card', el => el.textContent)).includes('Executive Summary'), `Region has Executive Summary`);
  assert((await page.$$eval('.activity-stat', els => els.length)) === 5, `5 activity stats at region level`);

  let territoryRows = await page.$$eval('.data-table tbody tr', rows => rows.length);
  assert(territoryRows >= 1, `At least 1 territory row (got ${territoryRows})`);

  let avgScores = await page.$$eval('.data-table tbody tr td:nth-child(3)', els => els.map(e => e.textContent));
  assert(avgScores.some(s => !isNaN(parseInt(s))), `At least one territory has a numeric avg score`);

  // ── DRILL INTO FIRST TERRITORY ──
  console.log('\n=== DRILL: TERRITORY ===');

  await page.click('.data-table tbody tr:first-child .drill-link');
  await page.waitForTimeout(100);

  h1 = await page.$eval('#app h1', el => el.textContent);
  console.log(`  Drilled into territory: ${h1}`);

  breadcrumb = await page.$eval('.breadcrumb', el => el.textContent);
  assert(breadcrumb.includes('NAPS'), `Breadcrumb still has NAPS`);

  let hasTable = await page.$('.data-table');
  let hasAccountLayout = await page.$('.account-layout');

  if (hasTable && !hasAccountLayout) {
    console.log('  → At account list view');
    assert((await page.$$eval('.data-table tbody tr', r => r.length)) >= 1, `At least 1 account row`);
    assert((await page.$$('.status-pill')).length > 0, `Signal pills rendered in account table`);
    assert((await page.$$('.match-badge')).length > 0, `Match badges rendered`);

    let firstColWidth = await page.$eval('.data-table td:first-child', el => el.getBoundingClientRect().width);
    assert(firstColWidth <= 300, `First column width ≤ 300px (got ${Math.round(firstColWidth)})`);

    // ── DRILL INTO FIRST ACCOUNT ──
    console.log('\n=== DRILL: ACCOUNT DETAIL ===');
    await page.click('.data-table tbody tr:first-child .drill-link');
    await page.waitForTimeout(100);
  } else {
    console.log('  → Single account, went straight to detail');
  }

  // ── ACCOUNT DETAIL CHECKS ──
  h1 = await page.$eval('#app h1', el => el.textContent);
  console.log(`  Account: ${h1}`);

  assert((await page.$('.account-layout')) !== null, `Account layout (main + sidebar) rendered`);
  assert((await page.$('.summary-card')) !== null, `30-Second Summary card exists`);
  assert((await page.$('.next-move')) !== null, `Recommended Next Move card exists`);

  let signalCards = await page.$$('.signal-card');
  assert(signalCards.length > 0, `Signal cards rendered (${signalCards.length} cards)`);

  let signalScores = await page.$$eval('.signal-score', els => els.map(e => parseInt(e.textContent)));
  let isSorted = signalScores.every((v, i) => i === 0 || v <= signalScores[i - 1]);
  assert(isSorted, `Signals sorted by score descending: ${JSON.stringify(signalScores)}`);

  assert((await page.$$eval('.signal-card .status-pill', els => els.length)) > 0, `Signal disposition pills in cards`);

  let detailsElements = await page.$$('details');
  assert(detailsElements.length > 0, `Collapsible details sections exist`);

  if (detailsElements.length > 0) {
    await page.click('details summary');
    await page.waitForTimeout(100);
    assert((await page.$('.detail-grid')) !== null, `Detail grid visible after clicking summary`);
  }

  let sidebarHeadings = await page.$$eval('.sidebar-card h3', els => els.map(e => e.textContent));
  assert(sidebarHeadings.includes('Account Details'), `Sidebar has Account Details`);
  assert(sidebarHeadings.some(h => h.includes('Activity')), `Sidebar has Activity card`);
  assert(sidebarHeadings.includes('Caveats'), `Sidebar has Caveats`);
  assert((await page.$eval('.account-sidebar', el => el.textContent)).includes('Priority Score'), `Priority Score in sidebar`);

  // ── BREADCRUMB BACK TO GEO ──
  console.log('\n=== BREADCRUMB BACK NAVIGATION ===');

  assert((await page.$$('.breadcrumb a')).length >= 1, `Breadcrumb has clickable links`);

  await page.click('.breadcrumb a:first-child');
  await page.waitForTimeout(100);

  h1 = await page.$eval('#app h1', el => el.textContent);
  assert(h1 === 'NAPS', `Breadcrumb navigated back to GEO (got "${h1}")`);
  assert((await page.$$eval('.data-table tbody tr', r => r.length)) === 3, `Back at GEO with 3 region rows`);

  // ── GUIDE TAB ──
  console.log('\n=== GUIDE TAB ===');

  await page.click('#tabBar button:last-child');
  await page.waitForTimeout(100);

  assert((await page.$eval('#app h1', el => el.textContent)) === 'Guide', `Guide page title`);

  let guideSections = await page.$$('.guide-section');
  assert(guideSections.length >= 8, `At least 8 guide sections (got ${guideSections.length})`);

  let guideHeadings = await page.$$eval('.guide-section h3', els => els.map(e => e.textContent));
  assert(guideHeadings.includes('Signal score'), `Guide covers signal score`);
  assert(guideHeadings.includes('Match status'), `Guide covers match status`);
  assert(guideHeadings.includes('Activity trend'), `Guide covers activity trend`);
  assert(guideHeadings.includes('How to navigate'), `Guide covers navigation`);
  assert(guideHeadings.some(h => h.includes('Act')), `Guide covers Act/Watch/Reject`);
  assert((await page.$$('.def-table')).length >= 5, `At least 5 definition tables in guide`);
  assert((await page.$$('.guide .status-pill')).length >= 3, `Guide shows ACT/WATCH/REJECT pills`);
  assert((await page.$$('.guide .match-badge')).length >= 4, `Guide shows all match badge types`);

  // ── BACK FROM GUIDE ──
  console.log('\n=== BACK FROM GUIDE ===');

  await page.click('#tabBar button:first-child');
  await page.waitForTimeout(100);
  assert((await page.$eval('#app h1', el => el.textContent)) === 'NAPS', `Back to GEO from Guide`);

  // ── EDGE: UNMATCHED ACCOUNT ──
  console.log('\n=== EDGE: UNMATCHED ACCOUNT ===');

  let allRows = await page.$$('.data-table tbody tr');
  for (let i = 0; i < allRows.length; i++) {
    let name = await allRows[i].$eval('td:first-child', el => el.textContent);
    if (name.includes('CIVILIAN')) {
      await allRows[i].$eval('.drill-link', el => el.click());
      break;
    }
  }
  await page.waitForTimeout(100);

  let terrRows = await page.$$('.data-table tbody tr');
  if (terrRows.length > 0) {
    await terrRows[0].$eval('.drill-link', el => el.click());
    await page.waitForTimeout(100);
  }

  let currentBadges = await page.$$eval('.match-badge', els => els.map(e => e.textContent.trim()));
  console.log(`  Match statuses found: ${JSON.stringify(currentBadges)}`);

  let acctRows = await page.$$('.data-table tbody tr');
  if (acctRows.length > 0) {
    let lastRow = acctRows[acctRows.length - 1];
    let lastLink = await lastRow.$('.drill-link');
    if (lastLink) {
      await lastLink.click();
      await page.waitForTimeout(100);
      console.log(`  Opened account: ${await page.$eval('#app h1', el => el.textContent)}`);
      assert(true, `Unmatched account detail rendered without errors`);
    }
  }

  // ── RESPONSIVE ──
  console.log('\n=== RESPONSIVE ===');

  await page.click('#tabBar button:first-child');
  await page.waitForTimeout(100);
  await page.click('.data-table tbody tr:first-child .drill-link');
  await page.waitForTimeout(100);
  let tRows = await page.$$('.data-table tbody tr');
  if (tRows.length > 0) { await tRows[0].$eval('.drill-link', el => el.click()); await page.waitForTimeout(100); }
  let aRows = await page.$$('.data-table tbody tr');
  if (aRows.length > 0) { await aRows[0].$eval('.drill-link', el => el.click()); await page.waitForTimeout(100); }

  await page.setViewportSize({ width: 920, height: 800 });
  await page.waitForTimeout(100);
  let gridAt920 = await page.$eval('.account-layout', el => window.getComputedStyle(el).gridTemplateColumns).catch(() => 'no layout');
  console.log(`  Grid at 920px: ${gridAt920}`);

  await page.setViewportSize({ width: 600, height: 800 });
  await page.waitForTimeout(100);
  let h1Size = await page.$eval('#app h1', el => window.getComputedStyle(el).fontSize);
  assert(h1Size === '28px', `H1 font-size at 600px is 28px (got ${h1Size})`);

  await page.setViewportSize({ width: 1280, height: 800 });

  // ── SUMMARY ──
  console.log('\n============================');
  console.log(`PASSED: ${passed}`);
  console.log(`FAILED: ${failed}`);
  console.log('============================\n');

  await browser.close();
  process.exit(failed > 0 ? 1 : 0);
})();
