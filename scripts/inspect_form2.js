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

  // Find Dutch and English option values
  const langValues = await page.$$eval('select[name="1019019"] option', opts => {
    const result = {};
    opts.forEach(o => {
      const text = o.text.trim();
      if (text === 'Dutch' || text === 'English' || text === 'Arabic') {
        result[text] = o.value;
      }
    });
    return result;
  });
  console.log('Language values:', JSON.stringify(langValues));

  // Try using Select2 programmatic API to select languages
  await page.evaluate((langVals) => {
    const sel = document.querySelector('select[name="1019019"]');
    if (!sel) { console.log('select not found'); return; }

    // Select the options by value
    const valuesToSelect = Object.values(langVals);
    for (const opt of sel.options) {
      if (valuesToSelect.includes(opt.value)) {
        opt.selected = true;
      }
    }

    // Trigger Select2 update using jQuery if available
    if (window.jQuery && window.jQuery(sel).data('select2')) {
      window.jQuery(sel).trigger('change');
    } else {
      // Dispatch change event
      sel.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }, langValues);

  await page.waitForTimeout(1000);

  // Verify selection
  const selected = await page.$$eval('select[name="1019019"] option:checked', opts =>
    opts.map(o => ({ value: o.value, text: o.text.trim() }))
  );
  console.log('Selected after programmatic set:', JSON.stringify(selected));

  // Check if Select2 visual shows the selection
  const select2Badges = await page.$$eval('.select2-selection__choice', els =>
    els.map(el => el.getAttribute('title') || el.textContent.trim())
  );
  console.log('Select2 visual badges:', JSON.stringify(select2Badges));

  // Try using the Select2 click UI approach
  // First, click the select2 container to open dropdown
  await page.click('.select2-container');
  await page.waitForTimeout(500);

  // Check if dropdown opened
  const dropdown = await page.$('.select2-dropdown');
  if (dropdown) {
    console.log('Select2 dropdown opened!');

    // Type to search
    const searchField = await page.$('.select2-search__field');
    if (searchField) {
      await searchField.fill('English');
      await page.waitForTimeout(500);

      // Check results
      const results = await page.$$eval('.select2-results__option', opts =>
        opts.map(o => o.textContent.trim())
      );
      console.log('Search results for "English":', JSON.stringify(results));
    }
  } else {
    console.log('Select2 dropdown did NOT open');
  }

  // Check flatpickr date field - try setting it via JS
  const dateSet = await page.evaluate(() => {
    const el = document.querySelector('input[name="899383"]');
    if (!el) return 'not found';

    // Try setting value via input event
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(el, '2025-03-01');
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));

    return el.value;
  });
  console.log('Date field value after JS set:', dateSet);

  // Try clicking on flatpickr to open calendar
  const dateField = await page.$('input[name="899383"]');
  if (dateField) {
    await dateField.click({ force: true });
    await page.waitForTimeout(1000);

    // Check if calendar opened
    const calendar = await page.$('.flatpickr-calendar');
    if (calendar) {
      console.log('Flatpickr calendar opened!');
      // Try clicking on a date (March 1, 2025)
      const todayBtn = await page.$('.flatpickr-day:not(.prevMonthDay):not(.nextMonthDay):first-child');
      if (todayBtn) {
        await todayBtn.click();
        console.log('Clicked a day in calendar');
      }
    } else {
      console.log('Calendar did not open');
    }
  }

  await page.screenshot({ path: '/home/user/Agents/output/screenshots/futures-works-inspect.png', fullPage: true });
  await browser.close();
  console.log('Done. Screenshot saved.');
})().catch(e => {
  console.error('Error:', e.message);
  process.exit(1);
});
