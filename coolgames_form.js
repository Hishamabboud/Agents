const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const execPath = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
  
  console.log('Launching browser with proxy...');
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

  // Intercept API calls
  const applyRequests = [];
  page.on('request', request => {
    if (request.url().includes('/apply')) {
      console.log('Apply request intercepted:', request.method(), request.url());
      applyRequests.push({
        method: request.method(),
        url: request.url(),
        headers: request.headers(),
        postData: request.postData()
      });
    }
  });
  
  page.on('response', async response => {
    if (response.url().includes('/apply')) {
      console.log('Apply response:', response.status(), response.url());
      try {
        const text = await response.text();
        console.log('Apply response body:', text.substring(0, 500));
        fs.writeFileSync('/home/user/Agents/data/coolgames-apply-response.txt', text);
      } catch(e) {}
    }
  });
  
  page.on('pageerror', err => console.log('Page error:', err.message.substring(0, 100)));

  console.log('Navigating to apply page...');
  await page.goto('https://apply.workable.com/coolgames/j/3654334706/apply/', { 
    waitUntil: 'networkidle',
    timeout: 60000 
  });
  console.log('Page loaded, waiting for form...');
  await page.waitForTimeout(5000);
  
  // Screenshot
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/coolgames-01-apply-form.png', fullPage: true });
  console.log('Screenshot saved: coolgames-01-apply-form.png');
  
  // Get page content
  const content = await page.evaluate(() => document.body.innerText);
  console.log('Content length:', content.length);
  console.log('Content preview:', content.substring(0, 800));
  fs.writeFileSync('/home/user/Agents/data/coolgames-form-content.txt', content);
  
  // Save apply requests
  fs.writeFileSync('/home/user/Agents/data/coolgames-apply-requests.json', JSON.stringify(applyRequests, null, 2));

  await browser.close();
  console.log('Done!');
})().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
