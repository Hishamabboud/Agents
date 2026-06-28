const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--ignore-certificate-errors', '--no-sandbox']
  });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  // Try SmartRecruiters API for Bosch - multiple query variants
  const queries = [
    'https://api.smartrecruiters.com/v1/companies/Bosch/postings?limit=100&offset=0&country=nl&q=software+engineer',
    'https://api.smartrecruiters.com/v1/companies/Bosch/postings?limit=100&offset=0&q=software+engineer',
    'https://api.smartrecruiters.com/v1/companies/Bosch/postings?limit=50&offset=0',
  ];

  for (const url of queries) {
    try {
      console.log(`\nQuerying: ${url}`);
      const response = await page.request.get(url, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      const text = await response.text();
      console.log('Status:', response.status());
      console.log('Response (first 2000 chars):', text.substring(0, 2000));

      if (response.status() === 200) {
        try {
          const json = JSON.parse(text);
          console.log('Total jobs:', json.totalFound || json.total || 'N/A');
          if (json.content && json.content.length > 0) {
            json.content.forEach(job => {
              const city = job.location?.city || '';
              const country = job.location?.country || '';
              console.log(`  - ${job.name} | ${city}, ${country} | ID: ${job.id} | Apply: ${job.applyUrl || ''}`);
            });
          }
        } catch(pe) {
          console.log('Parse error:', pe.message);
        }
        break;
      }
    } catch(e) {
      console.error('Error:', e.message.substring(0, 200));
    }
  }

  await browser.close();
})();
