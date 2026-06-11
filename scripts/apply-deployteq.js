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
    console.log('Navigating directly to application form...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-01-initial-load.png'), fullPage: true });
    console.log('Page loaded. URL:', page.url());

    // Dismiss cookie consent
    const cookieDialog = page.locator('[data-ui="cookie-consent"], [aria-label="Cookie Consent"]');
    const cookieVisible = await cookieDialog.isVisible({ timeout: 3000 }).catch(() => false);
    if (cookieVisible) {
      console.log('Cookie consent dialog found, dismissing...');
      for (const btnText of ['Accept all', 'Accept', 'OK', 'Got it', 'Agree', 'Decline']) {
        const btn = page.locator(`[data-ui="cookie-consent"] button:has-text("${btnText}")`).first();
        if (await btn.isVisible({ timeout: 500 }).catch(() => false)) {
          await btn.click({ force: true });
          console.log(`Clicked cookie button: ${btnText}`);
          await page.waitForTimeout(1500);
          break;
        }
      }
    }

    // Wait for form fields to appear
    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    await page.waitForTimeout(1000);
    console.log('Form loaded');

    // --- PERSONAL INFORMATION ---
    // First name
    await page.fill('input[name="firstname"]', 'Hisham');
    console.log('First name filled');

    // Last name
    await page.fill('input[name="lastname"]', 'Abboud');
    console.log('Last name filled');

    // Email
    await page.fill('input[type="email"]', 'hiaham123@hotmail.com');
    console.log('Email filled');

    // Phone - Workable has a phone flag selector + input
    const phoneInput = page.locator('input[type="tel"]').first();
    await phoneInput.fill('+31064841 2838');
    console.log('Phone filled');

    // Address - clear incorrect auto-fill and set properly
    const addressInput = page.locator('input[name="address"]').first();
    await addressInput.triple_click_and_fill_workaround: ;
    // Use triple click to select all then type
    await addressInput.click({ clickCount: 3 });
    await addressInput.fill('Eindhoven, Netherlands');
    console.log('Address filled');

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-02-personal-info.png'), fullPage: true });

    // --- RESUME UPLOAD ---
    // The resume input has data-ui="resume"
    console.log('Uploading resume to resume field...');
    const resumeInput = page.locator('input[data-ui="resume"], input[id*="resume" i]').first();
    const resumeInputById = page.locator('#input_files_input_kKnbNRvUbXbFNnqJ');
    // Use the correct resume file input (not the avatar one)
    const fileInputs = await page.locator('input[type="file"]').all();
    console.log(`Total file inputs: ${fileInputs.length}`);
    // Second file input is the resume (first is photo/avatar)
    if (fileInputs.length >= 2) {
      await fileInputs[1].setInputFiles(resumePath);
      console.log('Resume uploaded to second file input (resume field)');
    } else if (fileInputs.length === 1) {
      await fileInputs[0].setInputFiles(resumePath);
      console.log('Resume uploaded to only file input');
    }
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-03-after-upload.png'), fullPage: true });

    // --- COVER LETTER ---
    await page.fill('textarea[name="cover_letter"]', coverLetterText);
    console.log('Cover letter filled');

    // --- REQUIRED CUSTOM FIELDS ---
    // Notice period (CA_21813) - text field
    await page.fill('input[name="CA_21813"]', '1 month');
    console.log('Notice period filled');

    // Expected Salary (CA_21815) - text field
    await page.fill('input[name="CA_21815"]', '65000');
    console.log('Expected salary filled');

    // Right to work (CA_21816) - radio, select YES (true)
    const rightToWorkYes = page.locator('input[name="CA_21816"][value="true"]').first();
    if (await rightToWorkYes.isVisible({ timeout: 2000 }).catch(() => false)) {
      await rightToWorkYes.check();
      console.log('Right to work: YES selected');
    } else {
      // Try first radio button (YES)
      await page.locator('input[name="CA_21816"]').first().check();
      console.log('Right to work: first radio selected');
    }

    // QA_11807072 - "Are you live and reside in the Netherlands?"
    const qa1 = page.locator('textarea[name="QA_11807072"]');
    if (await qa1.isVisible({ timeout: 2000 }).catch(() => false)) {
      await qa1.fill('Yes, I currently reside in Eindhoven, Netherlands.');
      console.log('QA_11807072 filled');
    }

    // QA_11807073 - "Can you commute to our Office in Huis ter Heide, Utrecht?"
    const qa2 = page.locator('textarea[name="QA_11807073"]');
    if (await qa2.isVisible({ timeout: 2000 }).catch(() => false)) {
      await qa2.fill('Yes, I can commute to your office in Huis ter Heide, Utrecht. Eindhoven to Huis ter Heide is approximately 60 minutes by public transport.');
      console.log('QA_11807073 filled');
    }

    // GDPR checkbox
    const gdprCheckbox = page.locator('input[name="gdpr"]').first();
    if (await gdprCheckbox.isVisible({ timeout: 2000 }).catch(() => false)) {
      if (!await gdprCheckbox.isChecked()) {
        await gdprCheckbox.check({ force: true });
        console.log('GDPR checkbox checked');
      } else {
        console.log('GDPR already checked');
      }
    }

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-04-all-fields.png'), fullPage: true });

    // Scroll to bottom for final check
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-05-form-bottom.png'), fullPage: false });

    // Log form state
    const formState = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
        tag: el.tagName,
        type: el.type || '',
        name: el.name || '',
        id: el.id || '',
        value: el.value ? (el.value.length > 80 ? el.value.substring(0, 80) + '...' : el.value) : '',
        checked: el.type === 'checkbox' || el.type === 'radio' ? el.checked : undefined
      }));
    });
    console.log('Form state before submit:', JSON.stringify(formState, null, 2));

    // Full page pre-submit screenshot
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-06-pre-submit.png'), fullPage: true });

    // Submit
    console.log('Clicking submit button...');
    const submitBtn = page.locator('button[type="submit"]').first();
    await submitBtn.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await submitBtn.click();
    console.log('Submit clicked');

    await page.waitForTimeout(6000);

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
