#!/usr/bin/env python3
"""
Apply to Sendent B.V. Medior Software Engineer (Backend/Integrations/.NET)
Job URL: https://join.com/companies/sendentcom/16136012-medior-software-engineer-backend-integrations-net
(redirects to 16212500 - same listing, refreshed)
"""

import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

JOB_URL = "https://join.com/companies/sendentcom/16136012-medior-software-engineer-backend-integrations-net"
CANDIDATE_EMAIL = "hiaham123@hotmail.com"
CANDIDATE_FIRST = "Hisham"
CANDIDATE_LAST = "Abboud"
CANDIDATE_PHONE = "+31648412838"
CANDIDATE_LINKEDIN = "https://linkedin.com/in/hisham-abboud"
CANDIDATE_GITHUB = "https://github.com/Hishamabboud"
CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/sendent-medior-dotnet.md"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def screenshot(page, label):
    path = f"{SCREENSHOTS_DIR}/sendent-16136012-{label}-{TIMESTAMP}.png"
    try:
        page.screenshot(path=path, full_page=True)
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Screenshot failed for {label}: {e}")
    return path

def click_continue(page):
    """Try various ways to click a continue/next/submit button."""
    for selector in [
        "button[type='submit']",
        "button:has-text('Continue')",
        "button:has-text('Next')",
        "button:has-text('Proceed')",
        "button:has-text('Apply')",
        "button:has-text('Confirm')",
        "button:has-text('Submit')",
        "input[type='submit']",
    ]:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"Clicked button: {selector}")
                time.sleep(3)
                return True
        except:
            pass
    return False

def run():
    screenshots = []
    status = "failed"
    notes = ""
    final_url = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--ignore-certificate-errors"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            accept_downloads=True
        )
        page = context.new_page()

        try:
            # === Step 1: Navigate to job listing ===
            print(f"\n--- Step 1: Navigating to job listing ---")
            page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            s = screenshot(page, "01-job-listing")
            screenshots.append(s)
            actual_url = page.url
            print(f"Loaded URL: {actual_url}")
            print(f"Title: {page.title()}")

            # Extract the actual apply URL from the current page
            apply_base = actual_url.rstrip("/").replace(
                actual_url.split("/")[-1],
                actual_url.split("/")[-1].split("-")[0]
            )
            # Extract job ID from URL
            # URL format: /companies/sendentcom/16212500-job-title
            url_parts = actual_url.rstrip("/").split("/")
            job_slug = url_parts[-1]
            job_id = job_slug.split("-")[0]
            company_slug = url_parts[-2]
            apply_url = f"https://join.com/companies/{company_slug}/{job_id}/apply"
            print(f"Apply URL: {apply_url}")

            # === Step 2: Click Apply button ===
            print(f"\n--- Step 2: Finding Apply button ---")
            apply_btn = None
            for selector in [
                f"a[href*='/{job_id}/apply']",
                "a[href*='/apply']",
                "button:has-text('Apply now')",
                "button:has-text('Apply')",
                "a:has-text('Apply now')",
                "a:has-text('Apply')",
                "[data-testid='apply-button']",
            ]:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=2000):
                        apply_btn = el
                        print(f"Found apply button: {selector}")
                        break
                except:
                    pass

            if apply_btn:
                apply_btn.click()
                time.sleep(3)
                print(f"URL after apply click: {page.url}")
            else:
                print("No apply button visible, navigating directly to apply URL")
                page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

            s = screenshot(page, "02-after-apply-click")
            screenshots.append(s)
            print(f"Current URL: {page.url}")

            # === Step 3: Handle authentication (email entry) ===
            print(f"\n--- Step 3: Authentication ---")
            email_input = None
            for selector in ["input[type='email']", "input[name='email']", "input[placeholder*='mail' i]", "#email"]:
                try:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=3000):
                        email_input = el
                        print(f"Found email input: {selector}")
                        break
                except:
                    pass

            if email_input:
                email_input.clear()
                email_input.fill(CANDIDATE_EMAIL)
                time.sleep(1)
                s = screenshot(page, "03-email-entered")
                screenshots.append(s)
                print(f"Email entered: {CANDIDATE_EMAIL}")

                clicked = click_continue(page)
                s = screenshot(page, "04-after-email-submit")
                screenshots.append(s)
                current_url = page.url
                print(f"URL after email submit: {current_url}")

                page_body = ""
                try:
                    page_body = page.inner_text("body")[:800]
                    print(f"Page body snippet: {page_body}")
                except:
                    pass

                notes = f"Email {CANDIDATE_EMAIL} submitted on join.com auth page. Redirected to: {current_url}. "

                if "authentication" in current_url or "verify" in current_url or "login" in current_url:
                    # Magic link flow
                    notes += "join.com requires magic link authentication (passwordless). Magic link sent to hiaham123@hotmail.com. "
                    notes += "ACTION REQUIRED: Check hiaham123@hotmail.com inbox for magic link email from join.com (subject: 'Your secure login link' or similar). Click the link to complete authentication and the application form will appear."
                    status = "pending_magic_link"
                elif "personalInformation" in current_url or "personal-information" in current_url:
                    print("Reached personal info step - filling form")
                    status = fill_personal_info(page, screenshots)
                    notes += f"Reached personal info form. Status: {status}"
                elif "upload" in current_url.lower() or "resume" in current_url.lower() or "cv" in current_url.lower():
                    print("Reached upload step")
                    status = fill_personal_info(page, screenshots)
                    notes += f"Reached upload step. Status: {status}"
                else:
                    # Check if form elements are present
                    page_content = page.content()
                    if "firstName" in page_content or "First name" in page_content or "first-name" in page_content:
                        print("Form detected on page - filling")
                        status = fill_personal_info(page, screenshots)
                        notes += f"Form present. Status: {status}"
                    else:
                        notes += f"Unknown state. Page snippet: {page_body[:200]}"
                        status = "failed"
            else:
                # No email input - check if we're already on a form or different state
                current_url = page.url
                page_content = page.content()
                print(f"No email input found. URL: {current_url}")

                if "firstName" in page_content or "First name" in page_content:
                    print("Form accessible without email auth")
                    status = fill_personal_info(page, screenshots)
                    notes = f"Form accessible directly. Status: {status}"
                else:
                    # Capture what we can
                    try:
                        body_text = page.inner_text("body")[:500]
                        notes = f"No email input and no form found. URL: {current_url}. Content: {body_text}"
                    except:
                        notes = f"No email input and no form found. URL: {current_url}"
                    status = "failed"

            final_url = page.url

        except Exception as e:
            print(f"Unhandled error: {e}")
            try:
                s = screenshot(page, "unhandled-error")
                screenshots.append(s)
            except:
                pass
            notes = f"Unhandled error: {str(e)[:300]}"
            status = "failed"
        finally:
            browser.close()

    return status, notes, screenshots, final_url


