/**
 * Athora Netherlands - LLM/MLOps Engineer Application
 * Uses Playwright to navigate the Recruitee JS-rendered application form
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CANDIDATE = {
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31 06 4841 2838',
  linkedin: 'https://linkedin.com/in/hisham-abboud',
  github: 'https://github.com/Hishamabboud',
  city: 'Eindhoven',
  country: 'Netherlands',
};

const COVER_LETTER_PATH = '/home/user/Agents/output/cover-letters/athora-llm-mlops-engineer.md';
const RESUME_PDF_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';

const JOB_URL = 'https://athora.recruitee.com/o/llm-mlops-engineer';
const APPLY_URL = 'https://athora.recruitee.com/o/llm-mlops-engineer/applications/new';

function screenshot_name(label) {
  const ts = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_').slice(0, 19);
  return path.join(SCREENSHOTS_DIR, `athora-llm-mlops-${label}-${ts}.png`);
}

function read_cover_letter() {
  const content = fs.readFileSync(COVER_LETTER_PATH, 'utf8');
  // Strip markdown formatting for plain text fields
  return content
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/---+/g, '')
    .trim();
}

async function take_screenshot(page, label) {
  const filepath = screenshot_name(label);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`Screenshot saved: ${filepath}`);
  return filepath;
}

async function run() {
  console.log('Starting Athora LLM/MLOps Engineer application...');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    locale: 'en-US',
  });

  const page = await context.newPage();
  const result = {
    status: 'failed',
    screenshot: null,
    notes: '',
  };

  try {
    // Step 1: Try the job URL first
    console.log(`Navigating to job URL: ${JOB_URL}`);
    const response = await page.goto(JOB_URL, { waitUntil: 'networkidle', timeout: 30000 });
    const status = response ? response.status() : 0;
    console.log(`HTTP status: ${status}`);
    const title = await page.title();
    console.log(`Page title: ${title}`);
    const url_after = page.url();
    console.log(`URL after navigation: ${url_after}`);

    await take_screenshot(page, '01-job-url');

    // Check if we landed on the job page or were redirected
    const page_text = await page.innerText('body').catch(() => '');
    const is_job_page = page_text.toLowerCase().includes('llm') ||
                        page_text.toLowerCase().includes('mlops') ||
                        page_text.toLowerCase().includes('apply');
    const is_404 = page_text.toLowerCase().includes('not found') ||
                   page_text.toLowerCase().includes('404') ||
                   status === 404;

    console.log(`Is job page: ${is_job_page}, Is 404: ${is_404}`);

    if (!is_job_page || is_404) {
      result.notes = `Job URL returns 404 or redirects - listing appears to be closed/removed. HTTP ${status}. Title: "${title}"`;
      result.status = 'failed';
      console.log(result.notes);
      await take_screenshot(page, '02-not-found');
      await browser.close();
      return result;
    }

    // Step 2: Click Apply button
    console.log('Looking for Apply button...');
    await page.waitForTimeout(2000);
    const apply_btn = await page.$('a[href*="applications/new"], button:has-text("Apply"), a:has-text("Apply"), button:has-text("Solliciteer"), a:has-text("Solliciteer")');

    if (!apply_btn) {
      // Try navigating directly to the application form
      console.log('No apply button found, navigating directly to application form...');
      await page.goto(APPLY_URL, { waitUntil: 'networkidle', timeout: 30000 });
    } else {
      await apply_btn.click();
      await page.waitForLoadState('networkidle');
    }

    await take_screenshot(page, '02-apply-form');
    const form_url = page.url();
    console.log(`Form URL: ${form_url}`);

    // Step 3: Wait for form to load
    await page.waitForTimeout(2000);

    // Check for hCaptcha
    const has_captcha = await page.$('iframe[src*="hcaptcha"], iframe[src*="recaptcha"], .h-captcha, #h-captcha');
    if (has_captcha) {
      result.notes = 'CAPTCHA detected on application form - cannot proceed automatically';
      result.status = 'failed';
      await take_screenshot(page, '03-captcha-detected');
      console.log('CAPTCHA detected - marking as failed');
      await browser.close();
      return result;
    }

    // Step 4: Fill in the form
    console.log('Filling in application form...');
    const cover_letter_text = read_cover_letter();

    // Common Recruitee form field selectors
    const field_map = [
      { selectors: ['input[name*="first_name"]', 'input[placeholder*="First name"]', 'input[id*="first_name"]'], value: CANDIDATE.firstName },
      { selectors: ['input[name*="last_name"]', 'input[placeholder*="Last name"]', 'input[id*="last_name"]'], value: CANDIDATE.lastName },
      { selectors: ['input[name*="email"]', 'input[type="email"]', 'input[placeholder*="email"]'], value: CANDIDATE.email },
      { selectors: ['input[name*="phone"]', 'input[type="tel"]', 'input[placeholder*="phone"]', 'input[placeholder*="Phone"]'], value: CANDIDATE.phone },
      { selectors: ['input[name*="linkedin"]', 'input[placeholder*="LinkedIn"]', 'input[placeholder*="linkedin"]'], value: CANDIDATE.linkedin },
      { selectors: ['input[name*="github"]', 'input[placeholder*="GitHub"]', 'input[placeholder*="github"]'], value: CANDIDATE.github },
      { selectors: ['textarea[name*="cover_letter"]', 'textarea[placeholder*="cover"]', 'textarea[name*="message"]', 'textarea[placeholder*="letter"]'], value: cover_letter_text },
    ];

    for (const field of field_map) {
      for (const selector of field.selectors) {
        const el = await page.$(selector);
        if (el) {
          await el.click({ clickCount: 3 });
          await el.fill(field.value);
          console.log(`Filled: ${selector}`);
          break;
        }
      }
    }

    await take_screenshot(page, '03-fields-filled');

    // Step 5: Upload resume PDF
    console.log('Uploading resume PDF...');
    if (fs.existsSync(RESUME_PDF_PATH)) {
      const file_input = await page.$('input[type="file"]');
      if (file_input) {
        await file_input.setInputFiles(RESUME_PDF_PATH);
        console.log('Resume uploaded');
        await page.waitForTimeout(2000);
        await take_screenshot(page, '04-resume-uploaded');
      } else {
        console.log('No file input found');
      }
    } else {
      console.log(`Resume PDF not found at: ${RESUME_PDF_PATH}`);
    }

    // Step 6: Handle any additional questions
    await page.waitForTimeout(1000);

    // Check for yes/no or dropdown questions about experience
    const selects = await page.$$('select');
    for (const select of selects) {
      const label_text = await page.evaluate(el => {
        const label = document.querySelector(`label[for="${el.id}"]`);
        return label ? label.textContent : '';
      }, select);
      console.log(`Select field label: "${label_text}"`);
    }

    // Step 7: Screenshot before submit
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    const pre_submit_shot = await take_screenshot(page, '05-pre-submit');
    result.screenshot = pre_submit_shot;

    // Step 8: Find and click submit
    const submit_btn = await page.$(
      'button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Send"), button:has-text("Apply"), button:has-text("Versturen"), button:has-text("Solliciteer")'
    );

    if (!submit_btn) {
      result.notes = 'Form loaded and filled but no submit button found';
      result.status = 'failed';
      console.log(result.notes);
      await browser.close();
      return result;
    }

    const btn_text = await submit_btn.innerText().catch(() => 'unknown');
    console.log(`Submit button text: "${btn_text}"`);
    console.log('Clicking submit...');
    await submit_btn.click();
    await page.waitForTimeout(3000);

    await take_screenshot(page, '06-post-submit');
    const post_url = page.url();
    const post_text = await page.innerText('body').catch(() => '');
    console.log(`Post-submit URL: ${post_url}`);

    const success_indicators = ['thank', 'bedankt', 'confirmation', 'received', 'successfully', 'success', 'ontvangen'];
    const is_success = success_indicators.some(word => post_text.toLowerCase().includes(word));
    const has_error = post_text.toLowerCase().includes('error') || post_text.toLowerCase().includes('invalid');

    if (is_success) {
      result.status = 'applied';
      result.notes = `Application submitted successfully. Post-submit URL: ${post_url}`;
      console.log('SUCCESS: Application submitted');
    } else if (has_error) {
      result.status = 'failed';
      result.notes = `Errors on form after submit. Post-submit URL: ${post_url}. Content snippet: ${post_text.slice(0, 200)}`;
      console.log('Form errors detected');
    } else {
      result.status = 'applied';
      result.notes = `Form submitted (no explicit error). Post-submit URL: ${post_url}`;
      console.log('Form submitted (no error detected, assuming success)');
    }

  } catch (err) {
    result.status = 'failed';
    result.notes = `Exception: ${err.message}`;
    console.error('Error:', err.message);
    await take_screenshot(page, '99-error').catch(() => {});
  }

  await browser.close();
  return result;
}

run().then(result => {
  console.log('\n=== RESULT ===');
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.status === 'applied' ? 0 : 1);
}).catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
