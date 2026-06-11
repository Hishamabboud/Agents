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

  // Capture ALL API responses
  const jobApiResponses = [];
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('get_jobs')) {
      try {
        const text = await response.text();
        jobApiResponses.push({ url, status: response.status(), body: text });
      } catch(e) {}
    }
  });

  try {
    console.log('Loading Bosch NL jobs page with search...');
    // Try directly searching with a keyword in URL
    await page.goto('https://jobs.bosch.com/en/search/?q=software+engineer&country=nl', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-search-sw.png', fullPage: false });

    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 5000));
    console.log('Body text:', bodyText);

    console.log('\nCaptured get_jobs API responses:', jobApiResponses.length);
    jobApiResponses.forEach(r => {
      console.log(`URL: ${r.url.substring(0, 200)}`);
      // Parse and display jobs
      try {
        const json = JSON.parse(r.body);
        const inner = json.documents || json.result || json.items || json.content;
        if (inner && inner.length) {
          inner.forEach(job => {
            const title = job.title || job.name || job['job.title'] || JSON.stringify(job).substring(0, 60);
            const city = job['location.city'] || job.city || job.location?.city || '';
            const country = job['location.country'] || job.country || job.location?.country || '';
            console.log(`  Job: ${title} | ${city}, ${country}`);
          });
        } else {
          console.log('  Body:', r.body.substring(0, 500));
        }
      } catch(e) {
        console.log('  Raw:', r.body.substring(0, 300));
      }
    });
  } catch(e) {
    console.error('Error:', e.message.substring(0, 300));
  }

  // Try direct URL search
  try {
    console.log('\nTrying another search URL format...');
    await page.goto('https://jobs.bosch.com/en/?country=nl&q=software', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    await page.waitForTimeout(5000);
    const bodyText2 = await page.evaluate(() => document.body.innerText.substring(0, 5000));
    console.log('Body2:', bodyText2);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-search-sw2.png', fullPage: false });
  } catch(e) {
    console.log('Error2:', e.message.substring(0, 200));
  }

  await browser.close();
})();
