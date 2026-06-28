
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 }
  });
  const page = await context.newPage();
  
  try {
    // Navigate to the job page
    console.log('Navigating to job page...');
    await page.goto('https://ixonbv.recruitee.com/o/embedded-software-engineer', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/ixon-01-job-page.png', fullPage: true });
    console.log('Screenshot 1: Job page captured');
    
    // Get the page title and check for apply button
    const title = await page.title();
    console.log('Page title:', title);
    
    // Look for apply button
    const applyButton = await page.$('[data-testid="apply-button"], .apply-button, button:has-text("Apply"), a:has-text("Apply"), button:has-text("Solliciteren"), a:has-text("Solliciteren")');
    
    if (applyButton) {
      console.log('Found apply button, clicking...');
      await applyButton.click();
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: '/home/user/Agents/output/screenshots/ixon-02-after-apply-click.png', fullPage: true });
      console.log('Screenshot 2: After apply click');
    } else {
      console.log('No apply button found, checking page content...');
      const content = await page.content();
      // Check if we're already on form
      const hasForm = await page.$('form, input[type="email"], input[name="email"]');
      if (!hasForm) {
        // Try scrolling to find button
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
        await page.waitForTimeout(1000);
        await page.screenshot({ path: '/home/user/Agents/output/screenshots/ixon-02-scrolled.png', fullPage: true });
        console.log('Screenshot 2: Scrolled page');
      }
    }
    
    // Wait a moment for form to load
    await page.waitForTimeout(2000);
    
    // Take screenshot of current state
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/ixon-03-form-state.png', fullPage: true });
    console.log('Screenshot 3: Form state');
    
    // Try to find and fill form fields
    // Name field
    const nameField = await page.$('input[name="name"], input[placeholder*="name"], input[placeholder*="Name"], input[id*="name"]');
    if (nameField) {
      await nameField.fill('Hisham Abboud');
      console.log('Filled name field');
    }
    
    // First name
    const firstNameField = await page.$('input[name="first_name"], input[placeholder*="First name"], input[id*="first_name"]');
    if (firstNameField) {
      await firstNameField.fill('Hisham');
      console.log('Filled first name field');
    }
    
    // Last name
    const lastNameField = await page.$('input[name="last_name"], input[placeholder*="Last name"], input[id*="last_name"]');
    if (lastNameField) {
      await lastNameField.fill('Abboud');
      console.log('Filled last name field');
    }
    
    // Email field
    const emailField = await page.$('input[type="email"], input[name="email"], input[placeholder*="email"], input[placeholder*="Email"]');
    if (emailField) {
      await emailField.fill('hiaham123@hotmail.com');
      console.log('Filled email field');
    }
    
    // Phone field
    const phoneField = await page.$('input[type="tel"], input[name="phone"], input[placeholder*="phone"], input[placeholder*="Phone"]');
    if (phoneField) {
      await phoneField.fill('+31 06 4841 2838');
      console.log('Filled phone field');
    }
    
    // Take screenshot after filling basic fields
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/ixon-04-fields-filled.png', fullPage: true });
    console.log('Screenshot 4: Fields filled');
    
    // Look for file upload for resume
    const fileInput = await page.$('input[type="file"]');
    if (fileInput) {
      await fileInput.setInputFiles('/home/user/Agents/profile/Hisham Abboud CV.pdf');
      console.log('Uploaded resume file');
      await page.waitForTimeout(2000);
    }
    
    // Take pre-submit screenshot
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/ixon-05-pre-submit.png', fullPage: true });
    console.log('Screenshot 5: Pre-submit state');
    
    // Look for submit button
    const submitButton = await page.$('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Send"), button:has-text("Apply"), button:has-text("Verzenden"), button:has-text("Versturen")');
    
    if (submitButton) {
      const buttonText = await submitButton.textContent();
      console.log('Found submit button:', buttonText);
      // Don't submit yet - take final screenshot
      console.log('Submit button found - NOT submitting (manual review needed)');
    } else {
      console.log('No submit button found');
    }
    
    // Final screenshot
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/ixon-06-final.png', fullPage: true });
    console.log('Screenshot 6: Final state');
    
    // Get all form fields for reporting
    const formFields = await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
      return inputs.map(el => ({
        type: el.type || el.tagName,
        name: el.name,
        id: el.id,
        placeholder: el.placeholder,
        value: el.value ? el.value.substring(0, 50) : ''
      }));
    });
    console.log('Form fields found:', JSON.stringify(formFields, null, 2));
    
  } catch (err) {
    console.error('Error:', err.message);
    await page.screenshot({ path: '/home/user/Agents/output/screenshots/ixon-error.png', fullPage: true });
  } finally {
    await browser.close();
  }
})();
