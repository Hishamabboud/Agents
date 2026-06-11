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

  // Capture API responses
  const jobApiResponses = [];
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('get_jobs') || url.includes('caas-api') && url.includes('jobs')) {
      try {
        const text = await response.text();
        jobApiResponses.push({ url, status: response.status(), body: text.substring(0, 5000) });
      } catch(e) {}
    }
  });

  try {
    console.log('Loading Bosch NL jobs page...');
    await page.goto('https://jobs.bosch.com/en/?country=nl', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    await page.waitForTimeout(3000);

    // Now try to search for software engineer via the search box
    const searchInput = await page.$('input[type="search"], input[name*="search"], input[placeholder*="Job title"], input[placeholder*="Keywords"], [role="searchbox"]');
    if (searchInput) {
      console.log('Found search input, typing...');
      await searchInput.click();
      await searchInput.fill('software engineer');
      await page.waitForTimeout(1000);
      // Submit search
      const searchBtn = await page.$('button[type="submit"], button[aria-label*="search"], button[aria-label*="Search"]');
      if (searchBtn) {
        await searchBtn.click();
      } else {
        await searchInput.press('Enter');
      }
      await page.waitForTimeout(5000);
    }

    // Get all text on the page after search
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 5000));
    console.log('Page body after search:', bodyText);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-search-results.png', fullPage: true });

    // Log captured API responses
    console.log('\nCaptured API responses:', jobApiResponses.length);
    jobApiResponses.forEach(r => {
      console.log(`\nURL: ${r.url}`);
      console.log('Status:', r.status);
      console.log('Body:', r.body.substring(0, 1000));
    });
  } catch(e) {
    console.error('Error:', e.message);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-error2.png' }).catch(() => {});
  }

  await browser.close();
})();
