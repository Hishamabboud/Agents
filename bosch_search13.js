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

  // Capture the get_jobs API calls and their responses
  const apiData = [];
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('get_jobs')) {
      try {
        const text = await response.text();
        apiData.push({ url, body: text });
      } catch(e) {}
    }
  });

  try {
    // Load the page with no country filter to get all jobs (broader)
    await page.goto('https://jobs.bosch.com/en/?country=nl', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    await page.waitForTimeout(5000);

    // Extract the API URL being called
    const scriptContent = await page.evaluate(() => {
      // Look for CaaS configuration in scripts
      const scripts = Array.from(document.scripts).map(s => s.src || s.textContent?.substring(0, 200) || '');
      return scripts.filter(s => s.includes('caas') || s.includes('jobs.content')).join('\n---\n');
    });
    console.log('CaaS scripts:', scriptContent.substring(0, 500));

    // Captured API data
    console.log('\nCaptured API calls:', apiData.length);
    apiData.forEach(d => {
      console.log('\nURL:', d.url.substring(0, 200));
      try {
        const json = JSON.parse(d.body);
        const docs = json.documents || json.hits?.hits || json.hits?.documents || [];
        console.log('Doc count:', docs.length);
        docs.forEach(doc => {
          const title = doc.displayedJobTitle || doc['job.displayedJobTitle'] || doc.title || doc.name || Object.entries(doc).slice(0, 3).map(([k,v]) => `${k}=${v}`).join(', ');
          const city = doc['location.city'] || doc.city || doc.location?.city || '';
          const smartId = doc.smartJobId || doc['job.smartJobId'] || doc.id || '';
          console.log(`  - ${title} | ${city} | ID: ${smartId}`);
        });
        if (docs.length === 0) {
          console.log('Body:', d.body.substring(0, 500));
        }
      } catch(e) {
        console.log('Body:', d.body.substring(0, 300));
      }
    });

    // Try using fetch from the browser to call the API with proper cookies
    const fetchResult = await page.evaluate(async () => {
      // Get the CaaS API endpoint - decode from the page URL
      const avars = JSON.stringify({ country: ['nl'], sort: { releasedDate: -1 } });
      const url = `https://bosch-i3-caas-api.e-spirit.cloud/bosch-i3-prod/bosch-de.jobs.content/_aggrs/get_jobs?pagesize=100&avars=${encodeURIComponent(avars)}&page=1`;
      try {
        const resp = await fetch(url, { credentials: 'include' });
        const text = await resp.text();
        return { status: resp.status, body: text.substring(0, 5000) };
      } catch(e) {
        return { error: e.message };
      }
    });
    console.log('\nBrowser fetch result:');
    console.log('Status:', fetchResult.status);
    if (fetchResult.body) {
      try {
        const json = JSON.parse(fetchResult.body);
        const docs = json.documents || json.hits?.documents || [];
        console.log('Total docs:', docs.length);
        docs.forEach(doc => {
          const title = doc.displayedJobTitle || doc['job.displayedJobTitle'] || doc.title || Object.keys(doc).slice(0, 3).join(', ');
          const city = doc['location.city'] || doc.city || '';
          console.log(`  - ${title} | ${city}`);
        });
        if (docs.length === 0) {
          console.log('Body keys:', Object.keys(json).join(', '));
          console.log('Body:', fetchResult.body.substring(0, 1000));
        }
      } catch(e) {
        console.log('Body:', fetchResult.body.substring(0, 500));
      }
    }
    if (fetchResult.error) console.log('Error:', fetchResult.error);

  } catch(e) {
    console.error('Error:', e.message.substring(0, 300));
  }

  await browser.close();
})();
