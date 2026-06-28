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

  // Try to directly search the Bosch jobs portal with Breda filter
  const apiKey = '2b760fb7-49ef-4e83-b4ba-9c3a8d185e5e';

  // Try searching all jobs globally (no country filter) and filter by Breda or software
  const avars = JSON.stringify({ sort: { releasedDate: -1 }, city: 'Breda' });
  const url = `https://bosch-i3-caas-api.e-spirit.cloud/bosch-i3-prod/bosch-de.jobs.content/_aggrs/get_jobs?pagesize=50&avars=${encodeURIComponent(avars)}&page=1`;

  // Try with API key as query param (another variation)
  const variations = [
    `https://bosch-i3-caas-api.e-spirit.cloud/bosch-i3-prod/bosch-de.jobs.content/_aggrs/get_jobs?pagesize=100&avars=${encodeURIComponent(JSON.stringify({ sort: { releasedDate: -1 } }))}&page=1&apikey=${apiKey}`,
  ];

  for (const u of variations) {
    const response = await page.request.get(u, {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Accept': 'application/json',
        'Origin': 'https://jobs.bosch.com',
        'Referer': 'https://jobs.bosch.com/'
      }
    });
    console.log('URL:', u.substring(0, 100));
    console.log('Status:', response.status());
    const text = await response.text();
    if (response.status() === 200) {
      const json = JSON.parse(text);
      const resultData = json['_embedded']?.['rh:result']?.[0];
      const count = resultData?.meta?.[0]?.count || 0;
      const jobs = resultData?.data || [];
      console.log(`Total: ${count}, Returned: ${jobs.length}`);
      // Filter for software-related jobs
      const swJobs = jobs.filter(j => {
        const n = (j.name || '').toLowerCase();
        return n.includes('software') || n.includes('developer') || n.includes('.net') || n.includes('java') || n.includes('programm');
      });
      console.log('Software-related:', swJobs.length);
      swJobs.forEach(j => console.log(`  - ${j.name} | ${j.location?.city}, ${j.location?.country}`));
      // Also show Breda
      const bredaJobs = jobs.filter(j => j.location?.city?.toLowerCase().includes('breda'));
      console.log('\nBreda jobs:', bredaJobs.length);
      bredaJobs.forEach(j => console.log(`  - ${j.name} | ID: ${j._id}`));
    }
  }

  // Try the SmartRecruiters API for the job
  console.log('\n\nChecking SmartRecruiters for Breda software jobs...');
  const srUrl = 'https://api.smartrecruiters.com/v1/companies/BoschGroup/postings?limit=100&offset=0&location=Breda';
  const srResponse = await page.request.get(srUrl);
  console.log('SR status:', srResponse.status());
  const srText = await srResponse.text();
  if (srResponse.status() === 200) {
    const srJson = JSON.parse(srText);
    console.log('Total found:', srJson.totalFound);
    (srJson.content || []).forEach(j => {
      console.log(`  - ${j.name} | ${j.location?.city}, ${j.location?.countryCode}`);
    });
  }

  await browser.close();
})();
