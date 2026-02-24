#!/usr/bin/env python3
"""
Re-apply to Sendent B.V. Medior Software Engineer position on join.com
CRITICAL: Use email hiaham123@hotmail.com (NOT Hisham123@hotmail.com)
"""

import asyncio
import json
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/home/user/Agents/output/screenshots"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"
RESUME_PDF = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
JOB_URL = "https://join.com/companies/sendentcom/15650046-medior-software-engineer-backend-integrations-net"

APPLICANT = {
    "email": "hiaham123@hotmail.com",  # CORRECT email - hiaham not Hisham
    "first_name": "Hisham",
    "last_name": "Abboud",
    "phone": "0648412838",  # without country code
    "phone_country": "Netherlands",  # +31
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
}

COVER_LETTER = """Dear Sendent B.V. Hiring Team,

I am applying for the Medior Software Engineer (Backend/Integrations/.NET) position. Sendent's focus on sustainable software, privacy-first design, and real ownership aligns well with my professional values.

As a Software Service Engineer at Actemium in Eindhoven, I work daily with C#/.NET building and maintaining production integrations for industrial clients. I develop API connections, optimize databases, and troubleshoot complex issues in live environments. My experience migrating legacy codebases (Visual Basic to C#) at Delta Electronics demonstrates my ability to work with unfamiliar code and improve it methodically.

I also bring strong testing experience from ASML with Pytest and Locust, and CI/CD workflows in agile environments. My graduation project on GDPR data anonymization gave me direct exposure to privacy and compliance concerns.

I am based in Eindhoven with a valid Dutch work permit.

Best regards,
Hisham Abboud"""

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/sendent-reapply-{name}-{ts()}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"Screenshot: {path}")
    return path

