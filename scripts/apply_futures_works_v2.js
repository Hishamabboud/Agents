const path = require('path');
const fs = require('fs');

const APPLY_URL = 'https://www.careers-page.com/futures-works/job/LR994VY6/apply';
const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PDF = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const CHROMIUM_PATH = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';

const PERSONAL_DETAILS = {
  fullName: 'Hisham Abboud',
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'hiaham123@hotmail.com',  // CORRECTED email
  phone: '+31 06 4841 2838',
  linkedin: 'https://linkedin.com/in/hisham-abboud',
  city: 'Eindhoven',
  country: 'Netherlands',
  postcode: '5611'
};

// Language option values from the form (Arabic=7, Dutch=39, English=40)
const LANGUAGE_VALUES = ['7', '39', '40'];

const ANSWERS = {
  introduction: `I am Hisham Abboud, a Software Engineer based in Eindhoven with over 2 years of professional experience in C#/.NET development. I currently work at Actemium (VINCI Energies) where I develop full-stack applications for manufacturing clients. Prior to this, I completed internships at ASML in Veldhoven and Delta Electronics in Helmond, giving me strong exposure to the high-tech industrial sector in the Eindhoven region. I hold a Bachelor of Science in Software Engineering from Fontys University of Applied Sciences in Eindhoven and am fluent in Dutch, English, and Arabic.`,

  attraction: `I am drawn to this role because Futures.Works specifically focuses on connecting engineers with high-tech companies in the Eindhoven ecosystem - an environment I am already deeply familiar with through my work at Actemium and my internship at ASML. The opportunity to work with cutting-edge technology companies in the region, applying my C# and .NET expertise in challenging engineering contexts, is exactly the type of career growth I am seeking. The Eindhoven high-tech sector is world-class, and I want to be part of it at a deeper level.`,

  keySkills: `My key skills that make me suitable for this role include:
- 2+ years of professional C# and .NET development experience at Actemium (VINCI Energies)
- Full-stack development using ASP.NET, REST APIs, and SQL databases
- CI/CD pipeline experience with Azure DevOps
- Agile/Scrum methodology in industrial and high-tech contexts
- Direct high-tech sector experience from ASML internship (Python, Azure, Kubernetes, Jira)
- Legacy code migration from Visual Basic to C# (Delta Electronics)
- Strong understanding of OOP principles and software architecture
- Fluent in Dutch and English, enabling seamless collaboration with local teams`,

  improvements: `I am actively working to deepen my expertise in cloud-native architectures and microservices with Azure. I want to expand my knowledge of advanced design patterns and domain-driven design for large-scale enterprise systems. Additionally, I am improving my skills in DevSecOps practices and security-first software development, which is increasingly important in high-tech manufacturing environments.`,

  salaryExpectations: `My salary expectation is in the range of EUR 55,000 - EUR 70,000 gross per year, depending on the specific role, responsibilities, and benefits package. I am open to discussing the full compensation structure.`,

  workPreference: `Hybrid - I prefer a combination of on-site collaboration with the team and remote work for focused development tasks. I am based in Eindhoven so on-site work at local high-tech companies is very convenient for me.`,

  reasonLeaving: `I am looking for a new opportunity to work directly in the high-tech sector at a higher technical level. While I value my current role at Actemium, working with Futures.Works would give me access to more specialized C# development roles at leading high-tech companies in the Eindhoven region, which aligns better with my long-term career goals.`,

  workPermit: `I am a Dutch/EU citizen with a valid Dutch work permit (BSN). I have full right to work in the Netherlands without any restrictions or sponsorship requirements.`,

  reference: `Available upon request. I can provide references from my colleagues and supervisors at Actemium (VINCI Energies) and from my internship supervisor at ASML in Veldhoven.`,

  achievement: `Situation: At Delta Electronics, the HR salary management system was built on outdated Visual Basic code that was slow, error-prone, and difficult to maintain across 5 branches. Task: I was tasked with modernizing this system while ensuring zero disruption to payroll operations. Action: I designed and developed a new C# web application with a clean architecture, migrated the business logic from Visual Basic, and implemented SQL database optimizations that reduced query time by 60%. I also trained HR staff on the new system. Result: The new system reduced manual errors by 90%, cut processing time from hours to minutes, and was successfully deployed across all branches within the internship period.`
};

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
    return null;
  }
}

