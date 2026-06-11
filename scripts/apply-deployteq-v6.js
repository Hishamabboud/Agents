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

  // Click YES radio via React fiber onChange
  const clickYesRadio = () => page.evaluate(() => {
    const yesRadio = document.querySelector('input[name="CA_21816"][value="true"]');
    if (!yesRadio) return 'not found';
    const fiberKey = Object.keys(yesRadio).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
    if (!fiberKey) return 'no fiber';
    let fiber = yesRadio[fiberKey];
    while (fiber) {
      const props = fiber.memoizedProps;
      if (props && typeof props.onChange === 'function') {
        yesRadio.checked = true;
        props.onChange({ type: 'change', target: yesRadio, currentTarget: yesRadio, nativeEvent: { target: yesRadio }, bubbles: true, persist: () => {}, preventDefault: () => {}, stopPropagation: () => {} });
        return `onChange called. Checked: ${yesRadio.checked}`;
      }
      fiber = fiber.return;
    }
    return 'no onChange found';
  });

  // Click GDPR checkbox via React fiber onClick/onChange
  const clickGdprCheckbox = () => page.evaluate(() => {
    // The GDPR container
    const gdprContainer = document.querySelector('[data-ui="gdpr"]');
    const roleCheckbox = document.querySelector('[data-ui="gdpr"] [role="checkbox"]');
    const nativeCheckbox = document.querySelector('input[name="gdpr"]');

    if (!roleCheckbox && !nativeCheckbox) return 'no gdpr elements found';

    const results = [];

    // Try React fiber on the role=checkbox div
    if (roleCheckbox) {
      const fiberKey = Object.keys(roleCheckbox).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
      if (fiberKey) {
        let fiber = roleCheckbox[fiberKey];
        while (fiber) {
          const props = fiber.memoizedProps;
          if (props && (typeof props.onClick === 'function' || typeof props.onChange === 'function')) {
            const handler = props.onClick || props.onChange;
            // Create a synthetic click event
            const syntheticEvent = {
              type: 'click',
              target: roleCheckbox,
              currentTarget: roleCheckbox,
              nativeEvent: new MouseEvent('click', { bubbles: true }),
              bubbles: true,
              persist: () => {},
              preventDefault: () => {},
              stopPropagation: () => {}
            };
            handler(syntheticEvent);
            results.push(`Called onClick/onChange on role=checkbox. New aria-checked: ${roleCheckbox.getAttribute('aria-checked')}`);
            break;
          }
          fiber = fiber.return;
        }
      }
    }

    // Also try on the parent gdpr container label
    if (gdprContainer) {
      const fiberKey = Object.keys(gdprContainer).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
      if (fiberKey) {
        let fiber = gdprContainer[fiberKey];
        while (fiber) {
          const props = fiber.memoizedProps;
          if (props && typeof props.onClick === 'function') {
            props.onClick({ type: 'click', target: gdprContainer, persist: () => {}, preventDefault: () => {}, stopPropagation: () => {} });
            results.push(`Called onClick on gdpr container`);
            break;
          }
          fiber = fiber.return;
        }
      }
    }

    // Force native checkbox
    if (nativeCheckbox) {
      if (!nativeCheckbox.checked) {
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked');
        if (nativeSetter && nativeSetter.set) nativeSetter.set.call(nativeCheckbox, true);
        nativeCheckbox.dispatchEvent(new Event('change', { bubbles: true }));
        results.push(`Set native checkbox checked: ${nativeCheckbox.checked}`);
      } else {
        results.push('Native checkbox already checked');
      }
    }

    return results.join(' | ');
  });

  // Escape any modal
  const pressEsc = async () => {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
  };

  try {
    console.log('Navigating to application form...');
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

    // Fill text fields
    await page.fill('input[name="firstname"]', 'Hisham');
    await page.fill('input[name="lastname"]', 'Abboud');
    await page.fill('input[type="email"]', 'hiaham123@hotmail.com');
    await page.evaluate(() => document.querySelector('input[type="tel"]').focus());
    await page.fill('input[type="tel"]', '+31064841 2838');
    await pressEsc();
    await page.fill('input[name="address"]', 'Eindhoven, Netherlands');
    await pressEsc();
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
      console.log('Resume uploaded');
    }
    await page.waitForTimeout(3000);
    await pressEsc();

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v6-01-fields-filled.png'), fullPage: true });

    // Click YES radio via React
    const radioResult = await clickYesRadio();
    console.log('YES radio:', radioResult);
    const yesChecked = await page.evaluate(() => document.querySelector('input[name="CA_21816"][value="true"]')?.checked);
    console.log('YES radio checked:', yesChecked);
    await pressEsc();

    // Click GDPR via React
    const gdprResult = await clickGdprCheckbox();
    console.log('GDPR result:', gdprResult);
    const gdprState = await page.evaluate(() => ({
      ariaChecked: document.querySelector('[data-ui="gdpr"] [role="checkbox"]')?.getAttribute('aria-checked'),
      nativeChecked: document.querySelector('input[name="gdpr"]')?.checked
    }));
    console.log('GDPR state:', JSON.stringify(gdprState));
    await pressEsc();

    // Verify all fields
    const verify = await page.evaluate(() => {
      const g = sel => document.querySelector(sel);
      return {
        firstname: g('input[name="firstname"]')?.value,
        lastname: g('input[name="lastname"]')?.value,
        email: g('input[type="email"]')?.value,
        phone: g('input[type="tel"]')?.value,
        address: g('input[name="address"]')?.value,
        noticePeriod: g('input[name="CA_21813"]')?.value,
        salary: g('input[name="CA_21815"]')?.value,
        yesRadio: g('input[name="CA_21816"][value="true"]')?.checked,
        qa1len: g('textarea[name="QA_11807072"]')?.value?.length,
        qa2len: g('textarea[name="QA_11807073"]')?.value?.length,
        coverLen: g('textarea[name="cover_letter"]')?.value?.length,
        gdprAriaChecked: g('[data-ui="gdpr"] [role="checkbox"]')?.getAttribute('aria-checked'),
        gdprNative: g('input[name="gdpr"]')?.checked,
        hasResume: document.body.innerText.includes('Hisham Abboud CV.pdf'),
        hasModal: !!g('[data-role="modal-wrapper"]')
      };
    });
    console.log('Verification:', JSON.stringify(verify, null, 2));

    // Screenshots before submit
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v6-02-pre-submit-top.png'), fullPage: false });
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v6-03-pre-submit-mid.png'), fullPage: false });
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v6-04-pre-submit-bottom.png'), fullPage: false });

    // Full page pre-submit
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v6-05-pre-submit-full.png'), fullPage: true });

    // Submit
    console.log('Submitting...');
    const submitResult = await page.evaluate(() => {
      const btn = document.querySelector('button[type="submit"]');
      if (!btn) return 'NO BUTTON';
      btn.click();
      return `Clicked: "${btn.innerText.trim()}"`;
    });
    console.log('Submit:', submitResult);

    // Wait and check for success
    let success = false;
    for (let i = 0; i < 20; i++) {
      await page.waitForTimeout(1000);
      const url = page.url();
      const hasThank = await page.evaluate(() => {
        const t = document.body.innerText.toLowerCase();
        return t.includes('thank') || t.includes('received your application') || t.includes('successfully');
      });
      if (!url.includes('/5246F389F7/apply/') || hasThank) {
        success = true;
        console.log(`Success at iteration ${i}! URL: ${url}`);
        break;
      }
      if (i % 5 === 0) {
        const btnText = await page.evaluate(() => document.querySelector('button[type="submit"]')?.innerText.trim() || 'no button');
        console.log(`[${i}s] Submit button: "${btnText}", URL: ${url.substring(0, 60)}`);
        const errors = await page.evaluate(() => {
          return Array.from(document.querySelectorAll('[class*="error"]')).map(e => e.innerText.trim().substring(0, 80)).filter(t => t.length > 2);
        });
        if (errors.length) console.log('Errors:', errors);
      }
    }

    // Final screenshot
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved');
    console.log('Final URL:', page.url());

    const finalText = await page.evaluate(() => document.body.innerText.substring(0, 2000));
    console.log('Final page text:\n', finalText);

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v6-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
