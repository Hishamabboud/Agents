const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const proxyEnv = process.env.https_proxy || process.env.HTTPS_PROXY || '';
let proxyServer = '', proxyUsername = '', proxyPassword = '';
if (proxyEnv) {
  const match = proxyEnv.match(/^http:\/\/([^:]+):([^@]+)@(.+)$/);
  if (match) {
    proxyUsername = match[1];
    proxyPassword = match[2];
    proxyServer = 'http://' + match[3];
  }
}

const screenshotDir = '/home/user/Agents/output/screenshots';
const JOB_URL = 'https://careers.keylane.com/jobs/detail/technology/A059791533/software-developer/';
const RESUME_PATH = '/home/user/Agents/profile/resume.pdf';

const applicantDetails = {
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31 06 4841 2838',
  location: 'Eindhoven, Netherlands',
};

const coverLetter = `Dear Keylane Hiring Team,

I am writing to apply for the Software Developer position at Keylane. With my background in full-stack development and experience at Actemium (VINCI Energies), I am excited about the opportunity to contribute to Keylane's mission in the insurance and pension software space.

In my current role as Software Service Engineer, I develop and maintain applications using .NET, C#, ASP.NET, Python/Flask, and JavaScript for industrial clients. I have hands-on experience with microservices, REST APIs, and cloud platforms (Azure), which aligns well with Keylane's technology stack.

Key highlights:
- Full-stack development with .NET/C# and JavaScript frameworks
- Experience with TypeScript and Vue.js-compatible frontend development
- Proven track record in agile environments (Jira, Azure DevOps)
- BSc Software Engineering from Fontys University of Applied Sciences

I am particularly drawn to Keylane's focus on building scalable SaaS solutions for complex financial domains. I am based in Eindhoven and open to working at your Utrecht or Rotterdam offices.

I would welcome the opportunity to discuss how my skills can contribute to your team.

Kind regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com`;

