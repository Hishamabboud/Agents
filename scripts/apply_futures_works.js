const path = require('path');
const fs = require('fs');

const JOB_URL = 'https://www.careers-page.com/futures-works/job/LR994VY6';
const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PDF = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const CHROMIUM_PATH = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';

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

async function tryFillField(page, selectors, value) {
  for (const selector of selectors) {
    try {
      const el = await page.$(selector);
      if (el) {
        const isVisible = await el.isVisible();
        if (isVisible) {
          await el.fill(value);
          console.log(`  Filled field [${selector}] with: "${value}"`);
          return true;
        }
      }
    } catch (e) {
      // try next selector
    }
  }
  return false;
}

async function logFormStructure(page) {
  const elements = await page.$$eval(
    'input:not([type="hidden"]), textarea, select, label, [class*="field"], [class*="form"]',
    els => els.map(el => ({
      tag: el.tagName,
      type: el.type || '',
      name: el.name || '',
      id: el.id || '',
      placeholder: el.placeholder || '',
      ariaLabel: el.getAttribute('aria-label') || '',
      className: el.className || '',
      textContent: el.tagName === 'LABEL' ? el.textContent.trim().substring(0, 50) : ''
    }))
  );
  console.log('Form elements found:');
  elements.forEach(el => console.log(' ', JSON.stringify(el)));
  return elements;
}

