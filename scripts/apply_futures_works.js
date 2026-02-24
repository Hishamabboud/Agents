const path = require('path');
const fs = require('fs');

const JOB_URL = 'https://www.careers-page.com/futures-works/job/LR994VY6';
const APPLY_URL = 'https://www.careers-page.com/futures-works/job/LR994VY6/apply';
const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PDF = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const CHROMIUM_PATH = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';

const PERSONAL_DETAILS = {
  fullName: 'Hisham Abboud',
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'Hisham123@hotmail.com',
  phone: '+31 06 4841 2838',
  linkedin: 'https://linkedin.com/in/hisham-abboud',
  github: 'github.com/Hishamabboud',
  city: 'Eindhoven',
  country: 'Netherlands',
  postcode: '5611'
};

// Detailed answers for all screening questions
const ANSWERS = {
  introduction: `I am Hisham Abboud, a Software Engineer based in Eindhoven with over 2 years of professional experience in C#/.NET development. I currently work at Actemium (VINCI Energies) where I develop full-stack applications for manufacturing clients. Prior to this, I completed internships at ASML in Veldhoven and Delta Electronics in Helmond, giving me strong exposure to the high-tech industrial sector in the Eindhoven region. I hold a Bachelor of Science in Software Engineering from Fontys University of Applied Sciences in Eindhoven and am fluent in Dutch, English, and Arabic.`,

  attraction: `I am drawn to this role because Futures.Works specifically focuses on connecting engineers with high-tech companies in the Eindhoven ecosystem - an environment I am already deeply familiar with through my work at Actemium and my internship at ASML. The opportunity to work with cutting-edge technology companies in the region, applying my C# and .NET expertise in challenging engineering contexts, is exactly the type of career growth I am seeking. The Eindhoven high-tech sector is world-class, and I want to be part of it at a deeper level.`,

  keySkills: `My key skills that make me suitable for this role include:
- 2+ years of professional C# and .NET development experience at Actemium (VINCI Energies)
- Full-stack development using ASP.NET, REST APIs, and SQL databases
- CI/CD pipeline experience with Azure DevOps
- Agile/Scrum methodology experience in industrial and high-tech contexts
- Direct high-tech sector experience from ASML internship (Python, Azure, Kubernetes, Jira)
- Legacy code migration from Visual Basic to C# (Delta Electronics)
- Strong understanding of OOP principles and software architecture
- Fluent in Dutch and English, enabling seamless collaboration with local teams`,

  improvements: `I am actively working to deepen my expertise in cloud-native architectures and microservices with Azure. I want to expand my knowledge of advanced design patterns and domain-driven design for large-scale enterprise systems. Additionally, I am improving my skills in DevSecOps practices and security-first software development, which is increasingly important in high-tech manufacturing environments.`,

  availability: 'Immediately / Within 1 month',

  salaryExpectations: `My salary expectation is in the range of €55,000 - €70,000 gross per year, depending on the specific role, responsibilities, and benefits package. I am open to discussing the full compensation structure.`,

  workPreference: `Hybrid - I prefer a combination of on-site collaboration with the team and remote work for focused development tasks. I am based in Eindhoven so on-site work at local high-tech companies is very convenient for me.`,

  reasonLeaving: `I am looking for a new opportunity to work directly in the high-tech sector at a higher technical level. While I value my current role at Actemium, working with Futures.Works would give me access to more specialized C# development roles at leading high-tech companies in the Eindhoven region, which aligns better with my long-term career goals in software engineering for industrial and semiconductor technology.`,

  workPermit: `I am a Dutch/EU citizen with a valid Dutch work permit (BSN). I have full right to work in the Netherlands without any restrictions or sponsorship requirements.`,

  reference: `Available upon request. I can provide references from my colleagues and supervisors at Actemium (VINCI Energies) and from my internship supervisor at ASML.`,

  achievement: `Situation: At Delta Electronics, the HR salary management system was built on outdated Visual Basic code that was slow, error-prone, and difficult to maintain across 5 branches. Task: I was tasked with modernizing this system while ensuring zero disruption to payroll operations. Action: I designed and developed a new C# web application with a clean architecture, migrated the business logic from Visual Basic, and implemented a SQL database optimization that reduced query time by 60%. I also trained the HR staff on the new system. Result: The new system reduced manual errors by 90%, cut processing time from hours to minutes, and was successfully deployed across all branches within the 6-month internship period.`
};

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

