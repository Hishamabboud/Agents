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
  const resumePath = '/home/user/Agents/profile/Hisham Abboud CV.pdf';

  const coverLetterText = `Dear DeployTeq Hiring Team,

I am writing to apply for the Software Developer position at DeployTeq in Zeist.

As a Software Engineer at Actemium (VINCI Energies), I build and maintain full-stack applications using .NET/C#, ASP.NET, Python/Flask, and JavaScript. DeployTeq's focus on online marketing technology is an exciting domain where I can apply my backend and frontend development skills.

My technical experience includes:
- Backend: C#, .NET Core, ASP.NET MVC, Python, Flask, SQL Server, REST APIs
- Frontend: JavaScript, TypeScript, HTML5, CSS3, React
- DevOps: Git, Azure DevOps, CI/CD, Docker
- Testing: Unit testing, Pytest, Locust performance testing

At ASML, I built performance testing infrastructure on Azure Kubernetes Service. At Delta Electronics, I migrated legacy C++ systems to C#/.NET. I hold a BSc in Software Engineering from Fontys University of Applied Sciences.

I am eager to contribute to DeployTeq's platform development and grow within your team.

Kind regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
Eindhoven, Netherlands`;

  // Click the YES radio button by finding the label via React fiber onChange
  const clickYesRadioViaReact = async () => {
    return await page.evaluate(() => {
      const yesRadio = document.querySelector('input[name="CA_21816"][value="true"]');
      if (!yesRadio) return 'radio not found';

      // Walk up React fiber tree to find onChange handler
      const fiberKey = Object.keys(yesRadio).find(k =>
        k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance')
      );
      if (!fiberKey) return 'no fiber key';

      let fiber = yesRadio[fiberKey];
      let onChangeFiber = null;

      // Walk fiber tree to find component with onChange
      const maxDepth = 20;
      let current = fiber;
      for (let i = 0; i < maxDepth && current; i++) {
        const props = current.memoizedProps;
        if (props && typeof props.onChange === 'function') {
          onChangeFiber = { onChange: props.onChange, level: i };
          break;
        }
        current = current.return;
      }

      if (onChangeFiber) {
        // Create a synthetic event for React
        const syntheticEvent = {
          type: 'change',
          target: yesRadio,
          currentTarget: yesRadio,
          nativeEvent: new Event('change', { bubbles: true }),
          bubbles: true,
          cancelable: true,
          defaultPrevented: false,
          preventDefault: () => {},
          stopPropagation: () => {},
          persist: () => {}
        };
        yesRadio.checked = true;
        onChangeFiber.onChange(syntheticEvent);
        return `Called React onChange at level ${onChangeFiber.level}. Checked: ${yesRadio.checked}`;
      }

      // Fallback: try triggering the label click via getBoundingClientRect
      const label = yesRadio.closest('label');
      if (label) {
        const rect = label.getBoundingClientRect();
        // Dispatch click at center of label
        const clickEvent = new MouseEvent('click', {
          bubbles: true,
          cancelable: true,
          view: window,
          clientX: rect.left + rect.width / 2,
          clientY: rect.top + rect.height / 2
        });
        label.dispatchEvent(clickEvent);
        return `Dispatched click on label at (${rect.left + rect.width/2}, ${rect.top + rect.height/2}). Checked: ${yesRadio.checked}`;
      }

      return 'could not click - no onChange and no label';
    });
  };

  // Dismiss modal via Escape
  const pressEscapeIfModal = async () => {
    const hasModal = await page.evaluate(() => !!document.querySelector('[data-role="modal-wrapper"]'));
    if (hasModal) {
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
    }
  };

  try {
    console.log('Navigating to application form...');
    await page.goto('https://apply.workable.com/deployteq/j/5246F389F7/apply/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v5-01-loaded.png'), fullPage: true });

    // Accept cookies
    if (await page.locator('[data-ui="cookie-consent"]').isVisible({ timeout: 3000 }).catch(() => false)) {
      const acceptBtn = page.locator('[data-ui="cookie-consent"] button:has-text("Accept all"), [data-ui="cookie-consent"] button').first();
      await acceptBtn.click({ force: true });
      await page.waitForTimeout(1500);
    }

    await page.waitForSelector('input[name="firstname"]', { timeout: 15000 });
    console.log('Form loaded');

    // Fill text fields using page.fill() (proper Playwright method)
    await page.fill('input[name="firstname"]', 'Hisham');
    await page.fill('input[name="lastname"]', 'Abboud');
    await page.fill('input[type="email"]', 'hiaham123@hotmail.com');
    await page.fill('input[name="CA_21813"]', '1 month');
    await page.fill('input[name="CA_21815"]', '65000');

    // Phone - focus via JS first to avoid modal
    await page.evaluate(() => document.querySelector('input[type="tel"]').focus());
    await page.fill('input[type="tel"]', '+31064841 2838');
    await pressEscapeIfModal();

    // Address - fill then escape any autocomplete
    await page.fill('input[name="address"]', 'Eindhoven, Netherlands');
    await page.waitForTimeout(300);
    await pressEscapeIfModal();

    // Textareas
    await page.fill('textarea[name="cover_letter"]', coverLetterText);
    await page.fill('textarea[name="QA_11807072"]', 'Yes, I currently reside in Eindhoven, Netherlands.');
    await page.fill('textarea[name="QA_11807073"]', 'Yes, I can commute to the office in Huis ter Heide, Utrecht. The journey from Eindhoven is approximately 60 minutes by public transport, which I am comfortable doing.');

    console.log('Text fields filled');

    // Upload resume
    const fileInputs = await page.locator('input[type="file"]').all();
    if (fileInputs.length >= 2) {
      await fileInputs[1].setInputFiles(resumePath);
      console.log('Resume uploaded');
    } else if (fileInputs.length === 1) {
      await fileInputs[0].setInputFiles(resumePath);
      console.log('Resume uploaded (first input)');
    }
    await page.waitForTimeout(3000);
    await pressEscapeIfModal();

    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v5-02-fields-filled.png'), fullPage: true });

    // Click YES for right to work using React fiber
    console.log('Setting YES radio...');
    const radioResult = await clickYesRadioViaReact();
    console.log('Radio result:', radioResult);
    await page.waitForTimeout(300);
    await pressEscapeIfModal();

    const yesChecked = await page.evaluate(() => document.querySelector('input[name="CA_21816"][value="true"]')?.checked);
    console.log('YES radio checked after React click:', yesChecked);

    // If React approach didn't work, try using mouse.click() at the screen position
    if (!yesChecked) {
      console.log('React approach failed, trying coordinate click...');
      // Scroll to the radio area and get position
      await page.evaluate(() => {
        const radio = document.querySelector('input[name="CA_21816"][value="true"]');
        radio?.scrollIntoView({ block: 'center' });
      });
      await page.waitForTimeout(500);

      const position = await page.evaluate(() => {
        const label = document.querySelector('input[name="CA_21816"][value="true"]')?.closest('label');
        if (!label) return null;
        const rect = label.getBoundingClientRect();
        return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
      });

      if (position) {
        console.log('Clicking at position:', position);
        await page.mouse.click(position.x, position.y);
        await page.waitForTimeout(300);
        const checkedAfterMouse = await page.evaluate(() => document.querySelector('input[name="CA_21816"][value="true"]')?.checked);
        console.log('YES checked after mouse.click:', checkedAfterMouse);
      }
    }

    // GDPR
    const gdprRoleCheckbox = page.locator('[data-ui="gdpr"] [role="checkbox"]').first();
    const gdprState = await gdprRoleCheckbox.getAttribute('aria-checked');
    if (gdprState !== 'true') {
      await gdprRoleCheckbox.click({ force: true });
      await page.waitForTimeout(300);
    }
    console.log('GDPR state:', await gdprRoleCheckbox.getAttribute('aria-checked'));
    await pressEscapeIfModal();

    // Final verification
    const verify = await page.evaluate(() => {
      const g = sel => document.querySelector(sel);
      return {
        firstname: g('input[name="firstname"]')?.value,
        lastname: g('input[name="lastname"]')?.value,
        email: g('input[type="email"]')?.value,
        phone: g('input[type="tel"]')?.value,
        address: g('input[name="address"]')?.value,
        noticePeriod: g('input[name="CA_21813"]')?.value,
        salary: g('input[name="CA_21815"]')?.value,
        yesRadio: g('input[name="CA_21816"][value="true"]')?.checked,
        qa1len: g('textarea[name="QA_11807072"]')?.value?.length,
        qa2len: g('textarea[name="QA_11807073"]')?.value?.length,
        coverLen: g('textarea[name="cover_letter"]')?.value?.length,
        gdprAriaChecked: g('[data-ui="gdpr"] [role="checkbox"]')?.getAttribute('aria-checked'),
        gdprNative: g('input[name="gdpr"]')?.checked,
        hasResume: document.body.innerText.includes('Hisham Abboud CV.pdf'),
        hasModal: !!g('[data-role="modal-wrapper"]')
      };
    });
    console.log('Verification:', JSON.stringify(verify, null, 2));

    // Pre-submit screenshots
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v5-03-pre-submit-top.png'), fullPage: false });
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v5-04-pre-submit-bottom.png'), fullPage: false });
    await page.evaluate(() => window.scrollTo(0, 0));

    // Submit
    console.log('Submitting...');
    const submitResult = await page.evaluate(() => {
      const btn = document.querySelector('button[type="submit"]');
      if (!btn) return 'no submit button';
      btn.click();
      return `"${btn.innerText.trim()}"`;
    });
    console.log('Submit:', submitResult);

    // Monitor for URL change or success content
    let confirmed = false;
    for (let i = 0; i < 15; i++) {
      await page.waitForTimeout(1000);
      const url = page.url();
      const text = await page.evaluate(() => document.body.innerText.substring(0, 500));
      if (!url.includes('/5246F389F7/apply/') ||
          text.toLowerCase().includes('thank') ||
          text.toLowerCase().includes('received') ||
          text.toLowerCase().includes('success')) {
        confirmed = true;
        console.log('Success! URL:', url);
        break;
      }
      // Check for errors
      const hasErrors = await page.evaluate(() => {
        const errEls = document.querySelectorAll('[class*="error"]:not([class*="error-boundary"])');
        return Array.from(errEls).map(e => e.innerText.trim()).filter(t => t).slice(0, 3);
      });
      if (hasErrors.length > 0) {
        console.log('Errors after submit:', hasErrors);
      }
    }

    // Final screenshot
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-software-developer-after-submit.png'), fullPage: true });
    console.log('Final screenshot saved');
    console.log('Final URL:', page.url());

    const finalText = await page.evaluate(() => document.body.innerText.substring(0, 2000));
    console.log('Final text:\n', finalText);

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(screenshotDir, 'deployteq-v5-error.png'), fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
})();
