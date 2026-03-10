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
  
  console.log('Browser launched!');
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  page.on('requestfailed', req => console.log('Request failed:', req.url().substring(0, 80), req.failure().errorText));

  console.log('Testing with example.com...');
  try {
    await page.goto('https://example.com', { waitUntil: 'load', timeout: 20000 });
    const title = await page.title();
    console.log('example.com title:', title);
  } catch(e) {
    console.error('example.com error:', e.message.substring(0, 200));
  }

  await browser.close();
  console.log('Done!');
})().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
