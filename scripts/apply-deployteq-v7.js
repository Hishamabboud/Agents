const { chromium } = require('playwright');
const path = require('path');

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

  const coverLetterText = `Dear DeployTeq Hiring Team,

I am writing to apply for the Software Developer position at DeployTeq in Zeist.

As a Software Engineer at Actemium (VINCI Energies), I build and maintain full-stack applications using .NET/C#, ASP.NET, Python/Flask, and JavaScript. DeployTeq's focus on online marketing technology is an exciting domain where I can apply my backend and frontend development skills.

My technical experience includes:
- Backend: C#, .NET Core, ASP.NET MVC, Python, Flask, SQL Server, REST APIs
- Frontend: JavaScript, TypeScript, HTML5, CSS3, React
- DevOps: Git, Azure DevOps, CI/CD, Docker
- Testing: Unit testing, Pytest, Locust performance testing

At ASML, I built performance testing infrastructure on Azure Kubernetes Service. At Delta Electronics, I migrated legacy C++ systems to C#/.NET. I hold a BSc in Software Engineering from Fontys University of Applied Sciences.

I am eager to contribute to DeployTeq's platform development and grow within your team.

Kind regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
Eindhoven, Netherlands`;

  // Intercept and log API calls to monitor submission
  const apiResponses = [];
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('workable') && (url.includes('apply') || url.includes('candidate'))) {
      try {
        const status = response.status();
        let body = '';
        if (status !== 204) {
          body = await response.text().catch(() => '');
        }
        apiResponses.push({ url, status, body: body.substring(0, 200) });
        console.log(`API: ${status} ${url.substring(0, 80)} | ${body.substring(0, 100)}`);
      } catch(e) {}
    }
  });

  // Dismiss ALL cookie modals
  const dismissAllCookieModals = async () => {
    // Try clicking "Accept all" in any cookie modal
    const btns = ['button:has-text("Accept all")', 'button:has-text("Accept All")', 'button[class*="accept"]'];
    for (const sel of btns) {
      const btn = page.locator(sel).first();
      if (await btn.isVisible({ timeout: 500 }).catch(() => false)) {
        await btn.click({ force: true });
        await page.waitForTimeout(500);
      }
    }
    // Close via X button
    const closeBtn = page.locator('[aria-label="Close"], button:has-text("×"), button:has-text("X")').first();
    if (await closeBtn.isVisible({ timeout: 500 }).catch(() => false)) {
      await closeBtn.click({ force: true });
      await page.waitForTimeout(300);
    }
    // Remove modal from DOM
    await page.evaluate(() => {
      document.querySelectorAll('[data-role="modal-wrapper"], [data-role="backdrop"]').forEach(el => el.remove());
    });
  };

  try {
    // Pre-set cookie consent
    await context.addCookies([
      { name: 'wrkbl_cookie_pref', value: '{"necessary":true,"analytics":true,"advertisement":true,"functionality":true}', domain: 'apply.workable.com', path: '/' },
    ]);

    console.log('Navigating...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(2000);

    // Accept initial cookie banner
    await dismissAllCookieModals();
    await page.waitForTimeout(1000);

    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    console.log('Form ready');

    // Fill fields
    await page.fill('input[name="firstname"]', 'Hisham');
    await page.fill('input[name="lastname"]', 'Abboud');
    await page.fill('input[type="email"]', 'hiaham123@hotmail.com');
    await page.evaluate(() => document.querySelector('input[type="tel"]').focus());
    await page.fill('input[type="tel"]', '+31064841 2838');
    await page.keyboard.press('Escape');
    await page.fill('input[name="address"]', 'Eindhoven, Netherlands');
    await page.keyboard.press('Escape');
    await page.fill('textarea[name="cover_letter"]', coverLetterText);
    await page.fill('input[name="CA_21813"]', '1 month');
    await page.fill('input[name="CA_21815"]', '65000');
    await page.fill('textarea[name="QA_11807072"]', 'Yes, I currently reside in Eindhoven, Netherlands.');
    await page.fill('textarea[name="QA_11807073"]', 'Yes, I can commute to the office in Huis ter Heide, Utrecht. The journey from Eindhoven is approximately 60 minutes by public transport, which I am comfortable doing.');
    console.log('Text filled');

    // Upload resume
    const fileInputs = await page.locator('input[type="file"]').all();
    if (fileInputs.length >= 2) await fileInputs[1].setInputFiles(resumePath);
    else if (fileInputs.length === 1) await fileInputs[0].setInputFiles(resumePath);
    await page.waitForTimeout(3000);
    await dismissAllCookieModals();
    console.log('Resume uploaded');

    // YES radio via React
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
    console.log('YES radio set');

    // GDPR via React onKeyDown Space
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
    console.log('GDPR checked');

    // Verify
    const v = await page.evaluate(() => ({
      yes: document.querySelector('input[name="CA_21816"][value="true"]')?.checked,
      gdpr: document.querySelector('[data-ui="gdpr"] [role="checkbox"]')?.getAttribute('aria-checked'),
      nativeGdpr: document.querySelector('input[name="gdpr"]')?.checked
    }));
    console.log('State:', v);

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v7-01-pre-submit.png'), fullPage: true });

    // Click submit
    console.log('Clicking submit...');
    await page.evaluate(() => document.querySelector('button[type="submit"]')?.click());

    // Immediately after submit, watch for and dismiss cookie modals
    console.log('Monitoring post-submit for 20 seconds...');
    let success = false;
    for (let i = 0; i < 20; i++) {
      await page.waitForTimeout(1000);
      const url = page.url();
      const pageText = await page.evaluate(() => document.body.innerText.toLowerCase());

      if (!url.includes('/5246F389F7/apply/') || pageText.includes('thank') || pageText.includes('application received')) {
        success = true;
        console.log(`SUCCESS at ${i}s!`);
        break;
      }

      // Dismiss any cookie modal that appeared
      const cookieModalVisible = await page.evaluate(() => {
        const modal = document.querySelector('[data-role="modal-wrapper"]');
        return modal && modal.innerText?.includes('cookie');
      });
      if (cookieModalVisible) {
        console.log(`[${i}s] Cookie modal appeared, dismissing...`);
        await dismissAllCookieModals();
      }

      // Check button state
      const btnState = await page.evaluate(() => document.querySelector('button[type="submit"]')?.innerText.trim());
      if (i % 3 === 0) console.log(`[${i}s] Button: "${btnState}", URL: ${url.substring(50)}`);

      // If still "Submit application" (not submitting), try clicking again
      if (btnState === 'Submit application') {
        console.log(`[${i}s] Re-clicking submit button...`);
        await page.evaluate(() => document.querySelector('button[type="submit"]')?.click());
      }
    }

    // Take final screenshots
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v7-02-after-submit-top.png'), fullPage: false });
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v7-03-after-submit-bottom.png'), fullPage: false });

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved');
    console.log('Final URL:', page.url());

    const finalText = await page.evaluate(() => document.body.innerText.substring(0, 1500));
    console.log('Final text:\n', finalText);

    console.log('\nAPI Responses captured:', apiResponses.length);
    apiResponses.forEach(r => console.log(` - ${r.status} ${r.url}`));

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v7-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
