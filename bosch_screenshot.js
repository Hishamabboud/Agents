const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--ignore-certificate-errors', '--no-sandbox']
  });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  // Navigate to Bosch NL jobs and take screenshot showing no software engineer
  await page.goto('https://jobs.bosch.com/en/?country=nl', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  await page.waitForTimeout(3000);
  await page.screenshot({
    path: '/home/user/Agents/output/screenshots/bosch-medior-se-after-submit.png',
    fullPage: false
  });
  console.log('Screenshot taken');

  // Also do the keyword search to show 0 results
  const searchInput = await page.$('input[name="searchTerm"]');
  if (searchInput) {
    await searchInput.fill('software engineer');
    await searchInput.press('Enter');
    await page.waitForTimeout(4000);
    await page.screenshot({
      path: '/home/user/Agents/output/screenshots/bosch-search-no-results.png',
      fullPage: false
    });
    console.log('Search result screenshot taken');
    const text = await page.evaluate(() => document.body.innerText.substring(0, 1000));
    console.log('Result text:', text.substring(0, 300));
  }

  await browser.close();
})();
