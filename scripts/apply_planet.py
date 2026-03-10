#!/usr/bin/env python3
"""
Automated application for Planet - Software Engineer, Integration Platform
Job URL: https://boards.greenhouse.io/planetlabs/jobs/5034494
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

JOB_URL = "https://boards.greenhouse.io/planetlabs/jobs/5034494"
RESUME_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/planet-software-engineer.md"
SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
APPLICATIONS_JSON = Path("/home/user/Agents/data/applications.json")

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "city": "Eindhoven",
    "country": "Netherlands",
}

COVER_LETTER_TEXT = open(COVER_LETTER_PATH).read()

SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def load_applications():
    if APPLICATIONS_JSON.exists():
        with open(APPLICATIONS_JSON) as f:
            return json.load(f)
    return []

def save_application(app_data):
    apps = load_applications()
    apps.append(app_data)
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    log(f"Application logged to {APPLICATIONS_JSON}")

async def screenshot(page, name):
    path = str(SCREENSHOTS_DIR / f"planet-{name}-{ts()}.png")
    await page.screenshot(path=path, full_page=True)
    log(f"Screenshot saved: {path}")
    return path

async def try_fill(page, selector, value, label="field"):
    try:
        el = page.locator(selector).first
        await el.wait_for(state="visible", timeout=5000)
        await el.fill(value)
        log(f"Filled {label}: {value[:40] if value else ''}")
        return True
    except Exception as e:
        log(f"Could not fill {label} ({selector}): {e}")
        return False

async def run():
    application_data = {
        "id": f"planet-software-engineer-{ts()}",
        "company": "Planet",
        "role": "Software Engineer, Integration Platform",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 8,
        "status": "failed",
        "resume_file": RESUME_PATH,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshot": None,
        "notes": "",
        "response": None,
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        try:
            log(f"Navigating to {JOB_URL}")
            response = await page.goto(JOB_URL, wait_until="networkidle", timeout=30000)
            log(f"Page loaded, status: {response.status if response else 'unknown'}")

            # Handle redirect
            current_url = page.url
            log(f"Current URL: {current_url}")

            await screenshot(page, "01-job-page")

            # Read job description
            page_text = await page.inner_text("body")
            log(f"Page text length: {len(page_text)} chars")
            if "Software Engineer" in page_text or "Integration" in page_text:
                log("Found job description content.")
            else:
                log("Warning: job content may not be visible - page may have redirected to listing.")

            # Save job description snippet
            job_snippet = page_text[:500]
            log(f"Page snippet: {job_snippet}")

            # Look for the Apply button or form
            apply_button = page.get_by_role("link", name=re.compile(r"apply", re.IGNORECASE))
            apply_count = await apply_button.count()
            log(f"Apply buttons found: {apply_count}")

            if apply_count > 0:
                log("Clicking Apply button...")
                await apply_button.first.click()
                await page.wait_for_load_state("networkidle", timeout=15000)
                await screenshot(page, "02-apply-clicked")

            # Wait for form to appear
            await page.wait_for_timeout(2000)
            current_url = page.url
            log(f"URL after apply click: {current_url}")

            # Fill in the form fields
            # Greenhouse standard form fields
            field_map = [
                ("input#first_name, input[name='job_application[first_name]'], input[placeholder*='First']", CANDIDATE["first_name"], "First Name"),
                ("input#last_name, input[name='job_application[last_name]'], input[placeholder*='Last']", CANDIDATE["last_name"], "Last Name"),
                ("input#email, input[name='job_application[email]'], input[type='email']", CANDIDATE["email"], "Email"),
                ("input#phone, input[name='job_application[phone]'], input[type='tel']", CANDIDATE["phone"], "Phone"),
            ]

            for selector, value, label in field_map:
                await try_fill(page, selector, value, label)

            await page.wait_for_timeout(500)

            # Location / city field
            await try_fill(page, "input#job_application_location, input[name*='location'], input[placeholder*='ity'], input[placeholder*='ocation']", CANDIDATE["city"], "Location")

            # LinkedIn URL
            await try_fill(page, "input[id*='linkedin'], input[name*='linkedin'], input[placeholder*='LinkedIn'], input[placeholder*='linkedin']", CANDIDATE["linkedin"], "LinkedIn")

            # GitHub URL
            await try_fill(page, "input[id*='github'], input[name*='github'], input[placeholder*='GitHub'], input[placeholder*='github']", CANDIDATE["github"], "GitHub")

            # Website / Portfolio
            await try_fill(page, "input[id*='website'], input[name*='website'], input[placeholder*='Website'], input[placeholder*='website'], input[id*='portfolio']", "https://github.com/Hishamabboud", "Website")

            await page.wait_for_timeout(500)

            # Cover letter textarea
            cl_selectors = [
                "textarea[id*='cover'], textarea[name*='cover']",
                "textarea[placeholder*='cover'], textarea[placeholder*='Cover']",
                "textarea#job_application_cover_letter_text",
                "div[contenteditable='true']",
            ]
            cl_filled = False
            for sel in cl_selectors:
                try:
                    el = page.locator(sel).first
                    count = await el.count()
                    if count > 0:
                        await el.wait_for(state="visible", timeout=3000)
                        await el.fill(COVER_LETTER_TEXT)
                        log(f"Filled cover letter via {sel}")
                        cl_filled = True
                        break
                except Exception:
                    pass
            if not cl_filled:
                log("Could not find cover letter textarea.")

            # Resume upload
            resume_input = page.locator("input[type='file']").first
            resume_count = await resume_input.count()
            if resume_count > 0:
                log(f"Uploading resume: {RESUME_PATH}")
                await resume_input.set_input_files(RESUME_PATH)
                await page.wait_for_timeout(2000)
                log("Resume uploaded.")
            else:
                log("No file input found for resume upload.")

            await page.wait_for_timeout(1000)
            await screenshot(page, "03-form-filled")

            # Handle dropdowns / select fields (e.g., country)
            # Try to select Netherlands in any country dropdown
            country_dropdowns = page.locator("select[id*='country'], select[name*='country']")
            dd_count = await country_dropdowns.count()
            if dd_count > 0:
                try:
                    await country_dropdowns.first.select_option(label="Netherlands")
                    log("Selected Netherlands in country dropdown.")
                except Exception as e:
                    log(f"Could not set country: {e}")

            # Handle any required checkboxes (consent, privacy policy)
            checkboxes = page.locator("input[type='checkbox']")
            cb_count = await checkboxes.count()
            log(f"Found {cb_count} checkboxes.")
            for i in range(cb_count):
                cb = checkboxes.nth(i)
                try:
                    is_checked = await cb.is_checked()
                    if not is_checked:
                        label_for = await cb.get_attribute("id")
                        # Only auto-check if it looks like consent/privacy
                        nearby_text = ""
                        try:
                            nearby_text = await page.locator(f"label[for='{label_for}']").inner_text(timeout=1000)
                        except Exception:
                            pass
                        log(f"Checkbox {i}: label='{nearby_text[:60]}', checked={is_checked}")
                        if any(word in nearby_text.lower() for word in ["privacy", "consent", "agree", "terms", "gdpr", "policy"]):
                            await cb.check()
                            log(f"Checked privacy/consent checkbox {i}.")
                except Exception as e:
                    log(f"Checkbox {i} error: {e}")

            await page.wait_for_timeout(500)
            await screenshot(page, "04-before-submit")

            # Find and click submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
                "button:has-text('Send')",
            ]
            submitted = False
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    btn_count = await btn.count()
                    if btn_count > 0:
                        btn_text = await btn.inner_text(timeout=1000)
                        log(f"Found submit button: '{btn_text}' via {sel}")
                        await btn.click()
                        await page.wait_for_load_state("networkidle", timeout=15000)
                        log("Submit clicked, waiting for confirmation...")
                        await page.wait_for_timeout(3000)
                        submitted = True
                        break
                except Exception as e:
                    log(f"Submit selector {sel} failed: {e}")

            final_url = page.url
            page_text_after = await page.inner_text("body")
            final_screenshot = await screenshot(page, "05-after-submit")
            application_data["screenshot"] = final_screenshot

            # Determine outcome
            success_keywords = ["thank", "application received", "submitted", "confirmation", "we'll be in touch", "success"]
            is_success = any(kw in page_text_after.lower() for kw in success_keywords)

            if is_success:
                application_data["status"] = "applied"
                application_data["notes"] = f"Application submitted successfully. Final URL: {final_url}"
                log("Application submitted successfully!")
            elif submitted:
                application_data["status"] = "applied"
                application_data["notes"] = f"Submit button clicked. Final URL: {final_url}. Confirmation text not detected but form was submitted."
                log("Submit button clicked - outcome uncertain, marked as applied.")
            else:
                application_data["status"] = "failed"
                application_data["notes"] = f"Could not find or click submit button. Final URL: {final_url}"
                log("Failed to submit application.")

        except PlaywrightTimeoutError as e:
            log(f"Timeout error: {e}")
            application_data["status"] = "failed"
            application_data["notes"] = f"Timeout: {str(e)[:200]}"
            try:
                err_screenshot = await screenshot(page, "error")
                application_data["screenshot"] = err_screenshot
            except Exception:
                pass
        except Exception as e:
            log(f"Unexpected error: {e}")
            application_data["status"] = "failed"
            application_data["notes"] = f"Error: {str(e)[:200]}"
            try:
                err_screenshot = await screenshot(page, "error")
                application_data["screenshot"] = err_screenshot
            except Exception:
                pass
        finally:
            await browser.close()

    save_application(application_data)
    return application_data

if __name__ == "__main__":
    result = asyncio.run(run())
    print("\n=== APPLICATION RESULT ===")
    print(json.dumps(result, indent=2))
