const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const JOB_URL = 'https://www.careers-page.com/futures-works/job/LR994VY6';
const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PDF = '/home/user/Agents/profile/Hisham Abboud CV.pdf';

const PERSONAL_DETAILS = {
  fullName: 'Hisham Abboud',
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'Hisham123@hotmail.com',
  phone: '+31 06 4841 2838',
  linkedin: 'linkedin.com/in/hisham-abboud',
  github: 'github.com/Hishamabboud',
  city: 'Eindhoven',
  country: 'Netherlands'
};

const COVER_LETTER = `Dear Futures.Works Hiring Team,

I am applying for the C# Developer position for High Tech Companies in the Eindhoven region. With professional experience in C#/.NET at Actemium (VINCI Energies) and prior internships at ASML and Delta Electronics, I bring hands-on high-tech sector experience.

At Actemium, I develop full-stack applications using C#, .NET, ASP.NET for manufacturing clients, working with Azure, CI/CD, and Scrum methodologies. My experience at ASML in Veldhoven gave me direct exposure to the high-tech semiconductor sector.

I am based in Eindhoven with a valid Dutch work permit and am fluent in both Dutch and English.

Best regards,
Hisham Abboud`;

async function takeScreenshot(page, name) {
  const filepath = path.join(SCREENSHOTS_DIR, name);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`Screenshot saved: ${filepath}`);
  return filepath;
}

async function fillTextField(page, selectors, value) {
  for (const selector of selectors) {
    try {
      const el = await page.$(selector);
      if (el) {
        await el.fill(value);
        console.log(`Filled field (${selector}) with: ${value}`);
        return true;
      }
    } catch (e) {
      // try next selector
    }
  }
  return false;
}

