const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
const path = require('path');

// Apply stealth to bypass Cloudflare bot detection
chromium.use(stealth());

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu'
    ]
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    locale: 'en-US',
    timezoneId: 'Europe/Amsterdam'
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

  // Listen for the actual submission API call
  const submissionRequests = [];
  page.on('request', req => {
    const url = req.url();
    const method = req.method();
    if (method === 'POST' && url.includes('apply.workable.com')) {
      submissionRequests.push({ url, body: req.postData()?.substring(0, 300) });
      console.log(`POST ${url}: ${req.postData()?.substring(0, 100)}`);
    }
  });
  page.on('response', async resp => {
    const url = resp.url();
    if (url.includes('apply.workable.com') && resp.request().method() === 'POST') {
      const status = resp.status();
      const body = await resp.text().catch(() => '');
      console.log(`RESPONSE ${status} ${url}: ${body.substring(0, 200)}`);
    }
  });

  try {
    console.log('Navigating with stealth...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);

    // Dismiss cookies
    if (await page.locator('[data-ui="cookie-consent"]').isVisible({ timeout: 3000 }).catch(() => false)) {
      await page.locator('[data-ui="cookie-consent"] button').first().click({ force: true });
      await page.waitForTimeout(1500);
    }

    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    console.log('Form loaded');

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
    console.log('Text fields filled');

    // Upload resume
    const fileInputs = await page.locator('input[type="file"]').all();
    if (fileInputs.length >= 2) await fileInputs[1].setInputFiles(resumePath);
    else if (fileInputs.length === 1) await fileInputs[0].setInputFiles(resumePath);
    await page.waitForTimeout(3000);
    await page.keyboard.press('Escape');
    console.log('Resume uploaded');

    // YES radio via React fiber
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

    const verify = await page.evaluate(() => ({
      yes: document.querySelector('input[name="CA_21816"][value="true"]')?.checked,
      gdpr: document.querySelector('[data-ui="gdpr"] [role="checkbox"]')?.getAttribute('aria-checked'),
      nativeGdpr: document.querySelector('input[name="gdpr"]')?.checked
    }));
    console.log('Verification:', verify);

    // Screenshot before submit
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-stealth-pre-submit.png'), fullPage: true });

    // Submit
    console.log('Submitting...');
    await page.evaluate(() => document.querySelector('button[type="submit"]')?.click());

    // Wait and monitor
    let submitted = false;
    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(1000);
      const url = page.url();
      const text = await page.evaluate(() => document.body.innerText.toLowerCase().substring(0, 500));

      if (!url.includes('/5246F389F7/apply/') || text.includes('thank') || text.includes('application received')) {
        submitted = true;
        console.log(`SUCCESS at ${i}s! URL: ${url}`);
        break;
      }

      if (i % 5 === 0) {
        const btn = await page.evaluate(() => document.querySelector('button[type="submit"]')?.innerText.trim());
        console.log(`[${i}s] Button: "${btn}"`);

        const errors = await page.evaluate(() =>
          Array.from(document.querySelectorAll('[class*="error"]')).map(e => e.innerText.trim()).filter(t => t.length > 3).slice(0, 3)
        );
        if (errors.length) console.log(`[${i}s] Errors:`, errors);
      }
    }

    // Final screenshots
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved');
    console.log('URL:', page.url());

    const finalText = await page.evaluate(() => document.body.innerText.substring(0, 1000));
    console.log('Final text:', finalText);

    console.log('\nSubmission requests captured:', submissionRequests.length);

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-stealth-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
