const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--ignore-certificate-errors', '--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  // Try SmartRecruiters API for Bosch
  try {
    console.log('Trying SmartRecruiters API for Bosch...');
    const response = await page.request.get(
      'https://api.smartrecruiters.com/v1/companies/Bosch/postings?limit=100&offset=0&country=nl&q=software+engineer',
      { headers: { 'Content-Type': 'application/json' } }
    );
    const json = await response.json();
    console.log('SmartRecruiters response status:', response.status());
    if (json.content) {
      json.content.slice(0, 20).forEach(job => {
        console.log(`Job: ${job.name} | Location: ${job.location?.city}, ${job.location?.country} | URL: ${job.applyUrl || job.ref}`);
      });
    } else {
      console.log('Response:', JSON.stringify(json).substring(0, 500));
    }
  } catch(e) {
    console.error('SmartRecruiters error:', e.message);
  }

  // Also try the main Bosch job API
  try {
    console.log('\nTrying Bosch job API...');
    const response = await page.request.get(
      'https://bosch-i3-caas-api.e-spirit.cloud/api/v1/jobs?lang=en&country=NL&q=software+engineer&size=20',
      { headers: { 'Accept': 'application/json' } }
    );
    console.log('Bosch API response status:', response.status());
    const text = await response.text();
    console.log('Response:', text.substring(0, 1000));
  } catch(e) {
    console.error('Bosch API error:', e.message);
  }

  await browser.close();
})();
