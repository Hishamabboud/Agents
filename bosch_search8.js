const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--ignore-certificate-errors',
      '--ignore-certificate-errors-spki-list',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--allow-insecure-localhost',
    ]
  });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  // Intercept network requests to find the API
  const apiCalls = [];
  page.on('response', response => {
    const url = response.url();
    if (url.includes('api') || url.includes('job') || url.includes('caas') || url.includes('search')) {
      apiCalls.push({ url, status: response.status() });
    }
  });

  try {
    console.log('Navigating to jobs.bosch.com with SSL bypass...');
    await page.goto('https://jobs.bosch.com/en/?country=nl', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    console.log('Page title:', await page.title());
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-jobs-page.png', fullPage: false });
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 2000));
    console.log('Body text:', bodyText);
    console.log('\nAPI calls intercepted:', JSON.stringify(apiCalls, null, 2));
  } catch(e) {
    console.error('Error:', e.message.substring(0, 300));
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-ssl-error.png' }).catch(() => {});
  }

  // Try the API endpoint directly
  try {
    const caasEndpoints = [
      'https://bosch-i3-caas-api.e-spirit.cloud/api/v1/jobs?lang=en&country=NL&q=software+engineer',
      'https://bosch-i3-caas-api.e-spirit.cloud/api/v1/jobs?lang=en&query=software+engineer&country=nl',
    ];
    for (const url of caasEndpoints) {
      console.log(`\nTrying CaaS API: ${url}`);
      const response = await page.request.get(url, { ignoreHTTPSErrors: true });
      console.log('Status:', response.status());
      const text = await response.text();
      console.log('Response:', text.substring(0, 500));
    }
  } catch(e) {
    console.log('CaaS error:', e.message.substring(0, 200));
  }

  await browser.close();
})();
