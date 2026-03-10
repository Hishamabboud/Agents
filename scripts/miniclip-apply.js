const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function takeScreenshot(page, name) {
  const filepath = path.join(SCREENSHOTS_DIR, name);
  await page.screenshot({ path: filepath, fullPage: false });
  console.log('Screenshot saved:', filepath);
  return filepath;
}

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  console.log('Navigating to Miniclip vacancies page...');
  try {
    await page.goto('https://www.miniclip.com/careers/vacancies', {
      waitUntil: 'networkidle',
      timeout: 60000
    });
  } catch (e) {
    console.log('Navigation warning (may be OK):', e.message);
  }

  await takeScreenshot(page, 'miniclip-01-vacancies-page.png');

  const title = await page.title();
  const currentUrl = page.url();
  console.log('Page title:', title);
  console.log('Current URL:', currentUrl);

  // Get all text content to understand page structure
  const bodyText = await page.evaluate(() => document.body.innerText);
  console.log('Body text (first 3000 chars):', bodyText.substring(0, 3000));

  // Find all links on page
  const allLinks = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('a')).map(el => ({
      text: el.textContent.trim().substring(0, 100),
      href: el.href
    }));
  });

  // Filter for relevant job links
  const relevantLinks = allLinks.filter(l =>
    /net|backend|developer|engineer|c#|software|server|api/i.test(l.text + l.href)
  );

  console.log('All links count:', allLinks.length);
  console.log('Relevant links:', JSON.stringify(relevantLinks.slice(0, 30), null, 2));

  // Also look for iframes which might contain job listings
  const iframes = await page.frames();
  console.log('Number of frames:', iframes.length);
  for (const frame of iframes) {
    console.log('Frame URL:', frame.url());
  }

  await browser.close();
})().catch(e => {
  console.error('Fatal error:', e.message);
  console.error(e.stack);
  process.exit(1);
});
