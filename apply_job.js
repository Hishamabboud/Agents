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

const coverLetter = `Dear Interactivated Solutions Hiring Team,

I am applying for the .NET + React FHIR Developer for Healthcare SaaS position in Amsterdam (reference: https://englishjobsearch.nl/clickout/eb80853d6f90db7e).

I bring .NET backend and React frontend experience from Actemium, plus GDPR data privacy expertise from my graduation project. I am fluent in English and Dutch.

My details:
- Full Name: Hisham Abboud
- Email: Hisham123@hotmail.com
- Phone: +31 06 4841 2838
- LinkedIn: linkedin.com/in/hisham-abboud
- Location: Eindhoven, Netherlands

I look forward to discussing this opportunity with you.

Best regards,
Hisham Abboud`;

(async () => {
  const screenshotDir = '/home/user/Agents/output/screenshots';
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    proxy: proxyServer ? { server: proxyServer, username: proxyUsername, password: proxyPassword } : undefined
  });

  const context = await browser.newContext({
    locale: 'nl-NL',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 900 }
  });

  const page = await context.newPage();

  // Intercept form submissions and network requests
  let formSubmitResponse = null;
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('interactivated.me') && !url.includes('.png') && !url.includes('.css') && !url.includes('.js')) {
      try {
        const body = await response.text();
        console.log(`Response: ${response.status()} ${url.substring(0, 100)}`);
        if (body.length < 5000) console.log('Body:', body.substring(0, 500));
      } catch(e) {}
    }
  });

  console.log('Loading interactivated.me with cookie accept...');
  await page.goto('https://www.interactivated.me', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  
  // Accept cookies if dialog appears
  const cookieBtn = await page.$('button:has-text("ALLOW ALL"), button:has-text("Accept"), button:has-text("Akkoord"), .cookie-accept');
  if (cookieBtn) {
    console.log('Accepting cookies...');
    await cookieBtn.click();
    await page.waitForTimeout(1000);
  }

  // Scroll to contact form  
  await page.evaluate(() => {
    const form = document.querySelector('form');
    if (form) form.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  await page.waitForTimeout(2000);
  
  await page.screenshot({ path: path.join(screenshotDir, '19-contact-form.png') });
  console.log('Screenshot: 19-contact-form.png');
  
  // Fill in the form
  const nameInput = await page.$('input[name="name"], input[placeholder="Your Name"]');
  const emailInput = await page.$('input[name="email"], input[placeholder="Email"]');
  const messageInput = await page.$('textarea[name="message"], textarea[placeholder="Message"]');
  
  if (nameInput) {
    await nameInput.click({ clickCount: 3 });
    await nameInput.fill('Hisham Abboud');
    console.log('Name filled');
  }
  
  if (emailInput) {
    await emailInput.click({ clickCount: 3 });
    await emailInput.fill('Hisham123@hotmail.com');
    console.log('Email filled');
  }
  
  if (messageInput) {
    await messageInput.click({ clickCount: 3 });
    await messageInput.fill(coverLetter);
    console.log('Message filled');
  }

  await page.waitForTimeout(1000);
  
  // Scroll to see the form
  await page.evaluate(() => {
    const form = document.querySelector('form');
    if (form) form.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  await page.waitForTimeout(1000);
  
  await page.screenshot({ path: path.join(screenshotDir, '20-form-filled.png') });
  console.log('Screenshot: 20-form-filled.png');
  
  // Find submit button
  const submitBtn = await page.$('button[type="submit"], input[type="submit"], form button');
  if (submitBtn) {
    const btnText = await submitBtn.textContent().catch(() => 'N/A');
    console.log('Submit button text:', btnText.trim());
    await submitBtn.scrollIntoViewIfNeeded();
    
    await page.screenshot({ path: path.join(screenshotDir, '21-before-submit.png') });
    console.log('Screenshot: 21-before-submit.png - ABOUT TO SUBMIT');
    
    // Click submit
    await submitBtn.click();
    console.log('Submitted!');
    
    // Wait for response
    await page.waitForTimeout(5000);
    
    const finalUrl = page.url();
    const finalTitle = await page.title();
    const finalText = await page.evaluate(() => document.body.innerText);
    
    console.log('Final URL:', finalUrl);
    console.log('Final title:', finalTitle);
    console.log('Final text (first 1000):', finalText.substring(0, 1000));
    
    await page.screenshot({ path: path.join(screenshotDir, '22-after-submit.png') });
    console.log('Screenshot: 22-after-submit.png');
    
    // Check if form was cleared (success indicator)
    const nameValue = await page.$eval('input[name="name"]', el => el.value).catch(() => 'not found');
    const emailValue = await page.$eval('input[name="email"]', el => el.value).catch(() => 'not found');
    console.log('Name field after submit:', nameValue);
    console.log('Email field after submit:', emailValue);
  }

  await browser.close();
})().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
