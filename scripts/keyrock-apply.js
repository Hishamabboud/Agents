const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';

async function takeScreenshot(page, name) {
  const filepath = path.join(SCREENSHOTS_DIR, name);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log('Screenshot saved:', name);
  return filepath;
}

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();
  await page.setViewportSize({ width: 1280, height: 900 });

  try {
    console.log('Navigating to Keyrock job page...');
    await page.goto('https://jobs.ashbyhq.com/keyrock/13432bba-3821-4ca9-a994-9a13ba307fd2', { waitUntil: 'networkidle', timeout: 30000 });

    await takeScreenshot(page, 'keyrock-01-job-page.png');

    const title = await page.title();
    console.log('Page title:', title);

    // Get all text on the page
    const bodyText = await page.evaluate(() => document.body.innerText);
    console.log('Page text (first 2000 chars):', bodyText.substring(0, 2000));

    // Find all buttons
    const buttons = await page.evaluate(() => {
      const els = Array.from(document.querySelectorAll('button, a, [role="button"]'));
      return els.map(el => ({
        text: el.textContent ? el.textContent.trim().substring(0, 80) : '',
        tag: el.tagName,
        href: el.href || el.getAttribute('href') || '',
        id: el.id || '',
        className: (el.className || '').substring(0, 50)
      })).filter(el => el.text.length > 0);
    });
    console.log('Interactive elements:', JSON.stringify(buttons.slice(0, 30), null, 2));

  } catch (e) {
    console.error('Error:', e.message);
    await takeScreenshot(page, 'keyrock-error.png');
  }

  await browser.close();
})();
