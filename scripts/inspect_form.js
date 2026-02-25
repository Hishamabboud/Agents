const { chromium } = require('/opt/node22/lib/node_modules/playwright');

const proxyUrl = new URL(process.env.HTTPS_PROXY || process.env.HTTP_PROXY);
const proxy = {
  server: `${proxyUrl.protocol}//${proxyUrl.hostname}:${proxyUrl.port}`,
  username: decodeURIComponent(proxyUrl.username),
  password: decodeURIComponent(proxyUrl.password)
};

(async () => {
  const browser = await chromium.launch({
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    proxy
  });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();

  await page.goto('https://www.careers-page.com/futures-works/job/LR994VY6/apply', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  await page.waitForTimeout(2000);

  // Get all form elements with their labels
  const formInfo = await page.evaluate(() => {
    const results = [];
    const selectors = 'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select';
    document.querySelectorAll(selectors).forEach(el => {
      let label = '';
      if (el.id) {
        const labelEl = document.querySelector(`label[for="${el.id}"]`);
        if (labelEl) label = labelEl.textContent.trim();
      }
      // Check if parent div has label
      if (!label) {
        const parent = el.closest('.form-group, .field-group, [class*="field"]');
        if (parent) {
          const labelEl = parent.querySelector('label');
          if (labelEl) label = labelEl.textContent.trim();
        }
      }
      results.push({
        tag: el.tagName,
        type: el.type || '',
        name: el.name || '',
        id: el.id || '',
        placeholder: el.placeholder || '',
        label: label.substring(0, 100),
        required: el.hasAttribute('required') || el.getAttribute('aria-required') === 'true',
        className: (el.className || '').substring(0, 80)
      });
    });
    return results;
  });

  console.log('Form Fields:');
  formInfo.forEach(f => console.log(JSON.stringify(f)));

  // Check for Select2 initialization
  const select2Info = await page.evaluate(() => {
    const selects = document.querySelectorAll('select.select2-hidden-accessible');
    return Array.from(selects).map(el => ({
      name: el.name,
      id: el.id,
      multiple: el.multiple,
      selectedOptions: Array.from(el.selectedOptions).map(o => ({ value: o.value, text: o.text }))
    }));
  });
  console.log('\nSelect2 elements:', JSON.stringify(select2Info, null, 2));

  // Check what languages are currently selected after load
  const langSelect = await page.$('select[name="1019019"]');
  if (langSelect) {
    const options = await page.$$eval('select[name="1019019"] option', opts =>
      opts.filter(o => o.selected).map(o => ({ value: o.value, text: o.text }))
    );
    console.log('\nCurrently selected language options:', JSON.stringify(options));

    // Get first few option values
    const allOpts = await page.$$eval('select[name="1019019"] option', opts =>
      opts.slice(0, 20).map(o => ({ value: o.value, text: o.text }))
    );
    console.log('\nFirst 20 language options (with values):', JSON.stringify(allOpts));
  }

  // Look at the form structure around the languages field
  const langContainer = await page.evaluate(() => {
    const sel = document.querySelector('select[name="1019019"]');
    if (!sel) return 'select not found';
    const parent = sel.closest('.form-group');
    return parent ? parent.innerHTML.substring(0, 500) : 'no parent form-group';
  });
  console.log('\nLanguage field container HTML:', langContainer);

  // Check the "When available" date field
  const dateFieldInfo = await page.evaluate(() => {
    const el = document.querySelector('input.flatpickr-input');
    if (!el) return 'not found';
    return {
      name: el.name,
      id: el.id,
      placeholder: el.placeholder,
      type: el.type,
      readOnly: el.readOnly,
      className: el.className
    };
  });
  console.log('\nDate field info:', JSON.stringify(dateFieldInfo));

  await browser.close();
})().catch(e => {
  console.error('Error:', e.message);
  process.exit(1);
});
