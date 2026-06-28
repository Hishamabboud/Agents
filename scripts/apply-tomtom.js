const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';
const RESUME_PATH = '/home/user/Agents/profile/resume.pdf';

const applicant = {
  name: 'Hisham Abboud',
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31 06 4841 2838',
  location: 'Eindhoven, Netherlands',
};

function screenshotPath(name) {
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  return path.join(SCREENSHOTS_DIR, `tomtom-${name}-${ts}.png`);
}

async function run() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();

  const log = (msg) => {
    const ts = new Date().toISOString();
    console.log(`[${ts}] ${msg}`);
  };

  try {
    // Step 1: Navigate to TomTom careers
    log('Navigating to TomTom careers page...');
    await page.goto('https://www.tomtom.com/careers/joboverview/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: screenshotPath('01-careers-home'), fullPage: true });
    log('Screenshot 01 taken: careers home');

    // Step 2: Search for Software Engineer jobs
    log('Looking for Software Engineer vacancies...');

    // Try to find a search box or filter
    const searchSelectors = [
      'input[placeholder*="search" i]',
      'input[placeholder*="Search" i]',
      'input[type="search"]',
      'input[name*="search" i]',
      'input[id*="search" i]',
      '#search',
      '.search-input',
    ];

    let searchBox = null;
    for (const sel of searchSelectors) {
      try {
        searchBox = await page.$(sel);
        if (searchBox) {
          log(`Found search box: ${sel}`);
          break;
        }
      } catch (e) {}
    }

    if (searchBox) {
      await searchBox.click();
      await searchBox.fill('Software Engineer');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
      await page.screenshot({ path: screenshotPath('02-search-results'), fullPage: true });
      log('Screenshot 02 taken: search results');
    } else {
      log('No search box found, looking for job listings directly...');
      await page.screenshot({ path: screenshotPath('02-no-search'), fullPage: true });
    }

    // Step 3: Find relevant job listing
    log('Looking for Software Engineer job listing...');
    const jobLinkSelectors = [
      'a:has-text("Software Engineer")',
      'a:has-text("software engineer")',
      '[class*="job"] a',
      '[class*="vacancy"] a',
      '[class*="position"] a',
      '[class*="opening"] a',
    ];

    let jobLink = null;
    for (const sel of jobLinkSelectors) {
      try {
        const links = await page.$$(sel);
        if (links.length > 0) {
          // Prefer Eindhoven or Netherlands
          for (const link of links) {
            const text = await link.textContent();
            if (text && (text.toLowerCase().includes('eindhoven') || text.toLowerCase().includes('netherlands') || text.toLowerCase().includes('software'))) {
              jobLink = link;
              log(`Found job link: ${text.trim().substring(0, 100)}`);
              break;
            }
          }
          if (!jobLink) jobLink = links[0];
          break;
        }
      } catch (e) {}
    }

    if (jobLink) {
      await jobLink.click();
      await page.waitForTimeout(3000);
      await page.screenshot({ path: screenshotPath('03-job-detail'), fullPage: true });
      log('Screenshot 03 taken: job detail');
    } else {
      log('No direct job link found. Current URL: ' + page.url());
      // Try to get page content for analysis
      const content = await page.content();
      const linkMatches = content.match(/href="[^"]*job[^"]*"/gi) || [];
      log('Job-related links found: ' + linkMatches.slice(0, 5).join(', '));

      // Try alternative: look at all links
      const allLinks = await page.$$('a');
      log(`Total links on page: ${allLinks.length}`);
      for (const link of allLinks.slice(0, 20)) {
        const href = await link.getAttribute('href');
        const text = await link.textContent();
        if (href && text) log(`  Link: ${text.trim().substring(0, 50)} -> ${href.substring(0, 80)}`);
      }
    }

    // Step 4: Look for Apply button
    log('Looking for Apply button...');
    const applySelectors = [
      'a:has-text("Apply now")',
      'a:has-text("Apply Now")',
      'button:has-text("Apply")',
      'a:has-text("Apply")',
      '[class*="apply"]',
      '#apply',
    ];

    let applyButton = null;
    for (const sel of applySelectors) {
      try {
        applyButton = await page.$(sel);
        if (applyButton) {
          log(`Found apply button: ${sel}`);
          break;
        }
      } catch (e) {}
    }

    if (applyButton) {
      await applyButton.click();
      await page.waitForTimeout(4000);
      await page.screenshot({ path: screenshotPath('04-apply-page'), fullPage: true });
      log('Screenshot 04 taken: apply page');
      log('Current URL after Apply click: ' + page.url());
    } else {
      log('No Apply button found at this stage.');
    }

    // Step 5: Fill in the form
    log('Attempting to fill in the application form...');

    const fieldMappings = [
      { selectors: ['input[name*="first" i]', 'input[id*="first" i]', 'input[placeholder*="first name" i]'], value: applicant.firstName },
      { selectors: ['input[name*="last" i]', 'input[id*="last" i]', 'input[placeholder*="last name" i]'], value: applicant.lastName },
      { selectors: ['input[name*="email" i]', 'input[id*="email" i]', 'input[type="email"]'], value: applicant.email },
      { selectors: ['input[name*="phone" i]', 'input[id*="phone" i]', 'input[type="tel"]', 'input[placeholder*="phone" i]'], value: applicant.phone },
    ];

    let filledFields = 0;
    for (const field of fieldMappings) {
      for (const sel of field.selectors) {
        try {
          const el = await page.$(sel);
          if (el) {
            await el.click({ clickCount: 3 });
            await el.fill(field.value);
            log(`Filled field "${sel}" with "${field.value}"`);
            filledFields++;
            break;
          }
        } catch (e) {}
      }
    }

    if (filledFields > 0) {
      await page.screenshot({ path: screenshotPath('05-form-filled'), fullPage: true });
      log('Screenshot 05 taken: form filled');
    }

    // Step 6: Upload resume
    log('Attempting to upload resume...');
    const uploadSelectors = [
      'input[type="file"]',
      'input[name*="resume" i]',
      'input[name*="cv" i]',
      '[class*="upload"] input',
    ];

    let uploaded = false;
    for (const sel of uploadSelectors) {
      try {
        const fileInput = await page.$(sel);
        if (fileInput) {
          await fileInput.setInputFiles(RESUME_PATH);
          log(`Resume uploaded via: ${sel}`);
          uploaded = true;
          await page.waitForTimeout(2000);
          await page.screenshot({ path: screenshotPath('06-resume-uploaded'), fullPage: true });
          log('Screenshot 06 taken: resume uploaded');
          break;
        }
      } catch (e) {
        log(`Upload attempt failed for ${sel}: ${e.message}`);
      }
    }

    if (!uploaded) {
      log('Could not find file upload input.');
    }

    // Step 7: Final screenshot before submit
    await page.screenshot({ path: screenshotPath('07-pre-submit'), fullPage: true });
    log('Screenshot 07 taken: pre-submit state');
    log('Final URL: ' + page.url());

    // Check if there's a submit button (but DO NOT click it to avoid accidental submission)
    const submitSelectors = [
      'button[type="submit"]',
      'input[type="submit"]',
      'button:has-text("Submit")',
      'button:has-text("Send")',
    ];

    let submitFound = false;
    for (const sel of submitSelectors) {
      try {
        const btn = await page.$(sel);
        if (btn) {
          const text = await btn.textContent();
          log(`Found submit button: "${text}" (selector: ${sel}) — NOT clicking to avoid accidental submission`);
          submitFound = true;
          break;
        }
      } catch (e) {}
    }

    // Summary
    const summary = {
      company: 'TomTom',
      role: 'Software Engineer',
      url: page.url(),
      date: new Date().toISOString(),
      status: submitFound ? 'ready-to-submit' : 'form-explored',
      notes: `Filled ${filledFields} form fields. Resume uploaded: ${uploaded}. Submit button found: ${submitFound}.`,
      screenshots: fs.readdirSync(SCREENSHOTS_DIR).filter(f => f.startsWith('tomtom-')).map(f => path.join(SCREENSHOTS_DIR, f)),
    };

    console.log('\n=== SUMMARY ===');
    console.log(JSON.stringify(summary, null, 2));

  } catch (err) {
    log(`ERROR: ${err.message}`);
    await page.screenshot({ path: screenshotPath('error'), fullPage: true });
    console.error(err);
  } finally {
    await browser.close();
  }
}

run();
