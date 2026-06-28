const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  // Use older cached chromium  
  const execPath = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
  
  console.log('Launching browser with old Chromium...');
  const browser = await chromium.launch({ 
    headless: true,
    executablePath: execPath,
    args: [
      '--no-sandbox', 
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--no-first-run',
      '--no-zygote',
      '--single-process',
    ]
  });
  
  console.log('Browser launched!');
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });
  const page = await context.newPage();

  // Intercept requests to log API calls
  const apiRequests = [];
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      apiRequests.push({
        method: request.method(),
        url: request.url(),
        headers: request.headers(),
        postData: request.postData()
      });
    }
  });
  
  page.on('response', async response => {
    if (response.url().includes('/api/v1/jobs') && response.url().includes('/apply')) {
      console.log('APPLY RESPONSE:', response.status(), response.url());
      try {
        const text = await response.text();
        console.log('APPLY BODY:', text.substring(0, 500));
        fs.writeFileSync('/home/user/Agents/data/coolgames-apply-response.txt', text);
      } catch(e) {}
    }
  });

  console.log('Navigating to apply page...');
  try {
    await page.goto('https://apply.workable.com/coolgames/j/3654334706/apply/', { 
      waitUntil: 'networkidle',
      timeout: 60000 
    });
    console.log('Page loaded!');
    await page.waitForTimeout(3000);
    
    // Take screenshot
    await page.screenshot({ 
      path: '/home/user/Agents/output/screenshots/coolgames-01-apply-form.png', 
      fullPage: true 
    });
    console.log('Screenshot saved');
    
    // Get page content
    const content = await page.evaluate(() => document.body.innerText);
    console.log('Page content length:', content.length);
    console.log('Content preview:', content.substring(0, 500));
    
    fs.writeFileSync('/home/user/Agents/data/coolgames-form-content.txt', content);
    
    // Log API calls so far
    console.log('API calls made:', apiRequests.length);
    apiRequests.forEach(r => {
      console.log(`  ${r.method} ${r.url}`);
    });
    
  } catch(e) {
    console.error('Error:', e.message);
    await page.screenshot({ 
      path: '/home/user/Agents/output/screenshots/coolgames-error.png', 
      fullPage: true 
    });
  }

  await browser.close();
  console.log('Done!');
  
  // Save API requests log
  fs.writeFileSync('/home/user/Agents/data/coolgames-api-requests.json', JSON.stringify(apiRequests, null, 2));
})().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
