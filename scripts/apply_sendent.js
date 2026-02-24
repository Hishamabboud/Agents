const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';

// Ensure screenshots directory exists
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

const PERSONAL_DETAILS = {
  fullName: 'Hisham Abboud',
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'Hisham123@hotmail.com',
  phone: '+31 06 4841 2838',
  linkedin: 'linkedin.com/in/hisham-abboud',
  github: 'github.com/Hishamabboud',
  city: 'Eindhoven',
  country: 'Netherlands',
};

const COVER_LETTER = `Dear Sendent B.V. Hiring Team,

I am applying for the Medior Software Engineer (Backend/Integrations/.NET) position. Sendent's focus on sustainable software, privacy-first design, and real ownership aligns well with my professional values and career goals.

As a Software Service Engineer at Actemium in Eindhoven, I work daily with C#/.NET building and maintaining production integrations for industrial clients. I develop API connections, optimize databases, and troubleshoot complex issues in live environments — exactly the kind of backend ownership your Exchange Connector requires. My experience migrating legacy codebases (Visual Basic to C#) at Delta Electronics demonstrates my ability to work with unfamiliar code and improve it methodically.

I also bring strong testing experience from my internship at ASML, where I built automated test suites with Pytest and Locust, and worked with Git-based CI/CD workflows in an agile environment. My graduation project on GDPR data anonymization gave me direct exposure to privacy and compliance concerns — relevant to Sendent's mission of data sovereignty.

I am based in Eindhoven with a valid Dutch work permit and am comfortable with hybrid work. I would value the opportunity to grow by owning real software at Sendent.

Best regards,
Hisham Abboud`;

const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const JOB_URL = 'https://join.com/companies/sendentcom/15650046-medior-software-engineer-backend-integrations-net';

async function takeScreenshot(page, name) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = path.join(SCREENSHOTS_DIR, `sendent-${name}-${timestamp}.png`);
  await page.screenshot({ path: filename, fullPage: true });
  console.log(`Screenshot saved: ${filename}`);
  return filename;
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fillTextField(page, selectors, value) {
  for (const selector of selectors) {
    try {
      const el = await page.$(selector);
      if (el) {
        await el.fill(value);
        return true;
      }
    } catch (e) {
      // Try next selector
    }
  }
  return false;
}

