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

  try {
    await context.addCookies([
      { name: 'cookieyes-consent', value: 'consentid:accepted,consent:yes,action:yes,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes', domain: 'apply.workable.com', path: '/' },
    ]);

    console.log('Navigating to application form...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);

    if (await page.locator('[data-ui="cookie-consent"]').isVisible({ timeout: 2000 }).catch(() => false)) {
      await page.locator('[data-ui="cookie-consent"] button').first().click({ force: true });
      await page.waitForTimeout(1500);
    }

    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    console.log('Form loaded');

    // Fill text fields
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
    if (fileInputs.length >= 2) {
      await fileInputs[1].setInputFiles(resumePath);
    } else if (fileInputs.length === 1) {
      await fileInputs[0].setInputFiles(resumePath);
    }
    await page.waitForTimeout(3000);
    await page.keyboard.press('Escape');
    console.log('Resume uploaded');

    // YES radio via React fiber
    await page.evaluate(() => {
      const yesRadio = document.querySelector('input[name="CA_21816"][value="true"]');
      if (!yesRadio) return;
      const fiberKey = Object.keys(yesRadio).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
      if (!fiberKey) return;
      let fiber = yesRadio[fiberKey];
      while (fiber) {
        const props = fiber.memoizedProps;
        if (props && typeof props.onChange === 'function') {
          yesRadio.checked = true;
          props.onChange({ type: 'change', target: yesRadio, currentTarget: yesRadio, nativeEvent: { target: yesRadio }, bubbles: true, persist: () => {}, preventDefault: () => {}, stopPropagation: () => {} });
          break;
        }
        fiber = fiber.return;
      }
    });
    console.log('YES radio clicked via React');

    // GDPR via React onKeyDown Space
    await page.evaluate(() => {
      const roleChk = document.querySelector('[data-ui="gdpr"] [role="checkbox"]');
      if (!roleChk) return;
      const fiberKey = Object.keys(roleChk).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
      if (!fiberKey) return;
      let fiber = roleChk[fiberKey];
      while (fiber) {
        const props = fiber.memoizedProps;
        if (props && typeof props.onKeyDown === 'function') {
          props.onKeyDown({ type: 'keydown', key: ' ', code: 'Space', keyCode: 32, target: roleChk, currentTarget: roleChk, bubbles: true, persist: () => {}, preventDefault: () => {}, stopPropagation: () => {} });
          break;
        }
        fiber = fiber.return;
      }
    });
    await page.waitForTimeout(300);
    console.log('GDPR checked via React');

    const verify = await page.evaluate(() => {
      const g = sel => document.querySelector(sel);
      return {
        yesRadio: g('input[name="CA_21816"][value="true"]')?.checked,
        gdprAriaChecked: g('[data-ui="gdpr"] [role="checkbox"]')?.getAttribute('aria-checked'),
        gdprNative: g('input[name="gdpr"]')?.checked,
        hasModal: !!g('[data-role="modal-wrapper"]')
      };
    });
    console.log('Key state:', JSON.stringify(verify));

    // Scroll to bottom and take screenshot before submit
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-final-bottom-before-submit.png'), fullPage: false });

    // Check for CAPTCHA
    const captchaInfo = await page.evaluate(() => {
      const captchaEl = document.querySelector('iframe[src*="captcha"], iframe[src*="recaptcha"], iframe[src*="hcaptcha"], [class*="captcha"], [id*="captcha"]');
      const turnstile = document.querySelector('iframe[src*="turnstile"], [class*="turnstile"]');
      const verifyText = Array.from(document.querySelectorAll('*')).find(el => el.childNodes.length === 1 && el.innerText?.includes('Verify you are human'));
      return {
        captchaFound: !!captchaEl,
        turnstileFound: !!turnstile,
        captchaHTML: captchaEl?.outerHTML?.substring(0, 200),
        verifyHuman: verifyText?.outerHTML?.substring(0, 200)
      };
    });
    console.log('Captcha info:', JSON.stringify(captchaInfo, null, 2));

    // Pre-submit full screenshot
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-final-pre-submit-full.png'), fullPage: true });

    // Submit
    console.log('Submitting...');
    await page.evaluate(() => {
      const btn = document.querySelector('button[type="submit"]');
      if (btn) btn.click();
    });
    await page.waitForTimeout(3000);

    // Take bottom screenshot to see any CAPTCHA or errors
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-final-after-submit-bottom.png'), fullPage: false });

    // Check what happened
    const afterSubmitInfo = await page.evaluate(() => {
      const body = document.body.innerText;
      const g = sel => document.querySelector(sel);
      return {
        urlAfter: window.location.href,
        hasThankYou: body.toLowerCase().includes('thank'),
        hasCaptcha: !!g('iframe[src*="captcha"], iframe[src*="recaptcha"], iframe[src*="hcaptcha"]'),
        hasTurnstile: body.toLowerCase().includes('turnstile') || !!g('iframe[src*="turnstile"]'),
        hasVerifyHuman: body.toLowerCase().includes('verify you are human') || body.toLowerCase().includes('i am human'),
        hasError: body.toLowerCase().includes('error') || body.toLowerCase().includes('please accept'),
        submitBtnText: g('button[type="submit"]')?.innerText.trim(),
        bottomText: body.slice(-500)
      };
    });
    console.log('After submit info:', JSON.stringify(afterSubmitInfo, null, 2));

    // Wait more and try again if Submitting...
    if (afterSubmitInfo.submitBtnText === 'Submitting…') {
      console.log('Still submitting... waiting longer');
      await page.waitForTimeout(10000);
    }

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved');
    console.log('Final URL:', page.url());
    console.log('Final text:', await page.evaluate(() => document.body.innerText.substring(0, 1000)));

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-final-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
