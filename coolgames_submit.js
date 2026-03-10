const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const execPath = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
  const resumePath = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
  
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: execPath,
    proxy: {
      server: 'http://21.0.0.209:15004',
      username: 'container_container_01AreZs7BM1myrQbqsHGUfzc--claude_code_remote--6c5e86',
      password: 'jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6ImNiZDBkNGRmLTUxNDItNDAwYi05MzM3LWIzMDFhNDBjNmNmMSIsImlhdCI6MTc3MzE0MDUyNiwiZXhwIjoxNzczMTU0OTI2LCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6InRydWUiLCJzZXNzaW9uX2lkIjoic2Vzc2lvbl8wMTZoRU5XZWRGNml6UmNjWWE4Qk44YlkiLCJjb250YWluZXJfaWQiOiJjb250YWluZXJfMDFBcmVaczdCTTFteXJRYnFzSEdVZnpjLS1jbGF1ZGVfY29kZV9yZW1vdGUtLTZjNWU4NiJ9.IBMgMF3yMqGvA6CpqXyk-PZOGZVCOHlMxXDvCxGGm-Vfgkq3O81FwBgZvPP0het-jC3GI2x_qsKsV64sTayt6A',
    },
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  // Capture apply API response
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/v1/jobs/') && url.endsWith('/apply')) {
      const text = await response.text().catch(() => '');
      console.log('APPLY POST RESPONSE:', response.status(), text.substring(0, 300));
      fs.writeFileSync('/home/user/Agents/data/coolgames-submit-response.txt', JSON.stringify({status: response.status(), body: text}, null, 2));
    }
  });

  console.log('Loading form...');
  await page.goto('https://apply.workable.com/coolgames/j/3654334706/apply/', { 
    waitUntil: 'networkidle',
    timeout: 60000 
  });
  await page.waitForTimeout(2000);
  
  // Handle cookie consent dialog
  console.log('Checking for cookie consent dialog...');
  const cookieDialog = page.locator('[data-ui="cookie-consent"]');
  if (await cookieDialog.isVisible().catch(() => false)) {
    console.log('Cookie consent dialog found - accepting...');
    // Accept all cookies
    const acceptBtn = page.locator('[data-ui="cookie-consent"] button:has-text("Accept"), [data-ui="cookie-consent"] button:has-text("accept"), [data-ui="cookie-consent"] [class*="accept"]');
    if (await acceptBtn.count() > 0) {
      await acceptBtn.first().click({ force: true });
    } else {
      // Try any button in the dialog
      const dialogBtns = page.locator('[data-ui="cookie-consent"] button');
      const btnCount = await dialogBtns.count();
      console.log('Cookie dialog buttons:', btnCount);
      for (let i = 0; i < btnCount; i++) {
        const text = await dialogBtns.nth(i).innerText().catch(() => '');
        console.log(`  Button ${i}: "${text}"`);
      }
      if (btnCount > 0) await dialogBtns.last().click({ force: true });
    }
    await page.waitForTimeout(2000);
    
    // Check if dialog still visible
    const stillVisible = await cookieDialog.isVisible().catch(() => false);
    console.log('Cookie dialog still visible:', stillVisible);
  } else {
    console.log('No cookie consent dialog');
  }
  
  // Also dismiss via JavaScript
  await page.evaluate(() => {
    const backdrop = document.querySelector('[data-ui="backdrop"]');
    const cookieModal = document.querySelector('[data-ui="cookie-consent"]');
    if (backdrop) backdrop.remove();
    if (cookieModal) cookieModal.remove();
  });
  
  await page.waitForTimeout(1000);
  
  // Screenshot after dismissing dialog
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-01-form-loaded.png', fullPage: true });
  console.log('Screenshot 1: form loaded (after cookie dismiss)');

  // ===== FILL PERSONAL INFORMATION =====
  console.log('Filling personal info...');
  await page.fill('input[name="firstname"]', 'Hisham');
  await page.fill('input[name="lastname"]', 'Abboud');
  await page.fill('input[name="email"]', 'hiaham123@hotmail.com');
  
  const headlineField = page.locator('input[name="headline"]');
  if (await headlineField.isVisible().catch(() => false)) {
    await headlineField.fill('Software Engineer | .NET, C#, JavaScript, Python');
  }
  
  const phoneField = page.locator('input[name="phone"]');
  if (await phoneField.isVisible().catch(() => false)) {
    await phoneField.fill('+31064841283');
  }
  
  const addressField = page.locator('input[name="address"]');
  if (await addressField.isVisible().catch(() => false)) {
    await addressField.fill('Eindhoven, North Brabant, Netherlands');
  }
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-02-personal.png', fullPage: true });
  console.log('Screenshot 2: personal filled');

  // ===== UPLOAD RESUME =====
  console.log('Uploading resume...');
  // Find the resume file input (not photo)
  const fileInputs = page.locator('input[type="file"]');
  const fileCount = await fileInputs.count();
  console.log('File inputs found:', fileCount);
  
  // The second file input should be the resume (first is photo)
  for (let i = 0; i < fileCount; i++) {
    const accept = await fileInputs.nth(i).getAttribute('accept');
    console.log(`  File input ${i}: accept=${accept}`);
  }
  
  // Resume input should accept .pdf
  const resumeInput = fileInputs.nth(1); // Second one is usually resume
  await resumeInput.setInputFiles(resumePath);
  await page.waitForTimeout(3000);
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-03-resume.png', fullPage: true });
  console.log('Screenshot 3: resume uploaded');

  // ===== COVER LETTER =====
  const coverLetterText = `Dear CoolGames Hiring Team,

I am writing to express my strong interest in the Game Developer position at CoolGames. As a software engineer with hands-on experience in JavaScript, full-stack web development, and agile product delivery, I am excited by the opportunity to contribute to HTML5 casual game development at a studio whose titles are enjoyed by millions of players on platforms like Netflix, Discord, and Facebook.

In my current role as a Software Service Engineer at Actemium (VINCI Energies), I build and maintain production-grade applications using .NET, C#, ASP.NET, Python/Flask, and JavaScript — working under real-time production constraints where code quality, performance, and reliability are non-negotiable. This has sharpened my ability to write clean, readable, and maintainable code, and to balance speed with quality in a way that directly maps to the cadence of game development.

My JavaScript experience extends to building modern frontend interfaces. I independently developed CogitatAI, a full-stack AI platform with a JavaScript-based frontend and a Python/Flask backend deployed on cloud infrastructure. This project gave me practical experience in managing the full development lifecycle — from inception through deployment and iteration — which aligns well with CoolGames' expectation that developers contribute across the full game lifecycle, from new title development to live-ops and maintenance.

During my internship at ASML, I worked in an agile team using Azure, Jira, and Kubernetes for CI/CD — so I am comfortable in structured, professional engineering environments. I take ownership of my work, communicate risks early, and actively help improve the codebase rather than just implementing tickets.

CoolGames' international team, the quality of games you ship, and your partnerships with major global platforms make this a role I am genuinely excited about. I am available for CET hours (I am based in Eindhoven, Netherlands), and I would be glad to work hybrid in Amsterdam as needed.

Thank you for considering my application. I look forward to the opportunity to contribute to your team.

Kind regards,
Hisham Abboud`;

  console.log('Filling cover letter...');
  const textareas = page.locator('textarea');
  const taCount = await textareas.count();
  console.log('Textareas found:', taCount);
  
  // Fill first textarea (cover letter)
  if (taCount > 0) {
    await textareas.nth(0).fill(coverLetterText);
  }
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-04-cover-letter.png', fullPage: true });
  console.log('Screenshot 4: cover letter');

  // ===== SCREENING QUESTIONS =====
  console.log('Filling screening questions...');
  
  // Notice period - QA_11295526
  const noticePeriod = page.locator('[name="QA_11295526"]');
  if (await noticePeriod.count() > 0) {
    await noticePeriod.fill('1 month');
    console.log('Notice period filled');
  }
  
  // Hourly rate - QA_11295527
  const hourlyRate = page.locator('[name="QA_11295527"]');
  if (await hourlyRate.count() > 0) {
    await hourlyRate.fill('45-55');
    console.log('Hourly rate filled');
  }
  
  // CET hours - QA_11309707 (boolean/radio)
  // Use force: true to click through any overlapping elements
  const cetYes = page.locator('[name="QA_11309707"][value="true"]');
  if (await cetYes.count() > 0) {
    // Get the parent label/button and click that instead
    await page.evaluate(() => {
      const radios = document.querySelectorAll('[name="QA_11309707"]');
      for (const r of radios) {
        if (r.value === 'true') {
          r.click();
          r.checked = true;
          r.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
    });
    console.log('CET hours confirmed via JS');
  }
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-05-questions.png', fullPage: true });
  console.log('Screenshot 5: questions filled');

  // ===== SUBMIT BUTTON =====
  console.log('Looking for submit button...');
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(1000);
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-06-before-submit.png', fullPage: true });
  console.log('Screenshot 6: before submit (IMPORTANT)');
  
  // Find submit button
  const submitBtn = page.locator('button[type="submit"], button:has-text("Submit"), button:has-text("Apply")');
  const submitCount = await submitBtn.count();
  console.log('Submit buttons found:', submitCount);
  
  if (submitCount > 0) {
    const btnText = await submitBtn.first().innerText();
    console.log('Submit button text:', btnText);
    console.log('*** READY TO SUBMIT - CLICKING ***');
    await submitBtn.first().click();
    await page.waitForTimeout(8000);
    
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-07-after-submit.png', fullPage: true });
    console.log('Screenshot 7: after submit');
    
    const finalContent = await page.evaluate(() => document.body.innerText);
    console.log('Final page content:', finalContent.substring(0, 500));
    fs.writeFileSync('/home/user/Agents/data/coolgames-submit-result.txt', finalContent);
  } else {
    console.log('No submit button found!');
  }

  await browser.close();
  console.log('Done!');
})().catch(err => {
  console.error('Fatal error:', err.message.substring(0, 500));
  process.exit(1);
});
