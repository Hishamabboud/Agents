const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const execPath = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
  const resumePath = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
  
  console.log('Launching browser...');
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: execPath,
    proxy: {
      server: 'http://21.0.0.209:15004',
      username: 'container_container_01AreZs7BM1myrQbqsHGUfzc--claude_code_remote--6c5e86',
      password: 'jwt_eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6Iks3dlRfYUVsdXIySGdsYVJ0QWJ0UThDWDU4dFFqODZIRjJlX1VsSzZkNEEifQ.eyJpc3MiOiJhbnRocm9waWMtZWdyZXNzLWNvbnRyb2wiLCJvcmdhbml6YXRpb25fdXVpZCI6ImNiZDBkNGRmLTUxNDItNDAwYi05MzM3LWIzMDFhNDBjNmNmMSIsImlhdCI6MTc3MzE0MDUyNiwiZXhwIjoxNzczMTU0OTI2LCJhbGxvd2VkX2hvc3RzIjoiKiIsImlzX2hpcGFhX3JlZ3VsYXRlZCI6ImZhbHNlIiwiaXNfYW50X2hpcGkiOiJmYWxzZSIsInVzZV9lZ3Jlc3NfZ2F0ZXdheSI6InRydWUiLCJzZXNzaW9uX2lkIjoic2Vzc2lvbl8wMTZoRU5XZWRGNml6UmNjWWE4Qk44YlkiLCJjb250YWluZXJfaWQiOiJjb250YWluZXJfMDFBcmVaczdCTTFteXJRYnFzSEdVZnpjLS1jbGF1ZGVfY29kZV9yZW1vdGUtLTZjNWU4NiJ9.IBMgMF3yMqGvA6CpqXyk-PZOGZVCOHlMxXDvCxGGm-Vfgkq3O81FwBgZvPP0het-jC3GI2x_qsKsV64sTayt6A',
    },
    args: [
      '--no-sandbox', 
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
    ]
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  // Capture the apply POST request/response
  let applyResponse = null;
  page.on('response', async response => {
    if (response.url().includes('/api/v1/jobs/') && response.url().includes('/apply') && !response.url().includes('/apply/')) {
      try {
        const text = await response.text();
        console.log('APPLY API RESPONSE:', response.status());
        console.log('APPLY BODY:', text.substring(0, 500));
        applyResponse = { status: response.status(), body: text };
        fs.writeFileSync('/home/user/Agents/data/coolgames-apply-response.txt', text);
      } catch(e) {}
    }
  });

  console.log('Loading application form...');
  await page.goto('https://apply.workable.com/coolgames/j/3654334706/apply/', { 
    waitUntil: 'networkidle',
    timeout: 60000 
  });
  await page.waitForTimeout(3000);
  
  // Screenshot 1: form loaded
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-01-form-loaded.png', fullPage: true });
  console.log('Screenshot 1: form loaded');

  // ===== FILL PERSONAL INFORMATION =====
  console.log('Filling personal information...');
  
  // First name
  await page.fill('input[name="firstname"]', 'Hisham');
  // Last name
  await page.fill('input[name="lastname"]', 'Abboud');
  // Email
  await page.fill('input[name="email"]', 'hiaham123@hotmail.com');
  // Headline
  const headlineField = page.locator('input[name="headline"]');
  if (await headlineField.count() > 0) {
    await headlineField.fill('Software Engineer | .NET, C#, JavaScript, Python');
  }
  // Phone - need to handle country code selector
  const phoneField = page.locator('input[name="phone"]');
  if (await phoneField.count() > 0) {
    await phoneField.fill('+31064841283');
  }
  // Address
  const addressField = page.locator('input[name="address"]');
  if (await addressField.count() > 0) {
    await addressField.fill('Eindhoven, North Brabant, Netherlands');
  }
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-02-personal-filled.png', fullPage: true });
  console.log('Screenshot 2: personal info filled');

  // ===== UPLOAD RESUME =====
  console.log('Uploading resume...');
  const resumeInput = page.locator('input[type="file"]').first();
  await resumeInput.setInputFiles(resumePath);
  await page.waitForTimeout(3000);
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-03-resume-uploaded.png', fullPage: true });
  console.log('Screenshot 3: after resume upload');

  // ===== SCROLL DOWN TO COVER LETTER =====
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
  await page.waitForTimeout(1000);

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

  // Find cover letter textarea
  const coverLetterSelector = 'textarea[name="cover_letter"], textarea[id*="cover"], [data-ui="cover_letter"] textarea';
  let coverLetterField = page.locator('textarea').nth(0);
  
  // Try to find cover letter by looking at textareas near "Cover letter" label
  const allTextareas = page.locator('textarea');
  const count = await allTextareas.count();
  console.log('Found textareas:', count);
  
  // Fill cover letter - first textarea should be it based on form structure
  if (count > 0) {
    await allTextareas.nth(0).fill(coverLetterText);
    console.log('Cover letter filled');
  }
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-04-cover-letter.png', fullPage: true });
  console.log('Screenshot 4: cover letter filled');

  // ===== SCROLL DOWN MORE =====
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(1000);

  // ===== SCREENING QUESTIONS =====
  console.log('Filling screening questions...');
  
  // Notice period
  const allInputs = await page.locator('input[type="text"], input[type="number"]').all();
  console.log('Text inputs found:', allInputs.length);
  
  // Find screening question inputs by looking at page structure
  const pageContent = await page.evaluate(() => document.body.innerHTML);
  
  // QA_11295526: What is your notice period?
  // QA_11295527: What is your expected hourly rate?
  // QA_11309707: CET hours confirmation (boolean)
  
  // Try to fill notice period
  const noticePeriodInputs = page.locator('input[name*="QA_11295526"], [data-ui*="QA_11295526"] input');
  if (await noticePeriodInputs.count() > 0) {
    await noticePeriodInputs.first().fill('1 month');
    console.log('Notice period filled');
  } else {
    console.log('Notice period input not found by name, trying by position...');
    // Find inputs after specific labels
    const labels = await page.locator('label, [class*="label"]').all();
    for (const label of labels) {
      const text = await label.innerText().catch(() => '');
      if (text.includes('notice period')) {
        console.log('Found notice period label');
        const input = await label.locator('..').locator('input').first();
        if (await input.count() > 0) await input.fill('1 month');
      }
    }
  }
  
  // Try hourly rate
  const hourlyRateInputs = page.locator('input[name*="QA_11295527"], [data-ui*="QA_11295527"] input');
  if (await hourlyRateInputs.count() > 0) {
    await hourlyRateInputs.first().fill('45-55');
    console.log('Hourly rate filled');
  }
  
  // CET hours - boolean checkbox/toggle
  const cetInputs = page.locator('input[name*="QA_11309707"]');
  if (await cetInputs.count() > 0) {
    const cetType = await cetInputs.first().getAttribute('type');
    if (cetType === 'checkbox') {
      await cetInputs.first().check();
    } else {
      // It might be a yes/no radio button
      const yesOption = page.locator('[name*="QA_11309707"][value="true"], [name*="QA_11309707"][value="yes"]');
      if (await yesOption.count() > 0) await yesOption.first().check();
    }
    console.log('CET hours confirmed');
  }
  
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-05-questions.png', fullPage: true });
  console.log('Screenshot 5: questions filled');
  
  // Save full page HTML for inspection
  const html = await page.content();
  fs.writeFileSync('/home/user/Agents/data/coolgames-form-filled.html', html);
  console.log('HTML saved for inspection');

  await browser.close();
  console.log('Done filling form!');
})().catch(err => {
  console.error('Fatal:', err.message, err.stack ? err.stack.substring(0, 300) : '');
  process.exit(1);
});
