const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const proxyEnv = process.env.https_proxy || process.env.HTTPS_PROXY || '';
let proxyOpts;
if (proxyEnv) {
  const match = proxyEnv.match(/^http:\/\/([^:]+):([^@]+)@(.+)/);
  if (match) proxyOpts = { server: 'http://' + match[3], username: match[1], password: match[2] };
}

const screenshotDir = '/home/user/Agents/output/screenshots';
const JOB_URL = 'https://careers.keylane.com/jobs/junior-technical-application-engineer-plexus/';
const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';

const motivation = `Dear Keylane Hiring Team,

I am writing to apply for the Junior Technical Application Engineer - Plexus position at Keylane. As a Software Service Engineer at Actemium (VINCI Energies), I have hands-on experience maintaining and supporting enterprise software applications in production environments - experience that maps directly to this role.

In my current position I:
- Monitor and troubleshoot applications in production, resolving incidents related to performance, availability, and integrations
- Manage IIS-hosted .NET applications and configure REST API endpoints and webservices
- Work with SQL Server databases for support queries and optimizations
- Apply security patches and updates to Windows Server environments following change management procedures

I also bring experience with Azure DevOps for CI/CD pipelines and a solid foundation in ITIL-aligned incident and change management processes.

I am attracted to Keylane because of its position as the leading European SaaS platform for the insurance and pension industry and the opportunity to grow within a structured Technical Application Management team. My BSc in Software Engineering from Fontys University of Applied Sciences (Eindhoven, 2024) gives me a strong technical foundation, and I am eager to apply it in a domain-focused role.

I am fluent in English and Dutch, am willing to travel to Utrecht, and am available to start within short notice.

I look forward to the opportunity to contribute to the Keylane Plexus team.

Kind regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com`;

