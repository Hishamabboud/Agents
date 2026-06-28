const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const execPath = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
  
  console.log('Launching browser...');
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: execPath,
    args: [
      '--no-sandbox', 
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--no-first-run',
      '--no-zygote',
      '--single-process',
      '--ignore-certificate-errors',
      '--disable-web-security',
      '--allow-running-insecure-content',
    ],
    ignoreDefaultArgs: ['--disable-extensions']
  });
  
  console.log('Browser launched!');
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();
  
  // Log network errors
  page.on('pageerror', err => console.log('Page error:', err.message));
  page.on('requestfailed', req => console.log('Request failed:', req.url(), req.failure().errorText));

  console.log('Testing connection to a simple URL first...');
  try {
    await page.goto('https://example.com', { waitUntil: 'load', timeout: 15000 });
    const title = await page.title();
    console.log('example.com title:', title);
  } catch(e) {
    console.error('example.com failed:', e.message);
  }

  console.log('Now trying workable...');
  try {
    await page.goto('https://apply.workable.com/coolgames/j/3654334706/apply/', { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });
    console.log('Workable loaded!');
    await page.waitForTimeout(5000);
    const content = await page.evaluate(() => document.body.innerText);
    console.log('Content length:', content.length);
    console.log('Content:', content.substring(0, 300));
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-01-apply-form.png', fullPage: true });
  } catch(e) {
    console.error('Workable failed:', e.message);
    // Check what DNS resolves to
    const result = await page.evaluate(async () => {
      try {
        const r = await fetch('https://httpbin.org/ip');
        return await r.json();
      } catch(e) {
        return {error: e.message};
      }
    }).catch(e => ({error: e.message}));
    console.log('Network check:', result);
  }

  await browser.close();
  console.log('Done!');
})().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
