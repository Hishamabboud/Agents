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

  // Capture the full API response with jobs included
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

  // Navigate to trigger all 33 jobs loaded
  await page.goto('https://jobs.bosch.com/en/?country=nl', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  await page.waitForTimeout(3000);

  // The API key was found: 2b760fb7-49ef-4e83-b4ba-9c3a8d185e5e
  // Try calling with the API key directly using native fetch (will inherit browser context/CORS)
  const result = await page.evaluate(async () => {
    const apiKey = '2b760fb7-49ef-4e83-b4ba-9c3a8d185e5e';
    const avars = encodeURIComponent(JSON.stringify({ country: ['nl'], sort: { releasedDate: -1 } }));
    const url = `https://bosch-i3-caas-api.e-spirit.cloud/bosch-i3-prod/bosch-de.jobs.content/_aggrs/get_jobs?pagesize=100&avars=${avars}&page=1`;
    const resp = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'x-api-key': apiKey,
      }
    });
    const text = await resp.text();
    return { status: resp.status, body: text.substring(0, 10000) };
  });

  console.log('API with key, status:', result.status);
  if (result.status === 200) {
    try {
      const json = JSON.parse(result.body);
      console.log('Top keys:', Object.keys(json).join(', '));
      const resultData = json['_embedded']?.['rh:result']?.[0];
      if (resultData) {
        console.log('Result data keys:', Object.keys(resultData).join(', '));
        const jobs = resultData.documents || resultData.jobs || resultData.results || [];
        console.log('Jobs count:', jobs.length);
        jobs.forEach(j => {
          console.log(' -', JSON.stringify(j).substring(0, 200));
        });
        if (jobs.length === 0) {
          console.log('Result data:', JSON.stringify(resultData).substring(0, 2000));
        }
      } else {
        console.log('Response:', result.body.substring(0, 2000));
      }
    } catch(e) {
      console.log('Parse error:', e.message, result.body.substring(0, 500));
    }
  } else {
    console.log('Response:', result.body?.substring(0, 200) || '(empty)');
  }

  // Try API key as query param
  const result2 = await page.evaluate(async () => {
    const apiKey = '2b760fb7-49ef-4e83-b4ba-9c3a8d185e5e';
    const avars = encodeURIComponent(JSON.stringify({ country: ['nl'], sort: { releasedDate: -1 } }));
    const url = `https://bosch-i3-caas-api.e-spirit.cloud/bosch-i3-prod/bosch-de.jobs.content/_aggrs/get_jobs?pagesize=100&avars=${avars}&page=1&apikey=${apiKey}`;
    const resp = await fetch(url);
    const text = await resp.text();
    return { status: resp.status, body: text.substring(0, 10000) };
  });
  console.log('\nAPI key as param, status:', result2.status);
  if (result2.status === 200) {
    try {
      const json = JSON.parse(result2.body);
      const resultData = json['_embedded']?.['rh:result']?.[0];
      const meta = resultData?.meta || [];
      console.log('Meta:', JSON.stringify(meta));
      // Look for job documents
      const docs = resultData?.documents;
      if (docs) {
        console.log('Documents:', JSON.stringify(docs).substring(0, 2000));
      } else {
        console.log('All keys:', Object.keys(resultData || {}).join(', '));
        console.log('Preview:', result2.body.substring(0, 1000));
      }
    } catch(e) {
      console.log('Parse error:', e.message);
      console.log('Body:', result2.body.substring(0, 500));
    }
  }

  await browser.close();
})();
