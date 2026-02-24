const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const proxyEnv = process.env.https_proxy || process.env.HTTPS_PROXY || '';
let proxyServer = '', proxyUsername = '', proxyPassword = '';
if (proxyEnv) {
  const match = proxyEnv.match(/^http:\/\/([^:]+):([^@]+)@(.+)$/);
  if (match) {
    proxyUsername = match[1];
    proxyPassword = match[2];
    proxyServer = 'http://' + match[3];
  }
}

(async () => {
  const screenshotDir = '/home/user/Agents/output/screenshots';
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    proxy: proxyServer ? { server: proxyServer, username: proxyUsername, password: proxyPassword } : undefined
  });

  const context = await browser.newContext({
    locale: 'nl-NL',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  // Search on englishjobsearch.nl using Playwright
  console.log('Navigating to englishjobsearch.nl to search for jobs...');
  await page.goto('https://englishjobsearch.nl', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);
  
  await page.screenshot({ path: path.join(screenshotDir, '02-englishjobsearch-home.png') });
  console.log('Home page screenshot saved');
  
  // Try to search for the job
  const searchBox = await page.$('input[name="q"], input[type="text"], input[placeholder*="job"], input[placeholder*="Job"], #q, .search-input');
  if (searchBox) {
    console.log('Found search box, filling...');
    await searchBox.click();
    await searchBox.fill('.NET FHIR Developer');
    await page.waitForTimeout(500);
    
    // Look for location field
    const locationBox = await page.$('input[name="l"], input[placeholder*="location"], input[placeholder*="Location"], #l');
    if (locationBox) {
      await locationBox.click();
      await locationBox.fill('Amsterdam');
    }
    
    // Submit search
    await page.keyboard.press('Enter');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotDir, '03-search-results.png'), fullPage: false });
    console.log('Search results screenshot saved');
    console.log('Current URL:', page.url());
    
    // Find job links
    const jobLinks = await page.$$eval('a[href*="/job/"], a[href*="clickout"], .job-title a, h2 a', links => 
      links.map(a => ({ text: a.textContent.trim().substring(0, 100), href: a.href }))
    );
    console.log('Job links found:', JSON.stringify(jobLinks, null, 2));
  } else {
    console.log('No search box found');
    const inputs = await page.$$eval('input', inputs => inputs.map(i => ({ type: i.type, name: i.name, id: i.id, placeholder: i.placeholder })));
    console.log('Available inputs:', JSON.stringify(inputs, null, 2));
  }

  await browser.close();
})().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
