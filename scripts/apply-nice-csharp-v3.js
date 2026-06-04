const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const APPLICATION_URL = 'https://job-boards.eu.greenhouse.io/nice/jobs/4826064101';

const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);

async function screenshot(page, label) {
  const filename = `nice-csharp-v3-${label}-${timestamp}.png`;
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`Screenshot: ${filepath}`);
  return filename;
}

// Select an option in a React Select dropdown by finding the control near a label text
async function selectReactSelectByLabel(page, labelText, optionText) {
  console.log(`Selecting "${optionText}" for "${labelText}"...`);

  // Find the control div associated with this label
  const controlLocator = page.locator('.field-wrapper').filter({ hasText: labelText }).locator('.select__control').first();

  try {
    await controlLocator.waitFor({ state: 'visible', timeout: 5000 });
    await controlLocator.click();
    await page.waitForTimeout(300);

    // Now the dropdown menu should be open - look for the option
    // Greenhouse React Select renders options in the document (not inside the control)
    const optionLocator = page.locator('.select__option', { hasText: optionText });
    await optionLocator.first().waitFor({ state: 'visible', timeout: 3000 });
    await optionLocator.first().click();
    await page.waitForTimeout(200);

    console.log(`  -> Selected "${optionText}"`);
    return true;
  } catch(e) {
    console.log(`  -> Failed: ${e.message}`);

    // Fallback: try keyboard navigation
    try {
      await controlLocator.click();
      await page.waitForTimeout(300);
      // Type to filter
      await page.keyboard.type(optionText.substring(0, 2));
      await page.waitForTimeout(300);
      await page.keyboard.press('Enter');
      await page.waitForTimeout(200);
      console.log(`  -> Fallback keyboard selection attempted`);
      return true;
    } catch(e2) {
      console.log(`  -> Fallback also failed: ${e2.message}`);
      return false;
    }
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
  const screenshotFiles = [];

  try {
    console.log('Navigating...');
    await page.goto(APPLICATION_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1500);
    console.log('Title:', await page.title());
    screenshotFiles.push(await screenshot(page, '01-page-loaded'));

    // Fill text fields
    await page.locator('#first_name').fill('Hisham');
    await page.locator('#last_name').fill('Abboud');
    await page.locator('#email').fill('hiaham123@hotmail.com');
    console.log('Filled: name and email');

    // Phone country select - click the country control in the phone-input section
    const phoneCountryControl = page.locator('.phone-input__country .select__control');
    await phoneCountryControl.click();
    await page.waitForTimeout(400);
    // Type "Neth" to filter
    await page.keyboard.type('Neth');
    await page.waitForTimeout(400);
    // Click the Netherlands option
    await page.locator('.select__option').filter({ hasText: 'Netherlands' }).first().click();
    await page.waitForTimeout(300);
    console.log('Selected phone country: Netherlands');

    // Phone number
    await page.locator('#phone').fill('648412838');
    console.log('Filled: phone');

    screenshotFiles.push(await screenshot(page, '02-basic-filled'));

    // Upload resume via file input
    const resumeInput = page.locator('#resume');
    await resumeInput.setInputFiles(RESUME_PATH);
    await page.waitForTimeout(2000);
    console.log('Resume uploaded');

    screenshotFiles.push(await screenshot(page, '03-after-upload'));

    // LinkedIn
    await page.locator('#question_8590526101').fill('https://linkedin.com/in/hisham-abboud');
    console.log('Filled: LinkedIn');

    screenshotFiles.push(await screenshot(page, '04-linkedin-filled'));

    // Handle the three Yes/No dropdowns
    // 1. Relatives question -> No
    await selectReactSelectByLabel(page, 'first-degree relatives', 'No');
    await page.waitForTimeout(400);

    // 2. Worked at NICE -> No
    await selectReactSelectByLabel(page, 'worked at NICE', 'No');
    await page.waitForTimeout(400);

    // 3. Visa sponsorship -> No
    await selectReactSelectByLabel(page, 'visa sponsorship', 'No');
    await page.waitForTimeout(400);

    screenshotFiles.push(await screenshot(page, '05-dropdowns-done'));

    // Check hidden field values to confirm selections
    const hiddenVals = await page.locator('input[required][aria-hidden="true"]').all();
    for (const el of hiddenVals) {
      const val = await el.getAttribute('value');
      console.log(`Hidden required input value: "${val}"`);
    }

    // AI experience textarea
    const textarea = page.locator('#question_8973016101');
    await textarea.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await textarea.click();
    await textarea.fill('I use AI coding assistants daily as a core part of my development workflow. I work with Claude Code, GitHub Copilot, and Cursor regularly — both for code generation and for evaluating and improving AI-generated output. Through CogitatAI, my AI customer support platform, I have integrated LLM APIs directly and designed prompt engineering workflows for production use. I approach AI tools as collaborative development partners rather than shortcuts, and I actively refine prompts and review outputs critically.');
    console.log('Filled: AI experience');

    screenshotFiles.push(await screenshot(page, '06-all-filled'));

    // Scroll to top for pre-submit screenshot
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);
    screenshotFiles.push(await screenshot(page, '07-pre-submit'));

    // Click submit
    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.waitFor({ state: 'visible', timeout: 5000 });
    console.log('Submit button text:', await submitBtn.textContent());
    await submitBtn.click();
    await page.waitForTimeout(5000);
    screenshotFiles.push(await screenshot(page, '08-after-submit'));

    const finalUrl = page.url();
    const pageText = await page.evaluate(() => document.body.innerText.substring(0, 2000));
    const hasSuccess = /thank you|application received|successfully submitted|confirmation|submitted successfully/i.test(pageText);
    const hasError = /this field is required|please select|invalid/i.test(pageText);

    // Grab visible error messages
    const errors = await page.evaluate(() => {
      const errorEls = document.querySelectorAll('[class*="error"]:not([aria-hidden="true"])');
      return Array.from(errorEls)
        .map(el => el.textContent.trim())
        .filter(t => t && !t.includes('Select...'));
    });

    console.log('\n=== FINAL RESULT ===');
    console.log('URL:', finalUrl);
    console.log('Success:', hasSuccess);
    console.log('Error:', hasError);
    console.log('Errors found:', errors);
    console.log('Page text:', pageText.substring(0, 300));

    const result = {
      submitted: true,
      success: hasSuccess,
      finalUrl,
      errors,
      timestamp: new Date().toISOString(),
      screenshots: screenshotFiles
    };
    fs.writeFileSync('/home/user/Agents/data/nice-apply-result.json', JSON.stringify(result, null, 2));
    return result;

  } catch(error) {
    console.error('Error:', error.message);
    screenshotFiles.push(await screenshot(page, '99-error').catch(() => 'error-screenshot-failed'));
    const result = {
      submitted: false,
      error: error.message,
      timestamp: new Date().toISOString(),
      screenshots: screenshotFiles
    };
    fs.writeFileSync('/home/user/Agents/data/nice-apply-result.json', JSON.stringify(result, null, 2));
  } finally {
    await browser.close();
  }
}

run().catch(e => {
  console.error('Fatal:', e.message);
  process.exit(1);
});
