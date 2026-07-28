const { chromium } = require('playwright');
const path = require('path');

const FILE = path.resolve(__dirname, 'fixtures/intel-portfolio-preview.html');
const URL = 'file:///' + FILE.replace(/\\/g, '/');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  ✓ ${msg}`); }
  else { failed++; console.log(`  ✗ FAIL: ${msg}`); }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(URL, { waitUntil: 'networkidle' });

  // ── REGION OVERVIEW ──
  console.log('\n=== REGION OVERVIEW ===');

  let h1 = await page.$eval('#app h1', el => el.textContent);
  assert(h1 === 'INTEL', `Title is "INTEL" (got "${h1}")`);

  let tabs = await page.$$eval('#tabBar button', btns => btns.map(b => b.textContent));
  assert(tabs.some(t => t.includes('Region')), `Tab bar has Region tab`);
  assert(tabs.includes('Guide'), `Tab bar has Guide tab`);

  let subtitle = await page.$eval('.subtitle', el => el.textContent);
  assert(subtitle.includes('territor'), `Subtitle mentions territories`);
  assert(subtitle.includes('account'), `Subtitle mentions accounts`);

  let kpiValues = await page.$$eval('.kpi-value', els => els.map(e => e.textContent));
  assert(kpiValues.length === 5, `5 KPI cards rendered (got ${kpiValues.length})`);
  assert(kpiValues[0] === '9', `Accounts KPI is 9 (got "${kpiValues[0]}")`);

  let summaryCard = await page.$eval('.summary-card h2', el => el.textContent);
  assert(summaryCard === 'Executive Summary', `Summary heading is "Executive Summary"`);

  let activityStats = await page.$$eval('.activity-stat .stat-value', els => els.map(e => e.textContent));
  assert(activityStats.length === 5, `5 activity stats rendered`);
  assert(parseInt(activityStats[0]) > 0, `Total activities > 0 (got ${activityStats[0]})`);

  let tableRows = await page.$$eval('.data-table tbody tr', rows => rows.length);
  assert(tableRows === 6, `6 territory rows in table (got ${tableRows})`);

  let openLinks = await page.$$('.drill-link');
  assert(openLinks.length === 6, `6 "Open →" links`);

  // Check avg scores are numeric (signal_score was patched)
  let avgScores = await page.$$eval('.data-table tbody tr td:nth-child(3)', els => els.map(e => e.textContent.trim()));
  let numericScores = avgScores.filter(s => !isNaN(parseInt(s)));
  assert(numericScores.length === 6, `All 6 territories have numeric avg scores (got ${numericScores.length})`);

  // ── DRILL INTO FIRST TERRITORY ──
  console.log('\n=== DRILL: TERRITORY ===');

  await page.click('.data-table tbody tr:first-child .drill-link');
  await page.waitForTimeout(200);

  h1 = await page.$eval('#app h1', el => el.textContent);
  console.log(`  Drilled into: ${h1}`);

  let breadcrumb = await page.$eval('.breadcrumb', el => el.textContent);
  assert(breadcrumb.includes('INTEL'), `Breadcrumb contains INTEL`);

  // Check if we're at account list or went straight to account detail
  let hasTable = await page.$('.data-table');
  let hasAccountLayout = await page.$('.account-layout');

  if (hasTable && !hasAccountLayout) {
    console.log('  → At account list view');
    let accountRows = await page.$$eval('.data-table tbody tr', r => r.length);
    assert(accountRows >= 1, `At least 1 account row (got ${accountRows})`);

    let pills = await page.$$('.status-pill');
    assert(pills.length > 0, `Signal pills rendered`);

    let badges = await page.$$('.match-badge');
    assert(badges.length > 0, `Match badges rendered`);

    // Check signal scores show in table (not dashes)
    let scoreCell = await page.$eval('.data-table tbody tr:first-child td:nth-child(3)', el => el.textContent.trim());
    assert(!isNaN(parseInt(scoreCell)), `Account signal score is numeric in table (got "${scoreCell}")`);

    let firstColWidth = await page.$eval('.data-table td:first-child', el => el.getBoundingClientRect().width);
    assert(firstColWidth <= 300, `Name column width ≤ 300px (got ${Math.round(firstColWidth)})`);

    // ── DRILL INTO ACCOUNT ──
    console.log('\n=== DRILL: ACCOUNT DETAIL ===');
    await page.click('.data-table tbody tr:first-child .drill-link');
    await page.waitForTimeout(200);
  } else {
    console.log('  → Single account, went straight to detail');
  }

  // ── ACCOUNT DETAIL ──
  h1 = await page.$eval('#app h1', el => el.textContent);
  console.log(`  Account: ${h1}`);

  assert((await page.$('.account-layout')) !== null, `Account layout rendered`);
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
    assert((await page.$('.detail-grid')) !== null, `Detail grid visible after expand`);
  }

  let sidebarHeadings = await page.$$eval('.sidebar-card h3', els => els.map(e => e.textContent));
  assert(sidebarHeadings.includes('Account Details'), `Sidebar has Account Details`);
  assert(sidebarHeadings.some(h => h.includes('Activity')), `Sidebar has Activity card`);
  assert(sidebarHeadings.includes('Caveats'), `Sidebar has Caveats`);
  assert((await page.$eval('.account-sidebar', el => el.textContent)).includes('Priority Score'), `Priority Score in sidebar`);

  // Check activity metrics are populated (real data, not dashes)
  let activityCard = await page.$eval('.sidebar-card:nth-child(3)', el => el.textContent);
  console.log(`  Activity card snippet: ${activityCard.substring(0, 100)}`);

  // ── BREADCRUMB BACK TO REGION ──
  console.log('\n=== BREADCRUMB BACK ===');

  await page.click('.breadcrumb a:first-child');
  await page.waitForTimeout(200);

  h1 = await page.$eval('#app h1', el => el.textContent);
  assert(h1 === 'INTEL', `Breadcrumb back to INTEL (got "${h1}")`);
  assert((await page.$$eval('.data-table tbody tr', r => r.length)) === 6, `Back at region with 6 territory rows`);

  // ── GUIDE TAB ──
  console.log('\n=== GUIDE TAB ===');

  await page.click('#tabBar button:last-child');
  await page.waitForTimeout(200);

  assert((await page.$eval('#app h1', el => el.textContent)) === 'Guide', `Guide page title`);

  let guideSections = await page.$$('.guide-section');
  assert(guideSections.length >= 8, `At least 8 guide sections (got ${guideSections.length})`);
  assert((await page.$$('.def-table')).length >= 5, `At least 5 definition tables`);
  assert((await page.$$('.guide .status-pill')).length >= 3, `Guide shows status pills`);
  assert((await page.$$('.guide .match-badge')).length >= 4, `Guide shows match badges`);

  // ── BACK FROM GUIDE ──
  await page.click('#tabBar button:first-child');
  await page.waitForTimeout(200);
  assert((await page.$eval('#app h1', el => el.textContent)) === 'INTEL', `Back from Guide to INTEL`);

  // ── TEST MULTIPLE TERRITORIES ──
  console.log('\n=== MULTI-TERRITORY DRILL ===');

  // Drill into last territory (TERR06 has 2 accounts: AWS GovCloud + Microsoft Airgapped)
  let rows = await page.$$('.data-table tbody tr');
  await rows[rows.length - 1].$eval('.drill-link', el => el.click());
  await page.waitForTimeout(200);

  h1 = await page.$eval('#app h1', el => el.textContent);
  console.log(`  Drilled into: ${h1}`);

  hasTable = await page.$('.data-table');
  hasAccountLayout = await page.$('.account-layout');

  if (hasTable && !hasAccountLayout) {
    let acctCount = await page.$$eval('.data-table tbody tr', r => r.length);
    console.log(`  Accounts in territory: ${acctCount}`);
    assert(acctCount >= 1, `Territory has accounts`);

    // Open last account
    let acctRows = await page.$$('.data-table tbody tr');
    await acctRows[acctRows.length - 1].$eval('.drill-link', el => el.click());
    await page.waitForTimeout(200);
  }

  h1 = await page.$eval('#app h1', el => el.textContent);
  console.log(`  Account: ${h1}`);
  assert((await page.$('.account-layout')) !== null, `Second account layout rendered`);
  assert((await page.$$('.signal-card')).length > 0, `Second account has signal cards`);

  // ── RESPONSIVE ──
  console.log('\n=== RESPONSIVE ===');

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