async function main() {
  console.log('Starting Futures.Works application...');

  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  const page = await context.newPage();

  try {
    console.log('Navigating to job page...');
    await page.goto(JOB_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    await takeScreenshot(page, 'futures-works-01-job-page.png');
    console.log('Job page loaded successfully.');

    // Look for Apply button
    console.log('Looking for Apply button...');
    const applySelectors = [
      'a:has-text("Apply for Position")',
      'a:has-text("Apply")',
      'button:has-text("Apply")',
      '[href*="apply"]',
      '.apply-btn',
      '#apply-btn'
    ];

    let clicked = false;
    for (const selector of applySelectors) {
      try {
        const el = await page.$(selector);
        if (el) {
          console.log(`Found apply button with selector: ${selector}`);
          await el.click();
          clicked = true;
          break;
        }
      } catch (e) {
        // try next
      }
    }

    if (!clicked) {
      // Try finding by text content
      const links = await page.$$('a');
      for (const link of links) {
        const text = await link.textContent();
        if (text && (text.toLowerCase().includes('apply') || text.toLowerCase().includes('sollicit'))) {
          console.log(`Found apply link with text: ${text.trim()}`);
          await link.click();
          clicked = true;
          break;
        }
      }
    }

    if (!clicked) {
      console.log('Could not find apply button. Taking screenshot of current state.');
      await takeScreenshot(page, 'futures-works-error-no-apply-btn.png');

      // Log page content for debugging
      const content = await page.content();
      fs.writeFileSync('/home/user/Agents/output/screenshots/futures-works-page-debug.html', content);
      console.log('Page HTML saved for debugging.');
      await browser.close();
      return;
    }

    await page.waitForTimeout(3000);
    await takeScreenshot(page, 'futures-works-02-apply-form.png');
    console.log('Application form loaded.');

    // Check current URL
    const currentUrl = page.url();
    console.log(`Current URL: ${currentUrl}`);

    // Get all form fields on the page
    const formFields = await page.$$eval('input, textarea, select', (elements) => {
      return elements.map(el => ({
        tag: el.tagName,
        type: el.type,
        name: el.name,
        id: el.id,
        placeholder: el.placeholder,
        label: el.getAttribute('aria-label'),
        className: el.className
      }));
    });
    console.log('Form fields found:', JSON.stringify(formFields, null, 2));

    // Fill in the form fields
    console.log('Filling in form fields...');

    // Name fields
    await fillTextField(page, [
      'input[name="name"]',
      'input[name="full_name"]',
      'input[name="fullName"]',
      'input[id*="name" i]:not([id*="last" i]):not([id*="sur" i])',
      'input[placeholder*="name" i]:not([placeholder*="last" i])',
      'input[placeholder*="Name" i]'
    ], PERSONAL_DETAILS.fullName);

    await fillTextField(page, [
      'input[name="first_name"]',
      'input[name="firstName"]',
      'input[id*="first" i]',
      'input[placeholder*="first" i]',
      'input[placeholder*="First" i]'
    ], PERSONAL_DETAILS.firstName);

    await fillTextField(page, [
      'input[name="last_name"]',
      'input[name="lastName"]',
      'input[id*="last" i]',
      'input[placeholder*="last" i]',
      'input[placeholder*="Last" i]',
      'input[placeholder*="surname" i]'
    ], PERSONAL_DETAILS.lastName);

    // Email
    await fillTextField(page, [
      'input[type="email"]',
      'input[name="email"]',
      'input[id*="email" i]',
      'input[placeholder*="email" i]'
    ], PERSONAL_DETAILS.email);

    // Phone
    await fillTextField(page, [
      'input[type="tel"]',
      'input[name="phone"]',
      'input[name="telephone"]',
      'input[id*="phone" i]',
      'input[placeholder*="phone" i]',
      'input[placeholder*="tel" i]'
    ], PERSONAL_DETAILS.phone);

    // LinkedIn
    await fillTextField(page, [
      'input[name="linkedin"]',
      'input[id*="linkedin" i]',
      'input[placeholder*="linkedin" i]',
      'input[placeholder*="LinkedIn" i]'
    ], PERSONAL_DETAILS.linkedin);

    // GitHub
    await fillTextField(page, [
      'input[name="github"]',
      'input[id*="github" i]',
      'input[placeholder*="github" i]',
      'input[placeholder*="GitHub" i]'
    ], PERSONAL_DETAILS.github);

    // City / Location
    await fillTextField(page, [
      'input[name="city"]',
      'input[name="location"]',
      'input[id*="city" i]',
      'input[placeholder*="city" i]',
      'input[placeholder*="City" i]'
    ], PERSONAL_DETAILS.city);

    // Cover Letter / Message
    const coverLetterFilled = await fillTextField(page, [
      'textarea[name="cover_letter"]',
      'textarea[name="coverLetter"]',
      'textarea[name="message"]',
      'textarea[name="motivation"]',
      'textarea[id*="cover" i]',
      'textarea[id*="message" i]',
      'textarea[id*="motivation" i]',
      'textarea[placeholder*="cover" i]',
      'textarea[placeholder*="letter" i]',
      'textarea[placeholder*="message" i]',
      'textarea[placeholder*="motivation" i]',
      'textarea'
    ], COVER_LETTER);

    if (coverLetterFilled) {
      console.log('Cover letter filled successfully.');
    } else {
      console.log('No cover letter textarea found.');
    }

    // File upload for resume
    const fileInputs = await page.$$('input[type="file"]');
    if (fileInputs.length > 0) {
      console.log(`Found ${fileInputs.length} file input(s). Uploading resume...`);
      await fileInputs[0].setInputFiles(RESUME_PDF);
      console.log('Resume uploaded successfully.');
      await page.waitForTimeout(2000);
    } else {
      console.log('No file upload field found.');
    }

    await page.waitForTimeout(1000);
    await takeScreenshot(page, 'futures-works-03-form-filled.png');
    console.log('Form filled. Taking pre-submit screenshot.');

    // Check for any remaining required fields
    const requiredFields = await page.$$eval('input[required], textarea[required], select[required]', els =>
      els.map(el => ({ tag: el.tagName, name: el.name, id: el.id, value: el.value }))
    );
    console.log('Required fields status:', JSON.stringify(requiredFields, null, 2));

    // Look for submit button
    console.log('Looking for submit button...');
    const submitSelectors = [
      'button[type="submit"]',
      'input[type="submit"]',
      'button:has-text("Submit")',
      'button:has-text("Apply")',
      'button:has-text("Send")',
      '.submit-btn',
      '#submit-btn'
    ];

    let submitBtn = null;
    for (const selector of submitSelectors) {
      try {
        submitBtn = await page.$(selector);
        if (submitBtn) {
          console.log(`Found submit button with selector: ${selector}`);
          break;
        }
      } catch (e) {
        // try next
      }
    }

    if (!submitBtn) {
      // Try finding by text content
      const buttons = await page.$$('button');
      for (const btn of buttons) {
        const text = await btn.textContent();
        if (text && (text.toLowerCase().includes('submit') || text.toLowerCase().includes('apply') || text.toLowerCase().includes('send'))) {
          submitBtn = btn;
          console.log(`Found submit button with text: ${text.trim()}`);
          break;
        }
      }
    }

    if (submitBtn) {
      console.log('Clicking submit button...');
      await submitBtn.click();
      await page.waitForTimeout(5000);
      await takeScreenshot(page, 'futures-works-04-after-submit.png');
      console.log('Application submitted. Post-submit screenshot taken.');

      const finalUrl = page.url();
      console.log(`Final URL: ${finalUrl}`);

      // Check for success/confirmation messages
      const pageText = await page.innerText('body');
      if (pageText.toLowerCase().includes('thank') ||
          pageText.toLowerCase().includes('success') ||
          pageText.toLowerCase().includes('received') ||
          pageText.toLowerCase().includes('bedankt') ||
          pageText.toLowerCase().includes('ontvangen')) {
        console.log('SUCCESS: Application appears to have been submitted successfully!');
      } else {
        console.log('Page text after submit (first 500 chars):', pageText.substring(0, 500));
      }
    } else {
      console.log('WARNING: Could not find submit button!');
      await takeScreenshot(page, 'futures-works-04-no-submit-btn.png');
    }

  } catch (error) {
    console.error('Error during application:', error);
    await takeScreenshot(page, 'futures-works-error.png').catch(() => {});
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
