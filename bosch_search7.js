const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--ignore-certificate-errors', '--no-sandbox']
  });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();

  // Try more Bosch company IDs
  const companies = [
    'BoschGlobalSoftwareTechnologies',
    'BoschDigital',
    'BoschAutoComfort',
    'BoschEngineering',
    'BoschRexroth',
    'BoschSecurity',
    'BoschSoftwareTechnologies',
    'BGST',
    'BoschNederland',
    'RobertBoschNL',
  ];

  for (const id of companies) {
    try {
      const response = await page.request.get(
        `https://api.smartrecruiters.com/v1/companies/${id}/postings?limit=5`
      );
      const text = await response.text();
      if (response.status() === 200) {
        const json = JSON.parse(text);
        console.log(`${id}: ${json.totalFound} jobs`);
        if (json.totalFound > 0) {
          (json.content || []).slice(0, 3).forEach(j => {
            console.log(`  - ${j.name} | ${j.location?.city}, ${j.location?.countryCode}`);
          });
        }
      } else {
        console.log(`${id}: HTTP ${response.status()}`);
      }
    } catch(e) {
      console.log(`${id}: Error - ${e.message.substring(0, 80)}`);
    }
  }

  // Also check the Bosch job search page via Playwright to see what portal they link to
  try {
    console.log('\nChecking www.bosch.nl job page...');
    await page.goto('https://www.bosch.nl/en/careers/job-offers/', {
      waitUntil: 'domcontentloaded',
      timeout: 15000
    });
    // Look for iframe or links to job search
    const iframes = await page.$$eval('iframe', iframes => iframes.map(i => i.src));
    console.log('Iframes:', iframes);
    const links = await page.$$eval('a[href*="jobs"], a[href*="career"], a[href*="vacature"]', links =>
      links.slice(0, 20).map(a => ({ text: a.textContent.trim().substring(0, 80), href: a.href }))
    );
    console.log('Career links:', JSON.stringify(links, null, 2));
  } catch(e) {
    console.log('Page check error:', e.message.substring(0, 200));
  }

  await browser.close();
})();
