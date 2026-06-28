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

  // Wait for any blocking modal/dialog to disappear via Escape
  const waitForNoModal = async (maxWait = 5000) => {
    const start = Date.now();
    while (Date.now() - start < maxWait) {
      const hasModal = await page.evaluate(() => {
        const modal = document.querySelector('[data-role="modal-wrapper"]');
        return modal !== null && modal.querySelector('[data-role="backdrop"]') !== null;
      });
      if (!hasModal) return;
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    }
  };

  try {
    console.log('Navigating to application form...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v4-01-loaded.png'), fullPage: true });

    // Dismiss cookie consent
    const cookieSel = '[data-ui="cookie-consent"]';
    if (await page.locator(cookieSel).isVisible({ timeout: 3000 }).catch(() => false)) {
      // Use the "Accept all" button
      const acceptAll = page.locator('button:has-text("Accept all")').first();
      if (await acceptAll.isVisible({ timeout: 1000 }).catch(() => false)) {
        await acceptAll.click({ force: true });
      } else {
        await page.locator(`${cookieSel} button`).first().click({ force: true });
      }
      await page.waitForTimeout(1500);
      await waitForNoModal();
    }

    // Wait for form
    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    console.log('Form ready');

    // Use page.fill() for text fields - this properly handles React
    // page.fill() first focuses and clears the field, then types value

    await page.fill('input[name="firstname"]', 'Hisham');
    await page.waitForTimeout(200);
    console.log('First name:', await page.locator('input[name="firstname"]').inputValue());

    await page.fill('input[name="lastname"]', 'Abboud');
    await page.waitForTimeout(200);
    console.log('Last name:', await page.locator('input[name="lastname"]').inputValue());

    await page.fill('input[type="email"]', 'hiaham123@hotmail.com');
    await page.waitForTimeout(200);
    console.log('Email:', await page.locator('input[type="email"]').inputValue());

    // Phone - the phone input causes a country picker modal.
    // Focus via JS to avoid triggering the country picker button click
    await page.evaluate(() => {
      const phoneEl = document.querySelector('input[type="tel"]');
      if (phoneEl) phoneEl.focus();
    });
    await page.waitForTimeout(100);
    // Check if modal appeared
    await waitForNoModal(2000);
    // Fill directly
    await page.fill('input[type="tel"]', '+31064841 2838');
    await page.waitForTimeout(300);
    await waitForNoModal(3000);
    console.log('Phone:', await page.locator('input[type="tel"]').first().inputValue());

    // Address - fill normally, then close any autocomplete modal
    await page.fill('input[name="address"]', 'Eindhoven, Netherlands');
    await page.waitForTimeout(500);
    await waitForNoModal(3000);
    // Press Escape to close any autocomplete dropdown
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    console.log('Address:', await page.locator('input[name="address"]').inputValue());

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v4-02-personal.png'), fullPage: true });

    // Resume upload
    const fileInputs = await page.locator('input[type="file"]').all();
    console.log(`File inputs found: ${fileInputs.length}`);
    if (fileInputs.length >= 2) {
      await fileInputs[1].setInputFiles(resumePath);
      console.log('Resume uploaded to resume input (index 1)');
    } else {
      await fileInputs[0].setInputFiles(resumePath);
    }
    await page.waitForTimeout(3000);
    await waitForNoModal(3000);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v4-03-resume.png'), fullPage: true });

    // Cover letter
    await page.fill('textarea[name="cover_letter"]', coverLetterText);
    await page.waitForTimeout(300);
    console.log('Cover letter length:', await page.locator('textarea[name="cover_letter"]').inputValue().then(v => v.length));

    // Notice period
    await page.fill('input[name="CA_21813"]', '1 month');
    await page.waitForTimeout(200);
    console.log('Notice period:', await page.locator('input[name="CA_21813"]').inputValue());

    // Expected Salary
    await page.fill('input[name="CA_21815"]', '65000');
    await page.waitForTimeout(200);
    console.log('Expected salary:', await page.locator('input[name="CA_21815"]').inputValue());

    // Right to work - YES radio
    // The label has aria-hidden radio inside, we click the label
    // Use a more targeted approach
    const yesLabel = page.locator('label').filter({ hasText: /^YES$/ }).first();
    if (await yesLabel.count() > 0) {
      await yesLabel.click({ force: true });
      console.log('Clicked YES label for right to work');
    }
    await page.waitForTimeout(300);
    await waitForNoModal(2000);
    const yesChecked = await page.locator('input[name="CA_21816"][value="true"]').isChecked();
    console.log('YES radio checked:', yesChecked);

    // QA fields
    await page.fill('textarea[name="QA_11807072"]', 'Yes, I currently reside in Eindhoven, Netherlands.');
    await page.waitForTimeout(200);
    console.log('QA1:', await page.locator('textarea[name="QA_11807072"]').inputValue());

    await page.fill('textarea[name="QA_11807073"]', 'Yes, I can commute to the office in Huis ter Heide, Utrecht. The journey from Eindhoven is approximately 60 minutes by public transport, which I am comfortable doing.');
    await page.waitForTimeout(200);
    console.log('QA2 length:', await page.locator('textarea[name="QA_11807073"]').inputValue().then(v => v.length));

    // GDPR checkbox
    // The GDPR uses a custom checkbox with role="checkbox"
    const gdprRoleCheckbox = page.locator('[data-ui="gdpr"] [role="checkbox"]').first();
    if (await gdprRoleCheckbox.count() > 0) {
      const ariaChecked = await gdprRoleCheckbox.getAttribute('aria-checked');
      console.log('GDPR current aria-checked:', ariaChecked);
      if (ariaChecked !== 'true') {
        await gdprRoleCheckbox.click({ force: true });
        await page.waitForTimeout(300);
        console.log('GDPR clicked, new state:', await gdprRoleCheckbox.getAttribute('aria-checked'));
      }
    }
    await waitForNoModal(2000);

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v4-04-all-fields.png'), fullPage: true });

    // Scroll down to verify bottom of form
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v4-05-bottom.png'), fullPage: false });

    // Final verification
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
        qa1: g('textarea[name="QA_11807072"]')?.value?.substring(0, 40),
        qa2len: g('textarea[name="QA_11807073"]')?.value?.length,
        coverLen: g('textarea[name="cover_letter"]')?.value?.length,
        gdprAriaChecked: g('[data-ui="gdpr"] [role="checkbox"]')?.getAttribute('aria-checked'),
        gdprNative: g('input[name="gdpr"]')?.checked,
        resumeInPage: document.body.innerText.includes('Hisham Abboud CV.pdf'),
        hasModal: !!g('[data-role="modal-wrapper"]')
      };
    });
    console.log('Final verification:', JSON.stringify(verify, null, 2));

    // Pre-submit screenshot
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v4-06-pre-submit.png'), fullPage: true });

    // Watch for successful navigation
    page.once('load', () => console.log('Page load event fired!'));

    // Submit using JS to bypass any remaining overlay issues
    console.log('Submitting application...');
    await page.evaluate(() => {
      const btn = document.querySelector('button[type="submit"]');
      if (btn) {
        console.log('Clicking submit:', btn.innerText);
        btn.click();
      }
    });

    // Wait for network activity to settle and potential URL change
    try {
      await Promise.race([
        page.waitForURL(url => url !== 'https://apply.workable.com/deployteq/j/5246F389F7/apply/', { timeout: 15000 }),
        page.waitForSelector('[data-ui="success"], .success, [class*="confirmation"], [class*="thank"]', { timeout: 15000 })
      ]);
      console.log('Success indicator detected!');
    } catch (e) {
      console.log('No success indicator detected within 15s, checking current state...');
    }

    await page.waitForTimeout(5000);

    // Final screenshot
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved');
    console.log('URL:', page.url());

    const finalText = await page.evaluate(() => document.body.innerText.substring(0, 2000));
    console.log('Page text:\n', finalText);

    // Check for validation errors in DOM
    const validationErrors = await page.evaluate(() => {
      const errors = [];
      document.querySelectorAll('[class*="error"], [aria-invalid="true"], [class*="invalid"]').forEach(el => {
        if (el.innerText) errors.push(el.innerText.trim().substring(0, 100));
      });
      return errors.filter(e => e.length > 0);
    });
    if (validationErrors.length > 0) {
      console.log('Validation errors:', validationErrors);
    }

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v4-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
