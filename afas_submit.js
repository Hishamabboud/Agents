const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const SCREENSHOT_DIR = '/home/user/Agents/output/screenshots';

const COVER_LETTER = `Hisham Abboud
Eindhoven, Netherlands
hiaham123@hotmail.com | +31 06 4841 2838
linkedin.com/in/hisham-abboud

Datum: 11 juni 2026
Aan: AFAS Software, Recruitment Team
Betreft: Software Engineer - Leusden

Beste wervingsteam,

Met veel interesse schrijf ik u naar aanleiding van de vacature Software Engineer bij AFAS Software. Als afgestudeerd Software Engineer met ruim twee en een half jaar werkervaring en een passie voor het ontwikkelen van kwalitatieve software, sluit mijn profiel goed aan bij wat jullie zoeken. Dat AFAS al meerdere keren is uitgeroepen tot beste werkgever van Europa spreekt boekdelen over de cultuur en het werkklimaat - iets dat voor mij zwaar meeweegt in mijn keuze.

In mijn huidige functie als Software Service Engineer bij Actemium ontwikkel en onderhoud ik full-stack applicaties met C#, .NET, ASP.NET, Python/Flask en JavaScript voor industriele klanten. Ik werk dagelijks met SQL-databases, REST API's en complexe systeemintegraties in productieomgevingen. Tijdens mijn stage bij ASML heb ik Python-testframeworks ontwikkeld in een agile team met Azure en Kubernetes, en bij Delta Electronics heb ik een legacy Visual Basic codebase gemigreerd naar C# en een interne webapplicatie gebouwd. Deze ervaringen hebben mij een brede technische basis gegeven en het vermogen om snel nieuwe frameworks en talen eigen te maken - wat goed past bij het werken met de eigen frameworks van AFAS.

Naast mijn werkervaring heb ik CogitatAI opgezet: een AI-gestuurd klantenserviceplatform dat ik zelfstandig heb ontworpen en ontwikkeld met Python/Flask. Dit project toont mijn ondernemende instelling en mijn drive om end-to-end verantwoordelijkheid te nemen voor softwareproducten. Ik ben vloeiend in het Nederlands, Engels en Arabisch, en ik heb mijn HBO-diploma Software Engineering behaald aan Fontys in Eindhoven.

Het vooruitzicht van een vierdaagse werkweek met een ontwikkeldag op vrijdag spreekt mij bijzonder aan als kans om continu te blijven leren en groeien. Ik zou graag in een persoonlijk gesprek toelichten hoe mijn ervaring en enthousiasme kunnen bijdragen aan het team van AFAS. Hartelijk dank voor uw tijd en overweging.

Met vriendelijke groet,
Hisham Abboud`;

function ts() {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
}

