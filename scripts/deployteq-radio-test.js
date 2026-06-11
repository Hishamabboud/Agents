const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });
  const page = await context.newPage();

  try {
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);

    // Dismiss cookie
    if (await page.locator('[data-ui="cookie-consent"]').isVisible({ timeout: 2000 }).catch(() => false)) {
      await page.locator('button:has-text("Accept all")').first().click({ force: true }).catch(() =>
        page.locator('[data-ui="cookie-consent"] button').first().click({ force: true })
      );
      await page.waitForTimeout(1000);
    }

    await page.waitForSelector('input[name="CA_21816"]', { timeout: 10000 });

    // Inspect the radio button structure deeply
    const radioInfo = await page.evaluate(() => {
      const radios = document.querySelectorAll('input[name="CA_21816"]');
      return Array.from(radios).map(r => {
        const label = r.closest('label');
        const div = label ? label.querySelector('div') : null;
        return {
          value: r.value,
          checked: r.checked,
          ariaHidden: r.getAttribute('aria-hidden'),
          tabindex: r.getAttribute('tabindex'),
          labelText: label ? label.innerText.trim() : 'no label',
          labelOuterHTML: label ? label.outerHTML.substring(0, 400) : 'no label',
          divClassname: div ? div.className : 'no div'
        };
      });
    });
    console.log('Radio info:', JSON.stringify(radioInfo, null, 2));

    // Try clicking just the visible div inside the label
    const yesResult = await page.evaluate(() => {
      const yesRadio = document.querySelector('input[name="CA_21816"][value="true"]');
      if (!yesRadio) return 'No YES radio found';

      const label = yesRadio.closest('label');
      if (!label) return 'No label found';

      // Get the visible div inside the label (the visual checkbox/radio)
      const visibleDiv = label.querySelector('div > div');
      if (visibleDiv) {
        visibleDiv.click();
        return `Clicked inner div. Radio checked: ${yesRadio.checked}, div class: ${visibleDiv.className.substring(0, 50)}`;
      }

      const outerDiv = label.querySelector('div');
      if (outerDiv) {
        outerDiv.click();
        return `Clicked outer div. Radio checked: ${yesRadio.checked}`;
      }

      label.click();
      return `Clicked label. Radio checked: ${yesRadio.checked}`;
    });
    console.log('YES click attempt 1:', yesResult);

    // Check state
    let state = await page.evaluate(() => ({
      yesChecked: document.querySelector('input[name="CA_21816"][value="true"]')?.checked,
      noChecked: document.querySelector('input[name="CA_21816"][value="false"]')?.checked
    }));
    console.log('State after click 1:', state);

    // Try using React's synthetic event system
    const reactResult = await page.evaluate(() => {
      const yesRadio = document.querySelector('input[name="CA_21816"][value="true"]');
      if (!yesRadio) return 'not found';

      // Try to get React fiber
      const key = Object.keys(yesRadio).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
      if (key) {
        return `Found React key: ${key}`;
      }

      // Try simulating a proper pointer event sequence on the label
      const label = yesRadio.closest('label');
      if (label) {
        // Simulate full click sequence
        label.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
        label.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        label.dispatchEvent(new PointerEvent('pointerup', { bubbles: true }));
        label.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
        label.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        return `Dispatched events. Radio checked: ${yesRadio.checked}`;
      }
      return 'no label';
    });
    console.log('React event dispatch:', reactResult);
    state = await page.evaluate(() => ({
      yesChecked: document.querySelector('input[name="CA_21816"][value="true"]')?.checked,
      noChecked: document.querySelector('input[name="CA_21816"][value="false"]')?.checked
    }));
    console.log('State after React events:', state);

    // Take screenshot to see visual state
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-radio-test.png'), fullPage: true });

    // Try submitting the form and see what validation errors appear
    await page.fill('input[name="firstname"]', 'TEST');
    await page.fill('input[name="lastname"]', 'USER');
    await page.fill('input[type="email"]', 'test@test.com');
    await page.fill('input[name="CA_21813"]', '1 month');
    await page.fill('input[name="CA_21815"]', '50000');
    await page.fill('textarea[name="QA_11807072"]', 'Yes');
    await page.fill('textarea[name="QA_11807073"]', 'Yes');

    // Check GDPR
    const gdprCheckbox = page.locator('[data-ui="gdpr"] [role="checkbox"]').first();
    if (await gdprCheckbox.getAttribute('aria-checked') === 'false') {
      await gdprCheckbox.click({ force: true });
    }

    // Try to submit and capture validation state
    await page.evaluate(() => document.querySelector('button[type="submit"]')?.click());
    await page.waitForTimeout(2000);

    const validationInfo = await page.evaluate(() => {
      const errors = [];
      // Look for error messages
      document.querySelectorAll('[class*="error"], [class*="invalid"], [aria-invalid="true"]').forEach(el => {
        errors.push({ class: el.className.substring(0, 50), text: el.innerText.trim().substring(0, 100) });
      });
      // Check required field states
      const radioContainer = document.querySelector('input[name="CA_21816"]')?.closest('[class*="field"], [class*="radio"]');
      return {
        errors,
        radioContainerClass: radioContainer?.className.substring(0, 100),
        yesChecked: document.querySelector('input[name="CA_21816"][value="true"]')?.checked,
        pageUrl: window.location.href
      };
    });
    console.log('After submit attempt:', JSON.stringify(validationInfo, null, 2));

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-radio-after-submit.png'), fullPage: true });

    const screenshotDir = '/home/user/Agents/output/screenshots';
  } catch(e) {
    console.error(e.message);
  } finally {
    await browser.close();
  }
})();
