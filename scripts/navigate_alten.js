#!/usr/bin/env node
/**
 * Navigate to ALTEN Nederland job listing and find the application page.
 * Then attempt to apply.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';
const CV_PATH = '/home/user/Agents/profile/Hisham Abboud CV.pdf';

const APPLICANT = {
  firstName: 'Hisham',
  lastName: 'Abboud',
  name: 'Hisham Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31648412838',
  location: 'Eindhoven, Netherlands',
  linkedin: 'linkedin.com/in/hisham-abboud',
};

const COVER_LETTER = `Dear Hiring Manager at ALTEN Nederland,

I am writing to express my strong interest in the Software Engineer (Python/C#) - Data & Monitoring position at ALTEN Nederland in Rotterdam. With hands-on experience in both Python and C#/.NET, combined with a background in data monitoring and Azure, I am confident I can make an immediate contribution to your team.

At ASML, I developed Python-based solutions for data processing and automation. At Actemium and Delta Electronics, I built robust C#/.NET applications with focus on reliability and maintainability. My experience with Azure services and CI/CD pipelines aligns well with the modern development practices at ALTEN.

I hold a BSc in Software Engineering from Fontys University of Applied Sciences in Eindhoven, and I am eager to bring my technical skills to ALTEN's challenging engineering projects.

I would welcome the opportunity to discuss how my experience aligns with your team's needs.

Best regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
linkedin.com/in/hisham-abboud`;

async function screenshot(page, name) {
  const ts = new Date().toISOString().replace(/[:.]/g, '_').slice(0, 19);
  const filepath = path.join(SCREENSHOTS_DIR, `alten-${name}-${ts}.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`Screenshot: ${filepath}`);
  return filepath;
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled',
      '--disable-web-security',
    ],
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    locale: 'nl-NL',
    timezoneId: 'Europe/Amsterdam',
    viewport: { width: 1280, height: 800 },
  });

  const page = await context.newPage();

  // Remove automation indicators
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  const visitedUrls = [];
  page.on('response', (r) => {
    if ([200, 301, 302, 303, 307, 308].includes(r.status())) {
      visitedUrls.push({ status: r.status(), url: r.url() });
    }
  });

  console.log('Navigating to initial URL...');
  try {
    await page.goto('https://englishjobsearch.nl/clickout/bc0a1044202977b3', {
      waitUntil: 'networkidle',
      timeout: 30000,
    });
  } catch (e) {
    console.log(`Navigation timeout/error (may be OK): ${e.message}`);
  }

  let finalUrl = page.url();
  console.log(`Final URL: ${finalUrl}`);
  const ss1 = await screenshot(page, '01-initial');

  const title = await page.title();
  console.log(`Page title: ${title}`);

  // Get all links on page
  const links = await page.$$eval('a', (els) =>
    els.map((e) => ({ href: e.href, text: e.textContent.trim() }))
  );

  console.log('Links on page:');
  for (const l of links.slice(0, 20)) {
    if (l.href) console.log(`  [${l.text.slice(0, 50)}] => ${l.href}`);
  }

  // Check if we ended up on a meaningful page
  if (finalUrl.includes('thebigjobsite') || finalUrl.includes('englishjobsearch')) {
    console.log('\nStill on aggregator site. Looking for job detail link...');
    // Try to find the actual job URL
    const jobLinks = links.filter(
      (l) =>
        l.href &&
        !l.href.includes('englishjobsearch') &&
        !l.href.includes('thebigjobsite') &&
        (l.href.includes('alten') || l.href.includes('apply') || l.text.toLowerCase().includes('apply'))
    );
    console.log('Potential apply links:', jobLinks);
  }

  console.log('\nAll visited URLs:');
  for (const v of visitedUrls) {
    console.log(`  ${v.status}: ${v.url}`);
  }

  // Try navigating directly to ALTEN NL careers
  console.log('\nTrying ALTEN NL careers page directly...');
  const altenUrls = [
    'https://www.alten.nl/vacatures/',
    'https://www.alten.com/country/netherlands/jobs/',
    'https://careers.alten.nl/',
    'https://www.alten.nl/en/vacancies/',
  ];

  let foundAltenPage = false;
  for (const url of altenUrls) {
    console.log(`Trying: ${url}`);
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
      const currentUrl = page.url();
      const pageTitle = await page.title();
      console.log(`  -> ${currentUrl} | ${pageTitle}`);
      await screenshot(page, `alten-careers-${url.replace(/[^a-z0-9]/gi, '_').slice(-30)}`);
      if (!pageTitle.includes('404') && !pageTitle.includes('Error')) {
        foundAltenPage = true;
        console.log(`  Found a valid page!`);
        break;
      }
    } catch (e) {
      console.log(`  Error: ${e.message}`);
    }
  }

  await browser.close();
  console.log('\nDone.');
}

main().catch(console.error);
