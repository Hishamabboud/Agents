const { chromium } = require('playwright');
const path = require('path');
const proxyEnv = process.env.https_proxy || process.env.HTTPS_PROXY || '';
let proxyOpts;
if (proxyEnv) {
  const match = proxyEnv.match(/^http:\/\/([^:]+):([^@]+)@(.+)/);
  if (match) proxyOpts = { server: 'http://' + match[3], username: match[1], password: match[2] };
}

const screenshotDir = '/home/user/Agents/output/screenshots';

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    proxy: proxyOpts
  });
  const ctx = await browser.newContext({ ignoreHTTPSErrors: true, userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  // Intercept all AJAX responses from Keylane
  const keylaneResponses = [];
  page.on('response', async resp => {
    if (resp.url().includes('keylane') && !resp.url().match(/\.(css|js|png|woff|jpg|svg)/)) {
      const status = resp.status();
      const url = resp.url();
      try {
        const body = await resp.text();
        keylaneResponses.push({ status, url, body: body.substring(0, 2000) });
        console.log('Response:', status, url.substring(0, 100));
        if (body.length < 2000) console.log('  Body preview:', body.substring(0, 300));
      } catch(e) {}
    }
  });

  await page.goto('https://careers.keylane.com/jobs/junior-technical-application-engineer-plexus/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);

  const cookieBtn = await page.$('button:has-text("Accept All")');
  if (cookieBtn) { await cookieBtn.click(); await page.waitForTimeout(1000); }

  // Fill form with proper values
  const fnInput = await page.$('#input_3_33_3');
  await fnInput.fill('Hisham');
  const lnInput = await page.$('#input_3_33_6');
  await lnInput.fill('Abboud');
  const emailInput = await page.$('#input_3_2');
  await emailInput.fill('hiaham123@hotmail.com');
  const phoneInput = await page.$('#input_3_10');
  await phoneInput.fill('+31 06 4841 2838');
  const motivInput = await page.$('#input_3_12');
  await motivInput.fill('Motivation text for test - checking Gravity Forms AJAX response behavior');
  await page.evaluate(() => {
    const cb = document.querySelector('#input_3_22_1');
    if (cb) { cb.checked = true; cb.dispatchEvent(new Event('change', {bubbles: true})); }
  });

  // Listen for DOM changes after submit
  await page.evaluate(() => {
    window.__gformResponses = [];
    const observer = new MutationObserver(mutations => {
      for (const m of mutations) {
        for (const n of m.addedNodes) {
          if (n.nodeType === 1) window.__gformResponses.push(n.outerHTML ? n.outerHTML.substring(0, 500) : 'node added');
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });

  const btn = await page.$('#gform_submit_button_3');
  await btn.click();
  console.log('Clicked submit, waiting for AJAX...');
  await page.waitForTimeout(8000);

  // Check DOM changes
  const domChanges = await page.evaluate(() => window.__gformResponses || []);
  console.log('\nDOM changes after submit:', domChanges.slice(0, 5));

  // Check for confirmation/error in the form area
  const formAreaHTML = await page.$eval('#gform_3, .gform_wrapper', el => el.innerHTML.substring(0, 3000)).catch(() => 'Form not found');
  console.log('\nForm area HTML after submit:', formAreaHTML.substring(0, 1500));

  // Check for validation errors
  const validationErrors = await page.$$eval('.gfield_error, .validation_error, .gfield--error', els => els.map(e => ({ class: e.className, text: e.textContent.trim().substring(0, 200) })));
  console.log('\nValidation errors:', JSON.stringify(validationErrors, null, 2));

  // Full screenshot
  await page.screenshot({ path: path.join(screenshotDir, 'keylane-submit-check.png'), fullPage: true });
  console.log('\nScreenshot: keylane-submit-check.png');

  await browser.close();
})().catch(e => { console.error('Error:', e.message); process.exit(1); });
