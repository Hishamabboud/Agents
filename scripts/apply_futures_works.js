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

// Extract proxy credentials from environment
function getProxyConfig() {
  const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || '';
  if (!proxyUrl) return null;

  try {
    const url = new URL(proxyUrl);
    return {
      server: `${url.protocol}//${url.hostname}:${url.port}`,
      username: decodeURIComponent(url.username),
      password: decodeURIComponent(url.password)
    };
  } catch (e) {
    console.log('Could not parse proxy URL:', e.message);
    return null;
  }
}

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
        const isVisible = await el.isVisible().catch(() => false);
        if (isVisible) {
          await el.fill(value);
          console.log(`  Filled [${selector.substring(0, 60)}] with: "${value.substring(0, 30)}${value.length > 30 ? '...' : ''}"`);
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
  try {
    const elements = await page.$$eval(
      'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select',
      els => els.map(el => ({
        tag: el.tagName,
        type: el.type || '',
        name: el.name || '',
        id: el.id || '',
        placeholder: el.placeholder || '',
        ariaLabel: el.getAttribute('aria-label') || '',
        required: el.required,
        className: (el.className || '').substring(0, 60)
      }))
    );
    console.log(`Found ${elements.length} form input element(s):`);
    elements.forEach(el => console.log('  ', JSON.stringify(el)));
    return elements;
  } catch (e) {
    console.log('Could not log form structure:', e.message);
    return [];
  }
}

