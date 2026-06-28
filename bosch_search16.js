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

  // Get the full response to understand structure
  const avars = encodeURIComponent(JSON.stringify({ country: ['nl'], sort: { releasedDate: -1 } }));
  const url = `${baseUrl}?pagesize=100&avars=${avars}&page=1`;
  const response = await page.request.get(url, {
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Accept': 'application/json',
      'Origin': 'https://jobs.bosch.com',
      'Referer': 'https://jobs.bosch.com/'
    }
  });

  const text = await response.text();
  console.log('Status:', response.status());
  console.log('Full response length:', text.length);

  // Save full response
  fs.writeFileSync('/home/user/Agents/output/bosch-nl-jobs.json', text);

  // Parse and show all jobs
  const json = JSON.parse(text);
  const resultData = json['_embedded']?.['rh:result']?.[0];
  console.log('Result data keys:', Object.keys(resultData || {}).join(', '));
  const meta = resultData?.meta || [];
  console.log('Meta:', JSON.stringify(meta));

  // Print the full resultData to understand job structure
  console.log('\nFull resultData:', JSON.stringify(resultData).substring(0, 3000));

  await browser.close();
})();