async function main() {
  console.log('=== Futures.Works C# Developer Application ===');
  console.log('Starting application process...\n');

  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }

  if (!fs.existsSync(RESUME_PDF)) {
    console.error(`Resume PDF not found at: ${RESUME_PDF}`);
    process.exit(1);
  }

  // Use the global playwright which supports executablePath override
  const { chromium } = require('/opt/node22/lib/node_modules/playwright');

  const browser = await chromium.launch({
    executablePath: CHROMIUM_PATH,
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled',
      '--disable-web-security',
      '--ignore-certificate-errors'
    ]
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  // Capture console messages from page
  page.on('console', msg => {
    if (msg.type() === 'error') console.log(`[Page Error] ${msg.text()}`);
  });

  try {
    // Step 1: Navigate to job page
    console.log('Step 1: Navigating to job page...');
    console.log(`URL: ${JOB_URL}`);

    await page.goto(JOB_URL, {
      waitUntil: 'domcontentloaded',
      timeout: 45000
    });

    await page.waitForTimeout(3000);
    await takeScreenshot(page, 'futures-works-01-job-page.png');

    const pageTitle = await page.title();
    console.log(`Page title: ${pageTitle}`);

    // Step 2: Find and click Apply button
    console.log('\nStep 2: Looking for Apply button...');

    // Log all links and buttons
    const allButtons = await page.$$eval('a, button', els =>
      els.map(el => ({
        tag: el.tagName,
        text: el.textContent.trim().substring(0, 80),
        href: el.href || '',
        className: el.className || ''
      })).filter(el => el.text.length > 0)
    );
    console.log('All clickable elements:');
    allButtons.forEach(btn => console.log(' ', JSON.stringify(btn)));

    let clicked = false;

    // Try direct link navigation first
    const applyLinks = await page.$$('a[href*="apply"], a[href*="sollicit"]');
    for (const link of applyLinks) {
      const href = await link.getAttribute('href');
      const text = await link.textContent();
      console.log(`Found apply link: "${text.trim()}" -> ${href}`);
      await link.click();
      clicked = true;
      break;
    }

    if (!clicked) {
      // Try text matching
      const applyBtnTexts = ['Apply for Position', 'Apply for this position', 'Apply Now', 'Apply', 'Solliciteer'];
      for (const btnText of applyBtnTexts) {
        try {
          await page.click(`text="${btnText}"`, { timeout: 3000 });
          console.log(`Clicked button with text: "${btnText}"`);
          clicked = true;
          break;
        } catch (e) {
          // try next
        }
      }
    }

    if (!clicked) {
      console.log('WARNING: Could not find Apply button. Checking if we are already on a form page...');
      const formExists = await page.$('form');
      if (!formExists) {
        console.log('No form found and no apply button. Saving debug info...');
        const html = await page.content();
        fs.writeFileSync('/home/user/Agents/output/screenshots/futures-works-debug.html', html);
        console.log('Debug HTML saved to /home/user/Agents/output/screenshots/futures-works-debug.html');
      } else {
        console.log('Form found on current page, proceeding...');
        clicked = true;
      }
    }

    if (clicked) {
      await page.waitForTimeout(4000);
    }

    const currentUrl = page.url();
    console.log(`\nCurrent URL after click: ${currentUrl}`);
    await takeScreenshot(page, 'futures-works-02-after-apply-click.png');

    // Check if there's an iframe containing the form
    const iframes = await page.$$('iframe');
    console.log(`Found ${iframes.length} iframe(s) on page`);

    let formPage = page;

    if (iframes.length > 0) {
      for (let i = 0; i < iframes.length; i++) {
        try {
          const frame = await iframes[i].contentFrame();
          if (frame) {
            const frameUrl = frame.url();
            console.log(`Iframe ${i} URL: ${frameUrl}`);
            const frameForm = await frame.$('form, input, textarea');
            if (frameForm) {
              console.log(`Form found in iframe ${i}`);
              formPage = frame;
              break;
            }
          }
        } catch (e) {
          console.log(`Could not access iframe ${i}: ${e.message}`);
        }
      }
    }

    // Step 3: Log form structure
    console.log('\nStep 3: Analyzing form structure...');
    await logFormStructure(formPage);

    // Step 4: Fill in form fields
    console.log('\nStep 4: Filling in form fields...');

    // Name
    const nameFilled = await tryFillField(formPage, [
      'input[name="name"]',
      'input[name="full_name"]',
      'input[name="fullName"]',
      'input[id="name"]',
      'input[id="full_name"]',
      'input[id="fullName"]',
      'input[placeholder*="name" i]:not([placeholder*="last" i]):not([placeholder*="sur" i]):not([placeholder*="user" i])',
      'input[aria-label*="name" i]:not([aria-label*="last" i])',
      'input[class*="name" i]:not([class*="last" i])'
    ], PERSONAL_DETAILS.fullName);

    await tryFillField(formPage, [
      'input[name="first_name"]',
      'input[name="firstName"]',
      'input[id="first_name"]',
      'input[id="firstName"]',
      'input[placeholder*="first name" i]',
      'input[placeholder*="firstname" i]',
      'input[placeholder*="voornaam" i]',
      'input[aria-label*="first name" i]'
    ], PERSONAL_DETAILS.firstName);

    await tryFillField(formPage, [
      'input[name="last_name"]',
      'input[name="lastName"]',
      'input[name="surname"]',
      'input[id="last_name"]',
      'input[id="lastName"]',
      'input[placeholder*="last name" i]',
      'input[placeholder*="lastname" i]',
      'input[placeholder*="surname" i]',
      'input[placeholder*="achternaam" i]',
      'input[aria-label*="last name" i]'
    ], PERSONAL_DETAILS.lastName);

    // Email
    await tryFillField(formPage, [
      'input[type="email"]',
      'input[name="email"]',
      'input[id="email"]',
      'input[placeholder*="email" i]',
      'input[aria-label*="email" i]'
    ], PERSONAL_DETAILS.email);

    // Phone
    await tryFillField(formPage, [
      'input[type="tel"]',
      'input[name="phone"]',
      'input[name="telephone"]',
      'input[name="mobile"]',
      'input[id="phone"]',
      'input[id="telephone"]',
      'input[placeholder*="phone" i]',
      'input[placeholder*="tel" i]',
      'input[placeholder*="mobile" i]',
      'input[placeholder*="telefoon" i]',
      'input[placeholder*="mobiel" i]',
      'input[aria-label*="phone" i]'
    ], PERSONAL_DETAILS.phone);

    // LinkedIn
    await tryFillField(formPage, [
      'input[name="linkedin"]',
      'input[name="linkedin_url"]',
      'input[id="linkedin"]',
      'input[placeholder*="linkedin" i]',
      'input[aria-label*="linkedin" i]'
    ], PERSONAL_DETAILS.linkedin);

    // GitHub
    await tryFillField(formPage, [
      'input[name="github"]',
      'input[name="github_url"]',
      'input[id="github"]',
      'input[placeholder*="github" i]',
      'input[aria-label*="github" i]'
    ], PERSONAL_DETAILS.github);

    // City
    await tryFillField(formPage, [
      'input[name="city"]',
      'input[name="location"]',
      'input[id="city"]',
      'input[placeholder*="city" i]',
      'input[placeholder*="stad" i]',
      'input[placeholder*="location" i]',
      'input[aria-label*="city" i]'
    ], PERSONAL_DETAILS.city);

    // Cover Letter / Motivation
    const coverSelectors = [
      'textarea[name="cover_letter"]',
      'textarea[name="coverLetter"]',
      'textarea[name="motivation"]',
      'textarea[name="message"]',
      'textarea[name="body"]',
      'textarea[id="cover_letter"]',
      'textarea[id="coverLetter"]',
      'textarea[id="motivation"]',
      'textarea[id="message"]',
      'textarea[placeholder*="cover" i]',
      'textarea[placeholder*="letter" i]',
      'textarea[placeholder*="motivation" i]',
      'textarea[placeholder*="message" i]',
      'textarea[placeholder*="motivatie" i]',
      'textarea[aria-label*="cover" i]',
      'textarea[aria-label*="motivation" i]',
      'textarea'
    ];
    const coverFilled = await tryFillField(formPage, coverSelectors, COVER_LETTER);
    if (coverFilled) {
      console.log('Cover letter filled.');
    } else {
      console.log('No cover letter textarea found.');
    }

    // File upload
    console.log('\nStep 5: Handling file upload...');
    const fileInputs = await formPage.$$('input[type="file"]');
    console.log(`Found ${fileInputs.length} file input(s)`);

    if (fileInputs.length > 0) {
      for (let i = 0; i < fileInputs.length; i++) {
        try {
          await fileInputs[i].setInputFiles(RESUME_PDF);
          console.log(`Resume uploaded to file input ${i}`);
          await page.waitForTimeout(2000);
        } catch (e) {
          console.log(`Could not upload to file input ${i}: ${e.message}`);
        }
      }
    } else {
      // Try to find any upload buttons/areas
      const uploadBtns = await formPage.$$('[class*="upload"], [class*="Upload"], [data-testid*="upload"]');
      console.log(`Found ${uploadBtns.length} potential upload elements`);
    }

    await page.waitForTimeout(1500);
    await takeScreenshot(page, 'futures-works-03-form-filled.png');
    console.log('\nPre-submit screenshot taken: futures-works-03-form-filled.png');

    // Step 6: Find and click submit button
    console.log('\nStep 6: Looking for submit button...');

    const submitTexts = ['Submit', 'Apply', 'Send Application', 'Send', 'Verzenden', 'Solliciteer', 'Submit Application'];

    let submitBtn = null;
    for (const text of submitTexts) {
      try {
        submitBtn = await formPage.$(`button:has-text("${text}")`);
        if (submitBtn) {
          console.log(`Found submit button with text: "${text}"`);
          break;
        }
      } catch (e) {}
    }

    if (!submitBtn) {
      submitBtn = await formPage.$('button[type="submit"]');
      if (submitBtn) console.log('Found submit button by type="submit"');
    }

    if (!submitBtn) {
      submitBtn = await formPage.$('input[type="submit"]');
      if (submitBtn) console.log('Found submit input by type="submit"');
    }

    if (!submitBtn) {
      // Find all buttons and log them
      const allBtns = await formPage.$$eval('button', btns =>
        btns.map(b => ({ text: b.textContent.trim(), type: b.type, class: b.className }))
      );
      console.log('All buttons on form page:', JSON.stringify(allBtns));
    }

    if (submitBtn) {
      console.log('Clicking submit button...');
      await submitBtn.click();
      console.log('Submit clicked. Waiting for response...');
      await page.waitForTimeout(5000);

      await takeScreenshot(page, 'futures-works-04-after-submit.png');
      console.log('Post-submit screenshot taken: futures-works-04-after-submit.png');

      const finalUrl = page.url();
      console.log(`Final URL: ${finalUrl}`);

      // Check for success indicators
      const bodyText = await page.evaluate(() => document.body.innerText);
      console.log('\nPage text after submit (first 1000 chars):');
      console.log(bodyText.substring(0, 1000));

      const successKeywords = ['thank', 'success', 'received', 'bedankt', 'ontvangen', 'submitted', 'confirmation', 'bevestig'];
      const isSuccess = successKeywords.some(kw => bodyText.toLowerCase().includes(kw));

      if (isSuccess) {
        console.log('\nSUCCESS: Application submitted successfully!');
      } else {
        console.log('\nUncertain about submission status. Check screenshots for details.');
      }
    } else {
      console.log('WARNING: No submit button found. Taking final screenshot.');
      await takeScreenshot(page, 'futures-works-04-no-submit.png');
    }

    console.log('\n=== Application Process Complete ===');
    console.log('Screenshots saved to:', SCREENSHOTS_DIR);

  } catch (error) {
    console.error('\nError during application:', error.message);
    try {
      await takeScreenshot(page, 'futures-works-error-state.png');
    } catch (e) {}

    // Save page HTML for debugging
    try {
      const html = await page.content();
      fs.writeFileSync('/home/user/Agents/output/screenshots/futures-works-error-page.html', html);
      console.log('Error page HTML saved for debugging.');
    } catch (e) {}

    throw error;
  } finally {
    await browser.close();
    console.log('Browser closed.');
  }
}

main().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