const timestamp = new Date().toISOString().replace(/[:.]/g, '_').substring(0, 19);

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
        console.log(`  OK: "${placeholder.substring(0, 60)}"`);
        return true;
      }
    }
  } catch (e) {}
  console.log(`  MISS: "${placeholder.substring(0, 60)}"`);
  return false;
}

async function main() {
  console.log('=== Futures.Works C# Developer Re-Application (v2 - CORRECTED EMAIL) ===');
  console.log('Applicant: Hisham Abboud');
  console.log('Email: hiaham123@hotmail.com');
  console.log('Position: C# Developer - Eindhoven Region');
  console.log('');

  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }

  if (!fs.existsSync(RESUME_PDF)) {
    console.error(`ERROR: Resume PDF not found: ${RESUME_PDF}`);
    process.exit(1);
  }

  const proxyConfig = getProxyConfig();
  if (proxyConfig) console.log(`Proxy: ${proxyConfig.server}`);

  const { chromium } = require('/opt/node22/lib/node_modules/playwright');

  const launchOptions = {
    executablePath: CHROMIUM_PATH,
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--ignore-certificate-errors',
      '--disable-gpu'
    ]
  };
  if (proxyConfig) launchOptions.proxy = proxyConfig;

  const browser = await chromium.launch(launchOptions);
  const context = await browser.newContext({
    viewport: { width: 1280, height: 1200 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  const screenshots = [];

  try {
    // Step 1: Load the form
    console.log('--- Step 1: Loading application form ---');
    await page.goto(APPLY_URL, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(2000);
    console.log(`Page title: ${await page.title()}`);
    console.log(`URL: ${page.url()}`);
    const shot1 = await takeScreenshot(page, `futures-works-v2-01-form-loaded-${timestamp}.png`);
    screenshots.push(shot1);

    // Step 2: Fill basic text fields
    console.log('\n--- Step 2: Filling form fields ---');
    await fillByPlaceholder(page, 'Full Name', PERSONAL_DETAILS.fullName);
    await fillByPlaceholder(page, 'First Name', PERSONAL_DETAILS.firstName);
    await fillByPlaceholder(page, 'Last Name', PERSONAL_DETAILS.lastName);
    await fillByPlaceholder(page, 'Email', PERSONAL_DETAILS.email);
    await fillByPlaceholder(page, 'postcode (used for matching, can be approximate)', PERSONAL_DETAILS.postcode);
    await fillByPlaceholder(page, 'Current City', PERSONAL_DETAILS.city);
    await fillByPlaceholder(page, 'Current Country', PERSONAL_DETAILS.country);

    // Verify email was entered correctly
    const emailValue = await page.evaluate(() => {
      const emailInput = document.querySelector('[placeholder="Email"]');
      return emailInput ? emailInput.value : 'NOT FOUND';
    });
    console.log(`  Email field verification: "${emailValue}"`);

    // Step 3: Handle Select2 languages dropdown
    console.log('\n--- Step 3: Selecting languages (Dutch, English, Arabic) ---');
    await page.evaluate((langValues) => {
      const sel = document.querySelector('select[name="1019019"]');
      if (!sel) return;

      for (const opt of sel.options) {
        if (langValues.includes(opt.value)) {
          opt.selected = true;
        }
      }

      if (window.jQuery) {
        window.jQuery(sel).trigger('change.select2');
        window.jQuery(sel).trigger('change');
      } else {
        sel.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }, LANGUAGE_VALUES);

    await page.waitForTimeout(500);

    const selectedLangs = await page.$$eval('select[name="1019019"] option:checked', opts =>
      opts.map(o => o.text.trim())
    );
    console.log(`  Selected languages: ${selectedLangs.join(', ')}`);

    // Step 4: Fill screening questions (textareas)
    console.log('\n--- Step 4: Filling screening questions ---');
    await fillByPlaceholder(page, 'Give a short introduction of yourself', ANSWERS.introduction);
    await fillByPlaceholder(page, 'What attracts you in the role?', ANSWERS.attraction);
    await fillByPlaceholder(page, 'What are your key skills that make you suitable for the role?', ANSWERS.keySkills);
    await fillByPlaceholder(page, 'What are some skills or areas you want to improve in?', ANSWERS.improvements);
    await fillByPlaceholder(page, 'What are your exact salary expectations?', ANSWERS.salaryExpectations);
    await fillByPlaceholder(page, 'Do you want to work remote, on-site, or hybrid?', ANSWERS.workPreference);
    await fillByPlaceholder(page, 'Why do you want to leave your current job?', ANSWERS.reasonLeaving);
    await fillByPlaceholder(page, 'What is your work permit status?', ANSWERS.workPermit);
    await fillByPlaceholder(page, 'Provide a reference (someone that can say something about you)', ANSWERS.reference);
    await fillByPlaceholder(page, 'Achievement you are most proud of in format Situation, Task, Action, Result', ANSWERS.achievement);

    // Step 5: Set availability date via flatpickr
    console.log('\n--- Step 5: Setting availability date ---');
    const dateSet = await page.evaluate(() => {
      const el = document.querySelector('input[name="899383"]');
      if (!el) return null;

      if (el._flatpickr) {
        el._flatpickr.setDate('2025-03-17', true);
        return el.value;
      }

      el.removeAttribute('readonly');
      el.value = '2025-03-17';
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return el.value;
    });
    console.log(`  Availability date set to: ${dateSet}`);

    if (!dateSet || dateSet.trim() === '') {
      const dateField = await page.$('input[name="899383"]');
      if (dateField) {
        await dateField.click({ force: true });
        await page.waitForTimeout(800);
        const dayBtn = await page.$('.flatpickr-day:not(.prevMonthDay):not(.nextMonthDay):not(.flatpickr-disabled)');
        if (dayBtn) {
          await dayBtn.click();
          console.log('  Clicked on a calendar day as fallback');
        }
        await page.keyboard.press('Escape');
      }
    }

    // Step 6: LinkedIn URL
    console.log('\n--- Step 6: Filling LinkedIn URL ---');
    await fillByPlaceholder(page, 'Your LinkedIn URL', PERSONAL_DETAILS.linkedin);

    // Step 7: Upload resume
    console.log('\n--- Step 7: Uploading resume ---');
    const fileInput = await page.$('input[type="file"]');
    if (fileInput) {
      await fileInput.setInputFiles(RESUME_PDF);
      console.log(`  Resume uploaded: ${path.basename(RESUME_PDF)}`);
      await page.waitForTimeout(2000);
    } else {
      console.log('  WARNING: No file upload field found!');
    }

    // Step 8: Check all checkboxes (consent + terms)
    console.log('\n--- Step 8: Accepting consents and terms ---');
    const checkboxes = await page.$$('input[type="checkbox"]');
    for (let i = 0; i < checkboxes.length; i++) {
      const name = await checkboxes[i].getAttribute('name') || `cb-${i}`;
      const isChecked = await checkboxes[i].isChecked().catch(() => false);
      if (!isChecked) {
        await checkboxes[i].check();
        console.log(`  Checked: ${name}`);
      } else {
        console.log(`  Already checked: ${name}`);
      }
    }

    await page.waitForTimeout(1000);

    // Pre-submit screenshot - scroll to top first
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    const shot2 = await takeScreenshot(page, `futures-works-v2-02-pre-submit-${timestamp}.png`);
    screenshots.push(shot2);
    console.log('\nPre-submit screenshot saved. Verifying email one more time...');

    // Final email verification before submit
    const emailBeforeSubmit = await page.evaluate(() => {
      const emailInput = document.querySelector('[placeholder="Email"]');
      return emailInput ? emailInput.value : 'NOT FOUND';
    });
    console.log(`  FINAL EMAIL CHECK: "${emailBeforeSubmit}"`);

    if (emailBeforeSubmit !== 'hiaham123@hotmail.com') {
      console.log('  WARNING: Email mismatch! Correcting...');
      const emailField = await page.$('[placeholder="Email"]');
      if (emailField) {
        await emailField.fill('hiaham123@hotmail.com');
        console.log('  Email corrected to: hiaham123@hotmail.com');
      }
    }

    // Step 9: Submit
    console.log('\n--- Step 9: Submitting application ---');

    const submitBtn = await page.$('button[type="submit"]') ||
                      await page.$('input[type="submit"]') ||
                      await page.$('button:has-text("Apply")');

    if (!submitBtn) {
      console.log('ERROR: Submit button not found!');
      const shot_err = await takeScreenshot(page, `futures-works-v2-error-no-submit-${timestamp}.png`);
      screenshots.push(shot_err);
      await browser.close();
      return { status: 'failed', screenshots, notes: 'Submit button not found' };
    }

    const btnText = await submitBtn.evaluate(el => el.textContent || el.value || '');
    console.log(`Found submit button: "${btnText.trim()}"`);

    await submitBtn.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);

    console.log('Clicking submit...');
    await submitBtn.click();

    // Wait for response
    await Promise.race([
      page.waitForNavigation({ waitUntil: 'networkidle', timeout: 20000 }).catch(() => {}),
      page.waitForTimeout(12000)
    ]);

    console.log(`Final URL: ${page.url()}`);

    // Post-submit screenshots
    const shot3 = await takeScreenshot(page, `futures-works-v2-03-after-submit-${timestamp}.png`);
    screenshots.push(shot3);

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    const shot4 = await takeScreenshot(page, `futures-works-v2-04-result-top-${timestamp}.png`);
    screenshots.push(shot4);

    const bodyText = await page.evaluate(() => document.body.innerText || '');
    console.log('\nPage text after submit (first 1500 chars):');
    console.log(bodyText.substring(0, 1500));

    const successKeywords = ['thank', 'success', 'received', 'bedankt', 'ontvangen', 'submitted', 'confirmation', 'bevestig', 'application was successfully', 'successfully submitted'];
    const errorKeywords = ['required', 'this field is required', 'invalid', 'verplicht', 'error'];

    const isSuccess = successKeywords.some(kw => bodyText.toLowerCase().includes(kw));
    const hasErrors = errorKeywords.some(kw => bodyText.toLowerCase().includes(kw));

    if (isSuccess) {
      console.log('\n=== APPLICATION RE-SUBMITTED SUCCESSFULLY WITH CORRECT EMAIL ===');
      console.log('Email used: hiaham123@hotmail.com');
    } else if (hasErrors) {
      console.log('\n=== FORM VALIDATION ERRORS - Check screenshots ===');

      const errors = await page.$$eval(
        '.invalid-feedback, .field-error, [class*="error-message"], .alert-danger',
        els => els.map(el => el.textContent.trim()).filter(t => t.length > 0)
      );
      if (errors.length > 0) {
        console.log('Specific errors:', errors);
      }
    } else {
      console.log('\n=== Status uncertain - check screenshots ===');
    }

    console.log('\n=== Summary ===');
    console.log('Screenshots taken:');
    screenshots.forEach(s => console.log(`  ${s}`));

    return { status: isSuccess ? 'applied' : 'uncertain', screenshots, bodyText: bodyText.substring(0, 500) };

  } catch (error) {
    console.error('\nFATAL ERROR:', error.message);
    try {
      const shotErr = await takeScreenshot(page, `futures-works-v2-fatal-error-${timestamp}.png`);
      screenshots.push(shotErr);
    } catch (e) {}
    throw error;
  } finally {
    await browser.close();
    console.log('\nBrowser closed.');
  }
}

main().then(result => {
  console.log('\nResult:', JSON.stringify(result, null, 2));
}).catch(err => {
  console.error(err.message);
  process.exit(1);
});
