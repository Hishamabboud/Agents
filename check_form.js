const { chromium } = require('playwright');
const proxyEnv = process.env.https_proxy || process.env.HTTPS_PROXY || '';
let proxyOpts;
if (proxyEnv) {
  const match = proxyEnv.match(/^http:\/\/([^:]+):([^@]+)@(.+)/);
  if (match) proxyOpts = { server: 'http://' + match[3], username: match[1], password: match[2] };
}
(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    proxy: proxyOpts
  });
  const ctx = await browser.newContext({ ignoreHTTPSErrors: true, userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  await page.goto('https://careers.keylane.com/jobs/junior-technical-application-engineer-plexus/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);

  const cookieBtn = await page.$('button:has-text("Accept All")');
  if (cookieBtn) { await cookieBtn.click(); await page.waitForTimeout(1000); }

  // Find all form ids and their submit buttons
  const forms = await page.$$eval('form', els => els.map(e => ({ id: e.id, action: e.action, class: e.className.substring(0,80) })));
  console.log('Forms:', JSON.stringify(forms, null, 2));

  // Find button with text Submit
  const submitBtns = await page.$$eval('button:has-text("Submit"), input[value*="Submit"]', els => els.map(e => ({
    tag: e.tagName, id: e.id, class: e.className, text: e.textContent.trim(), outerHTML: e.outerHTML.substring(0, 300)
  })));
  console.log('Submit buttons:', JSON.stringify(submitBtns, null, 2));
  await browser.close();
})().catch(e => { console.error('Error:', e.message); process.exit(1); });
