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

  const apiKey = '2b760fb7-49ef-4e83-b4ba-9c3a8d185e5e';
  const baseUrl = 'https://bosch-i3-caas-api.e-spirit.cloud/bosch-i3-prod/bosch-de.jobs.content/_aggrs/get_jobs';

  // Get ALL global jobs but paginate to find software engineer in NL
  // First get total count
  const countResponse = await page.request.get(
    `${baseUrl}?pagesize=1&avars=${encodeURIComponent(JSON.stringify({ sort: { releasedDate: -1 } }))}&page=1`,
    { headers: { 'Authorization': `Bearer ${apiKey}`, 'Accept': 'application/json', 'Origin': 'https://jobs.bosch.com', 'Referer': 'https://jobs.bosch.com/' } }
  );
  const countText = await countResponse.text();
  const countJson = JSON.parse(countText);
  const total = countJson['_embedded']?.['rh:result']?.[0]?.meta?.[0]?.count || 0;
  console.log('Total global jobs:', total);

  // Fetch all NL jobs with all pages
  // First check if there are more NL jobs by trying higher page sizes
  for (let page_num = 1; page_num <= 5; page_num++) {
    const avars = encodeURIComponent(JSON.stringify({ country: ['nl'], sort: { releasedDate: -1 } }));
    const response = await page.request.get(
      `${baseUrl}?pagesize=100&avars=${avars}&page=${page_num}`,
      { headers: { 'Authorization': `Bearer ${apiKey}`, 'Accept': 'application/json', 'Origin': 'https://jobs.bosch.com', 'Referer': 'https://jobs.bosch.com/' } }
    );
    const text = await response.text();
    const json = JSON.parse(text);
    const resultData = json['_embedded']?.['rh:result']?.[0];
    const count = resultData?.meta?.[0]?.count || 0;
    const jobs = resultData?.data || [];
    console.log(`Page ${page_num}: count=${count}, returned=${jobs.length}`);
    if (jobs.length === 0) break;
    jobs.forEach(j => {
      const n = (j.name || '').toLowerCase();
      if (n.includes('software') || n.includes('.net') || n.includes('java') || n.includes('developer') || n.includes('breda')) {
        console.log(`  SOFTWARE/BREDA: ${j.name} | ${j.location?.city} | ID: ${j._id}`);
      }
    });
    if (jobs.length < 100) break;
  }

  // Try searching English-language jobs
  console.log('\n\nSearching English language NL jobs...');
  const enAvars = encodeURIComponent(JSON.stringify({ country: ['nl'], sort: { releasedDate: -1 }, lang: 'en' }));
  const enResponse = await page.request.get(
    `${baseUrl}?pagesize=100&avars=${enAvars}&page=1`,
    { headers: { 'Authorization': `Bearer ${apiKey}`, 'Accept': 'application/json', 'Origin': 'https://jobs.bosch.com', 'Referer': 'https://jobs.bosch.com/' } }
  );
  const enText = await enResponse.text();
  const enJson = JSON.parse(enText);
  const enResultData = enJson['_embedded']?.['rh:result']?.[0];
  const enCount = enResultData?.meta?.[0]?.count || 0;
  const enJobs = enResultData?.data || [];
  console.log(`English NL: count=${enCount}, returned=${enJobs.length}`);
  enJobs.forEach(j => {
    const n = (j.name || '').toLowerCase();
    if (n.includes('software') || n.includes('.net') || n.includes('java') || n.includes('developer')) {
      console.log(`  MATCH: ${j.name} | ${j.location?.city} | ID: ${j._id}`);
    }
  });

  await browser.close();
})();
