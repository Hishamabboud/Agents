const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--ignore-certificate-errors', '--ignore-certificate-errors-spki-list', '--no-sandbox']
  });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  // Try different Bosch job portals
  const urls = [
    'https://www.bosch.nl/en/careers/job-offers/',
    'https://www.bosch.com/careers/',
    'https://careers.bosch.com/',
  ];

  for (const url of urls) {
    try {
      console.log(`Trying: ${url}`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
      const title = await page.title();
      console.log('Title:', title);
      await page.screenshot({ path: `/home/user/Agents/output/screenshots/bosch-try-${url.replace(/[^a-z0-9]/gi, '_').substring(0, 30)}.png` });
      const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 1000));
      console.log('Body:', bodyText.substring(0, 500));
      console.log('---');
    } catch(e) {
      console.log(`Error for ${url}:`, e.message.substring(0, 100));
    }
  }

  await browser.close();
})();
