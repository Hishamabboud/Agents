#!/usr/bin/env python3
"""
Fortanix job application automation script via Playwright.
Uses --host-resolver-rules to bypass DNS resolution issues.
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

My experience includes building and maintaining industrial applications, developing REST APIs, working with cloud infrastructure (Azure, Kubernetes), and contributing to security-focused projects, including a GDPR data anonymization solution during my graduation project at Fontys ICT Cyber Security Research Group.

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
    try:
        await page.screenshot(path=path, full_page=True, timeout=20000)
        print(f"Screenshot saved: {path}")
    except Exception as e:
        print(f"Screenshot failed for {name}: {e}")
        # Try viewport-only screenshot
        try:
            await page.screenshot(path=path, timeout=10000)
            print(f"Viewport screenshot saved: {path}")
        except Exception as e2:
            print(f"Viewport screenshot also failed: {e2}")
            path = ""
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
    print(f"Application status updated to '{status}'")

async def try_fill_form(page):
    """Try to fill visible form fields."""
    filled = {}
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
                    print(f"  Filled '{sel}' -> '{value[:40]}'")
                    break
            except Exception:
                pass
    return filled

async def navigate_safe(page, url, label=""):
    """Navigate with fallback strategies."""
    print(f"Navigating to {url} ...")
    for wait_until in ["domcontentloaded", "commit"]:
        try:
            await page.goto(url, wait_until=wait_until, timeout=30000)
            print(f"  Loaded ({wait_until}). Title: {await page.title()}")
            return True
        except Exception as e:
            print(f"  Navigation attempt ({wait_until}) failed: {e}")
    return False

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
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-zygote",
                # Map workable.com domains to known IPs to bypass DNS
                "--host-resolver-rules=MAP apply.workable.com 104.16.148.37,"
                "MAP workablehr.s3.amazonaws.com 52.216.168.35,"
                "MAP workable-application-form.s3.amazonaws.com 52.216.168.35",
                "--ignore-certificate-errors",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = await context.new_page()
        last_shot = ""
        cl_saved = cl_path

        try:
            # Step 1: Load careers page
            print("\n=== Step 1: Load Fortanix careers page ===")
            ok = await navigate_safe(page, "https://apply.workable.com/fortanix/")
            await asyncio.sleep(4)
            last_shot = await take_screenshot(page, "01-careers-home")

            content = await page.content()
            page_title = await page.title()
            print(f"Page title: {page_title}")
            print(f"Content length: {len(content)}")
            print(f"Content preview: {content[:500]}")

            # Step 2: Find Software Engineer job links
            print("\n=== Step 2: Find Software Engineer job ===")
            await asyncio.sleep(2)

            job_link_el = None
            job_url = None

            # Try Workable job link pattern /j/JOBID/
            job_links = await page.query_selector_all("a[href*='/j/']")
            print(f"  Job links (/j/): {len(job_links)}")
            for link in job_links:
                href = await link.get_attribute("href") or ""
                text = await link.inner_text()
                print(f"    '{text.strip()[:60]}' -> {href}")
                if "software" in text.lower() or "engineer" in text.lower():
                    job_link_el = link
                    job_url = href
                    print(f"    -> SELECTED")
                    break

            if not job_link_el:
                # Try all links
                all_links = await page.query_selector_all("a")
                print(f"  Total links on page: {len(all_links)}")
                for link in all_links:
                    try:
                        href = await link.get_attribute("href") or ""
                        text = await link.inner_text()
                        if ("software" in text.lower() or "engineer" in text.lower()) and href:
                            print(f"  Candidate: '{text.strip()[:60]}' -> {href}")
                            job_link_el = link
                            job_url = href
                            break
                    except:
                        pass

            if not job_link_el:
                # Try navigating to a specific job URL - check Workable API first
                print("  No job link found via DOM. Trying Workable widget API...")
                try:
                    api_resp = await page.evaluate("""
                        async () => {
                            const r = await fetch('/api/v3/accounts/fortanix/jobs?details=true', {
                                headers: {'Accept': 'application/json'}
                            });
                            return { status: r.status, text: await r.text() };
                        }
                    """)
                    print(f"  API response: status={api_resp.get('status')}, text={str(api_resp.get('text',''))[:500]}")
                except Exception as e:
                    print(f"  API fetch failed: {e}")

            # Step 3: Navigate to job page
            print("\n=== Step 3: Navigate to job page ===")
            if job_url:
                if not job_url.startswith("http"):
                    job_url = f"https://apply.workable.com{job_url}"
                await navigate_safe(page, job_url)
                await asyncio.sleep(3)
                last_shot = await take_screenshot(page, "02-job-page")
                print(f"Job page: {page.url}")
            else:
                print("  No specific job URL found, continuing from current page.")
                last_shot = await take_screenshot(page, "02-no-job-found")

            # Step 4: Find and click Apply button
            print("\n=== Step 4: Find Apply button ===")
            apply_btn = None
            apply_selectors = [
                "a:has-text('Apply for this job')",
                "a:has-text('Apply now')",
                "button:has-text('Apply for this job')",
                "button:has-text('Apply now')",
                "button:has-text('Apply')",
                "a:has-text('Apply')",
                "[data-ui='apply-button']",
                ".apply-button",
                "a[href*='/apply']",
            ]
            for sel in apply_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        text = await el.inner_text()
                        print(f"  Found apply btn: '{text.strip()}' ({sel})")
                        apply_btn = el
                        break
                except:
                    pass

            if apply_btn:
                print("  Clicking Apply button...")
                await apply_btn.click()
                await asyncio.sleep(4)
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                except:
                    pass
                last_shot = await take_screenshot(page, "03-apply-form")
                print(f"  Apply form URL: {page.url}")
            else:
                print("  No Apply button found.")
                last_shot = await take_screenshot(page, "03-no-apply-btn")

            # Step 5: Fill form
            print("\n=== Step 5: Fill application form ===")
            await asyncio.sleep(2)
            filled = await try_fill_form(page)
            print(f"  Filled {len(filled)} fields.")
            if filled:
                last_shot = await take_screenshot(page, "04-form-filled")

            # Step 6: Upload resume
            print("\n=== Step 6: Upload resume ===")
            file_inputs = await page.query_selector_all("input[type='file']")
            print(f"  File inputs found: {len(file_inputs)}")
            resume_uploaded = False
            for fi in file_inputs:
                try:
                    if os.path.exists(RESUME_PDF):
                        await fi.set_input_files(RESUME_PDF)
                        print(f"  Resume uploaded: {RESUME_PDF}")
                        await asyncio.sleep(2)
                        last_shot = await take_screenshot(page, "05-resume-uploaded")
                        resume_uploaded = True
                        break
                except Exception as e:
                    print(f"  Upload error: {e}")

            # Step 7: Take pre-submit screenshot
            print("\n=== Step 7: Pre-submit state ===")
            pre_submit_shot = await take_screenshot(page, "06-pre-submit")
            if pre_submit_shot:
                last_shot = pre_submit_shot
            print(f"  Current URL: {page.url}")
            print(f"  Page title: {await page.title()}")

            # Step 8: Submit if form was filled
            print("\n=== Step 8: Submit application ===")
            submit_btn = None
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit application')",
                "button:has-text('Submit')",
                "button:has-text('Send')",
                "button:has-text('Apply')",
            ]
            for sel in submit_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        txt = await el.inner_text()
                        print(f"  Submit button: '{txt.strip()}' ({sel})")
                        submit_btn = el
                        break
                except:
                    pass

            if filled and submit_btn:
                print("  Submitting application...")
                await submit_btn.click()
                await asyncio.sleep(5)
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                except:
                    pass
                post_submit_shot = await take_screenshot(page, "07-post-submit")
                if post_submit_shot:
                    last_shot = post_submit_shot
                final_content = await page.content()
                final_url = page.url
                print(f"  Post-submit URL: {final_url}")

                if any(w in final_content.lower() for w in ["thank", "success", "submitted", "received"]):
                    await update_application("applied",
                        f"Application submitted successfully. Final URL: {final_url}",
                        last_shot, cl_saved)
                else:
                    await update_application("applied",
                        f"Submit clicked. Outcome unclear (no confirmation text). URL: {final_url}",
                        last_shot, cl_saved)

            elif not filled and not submit_btn:
                # Check what's on the page
                body_text = await page.evaluate("document.body ? document.body.innerText : ''")
                print(f"  Page text (first 500): {body_text[:500]}")
                notes = (f"Could not fill form or find submit button. "
                         f"The Workable careers page may require JS rendering beyond what loaded. "
                         f"URL: {page.url}, Title: {await page.title()}")
                await update_application("skipped", notes, last_shot, cl_saved)

            elif submit_btn and not filled:
                await update_application("skipped",
                    f"Found submit button but no form fields to fill. URL: {page.url}",
                    last_shot, cl_saved)
            else:
                await update_application("partial",
                    f"Filled {len(filled)} fields but no submit button found. URL: {page.url}",
                    last_shot, cl_saved)

        except Exception as e:
            print(f"\nUnhandled error: {e}")
            import traceback
            traceback.print_exc()
            try:
                err_shot = await take_screenshot(page, "error")
                if err_shot:
                    last_shot = err_shot
            except:
                pass
            await update_application("failed", f"Unhandled error: {str(e)}", last_shot, cl_saved)
        finally:
            await browser.close()
            print("\nBrowser closed.")

if __name__ == "__main__":
    asyncio.run(main())
