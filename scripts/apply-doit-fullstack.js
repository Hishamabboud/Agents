const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const JOB_URL = 'https://job-boards.greenhouse.io/doitintl/jobs/7136305003';

const CANDIDATE = {
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31 06 4841 2838',
  linkedin: 'linkedin.com/in/hisham-abboud',
  github: 'github.com/Hishamabboud',
  city: 'Eindhoven',
  country: 'Netherlands',
  resumePath: path.resolve('/home/user/Agents/profile/Hisham Abboud CV.pdf'),
  coverLetterPath: path.resolve('/home/user/Agents/output/cover-letters/doit-fullstack-engineer.md'),
};

const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';

async function takeScreenshot(page, name) {
  const filePath = path.join(SCREENSHOTS_DIR, `doit-${name}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  console.log(`Screenshot saved: ${filePath}`);
  return filePath;
}

async function safeType(page, selector, value) {
  try {
    const el = await page.waitForSelector(selector, { timeout: 5000 });
    await el.click({ clickCount: 3 });
    await el.type(value, { delay: 30 });
    return true;
  } catch (e) {
    console.log(`Could not fill field ${selector}: ${e.message}`);
    return false;
  }
}

async function run() {
  console.log('Launching browser...');
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });

  const page = await context.newPage();

  try {
    console.log(`Navigating to ${JOB_URL}...`);
    await page.goto(JOB_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);

    await takeScreenshot(page, '01-job-page');

    // Read page content for job description
    const pageTitle = await page.title();
    const pageText = await page.textContent('body');
    console.log('Page title:', pageTitle);
    console.log('Page text excerpt:', pageText.substring(0, 500));

    // Save job description
    fs.writeFileSync('/home/user/Agents/data/doit-job-description.txt', pageText);
    console.log('Job description saved.');

    // Look for Apply button or check if this is already the application form
    const applyButton = await page.$('a[href*="apply"], button:has-text("Apply"), a:has-text("Apply for this Job"), input[value="Apply"]');

    if (applyButton) {
      console.log('Found Apply button, clicking...');
      await applyButton.click();
      await page.waitForTimeout(2000);
      await takeScreenshot(page, '02-apply-clicked');
    } else {
      console.log('No separate Apply button found — checking if form is already visible...');
      await takeScreenshot(page, '02-page-state');
    }

    // Wait for form fields
    await page.waitForTimeout(2000);
    const currentUrl = page.url();
    console.log('Current URL:', currentUrl);

    // Greenhouse application forms - standard field IDs
    // Try to fill first name
    const firstNameSelectors = [
      'input#first_name',
      'input[name="job_application[first_name]"]',
      'input[placeholder*="First"]',
      'input[id*="first"]',
    ];

    let firstNameFilled = false;
    for (const sel of firstNameSelectors) {
      const el = await page.$(sel);
      if (el) {
        await el.click({ clickCount: 3 });
        await el.type(CANDIDATE.firstName, { delay: 30 });
        console.log(`First name filled with selector: ${sel}`);
        firstNameFilled = true;
        break;
      }
    }
    if (!firstNameFilled) console.log('WARNING: First name field not found');

    // Last name
    const lastNameSelectors = [
      'input#last_name',
      'input[name="job_application[last_name]"]',
      'input[placeholder*="Last"]',
      'input[id*="last"]',
    ];
    for (const sel of lastNameSelectors) {
      const el = await page.$(sel);
      if (el) {
        await el.click({ clickCount: 3 });
        await el.type(CANDIDATE.lastName, { delay: 30 });
        console.log(`Last name filled with selector: ${sel}`);
        break;
      }
    }

    // Email
    const emailSelectors = [
      'input#email',
      'input[name="job_application[email]"]',
      'input[type="email"]',
      'input[id*="email"]',
    ];
    for (const sel of emailSelectors) {
      const el = await page.$(sel);
      if (el) {
        await el.click({ clickCount: 3 });
        await el.type(CANDIDATE.email, { delay: 30 });
        console.log(`Email filled with selector: ${sel}`);
        break;
      }
    }

    // Phone
    const phoneSelectors = [
      'input#phone',
      'input[name="job_application[phone]"]',
      'input[type="tel"]',
      'input[id*="phone"]',
    ];
    for (const sel of phoneSelectors) {
      const el = await page.$(sel);
      if (el) {
        await el.click({ clickCount: 3 });
        await el.type(CANDIDATE.phone, { delay: 30 });
        console.log(`Phone filled with selector: ${sel}`);
        break;
      }
    }

    await takeScreenshot(page, '03-basic-fields-filled');

    // Resume upload
    const resumeInputSelectors = [
      'input#resume',
      'input[name="job_application[resume]"]',
      'input[type="file"][accept*="pdf"]',
      'input[type="file"]',
      'input[id*="resume"]',
    ];
    let resumeUploaded = false;
    for (const sel of resumeInputSelectors) {
      const el = await page.$(sel);
      if (el) {
        await el.setInputFiles(CANDIDATE.resumePath);
        console.log(`Resume uploaded with selector: ${sel}`);
        resumeUploaded = true;
        await page.waitForTimeout(2000);
        break;
      }
    }
    if (!resumeUploaded) {
      console.log('WARNING: Resume upload field not found — trying generic file input');
      const anyFileInput = await page.$('input[type="file"]');
      if (anyFileInput) {
        await anyFileInput.setInputFiles(CANDIDATE.resumePath);
        console.log('Resume uploaded via generic file input');
        resumeUploaded = true;
        await page.waitForTimeout(2000);
      }
    }

    await takeScreenshot(page, '04-after-resume-upload');

    // Cover letter upload (if separate field exists)
    const coverLetterInput = await page.$('input#cover_letter, input[name="job_application[cover_letter]"], input[id*="cover"]');
    if (coverLetterInput) {
      await coverLetterInput.setInputFiles(CANDIDATE.coverLetterPath);
      console.log('Cover letter uploaded');
      await page.waitForTimeout(1000);
    }

    // LinkedIn URL field
    const linkedinSelectors = [
      'input[id*="linkedin"]',
      'input[name*="linkedin"]',
      'input[placeholder*="LinkedIn"]',
      'input[placeholder*="linkedin"]',
    ];
    for (const sel of linkedinSelectors) {
      const el = await page.$(sel);
      if (el) {
        await el.click({ clickCount: 3 });
        await el.type(`https://${CANDIDATE.linkedin}`, { delay: 30 });
        console.log(`LinkedIn filled with selector: ${sel}`);
        break;
      }
    }

    // GitHub/Website field
    const githubSelectors = [
      'input[id*="github"]',
      'input[name*="github"]',
      'input[placeholder*="GitHub"]',
      'input[placeholder*="github"]',
      'input[id*="website"]',
      'input[name*="website"]',
      'input[placeholder*="Website"]',
    ];
    for (const sel of githubSelectors) {
      const el = await page.$(sel);
      if (el) {
        await el.click({ clickCount: 3 });
        await el.type(`https://${CANDIDATE.github}`, { delay: 30 });
        console.log(`GitHub/website filled with selector: ${sel}`);
        break;
      }
    }

    // Look for any other text fields (custom questions)
    await page.waitForTimeout(1000);
    const allInputs = await page.$$('input[type="text"], input[type="email"], input[type="tel"], textarea');
    console.log(`Total fillable fields found: ${allInputs.length}`);

    // Log all form fields to understand the form structure
    const formFields = await page.evaluate(() => {
      const fields = [];
      document.querySelectorAll('input, textarea, select').forEach(el => {
        fields.push({
          tag: el.tagName,
          type: el.type,
          id: el.id,
          name: el.name,
          placeholder: el.placeholder,
          value: el.value ? el.value.substring(0, 50) : '',
          label: el.labels && el.labels[0] ? el.labels[0].textContent.trim() : ''
        });
      });
      return fields;
    });
    console.log('Form fields detected:');
    formFields.forEach(f => console.log(`  ${f.tag}[${f.type}] id="${f.id}" name="${f.name}" placeholder="${f.placeholder}" label="${f.label}" value="${f.value}"`));

    // Save form fields to file for reference
    fs.writeFileSync('/home/user/Agents/data/doit-form-fields.json', JSON.stringify(formFields, null, 2));

    await takeScreenshot(page, '05-form-filled');

    // Scroll to bottom to see full form
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);
    await takeScreenshot(page, '06-form-bottom');

    // Scroll back to top to do another pass
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);

    // Check all form fields again and fill any missed ones
    const updatedFields = await page.evaluate(() => {
      const fields = [];
      document.querySelectorAll('input, textarea, select').forEach(el => {
        if (!el.value || el.value.trim() === '') {
          const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim().toLowerCase() : '';
          const placeholder = (el.placeholder || '').toLowerCase();
          const id = (el.id || '').toLowerCase();
          const name = (el.name || '').toLowerCase();
          fields.push({ tag: el.tagName, type: el.type, id: el.id, name: el.name, placeholder: el.placeholder, label });
        }
      });
      return fields;
    });

    console.log('Unfilled fields remaining:', updatedFields.length);
    updatedFields.forEach(f => console.log(`  UNFILLED: ${f.tag}[${f.type}] id="${f.id}" name="${f.name}" placeholder="${f.placeholder}" label="${f.label}"`));

    // Final screenshot before submit
    await takeScreenshot(page, '07-before-submit');

    // Look for submit button
    const submitButton = await page.$('input[type="submit"], button[type="submit"], button:has-text("Submit"), button:has-text("Apply")');
    if (submitButton) {
      const btnText = await submitButton.textContent().catch(() => 'unknown');
      const btnVal = await submitButton.getAttribute('value').catch(() => '');
      console.log(`Found submit button: "${btnText || btnVal}"`);

      // Take screenshot before submitting
      await takeScreenshot(page, '08-ready-to-submit');

      console.log('Submitting application...');
      await submitButton.click();
      await page.waitForTimeout(4000);

      await takeScreenshot(page, '09-after-submit');

      const postSubmitUrl = page.url();
      const postSubmitTitle = await page.title();
      const postSubmitText = await page.textContent('body');
      console.log('Post-submit URL:', postSubmitUrl);
      console.log('Post-submit title:', postSubmitTitle);
      console.log('Post-submit text excerpt:', postSubmitText.substring(0, 300));

      // Check for success indicators
      const successIndicators = ['thank you', 'application received', 'submitted', 'confirmation', 'success'];
      const isSuccess = successIndicators.some(indicator => postSubmitText.toLowerCase().includes(indicator));
      console.log('Application success:', isSuccess);

      return { success: isSuccess, url: postSubmitUrl, message: postSubmitText.substring(0, 200) };
    } else {
      console.log('WARNING: Submit button not found');
      await takeScreenshot(page, '08-no-submit-button');

      // List all buttons on page
      const buttons = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"]'))
          .map(b => ({ tag: b.tagName, type: b.type, text: b.textContent.trim().substring(0, 50), value: b.value }));
      });
      console.log('All buttons on page:', JSON.stringify(buttons));

      return { success: false, url: page.url(), message: 'Submit button not found' };
    }

  } catch (error) {
    console.error('Error during application:', error);
    await takeScreenshot(page, '99-error').catch(() => {});
    return { success: false, error: error.message };
  } finally {
    await browser.close();
    console.log('Browser closed.');
  }
}

run().then(result => {
  console.log('\n=== APPLICATION RESULT ===');
  console.log(JSON.stringify(result, null, 2));
  fs.writeFileSync('/home/user/Agents/data/doit-apply-result.json', JSON.stringify(result, null, 2));
}).catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