async function main() {
  console.log('Launching browser...');
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  const page = await context.newPage();

  console.log(`Navigating to: ${JOB_URL}`);

  try {
    await page.goto(JOB_URL, { waitUntil: 'networkidle', timeout: 60000 });
    console.log('Page loaded successfully');

    await takeScreenshot(page, '01-job-listing');

    // Look for apply button
    console.log('Looking for Apply button...');
    const applySelectors = [
      'a[href*="apply"]',
      'button:has-text("Apply")',
      'a:has-text("Apply")',
      'button:has-text("apply")',
      '[data-testid="apply-button"]',
      '.apply-button',
      '#apply-button',
      'button:has-text("Apply now")',
      'a:has-text("Apply now")',
    ];

    let applyClicked = false;
    for (const selector of applySelectors) {
      try {
        const el = await page.$(selector);
        if (el) {
          console.log(`Found apply button with selector: ${selector}`);
          await el.click();
          applyClicked = true;
          break;
        }
      } catch (e) {
        // Try next
      }
    }

    if (!applyClicked) {
      // Try clicking any visible button with apply text
      const buttons = await page.$$('button, a');
      for (const btn of buttons) {
        const text = await btn.textContent().catch(() => '');
        if (text && text.toLowerCase().includes('apply')) {
          console.log(`Clicking button with text: ${text.trim()}`);
          await btn.click();
          applyClicked = true;
          break;
        }
      }
    }

    if (!applyClicked) {
      console.log('Could not find apply button. Capturing page content...');
      const content = await page.content();
      fs.writeFileSync('/home/user/Agents/output/screenshots/sendent-page-content.html', content);
      await takeScreenshot(page, '02-no-apply-button');
    } else {
      console.log('Clicked apply button, waiting for form...');
      await sleep(3000);
      await takeScreenshot(page, '02-after-apply-click');

      // Check if we navigated to a new page/modal
      const currentUrl = page.url();
      console.log(`Current URL after clicking apply: ${currentUrl}`);

      // Wait for form fields to appear
      await page.waitForSelector('input, textarea, form', { timeout: 15000 }).catch(() => {
        console.log('No form fields detected within timeout');
      });

      await takeScreenshot(page, '03-form-page');

      // Try to fill in form fields
      console.log('Attempting to fill form fields...');

      // Name fields
      const nameSelectors = [
        ['input[name*="name" i]:not([name*="last" i]):not([name*="sur" i])', 'input[placeholder*="name" i]:not([placeholder*="last" i])', 'input[id*="name" i]:not([id*="last" i])', 'input[autocomplete="name"]'],
      ];

      // First name
      await fillTextField(page, [
        'input[name="first_name"]', 'input[name="firstName"]', 'input[id="first_name"]',
        'input[id="firstName"]', 'input[placeholder*="first name" i]', 'input[autocomplete="given-name"]',
        'input[name*="first" i]', 'input[id*="first" i]'
      ], PERSONAL_DETAILS.firstName);

      // Last name
      await fillTextField(page, [
        'input[name="last_name"]', 'input[name="lastName"]', 'input[id="last_name"]',
        'input[id="lastName"]', 'input[placeholder*="last name" i]', 'input[autocomplete="family-name"]',
        'input[name*="last" i]', 'input[id*="last" i]', 'input[name*="sur" i]'
      ], PERSONAL_DETAILS.lastName);

      // Full name (if no separate first/last)
      await fillTextField(page, [
        'input[name="name"]', 'input[name="full_name"]', 'input[name="fullName"]',
        'input[id="name"]', 'input[placeholder*="full name" i]', 'input[autocomplete="name"]'
      ], PERSONAL_DETAILS.fullName);

      // Email
      await fillTextField(page, [
        'input[type="email"]', 'input[name="email"]', 'input[id="email"]',
        'input[placeholder*="email" i]', 'input[autocomplete="email"]'
      ], PERSONAL_DETAILS.email);

      // Phone
      await fillTextField(page, [
        'input[type="tel"]', 'input[name="phone"]', 'input[name="telephone"]',
        'input[id="phone"]', 'input[placeholder*="phone" i]', 'input[autocomplete="tel"]',
        'input[name*="phone" i]', 'input[id*="phone" i]'
      ], PERSONAL_DETAILS.phone);

      // LinkedIn
      await fillTextField(page, [
        'input[name*="linkedin" i]', 'input[id*="linkedin" i]',
        'input[placeholder*="linkedin" i]', 'input[name*="social" i]'
      ], PERSONAL_DETAILS.linkedin);

      // GitHub
      await fillTextField(page, [
        'input[name*="github" i]', 'input[id*="github" i]',
        'input[placeholder*="github" i]'
      ], PERSONAL_DETAILS.github);

      // City
      await fillTextField(page, [
        'input[name*="city" i]', 'input[id*="city" i]',
        'input[placeholder*="city" i]', 'input[autocomplete="address-level2"]',
        'input[name*="location" i]'
      ], PERSONAL_DETAILS.city);

      // Cover letter textarea
      const coverLetterFilled = await fillTextField(page, [
        'textarea[name*="cover" i]', 'textarea[id*="cover" i]',
        'textarea[placeholder*="cover" i]', 'textarea[name*="letter" i]',
        'textarea[name*="motivation" i]', 'textarea[id*="motivation" i]',
        'textarea[placeholder*="motivation" i]', 'textarea[placeholder*="message" i]',
        'textarea'
      ], COVER_LETTER);

      if (coverLetterFilled) {
        console.log('Cover letter filled');
      }

      // Handle file upload for resume
      const fileInputs = await page.$$('input[type="file"]');
      if (fileInputs.length > 0) {
        console.log(`Found ${fileInputs.length} file input(s). Uploading resume...`);
        try {
          await fileInputs[0].setInputFiles(RESUME_PATH);
          console.log('Resume uploaded successfully');
          await sleep(2000);
        } catch (e) {
          console.log(`Error uploading resume: ${e.message}`);
        }
      }

      await takeScreenshot(page, '04-form-filled');

      // Check all form fields that are filled
      const inputs = await page.$$('input:not([type="hidden"]):not([type="file"]), textarea, select');
      console.log(`Total visible form fields: ${inputs.length}`);

      for (const input of inputs) {
        const name = await input.getAttribute('name').catch(() => '');
        const type = await input.getAttribute('type').catch(() => '');
        const value = await input.inputValue().catch(() => '');
        const tag = await input.evaluate(el => el.tagName).catch(() => '');
        if (value) {
          console.log(`  [${tag}] name="${name}" type="${type}" value="${value.substring(0, 50)}..."`);
        } else {
          console.log(`  [${tag}] name="${name}" type="${type}" value=(empty)`);
        }
      }

      // Take pre-submit screenshot
      console.log('Taking pre-submission screenshot...');
      const preSubmitScreenshot = await takeScreenshot(page, '05-before-submit');

      // Look for submit button
      console.log('Looking for submit button...');
      const submitSelectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Send application")',
        'button:has-text("Send Application")',
        'button:has-text("Apply")',
        'button:has-text("Submit application")',
        'button:has-text("Submit Application")',
      ];

      let submitButton = null;
      for (const selector of submitSelectors) {
        try {
          const el = await page.$(selector);
          if (el) {
            const isVisible = await el.isVisible();
            if (isVisible) {
              submitButton = el;
              console.log(`Found submit button: ${selector}`);
              break;
            }
          }
        } catch (e) {
          // Try next
        }
      }

      if (submitButton) {
        console.log('Submitting application...');
        await submitButton.click();
        await sleep(5000);

        await takeScreenshot(page, '06-after-submit');

        const finalUrl = page.url();
        console.log(`Final URL after submission: ${finalUrl}`);

        // Check for success messages
        const pageText = await page.textContent('body').catch(() => '');
        const successKeywords = ['thank', 'success', 'received', 'submitted', 'confirmation', 'bedankt', 'ontvangen'];
        const hasSuccess = successKeywords.some(kw => pageText.toLowerCase().includes(kw));

        if (hasSuccess) {
          console.log('SUCCESS: Application appears to have been submitted successfully!');
        } else {
          console.log('UNCERTAIN: Could not confirm successful submission from page content');
          // Save page content for inspection
          const content = await page.content();
          fs.writeFileSync('/home/user/Agents/output/screenshots/sendent-post-submit.html', content);
        }
      } else {
        console.log('Could not find submit button. Form may need manual intervention.');
        // Save page content for inspection
        const content = await page.content();
        fs.writeFileSync('/home/user/Agents/output/screenshots/sendent-no-submit.html', content);
      }
    }

  } catch (error) {
    console.error(`Error during application: ${error.message}`);
    await takeScreenshot(page, 'error');
    throw error;
  } finally {
    await browser.close();
    console.log('Browser closed.');
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
