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

  // The API key found: 2b760fb7-49ef-4e83-b4ba-9c3a8d185e5e
  const apiKey = '2b760fb7-49ef-4e83-b4ba-9c3a8d185e5e';
  const baseUrl = 'https://bosch-i3-caas-api.e-spirit.cloud/bosch-i3-prod/bosch-de.jobs.content/_aggrs/get_jobs';

  // Try with API key in header - make the request from node level not browser
  try {
    const avars = encodeURIComponent(JSON.stringify({ country: ['nl'], sort: { releasedDate: -1 } }));
    const url = `${baseUrl}?pagesize=100&avars=${avars}&page=1`;
    const response = await page.request.get(url, {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'X-Api-Key': apiKey,
        'Accept': 'application/json',
        'Origin': 'https://jobs.bosch.com',
        'Referer': 'https://jobs.bosch.com/'
      }
    });
    console.log('Status with Bearer:', response.status());
    const text = await response.text();
    console.log('Response:', text.substring(0, 500));
  } catch(e) {
    console.log('Error:', e.message.substring(0, 200));
  }

  // Try with cookies - load the page first to get session cookies
  await page.goto('https://jobs.bosch.com/en/?country=nl', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  await page.waitForTimeout(3000);

  const cookies = await context.cookies();
  const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join('; ');
  console.log('\nCookies:', cookieStr.substring(0, 200));

  try {
    const avars = encodeURIComponent(JSON.stringify({ country: ['nl'], sort: { releasedDate: -1 } }));
    const url = `${baseUrl}?pagesize=100&avars=${avars}&page=1`;
    const response = await page.request.get(url, {
      headers: {
        'Cookie': cookieStr,
        'Accept': 'application/json',
        'Origin': 'https://jobs.bosch.com',
        'Referer': 'https://jobs.bosch.com/'
      }
    });
    console.log('\nStatus with cookies:', response.status());
    const text = await response.text();
    console.log('Response:', text.substring(0, 1000));

    if (response.status() === 200) {
      const json = JSON.parse(text);
      const resultData = json['_embedded']?.['rh:result']?.[0];
      console.log('\nResult keys:', Object.keys(resultData || {}).join(', '));
      const docs = resultData?.documents || [];
      console.log('Docs count:', docs.length);
      docs.forEach(d => {
        console.log(' -', d.displayedJobTitle || d.title || JSON.stringify(d).substring(0, 100));
      });
    }
  } catch(e) {
    console.log('Error:', e.message.substring(0, 200));
  }

  await browser.close();
})();
