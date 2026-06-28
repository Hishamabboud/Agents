const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const COVER_LETTER = `Dear Hiring Team,

I am writing to express my strong interest in the .NET Developer Industrial Automation position at Hexapole Automatisering. Your focus on building software solutions for industrial automation and logistics resonates deeply with my current professional work, and I am excited about the opportunity to contribute to your team.

In my current role as a Software Service Engineer at Actemium (VINCI Energies), I work daily at the intersection of industrial systems and software development. I design and maintain Manufacturing Execution Systems (MES) using .NET, C#, and ASP.NET, translating complex industrial requirements into reliable software solutions. This hands-on experience with industrial automation gives me a strong foundation that directly aligns with Hexapole's core business.

My technical skill set is a close match for your requirements. I have solid experience with C# and .NET Core, complemented by proficiency in Python, JavaScript, and SQL. During my internship at ASML, I developed testing frameworks and worked within Azure and Kubernetes environments, which sharpened my ability to deliver robust, scalable solutions in high-tech industrial settings. My project work, including building the CogitatAI platform from the ground up, demonstrates my ability to architect and deliver complete software products independently.

Beyond technical skills, I bring a multilingual perspective — I am fluent in English, Dutch, and Arabic — which supports effective communication in diverse teams and with international clients. My entrepreneurial drive, evident from founding CogitatAI, means I take ownership of challenges and consistently look for ways to improve processes and deliver value.

I hold a BSc in Software Engineering from Fontys University of Applied Sciences in Eindhoven, and I am eager to bring my industrial automation experience and .NET expertise to Hexapole Automatisering. I would welcome the opportunity to discuss how my background can contribute to your projects in Alkmaar.

I am available for an interview at your earliest convenience and look forward to hearing from you.

Best regards,
Hisham Abboud`;

const SCREENSHOT_DIR = '/home/user/Agents/output/screenshots';

function ts() {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
}

async function takeScreenshot(page, name) {
  const filepath = path.join(SCREENSHOT_DIR, `hexapole-${name}.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log('Screenshot saved:', filepath);
  return filepath;
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 }
  });

  const page = await context.newPage();

  // --- Step 1: Screenshot the job page ---
  console.log('Navigating to Hexapole job page...');
  try {
    await page.goto('https://hexapole.com/en/vacancies/net-developer-net-core-industrial-automation/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(2000);
  } catch (e) {
    console.log('Page load timeout or error, taking screenshot anyway:', e.message);
  }

  await takeScreenshot(page, '01-job-page');

  const title = await page.title();
  console.log('Page title:', title);

  // Scroll to bottom to see the contact/apply info
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(1000);
  await takeScreenshot(page, '02-job-page-bottom');

  // Extract page text to find application instructions
  const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 3000));
  console.log('\n--- Page content (first 3000 chars) ---');
  console.log(bodyText);
  console.log('--- End of page content ---\n');

  // --- Step 2: Try to navigate to Outlook Web to send email ---
  console.log('Navigating to Outlook Web...');
  const mailPage = await context.newPage();

  try {
    await mailPage.goto('https://outlook.live.com/mail/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await mailPage.waitForTimeout(3000);

    const outlookUrl = mailPage.url();
    const outlookTitle = await mailPage.title();
    console.log('Outlook URL:', outlookUrl);
    console.log('Outlook title:', outlookTitle);

    await takeScreenshot(mailPage, '03-outlook-initial');

    const isLoginPage = outlookUrl.includes('login') || outlookUrl.includes('signin') ||
      outlookTitle.toLowerCase().includes('sign in') || outlookTitle.toLowerCase().includes('log in');

    if (isLoginPage) {
      console.log('Outlook requires login. Attempting to log in with hiaham123@hotmail.com...');

      // Try to fill email field
      try {
        const emailInput = await mailPage.waitForSelector('input[type="email"], input[name="loginfmt"], #i0116', { timeout: 8000 });
        await emailInput.fill('hiaham123@hotmail.com');
        await mailPage.waitForTimeout(500);
        await takeScreenshot(mailPage, '04-outlook-email-entered');

        // Click Next
        const nextBtn = await mailPage.$('input[type="submit"], button[type="submit"], #idSIButton9');
        if (nextBtn) {
          await nextBtn.click();
          await mailPage.waitForTimeout(3000);
          await takeScreenshot(mailPage, '05-outlook-after-email');
        }

        // Now we'd need the password — we don't have it stored
        console.log('Reached password step. No stored password available — cannot complete login automatically.');
        await takeScreenshot(mailPage, '06-outlook-password-step');
      } catch (loginErr) {
        console.log('Login attempt error:', loginErr.message);
        await takeScreenshot(mailPage, '04-outlook-login-error');
      }
    } else {
      console.log('Outlook appears to be accessible (possibly already logged in).');
      await takeScreenshot(mailPage, '04-outlook-logged-in');

      // Try to compose a new email
      try {
        // Look for New Email / Compose button
        const newEmailBtn = await mailPage.$('[aria-label*="New mail"], [aria-label*="Compose"], button[title*="New"], [data-automationid="newMailButton"]');
        if (newEmailBtn) {
          await newEmailBtn.click();
          await mailPage.waitForTimeout(2000);
          await takeScreenshot(mailPage, '05-compose-open');

          // Fill To field
          const toField = await mailPage.$('[aria-label="To"], input[placeholder*="To"]');
          if (toField) {
            await toField.fill('w.rebel@hexapole.com');
            await mailPage.keyboard.press('Tab');
            await mailPage.waitForTimeout(500);
          }

          // Fill Subject
          const subjectField = await mailPage.$('[aria-label="Subject"], input[placeholder*="Subject"]');
          if (subjectField) {
            await subjectField.fill('Application: .NET Developer | Industrial Automation — Hisham Abboud');
          }

          // Fill body
          const bodyField = await mailPage.$('[aria-label="Message body"], [contenteditable="true"].ms-rtestate-field, div[role="textbox"]');
          if (bodyField) {
            await bodyField.click();
            await bodyField.fill(COVER_LETTER);
          }

          await takeScreenshot(mailPage, '06-email-composed');
          console.log('Email composed. Taking pre-submit screenshot...');

          // Send the email
          const sendBtn = await mailPage.$('[aria-label="Send"], button[title="Send"]');
          if (sendBtn) {
            await takeScreenshot(mailPage, '07-pre-send');
            await sendBtn.click();
            await mailPage.waitForTimeout(3000);
            await takeScreenshot(mailPage, '08-after-send');
            console.log('Email sent!');
          } else {
            console.log('Send button not found — could not send email.');
          }
        } else {
          console.log('Compose button not found in Outlook.');
        }
      } catch (composeErr) {
        console.log('Error composing email:', composeErr.message);
        await takeScreenshot(mailPage, '05-compose-error');
      }
    }
  } catch (outlookErr) {
    console.log('Error loading Outlook:', outlookErr.message);
    await takeScreenshot(mailPage, '03-outlook-error');
  }

  await browser.close();

  console.log('\n=== SUMMARY ===');
  console.log('Job: .NET Developer | Industrial Automation at Hexapole Automatisering');
  console.log('Application email: w.rebel@hexapole.com');
  console.log('Applicant: Hisham Abboud <hiaham123@hotmail.com>');
  console.log('Screenshots saved to:', SCREENSHOT_DIR);
  console.log('Note: Application is email-based. No web form available.');
})().catch(e => {
  console.error('Fatal error:', e.message);
  console.error(e.stack);
  process.exit(1);
});