async function fillByPlaceholder(page, placeholder, value) {
  try {
    const el = await page.$(`[placeholder="${placeholder}"]`);
    if (el) {
      const visible = await el.isVisible().catch(() => false);
      if (visible) {
        await el.fill(value);
        console.log(`  Filled "${placeholder}" with: "${value.substring(0, 60)}${value.length > 60 ? '...' : ''}"`);
        return true;
      }
    }
  } catch (e) {}
  return false;
}

async function fillByName(page, name, value) {
  try {
    const el = await page.$(`[name="${name}"]`);
    if (el) {
      const visible = await el.isVisible().catch(() => false);
      if (visible) {
        await el.fill(value);
        console.log(`  Filled field name="${name}" with: "${value.substring(0, 60)}${value.length > 60 ? '...' : ''}"`);
        return true;
      }
    }
  } catch (e) {}
  return false;
}

async function fillById(page, id, value) {
  try {
    const el = await page.$(`#${id}`);
    if (el) {
      const visible = await el.isVisible().catch(() => false);
      if (visible) {
        await el.fill(value);
        console.log(`  Filled id="${id}" with: "${value.substring(0, 60)}${value.length > 60 ? '...' : ''}"`);
        return true;
      }
    }
  } catch (e) {}
  return false;
}

async function selectLanguageDropdown(page, languages) {
  // The language field appears to be a Select2 multi-select
  try {
    // Try clicking on the select2 container to open it
    const select2Container = await page.$('.select2-container');
    if (select2Container) {
      for (const lang of languages) {
        try {
          // Type in the search box
          const searchInput = await page.$('.select2-search__field');
          if (searchInput) {
            await searchInput.click();
            await searchInput.fill(lang);
            await page.waitForTimeout(1000);

            // Look for the option and click it
            const option = await page.$('.select2-results__option');
            if (option) {
              await option.click();
              console.log(`  Selected language: ${lang}`);
              await page.waitForTimeout(500);
            }
          }
        } catch (e) {
          console.log(`  Could not select language ${lang}: ${e.message}`);
        }
      }
    }
  } catch (e) {
    console.log(`  Could not interact with language dropdown: ${e.message}`);
  }

  // Also try setting the underlying select value
  try {
    const selectEl = await page.$('select[name="1019019"]');
    if (selectEl) {
      // Get available options
      const options = await page.$$eval('select[name="1019019"] option', opts =>
        opts.map(o => ({ value: o.value, text: o.textContent.trim() }))
      );
      console.log('  Available language options:', options.map(o => o.text).join(', '));

      // Select English and Dutch
      for (const opt of options) {
        if (opt.text.toLowerCase().includes('english') ||
            opt.text.toLowerCase().includes('dutch') ||
            opt.text.toLowerCase().includes('engels') ||
            opt.text.toLowerCase().includes('nederlands')) {
          await page.evaluate((val) => {
            const sel = document.querySelector('select[name="1019019"]');
            if (sel) {
              for (const opt of sel.options) {
                if (opt.value === val) opt.selected = true;
              }
              sel.dispatchEvent(new Event('change', { bubbles: true }));
            }
          }, opt.value);
          console.log(`  Programmatically selected: ${opt.text}`);
        }
      }
    }
  } catch (e) {
    console.log(`  Could not set select value: ${e.message}`);
  }
}

