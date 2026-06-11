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
    if (url.includes('get_jobs')) {
      try {
        const text = await response.text();
        apiResponses.push({ url, status: response.status(), body: text });
      } catch(e) {}
    }
  });

  await page.goto('https://jobs.bosch.com/en/?country=nl', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  await page.waitForTimeout(3000);

  // Use the keyword search input (name="searchTerm", visible at top:410)
  const searchInput = await page.$('input[name="searchTerm"]');
  if (searchInput) {
    console.log('Found searchTerm input');
    await searchInput.fill('software engineer');
    await page.waitForTimeout(500);
    // Press Enter to search
    await searchInput.press('Enter');
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-search-software.png', fullPage: false });
    const text = await page.evaluate(() => document.body.innerText.substring(0, 5000));
    console.log('After keyword search:', text);
  } else {
    console.log('searchTerm input not found');
  }

  // Print captured API responses
  console.log('\n\nAPI responses captured:', apiResponses.length);
  apiResponses.forEach(r => {
    const avarsMatch = r.url.match(/avars=([^&]+)/);
    const avars = avarsMatch ? JSON.parse(decodeURIComponent(avarsMatch[1])) : {};
    console.log('\navars:', JSON.stringify(avars));
    if (r.status === 200) {
      const json = JSON.parse(r.body);
      const resultData = json['_embedded']?.['rh:result']?.[0];
      const count = resultData?.meta?.[0]?.count || 0;
      const jobs = resultData?.data || [];
      console.log(`Count: ${count}, Jobs: ${jobs.length}`);
      jobs.forEach(j => {
        console.log(`  - ${j.name} | ${j.location?.city}, ${j.location?.country}`);
      });
    }
  });

  await browser.close();
})();
