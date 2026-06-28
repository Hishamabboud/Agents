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

  // Helper: set React-controlled input value
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
      return `Set: ${el.name || el.id || sel} = ${val.substring(0, 30)}`;
    }, { sel: selector, val: value });
  };

  // Helper: dismiss any open modal
  const dismissModal = async () => {
    const hasModal = await page.evaluate(() => {
      const modal = document.querySelector('[data-role="modal-wrapper"]');
      return modal !== null;
    });
    if (hasModal) {
      console.log('Modal detected, dismissing...');
      await page.keyboard.press('Escape');
      await page.waitForTimeout(800);
      // Also try clicking the backdrop
      await page.evaluate(() => {
        const backdrop = document.querySelector('[data-role="backdrop"]');
        if (backdrop) backdrop.click();
      });
      await page.waitForTimeout(500);
    }
  };

  try {
    console.log('Navigating directly to application form...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-01-initial-load.png'), fullPage: true });
    console.log('Page loaded. URL:', page.url());

    // Dismiss cookie consent
    const cookieDialog = page.locator('[data-ui="cookie-consent"]');
    if (await cookieDialog.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('Dismissing cookie consent...');
      await page.locator('[data-ui="cookie-consent"] button').first().click({ force: true });
      await page.waitForTimeout(1500);
    }

    // Wait for form
    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    await page.waitForTimeout(1000);
    console.log('Form loaded');

    // --- PERSONAL INFORMATION via page.fill (safe - doesn't trigger modals) ---
    await page.fill('input[name="firstname"]', 'Hisham');
    console.log('First name filled');

    await page.fill('input[name="lastname"]', 'Abboud');
    console.log('Last name filled');

    await page.fill('input[type="email"]', 'hiaham123@hotmail.com');
    console.log('Email filled');

    // Phone - use JS to avoid triggering country code modal
    let result = await jsSetInput('input[type="tel"]', '+31064841 2838');
    console.log('Phone:', result);

    // Dismiss any modal that may have opened
    await dismissModal();

    // Address - use JS to avoid autocomplete modal
    result = await jsSetInput('input[name="address"]', 'Eindhoven, Netherlands');
    console.log('Address:', result);

    await dismissModal();

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-02-personal-info.png'), fullPage: true });

    // --- RESUME UPLOAD ---
    console.log('Uploading resume...');
    const fileInputs = await page.locator('input[type="file"]').all();
    console.log(`Total file inputs: ${fileInputs.length}`);
    if (fileInputs.length >= 2) {
      await fileInputs[1].setInputFiles(resumePath);
      console.log('Resume uploaded to second file input (resume field)');
    } else if (fileInputs.length >= 1) {
      await fileInputs[0].setInputFiles(resumePath);
      console.log('Resume uploaded to first file input');
    }
    await page.waitForTimeout(3000);
    await dismissModal();
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-03-after-upload.png'), fullPage: true });

    // --- COVER LETTER ---
    result = await jsSetInput('textarea[name="cover_letter"]', coverLetterText);
    console.log('Cover letter:', result);
    await dismissModal();

    // --- REQUIRED CUSTOM FIELDS ---

    // Notice period (CA_21813)
    result = await jsSetInput('input[name="CA_21813"]', '1 month');
    console.log('Notice period:', result);

    // Expected Salary (CA_21815)
    result = await jsSetInput('input[name="CA_21815"]', '65000');
    console.log('Expected salary:', result);

    // Right to work (CA_21816) - click the YES label using JavaScript
    const radioResult = await page.evaluate(() => {
      // Find the label that contains the YES radio (value="true")
      const yesRadio = document.querySelector('input[name="CA_21816"][value="true"]');
      if (!yesRadio) return 'YES radio not found';
      const label = yesRadio.closest('label');
      if (!label) return 'Label not found';
      label.click();
      // Also directly set the radio as checked
      yesRadio.checked = true;
      yesRadio.dispatchEvent(new Event('change', { bubbles: true }));
      yesRadio.dispatchEvent(new Event('click', { bubbles: true }));
      return `Clicked label, radio checked: ${yesRadio.checked}, label text: ${label.innerText.trim()}`;
    });
    console.log('Right to work:', radioResult);
    await page.waitForTimeout(500);
    await dismissModal();

    // QA_11807072 - "Are you live and reside in the Netherlands?"
    result = await jsSetInput('textarea[name="QA_11807072"]', 'Yes, I currently reside in Eindhoven, Netherlands.');
    console.log('QA_11807072:', result);

    // QA_11807073 - "Can you commute to our Office in Huis ter Heide, Utrecht?"
    result = await jsSetInput('textarea[name="QA_11807073"]', 'Yes, I can commute to the office in Huis ter Heide, Utrecht. The journey from Eindhoven is approximately 60 minutes by public transport, which I am comfortable doing.');
    console.log('QA_11807073:', result);

    // GDPR - click via JavaScript
    const gdprResult = await page.evaluate(() => {
      // Try clicking the custom checkbox
      const gdprLabel = document.querySelector('[data-ui="gdpr"]');
      const roleCheckbox = document.querySelector('[data-ui="gdpr"] [role="checkbox"]');
      const nativeCheckbox = document.querySelector('input[name="gdpr"]');

      let results = [];
      if (roleCheckbox) {
        roleCheckbox.click();
        results.push(`role=checkbox clicked, aria-checked: ${roleCheckbox.getAttribute('aria-checked')}`);
      }
      if (gdprLabel) {
        results.push(`gdpr data-checked: ${gdprLabel.getAttribute('data-checked')}`);
      }
      if (nativeCheckbox) {
        nativeCheckbox.checked = true;
        nativeCheckbox.dispatchEvent(new Event('change', { bubbles: true }));
        results.push(`native checkbox checked: ${nativeCheckbox.checked}`);
      }
      return results.join(' | ');
    });
    console.log('GDPR:', gdprResult);
    await page.waitForTimeout(500);
    await dismissModal();

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-04-all-fields.png'), fullPage: true });

    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-05-form-bottom.png'), fullPage: false });

    // Final form state check
    const formState = await page.evaluate(() => {
      const fields = Array.from(document.querySelectorAll('input, textarea')).map(el => ({
        name: el.name || '',
        type: el.type || '',
        value: el.value ? (el.value.length > 80 ? el.value.substring(0, 80) + '...' : el.value) : '',
        checked: (el.type === 'checkbox' || el.type === 'radio') ? el.checked : undefined
      })).filter(f => f.name); // only named fields
      const gdpr = document.querySelector('[data-ui="gdpr"]');
      const gdprRoleChk = document.querySelector('[data-ui="gdpr"] [role="checkbox"]');
      return {
        fields,
        gdprDataChecked: gdpr ? gdpr.getAttribute('data-checked') : null,
        gdprAriaChecked: gdprRoleChk ? gdprRoleChk.getAttribute('aria-checked') : null,
        hasModal: !!document.querySelector('[data-role="modal-wrapper"]')
      };
    });
    console.log('Form state:', JSON.stringify(formState, null, 2));

    // Pre-submit screenshot
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-06-pre-submit.png'), fullPage: true });

    // Submit using JavaScript to bypass modal if still present
    console.log('Submitting form...');
    const submitResult = await page.evaluate(() => {
      const btn = document.querySelector('button[type="submit"]');
      if (!btn) return 'Submit button not found';
      btn.click();
      return `Submit button clicked: "${btn.innerText.trim()}"`;
    });
    console.log('Submit result:', submitResult);

    // Wait for response
    await page.waitForTimeout(8000);

    // Final screenshot
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved');
    console.log('Final URL:', page.url());
    console.log('Page title:', await page.title());

    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 3000));
    console.log('Final page content:\n', bodyText);

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
