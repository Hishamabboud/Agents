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

  // Capture ALL CaaS API responses
  const apiResponses = [];
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('caas-api') || url.includes('get_jobs') || url.includes('smartrecruiters')) {
      try {
        const text = await response.text();
        apiResponses.push({ url, status: response.status(), body: text });
      } catch(e) {}
    }
  });

  // Navigate to the Bosch jobs site and perform a keyword search
  await page.goto('https://jobs.bosch.com/en/?country=nl', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  await page.waitForTimeout(3000);

  // Take screenshot first
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-01-initial.png', fullPage: false });

  // Find the search input - it might be a different selector
  const allInputs = await page.$$eval('input', els =>
    els.map(el => ({
      type: el.type,
      name: el.name,
      id: el.id,
      placeholder: el.placeholder,
      className: el.className.substring(0, 50),
      visible: el.offsetParent !== null,
      rect: el.getBoundingClientRect ? {
        top: el.getBoundingClientRect().top,
        left: el.getBoundingClientRect().left,
        width: el.getBoundingClientRect().width
      } : null
    }))
  );
  console.log('All inputs:', JSON.stringify(allInputs, null, 2));

  // Try clicking the search area
  const searchArea = await page.$('[data-testid="search-input"], [aria-label="Search"], .search-input, #search, input[name="q"]');
  if (searchArea) {
    console.log('Found search area');
    await searchArea.click({ force: true });
    await searchArea.fill('software engineer');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-02-after-search.png', fullPage: false });
    const text = await page.evaluate(() => document.body.innerText.substring(0, 3000));
    console.log('After search:', text);
  } else {
    // Try to click on the search by JS
    const jsResult = await page.evaluate(() => {
      const inputs = document.querySelectorAll('input');
      return Array.from(inputs).map(i => ({
        type: i.type,
        name: i.name,
        id: i.id,
        placeholder: i.placeholder,
        value: i.value,
        displayed: window.getComputedStyle(i).display !== 'none',
        visibility: window.getComputedStyle(i).visibility
      }));
    });
    console.log('JS inputs:', JSON.stringify(jsResult, null, 2));
  }

  // Let's also check the page URL and see if we can modify it to add search terms
  console.log('\nCurrent URL:', page.url());

  // Try navigating with different search params in the URL
  await page.goto('https://jobs.bosch.com/en/?country=nl#software', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  await page.waitForTimeout(3000);
  console.log('API responses so far:', apiResponses.length);
  apiResponses.forEach(r => {
    if (r.url.includes('get_jobs')) {
      const avarsMatch = r.url.match(/avars=([^&]+)/);
      if (avarsMatch) {
        console.log('avars:', decodeURIComponent(avarsMatch[1]));
      }
    }
  });

  await browser.close();
})();
