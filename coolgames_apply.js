const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const execPath = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
  
  const browser = await chromium.launch({ 
    headless: true, 
    executablePath: execPath,
    args: [
      '--no-sandbox', 
      '--disable-setuid-sandbox', 
      '--disable-dev-shm-usage',
      '--no-proxy-server',
      '--ignore-certificate-errors'
    ]
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  // Clear any proxy settings
  await context.route('**/*', route => route.continue());

  console.log('Navigating to CoolGames job page...');
  try {
    await page.goto('https://apply.workable.com/coolgames/j/3654334706', { 
      waitUntil: 'domcontentloaded', 
      timeout: 30000 
    });
    await page.waitForTimeout(8000);

    await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-01-job-description.png', fullPage: true });
    console.log('Screenshot taken');

    const jobText = await page.evaluate(() => document.body.innerText);
    fs.writeFileSync('/home/user/Agents/data/coolgames-job-raw.txt', jobText);
    console.log('Text length:', jobText.length);
    console.log('Preview:', jobText.substring(0, 800));
  } catch (e) {
    console.error('Navigation error:', e.message);
  }

  await browser.close();
  console.log('Done.');
})().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
