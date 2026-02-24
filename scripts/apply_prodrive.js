const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const screenshotsDir = '/home/user/Agents/output/screenshots/';
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 900 });

  console.log('Navigating to Prodrive Technologies careers page...');
  await page.goto('https://prodrive-technologies.com/careers/apply/', {
    waitUntil: 'networkidle',
    timeout: 30000
  });

  const title = await page.title();
  console.log('Page title:', title);

  // Get all form elements for inspection
  const inputs = await page.evaluate(() => {
    const els = document.querySelectorAll('input, select, textarea, button');
    return Array.from(els).map(el => ({
      tag: el.tagName,
      type: el.type || '',
      name: el.name || '',
      id: el.id || '',
      placeholder: el.placeholder || '',
      required: el.required,
      value: el.value || '',
      options: el.tagName === 'SELECT' ? Array.from(el.options).map(o => ({ value: o.value, text: o.text })) : []
    }));
  });

  console.log('Form elements found:', JSON.stringify(inputs, null, 2));

  // Take initial screenshot
  await page.screenshot({ path: screenshotsDir + 'prodrive_initial.png', fullPage: true });
  console.log('Initial screenshot saved');

  await browser.close();
})().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
