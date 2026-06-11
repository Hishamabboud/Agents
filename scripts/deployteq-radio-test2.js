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
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);

    if (await page.locator('[data-ui="cookie-consent"]').isVisible({ timeout: 2000 }).catch(() => false)) {
      await page.locator('button:has-text("Accept all")').first().click({ force: true }).catch(() =>
        page.locator('[data-ui="cookie-consent"] button').first().click({ force: true })
      );
      await page.waitForTimeout(1000);
    }

    await page.waitForSelector('input[name="CA_21816"]', { timeout: 10000 });

    // Inspect React fiber on the radio input to find onClick handler
    const reactFiberInfo = await page.evaluate(() => {
      const yesRadio = document.querySelector('input[name="CA_21816"][value="true"]');
      if (!yesRadio) return { error: 'not found' };

      const label = yesRadio.closest('label');

      // Find React fiber
      const fiberKey = Object.keys(label || yesRadio).find(k =>
        k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance')
      );

      if (!fiberKey) return { error: 'no React fiber found' };

      const fiber = (label || yesRadio)[fiberKey];

      // Traverse fiber to find onClick
      const findHandlers = (fiber, depth = 0) => {
        if (!fiber || depth > 10) return null;
        const props = fiber.memoizedProps || fiber.pendingProps;
        if (props) {
          const handlers = Object.keys(props).filter(k => k.startsWith('on'));
          if (handlers.length > 0) return { depth, handlers, element: fiber.type };
        }
        return findHandlers(fiber.child, depth + 1) || findHandlers(fiber.return, depth + 1);
      };

      const info = findHandlers(fiber);
      return { fiberKey, info };
    });
    console.log('React fiber info:', JSON.stringify(reactFiberInfo, null, 2));

    // Try using Playwright's dispatchEvent on the label directly
    const yesLabel = page.locator('label').filter({ hasText: /^YES$/ }).first();
    console.log('YES label visible:', await yesLabel.isVisible());

    // Get the bounding box to click at the center of the visible element
    const bbox = await yesLabel.boundingBox();
    console.log('YES label bounding box:', bbox);

    if (bbox) {
      // Use mouse.click directly on the coordinates
      await page.mouse.click(bbox.x + bbox.width / 2, bbox.y + bbox.height / 2);
      await page.waitForTimeout(500);
      const checked1 = await page.evaluate(() => document.querySelector('input[name="CA_21816"][value="true"]')?.checked);
      console.log('After mouse.click on bbox center - checked:', checked1);
    }

    // Check if click worked
    let state = await page.evaluate(() => ({
      yes: document.querySelector('input[name="CA_21816"][value="true"]')?.checked,
      no: document.querySelector('input[name="CA_21816"][value="false"]')?.checked
    }));
    console.log('State after click:', state);

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-radio2-test.png'), fullPage: false });

    // If still not working, try triggering the React onChange on the label
    const reactClickResult = await page.evaluate(() => {
      const yesRadio = document.querySelector('input[name="CA_21816"][value="true"]');
      const label = yesRadio?.closest('label');
      if (!label) return 'no label';

      // Find the React fiber and call onChange
      const findFiberWithOnChange = (el) => {
        const key = Object.keys(el).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
        if (!key) return null;
        let fiber = el[key];
        while (fiber) {
          const props = fiber.memoizedProps;
          if (props && props.onChange) {
            return { onChange: props.onChange, props };
          }
          fiber = fiber.return;
        }
        return null;
      };

      // Try on the radio input itself
      const fiberResult = findFiberWithOnChange(yesRadio);
      if (fiberResult) {
        fiberResult.onChange({ target: yesRadio, currentTarget: yesRadio });
        return `Called onChange on radio. Checked: ${yesRadio.checked}`;
      }

      // Try on the label
      const labelFiber = findFiberWithOnChange(label);
      if (labelFiber) {
        return `Found onChange on label: ${Object.keys(labelFiber.props).join(', ')}`;
      }

      return 'No onChange handler found on radio or label';
    });
    console.log('React onChange result:', reactClickResult);

    state = await page.evaluate(() => ({
      yes: document.querySelector('input[name="CA_21816"][value="true"]')?.checked,
      no: document.querySelector('input[name="CA_21816"][value="false"]')?.checked
    }));
    console.log('State after onChange:', state);

  } catch(e) {
    console.error(e.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-radio2-error.png'), fullPage: true });
  } finally {
    await browser.close();
  }
})();
