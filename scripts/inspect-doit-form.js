/**
 * Inspect the DoiT Greenhouse application form to understand the dropdown/combobox structure
 */
const { chromium } = require('playwright');
const fs = require('fs');

const JOB_URL = 'https://job-boards.greenhouse.io/doitintl/jobs/7515281003';
const CHROME_PATH = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';

function getProxyConfig() {
  const proxyEnv = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || '';
  const m = proxyEnv.match(/http:\/\/([^:]+):([^@]+)@([^:]+):(\d+)/);
  if (m) return { server: 'http://' + m[3] + ':' + m[4], username: m[1], password: m[2] };
  return null;
}

async function run() {
  const proxy = getProxyConfig();
  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    proxy: proxy || undefined,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  try {
    await page.goto(JOB_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Scroll to questions area
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
    await page.waitForTimeout(500);

    // Get full HTML of the form area
    const formHTML = await page.evaluate(() => {
      const form = document.querySelector('form') || document.querySelector('[class*="form"]') || document.body;
      return form.innerHTML.substring(0, 30000);
    });
    fs.writeFileSync('/home/user/Agents/data/doit-form-html.txt', formHTML);
    console.log('Form HTML saved (length:', formHTML.length, ')');

    // Get ALL elements in the question areas
    const questionElements = await page.evaluate(() => {
      const result = [];
      // Find elements with question IDs
      ['question_28554843003', 'question_28554844003', 'question_28554848003', 'question_28554850003'].forEach(qId => {
        const el = document.getElementById(qId);
        if (el) {
          const parent = el.closest('[class*="s-form-field"], [class*="question"], li, .field') || el.parentElement;
          result.push({
            questionId: qId,
            elementTag: el.tagName,
            elementType: el.type,
            elementClasses: el.className,
            parentHTML: parent ? parent.outerHTML.substring(0, 2000) : 'no parent'
          });
        }
      });
      return result;
    });

    questionElements.forEach(q => {
      console.log(`\n=== Question ${q.questionId} ===`);
      console.log('Element:', q.elementTag, q.elementType, q.elementClasses);
      console.log('Parent HTML:', q.parentHTML);
    });

    // Look for listbox, combobox, aria-role elements
    const interactiveElements = await page.evaluate(() => {
      const found = [];
      document.querySelectorAll('[role="combobox"], [role="listbox"], [role="option"], [aria-haspopup], [data-testid*="select"], [class*="select"], [class*="dropdown"]').forEach(el => {
        found.push({
          tag: el.tagName,
          role: el.getAttribute('role') || '',
          ariaLabel: el.getAttribute('aria-label') || '',
          className: (el.className || '').substring(0, 100),
          id: el.id || '',
          text: el.textContent.trim().substring(0, 100)
        });
      });
      return found;
    });
    console.log('\n=== Interactive Select Elements ===');
    interactiveElements.forEach(e => console.log(e));

  } finally {
    await browser.close();
  }
}

run().catch(e => console.error('Error:', e.message));
