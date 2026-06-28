const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--ignore-certificate-errors', '--no-sandbox']
  });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();

  // Search BoschGroup for Software Engineer in NL
  const searchQueries = [
    'https://api.smartrecruiters.com/v1/companies/BoschGroup/postings?limit=100&offset=0&country=nl',
    'https://api.smartrecruiters.com/v1/companies/BoschGroup/postings?limit=100&offset=0&country=nl&q=software',
    'https://api.smartrecruiters.com/v1/companies/BoschGroup/postings?limit=100&offset=0&country=nl&q=developer',
  ];

  for (const url of searchQueries) {
    try {
      console.log(`\nQuerying: ${url}`);
      const response = await page.request.get(url);
      const text = await response.text();
      const json = JSON.parse(text);
      console.log(`Total found: ${json.totalFound}`);
      (json.content || []).forEach(j => {
        const loc = j.location;
        console.log(`  - ${j.name} | ${loc?.city}, ${loc?.countryCode || loc?.country} | ID: ${j.id}`);
      });
    } catch(e) {
      console.log('Error:', e.message.substring(0, 200));
    }
  }

  await browser.close();
})();
