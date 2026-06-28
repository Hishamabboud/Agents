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

  // Fill form quickly to test submission response
  await page.$eval('#input_3_33_3', el => el.value = 'Hisham');
  await page.$eval('#input_3_33_6', el => el.value = 'Abboud');
  await page.$eval('#input_3_2', el => el.value = 'hiaham123@hotmail.com');
  await page.$eval('#input_3_10', el => el.value = '+31064841 2838');
  await page.$eval('#input_3_12', el => el.value = 'Test motivation letter to see form submission behavior');
  await page.$eval('#input_3_22_1', el => { el.checked = true; el.dispatchEvent(new Event('change', {bubbles:true})); });

  // Listen for response after submit
  page.on('response', resp => {
    if (resp.url().includes('keylane') && !resp.url().match(/\.(css|js|png|woff)/)) {
      console.log('Response:', resp.status(), resp.url().substring(0, 100));
      resp.text().then(t => { if (t.length < 3000) console.log('  Body:', t.substring(0, 500)); }).catch(() => {});
    }
  });

  const btn = await page.$('#gform_submit_button_3');
  await btn.click();
  await page.waitForTimeout(6000);

  const bodyText = await page.evaluate(() => document.body.innerText);
  console.log('FULL PAGE TEXT AFTER SUBMIT (3000 chars):', bodyText.substring(0, 3000));
  console.log('\nURL after submit:', page.url());
  await browser.close();
})().catch(e => { console.error('Error:', e.message); process.exit(1); });
