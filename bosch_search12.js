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
    if (url.includes('get_jobs') || url.includes('caas-api')) {
      try {
        const text = await response.text();
        jobApiResponses.push({ url, status: response.status(), body: text });
      } catch(e) {}
    }
  });

  try {
    console.log('Loading Bosch NL jobs page...');
    await page.goto('https://jobs.bosch.com/en/?country=nl', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    await page.waitForTimeout(5000);

    // Find and click "See all jobs" button
    const seeAllBtn = await page.$('text=See all jobs');
    if (seeAllBtn) {
      console.log('Clicking See all jobs...');
      await seeAllBtn.click();
      await page.waitForTimeout(5000);
    }

    // Get all text on current page
    const bodyText = await page.evaluate(() => document.body.innerText);
    console.log('=== All NL jobs on page ===');
    console.log(bodyText.substring(0, 10000));

    // Try clicking search
    console.log('\n\n=== Looking for search inputs ===');
    const inputs = await page.$$eval('input', inputs =>
      inputs.map(i => ({ type: i.type, name: i.name, placeholder: i.placeholder, id: i.id, visible: i.offsetParent !== null }))
    );
    console.log('Inputs:', JSON.stringify(inputs, null, 2));

    // Log API responses
    console.log('\n\n=== Captured API responses ===', jobApiResponses.length);
    jobApiResponses.forEach(r => {
      try {
        const json = JSON.parse(r.body);
        const docs = json.documents || json.hits?.documents || [];
        console.log(`URL: ${r.url.substring(0, 150)}`);
        console.log(`Jobs count: ${docs.length}`);
        docs.forEach(doc => {
          const title = doc.displayedJobTitle || doc['job.displayedJobTitle'] || doc.title || 'Unknown';
          const city = doc['location.city'] || doc.city || '';
          const country = doc['location.country'] || doc.country || '';
          console.log(`  - ${title} | ${city}, ${country}`);
        });
      } catch(e) {
        console.log('Parse error:', r.body.substring(0, 200));
      }
    });

  } catch(e) {
    console.error('Error:', e.message.substring(0, 300));
  }

  await browser.close();
})();
