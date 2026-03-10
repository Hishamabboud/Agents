#!/usr/bin/env python3
"""
Fortanix job application automation script via Playwright.
"""

import asyncio
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
RESUME_PDF = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

APPLICANT = {
    "name": "Hisham Abboud",
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "location": "Eindhoven, Netherlands",
}

COVER_LETTER = """Dear Hiring Team at Fortanix,

I am writing to express my enthusiasm for the Software Engineer position at Fortanix. As a Software Service Engineer at Actemium (VINCI Energies) with a background in full-stack development using .NET, C#, Python, and JavaScript, I am excited by the opportunity to contribute to Fortanix's mission of securing data in the cloud and beyond.

My experience includes building and maintaining industrial applications, developing REST APIs, working with cloud infrastructure (Azure, Kubernetes), and contributing to security-focused projects — including a GDPR data anonymization solution during my graduation project at Fontys ICT Cyber Security Research Group.

Fortanix's work on confidential computing and data security aligns strongly with my professional interests and background. I am based in Eindhoven and would welcome the chance to join the team at High Tech Campus.

Thank you for your consideration. I look forward to the opportunity to discuss how I can contribute.

Best regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
"""

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def take_screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"fortanix-{name}-{ts()}.png")
    await page.screenshot(path=path, full_page=True)
    print(f"Screenshot saved: {path}")
    return path

async def update_application(status, notes, screenshot_path="", cover_letter_file=""):
    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)
    for app in apps:
        if app.get("company", "").lower() == "fortanix":
            app["status"] = status
            app["date_applied"] = datetime.now().strftime("%Y-%m-%d")
            app["notes"] = notes
            if screenshot_path:
                app["screenshot"] = screenshot_path
            if cover_letter_file:
                app["cover_letter_file"] = cover_letter_file
            app["resume_file"] = "profile/Hisham Abboud CV.pdf"
            break
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    print(f"Application status updated: {status}")

async def try_fill_form(page):
    """Try to fill any visible form fields."""
    filled = {}

    # Map of field selectors to values
    field_map = [
        (["input[name='firstname']", "input[name='first_name']", "input[id*='firstname']",
          "input[placeholder*='irst name']", "input[autocomplete='given-name']"],
         APPLICANT["first_name"]),
        (["input[name='lastname']", "input[name='last_name']", "input[id*='lastname']",
          "input[placeholder*='ast name']", "input[autocomplete='family-name']"],
         APPLICANT["last_name"]),
        (["input[name='email']", "input[type='email']", "input[id*='email']",
          "input[placeholder*='mail']", "input[autocomplete='email']"],
         APPLICANT["email"]),
        (["input[name='phone']", "input[type='tel']", "input[id*='phone']",
          "input[placeholder*='hone']", "input[autocomplete='tel']"],
         APPLICANT["phone"]),
        (["textarea[name='cover_letter']", "textarea[name='coverLetter']",
          "textarea[id*='cover']", "textarea[placeholder*='over letter']"],
         COVER_LETTER),
    ]

    for selectors, value in field_map:
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.fill(value)
                    filled[sel] = value[:40]
                    print(f"Filled '{sel}' -> '{value[:40]}'")
                    break
            except Exception as e:
                pass

    return filled