def fill_personal_info(page, screenshots):
    """Fill multi-step application form on join.com."""
    try:
        print("\n--- Filling application form ---")

        # === Upload CV ===
        for selector in ["input[type='file']", "input[name='resume']", "input[name='cv']", "input[accept*='pdf']"]:
            try:
                el = page.locator(selector).first
                if el.count() > 0:
                    el.set_input_files(CV_PATH)
                    print(f"CV uploaded via: {selector}")
                    time.sleep(2)
                    break
            except:
                pass

        # Also try clicking upload button and then setting file
        for upload_label in ["button:has-text('Upload')", "label:has-text('Upload')", "[data-testid='upload-resume']"]:
            try:
                with page.expect_file_chooser(timeout=3000) as fc_info:
                    page.locator(upload_label).first.click()
                file_chooser = fc_info.value
                file_chooser.set_files(CV_PATH)
                print(f"CV uploaded via file chooser: {upload_label}")
                time.sleep(2)
                break
            except:
                pass

        time.sleep(2)
        s = screenshot(page, "05-cv-upload-attempted")
        screenshots.append(s)

        # Continue past upload if needed
        click_continue(page)
        s = screenshot(page, "06-after-cv-continue")
        screenshots.append(s)
        print(f"URL: {page.url}")

        # === Fill personal info fields ===
        time.sleep(2)

        # First name
        for sel in ["input[name='firstName']", "input[name='first_name']", "input[placeholder*='First' i]", "#firstName"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.clear(); el.fill(CANDIDATE_FIRST)
                    print(f"First name filled")
                    break
            except:
                pass

        # Last name
        for sel in ["input[name='lastName']", "input[name='last_name']", "input[placeholder*='Last' i]", "#lastName"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.clear(); el.fill(CANDIDATE_LAST)
                    print(f"Last name filled")
                    break
            except:
                pass

        # Phone
        for sel in ["input[name='phone']", "input[type='tel']", "input[placeholder*='phone' i]", "#phone"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.clear(); el.fill(CANDIDATE_PHONE)
                    print(f"Phone filled")
                    break
            except:
                pass

        # Country - Netherlands
        for sel in ["select[name='country']", "select[name='countryCode']", "#country"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.select_option(label="Netherlands")
                    print("Country set to Netherlands")
                    break
            except:
                pass

        time.sleep(1)
        s = screenshot(page, "07-personal-info-filled")
        screenshots.append(s)

        click_continue(page)
        s = screenshot(page, "08-after-personal-info")
        screenshots.append(s)
        print(f"URL: {page.url}")
        time.sleep(2)

        # === Professional links ===
        for sel in ["input[name='linkedIn']", "input[name='linkedin']", "input[placeholder*='linkedin' i]", "input[placeholder*='LinkedIn' i]"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.clear(); el.fill(CANDIDATE_LINKEDIN)
                    print("LinkedIn filled")
                    break
            except:
                pass

        for sel in ["input[name='github']", "input[name='GitHub']", "input[placeholder*='github' i]", "input[placeholder*='GitHub' i]"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.clear(); el.fill(CANDIDATE_GITHUB)
                    print("GitHub filled")
                    break
            except:
                pass

        time.sleep(1)
        s = screenshot(page, "09-professional-links-filled")
        screenshots.append(s)

        click_continue(page)
        s = screenshot(page, "10-after-links")
        screenshots.append(s)
        print(f"URL: {page.url}")
        time.sleep(2)

        # === Upload cover letter ===
        for selector in ["input[type='file']", "input[name='coverLetter']", "input[accept*='pdf']"]:
            try:
                inputs = page.locator(selector).all()
                for inp in inputs:
                    if inp.is_visible(timeout=1000):
                        inp.set_input_files(COVER_LETTER_PATH)
                        print(f"Cover letter uploaded")
                        time.sleep(2)
                        break
            except:
                pass

        # Try cover letter text area
        for sel in ["textarea[name='coverLetter']", "textarea[name='cover_letter']", "textarea[placeholder*='cover' i]", "textarea[placeholder*='motivation' i]"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    with open(COVER_LETTER_PATH) as f:
                        cover_text = f.read()
                    el.fill(cover_text)
                    print("Cover letter text entered in textarea")
                    time.sleep(1)
                    break
            except:
                pass

        time.sleep(1)
        s = screenshot(page, "11-cover-letter-step")
        screenshots.append(s)

        click_continue(page)
        s = screenshot(page, "12-after-cover-letter")
        screenshots.append(s)
        print(f"URL: {page.url}")
        time.sleep(2)

        # === Screening questions ===
        # Q: When can you start?
        for sel in ["input[name='startDate']", "input[placeholder*='start' i]", "input[placeholder*='date' i]"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.fill("2026-03-01")
                    print("Start date filled")
                    break
            except:
                pass

        # Q: Work permit - Yes
        for sel in ["input[value='true'][name*='permit']", "input[value='Yes'][name*='permit']", "label:has-text('Yes')"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    print("Work permit: Yes clicked")
                    break
            except:
                pass

        # Q: Need visa sponsorship - No
        for sel in ["input[value='false'][name*='visa']", "input[value='No'][name*='visa']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    print("Visa sponsorship: No clicked")
                    break
            except:
                pass

        time.sleep(1)
        s = screenshot(page, "13-screening-questions")
        screenshots.append(s)

        click_continue(page)
        s = screenshot(page, "14-after-screening")
        screenshots.append(s)
        print(f"URL: {page.url}")
        time.sleep(2)

        # === Review and Submit ===
        s = screenshot(page, "15-review-page")
        screenshots.append(s)
        print(f"URL before submit: {page.url}")

        # Final submit
        submitted = False
        for selector in [
            "button:has-text('Confirm & apply')",
            "button:has-text('Submit application')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Confirm')",
            "button[type='submit']",
        ]:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=3000):
                    btn.click()
                    print(f"Clicked final submit: {selector}")
                    time.sleep(5)
                    submitted = True
                    break
            except:
                pass

        s = screenshot(page, "16-after-submit")
        screenshots.append(s)
        print(f"Final URL: {page.url}")

        if submitted:
            return "applied"
        else:
            return "partial"

    except Exception as e:
        print(f"Form fill error: {e}")
        try:
            s = screenshot(page, "form-error")
            screenshots.append(s)
        except:
            pass
        return "failed"


if __name__ == "__main__":
    print("=" * 60)
    print("Sendent B.V. Application - Job ID 16136012 (new listing)")
    print(f"Timestamp: {TIMESTAMP}")
    print("=" * 60)

    status, notes, screenshots, final_url = run()

    print(f"\n{'=' * 60}")
    print(f"Status: {status}")
    print(f"Final URL: {final_url}")
    print(f"Notes: {notes}")
    print(f"Screenshots ({len(screenshots)}):")
    for s in screenshots:
        print(f"  {s}")

    # Remove the failed test entry and log new one
    apps_file = "/home/user/Agents/data/applications.json"
    with open(apps_file) as f:
        apps = json.load(f)

    # Remove the dummy failed entry from the test run if present
    apps = [a for a in apps if a.get("id") != f"sendent-16136012-20260604_074429"]

    entry = {
        "id": f"sendent-16136012-{TIMESTAMP}",
        "company": "Sendent B.V.",
        "role": "Medior Software Engineer (Backend/Integrations/.NET)",
        "url": JOB_URL,
        "date_applied": datetime.now().strftime("%Y-%m-%d"),
        "score": 9.2,
        "status": status,
        "resume_file": CV_PATH,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshots": screenshots,
        "notes": notes,
        "final_url": final_url,
        "response": "awaiting"
    }

    apps.append(entry)

    with open(apps_file, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\nLogged to {apps_file}")
    print(f"Entry ID: {entry['id']}")
