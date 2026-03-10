/**
 * DoiT Full Stack Engineer - House Kubernetes (Netherlands)
 * Job ID: 7515281003
 * URL: https://job-boards.greenhouse.io/doitintl/jobs/7515281003
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const JOB_URL = 'https://job-boards.greenhouse.io/doitintl/jobs/7515281003';
const CHROME_PATH = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
const SCREENSHOTS_DIR = '/home/user/Agents/output/screenshots';

const CANDIDATE = {
  firstName: 'Hisham',
  lastName: 'Abboud',
  email: 'hiaham123@hotmail.com',
  phone: '+31 06 4841 2838',
  location: 'Eindhoven, Netherlands',
  linkedin: 'https://linkedin.com/in/hisham-abboud',
  resumePath: '/home/user/Agents/profile/Hisham Abboud CV.pdf',
  coverLetterPath: '/home/user/Agents/output/cover-letters/doit-fullstack-engineer.md',
};

// Answers to screening questions
const ANSWERS = {
  // Q9: Are you based in Netherlands?
  locationEligible: '1', // Yes

  // Q10: Visa sponsorship needed?
  visaSponsorship: '0', // No

  // Q11: Cloud cost optimization experience
  costOptimization: 'At Actemium, I optimized database queries and API response caching in our MES applications, reducing data retrieval time by ~40% for high-frequency operations. While not Kubernetes-native, this demonstrated my approach to performance bottlenecks. At ASML, I built performance test suites using Locust that identified throughput issues under load, enabling the team to address CI/CD bottlenecks before production releases.',

  // Q12: Go, React, Node.js / TypeScript experience
  stackExperience: 'My most recent full-stack work is in JavaScript/React on the frontend and Python/Flask and C#/.NET on the backend at Actemium. I have studied Go and find its concurrency model and performance profile well-suited to cloud microservices. For CogitatAI (my personal project), I built the full stack independently in Python/Flask + React. I am actively developing TypeScript skills and keen to deepen Go in a production setting like House Kubernetes.',

  // Q13: Microservices in cloud
  microservices: 'At ASML I worked within a microservices architecture deployed on Azure and Kubernetes, where I contributed to a performance testing service (Python/Locust) integrated into the CI pipeline. Individual services communicated via REST and were containerized with Docker and orchestrated by Kubernetes. My contribution focused on the test service design, load scenario authoring, and analysis tooling. This gave me direct exposure to the operational realities of microservices — service discovery, independent deployments, and observability.',

  // Q14: Salary range
  salaryRange: '147233154003', // 55K-100K EUR gross per year

  // Q15: Salary expectation
  salaryExpectation: '75,000 EUR gross per year',

  // Q16: Gender
  gender: '147233157003', // Male
};

function getProxyConfig() {
  const proxyEnv = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || '';
  const m = proxyEnv.match(/http:\/\/([^:]+):([^@]+)@([^:]+):(\d+)/);
  if (m) {
    return { server: 'http://' + m[3] + ':' + m[4], username: m[1], password: m[2] };
  }
  return null;
}

async function ss(page, name) {
  const fp = path.join(SCREENSHOTS_DIR, `doit-kubernetes-${name}.png`);
  await page.screenshot({ path: fp, fullPage: true });
  console.log('Screenshot:', fp);
  return fp;
}

async function fillInput(page, selectors, value, label) {
  if (!Array.isArray(selectors)) selectors = [selectors];
  for (const sel of selectors) {
    try {
      const el = await page.$(sel);
      if (el && await el.isVisible()) {
        await el.click({ clickCount: 3 });
        await el.fill('');
        await el.type(value, { delay: 15 });
        console.log(`Filled [${label}] using ${sel}`);
        return true;
      }
    } catch (e) {
      // try next
    }
  }
  console.log(`WARNING: Could not fill [${label}]`);
  return false;
}

async function run() {
  const proxy = getProxyConfig();
  console.log('Proxy:', proxy ? proxy.server : 'none');

  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    proxy: proxy || undefined,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  try {
    // ===== STEP 1: Load job page =====
    console.log('\n[1] Loading job page...');
    const resp = await page.goto(JOB_URL, { waitUntil: 'networkidle', timeout: 30000 });
    console.log('Status:', resp ? resp.status() : 'none');
    await page.waitForTimeout(2000);
    console.log('Title:', await page.title());
    console.log('URL:', page.url());
    await ss(page, '01-job-page');

    // Verify it's the right job
    const bodyText = await page.textContent('body');
    console.log('Page text excerpt:', bodyText.substring(0, 300));
    fs.writeFileSync('/home/user/Agents/data/doit-kubernetes-job.txt', bodyText.substring(0, 6000));

    // ===== STEP 2: Scan form fields =====
    const allFields = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('input, textarea, select')).map(el => {
        const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim() : '';
        const parentText = el.closest('div') ? el.closest('div').textContent.trim().substring(0, 100) : '';
        return {
          tag: el.tagName, type: el.type, id: el.id, name: el.name,
          placeholder: el.placeholder, label, parentText,
          visible: el.offsetParent !== null
        };
      });
    });
    console.log('\n=== FORM FIELDS ===');
    allFields.forEach(f => console.log(`  [${f.tag}/${f.type}] id="${f.id}" name="${f.name}" label="${f.label}" ph="${f.placeholder}"`));
    fs.writeFileSync('/home/user/Agents/data/doit-kubernetes-fields.json', JSON.stringify(allFields, null, 2));

    // ===== STEP 3: Fill basic fields =====
    console.log('\n[3] Filling basic fields...');

    await fillInput(page, [
      'input#first_name',
      'input[name="job_application[first_name]"]',
      'input[placeholder*="First"]',
      'input[id*="first_name"]'
    ], CANDIDATE.firstName, 'First Name');

    await fillInput(page, [
      'input#last_name',
      'input[name="job_application[last_name]"]',
      'input[placeholder*="Last"]',
      'input[id*="last_name"]'
    ], CANDIDATE.lastName, 'Last Name');

    await fillInput(page, [
      'input#email',
      'input[name="job_application[email]"]',
      'input[type="email"]'
    ], CANDIDATE.email, 'Email');

    await fillInput(page, [
      'input#phone',
      'input[name="job_application[phone]"]',
      'input[type="tel"]',
      'input[placeholder*="Phone"]'
    ], CANDIDATE.phone, 'Phone');

    // Candidate Location
    await fillInput(page, [
      'input[id*="location"]',
      'input[name*="location"]',
      'input[placeholder*="location"]',
      'input[placeholder*="Location"]',
      'input[placeholder*="City"]'
    ], CANDIDATE.location, 'Candidate Location');

    await ss(page, '02-basic-fields');

    // ===== STEP 4: LinkedIn =====
    console.log('\n[4] Filling LinkedIn...');
    await fillInput(page, [
      'input[id*="linkedin"]',
      'input[name*="linkedin"]',
      'input[placeholder*="LinkedIn"]',
      'input[placeholder*="linkedin"]'
    ], CANDIDATE.linkedin, 'LinkedIn');

    // ===== STEP 5: File uploads =====
    console.log('\n[5] Uploading resume...');

    // Log all file inputs
    const fileInputs = await page.$$('input[type="file"]');
    console.log('File inputs found:', fileInputs.length);
    for (let i = 0; i < fileInputs.length; i++) {
      const fi = fileInputs[i];
      const fid = await fi.getAttribute('id') || '';
      const fname = await fi.getAttribute('name') || '';
      const faccept = await fi.getAttribute('accept') || '';
      console.log(`  File input ${i}: id="${fid}" name="${fname}" accept="${faccept}"`);
    }

    // Upload resume to first file input or resume-specific one
    let resumeUploaded = false;
    const resumeInput = await page.$('input[type="file"][name*="resume"], input#resume, input[id*="resume"]');
    if (resumeInput) {
      await resumeInput.setInputFiles(CANDIDATE.resumePath);
      console.log('Resume uploaded (named selector)');
      resumeUploaded = true;
      await page.waitForTimeout(2000);
    } else if (fileInputs.length > 0) {
      await fileInputs[0].setInputFiles(CANDIDATE.resumePath);
      console.log('Resume uploaded (first file input)');
      resumeUploaded = true;
      await page.waitForTimeout(2000);
    }

    if (!resumeUploaded) {
      console.log('WARNING: Resume upload failed');
    }

    await ss(page, '03-after-resume');

    // Upload cover letter (if separate input)
    const coverInput = await page.$('input[type="file"][name*="cover"], input#cover_letter, input[id*="cover"]');
    if (coverInput) {
      await coverInput.setInputFiles(CANDIDATE.coverLetterPath);
      console.log('Cover letter uploaded');
      await page.waitForTimeout(1500);
    } else if (fileInputs.length > 1) {
      await fileInputs[1].setInputFiles(CANDIDATE.coverLetterPath);
      console.log('Cover letter uploaded (second file input)');
      await page.waitForTimeout(1500);
    } else {
      console.log('No separate cover letter upload field found');
    }

    // ===== STEP 6: Scroll down to find custom questions =====
    console.log('\n[6] Scrolling to find custom questions...');
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 3));
    await page.waitForTimeout(500);
    await ss(page, '04-mid-form');

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 2 / 3));
    await page.waitForTimeout(500);
    await ss(page, '05-lower-form');

    // ===== STEP 7: Fill screening questions =====
    console.log('\n[7] Filling screening questions...');

    // Get all form elements again after scroll
    const allInputsNow = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('input, textarea, select')).map(el => {
        const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim() : '';
        const surroundingText = el.closest('[class*="question"], [class*="field"], div') ?
          el.closest('[class*="question"], [class*="field"], div').textContent.trim().substring(0, 150) : '';
        return {
          tag: el.tagName, type: el.type, id: el.id, name: el.name,
          placeholder: el.placeholder, label, surroundingText,
          value: el.value ? el.value.substring(0, 50) : '',
          visible: el.offsetParent !== null
        };
      });
    });

    console.log('All inputs now:');
    allInputsNow.forEach(f => console.log(`  [${f.tag}/${f.type}] id="${f.id}" name="${f.name}" label="${f.label}" val="${f.value}" surround="${f.surroundingText.substring(0,80)}"`));

    // Fill textarea/text fields by label content
    const textareas = await page.$$('textarea');
    console.log('Textareas found:', textareas.length);

    // Try to find screening question textareas and fill them
    for (const ta of textareas) {
      const taId = await ta.getAttribute('id') || '';
      const taName = await ta.getAttribute('name') || '';
      const visible = await ta.isVisible();
      if (!visible) continue;

      // Try to find the label for this textarea
      const questionText = await page.evaluate(el => {
        const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim() : '';
        // Look up in the DOM for nearby question text
        const parent = el.closest('[class*="question"], [class*="field"], [class*="form"], li, .field-container') || el.parentElement;
        const parentText = parent ? parent.textContent.trim().substring(0, 200) : '';
        return { label, parentText };
      }, ta);

      console.log(`Textarea id="${taId}" label="${questionText.label}" parent="${questionText.parentText.substring(0,100)}"`);

      const parentLower = questionText.parentText.toLowerCase() + questionText.label.toLowerCase();

      if (parentLower.includes('cost') || parentLower.includes('optimiz') || parentLower.includes('performance')) {
        await ta.click({ clickCount: 3 });
        await ta.fill(ANSWERS.costOptimization);
        console.log('Filled: cost optimization question');
      } else if (parentLower.includes('go') || parentLower.includes('react') || parentLower.includes('node') || parentLower.includes('typescript') || parentLower.includes('stack')) {
        await ta.click({ clickCount: 3 });
        await ta.fill(ANSWERS.stackExperience);
        console.log('Filled: stack experience question');
      } else if (parentLower.includes('microservice') || parentLower.includes('cloud') || parentLower.includes('aws') || parentLower.includes('azure') || parentLower.includes('gcp')) {
        await ta.click({ clickCount: 3 });
        await ta.fill(ANSWERS.microservices);
        console.log('Filled: microservices question');
      } else if (parentLower.includes('salary') || parentLower.includes('compensation')) {
        await ta.click({ clickCount: 3 });
        await ta.fill(ANSWERS.salaryExpectation);
        console.log('Filled: salary expectation');
      }
    }

    // Try text inputs for screening questions
    const textInputs = await page.$$('input[type="text"]');
    for (const ti of textInputs) {
      const tiId = await ti.getAttribute('id') || '';
      const visible = await ti.isVisible();
      const currentVal = await ti.inputValue();
      if (!visible || currentVal.trim()) continue; // skip if already filled

      const questionText = await page.evaluate(el => {
        const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim() : '';
        const parent = el.closest('[class*="question"], [class*="field"], li') || el.parentElement;
        const parentText = parent ? parent.textContent.trim().substring(0, 200) : '';
        return { label, parentText };
      }, ti);

      const qLower = (questionText.label + ' ' + questionText.parentText).toLowerCase();

      if (qLower.includes('cost') || qLower.includes('optimiz')) {
        await ti.click({ clickCount: 3 });
        await ti.fill(ANSWERS.costOptimization);
        console.log(`Filled cost optimization in text input id="${tiId}"`);
      } else if (qLower.includes('go') || qLower.includes('react') || qLower.includes('node') || qLower.includes('typescript')) {
        await ti.click({ clickCount: 3 });
        await ti.fill(ANSWERS.stackExperience);
        console.log(`Filled stack experience in text input id="${tiId}"`);
      } else if (qLower.includes('microservice') || qLower.includes('kubernetes') || qLower.includes('aws') || qLower.includes('azure')) {
        await ti.click({ clickCount: 3 });
        await ti.fill(ANSWERS.microservices);
        console.log(`Filled microservices in text input id="${tiId}"`);
      } else if (qLower.includes('salary') || qLower.includes('compensation') || qLower.includes('expect')) {
        await ti.click({ clickCount: 3 });
        await ti.fill(ANSWERS.salaryExpectation);
        console.log(`Filled salary in text input id="${tiId}"`);
      } else if (qLower.includes('location') || qLower.includes('city') || qLower.includes('where')) {
        await ti.click({ clickCount: 3 });
        await ti.fill(CANDIDATE.location);
        console.log(`Filled location in text input id="${tiId}"`);
      } else if (qLower.includes('linkedin')) {
        await ti.click({ clickCount: 3 });
        await ti.fill(CANDIDATE.linkedin);
        console.log(`Filled linkedin in text input id="${tiId}"`);
      }
    }

    // ===== STEP 8: Radio/Select fields =====
    console.log('\n[8] Handling select/radio fields...');

    // Handle select dropdowns
    const selects = await page.$$('select');
    for (const sel of selects) {
      const selId = await sel.getAttribute('id') || '';
      const selName = await sel.getAttribute('name') || '';
      const visible = await sel.isVisible();
      if (!visible) continue;

      const questionText = await page.evaluate(el => {
        const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim() : '';
        const parent = el.closest('[class*="question"], [class*="field"], li') || el.parentElement;
        const parentText = parent ? parent.textContent.trim().substring(0, 200) : '';
        return { label, parentText };
      }, sel);

      const qLower = (questionText.label + ' ' + questionText.parentText).toLowerCase();
      console.log(`Select id="${selId}" label="${questionText.label}" parent="${questionText.parentText.substring(0,80)}"`);

      // Get available options
      const opts = await sel.evaluate(s => Array.from(s.options).map(o => ({ text: o.text, value: o.value })));
      console.log('  Options:', JSON.stringify(opts.slice(0, 6)));

      if (qLower.includes('based') || qLower.includes('netherlands') || qLower.includes('eligible') || qLower.includes('country')) {
        await sel.selectOption({ value: ANSWERS.locationEligible });
        console.log(`Selected location eligible: ${ANSWERS.locationEligible}`);
      } else if (qLower.includes('visa') || qLower.includes('sponsorship')) {
        await sel.selectOption({ value: ANSWERS.visaSponsorship });
        console.log(`Selected visa sponsorship: ${ANSWERS.visaSponsorship}`);
      } else if (qLower.includes('salary') || qLower.includes('range')) {
        try {
          await sel.selectOption({ value: ANSWERS.salaryRange });
          console.log(`Selected salary range: ${ANSWERS.salaryRange}`);
        } catch (e) {
          // try selecting by text
          await sel.selectOption({ label: '55K-100K EUR gross per year' });
          console.log('Selected salary range by text');
        }
      } else if (qLower.includes('gender')) {
        try {
          await sel.selectOption({ value: ANSWERS.gender });
          console.log(`Selected gender: ${ANSWERS.gender}`);
        } catch (e) {
          await sel.selectOption({ label: 'Male' });
          console.log('Selected gender by text: Male');
        }
      }
    }

    // Handle radio buttons
    const radioGroups = await page.evaluate(() => {
      const groups = {};
      document.querySelectorAll('input[type="radio"]').forEach(r => {
        const name = r.name || r.id;
        if (!groups[name]) groups[name] = [];
        const label = r.labels && r.labels[0] ? r.labels[0].textContent.trim() : '';
        const parent = r.closest('[class*="question"], [class*="field"], li') || r.parentElement;
        groups[name].push({
          name: r.name, id: r.id, value: r.value, label,
          parentText: parent ? parent.textContent.trim().substring(0, 200) : '',
          checked: r.checked
        });
      });
      return groups;
    });

    for (const [groupName, radios] of Object.entries(radioGroups)) {
      console.log(`Radio group "${groupName}":`, JSON.stringify(radios.map(r => ({ val: r.value, lbl: r.label }))));
      const groupText = (radios[0].parentText + ' ' + radios[0].label).toLowerCase();

      if (groupText.includes('based') || groupText.includes('netherlands') || groupText.includes('eligible')) {
        // Select Yes
        const yesRadio = radios.find(r => r.value === '1' || r.label.toLowerCase() === 'yes');
        if (yesRadio) {
          await page.click(`input[type="radio"][value="${yesRadio.value}"][name="${groupName}"]`);
          console.log('Selected: location eligible = Yes');
        }
      } else if (groupText.includes('visa') || groupText.includes('sponsor')) {
        // Select No
        const noRadio = radios.find(r => r.value === '0' || r.label.toLowerCase() === 'no');
        if (noRadio) {
          await page.click(`input[type="radio"][value="${noRadio.value}"][name="${groupName}"]`);
          console.log('Selected: visa sponsorship = No');
        }
      } else if (groupText.includes('salary') || groupText.includes('range')) {
        const mid = radios.find(r => r.value === ANSWERS.salaryRange || r.label.includes('55K') || r.label.includes('55k'));
        if (mid) {
          await page.click(`input[type="radio"][value="${mid.value}"][name="${groupName}"]`);
          console.log('Selected salary range: 55K-100K');
        }
      } else if (groupText.includes('gender')) {
        const male = radios.find(r => r.value === ANSWERS.gender || r.label.toLowerCase() === 'male');
        if (male) {
          await page.click(`input[type="radio"][value="${male.value}"][name="${groupName}"]`);
          console.log('Selected gender: Male');
        }
      }
    }

    await page.waitForTimeout(500);
    await ss(page, '06-screening-filled');

    // ===== STEP 9: Scroll to bottom =====
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);
    await ss(page, '07-bottom-of-form');

    // ===== STEP 10: Check remaining empty fields =====
    const remaining = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], textarea')).filter(el => {
        return el.offsetParent !== null && (!el.value || el.value.trim() === '');
      }).map(el => {
        const label = el.labels && el.labels[0] ? el.labels[0].textContent.trim() : '';
        const parent = el.closest('[class*="question"], [class*="field"], li') || el.parentElement;
        return { id: el.id, name: el.name, placeholder: el.placeholder, label, parentText: parent ? parent.textContent.trim().substring(0, 150) : '' };
      });
    });
    console.log('\nRemaining empty fields:', JSON.stringify(remaining, null, 2));

    // ===== STEP 11: Final pre-submit screenshot =====
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    await ss(page, '08-before-submit');

    // Log all buttons
    const buttons = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button, input[type="submit"]')).map(b => ({
        tag: b.tagName, type: b.type, text: b.textContent.trim().substring(0, 80),
        value: b.value || '', visible: b.offsetParent !== null
      }));
    });
    console.log('Buttons:', JSON.stringify(buttons));

    // ===== STEP 12: Submit =====
    console.log('\n[12] Looking for submit button...');
    const submitBtn = await page.$('input[type="submit"]:visible, button[type="submit"]:visible, button:has-text("Submit"):visible');
    if (submitBtn) {
      const btnText = await submitBtn.textContent().catch(() => '');
      const btnVal = await submitBtn.getAttribute('value').catch(() => '');
      console.log('Submit button found:', btnText || btnVal);

      await ss(page, '09-ready-to-submit');
      console.log('Submitting application...');
      await submitBtn.click();
      await page.waitForTimeout(5000);

      const postUrl = page.url();
      const postTitle = await page.title();
      const postText = await page.textContent('body');
      console.log('Post-submit URL:', postUrl);
      console.log('Post-submit title:', postTitle);
      console.log('Post-submit text:', postText.substring(0, 500));

      await ss(page, '10-after-submit');

      const successWords = ['thank', 'received', 'submitted', 'success', 'confirm', 'application'];
      const isSuccess = successWords.some(w => postText.toLowerCase().includes(w)) &&
                        !postText.toLowerCase().includes('error') && postUrl !== JOB_URL;

      console.log('SUCCESS:', isSuccess);
      return { success: isSuccess, postUrl, postTitle, message: postText.substring(0, 400) };

    } else {
      console.log('No visible submit button found');
      await ss(page, '09-no-submit');

      // All buttons
      const allBtns = await page.evaluate(() =>
        Array.from(document.querySelectorAll('button, input[type="submit"]')).map(b => ({
          text: b.textContent.trim().substring(0, 80), type: b.type, visible: b.offsetParent !== null
        }))
      );
      console.log('All buttons on page:', JSON.stringify(allBtns));
      return { success: false, error: 'No submit button found', postUrl: page.url() };
    }

  } catch (err) {
    console.error('Error:', err.message);
    await ss(page, '99-error').catch(() => {});
    return { success: false, error: err.message };
  } finally {
    await browser.close();
    console.log('Browser closed.');
  }
}

run().then(result => {
  console.log('\n=== FINAL RESULT ===');
  console.log(JSON.stringify(result, null, 2));
  fs.writeFileSync('/home/user/Agents/data/doit-kubernetes-result.json', JSON.stringify(result, null, 2));
}).catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
