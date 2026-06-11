const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--ignore-certificate-errors', '--no-sandbox']
  });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();

  // Try different company slugs for Bosch
  const companyIds = ['Bosch', 'BoschNL', 'BoschNetherlands', 'RobertBosch', 'BoschGroup'];

  for (const id of companyIds) {
    try {
      const url = `https://api.smartrecruiters.com/v1/companies/${id}/postings?limit=5`;
      const response = await page.request.get(url);
      const text = await response.text();
      if (response.status() === 200 && text.includes('"content"')) {
        const json = JSON.parse(text);
        if (json.totalFound > 0) {
          console.log(`Found ${json.totalFound} jobs at company ID: ${id}`);
          json.content.slice(0, 5).forEach(j => {
            const loc = j.location;
            console.log(`  - ${j.name} | ${loc?.city}, ${loc?.country} | ${j.id}`);
          });
        } else {
          console.log(`Company ${id}: 0 jobs`);
        }
      } else {
        console.log(`Company ${id}: status ${response.status()}`);
      }
    } catch(e) {
      console.log(`Company ${id} error: ${e.message.substring(0,100)}`);
    }
  }

  // Try searching Bosch on SmartRecruiters using the search API
  try {
    console.log('\nSearching SmartRecruiters for Bosch NL jobs...');
    const response = await page.request.get(
      'https://api.smartrecruiters.com/v1/postings?q=software+engineer+bosch&country=nl&limit=20'
    );
    const text = await response.text();
    console.log('Status:', response.status(), 'Length:', text.length);
    if (response.status() === 200) {
      const json = JSON.parse(text);
      console.log('Total:', json.totalFound);
      (json.content || []).slice(0, 10).forEach(j => {
        console.log(`  - ${j.name} | ${j.company?.name} | ${j.location?.city}, ${j.location?.country}`);
      });
    }
  } catch(e) {
    console.log('Global search error:', e.message.substring(0, 200));
  }

  await browser.close();
})();
