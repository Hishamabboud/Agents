const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const COVER_LETTER_PATH = '/home/user/Agents/output/cover-letters/foxtek-net-developer.md';

const APPLICANT = {
  name: 'Hisham Abboud',
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31 06 4841 2838',
  location: 'Eindhoven, Netherlands',
  currentRole: 'Software Service Engineer at Actemium (VINCI Energies)',
};

function timestamp() {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
}

async function screenshot(page, name) {
  const filePath = path.join(SCREENSHOTS_DIR, `foxtek-${name}-${timestamp()}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  console.log(`Screenshot saved: ${filePath}`);
  return filePath;
}

async function run() {
  const coverLetter = fs.readFileSync(COVER_LETTER_PATH, 'utf8').trim();

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const context = await browser.newContext({
    userAgent:
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });

  const page = await context.newPage();

  try {
    console.log('Navigating to job page...');
    await page.goto('https://www.foxtekrs.com/job/dot-net-developer-1', {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    await page.waitForTimeout(2000);
    await screenshot(page, '01-job-page');
    console.log('Job page loaded. Title:', await page.title());

    // Look for Apply button
    const applySelectors = [
      'a:has-text("Apply")',
      'button:has-text("Apply")',
      'a:has-text("apply")',
      'button:has-text("apply")',
      'a[href*="apply"]',
      '.apply-button',
      '#apply-button',
      'a:has-text("Apply Now")',
      'button:has-text("Apply Now")',
    ];

    let applyBtn = null;
    for (const sel of applySelectors) {
      try {
        applyBtn = await page.$(sel);
        if (applyBtn) {
          console.log(`Found apply button with selector: ${sel}`);
          break;
        }
      } catch (e) {
        // continue
      }
    }

    if (applyBtn) {
      await applyBtn.click();
      await page.waitForTimeout(2000);
      await screenshot(page, '02-after-apply-click');
      console.log('Clicked Apply. Current URL:', page.url());
    } else {
      console.log('No direct Apply button found. Checking page content for form or links...');
      await screenshot(page, '02-no-apply-button');
    }

    // Check for external redirect or new page
    const currentUrl = page.url();
    console.log('Current URL after apply click:', currentUrl);

    // Try to detect a form on the current page
    const formExists = await page.$('form');
    if (formExists) {
      console.log('Form detected on current page. Attempting to fill...');
      await fillForm(page, coverLetter, screenshot);
    } else {
      console.log('No form on this page. Checking for iframe or modal...');

      // Check for modal
      const modal = await page.$('[class*="modal"], [class*="dialog"], [id*="modal"]');
      if (modal) {
        console.log('Modal detected.');
        await screenshot(page, '03-modal');
      }

      // Full page text for analysis
      const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 2000));
      console.log('Page text excerpt:', bodyText);
      await screenshot(page, '03-final-state');
    }

  } catch (err) {
    console.error('Error during automation:', err.message);
    await screenshot(page, 'error').catch(() => {});
  } finally {
    await browser.close();
  }
}

async function fillForm(page, coverLetter, screenshotFn) {
  console.log('Filling in form fields...');

  // Helper: fill field if selector found
  async function tryFill(selectors, value) {
    for (const sel of selectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          await el.click({ timeout: 3000 });
          await el.fill(value);
          console.log(`Filled "${sel}" with "${value.substring(0, 30)}..."`);
          return true;
        }
      } catch (e) {
        // continue
      }
    }
    return false;
  }

  // Name fields
  await tryFill(
    ['input[name*="first_name"]', 'input[name*="firstName"]', 'input[placeholder*="First"]', '#first_name'],
    APPLICANT.firstName
  );
  await tryFill(
    ['input[name*="last_name"]', 'input[name*="lastName"]', 'input[placeholder*="Last"]', '#last_name'],
    APPLICANT.lastName
  );
  await tryFill(
    ['input[name*="name"]:not([name*="last"]):not([name*="first"])', 'input[placeholder*="Full Name"]', 'input[placeholder*="Name"]', '#name'],
    APPLICANT.name
  );

  // Email
  await tryFill(
    ['input[type="email"]', 'input[name*="email"]', 'input[placeholder*="email"]', '#email'],
    APPLICANT.email
  );

  // Phone
  await tryFill(
    ['input[type="tel"]', 'input[name*="phone"]', 'input[placeholder*="phone"]', '#phone'],
    APPLICANT.phone
  );

  // Location
  await tryFill(
    ['input[name*="location"]', 'input[name*="city"]', 'input[placeholder*="location"]', 'input[placeholder*="city"]'],
    APPLICANT.location
  );

  // Cover letter / message
  const coverSelectors = [
    'textarea[name*="cover"]',
    'textarea[name*="message"]',
    'textarea[name*="letter"]',
    'textarea[placeholder*="cover"]',
    'textarea[placeholder*="message"]',
    'textarea',
  ];
  for (const sel of coverSelectors) {
    try {
      const el = await page.$(sel);
      if (el) {
        await el.click();
        await el.fill(coverLetter);
        console.log(`Filled cover letter into: ${sel}`);
        break;
      }
    } catch (e) {
      // continue
    }
  }

  // Resume upload
  const resumeInput = await page.$('input[type="file"]');
  if (resumeInput) {
    try {
      await resumeInput.setInputFiles(RESUME_PATH);
      console.log('Uploaded resume file.');
    } catch (e) {
      console.log('Could not upload resume:', e.message);
    }
  } else {
    console.log('No file upload input found.');
  }

  await page.waitForTimeout(1000);
  await screenshotFn(page, '04-form-filled');

  // Look for submit button
  const submitSelectors = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Submit")',
    'button:has-text("Apply")',
    'button:has-text("Send")',
  ];

  let submitted = false;
  for (const sel of submitSelectors) {
    try {
      const btn = await page.$(sel);
      if (btn) {
        await screenshotFn(page, '05-pre-submit');
        console.log(`Clicking submit: ${sel}`);
        await btn.click();
        await page.waitForTimeout(3000);
        await screenshotFn(page, '06-post-submit');
        console.log('Form submitted. URL:', page.url());
        submitted = true;
        break;
      }
    } catch (e) {
      // continue
    }
  }

  if (!submitted) {
    console.log('No submit button found.');
    await screenshotFn(page, '05-no-submit');
  }
}

run().then(() => {
  console.log('Done.');
}).catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
