const { chromium } = require('playwright');
const fs = require('fs');

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });
  const page = await context.newPage();

  console.log('Loading AFAS job page...');
  await page.goto('https://www.werkenbijafas.nl/job/software-engineer', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);

  const title = await page.title();
  const url = page.url();
  console.log('Title:', title);
  console.log('URL:', url);

  // Save HTML
  const html = await page.content();
  fs.writeFileSync('/home/user/Agents/data/afas-job-page.html', html);
  console.log('HTML saved, length:', html.length);

  // Get all links
  const links = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('a')).map(el => ({
      text: el.textContent ? el.textContent.trim().slice(0, 80) : '',
      href: el.href || '',
      classes: el.className || ''
    }));
  });
  console.log('\nAll links:');
  links.forEach(l => {
    if (l.text) console.log('  "' + l.text + '" => ' + l.href);
  });

  // Get buttons
  const buttons = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button')).map(el => ({
      text: el.textContent ? el.textContent.trim().slice(0, 80) : '',
      type: el.type,
      classes: el.className
    }));
  });
  console.log('\nAll buttons:');
  buttons.forEach(b => console.log('  [' + b.type + '] "' + b.text + '" class=' + b.classes));

  // Get form inputs
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
      tag: el.tagName,
      type: el.type || '',
      name: el.name || '',
      id: el.id || '',
      placeholder: el.placeholder || ''
    }));
  });
  console.log('\nForm inputs:', inputs.length);
  inputs.forEach(i => console.log('  ' + JSON.stringify(i)));

  // Body text snippet
  const bodyText = await page.evaluate(() => document.body.innerText);
  const sollicitLines = bodyText.split('\n').filter(l => l.toLowerCase().includes('sollicit'));
  console.log('\nLines containing "sollicit":', sollicitLines);

  await page.screenshot({ path: '/home/user/Agents/output/screenshots/afas-explore-01.png', fullPage: true });
  console.log('\nScreenshot saved');

  await browser.close();
}

main().catch(e => console.error('ERROR:', e.message, e.stack));
