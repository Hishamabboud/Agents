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
      console.log('APPLY POST RESPONSE STATUS:', response.status());
      console.log('APPLY POST BODY:', text.substring(0, 500));
      fs.writeFileSync('/home/user/Agents/data/coolgames-submit-response.txt', JSON.stringify({status: response.status(), body: text}, null, 2));
    }
  });

  console.log('Loading form...');
  await page.goto('https://apply.workable.com/coolgames/j/3654334706/apply/', { 
    waitUntil: 'networkidle',
    timeout: 60000 
  });
  
  // Wait for the form to actually render (wait for firstname input)
  console.log('Waiting for form to render...');
  try {
    await page.waitForSelector('input[name="firstname"]', { timeout: 30000 });
    console.log('Form rendered!');
  } catch(e) {
    console.log('Form not ready yet, checking page state...');
    const content = await page.evaluate(() => document.body.innerText);
    console.log('Page content:', content.substring(0, 300));
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-debug.png', fullPage: true });
  }
  
  // Handle cookie consent - click through it
  const cookieDialog = page.locator('[data-ui="cookie-consent"]');
  const backdrop = page.locator('[data-ui="backdrop"]');
  
  let attempts = 0;
  while (attempts < 5) {
    const cookieVisible = await cookieDialog.isVisible().catch(() => false);
    if (!cookieVisible) break;
    
    console.log(`Cookie dialog visible (attempt ${attempts + 1}), dismissing...`);
    
    // Try clicking accept button
    const btns = page.locator('[data-ui="cookie-consent"] button');
    const btnCount = await btns.count();
    for (let i = 0; i < btnCount; i++) {
      const text = await btns.nth(i).innerText().catch(() => '');
      console.log(`  Button ${i}: "${text}"`);
    }
    
    // Click the last button (usually "Accept" or "OK")
    if (btnCount > 0) {
      await btns.last().click({ force: true });
    }
    await page.waitForTimeout(2000);
    attempts++;
  }
  
  // Force remove overlay elements via JS
  await page.evaluate(() => {
    const els = document.querySelectorAll('[data-ui="backdrop"], [data-ui="cookie-consent"], [role="dialog"]');
    els.forEach(el => {
      el.style.display = 'none';
      el.style.visibility = 'hidden';
      el.style.pointerEvents = 'none';
    });
  });
  
  // Wait for form to be visible
  await page.waitForSelector('input[name="firstname"]', { timeout: 20000 });
  console.log('Form input visible!');
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-01-form-ready.png', fullPage: true });
  console.log('Screenshot 1: form ready');

  // ===== FILL FORM =====
  console.log('Filling form...');
  await page.fill('input[name="firstname"]', 'Hisham');
  await page.fill('input[name="lastname"]', 'Abboud');
  await page.fill('input[name="email"]', 'hiaham123@hotmail.com');
  
  try { await page.fill('input[name="headline"]', 'Software Engineer | .NET, C#, JavaScript, Python'); } catch(e) {}
  try { await page.fill('input[name="phone"]', '+31064841283'); } catch(e) {}
  try { await page.fill('input[name="address"]', 'Eindhoven, North Brabant, Netherlands'); } catch(e) {}
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-02-personal.png', fullPage: true });
  console.log('Screenshot 2: personal info filled');

  // ===== UPLOAD RESUME =====
  console.log('Uploading resume...');
  const fileInputs = await page.locator('input[type="file"]').all();
  console.log('File inputs found:', fileInputs.length);
  
  // Find resume input (accepts .pdf)
  let resumeInputIndex = 1; // Default to second file input
  for (let i = 0; i < fileInputs.length; i++) {
    const accept = await fileInputs[i].getAttribute('accept').catch(() => '');
    console.log(`  File ${i} accept: ${accept}`);
    if (accept && accept.includes('.pdf')) {
      resumeInputIndex = i;
    }
  }
  
  await page.locator('input[type="file"]').nth(resumeInputIndex).setInputFiles(resumePath);
  await page.waitForTimeout(3000);
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-03-resume.png', fullPage: true });
  console.log('Screenshot 3: resume uploaded');

  // ===== COVER LETTER =====
  const coverLetterText = `Dear CoolGames Hiring Team,

I am writing to express my strong interest in the Game Developer position at CoolGames. As a software engineer with hands-on experience in JavaScript, full-stack web development, and agile product delivery, I am excited by the opportunity to contribute to HTML5 casual game development at a studio whose titles are enjoyed by millions of players on platforms like Netflix, Discord, and Facebook.

In my current role as a Software Service Engineer at Actemium (VINCI Energies), I build and maintain production-grade applications using .NET, C#, ASP.NET, Python/Flask, and JavaScript, working under real-time production constraints where code quality, performance, and reliability are non-negotiable. This has sharpened my ability to write clean, readable, and maintainable code, and to balance speed with quality in a way that directly maps to the cadence of game development.

My JavaScript experience extends to building modern frontend interfaces. I independently developed CogitatAI, a full-stack AI platform with a JavaScript-based frontend and a Python/Flask backend deployed on cloud infrastructure. This project gave me practical experience in managing the full development lifecycle from inception through deployment and iteration, which aligns well with CoolGames' expectation that developers contribute across the full game lifecycle, from new title development to live-ops and maintenance.

During my internship at ASML, I worked in an agile team using Azure, Jira, and Kubernetes for CI/CD, so I am comfortable in structured, professional engineering environments. I take ownership of my work, communicate risks early, and actively help improve the codebase rather than just implementing tickets.

CoolGames' international team, the quality of games you ship, and your partnerships with major global platforms make this a role I am genuinely excited about. I am available for CET hours and based in Eindhoven, Netherlands.

Thank you for considering my application.

Kind regards,
Hisham Abboud`;

  console.log('Filling cover letter...');
  const textareas = await page.locator('textarea').all();
  console.log('Textareas:', textareas.length);
  if (textareas.length > 0) {
    await textareas[0].fill(coverLetterText);
    console.log('Cover letter filled');
  }
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-04-cover-letter.png', fullPage: true });
  console.log('Screenshot 4: cover letter');

  // ===== SCREENING QUESTIONS =====
  console.log('Filling screening questions...');
  
  // Notice period
  try {
    await page.fill('[name="QA_11295526"]', '1 month');
    console.log('Notice period filled');
  } catch(e) { console.log('Notice period error:', e.message.substring(0, 100)); }
  
  // Hourly rate
  try {
    await page.fill('[name="QA_11295527"]', '45-55');
    console.log('Hourly rate filled');
  } catch(e) { console.log('Hourly rate error:', e.message.substring(0, 100)); }
  
  // CET hours (radio/boolean) - use JS click
  await page.evaluate(() => {
    const inputs = document.querySelectorAll('[name="QA_11309707"]');
    for (const input of inputs) {
      console.log('CET input:', input.type, input.value);
      if (input.value === 'true' || input.value === '1') {
        input.checked = true;
        input.dispatchEvent(new Event('change', { bubbles: true }));
        input.click();
      }
    }
  });
  console.log('CET hours set via JS');
  
  // Scroll to see all questions
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(1000);
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-05-questions.png', fullPage: true });
  console.log('Screenshot 5: questions');

  // ===== PRE-SUBMIT SCREENSHOT =====
  console.log('Taking pre-submit screenshot...');
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(500);
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-06-before-submit.png', fullPage: true });
  console.log('Screenshot 6: PRE-SUBMIT');

  // ===== SUBMIT =====
  console.log('Finding submit button...');
  const submitBtn = page.locator('button[type="submit"]').first();
  const submitVisible = await submitBtn.isVisible().catch(() => false);
  console.log('Submit button visible:', submitVisible);
  
  if (submitVisible) {
    const btnText = await submitBtn.innerText().catch(() => '');
    console.log('Submit button text:', btnText);
    
    console.log('SUBMITTING APPLICATION...');
    await submitBtn.click();
    await page.waitForTimeout(10000);
    
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-07-submitted.png', fullPage: true });
    console.log('Screenshot 7: after submit');
    
    const finalContent = await page.evaluate(() => document.body.innerText);
    console.log('=== RESULT ===');
    console.log(finalContent.substring(0, 600));
    fs.writeFileSync('/home/user/Agents/data/coolgames-submit-result.txt', finalContent);
  } else {
    // Find all buttons
    const allBtns = await page.locator('button').all();
    console.log('All buttons found:');
    for (const btn of allBtns) {
      const t = await btn.innerText().catch(() => '');
      const type = await btn.getAttribute('type').catch(() => '');
      console.log(`  type=${type} text="${t}"`);
    }
  }

  await browser.close();
  console.log('Done!');
})().catch(err => {
  console.error('Fatal:', err.message.substring(0, 400));
});
