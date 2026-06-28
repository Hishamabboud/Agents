const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SCREENSHOT_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const COVER_LETTER_PATH = '/home/user/Agents/output/cover-letters/nice-csharp-engineer.md';
const APPLICATION_URL = 'https://job-boards.eu.greenhouse.io/nice/jobs/4826064101';

const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);

async function screenshot(page, label) {
  const filename = `nice-csharp-engineer-${label}-${timestamp}.png`;
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`Screenshot saved: ${filepath}`);
  return filepath;
}

async function run() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  try {
    console.log('Navigating to Greenhouse application page...');
    await page.goto(APPLICATION_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await screenshot(page, '01-page-loaded');

    console.log('Page title:', await page.title());
    console.log('URL:', page.url());

    // Wait for form to be present
    await page.waitForSelector('form#application_form, form[action*="application"], #application-form, form', { timeout: 15000 });
    await screenshot(page, '02-form-visible');

    // Fill in first name
    const firstNameSelectors = ['#first_name', 'input[name="first_name"]', 'input[id*="first"]', 'input[placeholder*="First"]'];
    for (const sel of firstNameSelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          await el.fill('Hisham');
          console.log(`Filled first name with selector: ${sel}`);
          break;
        }
      } catch(e) {}
    }

    // Fill in last name
    const lastNameSelectors = ['#last_name', 'input[name="last_name"]', 'input[id*="last"]', 'input[placeholder*="Last"]'];
    for (const sel of lastNameSelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          await el.fill('Abboud');
          console.log(`Filled last name with selector: ${sel}`);
          break;
        }
      } catch(e) {}
    }

    // Fill in email
    const emailSelectors = ['#email', 'input[name="email"]', 'input[type="email"]', 'input[id*="email"]'];
    for (const sel of emailSelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          await el.fill('hiaham123@hotmail.com');
          console.log(`Filled email with selector: ${sel}`);
          break;
        }
      } catch(e) {}
    }

    // Fill in phone
    const phoneSelectors = ['#phone', 'input[name="phone"]', 'input[type="tel"]', 'input[id*="phone"]'];
    for (const sel of phoneSelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          await el.fill('+31 06 4841 2838');
          console.log(`Filled phone with selector: ${sel}`);
          break;
        }
      } catch(e) {}
    }

    // Fill in LinkedIn
    const linkedinSelectors = ['input[name="linkedin_profile"]', 'input[id*="linkedin"]', 'input[placeholder*="LinkedIn"]', 'input[name*="linkedin"]'];
    for (const sel of linkedinSelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          await el.fill('https://linkedin.com/in/hisham-abboud');
          console.log(`Filled LinkedIn with selector: ${sel}`);
          break;
        }
      } catch(e) {}
    }

    await screenshot(page, '03-basic-fields-filled');

    // Handle country dropdown (if present)
    // Greenhouse often uses a select for country
    try {
      const countrySelect = await page.$('select[name="country"]');
      if (countrySelect) {
        await countrySelect.selectOption({ label: 'Netherlands' });
        console.log('Selected Netherlands for country');
      }
    } catch(e) {
      console.log('Country select not found or already set:', e.message);
    }

    // Upload resume
    console.log('Attempting to upload resume PDF...');
    try {
      // Greenhouse file input
      const fileInputSelectors = [
        'input[type="file"]',
        '#resume',
        'input[name="resume"]',
        'input[accept*="pdf"]'
      ];
      let uploaded = false;
      for (const sel of fileInputSelectors) {
        try {
          const fileInput = await page.$(sel);
          if (fileInput) {
            await fileInput.setInputFiles(RESUME_PATH);
            console.log(`Resume uploaded with selector: ${sel}`);
            uploaded = true;
            await page.waitForTimeout(2000);
            break;
          }
        } catch(e) {}
      }
      if (!uploaded) {
        console.log('Could not find file input for resume upload');
      }
    } catch(e) {
      console.log('Resume upload error:', e.message);
    }

    await screenshot(page, '04-after-upload');

    // Handle custom questions (Greenhouse "questions" section)
    // These are usually radio buttons or dropdowns for yes/no questions

    // "Do you have first-degree relatives employed by NICE?" - should be No
    try {
      const relativeQuestion = await page.$('input[value="No"][name*="relative"], input[value="no"][name*="relative"]');
      if (relativeQuestion) {
        await relativeQuestion.click();
        console.log('Selected No for relatives question');
      } else {
        // Try to find by label text
        const labels = await page.$$eval('label', els => els.map(e => ({ text: e.textContent.trim(), forAttr: e.getAttribute('for') })));
        const relLabel = labels.find(l => l.text.toLowerCase().includes('relative') || l.text.toLowerCase().includes('first-degree'));
        if (relLabel && relLabel.forAttr) {
          // Look for No option nearby
          const noInput = await page.$(`#${relLabel.forAttr}`);
          if (noInput) await noInput.click();
        }
      }
    } catch(e) {
      console.log('Could not find relatives question:', e.message);
    }

    // "Have you ever worked at NICE?" - should be No
    try {
      // Look for radio buttons with "No" near "worked at NICE"
      const allRadios = await page.$$('input[type="radio"]');
      for (const radio of allRadios) {
        const value = await radio.getAttribute('value');
        const id = await radio.getAttribute('id');
        if (value && value.toLowerCase() === 'no') {
          // Check surrounding text
          const labelText = await page.$eval(`label[for="${id}"]`, el => el.textContent).catch(() => '');
          if (labelText.toLowerCase().includes('no')) {
            // Get question text from parent
            const questionText = await page.evaluate(el => {
              const parent = el.closest('.field, .question, [class*="field"], [class*="question"]');
              return parent ? parent.textContent.substring(0, 200) : '';
            }, radio).catch(() => '');
            if (questionText.toLowerCase().includes('nice') || questionText.toLowerCase().includes('relative') || questionText.toLowerCase().includes('visa')) {
              await radio.click();
              console.log(`Clicked No radio for question: ${questionText.substring(0, 80)}`);
            }
          }
        }
      }
    } catch(e) {
      console.log('Radio button handling error:', e.message);
    }

    // Handle AI-assisted software development experience question (open text)
    try {
      const textareas = await page.$$('textarea');
      for (const ta of textareas) {
        const placeholder = await ta.getAttribute('placeholder') || '';
        const id = await ta.getAttribute('id') || '';
        const name = await ta.getAttribute('name') || '';
        if (placeholder.toLowerCase().includes('ai') || id.toLowerCase().includes('ai') || name.toLowerCase().includes('ai') || placeholder === '') {
          // Get surrounding label
          const labelText = await page.evaluate(el => {
            const label = document.querySelector(`label[for="${el.id}"]`);
            if (label) return label.textContent;
            const parent = el.closest('.field, .form-field, [class*="field"]');
            return parent ? parent.querySelector('label, .label, p')?.textContent || '' : '';
          }, ta).catch(() => '');

          if (labelText.toLowerCase().includes('ai') || labelText === '') {
            await ta.fill('I use AI coding assistants daily as a core part of my development workflow. I work with Claude Code, GitHub Copilot, and Cursor regularly — both for code generation and for evaluating and improving AI-generated output. Through CogitatAI, my AI customer support platform, I have integrated LLM APIs directly and designed prompt engineering workflows for production use. I approach AI tools as collaborative development partners rather than shortcuts, and I actively refine prompts and review outputs critically.');
            console.log(`Filled textarea for AI question: ${labelText.substring(0, 80)}`);
          }
        }
      }
    } catch(e) {
      console.log('Textarea handling error:', e.message);
    }

    await screenshot(page, '05-all-fields-filled');

    // Handle remaining Greenhouse specific questions
    // Let's dump the current form state to understand what's on the page
    const formHTML = await page.evaluate(() => {
      const form = document.querySelector('form#application_form, form[action*="application"], form');
      return form ? form.innerHTML.substring(0, 5000) : document.body.innerHTML.substring(0, 3000);
    });
    console.log('Form HTML snippet:', formHTML.substring(0, 2000));

    await screenshot(page, '06-pre-submit');

    // Try to find and fill any remaining required fields
    // Get all visible required inputs that are empty
    const emptyRequired = await page.$$eval(
      'input[required]:not([type="hidden"]):not([type="file"]), select[required], textarea[required]',
      els => els.map(el => ({
        tag: el.tagName,
        type: el.type || '',
        name: el.name || '',
        id: el.id || '',
        value: el.value || '',
        placeholder: el.placeholder || ''
      }))
    );
    console.log('Empty/required fields:', JSON.stringify(emptyRequired, null, 2));

    // Take final screenshot before submit
    await screenshot(page, '07-final-pre-submit');

    // Find and click submit button
    console.log('Looking for submit button...');
    const submitSelectors = [
      'input[type="submit"]',
      'button[type="submit"]',
      'button:has-text("Submit Application")',
      'button:has-text("Apply")',
      'button:has-text("Submit")',
      '#submit_app',
      'input[value="Submit Application"]'
    ];

    let submitted = false;
    for (const sel of submitSelectors) {
      try {
        const btn = await page.$(sel);
        if (btn) {
          const btnText = await btn.evaluate(el => el.textContent || el.value || '');
          console.log(`Found submit button: "${btnText}" with selector: ${sel}`);
          // Take screenshot right before clicking
          await screenshot(page, '08-about-to-submit');
          await btn.click();
          console.log('Submit button clicked!');
          await page.waitForTimeout(3000);
          await screenshot(page, '09-after-submit');
          submitted = true;
          break;
        }
      } catch(e) {}
    }

    if (!submitted) {
      console.log('Could not find submit button');
      await screenshot(page, '99-no-submit-button');
    }

    // Check for success/error
    const finalUrl = page.url();
    const pageContent = await page.content();
    const hasSuccess = /thank you|application received|successfully submitted|confirmation/i.test(pageContent);
    const hasError = /error|required|please fill|invalid/i.test(pageContent);

    console.log('Final URL:', finalUrl);
    console.log('Has success message:', hasSuccess);
    console.log('Has error message:', hasError);

    // Save result
    const result = {
      submitted,
      finalUrl,
      hasSuccess,
      hasError,
      timestamp: new Date().toISOString()
    };
    fs.writeFileSync('/home/user/Agents/data/nice-apply-result.json', JSON.stringify(result, null, 2));
    console.log('Result:', JSON.stringify(result, null, 2));

  } catch(error) {
    console.error('Error during application:', error.message);
    await screenshot(page, '99-error').catch(() => {});
    throw error;
  } finally {
    await browser.close();
  }
}

run().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});
