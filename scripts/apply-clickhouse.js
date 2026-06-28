const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const JOB_URL = 'https://job-boards.greenhouse.io/clickhouse/jobs/5803692004';
const RESUME_PDF = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';

const CANDIDATE = {
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31 06 4841 2838',
  linkedin: 'linkedin.com/in/hisham-abboud',
  github: 'github.com/Hishamabboud',
  location: 'Eindhoven, Netherlands',
};

const COVER_LETTER_TEXT = fs.readFileSync(
  '/home/user/Agents/output/cover-letters/clickhouse-cloud-engineer.md',
  'utf8'
);

async function screenshot(page, name) {
  const filePath = path.join(SCREENSHOTS_DIR, `clickhouse-${name}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  console.log(`Screenshot saved: ${filePath}`);
  return filePath;
}

async function run() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('Navigating to job application page...');
  await page.goto(JOB_URL, { waitUntil: 'networkidle', timeout: 60000 });
  await screenshot(page, '01-job-page-loaded');

  console.log('Page title:', await page.title());

  // Wait for the form to appear
  await page.waitForSelector('form', { timeout: 30000 });
  await screenshot(page, '02-form-visible');

  // --- Fill First Name ---
  const firstNameField = await page.locator('input[name="first_name"], input[id*="first_name"], input[placeholder*="First"]').first();
  if (await firstNameField.count() > 0) {
    await firstNameField.fill(CANDIDATE.firstName);
    console.log('Filled first name');
  } else {
    console.log('WARNING: first name field not found');
  }

  // --- Fill Last Name ---
  const lastNameField = await page.locator('input[name="last_name"], input[id*="last_name"], input[placeholder*="Last"]').first();
  if (await lastNameField.count() > 0) {
    await lastNameField.fill(CANDIDATE.lastName);
    console.log('Filled last name');
  } else {
    console.log('WARNING: last name field not found');
  }

  // --- Fill Email ---
  const emailField = await page.locator('input[name="email"], input[type="email"]').first();
  if (await emailField.count() > 0) {
    await emailField.fill(CANDIDATE.email);
    console.log('Filled email');
  } else {
    console.log('WARNING: email field not found');
  }

  // --- Fill Phone ---
  const phoneField = await page.locator('input[name="phone"], input[type="tel"], input[id*="phone"]').first();
  if (await phoneField.count() > 0) {
    await phoneField.fill(CANDIDATE.phone);
    console.log('Filled phone');
  } else {
    console.log('WARNING: phone field not found');
  }

  await screenshot(page, '03-basic-fields-filled');

  // --- Upload Resume ---
  if (fs.existsSync(RESUME_PDF)) {
    const fileInput = await page.locator('input[type="file"]').first();
    if (await fileInput.count() > 0) {
      await fileInput.setInputFiles(RESUME_PDF);
      console.log('Resume uploaded');
      await page.waitForTimeout(2000);
      await screenshot(page, '04-resume-uploaded');
    } else {
      console.log('WARNING: file input not found for resume');
    }
  } else {
    console.log('WARNING: Resume PDF not found at', RESUME_PDF);
  }

  // --- Fill LinkedIn ---
  const linkedinField = await page.locator('input[name*="linkedin"], input[id*="linkedin"], input[placeholder*="LinkedIn"]').first();
  if (await linkedinField.count() > 0) {
    await linkedinField.fill(`https://${CANDIDATE.linkedin}`);
    console.log('Filled LinkedIn');
  } else {
    console.log('LinkedIn field not found (may be optional)');
  }

  // --- Fill GitHub ---
  const githubField = await page.locator('input[name*="github"], input[id*="github"], input[placeholder*="GitHub"]').first();
  if (await githubField.count() > 0) {
    await githubField.fill(`https://${CANDIDATE.github}`);
    console.log('Filled GitHub');
  } else {
    console.log('GitHub field not found (may be optional)');
  }

  // --- Fill Cover Letter (if text area exists) ---
  const coverLetterArea = await page.locator('textarea[name*="cover"], textarea[id*="cover"], textarea[placeholder*="cover"]').first();
  if (await coverLetterArea.count() > 0) {
    await coverLetterArea.fill(COVER_LETTER_TEXT);
    console.log('Filled cover letter text area');
  } else {
    console.log('Cover letter text area not found (may be file upload only)');
  }

  // --- Fill Location if asked ---
  const locationField = await page.locator('input[name*="location"], input[id*="location"], input[placeholder*="ocation"]').first();
  if (await locationField.count() > 0) {
    await locationField.fill(CANDIDATE.location);
    console.log('Filled location');
  }

  await screenshot(page, '05-all-fields-filled');

  // --- Handle Visa Sponsorship dropdown ---
  // Look for any dropdown asking about visa/work authorization
  const visaSelects = await page.locator('select').all();
  for (const sel of visaSelects) {
    const id = await sel.getAttribute('id') || '';
    const name = await sel.getAttribute('name') || '';
    if (id.toLowerCase().includes('visa') || name.toLowerCase().includes('visa') ||
        id.toLowerCase().includes('sponsor') || name.toLowerCase().includes('sponsor') ||
        id.toLowerCase().includes('auth') || name.toLowerCase().includes('auth')) {
      // Select "No" for sponsorship (candidate is in Netherlands, presumably authorized)
      try {
        await sel.selectOption({ label: 'No' });
        console.log(`Set visa/sponsorship dropdown (${id || name}) to No`);
      } catch (e) {
        console.log('Could not set visa dropdown:', e.message);
      }
    }
  }

  await screenshot(page, '06-before-submit');

  // --- Log all form fields for debugging ---
  const allInputs = await page.locator('input, select, textarea').all();
  console.log(`\nTotal form elements found: ${allInputs.length}`);
  for (const el of allInputs) {
    const tag = await el.evaluate(e => e.tagName);
    const type = await el.getAttribute('type') || '';
    const name = await el.getAttribute('name') || '';
    const id = await el.getAttribute('id') || '';
    const placeholder = await el.getAttribute('placeholder') || '';
    const value = await el.evaluate(e => e.value || '').catch(() => '');
    console.log(`  ${tag} type=${type} name=${name} id=${id} placeholder=${placeholder} value=${value.substring(0, 40)}`);
  }

  // --- Submit ---
  console.log('\nLooking for submit button...');
  const submitBtn = await page.locator('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Apply")').first();
  if (await submitBtn.count() > 0) {
    const btnText = await submitBtn.textContent();
    console.log(`Found submit button: "${btnText}"`);
    await screenshot(page, '07-ready-to-submit');

    console.log('Submitting application...');
    await submitBtn.click();
    await page.waitForTimeout(5000);
    await screenshot(page, '08-after-submit');

    const finalUrl = page.url();
    const finalTitle = await page.title();
    console.log('Final URL:', finalUrl);
    console.log('Final Title:', finalTitle);

    // Check for success
    const pageContent = await page.content();
    const isSuccess = pageContent.toLowerCase().includes('thank you') ||
                      pageContent.toLowerCase().includes('application received') ||
                      pageContent.toLowerCase().includes('successfully') ||
                      finalUrl.includes('confirmation') ||
                      finalUrl.includes('success');

    if (isSuccess) {
      console.log('SUCCESS: Application submitted successfully!');
    } else {
      console.log('UNCERTAIN: Could not confirm submission success. Check screenshot.');
    }

    await screenshot(page, '09-final-state');
  } else {
    console.log('ERROR: Submit button not found!');
    await screenshot(page, '07-no-submit-button');
  }

  await browser.close();
  console.log('Browser closed. Script complete.');
}

run().catch(async (err) => {
  console.error('Script failed:', err.message);
  console.error(err.stack);
  process.exit(1);
});