async function main() {
  console.log('=== Futures.Works C# Developer Application ===');
  console.log('Applicant: Hisham Abboud');
  console.log('Position: C# Developer - Eindhoven Region');
  console.log('Apply URL:', APPLY_URL);
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

  const context = await browser.newContext({
    viewport: { width: 1280, height: 1200 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') console.log(`[Page Error] ${msg.text().substring(0, 120)}`);
  });

  try {
    // Step 1: Navigate directly to apply form
    console.log('--- Step 1: Navigating directly to application form ---');
    await page.goto(APPLY_URL, {
      waitUntil: 'networkidle',
      timeout: 45000
    });

    await page.waitForTimeout(3000);
    const pageTitle = await page.title();
    console.log(`Page title: ${pageTitle}`);
    console.log(`Current URL: ${page.url()}`);

    await takeScreenshot(page, 'futures-works-01-apply-form-loaded.png');

    // Step 2: Fill all form fields
    console.log('\n--- Step 2: Filling all form fields ---');

    // Basic info fields (by placeholder based on form analysis)
    await fillByPlaceholder(page, 'Full Name', PERSONAL_DETAILS.fullName);
    await fillByPlaceholder(page, 'First Name', PERSONAL_DETAILS.firstName);
    await fillByPlaceholder(page, 'Last Name', PERSONAL_DETAILS.lastName);
    await fillByPlaceholder(page, 'Email', PERSONAL_DETAILS.email);

    // Postcode field
    await fillByPlaceholder(page, 'postcode (used for matching, can be approximate)', PERSONAL_DETAILS.postcode);

    // Current city and country
    await fillByPlaceholder(page, 'Current City', PERSONAL_DETAILS.city);
    await fillByPlaceholder(page, 'Current Country', PERSONAL_DETAILS.country);

    // Languages (Select2 multi-select)
    console.log('  Handling language selection...');
    await selectLanguageDropdown(page, ['English', 'Dutch', 'Nederlands', 'Engels']);

    // Screening questions (textareas)
    await fillByPlaceholder(page, 'Give a short introduction of yourself', ANSWERS.introduction);
    await fillByPlaceholder(page, 'What attracts you in the role?', ANSWERS.attraction);
    await fillByPlaceholder(page, 'What are your key skills that make you suitable for the role?', ANSWERS.keySkills);
    await fillByPlaceholder(page, 'What are some skills or areas you want to improve in?', ANSWERS.improvements);

    // Availability date field
    await fillByPlaceholder(page, 'When are you available to start working?', ANSWERS.availability);

    // Salary expectations
    await fillByPlaceholder(page, 'What are your exact salary expectations?', ANSWERS.salaryExpectations);

    // Work preference (remote/on-site/hybrid)
    await fillByPlaceholder(page, 'Do you want to work remote, on-site, or hybrid?', ANSWERS.workPreference);

    // Reason for leaving
    await fillByPlaceholder(page, 'Why do you want to leave your current job?', ANSWERS.reasonLeaving);

    // Work permit
    await fillByPlaceholder(page, 'What is your work permit status?', ANSWERS.workPermit);

    // Reference
    await fillByPlaceholder(page, 'Provide a reference (someone that can say something about you)', ANSWERS.reference);

    // Achievement (STAR format)
    await fillByPlaceholder(page, 'Achievement you are most proud of in format Situation, Task, Action, Result', ANSWERS.achievement);

    // LinkedIn URL
    await fillByPlaceholder(page, 'Your LinkedIn URL', PERSONAL_DETAILS.linkedin);

    // Step 3: Upload resume
    console.log('\n--- Step 3: Uploading resume PDF ---');
    const fileInputs = await page.$$('input[type="file"]');
    console.log(`Found ${fileInputs.length} file input(s)`);

    if (fileInputs.length > 0) {
      try {
        await fileInputs[0].setInputFiles(RESUME_PDF);
        console.log(`Resume uploaded successfully: ${RESUME_PDF}`);
        await page.waitForTimeout(2000);
      } catch (e) {
        console.log(`Could not upload resume: ${e.message}`);
      }
    }

    // Step 4: Handle checkboxes (consent, terms)
    console.log('\n--- Step 4: Handling checkboxes ---');
    const checkboxes = await page.$$('input[type="checkbox"]');
    console.log(`Found ${checkboxes.length} checkbox(es)`);

    for (let i = 0; i < checkboxes.length; i++) {
      try {
        const isChecked = await checkboxes[i].isChecked();
        if (!isChecked) {
          await checkboxes[i].check();
          const name = await checkboxes[i].getAttribute('name');
          console.log(`  Checked checkbox: ${name || `checkbox-${i}`}`);
        }
      } catch (e) {
        console.log(`  Could not check checkbox ${i}: ${e.message}`);
      }
    }

    await page.waitForTimeout(1500);

    // Take pre-submit screenshot
    await takeScreenshot(page, 'futures-works-02-form-filled-pre-submit.png');
    console.log('\nPre-submit screenshot saved.');

    // Step 5: Scroll through form to verify filled fields
    console.log('\n--- Step 5: Verifying form state ---');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);

    // Check for any validation errors visible
    const errorMessages = await page.$$eval(
      '.error, .invalid-feedback, [class*="error"]:not([class*="form"]):not([class*="control"])',
      els => els.map(el => el.textContent.trim()).filter(t => t.length > 0)
    );
    if (errorMessages.length > 0) {
      console.log('Validation errors visible:', errorMessages);
    } else {
      console.log('No visible validation errors found.');
    }

    // Step 6: Find and click submit
    console.log('\n--- Step 6: Submitting the application ---');

    // Look for submit button
    let submitBtn = null;

    const submitSelectors = [
      'button[type="submit"]',
      'input[type="submit"]'
    ];

    for (const sel of submitSelectors) {
      const btn = await page.$(sel);
      if (btn) {
        const visible = await btn.isVisible().catch(() => false);
        if (visible) {
          const text = await btn.evaluate(el => el.textContent || el.value || '');
          console.log(`Found submit button: "${text.trim()}" (selector: ${sel})`);
          submitBtn = btn;
          break;
        }
      }
    }

    if (!submitBtn) {
      // Try text-based search
      const submitTexts = ['Apply', 'Submit', 'Verzenden', 'Solliciteer'];
      for (const text of submitTexts) {
        const btn = await page.$(`button:has-text("${text}")`);
        if (btn) {
          const visible = await btn.isVisible().catch(() => false);
          if (visible) {
            console.log(`Found submit button by text: "${text}"`);
            submitBtn = btn;
            break;
          }
        }
      }
    }

    if (submitBtn) {
      // Scroll to bottom first
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(1000);

      console.log('Clicking submit button...');
      await submitBtn.click();
      console.log('Submit clicked! Waiting for response...');

      // Wait for navigation or response
      await Promise.race([
        page.waitForNavigation({ timeout: 15000 }).catch(() => {}),
        page.waitForTimeout(8000)
      ]);

      const finalUrl = page.url();
      console.log(`Final URL: ${finalUrl}`);

      // Take post-submit screenshot
      await takeScreenshot(page, 'futures-works-03-after-submit.png');
      console.log('Post-submit screenshot saved.');

      // Get page text to check for success/error
      const bodyText = await page.evaluate(() => document.body.innerText || '');
      console.log('\nPage content after submit (first 1000 chars):');
      console.log(bodyText.substring(0, 1000));

      // Check for success indicators
      const successKeywords = ['thank', 'success', 'received', 'bedankt', 'ontvangen', 'submitted', 'confirmation', 'bevestig'];
      const errorKeywords = ['required', 'error', 'invalid', 'please fill', 'verplicht'];

      const isSuccess = successKeywords.some(kw => bodyText.toLowerCase().includes(kw));
      const hasErrors = errorKeywords.some(kw => bodyText.toLowerCase().includes(kw));

      if (isSuccess) {
        console.log('\n=== SUCCESS: Application submitted successfully! ===');
      } else if (hasErrors) {
        console.log('\n=== WARNING: Form may have validation errors. Check screenshots. ===');

        // Take another screenshot after scrolling to top to see errors
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.waitForTimeout(500);
        await takeScreenshot(page, 'futures-works-04-validation-errors.png');
      } else {
        console.log('\n=== Application submitted - status uncertain, check screenshots ===');
      }
    } else {
      console.log('Could not find submit button!');

      // Log all buttons for debugging
      const allBtns = await page.$$eval('button, input[type="submit"]', btns =>
        btns.map(b => ({ text: (b.textContent || b.value || '').trim(), type: b.type, visible: b.offsetParent !== null }))
      );
      console.log('All buttons found:', JSON.stringify(allBtns));

      await takeScreenshot(page, 'futures-works-03-no-submit-found.png');
    }

    console.log('\n=== Application Process Complete ===');
    console.log('Screenshots saved to:', SCREENSHOTS_DIR);

  } catch (error) {
    console.error('\nERROR:', error.message);
    try { await takeScreenshot(page, 'futures-works-error-state.png'); } catch (e) {}
    try {
      const html = await page.content();
      fs.writeFileSync('/home/user/Agents/output/screenshots/futures-works-debug.html', html);
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
