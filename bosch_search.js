const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  try {
    console.log('Navigating to Bosch jobs search...');
    await page.goto('https://jobs.bosch.com/en/?country=nl', { waitUntil: 'networkidle', timeout: 30000 });
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-01-search-page.png', fullPage: false });
    console.log('Page title:', await page.title());

    // Try to search for software engineer
    const searchInput = await page.$('input[type="search"], input[placeholder*="search"], input[name*="search"], input[id*="search"], [data-testid*="search"] input');
    if (searchInput) {
      await searchInput.fill('software engineer');
      await searchInput.press('Enter');
      await page.waitForTimeout(3000);
      await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-02-search-results.png', fullPage: false });
      console.log('Search executed');
    } else {
      console.log('No search input found, trying URL-based search');
      await page.goto('https://jobs.bosch.com/en/search/?q=software+engineer&country=NL', { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(3000);
      await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-02-search-results.png', fullPage: false });
    }

    // Get all job listings
    const content = await page.content();
    // Look for job links
    const jobLinks = await page.$$eval('a', links =>
      links
        .filter(a => a.href && (a.href.includes('/en/job') || a.href.includes('jobs.bosch') || a.textContent.toLowerCase().includes('engineer') || a.textContent.toLowerCase().includes('developer')))
        .map(a => ({ text: a.textContent.trim().substring(0, 100), href: a.href }))
        .slice(0, 30)
    );
    console.log('Found links:', JSON.stringify(jobLinks, null, 2));

    // Get page text
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 3000));
    console.log('Page text:', bodyText);

  } catch(e) {
    console.error('Error:', e.message);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/bosch-error.png', fullPage: false });
  }

  await browser.close();
})();
