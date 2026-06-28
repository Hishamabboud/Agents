const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const APPLICATION_URL = 'https://job-boards.eu.greenhouse.io/nice/jobs/4826064101';

const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);

async function screenshot(page, label) {
  const filename = `nice-csharp-engineer-${label}-${timestamp}.png`;
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`Screenshot: ${filepath}`);
  return filepath;
}

// Helper to select an option in a React Select dropdown
async function selectReactOption(page, containerId, optionText) {
  // Click the control to open the dropdown
  const control = await page.$(`.select-shell:has(#react-select-${containerId}-placeholder), .select-shell:has(#react-select-${containerId}-input), div:has(> #react-select-${containerId}-live-region)`);

  // Alternative: find by the label's "for" attribute mapping to the container
  // Click the dropdown control
  try {
    await page.click(`#react-select-${containerId}-placeholder, #react-select-${containerId}-input`, { timeout: 5000 });
  } catch(e) {
    // Try clicking the control div directly
    await page.evaluate((id) => {
      const liveRegion = document.getElementById(`react-select-${id}-live-region`);
      if (liveRegion) {
        const container = liveRegion.closest('.select-shell');
        if (container) {
          const control = container.querySelector('.select__control');
          if (control) control.click();
        }
      }
    }, containerId);
  }

  await page.waitForTimeout(500);

  // Now look for the option in the dropdown menu
  const optionSelector = `.select__option:has-text("${optionText}"), [class*="option"]:has-text("${optionText}")`;
  try {
    await page.click(optionSelector, { timeout: 5000 });
    console.log(`Selected "${optionText}" for ${containerId}`);
    return true;
  } catch(e) {
    // Try clicking by text evaluation
    const clicked = await page.evaluate((text) => {
      const options = document.querySelectorAll('[class*="option"]');
      for (const opt of options) {
        if (opt.textContent.trim() === text) {
          opt.click();
          return true;
        }
      }
      return false;
    }, optionText);
    if (clicked) {
      console.log(`Selected "${optionText}" for ${containerId} via evaluate`);
      return true;
    }
    console.log(`Failed to select "${optionText}" for ${containerId}: ${e.message}`);
    return false;
  }
}

// Select country in phone field
async function selectPhoneCountry(page, countryName) {
  // The phone country select is the first React Select on the page
  try {
    // Click the country select control
    await page.click('.phone-input__country .select__control', { timeout: 5000 });
    await page.waitForTimeout(300);

    // Type to filter
    await page.keyboard.type(countryName.substring(0, 4));
    await page.waitForTimeout(500);

    // Click the matching option
    const clicked = await page.evaluate((text) => {
      const options = document.querySelectorAll('[class*="option"]');
      for (const opt of options) {
        if (opt.textContent.trim().toLowerCase().includes(text.toLowerCase())) {
          opt.click();
          return true;
        }
      }
      return false;
    }, countryName);

    if (clicked) {
      console.log(`Selected phone country: ${countryName}`);
    } else {
      console.log(`Could not find phone country option: ${countryName}`);
    }
  } catch(e) {
    console.log(`Phone country selection error: ${e.message}`);
  }
}

