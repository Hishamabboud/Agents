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
  const screenshotDir = '/home/user/Agents/output/screenshots';

  try {
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded', timeout: 30000
    });
    await page.waitForTimeout(3000);

    if (await page.locator('[data-ui="cookie-consent"]').isVisible({ timeout: 2000 }).catch(() => false)) {
      await page.locator('[data-ui="cookie-consent"] button').first().click({ force: true });
      await page.waitForTimeout(1500);
    }

    await page.waitForSelector('input[name="gdpr"]', { timeout: 10000 });

    // Inspect GDPR element structure deeply
    const gdprInfo = await page.evaluate(() => {
      const gdprLabel = document.querySelector('[data-ui="gdpr"]');
      const roleChk = document.querySelector('[data-ui="gdpr"] [role="checkbox"]');
      const nativeChk = document.querySelector('input[name="gdpr"]');

      const info = {
        gdprLabelHTML: gdprLabel?.outerHTML.substring(0, 600),
        roleCheckboxAriaChecked: roleChk?.getAttribute('aria-checked'),
        roleCheckboxClass: roleChk?.className,
        nativeChecked: nativeChk?.checked,
        nativeType: nativeChk?.type
      };

      // Find React fiber on each element
      const findFiber = (el, label) => {
        if (!el) return `${label}: element not found`;
        const key = Object.keys(el).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
        if (!key) return `${label}: no fiber`;
        let fiber = el[key];
        const handlers = [];
        while (fiber && handlers.length < 10) {
          const props = fiber.memoizedProps;
          if (props) {
            const evts = Object.keys(props).filter(k => k.startsWith('on'));
            if (evts.length) handlers.push({ level: fiber.type?.name || fiber.type || 'unknown', events: evts });
          }
          fiber = fiber.return;
        }
        return { label, handlers };
      };

      return {
        ...info,
        gdprLabelFiber: findFiber(gdprLabel, 'gdprLabel'),
        roleChkFiber: findFiber(roleChk, 'roleCheckbox'),
        nativeChkFiber: findFiber(nativeChk, 'nativeCheckbox')
      };
    });
    console.log('GDPR info:', JSON.stringify(gdprInfo, null, 2));

    // Try different click approaches
    const attempts = await page.evaluate(() => {
      const results = [];
      const gdprLabel = document.querySelector('[data-ui="gdpr"]');
      const roleChk = document.querySelector('[data-ui="gdpr"] [role="checkbox"]');
      const nativeChk = document.querySelector('input[name="gdpr"]');

      // Approach 1: Click the role=checkbox div directly
      if (roleChk) {
        const rect = roleChk.getBoundingClientRect();
        roleChk.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: rect.x + 5, clientY: rect.y + 5 }));
        roleChk.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: rect.x + 5, clientY: rect.y + 5 }));
        roleChk.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: rect.x + 5, clientY: rect.y + 5 }));
        results.push(`After role=checkbox click: aria-checked=${roleChk.getAttribute('aria-checked')}`);
      }

      // Approach 2: Use keyboard space on the role=checkbox
      if (roleChk) {
        roleChk.focus();
        roleChk.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', code: 'Space', bubbles: true }));
        roleChk.dispatchEvent(new KeyboardEvent('keyup', { key: ' ', code: 'Space', bubbles: true }));
        results.push(`After Space key: aria-checked=${roleChk.getAttribute('aria-checked')}`);
      }

      return results;
    });
    console.log('Attempt results:', attempts);

    // Take screenshot
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-gdpr-test.png'), fullPage: false });

    // Now try actual Playwright click on the element
    const gdprRoleEl = page.locator('[data-ui="gdpr"] [role="checkbox"]').first();
    console.log('GDPR role=checkbox visible:', await gdprRoleEl.isVisible());
    const bbox = await gdprRoleEl.boundingBox();
    console.log('GDPR role=checkbox boundingBox:', bbox);

    if (bbox) {
      // Scroll into view
      await gdprRoleEl.scrollIntoViewIfNeeded();
      await page.waitForTimeout(300);
      // Click at the center using mouse
      await page.mouse.click(bbox.x + bbox.width / 2, bbox.y + bbox.height / 2);
      await page.waitForTimeout(500);
      const stateAfterMouse = await page.evaluate(() => ({
        ariaChecked: document.querySelector('[data-ui="gdpr"] [role="checkbox"]')?.getAttribute('aria-checked'),
        nativeChecked: document.querySelector('input[name="gdpr"]')?.checked
      }));
      console.log('After mouse.click on GDPR:', stateAfterMouse);
    }

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-gdpr-after-click.png'), fullPage: false });

  } catch(e) {
    console.error(e.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-gdpr-error.png'), fullPage: true });
  } finally {
    await browser.close();
  }
})();
