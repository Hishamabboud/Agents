const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const SCREENSHOT_DIR = '/home/user/Agents/output/screenshots';

const COVER_LETTER = `Hisham Abboud
Eindhoven, Netherlands
hiaham123@hotmail.com | +31 06 4841 2838
linkedin.com/in/hisham-abboud

---

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

async function main() {
  const browser = await chromium.launch({ headless: true, slowMo: 100 });
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });
  const page = await context.newPage();

  const screenshots = [];

  try {
    console.log('=== Step 1: Load job page ===');
    await page.goto('https://www.werkenbijafas.nl/job/software-engineer', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });
    await page.waitForTimeout(3000);
    screenshots.push(await shot(page, '01-loaded'));

    console.log('=== Step 2: Accept cookies ===');
    // Accept all cookies to dismiss the banner
    try {
      const acceptBtn = await page.$('#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll, button.CybotCookiebotDialogBodyButton');
      if (acceptBtn) {
        // Find the "Alles toestaan" button specifically
        const allBtns = await page.$$('button.CybotCookiebotDialogBodyButton');
        for (const btn of allBtns) {
          const txt = await btn.textContent();
          if (txt && txt.trim().includes('Alles toestaan')) {
            await btn.click();
            console.log('Clicked "Alles toestaan"');
            break;
          }
        }
      }
    } catch(e) {
      console.log('Cookie banner dismissal:', e.message);
    }
    await page.waitForTimeout(1500);
    screenshots.push(await shot(page, '02-cookies-dismissed'));

    console.log('=== Step 3: Click Solliciteren button ===');
    // Find and click the Solliciteren link
    const sollLinks = await page.$$('a');
    let clicked = false;
    for (const link of sollLinks) {
      const txt = await link.textContent();
      if (txt && txt.trim() === 'Solliciteren') {
        await link.scrollIntoViewIfNeeded();
        await link.click();
        console.log('Clicked Solliciteren link');
        clicked = true;
        break;
      }
    }
    if (!clicked) {
      console.log('Solliciteren link not found, trying other approach...');
      // Try scrolling to the bottom where the form might be
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    }
    await page.waitForTimeout(3000);
    screenshots.push(await shot(page, '03-after-solliciteer-click'));

    // Check what happened after click
    const currentUrl = page.url();
    console.log('URL after click:', currentUrl);

    // Look for any iframes (Typeform is mentioned in cookies)
    const iframes = await page.$$('iframe');
    console.log('Iframes found:', iframes.length);
    for (let i = 0; i < iframes.length; i++) {
      const src = await iframes[i].getAttribute('src');
      console.log(`  iframe[${i}] src:`, src);
    }

    // Look for any visible form inputs now
    const inputs = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"]), textarea, select')).map(el => ({
        tag: el.tagName,
        type: el.type || '',
        name: el.name || '',
        id: el.id || '',
        placeholder: el.placeholder || '',
        visible: el.offsetParent !== null
      }));
    });
    console.log('Visible inputs after click:', inputs.filter(i => i.visible).length);
    inputs.forEach(i => { if(i.visible) console.log('  ' + JSON.stringify(i)); });

    // Check for any modal/overlay
    const modals = await page.evaluate(() => {
      const els = document.querySelectorAll('[class*="modal"], [class*="overlay"], [class*="dialog"], [role="dialog"], [role="modal"]');
      return Array.from(els).map(el => ({
        class: el.className,
        visible: el.offsetParent !== null,
        html: el.innerHTML.slice(0, 200)
      }));
    });
    console.log('Modals/overlays:', modals.length);
    modals.forEach(m => { if(m.visible) console.log('  VISIBLE:', m.class, m.html); });

    // Check if page navigated or if there's a hash change
    const bodyHTML = await page.evaluate(() => document.body.innerHTML.slice(0, 2000));
    console.log('\nBody HTML snippet after click:');
    console.log(bodyHTML.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 500));

    // Try checking for Typeform embed specifically (it was in the cookie list)
    const typeformEl = await page.$('[data-tf-live], [data-typeform], iframe[src*="typeform"]');
    if (typeformEl) {
      console.log('Found Typeform element!');
      const tf = await typeformEl.evaluate(el => ({
        tag: el.tagName,
        src: el.src || '',
        dataTf: el.dataset ? JSON.stringify(el.dataset) : '',
        html: el.outerHTML.slice(0, 200)
      }));
      console.log('Typeform element:', JSON.stringify(tf));
    }

    // Save current page HTML
    const html = await page.content();
    fs.writeFileSync('/home/user/Agents/data/afas-after-solliciteer.html', html);
    console.log('Saved HTML to data/afas-after-solliciteer.html');

    // Try to navigate directly to a potential form URL pattern
    console.log('\n=== Checking for embedded form / hidden sections ===');

    // Look for any element with "form" related classes or attributes
    const formElements = await page.evaluate(() => {
      const els = document.querySelectorAll('[class*="form"], [id*="form"], [class*="Form"], [id*="Form"], form');
      return Array.from(els).map(el => ({
        tag: el.tagName,
        id: el.id,
        class: el.className.slice(0, 50),
        visible: el.offsetParent !== null
      }));
    });
    console.log('Form-related elements:', formElements.length);
    formElements.forEach(e => console.log('  ' + JSON.stringify(e)));

  } catch(e) {
    console.error('Error:', e.message, e.stack);
    screenshots.push(await shot(page, '99-error'));
  } finally {
    await browser.close();
  }

  return screenshots;
}

main().then(shots => {
  console.log('\n=== DONE ===');
  console.log('Screenshots:', shots);
}).catch(e => console.error('FATAL:', e.message));
