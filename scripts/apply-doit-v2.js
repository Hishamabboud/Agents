const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';
const JOB_URL = 'https://job-boards.greenhouse.io/doitintl/jobs/7136305003';

const CANDIDATE = {
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31 06 4841 2838',
  linkedin: 'https://linkedin.com/in/hisham-abboud',
  github: 'https://github.com/Hishamabboud',
  resumePath: '/home/user/Agents/profile/Hisham Abboud CV.pdf',
};

const COVER_LETTER_PATH = '/home/user/Agents/output/cover-letters/doit-fullstack-engineer.md';

// Parse proxy from env
function getProxyConfig() {
  const proxyEnv = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || '';
  const m = proxyEnv.match(/http:\/\/([^:]+):([^@]+)@([^:]+):(\d+)/);
  if (m) {
    return { server: 'http://' + m[3] + ':' + m[4], username: m[1], password: m[2] };
  }
  return null;
}

async function run() {
  const proxyConfig = getProxyConfig();
  console.log('Proxy:', proxyConfig ? proxyConfig.server : 'none');

  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    proxy: proxyConfig || undefined,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  try {
    // === STEP 1: Load job page ===
    console.log('Loading job page...');
    const response = await page.goto(JOB_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    console.log('HTTP status:', response ? response.status() : 'no response');
    await page.waitForTimeout(2000);

    const title = await page.title();
    const bodyText = await page.textContent('body');
    console.log('Page title:', title);
    console.log('Body text length:', bodyText.length);

    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'doit-01-job-page.png'), fullPage: true });
    console.log('Screenshot 01 saved');

    fs.writeFileSync('/home/user/Agents/data/doit-job-description.txt', bodyText.substring(0, 8000));

    // === STEP 2: Inspect form structure ===
    const formFields = await page.evaluate(() => {
      const fields = [];
      document.querySelectorAll('input, textarea, select').forEach(el => {
        const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim() : '';
        fields.push({
          tag: el.tagName,
          type: el.type || '',
          id: el.id || '',
          name: el.name || '',
          placeholder: el.placeholder || '',
          label: label,
          visible: el.offsetParent !== null
        });
      });
      return fields;
    });

    console.log('\n=== FORM FIELDS ===');
    formFields.forEach(f => {
      console.log(`  [${f.tag}/${f.type}] id="${f.id}" name="${f.name}" label="${f.label}" placeholder="${f.placeholder}" visible=${f.visible}`);
    });

    fs.writeFileSync('/home/user/Agents/data/doit-form-fields.json', JSON.stringify(formFields, null, 2));

    // === STEP 3: Check for Apply button ===
    const applyBtn = await page.$('a[href*="apply"], button:text("Apply"), a:text("Apply for this Job"), a:text("Apply Now")');
    if (applyBtn) {
      const href = await applyBtn.getAttribute('href');
      const text = await applyBtn.textContent();
      console.log('Apply button found:', text.trim(), 'href:', href);
      await applyBtn.click();
      await page.waitForTimeout(3000);
      console.log('After click URL:', page.url());
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'doit-02-apply-clicked.png'), fullPage: true });
    } else {
      console.log('No separate Apply button — form may be on this page');
    }

    // === STEP 4: Fill standard Greenhouse fields ===
    const fillField = async (selectors, value, label) => {
      for (const sel of selectors) {
        const el = await page.$(sel);
        if (el) {
          const visible = await el.isVisible();
          if (visible) {
            await el.click({ clickCount: 3 });
            await el.type(value, { delay: 20 });
            console.log(`Filled ${label} using ${sel}`);
            return true;
          }
        }
      }
      console.log(`WARNING: Could not fill ${label}`);
      return false;
    };

    await fillField(['input#first_name', 'input[name="job_application[first_name]"]', 'input[placeholder*="First"]'], CANDIDATE.firstName, 'first_name');
    await fillField(['input#last_name', 'input[name="job_application[last_name]"]', 'input[placeholder*="Last"]'], CANDIDATE.lastName, 'last_name');
    await fillField(['input#email', 'input[name="job_application[email]"]', 'input[type="email"]'], CANDIDATE.email, 'email');
    await fillField(['input#phone', 'input[name="job_application[phone]"]', 'input[type="tel"]', 'input[placeholder*="Phone"]'], CANDIDATE.phone, 'phone');

    // LinkedIn
    await fillField(
      ['input[id*="linkedin"]', 'input[name*="linkedin"]', 'input[placeholder*="LinkedIn"]', 'input[placeholder*="linkedin"]'],
      CANDIDATE.linkedin, 'linkedin'
    );

    // GitHub / website
    await fillField(
      ['input[id*="github"]', 'input[name*="github"]', 'input[placeholder*="GitHub"]', 'input[id*="website"]', 'input[placeholder*="Website"]', 'input[placeholder*="portfolio"]'],
      CANDIDATE.github, 'github/website'
    );

    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'doit-03-basic-fields.png'), fullPage: true });

    // === STEP 5: Upload resume ===
    const resumeInput = await page.$('input[type="file"][name*="resume"], input#resume, input[id*="resume"], input[type="file"]');
    if (resumeInput) {
      await resumeInput.setInputFiles(CANDIDATE.resumePath);
      console.log('Resume uploaded');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'doit-04-resume-uploaded.png'), fullPage: true });
    } else {
      console.log('WARNING: No file input found for resume');
    }

    // === STEP 6: Scroll down and check full form ===
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'doit-05-midform.png'), fullPage: true });

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'doit-06-bottom.png'), fullPage: true });

    // Check for remaining empty text fields
    const emptyFields = await page.evaluate(() => {
      const result = [];
      document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], textarea').forEach(el => {
        if (!el.value || el.value.trim() === '') {
          const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim() : '';
          result.push({ id: el.id, name: el.name, placeholder: el.placeholder, label });
        }
      });
      return result;
    });
    console.log('Empty fields remaining:', JSON.stringify(emptyFields));

    // === STEP 7: Final screenshot before submit ===
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'doit-07-before-submit.png'), fullPage: true });
    console.log('Pre-submit screenshot saved');

    // Log all buttons
    const buttons = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"]')).map(b => ({
        tag: b.tagName, type: b.type || '', text: b.textContent.trim().substring(0, 80), value: b.value || ''
      }));
    });
    console.log('Buttons on page:', JSON.stringify(buttons));

    // === STEP 8: Submit ===
    const submitBtn = await page.$('input[type="submit"], button[type="submit"]');
    if (submitBtn) {
      const btnText = await submitBtn.textContent().catch(() => '');
      const btnVal = await submitBtn.getAttribute('value').catch(() => '');
      console.log('Submit button text:', btnText || btnVal);

      console.log('Submitting...');
      await submitBtn.click();
      await page.waitForTimeout(5000);

      const postUrl = page.url();
      const postTitle = await page.title();
      const postText = await page.textContent('body');
      console.log('Post-submit URL:', postUrl);
      console.log('Post-submit title:', postTitle);
      console.log('Post-submit text (first 500):', postText.substring(0, 500));

      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'doit-08-submitted.png'), fullPage: true });

      const successWords = ['thank', 'received', 'submitted', 'success', 'confirm'];
      const isSuccess = successWords.some(w => postText.toLowerCase().includes(w));
      console.log('SUCCESS:', isSuccess);

      const result = { success: isSuccess, postUrl, postTitle, message: postText.substring(0, 300) };
      fs.writeFileSync('/home/user/Agents/data/doit-apply-result.json', JSON.stringify(result, null, 2));
      return result;
    } else {
      console.log('No submit button found');
      const result = { success: false, error: 'No submit button found', postUrl: page.url() };
      fs.writeFileSync('/home/user/Agents/data/doit-apply-result.json', JSON.stringify(result, null, 2));
      return result;
    }

  } catch (err) {
    console.error('Error:', err.message);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'doit-99-error.png'), fullPage: true }).catch(() => {});
    const result = { success: false, error: err.message };
    fs.writeFileSync('/home/user/Agents/data/doit-apply-result.json', JSON.stringify(result, null, 2));
    return result;
  } finally {
    await browser.close();
  }
}

run().then(r => {
  console.log('\n=== RESULT ===');
  console.log(JSON.stringify(r, null, 2));
}).catch(e => {
  console.error('Fatal:', e.message);
  process.exit(1);
});