async function main() {
  console.log('=== Futures.Works C# Developer Application ===');
  console.log('Applicant: Hisham Abboud');
  console.log('Position: C# Developer - Eindhoven Region');
  console.log('URL:', JOB_URL);
  console.log('');

  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }

  if (!fs.existsSync(RESUME_PDF)) {
    console.error(`ERROR: Resume PDF not found at: ${RESUME_PDF}`);
    process.exit(1);
  }
  console.log(`Resume PDF verified: ${RESUME_PDF}`);

  const proxyConfig = getProxyConfig();
  if (proxyConfig) {
    console.log(`Using proxy: ${proxyConfig.server}`);
  }

  const { chromium } = require('/opt/node22/lib/node_modules/playwright');

  const launchOptions = {
    executablePath: CHROMIUM_PATH,
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled'
    ]
  };

  if (proxyConfig) {
    launchOptions.proxy = proxyConfig;
  }

  const browser = await chromium.launch(launchOptions);

  const contextOptions = {
    viewport: { width: 1280, height: 900 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true
  };

  const context = await browser.newContext(contextOptions);

  // Handle proxy authentication automatically
  if (proxyConfig) {
    await context.route('**/*', async (route) => {
      route.continue();
    });
  }

  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') console.log(`[Page Error] ${msg.text().substring(0, 100)}`);
  });

  try {
    // Step 1: Navigate to job page
    console.log('\n--- Step 1: Navigating to job page ---');
    await page.goto(JOB_URL, {
      waitUntil: 'domcontentloaded',
      timeout: 45000
    });

    await page.waitForTimeout(3000);
    const pageTitle = await page.title();
    console.log(`Page title: ${pageTitle}`);
    console.log(`Current URL: ${page.url()}`);

    await takeScreenshot(page, 'futures-works-01-job-page.png');

    // Step 2: Find and click Apply button
    console.log('\n--- Step 2: Looking for Apply button ---');

    // Log all links/buttons for debugging
    const clickables = await page.$$eval('a, button', els =>
      els.map(el => ({
        tag: el.tagName,
        text: el.textContent.trim().substring(0, 60),
        href: el.getAttribute('href') || ''
      })).filter(el => el.text.length > 0)
    );
    console.log('Clickable elements:');
    clickables.forEach(c => console.log(`  ${c.tag}: "${c.text}" href="${c.href}"`));

    let clicked = false;

    // Try various apply button selectors
    const applyTextOptions = [
      'Apply for Position',
      'Apply for this position',
      'Apply Now',
      'Apply',
      'Solliciteer',
      'Solliciteer nu'
    ];

    for (const text of applyTextOptions) {
      try {
        const el = await page.$(`a:has-text("${text}"), button:has-text("${text}")`);
        if (el) {
          console.log(`Found Apply element with text: "${text}"`);
          const href = await el.getAttribute('href');
          if (href && href.startsWith('http')) {
            // Navigate directly
            console.log(`Navigating to: ${href}`);
            await page.goto(href, { waitUntil: 'domcontentloaded', timeout: 30000 });
          } else {
            await el.click();
          }
          clicked = true;
          break;
        }
      } catch (e) {
        // try next
      }
    }

    if (!clicked) {
      // Try finding any link containing "apply" in href
      const applyLinks = await page.$$eval('a[href]', links =>
        links.map(l => ({ text: l.textContent.trim(), href: l.href }))
              .filter(l => l.href.toLowerCase().includes('apply') || l.text.toLowerCase().includes('apply'))
      );

      if (applyLinks.length > 0) {
        console.log(`Found apply link: "${applyLinks[0].text}" -> ${applyLinks[0].href}`);
        await page.goto(applyLinks[0].href, { waitUntil: 'domcontentloaded', timeout: 30000 });
        clicked = true;
      }
    }

    if (!clicked) {
      console.log('No separate apply button found. Checking if form is on current page...');
      const formEl = await page.$('form');
      if (formEl) {
        console.log('Form found on current page.');
        clicked = true;
      } else {
        console.log('WARNING: No apply button and no form found on page.');
      }
    }

    await page.waitForTimeout(3000);
    const afterClickUrl = page.url();
    console.log(`URL after click: ${afterClickUrl}`);
    await takeScreenshot(page, 'futures-works-02-after-apply-click.png');

    // Check for iframes
    const iframes = await page.$$('iframe');
    console.log(`\nFound ${iframes.length} iframe(s)`);

    let formContext = page;

    if (iframes.length > 0) {
      for (let i = 0; i < iframes.length; i++) {
        try {
          const frame = await iframes[i].contentFrame();
          if (frame) {
            const frameUrl = frame.url();
            console.log(`  Iframe ${i} URL: ${frameUrl}`);
            const frameInputs = await frame.$$('input, textarea');
            if (frameInputs.length > 0) {
              console.log(`  Iframe ${i} has ${frameInputs.length} form elements. Using this frame.`);
              formContext = frame;
              break;
            }
          }
        } catch (e) {
          console.log(`  Iframe ${i} not accessible: ${e.message}`);
        }
      }
    }

    // Step 3: Analyze form
    console.log('\n--- Step 3: Analyzing form structure ---');
    const formElements = await logFormStructure(formContext);

    if (formElements.length === 0 && iframes.length === 0) {
      console.log('No form elements found. The form may be on a different page or loaded dynamically.');

      // Try waiting longer for dynamic content
      await page.waitForTimeout(5000);
      const formElements2 = await logFormStructure(formContext);
      if (formElements2.length === 0) {
        console.log('Still no form elements after waiting. Saving debug info...');
        const html = await page.content();
        fs.writeFileSync('/home/user/Agents/output/screenshots/futures-works-debug.html', html);
        console.log('Page HTML saved to /home/user/Agents/output/screenshots/futures-works-debug.html');
      }
    }

    // Step 4: Fill form fields
    console.log('\n--- Step 4: Filling form fields ---');

    // Full name
    await tryFillField(formContext, [
      'input[name="name"]',
      'input[name="full_name"]',
      'input[name="fullName"]',
      'input[id="name"]',
      'input[id="full_name"]',
      'input[placeholder*="name" i]:not([placeholder*="last" i]):not([placeholder*="sur" i]):not([placeholder*="user" i])'
    ], PERSONAL_DETAILS.fullName);

    // First name
    await tryFillField(formContext, [
      'input[name="first_name"]',
      'input[name="firstName"]',
      'input[id="first_name"]',
      'input[id="firstName"]',
      'input[placeholder*="first name" i]',
      'input[placeholder*="firstname" i]',
      'input[placeholder*="voornaam" i]',
      'input[aria-label*="first name" i]',
      'input[aria-label*="voornaam" i]'
    ], PERSONAL_DETAILS.firstName);

    // Last name
    await tryFillField(formContext, [
      'input[name="last_name"]',
      'input[name="lastName"]',
      'input[name="surname"]',
      'input[id="last_name"]',
      'input[id="lastName"]',
      'input[placeholder*="last name" i]',
      'input[placeholder*="lastname" i]',
      'input[placeholder*="surname" i]',
      'input[placeholder*="achternaam" i]',
      'input[aria-label*="last name" i]',
      'input[aria-label*="achternaam" i]'
    ], PERSONAL_DETAILS.lastName);

    // Email
    await tryFillField(formContext, [
      'input[type="email"]',
      'input[name="email"]',
      'input[id="email"]',
      'input[placeholder*="email" i]',
      'input[aria-label*="email" i]'
    ], PERSONAL_DETAILS.email);

    // Phone
    await tryFillField(formContext, [
      'input[type="tel"]',
      'input[name="phone"]',
      'input[name="telephone"]',
      'input[name="mobile"]',
      'input[name="phone_number"]',
      'input[id="phone"]',
      'input[id="telephone"]',
      'input[placeholder*="phone" i]',
      'input[placeholder*="tel" i]',
      'input[placeholder*="mobile" i]',
      'input[placeholder*="telefoon" i]',
      'input[placeholder*="mobiel" i]',
      'input[aria-label*="phone" i]',
      'input[aria-label*="tel" i]'
    ], PERSONAL_DETAILS.phone);

    // LinkedIn
    await tryFillField(formContext, [
      'input[name="linkedin"]',
      'input[name="linkedin_url"]',
      'input[name="linkedinUrl"]',
      'input[id="linkedin"]',
      'input[placeholder*="linkedin" i]',
      'input[aria-label*="linkedin" i]'
    ], PERSONAL_DETAILS.linkedin);

    // GitHub
    await tryFillField(formContext, [
      'input[name="github"]',
      'input[name="github_url"]',
      'input[id="github"]',
      'input[placeholder*="github" i]',
      'input[aria-label*="github" i]'
    ], PERSONAL_DETAILS.github);

    // City
    await tryFillField(formContext, [
      'input[name="city"]',
      'input[name="location"]',
      'input[name="woonplaats"]',
      'input[id="city"]',
      'input[placeholder*="city" i]',
      'input[placeholder*="stad" i]',
      'input[placeholder*="woonplaats" i]',
      'input[aria-label*="city" i]'
    ], PERSONAL_DETAILS.city);

    // Cover letter
    const coverFilled = await tryFillField(formContext, [
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
    ], COVER_LETTER);

    if (coverFilled) {
      console.log('Cover letter filled successfully.');
    } else {
      console.log('No cover letter textarea found.');
    }

    // Step 5: File upload
    console.log('\n--- Step 5: Uploading resume ---');
    const fileInputs = await formContext.$$('input[type="file"]');
    console.log(`Found ${fileInputs.length} file input(s)`);

    if (fileInputs.length > 0) {
      for (let i = 0; i < fileInputs.length; i++) {
        try {
          const acceptAttr = await fileInputs[i].getAttribute('accept');
          console.log(`File input ${i} accepts: ${acceptAttr || 'any'}`);
          await fileInputs[i].setInputFiles(RESUME_PDF);
          console.log(`Resume uploaded to file input ${i}`);
          await page.waitForTimeout(2000);
          break; // Upload to first file input only
        } catch (e) {
          console.log(`Could not upload to file input ${i}: ${e.message}`);
        }
      }
    } else {
      console.log('No file upload field found on form.');
    }

    await page.waitForTimeout(1500);
    await takeScreenshot(page, 'futures-works-03-form-filled.png');
    console.log('\nPre-submit screenshot saved: futures-works-03-form-filled.png');

    // Step 6: Submit
    console.log('\n--- Step 6: Submitting application ---');

    let submitBtn = null;
    const submitTexts = ['Submit Application', 'Submit', 'Apply', 'Send', 'Verzenden', 'Solliciteer'];

    for (const text of submitTexts) {
      try {
        const btn = await formContext.$(`button:has-text("${text}"), input[type="submit"][value="${text}"]`);
        if (btn) {
          const visible = await btn.isVisible().catch(() => false);
          if (visible) {
            console.log(`Found submit button: "${text}"`);
            submitBtn = btn;
            break;
          }
        }
      } catch (e) {}
    }

    if (!submitBtn) {
      submitBtn = await formContext.$('button[type="submit"], input[type="submit"]');
      if (submitBtn) {
        const btnText = await submitBtn.evaluate(el => el.textContent || el.value || '');
        console.log(`Found submit button by type: "${btnText.trim()}"`);
      }
    }

    if (!submitBtn) {
      // Log all buttons
      const allBtns = await formContext.$$eval(
        'button, input[type="submit"]',
        btns => btns.map(b => ({
          text: (b.textContent || b.value || '').trim(),
          type: b.type,
          disabled: b.disabled,
          class: b.className
        }))
      );
      console.log('All buttons found:', JSON.stringify(allBtns));
    }

    if (submitBtn) {
      console.log('Submitting application...');
      await submitBtn.click();
      console.log('Submit clicked! Waiting for confirmation...');
      await page.waitForTimeout(6000);

      await takeScreenshot(page, 'futures-works-04-after-submit.png');
      console.log('Post-submit screenshot saved: futures-works-04-after-submit.png');

      const finalUrl = page.url();
      console.log(`Final URL: ${finalUrl}`);

      const bodyText = await page.evaluate(() => document.body.innerText || document.body.textContent || '');
      console.log('\nPage content after submit (first 800 chars):');
      console.log(bodyText.substring(0, 800));

      const successKeywords = ['thank', 'success', 'received', 'bedankt', 'ontvangen', 'submitted', 'confirmation', 'bevestig', 'application'];
      const isSuccess = successKeywords.some(kw => bodyText.toLowerCase().includes(kw));

      if (isSuccess) {
        console.log('\n=== SUCCESS: Application submitted successfully! ===');
      } else {
        console.log('\n=== Application submitted - check screenshots to confirm ===');
      }
    } else {
      console.log('WARNING: Could not find submit button!');
      await takeScreenshot(page, 'futures-works-04-no-submit.png');
      console.log('Screenshot of form state saved.');
    }

    console.log('\n=== Application Process Complete ===');
    console.log('All screenshots saved to:', SCREENSHOTS_DIR);
    console.log('Screenshots:');
    const screenshots = fs.readdirSync(SCREENSHOTS_DIR).filter(f => f.startsWith('futures-works'));
    screenshots.forEach(s => console.log(' -', path.join(SCREENSHOTS_DIR, s)));

  } catch (error) {
    console.error('\nERROR during application:', error.message);
    try {
      await takeScreenshot(page, 'futures-works-error-state.png');
      console.log('Error state screenshot saved.');
    } catch (e) {}

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
