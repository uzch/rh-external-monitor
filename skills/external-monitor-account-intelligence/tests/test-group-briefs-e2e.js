const { chromium } = require('playwright');
const path = require('path');

let passed = 0, failed = 0;
function assert(cond, msg) {
  if (cond) { console.log('  ✓ ' + msg); passed++; }
  else { console.log('  ✗ FAIL: ' + msg); failed++; }
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const htmlPath = 'file:///' + path.resolve('tests/test-output.html').replace(/\\/g, '/');
  await page.goto(htmlPath);
  await page.waitForTimeout(300);

  // === TOP LEVEL: _top brief ===
  console.log('=== TOP LEVEL: _top brief ===');
  var summaryText = await page.$eval('.summary-card p', function(el) { return el.textContent.trim(); });
  assert(summaryText.includes('Intelligence and defense modernization dominate'),
    'Top-level summary uses _top brief (got: "' + summaryText.substring(0, 80) + '...")');
  assert(!/contains \d+ accounts across/.test(summaryText),
    'Top-level summary is NOT the build_portfolio placeholder');

  // === DRILL INTO REGION: INTEL ===
  console.log('\n=== DRILL: INTEL region brief ===');
  var rows = await page.$$('.data-table tbody tr');
  for (var i = 0; i < rows.length; i++) {
    var name = await rows[i].$eval('td:first-child', function(el) { return el.textContent.trim(); });
    if (name === 'INTEL') {
      await rows[i].$eval('.drill-link', function(el) { el.click(); });
      break;
    }
  }
  await page.waitForTimeout(200);
  summaryText = await page.$eval('.summary-card p', function(el) { return el.textContent.trim(); });
  assert(summaryText.includes('DIA and NSA are driving the bulk'),
    'INTEL region brief uses group_briefs["INTEL"] (got: "' + summaryText.substring(0, 80) + '...")');
  assert(summaryText.includes('Maryland Procurement Office'),
    'INTEL brief mentions MPO');

  // === DRILL INTO TERRITORY: FED_INTEL_ENT_POD_TERR01 ===
  console.log('\n=== DRILL: TERR01 territory brief ===');
  rows = await page.$$('.data-table tbody tr');
  for (var i = 0; i < rows.length; i++) {
    var name = await rows[i].$eval('td:first-child', function(el) { return el.textContent.trim(); });
    if (name === 'FED_INTEL_ENT_POD_TERR01') {
      await rows[i].$eval('.drill-link', function(el) { el.click(); });
      break;
    }
  }
  await page.waitForTimeout(200);

  var summaryCard = await page.$('.summary-card p');
  if (summaryCard) {
    summaryText = await summaryCard.evaluate(function(el) { return el.textContent.trim(); });
    assert(summaryText.includes('DIA and NSA both show strong engagement'),
      'TERR01 territory brief uses group_briefs (got: "' + summaryText.substring(0, 80) + '...")');
  } else {
    console.log('  (territory had single account, skipped to detail)');
  }

  // === BREADCRUMB BACK TO GEO ===
  console.log('\n=== NAVIGATE BACK: breadcrumb to GEO ===');
  await page.click('.breadcrumb a:first-child');
  await page.waitForTimeout(200);
  summaryText = await page.$eval('.summary-card p', function(el) { return el.textContent.trim(); });
  assert(summaryText.includes('Intelligence and defense modernization'),
    'Back at GEO, _top brief restored');

  // === DRILL INTO CIVILIAN REGION ===
  console.log('\n=== DRILL: CIVILIAN region brief ===');
  rows = await page.$$('.data-table tbody tr');
  for (var i = 0; i < rows.length; i++) {
    var name = await rows[i].$eval('td:first-child', function(el) { return el.textContent.trim(); });
    if (name === 'CIVILIAN') {
      await rows[i].$eval('.drill-link', function(el) { el.click(); });
      break;
    }
  }
  await page.waitForTimeout(200);
  summaryText = await page.$eval('.summary-card p', function(el) { return el.textContent.trim(); });
  assert(summaryText.includes('IRS modernization is the standout'),
    'CIVILIAN region brief uses group_briefs["CIVILIAN"] (got: "' + summaryText.substring(0, 80) + '...")');

  // === DRILL INTO FINANCIALS TERRITORY ===
  console.log('\n=== DRILL: Financials territory brief ===');
  rows = await page.$$('.data-table tbody tr');
  for (var i = 0; i < rows.length; i++) {
    var name = await rows[i].$eval('td:first-child', function(el) { return el.textContent.trim(); });
    if (name === 'FED_CIVILIAN_FINANCIALS_ENT_POD_TERR08') {
      await rows[i].$eval('.drill-link', function(el) { el.click(); });
      break;
    }
  }
  await page.waitForTimeout(200);
  summaryCard = await page.$('.summary-card p');
  if (summaryCard) {
    summaryText = await summaryCard.evaluate(function(el) { return el.textContent.trim(); });
    assert(summaryText.includes('IRS modernization drives this territory'),
      'Financials territory brief uses group_briefs (got: "' + summaryText.substring(0, 80) + '...")');
  } else {
    console.log('  (territory went straight to account detail)');
  }

  // === DEFENSE REGION ===
  console.log('\n=== DRILL: DEFENSE region brief ===');
  await page.click('.breadcrumb a:first-child');
  await page.waitForTimeout(200);
  rows = await page.$$('.data-table tbody tr');
  for (var i = 0; i < rows.length; i++) {
    var name = await rows[i].$eval('td:first-child', function(el) { return el.textContent.trim(); });
    if (name === 'DEFENSE') {
      await rows[i].$eval('.drill-link', function(el) { el.click(); });
      break;
    }
  }
  await page.waitForTimeout(200);
  summaryText = await page.$eval('.summary-card p', function(el) { return el.textContent.trim(); });
  assert(summaryText.includes('Army CECOM and General Dynamics'),
    'DEFENSE region brief uses group_briefs["DEFENSE"] (got: "' + summaryText.substring(0, 80) + '...")');

  console.log('\n============================');
  console.log('PASSED: ' + passed);
  console.log('FAILED: ' + failed);
  console.log('============================');
  await browser.close();
  process.exit(failed > 0 ? 1 : 0);
})();
