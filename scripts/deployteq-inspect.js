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

    // Dismiss cookie consent
    const cookieDialog = page.locator('[data-ui="cookie-consent"]');
    if (await cookieDialog.isVisible({ timeout: 2000 }).catch(() => false)) {
      await page.locator('[data-ui="cookie-consent"] button').first().click({ force: true });
      await page.waitForTimeout(1000);
    }

    await page.waitForSelector('input[name="firstname"]', { timeout: 10000 });

    // Get the HTML around the right to work radio buttons
    const radioHtml = await page.evaluate(() => {
      const radios = document.querySelectorAll('input[name="CA_21816"]');
      return Array.from(radios).map(r => {
        // Walk up to find the parent container
        let parent = r.parentElement;
        for (let i = 0; i < 5; i++) {
          if (parent) parent = parent.parentElement;
        }
        return {
          radioId: r.id,
          radioValue: r.value,
          ariaHidden: r.getAttribute('aria-hidden'),
          parentHtml: parent ? parent.innerHTML.substring(0, 500) : 'no parent'
        };
      });
    });
    console.log('Radio button structure:', JSON.stringify(radioHtml, null, 2));

    // Also check labels
    const labels = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('label')).map(l => ({
        for: l.getAttribute('for'),
        text: l.innerText.trim().substring(0, 100),
        html: l.outerHTML.substring(0, 200)
      })).filter(l => l.text.length > 0);
    });
    console.log('All labels:', JSON.stringify(labels, null, 2));

    // Check the CA_21816 section more broadly
    const caSection = await page.evaluate(() => {
      // Find element with name CA_21816
      const el = document.querySelector('[name="CA_21816"]');
      if (!el) return 'not found';
      // Go up 8 levels
      let p = el;
      for (let i = 0; i < 8; i++) { p = p.parentElement; if (!p) break; }
      return p ? p.innerHTML.substring(0, 1500) : 'no parent found';
    });
    console.log('CA_21816 section HTML:', caSection);

    // Also inspect the QA fields
    const qaSection = await page.evaluate(() => {
      const qa1 = document.querySelector('[name="QA_11807072"]');
      const qa2 = document.querySelector('[name="QA_11807073"]');
      let p1 = qa1, p2 = qa2;
      for (let i = 0; i < 5; i++) {
        if (p1) p1 = p1.parentElement;
        if (p2) p2 = p2.parentElement;
      }
      return {
        qa1Label: p1 ? p1.innerText.substring(0, 200) : 'not found',
        qa2Label: p2 ? p2.innerText.substring(0, 200) : 'not found'
      };
    });
    console.log('QA fields context:', JSON.stringify(qaSection, null, 2));

    // Check for the Pronouns dropdown
    const ca21817 = await page.evaluate(() => {
      const el = document.querySelector('[name="CA_21817"]');
      if (!el) return 'not found';
      let p = el;
      for (let i = 0; i < 5; i++) { p = p.parentElement; if (!p) break; }
      return p ? p.innerText.substring(0, 300) : 'no parent';
    });
    console.log('CA_21817 (Pronouns?) context:', ca21817);

  } finally {
    await browser.close();
  }
})();
