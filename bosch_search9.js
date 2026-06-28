const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--ignore-certificate-errors', '--no-sandbox']
  });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();

  // Use the discovered CaaS API endpoint to search for software engineer jobs
  const baseUrl = 'https://bosch-i3-caas-api.e-spirit.cloud/bosch-i3-prod/bosch-de.jobs.content/_aggrs/get_jobs';

  // Search with different keyword filters
  const searches = [
    // All NL jobs
    { pagesize: 100, avars: { country: ['nl'], sort: { releasedDate: -1 } } },
    // Software engineer NL jobs
    { pagesize: 50, avars: { country: ['nl'], sort: { releasedDate: -1 }, searchPhrase: 'software engineer' } },
    // .NET NL jobs
    { pagesize: 50, avars: { country: ['nl'], sort: { releasedDate: -1 }, searchPhrase: '.NET' } },
    // Java NL jobs
    { pagesize: 50, avars: { country: ['nl'], sort: { releasedDate: -1 }, searchPhrase: 'java developer' } },
    // Breda jobs
    { pagesize: 50, avars: { country: ['nl'], city: ['Breda'], sort: { releasedDate: -1 } } },
  ];

  for (const search of searches) {
    const avarsEncoded = encodeURIComponent(JSON.stringify(search.avars));
    const url = `${baseUrl}?pagesize=${search.pagesize}&avars=${avarsEncoded}&page=1`;
    try {
      console.log(`\nQuery: avars=${JSON.stringify(search.avars).substring(0, 80)}`);
      const response = await page.request.get(url, {
        headers: {
          'Accept': 'application/json',
          'Origin': 'https://jobs.bosch.com',
          'Referer': 'https://jobs.bosch.com/'
        }
      });
      console.log('Status:', response.status());
      const text = await response.text();
      if (response.status() === 200) {
        const json = JSON.parse(text);
        const jobs = json.result || json.jobs || json.items || (Array.isArray(json) ? json : []);
        console.log('Result keys:', Object.keys(json).join(', '));
        console.log('Response preview:', text.substring(0, 500));
      } else {
        console.log('Response:', text.substring(0, 200));
      }
    } catch(e) {
      console.log('Error:', e.message.substring(0, 200));
    }
  }

  await browser.close();
})();
