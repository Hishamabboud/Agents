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

  // Helper: set React-controlled input/textarea value
  const jsSetInput = async (selector, value) => {
    return await page.evaluate(({ sel, val }) => {
      const el = document.querySelector(sel);
      if (!el) return `Not found: ${sel}`;
      const proto = el.tagName === 'TEXTAREA'
        ? window.HTMLTextAreaElement.prototype
        : window.HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, 'value');
      if (setter && setter.set) setter.set.call(el, val);
      else el.value = val;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return `OK: ${el.name || el.id || sel}`;
    }, { sel: selector, val: value });
  };

  // Helper: close all modals and overlays via JS
  const closeAllModals = async () => {
    await page.evaluate(() => {
      // Remove modal wrappers
      document.querySelectorAll('[data-role="modal-wrapper"]').forEach(el => {
        el.remove();
      });
      // Remove backdrops
      document.querySelectorAll('[data-role="backdrop"]').forEach(el => {
        el.remove();
      });
      // Remove cookie consent dialogs
      document.querySelectorAll('[data-ui="cookie-consent"]').forEach(el => {
        el.remove();
      });
      // Remove any fixed overlays
      document.querySelectorAll('[role="dialog"]').forEach(el => {
        el.remove();
      });
    });
    await page.waitForTimeout(300);
  };

  try {
    console.log('Navigating to application form...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-01-initial-load.png'), fullPage: true });

    // Dismiss cookie consent the normal way first
    const cookieDialog = page.locator('[data-ui="cookie-consent"]');
    if (await cookieDialog.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('Dismissing cookie consent...');
      await page.locator('[data-ui="cookie-consent"] button').first().click({ force: true });
      await page.waitForTimeout(1500);
    }

    // Wait for form
    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    await page.waitForTimeout(500);
    console.log('Form ready');

    // Fill all form fields using JS to avoid triggering React autocomplete/dropdown modals
    const fillResults = await page.evaluate(({ cl }) => {
      const results = [];

      const setVal = (selector, value) => {
        const el = document.querySelector(selector);
        if (!el) { results.push(`NOT FOUND: ${selector}`); return; }
        const proto = el.tagName === 'TEXTAREA'
          ? window.HTMLTextAreaElement.prototype
          : window.HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value');
        if (setter && setter.set) setter.set.call(el, value);
        else el.value = value;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        results.push(`SET ${el.name || selector}: ${value.substring(0, 30)}`);
      };

      setVal('input[name="firstname"]', 'Hisham');
      setVal('input[name="lastname"]', 'Abboud');
      setVal('input[type="email"]', 'hiaham123@hotmail.com');
      setVal('input[type="tel"]', '+31064841 2838');
      setVal('input[name="address"]', 'Eindhoven, Netherlands');
      setVal('textarea[name="cover_letter"]', cl);
      setVal('input[name="CA_21813"]', '1 month');
      setVal('input[name="CA_21815"]', '65000');
      setVal('textarea[name="QA_11807072"]', 'Yes, I currently reside in Eindhoven, Netherlands.');
      setVal('textarea[name="QA_11807073"]', 'Yes, I can commute to the office in Huis ter Heide, Utrecht. The journey from Eindhoven is approximately 60 minutes by public transport.');

      // Click YES for right to work
      const yesLabel = document.querySelector('label:has(input[name="CA_21816"][value="true"])');
      if (yesLabel) {
        yesLabel.click();
        const yesRadio = document.querySelector('input[name="CA_21816"][value="true"]');
        if (yesRadio) { yesRadio.checked = true; yesRadio.dispatchEvent(new Event('change', { bubbles: true })); }
        results.push('Clicked YES for right to work');
      }

      // GDPR
      const roleCheckbox = document.querySelector('[data-ui="gdpr"] [role="checkbox"]');
      if (roleCheckbox) {
        roleCheckbox.click();
        roleCheckbox.setAttribute('aria-checked', 'true');
        results.push(`GDPR role=checkbox clicked`);
      }
      const nativeGdpr = document.querySelector('input[name="gdpr"]');
      if (nativeGdpr) {
        nativeGdpr.checked = true;
        nativeGdpr.dispatchEvent(new Event('change', { bubbles: true }));
        results.push('GDPR native checked');
      }

      return results;
    }, { cl: coverLetterText });

    console.log('Batch fill results:', fillResults);
    await page.waitForTimeout(1000);

    // Close all modals that may have opened
    await closeAllModals();
    console.log('Modals cleared');

    // Upload resume (must be done via file input, not JS)
    const fileInputs = await page.locator('input[type="file"]').all();
    console.log(`File inputs found: ${fileInputs.length}`);
    if (fileInputs.length >= 2) {
      await fileInputs[1].setInputFiles(resumePath);
      console.log('Resume uploaded to second file input (resume)');
    } else if (fileInputs.length === 1) {
      await fileInputs[0].setInputFiles(resumePath);
      console.log('Resume uploaded');
    }
    await page.waitForTimeout(3000);

    // Close modals again after file upload
    await closeAllModals();

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-02-fields-filled.png'), fullPage: true });

    // Verify form state
    const formCheck = await page.evaluate(() => {
      const get = sel => {
        const el = document.querySelector(sel);
        return el ? el.value || el.checked : 'NOT FOUND';
      };
      const gdprEl = document.querySelector('[data-ui="gdpr"] [role="checkbox"]');
      const nativeGdpr = document.querySelector('input[name="gdpr"]');
      return {
        firstname: get('input[name="firstname"]'),
        lastname: get('input[name="lastname"]'),
        email: get('input[type="email"]'),
        phone: get('input[type="tel"]'),
        address: get('input[name="address"]'),
        noticePeriod: get('input[name="CA_21813"]'),
        salary: get('input[name="CA_21815"]'),
        rightToWorkYes: document.querySelector('input[name="CA_21816"][value="true"]')?.checked,
        qa1: get('textarea[name="QA_11807072"]'),
        qa2Length: document.querySelector('textarea[name="QA_11807073"]')?.value?.length,
        coverLetterLength: document.querySelector('textarea[name="cover_letter"]')?.value?.length,
        resumeUploaded: document.querySelector('input[type="file"][id*="resume"]')?.files?.length > 0 ||
          document.body.innerText.includes('Hisham Abboud CV.pdf'),
        gdprAriaChecked: gdprEl?.getAttribute('aria-checked'),
        gdprNativeChecked: nativeGdpr?.checked,
        hasModal: !!document.querySelector('[data-role="modal-wrapper"]'),
        hasCookieDialog: !!document.querySelector('[data-ui="cookie-consent"]')
      };
    });
    console.log('Form verification:', JSON.stringify(formCheck, null, 2));

    // Full page pre-submit
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-03-pre-submit.png'), fullPage: true });

    // Submit via JS click to bypass any overlays
    const submitResult = await page.evaluate(() => {
      const btn = document.querySelector('button[type="submit"]');
      if (!btn) return 'SUBMIT BUTTON NOT FOUND';
      const isDisabled = btn.disabled || btn.getAttribute('aria-disabled') === 'true';
      btn.click();
      return `Clicked: "${btn.innerText.trim()}", disabled: ${isDisabled}`;
    });
    console.log('Submit result:', submitResult);

    // Wait longer for confirmation page
    await page.waitForTimeout(10000);

    // Final screenshot
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved');
    console.log('Final URL:', page.url());
    console.log('Page title:', await page.title());

    // Check for success
    const finalText = await page.evaluate(() => document.body.innerText.substring(0, 3000));
    console.log('Final page text:\n', finalText);

    const isSuccess = finalText.toLowerCase().includes('thank') ||
      finalText.toLowerCase().includes('success') ||
      finalText.toLowerCase().includes('received') ||
      finalText.toLowerCase().includes('submitted') ||
      page.url().includes('thank') ||
      page.url().includes('success');
    console.log(`\nApplication status: ${isSuccess ? 'SUCCESS - Confirmation detected' : 'UNCERTAIN - Check screenshot'}`);

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
