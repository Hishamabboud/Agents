const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  console.log('Navigating to CoolGames job page...');
  await page.goto('https://apply.workable.com/coolgames/j/3654334706', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(3000);

  // Take screenshot of job description page
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-job-description.png', fullPage: true });
  console.log('Screenshot taken: coolgames-job-description.png');

  // Extract job description text
  const jobText = await page.evaluate(() => document.body.innerText);
  fs.writeFileSync('/home/user/Agents/data/coolgames-job-raw.txt', jobText);
  console.log('Job description saved.');

  // Look for Apply button
  const applyBtn = page.locator('a[href*="apply"], button:has-text("Apply"), a:has-text("Apply")').first();
  const applyBtnCount = await applyBtn.count();
  console.log('Apply button found:', applyBtnCount > 0);

  if (applyBtnCount > 0) {
    await applyBtn.click();
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-apply-form.png', fullPage: true });
    console.log('Screenshot taken: coolgames-apply-form.png');
    const formText = await page.evaluate(() => document.body.innerText);
    fs.writeFileSync('/home/user/Agents/data/coolgames-form-raw.txt', formText);
    console.log('Form page saved.');
  }

  await browser.close();
  console.log('Done.');
})();