async def main():
    screenshots = []
    status = "failed"
    notes = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--ignore-certificate-errors",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
        )

        # Mask webdriver property
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        page = await context.new_page()

        try:
            # Step 1: Navigate to job listing
            print(f"Navigating to job listing: {JOB_URL}")
            await page.goto(JOB_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            s = await screenshot(page, "01-job-listing")
            screenshots.append(s)

            # Step 2: Click Apply button
            print("Looking for Apply button...")
            apply_btn = page.locator("a[href*='/apply'], button:has-text('Apply'), a:has-text('Apply now'), a:has-text('Apply')")

            # Try different selectors
            found = False
            for selector in [
                "a[href*='/apply']",
                "button:has-text('Apply')",
                "a:has-text('Apply now')",
                "a:has-text('Apply')",
                "[data-testid='apply-button']",
                ".apply-button",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=2000):
                        print(f"Found apply button with selector: {selector}")
                        await el.click()
                        found = True
                        break
                except:
                    continue

            if not found:
                # Try direct navigation to apply URL
                apply_url = "https://join.com/companies/sendentcom/15650046/apply"
                print(f"No apply button found, navigating directly to: {apply_url}")
                await page.goto(apply_url, wait_until="networkidle", timeout=30000)

            await asyncio.sleep(3)
            s = await screenshot(page, "02-after-apply-click")
            screenshots.append(s)

            current_url = page.url
            print(f"Current URL: {current_url}")

            # Step 3: Handle email entry step
            # join.com flow: first enter email, then personal details
            email_input = None
            for selector in [
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='email' i]",
                "input[placeholder*='Email' i]",
                "#email",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=3000):
                        email_input = el
                        print(f"Found email input with: {selector}")
                        break
                except:
                    continue

            if email_input:
                print(f"Entering email: {APPLICANT['email']}")
                await email_input.click()
                await email_input.triple_click()
                await email_input.fill("")
                await asyncio.sleep(0.5)
                # Type slowly to avoid autocorrect
                await email_input.type(APPLICANT['email'], delay=80)
                await asyncio.sleep(1)

                # Verify what was typed
                typed_value = await email_input.input_value()
                print(f"Email field contains: '{typed_value}'")

                s = await screenshot(page, "03-email-entered")
                screenshots.append(s)

                # Click Continue/Next button
                for btn_selector in [
                    "button[type='submit']",
                    "button:has-text('Continue')",
                    "button:has-text('Next')",
                    "button:has-text('Sign up')",
                    "button:has-text('Get started')",
                    "input[type='submit']",
                ]:
                    try:
                        btn = page.locator(btn_selector).first
                        if await btn.is_visible(timeout=2000):
                            print(f"Clicking continue with: {btn_selector}")
                            await btn.click()
                            break
                    except:
                        continue

                await asyncio.sleep(3)
                s = await screenshot(page, "04-after-email-continue")
                screenshots.append(s)
                current_url = page.url
                print(f"URL after email: {current_url}")
            else:
                print("No email input found on this page")

            # Step 4: Personal Information form
            # Check if we're on personal information page
            page_content = await page.content()
            current_url = page.url
            print(f"Current URL: {current_url}")

            if "personalInformation" in current_url or "personal" in current_url.lower():
                print("On personal information page")

            # Fill First Name
            for selector in [
                "input[name='firstName']",
                "input[placeholder*='First name' i]",
                "input[id*='firstName' i]",
                "input[id*='first' i]",
                "input[placeholder*='first' i]",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=3000):
                        print(f"Filling first name with selector: {selector}")
                        await el.triple_click()
                        await el.fill(APPLICANT['first_name'])
                        break
                except:
                    continue

            # Fill Last Name
            for selector in [
                "input[name='lastName']",
                "input[placeholder*='Last name' i]",
                "input[id*='lastName' i]",
                "input[id*='last' i]",
                "input[placeholder*='last' i]",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=3000):
                        print(f"Filling last name with selector: {selector}")
                        await el.triple_click()
                        await el.fill(APPLICANT['last_name'])
                        break
                except:
                    continue

            await asyncio.sleep(1)

            # Set Country of Residence to Netherlands
            print("Setting country to Netherlands...")
            country_set = False
            for selector in [
                "select[name='country']",
                "select[id*='country' i]",
                "[class*='country'] select",
                "select:near(:text('Country'))",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=2000):
                        await el.select_option(label="Netherlands")
                        print(f"Set country via select: {selector}")
                        country_set = True
                        break
                except:
                    continue

            if not country_set:
                # Try dropdown/combobox approach
                for selector in [
                    "[aria-label*='country' i]",
                    "[placeholder*='Country' i]",
                    "div[class*='country']",
                ]:
                    try:
                        el = page.locator(selector).first
                        if await el.is_visible(timeout=2000):
                            await el.click()
                            await asyncio.sleep(1)
                            netherlands_option = page.locator("text=Netherlands").first
                            if await netherlands_option.is_visible(timeout=2000):
                                await netherlands_option.click()
                                country_set = True
                                print(f"Set country via dropdown click")
                                break
                    except:
                        continue

            await asyncio.sleep(1)

            # Set Phone Number with Netherlands prefix (+31)
            print("Setting phone number with Netherlands prefix...")

            # First try to set the country code dropdown
            phone_country_set = False
            for selector in [
                "select[name='phoneCountry']",
                "select[name='countryCode']",
                "button[class*='phone']:has-text('+1')",
                "button[class*='phone']",
                "[class*='phone-country']",
                "[class*='phoneCountry']",
                "div[class*='PhoneInput'] button",
                ".phone-code-selector",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=2000):
                        print(f"Found phone country with: {selector}")
                        if selector.startswith("select"):
                            await el.select_option(label="Netherlands")
                            phone_country_set = True
                        else:
                            await el.click()
                            await asyncio.sleep(1)
                            # Look for Netherlands in dropdown
                            for nl_selector in [
                                "text=Netherlands",
                                "li:has-text('Netherlands')",
                                "option:has-text('Netherlands')",
                                "[data-country='NL']",
                            ]:
                                try:
                                    nl_el = page.locator(nl_selector).first
                                    if await nl_el.is_visible(timeout=2000):
                                        await nl_el.click()
                                        phone_country_set = True
                                        print("Set phone country to Netherlands")
                                        break
                                except:
                                    continue
                        if phone_country_set:
                            break
                except:
                    continue

            await asyncio.sleep(1)

            # Fill phone number
            for selector in [
                "input[name='phone']",
                "input[type='tel']",
                "input[placeholder*='phone' i]",
                "input[placeholder*='Phone' i]",
                "input[id*='phone' i]",
                "[class*='phone'] input",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=3000):
                        print(f"Filling phone with selector: {selector}")
                        await el.triple_click()
                        await el.fill("")
                        await asyncio.sleep(0.3)
                        await el.fill(APPLICANT['phone'])
                        break
                except:
                    continue

            await asyncio.sleep(1)
            s = await screenshot(page, "05-personal-info-filled")
            screenshots.append(s)

            # Click Continue/Next for personal info
            for btn_selector in [
                "button[type='submit']",
                "button:has-text('Continue')",
                "button:has-text('Next')",
                "button:has-text('Save')",
            ]:
                try:
                    btn = page.locator(btn_selector).first
                    if await btn.is_visible(timeout=2000):
                        print(f"Clicking continue for personal info: {btn_selector}")
                        await btn.click()
                        break
                except:
                    continue

            await asyncio.sleep(3)
            s = await screenshot(page, "06-after-personal-info")
            screenshots.append(s)
            current_url = page.url
            print(f"URL after personal info: {current_url}")

            # Step 5: CV Upload
            print("Looking for CV upload...")
            cv_upload_done = False

            # Check if we're on a resume/CV upload step
            for file_selector in [
                "input[type='file']",
                "input[accept*='pdf']",
                "input[accept*='.pdf']",
            ]:
                try:
                    el = page.locator(file_selector).first
                    if await el.count() > 0:
                        print(f"Found file input: {file_selector}")
                        await el.set_input_files(RESUME_PDF)
                        cv_upload_done = True
                        print("CV uploaded")
                        await asyncio.sleep(3)
                        s = await screenshot(page, "07-cv-uploaded")
                        screenshots.append(s)
                        break
                except Exception as e:
                    print(f"File upload error: {e}")
                    continue

            if not cv_upload_done:
                # Look for upload button to trigger file input
                for btn_sel in [
                    "button:has-text('Upload')",
                    "button:has-text('Choose file')",
                    "button:has-text('Browse')",
                    "[class*='upload']",
                    "label[for*='resume']",
                    "label[for*='cv']",
                ]:
                    try:
                        el = page.locator(btn_sel).first
                        if await el.is_visible(timeout=2000):
                            # Set up file chooser handler
                            async with page.expect_file_chooser() as fc_info:
                                await el.click()
                            file_chooser = await fc_info.value
                            await file_chooser.set_files(RESUME_PDF)
                            cv_upload_done = True
                            print(f"CV uploaded via file chooser: {btn_sel}")
                            await asyncio.sleep(3)
                            s = await screenshot(page, "07-cv-uploaded")
                            screenshots.append(s)
                            break
                    except Exception as e:
                        print(f"File chooser error with {btn_sel}: {e}")
                        continue

            # Continue after CV upload
            for btn_selector in [
                "button[type='submit']",
                "button:has-text('Continue')",
                "button:has-text('Next')",
                "button:has-text('Upload')",
            ]:
                try:
                    btn = page.locator(btn_selector).first
                    if await btn.is_visible(timeout=2000):
                        btn_text = await btn.text_content()
                        if btn_text and "upload" not in btn_text.lower():
                            print(f"Clicking continue after CV: {btn_selector} '{btn_text}'")
                            await btn.click()
                            break
                except:
                    continue

            await asyncio.sleep(3)
            current_url = page.url
            print(f"URL after CV: {current_url}")
            s = await screenshot(page, "08-after-cv-step")
            screenshots.append(s)

            # Step 6: Cover Letter / Motivation
            page_content = await page.content()
            if "cover" in page_content.lower() or "motivation" in page_content.lower() or "letter" in page_content.lower():
                print("Found cover letter / motivation field")
                for selector in [
                    "textarea[name*='cover']",
                    "textarea[name*='motivation']",
                    "textarea[placeholder*='cover' i]",
                    "textarea[placeholder*='motivation' i]",
                    "textarea[placeholder*='letter' i]",
                    "textarea",
                ]:
                    try:
                        el = page.locator(selector).first
                        if await el.is_visible(timeout=2000):
                            print(f"Filling cover letter: {selector}")
                            await el.click()
                            await el.fill(COVER_LETTER)
                            await asyncio.sleep(1)
                            s = await screenshot(page, "09-cover-letter-filled")
                            screenshots.append(s)
                            break
                    except:
                        continue

                # Continue after cover letter
                for btn_selector in [
                    "button[type='submit']",
                    "button:has-text('Continue')",
                    "button:has-text('Next')",
                ]:
                    try:
                        btn = page.locator(btn_selector).first
                        if await btn.is_visible(timeout=2000):
                            await btn.click()
                            break
                    except:
                        continue

                await asyncio.sleep(3)
                current_url = page.url
                print(f"URL after cover letter: {current_url}")

            # Step 7: Look for final Submit button
            print("Looking for final submit...")
            s = await screenshot(page, "10-pre-submit")
            screenshots.append(s)

            # Check current page state
            page_text = await page.inner_text("body")
            print(f"Page content snippet: {page_text[:500]}")

            for btn_selector in [
                "button:has-text('Submit application')",
                "button:has-text('Submit')",
                "button:has-text('Send application')",
                "button:has-text('Apply')",
                "button[type='submit']",
                "input[type='submit']",
            ]:
                try:
                    btn = page.locator(btn_selector).first
                    if await btn.is_visible(timeout=2000):
                        btn_text = await btn.text_content()
                        print(f"Found submit button: '{btn_text}' with {btn_selector}")
                        await btn.click()
                        await asyncio.sleep(4)
                        break
                except:
                    continue

            s = await screenshot(page, "11-after-submit")
            screenshots.append(s)

            # Check for success
            final_url = page.url
            final_content = await page.inner_text("body")
            print(f"Final URL: {final_url}")
            print(f"Final content: {final_content[:500]}")

            if any(word in final_content.lower() for word in ["thank you", "thanks", "received", "submitted", "success", "application sent"]):
                status = "applied"
                notes = f"Application submitted successfully. Confirmation detected. Email used: {APPLICANT['email']}. Final URL: {final_url}"
                print("SUCCESS: Application submitted!")
            elif "personalInformation" in final_url:
                status = "skipped"
                notes = f"Stuck on personal information page. May need manual completion. Email: {APPLICANT['email']}. URL: {final_url}"
                print("WARNING: Still on personal information page")
            else:
                status = "applied"
                notes = f"Submit clicked. Final URL: {final_url}. Email used: {APPLICANT['email']}. Content: {final_content[:200]}"
                print(f"Submit clicked, final URL: {final_url}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            try:
                s = await screenshot(page, "error")
                screenshots.append(s)
            except:
                pass
            status = "failed"
            notes = f"Error: {str(e)}"

        finally:
            await browser.close()

    # Update applications.json
    app_entry = {
        "id": f"sendent-reapply-correct-email-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "Sendent B.V.",
        "role": "Medior Software Engineer (Backend/Integrations/.NET)",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9,
        "status": status,
        "resume_file": RESUME_PDF,
        "cover_letter_file": None,
        "screenshots": screenshots,
        "notes": notes,
        "email_used": APPLICANT['email'],
        "response": None,
    }

    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)

    apps.append(app_entry)

    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\nApplication entry saved to {APPLICATIONS_JSON}")
    print(f"Status: {status}")
    print(f"Notes: {notes}")
    print(f"Screenshots: {screenshots}")

    return status, screenshots

if __name__ == "__main__":
    asyncio.run(main())
