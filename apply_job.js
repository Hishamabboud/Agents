const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const screenshotDir = '/home/user/Agents/output/screenshots';
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--proxy-bypass-list=*'
    ],
    proxy: { server: 'direct://' }
  });

  const context = await browser.newContext({
    locale: 'nl-NL',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  console.log('Navigating to interactivated.nl...');
  try {
    await page.goto('https://www.interactivated.nl', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    const finalUrl = page.url();
    const title = await page.title();
    console.log('Final URL:', finalUrl);
    console.log('Title:', title);
    
    await page.screenshot({ path: path.join(screenshotDir, '01-interactivated-home.png'), fullPage: true });
    console.log('Screenshot 01 saved');

    // Look for links related to jobs or vacancies
    const links = await page.$$eval('a', links => links.map(a => ({ text: a.textContent.trim(), href: a.href })));
    console.log('All links:', JSON.stringify(links.filter(l => l.href && l.href.length > 0), null, 2));

  } catch(e) {
    console.log('Error:', e.message);
    await page.screenshot({ path: path.join(screenshotDir, '01-error.png'), fullPage: true });
  }

  await browser.close();
})().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
