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

  const apiKey = '2b760fb7-49ef-4e83-b4ba-9c3a8d185e5e';
  const baseUrl = 'https://bosch-i3-caas-api.e-spirit.cloud/bosch-i3-prod/bosch-de.jobs.content/_aggrs/get_jobs';

  // Search globally (no country filter) for software engineer
  const searches = [
    { label: 'software engineer global', avars: { sort: { releasedDate: -1 }, searchPhrase: 'software engineer' } },
    { label: '.NET global', avars: { sort: { releasedDate: -1 }, searchPhrase: '.NET' } },
    { label: 'medior software', avars: { sort: { releasedDate: -1 }, searchPhrase: 'medior software' } },
    { label: 'activeschematics', avars: { sort: { releasedDate: -1 }, searchPhrase: 'ActiveSchematics' } },
    { label: 'Java NL', avars: { country: ['nl'], sort: { releasedDate: -1 }, searchPhrase: 'Java' } },
    { label: 'Breda all', avars: { city: ['Breda'], sort: { releasedDate: -1 } } },
  ];

  for (const s of searches) {
    const avars = encodeURIComponent(JSON.stringify(s.avars));
    const url = `${baseUrl}?pagesize=50&avars=${avars}&page=1`;
    try {
      const response = await page.request.get(url, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Accept': 'application/json',
          'Origin': 'https://jobs.bosch.com',
          'Referer': 'https://jobs.bosch.com/'
        }
      });
      const text = await response.text();
      if (response.status() === 200) {
        const json = JSON.parse(text);
        const resultData = json['_embedded']?.['rh:result']?.[0];
        const count = resultData?.meta?.[0]?.count || 0;
        const jobs = resultData?.data || [];
        console.log(`\n[${s.label}] Total: ${count}, Returned: ${jobs.length}`);
        jobs.forEach(j => {
          console.log(`  - ${j.name} | ${j.location?.city}, ${j.location?.country}`);
        });
      } else {
        console.log(`[${s.label}] HTTP ${response.status()}`);
      }
    } catch(e) {
      console.log(`[${s.label}] Error: ${e.message.substring(0, 100)}`);
    }
  }

  await browser.close();
})();
