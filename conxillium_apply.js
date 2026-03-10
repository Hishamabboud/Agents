const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  console.log('Navigating to Conxillium job posting...');
  await page.goto('https://werkenbijconxillium.nl/l/en/o/fullstack-mobile-software-engineer-net-maui', {
    waitUntil: 'networkidle',
    timeout: 30000
  });

  // Screenshot the job posting
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/conxillium-job-posting.png', fullPage: true });
  console.log('Screenshot saved: conxillium-job-posting.png');

  // Look for the apply button
  const applyBtn = await page.$('a[href*="apply"], button:has-text("Apply"), a:has-text("Apply"), button:has-text("Solliciteren"), a:has-text("Solliciteren"), a[href*="application"]');
  if (applyBtn) {
    const href = await applyBtn.getAttribute('href');
    const text = await applyBtn.textContent();
    console.log('Found apply button:', text, href);
    await applyBtn.click();
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  } else {
    console.log('No apply button found directly, checking all links...');
    const links = await page.$$eval('a', els => els.map(e => ({ text: e.textContent.trim(), href: e.getAttribute('href') })));
    console.log('All links:', JSON.stringify(links.slice(0, 30)));
  }

  const currentUrl = page.url();
  console.log('Current URL after click:', currentUrl);

  await page.screenshot({ path: '/home/user/Agents/output/screenshots/conxillium-after-apply-click.png', fullPage: true });
  console.log('Screenshot saved: conxillium-after-apply-click.png');

  // Print page content for form analysis
  const pageTitle = await page.title();
  const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 3000));
  console.log('Page title:', pageTitle);
  console.log('Body text preview:', bodyText);

  // Check for form fields
  const inputs = await page.$$eval('input, textarea, select', els => els.map(e => ({
    type: e.type,
    name: e.name,
    id: e.id,
    placeholder: e.placeholder,
    label: e.getAttribute('aria-label') || ''
  })));
  console.log('Form inputs found:', JSON.stringify(inputs));

  await browser.close();
})();