async function shot(page, name) {
  const file = path.join(SCREENSHOT_DIR, `afas-${name}-${ts()}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log('Screenshot:', file);
  return file;
}

// Helper to fill an AFAS web component input using Shadow DOM
async function fillAfasInput(page, elementId, value) {
  // AFAS custom elements use shadow DOM - we need to pierce it
  return await page.evaluate(({ id, val }) => {
    const el = document.getElementById(id);
    if (!el) return `Element ${id} not found`;

    // Try shadow DOM first
    const shadow = el.shadowRoot;
    if (shadow) {
      const input = shadow.querySelector('input, textarea');
      if (input) {
        input.focus();
        input.value = val;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        return `Filled via shadow DOM: ${id} = ${val}`;
      }
    }

    // Try setting value attribute and dispatching events
    if (el.value !== undefined) {
      el.value = val;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return `Filled via value property: ${id} = ${val}`;
    }

    // Try setAttribute
    el.setAttribute('value', val);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return `Set attribute: ${id} = ${val}`;
  }, { id: elementId, val: value });
}

// Helper to fill AFAS input by clicking and typing
async function typeInAfasInput(page, elementId, value) {
  // Click the element to focus it, then look for the inner input
  const el = await page.$(`#${elementId}`);
  if (!el) {
    console.log(`Element not found: ${elementId}`);
    return false;
  }

  try {
    await el.click();
    await page.waitForTimeout(300);
  } catch(e) {}

  // Try to find input inside shadow root using piercing selector
  try {
    // Use >> pierce operator
    const innerInput = await page.$(`#${elementId} >> input`);
    if (innerInput) {
      await innerInput.click({ clickCount: 3 });
      await innerInput.type(value, { delay: 30 });
      await innerInput.press('Tab');
      console.log(`Typed in shadow DOM input of ${elementId}`);
      return true;
    }
  } catch(e) {}

  // Try evaluating inside shadow root
  const result = await page.evaluate(({ id, val }) => {
    function findInput(root) {
      if (!root) return null;
      const el = root.getElementById ? root.getElementById(id) : root.querySelector('#' + id);
      if (!el) return null;
      const sr = el.shadowRoot;
      if (sr) {
        const inp = sr.querySelector('input, textarea');
        if (inp) return inp;
      }
      return null;
    }

    const inp = findInput(document);
    if (inp) {
      inp.focus();
      inp.value = '';
      inp.value = val;
      ['input', 'change', 'blur'].forEach(evt =>
        inp.dispatchEvent(new Event(evt, { bubbles: true }))
      );
      return 'success: ' + val;
    }
    return 'not found';
  }, { id: elementId, val: value });

  console.log(`Fill ${elementId}: ${result}`);
  return result.startsWith('success');
}

async function main() {
  const browser = await chromium.launch({ headless: true, slowMo: 50 });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });
  const page = await context.newPage();
  const screenshots = [];
  const results = {
    success: false,
    url: '',
    screenshots: [],
    notes: []
  };

  try {
    // === Step 1: Load job page ===
    console.log('\n=== Step 1: Load job page ===');
    await page.goto('https://www.werkenbijafas.nl/job/software-engineer', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });
    await page.waitForTimeout(2500);
    screenshots.push(await shot(page, '01-job-page'));

    // === Step 2: Accept cookies ===
    console.log('\n=== Step 2: Accept cookies ===');
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
    } catch(e) {
      console.log('Cookie banner not found or already accepted');
    }
    await page.waitForTimeout(1000);

    // === Step 3: Click Solliciteren ===
    console.log('\n=== Step 3: Click Solliciteren ===');
    const links = await page.$$('a');
    let solliciterenClicked = false;
    for (const link of links) {
      const txt = await link.textContent();
      if (txt && txt.trim() === 'Solliciteren') {
        await link.scrollIntoViewIfNeeded();
        await link.click();
        console.log('Clicked Solliciteren');
        solliciterenClicked = true;
        break;
      }
    }
    if (!solliciterenClicked) {
      throw new Error('Solliciteren button not found');
    }

    // Wait for form page to load
    await page.waitForURL('**/sollicitatie**', { timeout: 15000 });
    await page.waitForTimeout(4000);
    console.log('Form URL:', page.url());
    results.url = page.url();
    screenshots.push(await shot(page, '02-form-loaded'));

    // === Step 4: Fill personal details ===
    console.log('\n=== Step 4: Fill personal details ===');

    // Voorletters (H.)
    await typeInAfasInput(page, 'Window_0_Hr_Cra_T302_HrCra_In', 'H.');
    await page.waitForTimeout(300);

    // Roepnaam (first name)
    await typeInAfasInput(page, 'Window_0_Hr_Cra_T302_HrCra_CaNm', 'Hisham');
    await page.waitForTimeout(300);

    // Achternaam (last name)
    await typeInAfasInput(page, 'Window_0_Hr_Cra_T302_HrCra_LaNm', 'Abboud');
    await page.waitForTimeout(300);

    // Geslacht - try to set via component property
    await page.evaluate(() => {
      const el = document.getElementById('Window_0_Hr_Cra_T302_HrCra_ViGe');
      if (el) {
        el.value = 'M';
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    await page.waitForTimeout(300);

    // Geboortedatum - skip, not required (or try a date)
    // We'll leave optional fields empty

    // Phone
    await typeInAfasInput(page, 'Window_0_Hr_Cra_T305_HrCra_TeN2', '+31648412838');
    await page.waitForTimeout(300);

    // Email
    await typeInAfasInput(page, 'Window_0_Hr_Cra_T305_HrCra_EmA2', 'hiaham123@hotmail.com');
    await page.waitForTimeout(300);

    // Consent checkbox - click to enable
    await page.evaluate(() => {
      const el = document.getElementById('Window_0_Hr_Cra_T305_HrCra_OpEm');
      if (el) {
        const sr = el.shadowRoot;
        if (sr) {
          const cb = sr.querySelector('input[type="checkbox"]');
          if (cb && !cb.checked) cb.click();
        } else {
          el.setAttribute('value', 'true');
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    });
    await page.waitForTimeout(300);

    // Postcode + huisnummer (leave empty - address in Eindhoven)
    // Could fill with e.g. "5611 AB" + "1" but it's optional

    screenshots.push(await shot(page, '03-personal-details'));
    console.log('Personal details filled');

    // === Step 5: Fill motivation (cover letter) ===
    console.log('\n=== Step 5: Fill motivation ===');

    // The motivation field uses afas-markdown-editor
    // It likely has a contenteditable or textarea inside shadow DOM
    const motivResult = await page.evaluate((coverLetter) => {
      const el = document.getElementById('Window_0_Hr_Cra_T307_HrCra_Mo');
      if (!el) return 'Element not found';

      const sr = el.shadowRoot;
      if (sr) {
        // Look for contenteditable div or textarea
        const editable = sr.querySelector('[contenteditable="true"], textarea, .CodeMirror textarea, .cm-content');
        if (editable) {
          editable.focus();
          if (editable.tagName === 'TEXTAREA') {
            editable.value = coverLetter;
          } else {
            editable.textContent = coverLetter;
          }
          editable.dispatchEvent(new InputEvent('input', { bubbles: true, data: coverLetter }));
          editable.dispatchEvent(new Event('change', { bubbles: true }));
          return 'Filled via shadow DOM: ' + editable.tagName;
        }
        // Try to find nested shadow roots
        const allEls = sr.querySelectorAll('*');
        for (const child of allEls) {
          if (child.shadowRoot) {
            const deepInput = child.shadowRoot.querySelector('[contenteditable="true"], textarea');
            if (deepInput) {
              deepInput.focus();
              if (deepInput.tagName === 'TEXTAREA') {
                deepInput.value = coverLetter;
              } else {
                deepInput.textContent = coverLetter;
              }
              deepInput.dispatchEvent(new InputEvent('input', { bubbles: true }));
              deepInput.dispatchEvent(new Event('change', { bubbles: true }));
              return 'Filled via nested shadow DOM: ' + deepInput.tagName;
            }
          }
        }
        return 'Shadow DOM found but no editable element. Children: ' + Array.from(allEls).map(e => e.tagName).join(',').slice(0, 200);
      }

      // Try direct approach
      if (el.value !== undefined) {
        el.value = coverLetter;
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return 'Set value directly';
      }
      el.setAttribute('value', coverLetter);
      return 'Set attribute';
    }, COVER_LETTER);

    console.log('Motivation fill result:', motivResult);

    // Try clicking the motivation area and typing
    if (!motivResult.includes('Filled')) {
      console.log('Trying to click and type in motivation field...');
      const motivEl = await page.$('#Window_0_Hr_Cra_T307_HrCra_Mo');
      if (motivEl) {
        await motivEl.click();
        await page.waitForTimeout(500);

        // Try keyboard shortcut to select all and type
        await page.keyboard.press('Control+a');
        await page.keyboard.type(COVER_LETTER.slice(0, 100), { delay: 20 }); // type first 100 chars to test
        console.log('Typed some text in motivation field');
      }
    }

    await page.waitForTimeout(500);
    screenshots.push(await shot(page, '04-motivation-filled'));

    // === Step 6: Upload CV ===
    console.log('\n=== Step 6: Upload CV ===');

    // File upload through afas-file-input
    // The file input might be accessible through shadow DOM
    const fileInputResult = await page.evaluate(() => {
      // Look for any file input in the page (including shadow DOM)
      function findFileInputs(root) {
        const inputs = [];
        if (!root) return inputs;
        const direct = root.querySelectorAll('input[type="file"]');
        direct.forEach(i => inputs.push({ el: i, source: 'direct' }));

        const allEls = root.querySelectorAll('*');
        for (const el of allEls) {
          if (el.shadowRoot) {
            const shadowInputs = el.shadowRoot.querySelectorAll('input[type="file"]');
            shadowInputs.forEach(i => inputs.push({ el: i, id: el.id, source: 'shadow:' + el.tagName }));
          }
        }
        return inputs;
      }

      const found = findFileInputs(document);
      return found.map(f => ({
        id: f.el.id || '',
        name: f.el.name || '',
        source: f.source,
        parentId: f.id || ''
      }));
    });

    console.log('File inputs found:', JSON.stringify(fileInputResult));

    // Try using Playwright's file chooser
    let fileUploaded = false;
    const fileInputId = 'Window_0_Hr_Cra_T307_HrCra_MultiFile_search';

    // Method 1: Set files on any found file input via shadow DOM
    try {
      const fileChooserPromise = page.waitForFileChooser({ timeout: 5000 });
      const fileInputEl = await page.$(`#${fileInputId}`);
      if (fileInputEl) {
        await fileInputEl.click();
        const fileChooser = await fileChooserPromise;
        await fileChooser.setFiles(RESUME_PATH);
        console.log('File uploaded via file chooser');
        fileUploaded = true;
      }
    } catch(e) {
      console.log('File chooser method failed:', e.message);
    }

    // Method 2: Find file input in shadow DOM and set files directly
    if (!fileUploaded) {
      try {
        const shadowFileInput = await page.evaluateHandle(() => {
          const el = document.getElementById('Window_0_Hr_Cra_T307_HrCra_MultiFile_search');
          if (!el) return null;
          const sr = el.shadowRoot;
          if (!sr) return null;
          return sr.querySelector('input[type="file"]');
        });

        if (shadowFileInput) {
          const dataTransfer = await page.evaluateHandle(() => new DataTransfer());
          await page.evaluate(async ({ input, filePath }) => {
            // Can't easily set files from evaluate, need to use page.setInputFiles
          }, {});
        }
      } catch(e) {
        console.log('Shadow DOM file input method failed:', e.message);
      }
    }

    // Method 3: Use Playwright's setInputFiles on shadow DOM
    if (!fileUploaded) {
      try {
        await page.evaluate(() => {
          // Make file input visible and accessible
          const allInputs = [];
          document.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) {
              el.shadowRoot.querySelectorAll('input[type="file"]').forEach(inp => {
                inp.style.display = 'block';
                inp.style.visibility = 'visible';
                inp.style.opacity = '1';
                inp.id = 'afas-file-input-exposed';
                allInputs.push(inp);
              });
            }
          });
          return allInputs.length;
        });

        // Now try setInputFiles on the exposed input
        const exposedInput = await page.$('#afas-file-input-exposed');
        if (exposedInput) {
          await exposedInput.setInputFiles(RESUME_PATH);
          console.log('File uploaded via exposed shadow DOM input');
          fileUploaded = true;
        }
      } catch(e) {
        console.log('Exposed file input method failed:', e.message);
      }
    }

    if (!fileUploaded) {
      results.notes.push('CV upload may have failed - could not find accessible file input');
      console.log('WARNING: Could not upload file');
    }

    await page.waitForTimeout(1000);
    screenshots.push(await shot(page, '05-file-upload'));

    // === Step 7: Select Informatiebron (LinkedIn) ===
    console.log('\n=== Step 7: Select Informatiebron ===');
    const infoResult = await page.evaluate(() => {
      const el = document.getElementById('Window_0_Hr_Cra_T308_HrCra_ViSo');
      if (!el) return 'Element not found';
      el.setAttribute('value', 'LIN');  // LinkedIn
      el.dispatchEvent(new Event('change', { bubbles: true }));
      // Try setting the value property
      try { el.value = 'LIN'; } catch(e) {}
      return 'Set to LinkedIn (LIN)';
    });
    console.log('Informatiebron:', infoResult);
    await page.waitForTimeout(300);

    // Also try clicking the select
    try {
      const selectEl = await page.$('#Window_0_Hr_Cra_T308_HrCra_ViSo');
      if (selectEl) {
        await selectEl.click();
        await page.waitForTimeout(500);
        // Look for LinkedIn menu item
        const liMenu = await page.$('afas-menu-item[value="LIN"]');
        if (liMenu) {
          await liMenu.click();
          console.log('Clicked LinkedIn menu item');
        }
      }
    } catch(e) {
      console.log('Select click method:', e.message);
    }
    await page.waitForTimeout(300);

    // === Step 8: Final screenshot before submit ===
    console.log('\n=== Step 8: Pre-submit screenshot ===');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    screenshots.push(await shot(page, '06-pre-submit-top'));

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    screenshots.push(await shot(page, '07-pre-submit-bottom'));

    // === Step 9: Submit form ===
    console.log('\n=== Step 9: Submit form ===');

    // Click the Solliciteren submit button
    const submitBtn = await page.$('#Window_0_Actions_AntaUpdateCloseWebForm');
    if (submitBtn) {
      console.log('Found submit button, clicking...');
      await submitBtn.click();
      await page.waitForTimeout(5000);
      console.log('Post-submit URL:', page.url());

      screenshots.push(await shot(page, '08-after-submit'));

      // Check for success/error messages
      const pageText = await page.evaluate(() => document.body.innerText);
      const successIndicators = ['bedankt', 'ontvangen', 'ingediend', 'thank', 'success', 'bevestig'];
      const errorIndicators = ['fout', 'error', 'verplicht', 'required', 'validat'];

      const hasSuccess = successIndicators.some(s => pageText.toLowerCase().includes(s));
      const hasError = errorIndicators.some(s => pageText.toLowerCase().includes(s));

      console.log('Success indicators found:', hasSuccess);
      console.log('Error indicators found:', hasError);
      console.log('Page text snippet:', pageText.slice(0, 500));

      if (hasSuccess && !hasError) {
        results.success = true;
        results.notes.push('Application submitted successfully');
      } else if (hasError) {
        results.notes.push('Form validation errors detected: ' + pageText.slice(0, 200));
      } else {
        results.notes.push('Submission status unclear. URL: ' + page.url());
      }
    } else {
      console.log('Submit button not found!');
      results.notes.push('Submit button (Window_0_Actions_AntaUpdateCloseWebForm) not found');
    }

  } catch(e) {
    console.error('ERROR:', e.message, e.stack);
    results.notes.push('Script error: ' + e.message);
    try {
      screenshots.push(await shot(page, '99-error'));
    } catch(e2) {}
  } finally {
    await browser.close();
  }

  results.screenshots = screenshots;

  console.log('\n=== RESULTS ===');
  console.log(JSON.stringify(results, null, 2));

  // Save results
  fs.writeFileSync('/home/user/Agents/data/afas-apply-result.json', JSON.stringify(results, null, 2));
  console.log('Results saved to data/afas-apply-result.json');

  return results;
}

main().catch(e => console.error('FATAL:', e.message));
