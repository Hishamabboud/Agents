const { chromium } = require('playwright');
const fs = require('fs');

const FORM_URL = 'https://www.werkenbijafas.nl/aanmaken-sollicitatie-incl-autorisatie-prs/sollicitatie-development-nl?VcSn=296';

async function main() {
  const browser = await chromium.launch({ headless: true, slowMo: 100 });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });
  const page = await context.newPage();

  // First go to job page, accept cookies, then click solliciteren
  console.log('Loading job page...');
  await page.goto('https://www.werkenbijafas.nl/job/software-engineer', {
    waitUntil: 'domcontentloaded',
    timeout: 60000
  });
  await page.waitForTimeout(2000);

  // Accept cookies
  try {
    const allBtns = await page.$$('button.CybotCookiebotDialogBodyButton');
    for (const btn of allBtns) {
      const txt = await btn.textContent();
      if (txt && txt.includes('Alles toestaan')) {
        await btn.click();
        console.log('Cookies accepted');
        break;
      }
    }
  } catch(e) {}
  await page.waitForTimeout(1000);

  // Click Solliciteren
  const links = await page.$$('a');
  for (const link of links) {
    const txt = await link.textContent();
    if (txt && txt.trim() === 'Solliciteren') {
      await link.click();
      console.log('Clicked Solliciteren');
      break;
    }
  }

  // Wait for navigation to form page
  await page.waitForURL('**/sollicitatie**', { timeout: 15000 });
  await page.waitForTimeout(4000);

  console.log('Current URL:', page.url());

  // Save the form HTML
  const html = await page.content();
  fs.writeFileSync('/home/user/Agents/data/afas-form-page.html', html);
  console.log('Saved form HTML, length:', html.length);

  // Take screenshot
  await page.screenshot({ path: '/home/user/Agents/output/screenshots/afas-form-01.png', fullPage: true });
  console.log('Screenshot: afas-form-01.png');

  // Find all form inputs
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input, textarea, select')).map(el => {
      const labelEl = document.querySelector(`label[for="${el.id}"]`);
      const parentLabel = el.closest('label');
      const nearbyLabel = el.parentElement ? el.parentElement.querySelector('label') : null;
      return {
        tag: el.tagName,
        type: el.type || '',
        name: el.name || '',
        id: el.id || '',
        placeholder: el.placeholder || '',
        value: el.value || '',
        label: (labelEl || parentLabel || nearbyLabel || {}).textContent ?
               ((labelEl || parentLabel || nearbyLabel).textContent || '').trim().slice(0, 80) : '',
        visible: el.offsetParent !== null,
        required: el.required,
        'aria-label': el.getAttribute('aria-label') || ''
      };
    });
  });

  console.log('\nAll form inputs (' + inputs.length + '):');
  inputs.forEach(i => console.log('  ' + JSON.stringify(i)));

  // Find AFAS-specific elements
  const afasEls = await page.evaluate(() => {
    const customEls = document.querySelectorAll('[data-field-id], [data-field-name], afas-field, afas-input, [id*="Field"], [id*="field"]');
    return Array.from(customEls).slice(0, 50).map(el => ({
      tag: el.tagName,
      id: el.id,
      class: el.className.slice(0, 50),
      dataField: el.getAttribute('data-field-id') || el.getAttribute('data-field-name') || '',
      html: el.outerHTML.slice(0, 200)
    }));
  });
  console.log('\nAFAS field elements (' + afasEls.length + '):');
  afasEls.forEach(e => console.log('  ' + JSON.stringify(e)));

  // Get visible text on page to understand form structure
  const pageText = await page.evaluate(() => document.body.innerText);
  console.log('\nPage text (first 3000 chars):');
  console.log(pageText.slice(0, 3000));

  // Look for any specific field labels / sections
  const sections = await page.evaluate(() => {
    const headers = document.querySelectorAll('h1, h2, h3, h4, .label, label, .field-label, [class*="label"], [class*="Label"]');
    return Array.from(headers).slice(0, 50).map(el => ({
      tag: el.tagName,
      class: el.className.slice(0, 50),
      text: (el.textContent || '').trim().slice(0, 100),
      visible: el.offsetParent !== null
    }));
  });
  console.log('\nHeadings and labels:');
  sections.forEach(s => { if(s.visible && s.text) console.log('  [' + s.tag + '.' + s.class + '] ' + s.text); });

  await browser.close();
}

main().catch(e => console.error('FATAL:', e.message, e.stack));
