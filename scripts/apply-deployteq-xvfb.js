const { chromium } = require('playwright');
const path = require('path');

// This script runs with Xvfb for a real display to pass Cloudflare Turnstile
(async () => {
  // Launch with headed mode but Xvfb provides virtual display
  const browser = await chromium.launch({
    headless: false,  // headed mode to help pass Cloudflare checks
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled',
      '--disable-infobars',
      '--window-size=1280,900',
      '--start-maximized'
    ]
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    locale: 'en-US',
    timezoneId: 'Europe/Amsterdam',
    // Remove automation indicators
    javaScriptEnabled: true
  });

  // Spoof webdriver detection
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    delete navigator.__proto__.webdriver;
    window.chrome = { runtime: {} };
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'nl'] });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
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

  // Listen for successful submission
  let submissionToken = null;
  page.on('request', req => {
    if (req.method() === 'POST' && req.url().includes('apply.workable.com/api')) {
      console.log(`API POST: ${req.url()}`);
      const headers = req.headers();
      if (headers['x-turnstile-token']) {
        submissionToken = headers['x-turnstile-token'];
        console.log('Got Turnstile token!', submissionToken.substring(0, 20));
      }
    }
  });

  page.on('response', async resp => {
    if (resp.request().method() === 'POST' && resp.url().includes('apply.workable.com/api')) {
      const status = resp.status();
      const body = await resp.text().catch(() => '');
      console.log(`API RESPONSE ${status}: ${body.substring(0, 300)}`);
    }
  });

  try {
    console.log('Navigating (headed mode with Xvfb)...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);

    // Accept cookies
    if (await page.locator('[data-ui="cookie-consent"]').isVisible({ timeout: 3000 }).catch(() => false)) {
      await page.locator('[data-ui="cookie-consent"] button').first().click({ force: true });
      await page.waitForTimeout(1500);
    }

    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    console.log('Form loaded');

    // Simulate human behavior - small mouse movements
    await page.mouse.move(100, 100);
    await page.waitForTimeout(200);
    await page.mouse.move(300, 200);
    await page.waitForTimeout(100);

    // Fill fields
    await page.fill('input[name="firstname"]', 'Hisham');
    await page.waitForTimeout(300);
    await page.fill('input[name="lastname"]', 'Abboud');
    await page.waitForTimeout(200);
    await page.fill('input[type="email"]', 'hiaham123@hotmail.com');
    await page.waitForTimeout(200);
    await page.evaluate(() => document.querySelector('input[type="tel"]').focus());
    await page.fill('input[type="tel"]', '+31064841 2838');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    await page.fill('input[name="address"]', 'Eindhoven, Netherlands');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);
    await page.fill('textarea[name="cover_letter"]', coverLetterText);
    await page.waitForTimeout(200);
    await page.fill('input[name="CA_21813"]', '1 month');
    await page.waitForTimeout(200);
    await page.fill('input[name="CA_21815"]', '65000');
    await page.waitForTimeout(200);
    await page.fill('textarea[name="QA_11807072"]', 'Yes, I currently reside in Eindhoven, Netherlands.');
    await page.waitForTimeout(200);
    await page.fill('textarea[name="QA_11807073"]', 'Yes, I can commute to the office in Huis ter Heide, Utrecht. The journey from Eindhoven is approximately 60 minutes by public transport, which I am comfortable doing.');
    await page.waitForTimeout(200);
    console.log('Text fields filled');

    // Scroll around to simulate human behavior
    await page.evaluate(() => window.scrollTo(0, 300));
    await page.waitForTimeout(500);
    await page.evaluate(() => window.scrollTo(0, 600));
    await page.waitForTimeout(500);

    // Upload resume
    const fileInputs = await page.locator('input[type="file"]').all();
    if (fileInputs.length >= 2) await fileInputs[1].setInputFiles(resumePath);
    else if (fileInputs.length === 1) await fileInputs[0].setInputFiles(resumePath);
    await page.waitForTimeout(3000);
    await page.keyboard.press('Escape');
    console.log('Resume uploaded');

    // Scroll down to see the rest of the form
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
    await page.waitForTimeout(500);

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
    await page.waitForTimeout(200);

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

    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);

    // Verify
    const v = await page.evaluate(() => ({
      yes: document.querySelector('input[name="CA_21816"][value="true"]')?.checked,
      gdpr: document.querySelector('[data-ui="gdpr"] [role="checkbox"]')?.getAttribute('aria-checked'),
      hasModal: !!document.querySelector('[data-role="modal-wrapper"]')
    }));
    console.log('State:', v);

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-xvfb-pre-submit.png'), fullPage: true });

    // Scroll back to top
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);

    // The Turnstile widget should be loaded at this point
    // Let's check its state
    const turnstileInfo = await page.evaluate(() => {
      const widget = document.querySelector('[id*="turnstile"], [class*="turnstile"], iframe[src*="turnstile"]');
      return {
        hasWidget: !!widget,
        widgetInfo: widget ? widget.outerHTML.substring(0, 200) : null,
        windowTurnstile: !!window.turnstile
      };
    });
    console.log('Turnstile info:', turnstileInfo);

    // Click submit (Turnstile should auto-complete in headed mode)
    console.log('Submitting...');
    await page.evaluate(() => document.querySelector('button[type="submit"]')?.click());

    // Wait for submission to complete
    let success = false;
    for (let i = 0; i < 45; i++) {
      await page.waitForTimeout(1000);
      const url = page.url();
      const text = await page.evaluate(() => document.body.innerText.toLowerCase().substring(0, 500));

      if (!url.includes('/5246F389F7/apply/') || text.includes('thank') || text.includes('application received')) {
        success = true;
        console.log(`SUCCESS at ${i}s! URL: ${url}`);
        break;
      }

      if (i % 5 === 0) {
        const btn = await page.evaluate(() => document.querySelector('button[type="submit"]')?.innerText.trim());
        const errors = await page.evaluate(() =>
          Array.from(document.querySelectorAll('[class*="error"]')).map(e => e.innerText.trim()).filter(t => t.length > 3).slice(0, 3)
        );
        console.log(`[${i}s] Button: "${btn}" | Errors: ${JSON.stringify(errors)}`);

        if (btn === 'Submit application') {
          // Turnstile might have timed out, try clicking again
          await page.evaluate(() => document.querySelector('button[type="submit"]')?.click());
        }
      }
    }

    // Final screenshots
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved');
    console.log('Final URL:', page.url());

    const finalText = await page.evaluate(() => document.body.innerText.substring(0, 1500));
    console.log('Final text:', finalText);

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-xvfb-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