(async () => {
  console.log('=== Keylane Junior Technical Application Engineer - Plexus ===');
  console.log('Starting application...\n');

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    proxy: proxyOpts
  });

  const ctx = await browser.newContext({
    ignoreHTTPSErrors: true,
    locale: 'en-US',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });

  const page = await ctx.newPage();

  // Step 1: Navigate to job page
  console.log('Step 1: Navigating to job page...');
  await page.goto(JOB_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  console.log('  URL:', page.url());
  console.log('  Title:', await page.title());

  // Accept cookies
  const cookieBtn = await page.$('button:has-text("Accept All")');
  if (cookieBtn) {
    await cookieBtn.click();
    await page.waitForTimeout(1000);
    console.log('  Accepted cookies');
  }

  await page.screenshot({ path: path.join(screenshotDir, 'keylane-01-job-page.png'), fullPage: false });
  console.log('  Screenshot saved: keylane-01-job-page.png');

  // Step 2: Scroll to and click Apply button
  console.log('\nStep 2: Scrolling to Apply now button...');
  const applyBtn = await page.$('a:has-text("Apply now"), a[href="#apply-now"]');
  if (!applyBtn) {
    console.log('  ERROR: Apply button not found!');
    await browser.close();
    process.exit(1);
  }

  await applyBtn.scrollIntoViewIfNeeded();
  await page.waitForTimeout(500);
  await applyBtn.click();
  await page.waitForTimeout(2000);

  // Scroll to the gform
  await page.evaluate(() => {
    const el = document.querySelector('#gform_3, #apply-now, .gform_wrapper');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  await page.waitForTimeout(1500);

  await page.screenshot({ path: path.join(screenshotDir, 'keylane-02-form-visible.png'), fullPage: false });
  console.log('  Screenshot saved: keylane-02-form-visible.png');

  // Step 3: Fill in the form
  console.log('\nStep 3: Filling in the application form...');

  // First name
  const firstNameInput = await page.$('#input_3_33_3');
  if (firstNameInput) {
    await firstNameInput.click({ clickCount: 3 });
    await firstNameInput.fill('Hisham');
    console.log('  First name filled');
  } else {
    console.log('  WARNING: First name field not found');
  }

  // Last name
  const lastNameInput = await page.$('#input_3_33_6');
  if (lastNameInput) {
    await lastNameInput.click({ clickCount: 3 });
    await lastNameInput.fill('Abboud');
    console.log('  Last name filled');
  } else {
    console.log('  WARNING: Last name field not found');
  }

  // Email
  const emailInput = await page.$('#input_3_2');
  if (emailInput) {
    await emailInput.click({ clickCount: 3 });
    await emailInput.fill('hiaham123@hotmail.com');
    console.log('  Email filled');
  } else {
    console.log('  WARNING: Email field not found');
  }

  // Phone
  const phoneInput = await page.$('#input_3_10');
  if (phoneInput) {
    await phoneInput.click({ clickCount: 3 });
    await phoneInput.fill('+31 06 4841 2838');
    console.log('  Phone filled');
  } else {
    console.log('  WARNING: Phone field not found');
  }

  // Motivation / cover letter
  const motivationInput = await page.$('#input_3_12');
  if (motivationInput) {
    await motivationInput.click({ clickCount: 3 });
    await motivationInput.fill(motivation);
    console.log('  Motivation letter filled');
  } else {
    console.log('  WARNING: Motivation field not found');
  }

  // Upload resume
  const fileInput = await page.$('#input_3_13');
  if (fileInput) {
    await fileInput.setInputFiles(RESUME_PATH);
    await page.waitForTimeout(2000);
    console.log('  Resume uploaded:', RESUME_PATH);
  } else {
    console.log('  WARNING: File upload field not found');
  }

  // Consent checkbox - use JavaScript to check it since it may be visually hidden
  const consentChecked = await page.evaluate(() => {
    const checkbox = document.querySelector('#input_3_22_1');
    if (checkbox) {
      if (!checkbox.checked) {
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
      }
      return checkbox.checked;
    }
    return null;
  });
  if (consentChecked !== null) {
    console.log('  Consent checkbox set to checked via JS:', consentChecked);
  } else {
    console.log('  NOTE: No consent checkbox found');
  }

  await page.waitForTimeout(1000);

  // Scroll to see the submit button
  await page.evaluate(() => {
    const btn = document.getElementById('gform_submit_button_3');
    if (btn) btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  await page.waitForTimeout(1500);

  await page.screenshot({ path: path.join(screenshotDir, 'keylane-03-form-filled.png'), fullPage: false });
  console.log('  Screenshot saved: keylane-03-form-filled.png');

  // Check for CAPTCHA
  const pageContent = await page.content();
  if (pageContent.includes('captcha') || pageContent.includes('recaptcha') || pageContent.includes('hcaptcha') || pageContent.includes('cf-turnstile')) {
    console.log('\n  CAPTCHA detected! Marking as failed.');
    await browser.close();
    console.log('\nResult: failed - CAPTCHA');
    process.exit(2);
  }

  // Step 4: Pre-submit screenshot
  console.log('\nStep 4: Pre-submit state...');
  await page.screenshot({ path: path.join(screenshotDir, 'keylane-04-pre-submit.png'), fullPage: false });
  console.log('  Screenshot saved: keylane-04-pre-submit.png (PRE-SUBMIT)');

  // Step 5: Submit - target the Gravity Forms submit button specifically by ID
  console.log('\nStep 5: Submitting application...');
  const submitBtn = await page.$('#gform_submit_button_3, .gform_button');
  if (!submitBtn) {
    console.log('  ERROR: Gravity Forms submit button #gform_submit_button_3 not found!');
    await browser.close();
    process.exit(1);
  }

  const submitText = await submitBtn.textContent().catch(() => 'submit');
  console.log('  Submit button found, text:', submitText.trim());

  await submitBtn.click();
  console.log('  Clicked submit!');
  await page.waitForTimeout(6000);

  const finalUrl = page.url();
  const finalTitle = await page.title();
  const finalText = await page.evaluate(() => document.body.innerText);

  console.log('\n  Final URL:', finalUrl);
  console.log('  Final title:', finalTitle);
  console.log('  Page text (first 1200):', finalText.substring(0, 1200));

  await page.screenshot({ path: path.join(screenshotDir, 'keylane-05-confirmation.png'), fullPage: true });
  console.log('\n  Screenshot saved: keylane-05-confirmation.png (POST-SUBMIT)');

  const successKeywords = ['thank you', 'thank-you', 'dank', 'received', 'submitted', 'success', 'confirmation', 'ontvangen', 'bedankt'];
  const isSuccess = successKeywords.some(k =>
    finalText.toLowerCase().includes(k) ||
    finalTitle.toLowerCase().includes(k) ||
    finalUrl.toLowerCase().includes(k)
  );

  console.log('\n=== APPLICATION RESULT:', isSuccess ? 'SUCCESS' : 'UNCERTAIN - check screenshots', '===');

  await browser.close();
  process.exit(isSuccess ? 0 : 3);
})().catch(async err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
