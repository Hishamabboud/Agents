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

  // Fill a field by clicking it and using keyboard (ensures React detects the input)
  const fillViaKeyboard = async (selector, value) => {
    const el = page.locator(selector).first();
    await el.scrollIntoViewIfNeeded();
    await el.click({ force: true });
    await page.waitForTimeout(100);
    // Select all and delete existing content
    await page.keyboard.press('Control+a');
    await page.keyboard.press('Delete');
    await page.waitForTimeout(50);
    // Type the value
    await page.keyboard.type(value, { delay: 10 });
    await page.keyboard.press('Tab');
    await page.waitForTimeout(200);
  };

  // Dismiss modals by pressing Escape and removing via JS
  const clearModals = async () => {
    // Press Escape multiple times
    for (let i = 0; i < 3; i++) {
      await page.keyboard.press('Escape');
      await page.waitForTimeout(200);
    }
    // Also remove via JS
    await page.evaluate(() => {
      document.querySelectorAll('[data-role="modal-wrapper"], [data-role="backdrop"]').forEach(el => el.remove());
    });
    await page.waitForTimeout(200);
  };

  try {
    console.log('Navigating to application form...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);

    // Dismiss cookie consent
    const cookieSel = '[data-ui="cookie-consent"]';
    if (await page.locator(cookieSel).isVisible({ timeout: 3000 }).catch(() => false)) {
      await page.locator(`${cookieSel} button`).first().click({ force: true });
      await page.waitForTimeout(1000);
    }
    // Also try to accept all cookies if present again
    const acceptAllBtn = page.locator('button:has-text("Accept all")').first();
    if (await acceptAllBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await acceptAllBtn.click({ force: true });
      await page.waitForTimeout(1000);
    }

    // Wait for form
    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    await page.waitForTimeout(500);
    console.log('Form ready');

    // Fill First name
    await fillViaKeyboard('input[name="firstname"]', 'Hisham');
    await clearModals();
    console.log('First name filled');

    // Fill Last name
    await fillViaKeyboard('input[name="lastname"]', 'Abboud');
    await clearModals();
    console.log('Last name filled');

    // Fill Email
    await fillViaKeyboard('input[type="email"]', 'hiaham123@hotmail.com');
    await clearModals();
    console.log('Email filled');

    // Fill Phone - click outside the flag button area (click the text part of the phone input)
    const phoneInput = page.locator('input[type="tel"]').first();
    await phoneInput.scrollIntoViewIfNeeded();
    // Use Tab to focus it without clicking the flag
    await page.evaluate(() => {
      const phoneEl = document.querySelector('input[type="tel"]');
      if (phoneEl) phoneEl.focus();
    });
    await page.waitForTimeout(100);
    await page.keyboard.press('Control+a');
    await page.keyboard.press('Delete');
    await page.keyboard.type('+31064841 2838', { delay: 10 });
    await page.keyboard.press('Tab');
    await page.waitForTimeout(300);
    await clearModals();
    console.log('Phone filled');

    // Address - use JS focus to avoid dropdown
    await page.evaluate(() => {
      const el = document.querySelector('input[name="address"]');
      if (el) el.focus();
    });
    await page.waitForTimeout(100);
    await page.keyboard.press('Control+a');
    await page.keyboard.press('Delete');
    await page.keyboard.type('Eindhoven, Netherlands', { delay: 10 });
    await page.keyboard.press('Tab');
    await page.waitForTimeout(500);
    await clearModals();
    console.log('Address filled');

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v3-01-personal.png'), fullPage: true });

    // Upload resume (file upload doesn't trigger modals)
    const fileInputs = await page.locator('input[type="file"]').all();
    console.log(`File inputs: ${fileInputs.length}`);
    if (fileInputs.length >= 2) {
      await fileInputs[1].setInputFiles(resumePath);
      console.log('Resume uploaded');
    } else if (fileInputs.length === 1) {
      await fileInputs[0].setInputFiles(resumePath);
      console.log('Resume uploaded (first input)');
    }
    await page.waitForTimeout(3000);
    await clearModals();
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v3-02-after-upload.png'), fullPage: true });

    // Cover letter
    await fillViaKeyboard('textarea[name="cover_letter"]', coverLetterText);
    await clearModals();
    console.log('Cover letter filled');

    // Notice period
    await fillViaKeyboard('input[name="CA_21813"]', '1 month');
    await clearModals();
    console.log('Notice period filled');

    // Expected Salary
    await fillViaKeyboard('input[name="CA_21815"]', '65000');
    await clearModals();
    console.log('Expected salary filled');

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v3-03-details.png'), fullPage: true });

    // Right to work - click YES label
    await page.evaluate(() => {
      const labels = document.querySelectorAll('label');
      for (const label of labels) {
        if (label.innerText.trim() === 'YES') {
          label.click();
          break;
        }
      }
    });
    await page.waitForTimeout(500);
    await clearModals();
    console.log('Right to work YES clicked');

    // QA fields
    await fillViaKeyboard('textarea[name="QA_11807072"]', 'Yes, I currently reside in Eindhoven, Netherlands.');
    await clearModals();
    console.log('QA1 filled');

    await fillViaKeyboard('textarea[name="QA_11807073"]', 'Yes, I can commute to the office in Huis ter Heide, Utrecht. The journey from Eindhoven is approximately 60 minutes by public transport, which I am comfortable doing.');
    await clearModals();
    console.log('QA2 filled');

    // GDPR - click via label text
    await page.evaluate(() => {
      // Find the GDPR checkbox container and click it
      const gdprContainer = document.querySelector('[data-ui="gdpr"]');
      if (gdprContainer) {
        const roleChk = gdprContainer.querySelector('[role="checkbox"]');
        if (roleChk) roleChk.click();
      }
      // Also try the native input
      const nativeGdpr = document.querySelector('input[name="gdpr"]');
      if (nativeGdpr && !nativeGdpr.checked) {
        nativeGdpr.click();
      }
    });
    await page.waitForTimeout(500);
    await clearModals();
    console.log('GDPR clicked');

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v3-04-all-filled.png'), fullPage: true });

    // Scroll to bottom to verify
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v3-05-bottom.png'), fullPage: false });

    // Verify all fields
    const verify = await page.evaluate(() => {
      const g = (sel) => document.querySelector(sel);
      const gdprRole = g('[data-ui="gdpr"] [role="checkbox"]');
      return {
        firstname: g('input[name="firstname"]')?.value,
        lastname: g('input[name="lastname"]')?.value,
        email: g('input[type="email"]')?.value,
        phone: g('input[type="tel"]')?.value,
        address: g('input[name="address"]')?.value,
        noticePeriod: g('input[name="CA_21813"]')?.value,
        salary: g('input[name="CA_21815"]')?.value,
        yesRadioChecked: g('input[name="CA_21816"][value="true"]')?.checked,
        qa1: g('textarea[name="QA_11807072"]')?.value?.substring(0, 30),
        qa2len: g('textarea[name="QA_11807073"]')?.value?.length,
        coverLetterLen: g('textarea[name="cover_letter"]')?.value?.length,
        gdprAriaChecked: gdprRole?.getAttribute('aria-checked'),
        gdprNativeChecked: g('input[name="gdpr"]')?.checked,
        resumeFilename: document.body.innerText.includes('Hisham Abboud CV.pdf'),
        hasBlockingModal: !!g('[data-role="modal-wrapper"]')
      };
    });
    console.log('Verification:', JSON.stringify(verify, null, 2));

    // Pre-submit full page screenshot
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v3-06-pre-submit.png'), fullPage: true });

    // Listen for network responses to detect success
    let submissionResponse = null;
    page.on('response', async (response) => {
      if (response.url().includes('apply') || response.url().includes('workable')) {
        const status = response.status();
        if (status === 200 || status === 201 || status === 302) {
          console.log(`Network response: ${status} ${response.url()}`);
        }
      }
    });

    // Submit using JS to ensure no overlay blocks it
    console.log('Submitting...');
    const submitInfo = await page.evaluate(() => {
      const btn = document.querySelector('button[type="submit"]');
      if (!btn) return { error: 'No submit button' };
      const info = {
        text: btn.innerText.trim(),
        disabled: btn.disabled,
        type: btn.type
      };
      btn.click();
      return info;
    });
    console.log('Submit button info:', submitInfo);

    // Wait for page change or confirmation
    try {
      await page.waitForURL(url => !url.includes('/apply/') || url.includes('thank'), { timeout: 15000 });
      console.log('URL changed to:', page.url());
    } catch (e) {
      console.log('URL did not change within 15s, checking page content...');
    }

    await page.waitForTimeout(5000);

    // Final screenshot
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved to deployteq-software-developer-after-submit.png');
    console.log('Final URL:', page.url());

    const finalText = await page.evaluate(() => document.body.innerText.substring(0, 2000));
    console.log('Final page text:\n', finalText);

    // Check for errors
    const errors = await page.evaluate(() => {
      const errorEls = document.querySelectorAll('[class*="error"], [class*="alert"], [role="alert"]');
      return Array.from(errorEls).map(el => el.innerText.trim()).filter(t => t.length > 0);
    });
    if (errors.length > 0) {
      console.log('ERRORS DETECTED:', errors);
    }

    const isSuccess = finalText.toLowerCase().includes('thank') ||
      finalText.toLowerCase().includes('application received') ||
      finalText.toLowerCase().includes('successfully') ||
      page.url().includes('thank');
    console.log(`\nResult: ${isSuccess ? 'SUCCESS' : 'CHECK SCREENSHOT - May need verification'}`);

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v3-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