(async () => {
  console.log('Starting Keylane application...');

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    proxy: proxyServer ? { server: proxyServer, username: proxyUsername, password: proxyPassword } : undefined
  });

  const context = await browser.newContext({
    locale: 'en-US',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 900 }
  });

  const page = await context.newPage();

  // Track navigation and responses
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('keylane') && !url.match(/\.(png|jpg|css|js|svg|woff|ico)$/)) {
      console.log(`  Response: ${response.status()} ${url.substring(0, 120)}`);
    }
  });

  // Step 1: Navigate to the job page
  console.log('\nStep 1: Navigating to job page...');
  try {
    await page.goto(JOB_URL, { waitUntil: 'networkidle', timeout: 30000 });
  } catch (e) {
    console.log('  Navigation warning:', e.message.substring(0, 100));
  }

  await page.waitForTimeout(2000);
  const url1 = page.url();
  const title1 = await page.title();
  console.log(`  URL: ${url1}`);
  console.log(`  Title: ${title1}`);

  await page.screenshot({ path: path.join(screenshotDir, 'keylane-01-job-page.png'), fullPage: true });
  console.log('  Screenshot: keylane-01-job-page.png');

  // Check page content
  const bodyText = await page.evaluate(() => document.body.innerText);
  console.log('  Page text (first 500):', bodyText.substring(0, 500));

  // Check if 404
  if (bodyText.toLowerCase().includes('404') || bodyText.toLowerCase().includes('not found') || bodyText.toLowerCase().includes('page not found')) {
    console.log('\n  WARNING: Page appears to be a 404 / not found page.');
    console.log('  The job posting may no longer be active.');

    // Try the careers home page
    console.log('\nStep 1b: Trying Keylane careers home...');
    try {
      await page.goto('https://careers.keylane.com/jobs/', { waitUntil: 'networkidle', timeout: 30000 });
    } catch (e) {
      console.log('  Navigation warning:', e.message.substring(0, 100));
    }
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(screenshotDir, 'keylane-01b-careers-home.png'), fullPage: true });
    console.log('  Screenshot: keylane-01b-careers-home.png');

    const careersText = await page.evaluate(() => document.body.innerText);
    console.log('  Careers page text (first 800):', careersText.substring(0, 800));

    // Search for Software Developer job on the careers page
    const swDevLinks = await page.$$eval('a', links =>
      links
        .filter(l => l.textContent.toLowerCase().includes('software developer') || l.href.includes('software-developer'))
        .map(l => ({ text: l.textContent.trim(), href: l.href }))
    );

    if (swDevLinks.length > 0) {
      console.log('  Found Software Developer links:', JSON.stringify(swDevLinks));
      // Navigate to first matching link
      const targetLink = swDevLinks[0];
      console.log(`  Navigating to: ${targetLink.href}`);
      try {
        await page.goto(targetLink.href, { waitUntil: 'networkidle', timeout: 30000 });
      } catch (e) {
        console.log('  Navigation warning:', e.message.substring(0, 100));
      }
      await page.waitForTimeout(2000);
      await page.screenshot({ path: path.join(screenshotDir, 'keylane-01c-new-job-page.png'), fullPage: true });
      console.log('  Screenshot: keylane-01c-new-job-page.png');
    } else {
      console.log('  No Software Developer link found on careers page.');
      await browser.close();
      return { status: 'failed', reason: 'Job posting 404 and no alternative found on careers page' };
    }
  }

  // Step 2: Look for Apply button
  console.log('\nStep 2: Looking for Apply button...');

  // Accept cookies if any
  const cookieSelectors = [
    'button:has-text("Accept")',
    'button:has-text("Accept all")',
    'button:has-text("Allow all")',
    'button:has-text("Akkoord")',
    '[id*="cookie"] button',
    '.cookie-consent button',
    '#onetrust-accept-btn-handler',
    '[data-testid="cookie-accept"]'
  ];
  for (const sel of cookieSelectors) {
    try {
      const btn = await page.$(sel);
      if (btn) {
        await btn.click();
        console.log(`  Accepted cookies via: ${sel}`);
        await page.waitForTimeout(1000);
        break;
      }
    } catch (e) {}
  }

  // Find Apply button
  const applySelectors = [
    'a:has-text("Apply")',
    'a:has-text("Apply now")',
    'button:has-text("Apply")',
    'button:has-text("Apply now")',
    'a[href*="apply"]',
    '.apply-button',
    '[data-testid*="apply"]',
    'a:has-text("Solliciteren")',
    'a:has-text("Solliciteer")',
    'button:has-text("Solliciteer")'
  ];

  let applyBtn = null;
  let applyBtnText = '';
  for (const sel of applySelectors) {
    try {
      const btn = await page.$(sel);
      if (btn) {
        applyBtnText = await btn.textContent().catch(() => sel);
        console.log(`  Found Apply button: "${applyBtnText.trim()}" via selector: ${sel}`);
        applyBtn = btn;
        break;
      }
    } catch (e) {}
  }

  if (!applyBtn) {
    // Try to find any button or link that might be for applying
    const allLinks = await page.$$eval('a, button', els =>
      els.map(el => ({ tag: el.tagName, text: el.textContent.trim(), href: el.href || '' }))
         .filter(el => el.text.length > 0 && el.text.length < 50)
    );
    console.log('  All buttons/links found:', JSON.stringify(allLinks.slice(0, 20)));
  }

  if (applyBtn) {
    // Scroll to apply button and screenshot
    await applyBtn.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(screenshotDir, 'keylane-02-apply-button.png') });
    console.log('  Screenshot: keylane-02-apply-button.png');

    // Step 3: Click Apply
    console.log('\nStep 3: Clicking Apply button...');
    await applyBtn.click();
    await page.waitForTimeout(3000);

    const url3 = page.url();
    const title3 = await page.title();
    console.log(`  URL after click: ${url3}`);
    console.log(`  Title: ${title3}`);
    await page.screenshot({ path: path.join(screenshotDir, 'keylane-03-after-apply-click.png'), fullPage: true });
    console.log('  Screenshot: keylane-03-after-apply-click.png');

    // Step 4: Fill in the form
    console.log('\nStep 4: Filling in the application form...');

    // Detect form fields
    const formHTML = await page.evaluate(() => {
      const forms = document.querySelectorAll('form');
      return Array.from(forms).map(f => f.outerHTML.substring(0, 2000)).join('\n---\n');
    });
    console.log('  Forms found (first 1000):', formHTML.substring(0, 1000));

    // Common field selectors for applicant tracking systems
    const fieldMappings = [
      { selectors: ['input[name*="first"], input[id*="first"], input[placeholder*="First"]'], value: applicantDetails.firstName, label: 'First name' },
      { selectors: ['input[name*="last"], input[id*="last"], input[placeholder*="Last"]'], value: applicantDetails.lastName, label: 'Last name' },
      { selectors: ['input[name*="email"], input[id*="email"], input[type="email"]'], value: applicantDetails.email, label: 'Email' },
      { selectors: ['input[name*="phone"], input[id*="phone"], input[type="tel"]'], value: applicantDetails.phone, label: 'Phone' },
      { selectors: ['input[name*="name"]:not([name*="first"]):not([name*="last"]), input[id*="name"]:not([id*="first"]):not([id*="last"])'], value: `${applicantDetails.firstName} ${applicantDetails.lastName}`, label: 'Full name' },
      { selectors: ['textarea[name*="cover"], textarea[id*="cover"], textarea[name*="motivation"], textarea[id*="motivation"], textarea[placeholder*="motivation"]'], value: coverLetter, label: 'Cover letter / motivation' },
    ];

    for (const field of fieldMappings) {
      for (const sel of field.selectors) {
        try {
          const input = await page.$(sel);
          if (input) {
            await input.click({ clickCount: 3 });
            await input.fill(field.value);
            console.log(`  Filled ${field.label} via: ${sel}`);
            break;
          }
        } catch (e) {}
      }
    }

    // Handle resume upload
    console.log('\n  Looking for resume/CV upload field...');
    const uploadSelectors = [
      'input[type="file"]',
      'input[name*="resume"]',
      'input[name*="cv"]',
      'input[accept*="pdf"]'
    ];
    for (const sel of uploadSelectors) {
      try {
        const uploader = await page.$(sel);
        if (uploader) {
          await uploader.setInputFiles(RESUME_PATH);
          console.log(`  Uploaded resume via: ${sel}`);
          await page.waitForTimeout(2000);
          break;
        }
      } catch (e) {
        console.log(`  Upload failed for ${sel}: ${e.message.substring(0, 80)}`);
      }
    }

    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(screenshotDir, 'keylane-04-form-filled.png'), fullPage: true });
    console.log('  Screenshot: keylane-04-form-filled.png');

    // Step 5: Screenshot before submit
    console.log('\nStep 5: Pre-submit screenshot...');

    // Find submit button
    const submitSelectors = [
      'button[type="submit"]',
      'input[type="submit"]',
      'button:has-text("Submit")',
      'button:has-text("Send")',
      'button:has-text("Apply")',
      'button:has-text("Send application")',
      'button:has-text("Verstuur")',
      'button:has-text("Verzenden")'
    ];

    let submitBtn = null;
    for (const sel of submitSelectors) {
      try {
        const btn = await page.$(sel);
        if (btn) {
          submitBtn = btn;
          const btnText = await btn.textContent().catch(() => sel);
          console.log(`  Found submit button: "${btnText.trim()}" via: ${sel}`);
          break;
        }
      } catch (e) {}
    }

    if (submitBtn) {
      await submitBtn.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(screenshotDir, 'keylane-05-pre-submit.png'), fullPage: true });
      console.log('  Screenshot: keylane-05-pre-submit.png (PRE-SUBMIT)');

      // Check for CAPTCHA before submitting
      const pageContent = await page.content();
      if (pageContent.includes('captcha') || pageContent.includes('recaptcha') || pageContent.includes('hcaptcha')) {
        console.log('\n  CAPTCHA detected! Cannot auto-submit.');
        await browser.close();
        return { status: 'failed', reason: 'CAPTCHA detected before form submission' };
      }

      // Step 6: Submit
      console.log('\nStep 6: Submitting application...');
      await submitBtn.click();
      await page.waitForTimeout(5000);

      const finalUrl = page.url();
      const finalTitle = await page.title();
      const finalText = await page.evaluate(() => document.body.innerText);
      console.log(`  Final URL: ${finalUrl}`);
      console.log(`  Final title: ${finalTitle}`);
      console.log('  Final page text (first 800):', finalText.substring(0, 800));

      // Step 7: Confirmation screenshot
      await page.screenshot({ path: path.join(screenshotDir, 'keylane-06-confirmation.png'), fullPage: true });
      console.log('  Screenshot: keylane-06-confirmation.png (POST-SUBMIT)');

      // Determine if successful
      const successIndicators = ['thank you', 'thank-you', 'dank', 'application received', 'submitted', 'confirmation', 'success', 'ontvangen'];
      const isSuccess = successIndicators.some(s => finalText.toLowerCase().includes(s) || finalTitle.toLowerCase().includes(s) || finalUrl.toLowerCase().includes(s));
      console.log(`\n  Application result: ${isSuccess ? 'SUCCESS' : 'UNCERTAIN - check screenshots'}`);
      return { status: isSuccess ? 'applied' : 'uncertain', finalUrl, finalTitle };
    } else {
      console.log('  No submit button found!');
      await page.screenshot({ path: path.join(screenshotDir, 'keylane-05-no-submit.png'), fullPage: true });
      return { status: 'failed', reason: 'No submit button found' };
    }
  } else {
    // No Apply button found - log full page for debugging
    const bodyHtml = await page.content();
    fs.writeFileSync('/home/user/Agents/data/keylane-page-debug.html', bodyHtml);
    console.log('  No Apply button found. Page HTML saved to data/keylane-page-debug.html');
    await browser.close();
    return { status: 'failed', reason: 'No Apply button found on page' };
  }

  await browser.close();
})().catch(async err => {
  console.error('Fatal error:', err.message);
  console.error(err.stack);
  process.exit(1);
});
