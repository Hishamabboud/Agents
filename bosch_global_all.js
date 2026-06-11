const { chromium } = require('playwright');
const fs = require('fs');

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
  const apiResponses = [];
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('get_jobs') && url.includes('search_term')) {
      try {
        const text = await response.text();
        apiResponses.push({ url, status: response.status(), body: text });
      } catch(e) {}
    }
  });

  // Try global Bosch search (no country filter) with software engineer keyword
  await page.goto('https://jobs.bosch.com/en/', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  await page.waitForTimeout(3000);

  // Fill the keyword search
  const searchInput = await page.$('input[name="searchTerm"]');
  if (searchInput) {
    console.log('Found searchTerm');
    await searchInput.fill('software engineer java');
    await searchInput.press('Enter');
    await page.waitForTimeout(6000);

    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 5000));
    console.log('Results:', bodyText.substring(0, 3000));
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-global-search.png', fullPage: false });
  }

  // Also try searching for Breda location
  await page.goto('https://jobs.bosch.com/en/', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  await page.waitForTimeout(2000);

  // Fill the location search
  const locationInput = await page.$('input[placeholder="Bosch Location"]');
  if (locationInput) {
    console.log('Found location input');
    await locationInput.fill('Breda');
    await page.waitForTimeout(2000);
    // Try clicking first suggestion
    const suggestion = await page.$('[role="option"], .suggestion, .autocomplete-item');
    if (suggestion) {
      await suggestion.click();
    } else {
      await locationInput.press('Enter');
    }
    await page.waitForTimeout(4000);
    const bodyText2 = await page.evaluate(() => document.body.innerText.substring(0, 5000));
    console.log('\nBreda search results:', bodyText2.substring(0, 2000));
  }

  // Log API responses
  console.log('\nAPI responses with search_term:', apiResponses.length);
  apiResponses.forEach(r => {
    const json = JSON.parse(r.body || '{}');
    const resultData = json['_embedded']?.['rh:result']?.[0];
    const count = resultData?.meta?.[0]?.count || 0;
    const jobs = resultData?.data || [];
    console.log(`Count: ${count}, Jobs: ${jobs.length}`);
    jobs.slice(0, 20).forEach(j => {
      console.log(`  - ${j.name} | ${j.location?.city}, ${j.location?.country}`);
    });
  });

  await browser.close();
})();