async def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    # Save cover letter
    cl_path = "/home/user/Agents/output/cover-letters/fortanix-software-engineer.md"
    os.makedirs(os.path.dirname(cl_path), exist_ok=True)
    with open(cl_path, "w") as f:
        f.write(COVER_LETTER)
    print(f"Cover letter saved: {cl_path}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                  "--disable-setuid-sandbox", "--no-zygote"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        last_shot = ""

        try:
            print("Step 1: Navigating to Fortanix Workable careers page...")
            try:
                await page.goto("https://apply.workable.com/fortanix/",
                                wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                print(f"Initial navigation timeout/error: {e}")
                # Continue anyway - page may have partially loaded
            await asyncio.sleep(4)

            last_shot = await take_screenshot(page, "01-careers-home")
            page_title = await page.title()
            current_url = page.url
            print(f"Title: {page_title}, URL: {current_url}")

            # Check for blocking
            content = await page.content()
            if "captcha" in content.lower() and "workable" not in page_title.lower():
                print("CAPTCHA detected.")
                await update_application("failed", "CAPTCHA block on Workable careers page", last_shot, cl_path)
                await browser.close()
                return

            # Look for job listings on the page
            print("Step 2: Looking for Software Engineer vacancies...")
            await asyncio.sleep(2)

            # Workable job cards typically have specific selectors
            job_link = None
            job_selectors_to_try = [
                "a[href*='/j/']",          # Workable job link pattern
                "[data-ui='job'] a",
                "li a[href*='software']",
                "li a[href*='engineer']",
                "a:has-text('Software Engineer')",
                "a:has-text('engineer')",
                "a:has-text('software')",
            ]

            for sel in job_selectors_to_try:
                try:
                    els = await page.query_selector_all(sel)
                    if els:
                        for el in els:
                            text = await el.inner_text()
                            href = await el.get_attribute("href") or ""
                            print(f"  Found link: '{text.strip()[:80]}' -> {href[:80]}")
                            if "software" in text.lower() or "engineer" in text.lower():
                                job_link = el
                                print(f"  -> Selected this job link")
                                break
                        if job_link:
                            break
                except Exception as e:
                    pass

            if not job_link:
                # Try to list all links on page
                print("No direct job link found. Listing all links...")
                all_links = await page.query_selector_all("a[href]")
                for link in all_links[:30]:
                    try:
                        href = await link.get_attribute("href") or ""
                        text = await link.inner_text()
                        print(f"  Link: '{text.strip()[:60]}' -> {href[:80]}")
                    except:
                        pass

            if job_link:
                print("Step 3: Clicking on Software Engineer job...")
                await job_link.click()
                await asyncio.sleep(3)
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                except:
                    pass
                last_shot = await take_screenshot(page, "02-job-detail")
                print(f"Job page URL: {page.url}")
            else:
                # Navigate directly to the job URL path
                print("Step 3: Trying direct job URL navigation...")
                try:
                    await page.goto("https://apply.workable.com/fortanix/j/software-engineer/",
                                    wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(3)
                    last_shot = await take_screenshot(page, "02-direct-job-url")
                    print(f"Direct URL page title: {await page.title()}")
                except Exception as e:
                    print(f"Direct URL failed: {e}")

            # Step 4: Look for Apply button
            print("Step 4: Looking for Apply button...")
            apply_btn = None
            apply_btn_selectors = [
                "a:has-text('Apply for this job')",
                "button:has-text('Apply')",
                "a:has-text('Apply now')",
                "a:has-text('Apply')",
                "[data-ui='apply-button']",
                "a[href*='apply']",
                ".apply-button",
                "#apply-button",
            ]
            for sel in apply_btn_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        text = await el.inner_text()
                        print(f"Found apply button: '{text.strip()}' with selector {sel}")
                        apply_btn = el
                        break
                except:
                    pass

            if apply_btn:
                print("Step 5: Clicking Apply button...")
                await apply_btn.click()
                await asyncio.sleep(4)
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                except:
                    pass
                last_shot = await take_screenshot(page, "03-application-form")
                print(f"Application form URL: {page.url}")
            else:
                print("No Apply button found yet, taking screenshot of current state...")
                last_shot = await take_screenshot(page, "03-no-apply-btn")

                # Look for any form on the current page
                forms = await page.query_selector_all("form")
                print(f"Forms found on current page: {len(forms)}")

            # Step 6: Fill in the application form
            print("Step 6: Filling in application form...")
            await asyncio.sleep(2)
            filled = await try_fill_form(page)

            if filled:
                last_shot = await take_screenshot(page, "04-form-filled")
                print(f"Filled {len(filled)} fields.")
            else:
                print("No form fields found to fill.")
                last_shot = await take_screenshot(page, "04-no-form-fields")

            # Step 7: Upload resume
            print("Step 7: Attempting resume upload...")
            file_inputs = await page.query_selector_all("input[type='file']")
            print(f"File inputs found: {len(file_inputs)}")
            resume_uploaded = False
            for fi in file_inputs:
                try:
                    if os.path.exists(RESUME_PDF):
                        await fi.set_input_files(RESUME_PDF)
                        print(f"Resume uploaded: {RESUME_PDF}")
                        await asyncio.sleep(2)
                        last_shot = await take_screenshot(page, "05-resume-uploaded")
                        resume_uploaded = True
                        break
                except Exception as e:
                    print(f"File upload error: {e}")

            if not resume_uploaded:
                print("Could not upload resume (no file input or upload error).")

            # Step 8: Take pre-submit screenshot
            pre_submit_shot = await take_screenshot(page, "06-pre-submit")
            last_shot = pre_submit_shot

            # Step 9: Check page content and determine status
            final_content = await page.content()
            final_title = await page.title()
            final_url = page.url
            print(f"Final state - Title: {final_title}, URL: {final_url}")

            # Look for submit button (but do NOT click unless form is properly filled)
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Send application')",
                "button:has-text('Apply')",
            ]
            submit_btn = None
            for sel in submit_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        text = await el.inner_text()
                        print(f"Submit button found: '{text.strip()}' with selector {sel}")
                        submit_btn = el
                        break
                except:
                    pass

            if filled and submit_btn:
                print("Step 8: Submitting application...")
                await submit_btn.click()
                await asyncio.sleep(5)
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                except:
                    pass
                final_content = await page.content()
                last_shot = await take_screenshot(page, "07-post-submit")
                print(f"Post-submit URL: {page.url}")

                if any(word in final_content.lower() for word in ["thank", "success", "submitted", "received", "application"]):
                    await update_application("applied",
                        f"Application submitted. Final URL: {page.url}",
                        last_shot, cl_path)
                else:
                    await update_application("applied",
                        f"Submit clicked, outcome unclear. Final URL: {page.url}",
                        last_shot, cl_path)
            elif not filled and not submit_btn:
                # Could not find form or button - the page may be JS-rendered and blocked
                notes = (f"Could not find application form fields or submit button. "
                         f"Page: '{final_title}', URL: {final_url}. "
                         f"The page likely requires JavaScript rendering or manual login.")
                await update_application("skipped", notes, last_shot, cl_path)
            elif submit_btn and not filled:
                notes = (f"Found submit button but could not fill form fields. "
                         f"URL: {final_url}")
                await update_application("skipped", notes, last_shot, cl_path)
            else:
                notes = (f"Form fields filled ({len(filled)}) but no submit button found. "
                         f"URL: {final_url}")
                await update_application("partial", notes, last_shot, cl_path)

        except Exception as e:
            print(f"Unhandled error: {e}")
            import traceback
            traceback.print_exc()
            try:
                err_shot = await take_screenshot(page, "error")
                last_shot = err_shot
            except:
                pass
            await update_application("failed", f"Error: {str(e)}", last_shot, cl_path)
        finally:
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