async function run() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 1200 },
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  try {
    console.log('Navigating to application page...');
    await page.goto(APPLICATION_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1000);
    console.log('Page loaded:', await page.title());
    await screenshot(page, '01-page-loaded');

    // Fill basic text fields
    await page.fill('#first_name', 'Hisham');
    console.log('Filled: First Name');

    await page.fill('#last_name', 'Abboud');
    console.log('Filled: Last Name');

    await page.fill('#email', 'hiaham123@hotmail.com');
    console.log('Filled: Email');

    // Select phone country (Netherlands = +31)
    await selectPhoneCountry(page, 'Netherlands');
    await page.waitForTimeout(500);

    // Fill phone number
    await page.fill('#phone', '+31 06 4841 2838');
    console.log('Filled: Phone');

    await screenshot(page, '02-basic-filled');

    // Upload resume
    console.log('Uploading resume...');
    const fileInput = await page.$('#resume');
    if (fileInput) {
      await fileInput.setInputFiles(RESUME_PATH);
      await page.waitForTimeout(2000);
      console.log('Resume uploaded');
    } else {
      console.log('Resume input not found');
    }

    await screenshot(page, '03-after-upload');

    // Fill LinkedIn
    try {
      const linkedinInput = await page.$('#question_8590526101');
      if (linkedinInput) {
        await linkedinInput.fill('https://linkedin.com/in/hisham-abboud');
        console.log('Filled: LinkedIn');
      }
    } catch(e) {
      console.log('LinkedIn fill error:', e.message);
    }

    await screenshot(page, '04-linkedin-filled');

    // Handle Yes/No dropdowns using React Select
    // Question: Do you have first-degree relatives at NICE? -> No
    console.log('Handling relatives question...');
    await page.click(`[id="react-select-question_8590527101-placeholder"], .select-shell:first-of-type .select__control`, { timeout: 5000 }).catch(async () => {
      // Try finding by label
      await page.evaluate(() => {
        const labels = document.querySelectorAll('label');
        for (const label of labels) {
          if (label.textContent.includes('first-degree relatives')) {
            const fieldWrapper = label.closest('.field-wrapper');
            if (fieldWrapper) {
              const control = fieldWrapper.querySelector('.select__control');
              if (control) control.click();
            }
            break;
          }
        }
      });
    });
    await page.waitForTimeout(500);

    // Click "No" option
    let noClicked = await page.evaluate(() => {
      const options = document.querySelectorAll('[class*="option"]');
      for (const opt of options) {
        if (opt.textContent.trim() === 'No') {
          opt.click();
          return true;
        }
      }
      return false;
    });
    if (noClicked) {
      console.log('Selected No for relatives question');
    } else {
      console.log('Could not select No for relatives - trying alternative');
    }
    await page.waitForTimeout(300);

    // Question: Have you ever worked at NICE? -> No
    console.log('Handling worked at NICE question...');
    await page.evaluate(() => {
      const labels = document.querySelectorAll('label');
      for (const label of labels) {
        if (label.textContent.includes('worked at NICE')) {
          const fieldWrapper = label.closest('.field-wrapper');
          if (fieldWrapper) {
            const control = fieldWrapper.querySelector('.select__control');
            if (control) control.click();
          }
          break;
        }
      }
    });
    await page.waitForTimeout(500);

    noClicked = await page.evaluate(() => {
      const options = document.querySelectorAll('[class*="option"]');
      for (const opt of options) {
        if (opt.textContent.trim() === 'No') {
          opt.click();
          return true;
        }
      }
      return false;
    });
    if (noClicked) {
      console.log('Selected No for worked at NICE question');
    } else {
      console.log('Could not select No for worked at NICE');
    }
    await page.waitForTimeout(300);

    // Question: Do you require visa sponsorship? -> No
    console.log('Handling visa sponsorship question...');
    await page.evaluate(() => {
      const labels = document.querySelectorAll('label');
      for (const label of labels) {
        if (label.textContent.includes('visa sponsorship')) {
          const fieldWrapper = label.closest('.field-wrapper');
          if (fieldWrapper) {
            const control = fieldWrapper.querySelector('.select__control');
            if (control) control.click();
          }
          break;
        }
      }
    });
    await page.waitForTimeout(500);

    noClicked = await page.evaluate(() => {
      const options = document.querySelectorAll('[class*="option"]');
      for (const opt of options) {
        if (opt.textContent.trim() === 'No') {
          opt.click();
          return true;
        }
      }
      return false;
    });
    if (noClicked) {
      console.log('Selected No for visa sponsorship question');
    } else {
      console.log('Could not select No for visa sponsorship');
    }
    await page.waitForTimeout(300);

    await screenshot(page, '05-dropdowns-filled');

    // Fill AI experience textarea
    console.log('Filling AI experience textarea...');
    try {
      const textarea = await page.$('#question_8973016101');
      if (textarea) {
        // Scroll into view first
        await textarea.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
        await textarea.click();
        await textarea.fill('I use AI coding assistants daily as a core part of my development workflow. I work with Claude Code, GitHub Copilot, and Cursor regularly — both for code generation and for evaluating and improving AI-generated output. Through CogitatAI, my AI customer support platform, I have integrated LLM APIs directly and designed prompt engineering workflows for production use. I approach AI tools as collaborative development partners rather than shortcuts, and I actively refine prompts and review outputs critically.');
        console.log('Filled AI experience textarea');
      } else {
        console.log('AI textarea not found');
      }
    } catch(e) {
      console.log('AI textarea error:', e.message);
    }

    await screenshot(page, '06-all-filled');

    // Scroll to bottom to see full form state
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await screenshot(page, '07-scrolled-bottom');

    // Check form validation state
    const formState = await page.evaluate(() => {
      const hiddenRequired = document.querySelectorAll('input[required][aria-hidden="true"]');
      const states = [];
      hiddenRequired.forEach(el => {
        const container = el.closest('.select-shell, .field-wrapper');
        const label = container ? container.closest('.field-wrapper')?.querySelector('label')?.textContent?.trim() : 'unknown';
        states.push({ value: el.value, label });
      });
      return states;
    });
    console.log('Hidden required field states:', JSON.stringify(formState, null, 2));

    // Take final screenshot
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);
    await screenshot(page, '08-pre-submit');

    // Submit
    console.log('Clicking submit...');
    const submitBtn = await page.$('button[type="submit"]');
    if (submitBtn) {
      const btnText = await submitBtn.textContent();
      console.log(`Submit button text: "${btnText}"`);
      await submitBtn.click();
      await page.waitForTimeout(4000);
      await screenshot(page, '09-after-submit');
    } else {
      console.log('No submit button found');
    }

    const finalUrl = page.url();
    const pageText = await page.evaluate(() => document.body.innerText);
    const hasSuccess = /thank you|application received|successfully submitted|confirmation|submitted/i.test(pageText);
    const hasError = /error|required field|please complete|invalid|please select/i.test(pageText);
    const hasValidationErrors = await page.$$eval('.error-message, [class*="error"]:not([aria-hidden="true"]):not([style*="display: none"])', els =>
      els.filter(el => el.textContent.trim()).map(el => el.textContent.trim())
    );

    console.log('\n=== RESULT ===');
    console.log('Final URL:', finalUrl);
    console.log('Has success:', hasSuccess);
    console.log('Has error:', hasError);
    console.log('Validation errors:', hasValidationErrors);
    console.log('Page text snippet:', pageText.substring(0, 500));

    const result = {
      submitted: true,
      success: hasSuccess,
      finalUrl,
      hasError,
      validationErrors: hasValidationErrors,
      timestamp: new Date().toISOString()
    };
    fs.writeFileSync('/home/user/Agents/data/nice-apply-result.json', JSON.stringify(result, null, 2));

  } catch(error) {
    console.error('Error:', error.message);
    await screenshot(page, '99-error').catch(() => {});
    const result = { submitted: false, error: error.message, timestamp: new Date().toISOString() };
    fs.writeFileSync('/home/user/Agents/data/nice-apply-result.json', JSON.stringify(result, null, 2));
    throw error;
  } finally {
    await browser.close();
  }
}

run().catch(e => {
  console.error('Fatal:', e.message);
  process.exit(1);
});
