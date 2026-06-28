const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const COVER_LETTER = `Hisham Abboud
Eindhoven, Netherlands
hiaham123@hotmail.com | +31 06 4841 2838
linkedin.com/in/hisham-abboud

---

Datum: 11 juni 2026
Aan: AFAS Software, Recruitment Team
Betreft: Software Engineer — Leusden

Beste wervingsteam,

Met veel interesse schrijf ik u naar aanleiding van de vacature Software Engineer bij AFAS Software. Als afgestudeerd Software Engineer met ruim twee en een half jaar werkervaring en een passie voor het ontwikkelen van kwalitatieve software, sluit mijn profiel goed aan bij wat jullie zoeken. Dat AFAS al meerdere keren is uitgeroepen tot beste werkgever van Europa spreekt boekdelen over de cultuur en het werkklimaat — iets dat voor mij zwaar meeweegt in mijn keuze.

In mijn huidige functie als Software Service Engineer bij Actemium ontwikkel en onderhoud ik full-stack applicaties met C#, .NET, ASP.NET, Python/Flask en JavaScript voor industriele klanten. Ik werk dagelijks met SQL-databases, REST API's en complexe systeemintegraties in productieomgevingen. Tijdens mijn stage bij ASML heb ik Python-testframeworks ontwikkeld in een agile team met Azure en Kubernetes, en bij Delta Electronics heb ik een legacy Visual Basic codebase gemigreerd naar C# en een interne webapplicatie gebouwd. Deze ervaringen hebben mij een brede technische basis gegeven en het vermogen om snel nieuwe frameworks en talen eigen te maken — wat goed past bij het werken met de eigen frameworks van AFAS.

Naast mijn werkervaring heb ik CogitatAI opgezet: een AI-gestuurd klantenserviceplatform dat ik zelfstandig heb ontworpen en ontwikkeld met Python/Flask. Dit project toont mijn ondernemende instelling en mijn drive om end-to-end verantwoordelijkheid te nemen voor softwareproducten. Ik ben vloeiend in het Nederlands, Engels en Arabisch, en ik heb mijn HBO-diploma Software Engineering behaald aan Fontys in Eindhoven.

Het vooruitzicht van een vierdaagse werkweek met een ontwikkeldag op vrijdag spreekt mij bijzonder aan als kans om continu te blijven leren en groeien. Ik zou graag in een persoonlijk gesprek toelichten hoe mijn ervaring en enthousiasme kunnen bijdragen aan het team van AFAS. Hartelijk dank voor uw tijd en overweging.

Met vriendelijke groet,
Hisham Abboud`;

const RESUME_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';
const SCREENSHOT_DIR = '/home/user/Agents/output/screenshots';

function ts() {
  return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
}

async function screenshot(page, name) {
  const file = path.join(SCREENSHOT_DIR, `afas-${name}-${ts()}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`Screenshot: ${file}`);
  return file;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 }
  });
  const page = await context.newPage();

  try {
    console.log('Navigating to AFAS job page...');
    await page.goto('https://www.werkenbijafas.nl/job/software-engineer', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    await screenshot(page, '01-job-page');

    // Log page title and URL
    console.log('Page title:', await page.title());
    console.log('Current URL:', page.url());

    // Look for apply/solliciteer button
    const pageContent = await page.content();
    console.log('Page length:', pageContent.length);

    // Save page HTML for inspection
    fs.writeFileSync('/home/user/Agents/data/afas-job-page.html', pageContent);
    console.log('Saved page HTML to data/afas-job-page.html');

    // Find all buttons and links
    const buttons = await page.$$eval('a, button', els => els.map(el => ({
      tag: el.tagName,
      text: el.textContent?.trim().slice(0, 100),
      href: el.href || '',
      classes: el.className
    })));

    console.log('\nAll links/buttons found:');
    buttons.forEach(b => {
      if (b.text && b.text.length > 0) {
        console.log(`  [${b.tag}] "${b.text}" => ${b.href || '(no href)'}`);
      }
    });

    // Try to find solliciteer button
    const applySelectors = [
      'a[href*="sollicit"]',
      'button:has-text("Solliciteer")',
      'a:has-text("Solliciteer")',
      'button:has-text("sollicit")',
      'a:has-text("sollicit")',
      'a[href*="apply"]',
      '.apply-button',
      '[data-test="apply-button"]',
      'button[type="submit"]',
      '.btn-apply'
    ];

    let applyEl = null;
    for (const sel of applySelectors) {
      try {
        const el = await page.$(sel);
        if (el) {
          applyEl = el;
          console.log(`Found apply element with selector: ${sel}`);
          break;
        }
      } catch(e) {}
    }

    if (applyEl) {
      const href = await applyEl.getAttribute('href');
      const text = await applyEl.textContent();
      console.log(`Apply button text: "${text}", href: ${href}`);

      await applyEl.click();
      await page.waitForTimeout(3000);
      await screenshot(page, '02-after-apply-click');
      console.log('After click URL:', page.url());
    } else {
      console.log('No apply button found via selectors, checking page text...');

      // Look for any text containing sollicit
      const textContent = await page.evaluate(() => document.body.innerText);
      const lines = textContent.split('\n').filter(l => l.toLowerCase().includes('sollicit'));
      console.log('Lines with "sollicit":', lines.slice(0, 10));

      // Try scrolling down to load more content
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(2000);
      await screenshot(page, '02-scrolled-down');

      // Check again after scroll
      const applyEl2 = await page.$('a[href*="sollicit"], button:has-text("Solliciteer"), a:has-text("Solliciteer")');
      if (applyEl2) {
        console.log('Found apply button after scroll');
        await applyEl2.click();
        await page.waitForTimeout(3000);
        await screenshot(page, '03-after-apply-click');
        console.log('After click URL:', page.url());
      }
    }

    // Check current state - are we on a form now?
    const currentUrl = page.url();
    console.log('\nCurrent URL after navigation attempt:', currentUrl);

    // Look for form elements
    const formInputs = await page.$$eval('input, textarea, select', els => els.map(el => ({
      type: el.type || el.tagName,
      name: el.name,
      placeholder: el.placeholder,
      id: el.id,
      label: document.querySelector(`label[for="${el.id}"]`)?.textContent?.trim()
    })));

    console.log('\nForm inputs found:', formInputs.length);
    formInputs.forEach(i => console.log(`  ${JSON.stringify(i)}`));

  } catch(e) {
    console.error('Error:', e.message);
    await screenshot(page, '99-error');
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
