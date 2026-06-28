const { chromium } = require('playwright');
const path = require('path');

// This script captures the API call made when submitting the Workable form
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });
  const page = await context.newPage();
  const screenshotDir = '/home/user/Agents/output/screenshots';
  const resumePath = '/home/user/Agents/profile/Hisham Abboud CV.pdf';

  // Capture ALL network requests
  const capturedRequests = [];
  page.on('request', request => {
    const url = request.url();
    const method = request.method();
    if (method === 'POST' || (url.includes('candidate') || url.includes('apply') || url.includes('submit'))) {
      capturedRequests.push({
        method,
        url,
        postData: request.postData()?.substring(0, 500),
        headers: Object.fromEntries(
          Object.entries(request.headers()).filter(([k]) => ['content-type', 'authorization', 'x-csrf-token', 'x-requested-with'].includes(k))
        )
      });
    }
  });

  page.on('response', async response => {
    const url = response.url();
    const status = response.status();
    if (url.includes('workable') && status !== 200 && status !== 204) {
      const text = await response.text().catch(() => '');
      console.log(`RESPONSE ${status} ${url}: ${text.substring(0, 200)}`);
    }
  });

  try {
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded', timeout: 30000
    });
    await page.waitForTimeout(2000);

    if (await page.locator('[data-ui="cookie-consent"]').isVisible({ timeout: 2000 }).catch(() => false)) {
      await page.locator('[data-ui="cookie-consent"] button').first().click({ force: true });
      await page.waitForTimeout(1000);
    }

    await page.waitForSelector('input[name="firstname"]', { timeout: 10000 });

    // Fill all fields
    await page.fill('input[name="firstname"]', 'Hisham');
    await page.fill('input[name="lastname"]', 'Abboud');
    await page.fill('input[type="email"]', 'hiaham123@hotmail.com');
    await page.evaluate(() => document.querySelector('input[type="tel"]').focus());
    await page.fill('input[type="tel"]', '+31064841 2838');
    await page.keyboard.press('Escape');
    await page.fill('input[name="address"]', 'Eindhoven, Netherlands');
    await page.keyboard.press('Escape');
    await page.fill('textarea[name="cover_letter"]', 'Test cover letter for capturing the API endpoint.');
    await page.fill('input[name="CA_21813"]', '1 month');
    await page.fill('input[name="CA_21815"]', '65000');
    await page.fill('textarea[name="QA_11807072"]', 'Yes.');
    await page.fill('textarea[name="QA_11807073"]', 'Yes.');

    // Upload resume
    const fileInputs = await page.locator('input[type="file"]').all();
    if (fileInputs.length >= 2) await fileInputs[1].setInputFiles(resumePath);
    await page.waitForTimeout(3000);
    await page.keyboard.press('Escape');

    // YES radio
    await page.evaluate(() => {
      const r = document.querySelector('input[name="CA_21816"][value="true"]');
      if (!r) return;
      const fk = Object.keys(r).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
      if (!fk) return;
      let f = r[fk];
      while (f) {
        const p = f.memoizedProps;
        if (p && typeof p.onChange === 'function') {
          r.checked = true;
          p.onChange({ type: 'change', target: r, currentTarget: r, nativeEvent: { target: r }, bubbles: true, persist: () => {}, preventDefault: () => {}, stopPropagation: () => {} });
          break;
        }
        f = f.return;
      }
    });

    // GDPR
    await page.evaluate(() => {
      const rc = document.querySelector('[data-ui="gdpr"] [role="checkbox"]');
      if (!rc) return;
      const fk = Object.keys(rc).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
      if (!fk) return;
      let f = rc[fk];
      while (f) {
        const p = f.memoizedProps;
        if (p && typeof p.onKeyDown === 'function') {
          p.onKeyDown({ type: 'keydown', key: ' ', code: 'Space', keyCode: 32, target: rc, currentTarget: rc, bubbles: true, persist: () => {}, preventDefault: () => {}, stopPropagation: () => {} });
          break;
        }
        f = f.return;
      }
    });
    await page.waitForTimeout(300);

    console.log('All fields filled. Clicking submit to capture API call...');
    await page.evaluate(() => document.querySelector('button[type="submit"]')?.click());

    // Wait and capture
    await page.waitForTimeout(15000);

    console.log('\n=== CAPTURED REQUESTS ===');
    capturedRequests.forEach(r => {
      console.log(`${r.method} ${r.url}`);
      if (r.postData) console.log(`  Body: ${r.postData}`);
      if (Object.keys(r.headers).length) console.log(`  Headers: ${JSON.stringify(r.headers)}`);
    });

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-capture-api.png'), fullPage: true });

  } catch(e) {
    console.error(e.message);
  } finally {
    await browser.close();
  }
})();
