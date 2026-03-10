const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const JOB_URL = 'https://ixonbv.recruitee.com/o/embedded-software-engineer';

const APPLICANT = {
  name: 'Hisham Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31 06 4841 2838',
  location: 'Eindhoven, Netherlands',
};

function ts() {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
}

async function screenshot(page, label) {
  const filename = `ixon-${label}-${ts()}.png`;
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`Screenshot saved: ${filepath}`);
  return filepath;
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    userAgent:
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });

  const page = await context.newPage();

  try {
    console.log('Navigating to job page...');
    await page.goto(JOB_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await screenshot(page, '01-job-page');

    // Look for Apply button
    console.log('Looking for Apply button...');
    const applyBtn = page.locator('a[href*="apply"], button:has-text("Apply"), a:has-text("Apply"), .apply-button, [data-qa="apply-button"]').first();

    let applyBtnVisible = false;
    try {
      await applyBtn.waitFor({ timeout: 5000 });
      applyBtnVisible = true;
    } catch (e) {
      console.log('Standard apply button not found, trying other selectors...');
    }

    if (applyBtnVisible) {
      console.log('Clicking Apply button...');
      await applyBtn.click();
      await page.waitForTimeout(2000);
      await screenshot(page, '02-after-apply-click');
    } else {
      // Try scrolling to find apply button
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(1000);
      await screenshot(page, '02-scrolled-page');

      const applyBtn2 = page.locator('text=Apply').first();
      try {
        await applyBtn2.click();
        await page.waitForTimeout(2000);
        await screenshot(page, '02b-after-apply-click');
      } catch (e) {
        console.log('Could not find apply button by text either:', e.message);
      }
    }

    console.log('Current URL:', page.url());

    // Wait for form to appear
    await page.waitForTimeout(2000);

    // Check for name field
    const nameField = page.locator('input[name="name"], input[placeholder*="name" i], input[id*="name" i], input[autocomplete="name"]').first();
    let nameVisible = false;
    try {
      await nameField.waitFor({ timeout: 5000 });
      nameVisible = true;
    } catch (e) {
      console.log('Name field not found with standard selectors, checking page...');
    }

    if (!nameVisible) {
      // Check if form is embedded on same page
      const inputs = await page.locator('input').all();
      console.log(`Found ${inputs.length} input fields on page`);
      for (const inp of inputs) {
        const placeholder = await inp.getAttribute('placeholder');
        const name = await inp.getAttribute('name');
        const id = await inp.getAttribute('id');
        console.log(`  Input: name="${name}" id="${id}" placeholder="${placeholder}"`);
      }
    }

    // Try to fill name
    try {
      const nameSelectors = [
        'input[name="name"]',
        'input[id="name"]',
        'input[placeholder*="name" i]',
        'input[autocomplete="name"]',
        'input[name="full_name"]',
        'input[name="candidate[name]"]',
      ];

      let filled = false;
      for (const sel of nameSelectors) {
        try {
          const el = page.locator(sel).first();
          await el.waitFor({ timeout: 2000 });
          await el.fill(APPLICANT.name);
          console.log(`Filled name using selector: ${sel}`);
          filled = true;
          break;
        } catch (e) {
          // try next
        }
      }
      if (!filled) console.log('Could not fill name field');
    } catch (e) {
      console.log('Error filling name:', e.message);
    }

    // Fill email
    try {
      const emailSelectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[id="email"]',
        'input[placeholder*="email" i]',
        'input[name="candidate[email]"]',
      ];

      let filled = false;
      for (const sel of emailSelectors) {
        try {
          const el = page.locator(sel).first();
          await el.waitFor({ timeout: 2000 });
          await el.fill(APPLICANT.email);
          console.log(`Filled email using selector: ${sel}`);
          filled = true;
          break;
        } catch (e) {
          // try next
        }
      }
      if (!filled) console.log('Could not fill email field');
    } catch (e) {
      console.log('Error filling email:', e.message);
    }

    // Fill phone
    try {
      const phoneSelectors = [
        'input[type="tel"]',
        'input[name="phone"]',
        'input[id="phone"]',
        'input[placeholder*="phone" i]',
        'input[name="candidate[phone]"]',
      ];

      let filled = false;
      for (const sel of phoneSelectors) {
        try {
          const el = page.locator(sel).first();
          await el.waitFor({ timeout: 2000 });
          await el.fill(APPLICANT.phone);
          console.log(`Filled phone using selector: ${sel}`);
          filled = true;
          break;
        } catch (e) {
          // try next
        }
      }
      if (!filled) console.log('Could not fill phone field');
    } catch (e) {
      console.log('Error filling phone:', e.message);
    }

    // Handle country selection
    try {
      const countrySelectors = [
        'select[name="country"]',
        'select[id="country"]',
        'select[name="candidate[country]"]',
      ];

      for (const sel of countrySelectors) {
        try {
          const el = page.locator(sel).first();
          await el.waitFor({ timeout: 2000 });
          await el.selectOption({ label: 'Netherlands' });
          console.log(`Selected country using selector: ${sel}`);
          break;
        } catch (e) {
          // try next
        }
      }
    } catch (e) {
      console.log('Error selecting country:', e.message);
    }

    await screenshot(page, '03-form-filled');

    // Upload resume
    try {
      if (fs.existsSync(RESUME_PATH)) {
        const fileInputSelectors = [
          'input[type="file"]',
          'input[accept*="pdf"]',
          'input[name="resume"]',
          'input[name="cv"]',
        ];

        let uploaded = false;
        for (const sel of fileInputSelectors) {
          try {
            const fileInput = page.locator(sel).first();
            await fileInput.waitFor({ timeout: 2000 });
            await fileInput.setInputFiles(RESUME_PATH);
            console.log(`Resume uploaded using selector: ${sel}`);
            uploaded = true;
            break;
          } catch (e) {
            // try next
          }
        }
        if (!uploaded) console.log('Could not upload resume - no file input found');
      } else {
        console.log(`Resume not found at: ${RESUME_PATH}`);
      }
    } catch (e) {
      console.log('Error uploading resume:', e.message);
    }

    await page.waitForTimeout(2000);
    await screenshot(page, '04-resume-uploaded');

    // Take screenshot before submit
    await screenshot(page, '05-pre-submit');

    // Look for submit button
    try {
      const submitSelectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Send")',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
        '.submit-button',
      ];

      let submitted = false;
      for (const sel of submitSelectors) {
        try {
          const btn = page.locator(sel).first();
          await btn.waitFor({ timeout: 2000 });
          const btnText = await btn.textContent();
          console.log(`Found submit button: "${btnText}" with selector: ${sel}`);

          // Screenshot before clicking submit
          await screenshot(page, '06-before-final-submit');
          await btn.click();
          console.log('Submitted application!');
          submitted = true;
          break;
        } catch (e) {
          // try next
        }
      }
      if (!submitted) console.log('Could not find submit button');
    } catch (e) {
      console.log('Error submitting:', e.message);
    }

    await page.waitForTimeout(3000);
    await screenshot(page, '07-post-submit');

    // Check for confirmation
    const pageContent = await page.content();
    if (pageContent.includes('successfully submitted') || pageContent.includes('Thank you') || pageContent.includes('success')) {
      console.log('SUCCESS: Application appears to have been submitted!');
    } else {
      console.log('Status unclear - check screenshots for confirmation');
    }

    console.log('Final URL:', page.url());

  } catch (err) {
    console.error('Error during application:', err.message);
    await screenshot(page, '99-error');
  } finally {
    await browser.close();
    console.log('Browser closed.');
  }
})();
