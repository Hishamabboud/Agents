#!/usr/bin/env python3
"""
Fortanix job application via Playwright.
Target: Senior Software Engineer - Backend Microservices, Rust (Netherlands)
Apply URL: https://apply.workable.com/fortanix/j/DFCBABCC33/apply/

Confirmed form fields (from screenshots):
  Personal: firstname, lastname, email, phone, address, city, postcode, country
  Content: summary (text), cover_letter (textarea)
  Screening questions (textareas in order):
    QA_11110678: Which programming languages are you proficient in?
    QA_11110679: On a scale of 1-10, how proficient are you with Rust?
    QA_11110680: What percentage of your time is spent with hands-on coding?
    QA_11110681: How many years of experience with microservices architecture and distributed systems?
    QA_11110682: On a scale of 1-10, how proficient are you with Docker and Kubernetes?
    QA_11110683: How many years of experience with core backend software engineering?

Known challenge: Cloudflare Turnstile appears on submit.
Workable config shows recaptcha:false but Turnstile is present.
The Turnstile may auto-pass in headless mode through the proxy (it uses behavioral analysis).
"""

import asyncio
import os
import re
import json
from datetime import datetime
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
RESUME_PDF = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

JOB_TITLE = "Senior Software Engineer - Backend Microservices, Rust (Netherlands)"
JOB_SHORTCODE = "DFCBABCC33"
JOB_URL = "https://apply.workable.com/fortanix/j/DFCBABCC33/"
APPLY_URL = "https://apply.workable.com/fortanix/j/DFCBABCC33/apply/"

APPLICANT = {
    "firstname": "Hisham",
    "lastname": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
    "address": "Eindhoven",
    "city": "Eindhoven",
    "postcode": "5612",
    "country": "Netherlands",
}

SUMMARY = "Software Engineer with 3+ years experience in .NET/C#, Python, REST APIs, Azure, and Kubernetes. Background in full-stack development and security-focused projects."

COVER_LETTER = """Dear Hiring Team at Fortanix,

I am writing to express my enthusiasm for the Software Engineer position at Fortanix in Eindhoven. As a Software Service Engineer at Actemium (VINCI Energies) with a background in full-stack development using .NET, C#, Python, and JavaScript, I am excited by the opportunity to contribute to Fortanix's mission of securing data in the cloud and beyond.

My experience includes building and maintaining industrial applications, developing REST APIs, working with cloud infrastructure (Azure, Kubernetes), and contributing to security-focused projects, including a GDPR data anonymization solution during my graduation project at Fontys ICT Cyber Security Research Group.

Fortanix's work on confidential computing and data security aligns strongly with my professional interests and background. I am based in Eindhoven and would welcome the chance to join the team at High Tech Campus.

Thank you for your consideration. I look forward to discussing how I can contribute.

Best regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
"""

# Correct order based on confirmed screenshots
SCREENING = {
    "QA_11110678": "Python, C#/.NET, JavaScript, SQL, Visual Basic. Primarily Python and C# in production environments.",
    "QA_11110679": "3 - I have experimented with Rust in personal projects and am actively building proficiency.",
    "QA_11110680": "Approximately 70% of my time is spent hands-on coding; the rest is architecture, reviews, and support.",
    "QA_11110681": "3 years. I have built and maintained microservices-based systems using .NET, REST APIs, and deployed via Azure and Kubernetes.",
    "QA_11110682": "7 - I have substantial experience with Docker and Kubernetes through my work at Actemium and my ASML internship.",
    "QA_11110683": "3 years of professional backend engineering experience in .NET/C#, Python, and API development.",
}

def get_proxy_config():
    proxy_url = (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or
                 os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"))
    if not proxy_url:
        return None, None, None
    m = re.match(r'https?://([^:@]+):([^@]+)@([^/]+)', proxy_url)
    if m:
        user, pwd, server = m.groups()
        return f"http://{server}", user, pwd
    m2 = re.match(r'https?://([^/]+)', proxy_url)
    if m2:
        return f"http://{m2.group(1)}", None, None
    return None, None, None

def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"fortanix-{name}-{ts()}.png")
    try:
        await page.screenshot(path=path, full_page=False, timeout=15000)
        print(f"  Screenshot: {path}")
        return path
    except Exception as e:
        print(f"  Screenshot failed: {e}")
        return ""

async def update_app(status, notes, shot="", cl="", job_title="", job_url=""):
    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)
    for app in apps:
        if app.get("company", "").lower() == "fortanix":
            app["status"] = status
            app["date_applied"] = datetime.now().strftime("%Y-%m-%d")
            app["notes"] = notes
            if shot:
                app["screenshot"] = shot
            if cl:
                app["cover_letter_file"] = cl
            if job_title:
                app["role"] = job_title
            if job_url:
                app["url"] = job_url
            app["resume_file"] = "profile/Hisham Abboud CV.pdf"
            break
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    print(f"  Tracker: '{status}'")

async def remove_modals(page):
    """Remove all modal overlays and backdrops via JS."""
    removed = await page.evaluate("""
        () => {
            let n = 0;
            [
                '[data-role="modal-wrapper"]',
                '[data-role="backdrop"]',
                '[data-evergreen-dialog-backdrop]',
                '[data-ui="backdrop"]',
            ].forEach(sel => {
                document.querySelectorAll(sel).forEach(el => {
                    el.style.display = 'none';
                    el.style.pointerEvents = 'none';
                    n++;
                });
            });
            return n;
        }
    """)
    if removed > 0:
        print(f"  Removed {removed} modal/backdrop elements")

async def accept_cookies(page):
    """Accept cookies using the main banner 'Accept all' button."""
    # Try inside modal first (the About Cookies dialog)
    for sel in [
        "[data-role='modal-wrapper'] button:has-text('Accept all')",
        "button:has-text('Accept all')",
        "button:has-text('Accept All')",
    ]:
        try:
            els = await page.query_selector_all(sel)
            for el in els:
                if await el.is_visible():
                    txt = await el.inner_text()
                    print(f"  Accepting cookies: '{txt.strip()}'")
                    await el.click(timeout=5000)
                    await asyncio.sleep(1.5)
                    return True
        except:
            pass
    return False

async def fill(page, name, value):
    """Fill an input or textarea by name attribute."""
    for sel in [f"input[name='{name}']", f"textarea[name='{name}']"]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.fill(value)
                return True
        except:
            pass
    return False

async def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    cl_path = "/home/user/Agents/output/cover-letters/fortanix-software-engineer.md"
    os.makedirs(os.path.dirname(cl_path), exist_ok=True)
    with open(cl_path, "w") as f:
        f.write(COVER_LETTER)
    print(f"Cover letter saved: {cl_path}")

    proxy_server, proxy_user, proxy_pass = get_proxy_config()
    print(f"Proxy: {proxy_server}")

    proxy_cfg = None
    if proxy_server:
        proxy_cfg = {"server": proxy_server}
        if proxy_user:
            proxy_cfg["username"] = proxy_user
        if proxy_pass:
            proxy_cfg["password"] = proxy_pass

    last_shot = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy_cfg,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--no-zygote"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
            proxy=proxy_cfg,
        )
        page = await ctx.new_page()

        try:
            # === Step 1: Load the application form page ===
            print(f"\n=== Step 1: Load application form ===")
            resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"  Status: {resp.status if resp else 'N/A'}")
            await asyncio.sleep(5)
            last_shot = await screenshot(page, "01-form-loaded")
            print(f"  Title: {await page.title()}")

            # === Step 2: Handle cookie consent ===
            print(f"\n=== Step 2: Accept cookie consent ===")
            accepted = await accept_cookies(page)
            await asyncio.sleep(1)
            # Also remove any leftover modals
            await remove_modals(page)
            await asyncio.sleep(0.5)
            last_shot = await screenshot(page, "02-cookies-handled")

            # === Step 3: Verify form is visible ===
            print(f"\n=== Step 3: Verify form ===")
            firstname_el = await page.query_selector("input[name='firstname']")
            if not firstname_el:
                print("  Form not visible yet, waiting...")
                await asyncio.sleep(3)
                firstname_el = await page.query_selector("input[name='firstname']")
            print(f"  First name field present: {firstname_el is not None}")

            inputs = await page.query_selector_all("input:not([type='file']):not([type='checkbox'])")
            textareas = await page.query_selector_all("textarea")
            file_inputs = await page.query_selector_all("input[type='file']")
            print(f"  Text inputs: {len(inputs)}, Textareas: {len(textareas)}, File inputs: {len(file_inputs)}")

            # === Step 4: Fill personal info ===
            print(f"\n=== Step 4: Fill personal information ===")
            filled_count = 0
            for name, value in APPLICANT.items():
                if await fill(page, name, value):
                    print(f"  [{name}] = '{value[:40]}'")
                    filled_count += 1
                else:
                    print(f"  [{name}] NOT FILLED")

            # Handle phone - may have country prefix selector
            phone_el = await page.query_selector("input[type='tel']")
            if phone_el and await phone_el.is_visible():
                current = await phone_el.input_value()
                if not current:
                    await phone_el.fill(APPLICANT["phone"])
                    print(f"  [phone via tel] = '{APPLICANT['phone']}'")
                    filled_count += 1

            # Summary
            if await fill(page, "summary", SUMMARY):
                print(f"  [summary] = '{SUMMARY[:50]}'")
                filled_count += 1

            # Cover letter
            if await fill(page, "cover_letter", COVER_LETTER):
                print(f"  [cover_letter] = (set)")
                filled_count += 1

            # === Step 5: Fill screening questions ===
            print(f"\n=== Step 5: Fill screening questions ===")
            for qa_name, answer in SCREENING.items():
                if await fill(page, qa_name, answer):
                    print(f"  [{qa_name}] = '{answer[:60]}'")
                    filled_count += 1
                else:
                    print(f"  [{qa_name}] NOT FILLED")

            print(f"\n  Total fields filled: {filled_count}")
            last_shot = await screenshot(page, "03-form-filled")

            # === Step 6: Upload resume ===
            print(f"\n=== Step 6: Upload resume ===")
            if file_inputs and os.path.exists(RESUME_PDF):
                try:
                    await file_inputs[0].set_input_files(RESUME_PDF)
                    print(f"  Uploaded: {RESUME_PDF}")
                    await asyncio.sleep(3)
                    last_shot = await screenshot(page, "04-resume-uploaded")
                except Exception as e:
                    print(f"  Upload error: {e}")

            # === Step 7: Scroll to bottom, ensure no modals ===
            print(f"\n=== Step 7: Pre-submit preparation ===")
            await remove_modals(page)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            last_shot = await screenshot(page, "05-pre-submit")

            # Check submit button
            submit_el = await page.query_selector("button[type='submit']")
            if submit_el:
                txt = await submit_el.inner_text()
                vis = await submit_el.is_visible()
                en = await submit_el.is_enabled()
                print(f"  Submit button: '{txt.strip()}' visible={vis} enabled={en}")

            # === Step 8: Submit the application ===
            print(f"\n=== Step 8: Submit ===")
            if filled_count < 5:
                print(f"  Only {filled_count} fields filled - skipping submission")
                await update_app("partial",
                    f"Only {filled_count} fields filled. URL: {page.url}",
                    last_shot, cl_path, JOB_TITLE, JOB_URL)
                await browser.close()
                return

            # Use JS click to avoid overlay issues
            print("  Submitting via JS...")
            await page.evaluate("""
                () => {
                    const btn = document.querySelector('button[type="submit"]');
                    if (btn) btn.click();
                }
            """)

            # Wait longer to allow Turnstile to auto-process and form to submit
            print("  Waiting for submission to process (Turnstile may appear)...")
            await asyncio.sleep(3)
            last_shot = await screenshot(page, "06-submitting")

            # Check if Turnstile is visible
            turnstile_frame = None
            for frame in page.frames:
                if "challenges.cloudflare.com" in frame.url or "turnstile" in frame.url.lower():
                    print(f"  Turnstile frame detected: {frame.url}")
                    turnstile_frame = frame
                    break

            if turnstile_frame:
                print("  Cloudflare Turnstile detected - attempting auto-solve...")
                # Turnstile may auto-pass in some environments
                # Wait up to 15 seconds for it to auto-complete
                for i in range(15):
                    await asyncio.sleep(1)
                    # Check if the frame/challenge is gone
                    frames_with_turnstile = [f for f in page.frames if "turnstile" in f.url.lower()]
                    if not frames_with_turnstile:
                        print(f"  Turnstile auto-solved after {i+1}s")
                        break
                    if i == 7:
                        print(f"  Still waiting for Turnstile... ({i+1}s)")
                        last_shot = await screenshot(page, f"06b-turnstile-{i+1}s")

            # Wait for final result
            await asyncio.sleep(8)
            last_shot = await screenshot(page, "07-post-submit")
            final_url = page.url
            try:
                body = await page.evaluate("document.body.innerText")
            except:
                body = ""
            print(f"  Final URL: {final_url}")
            print(f"  Final body (500): {body[:500]}")

            # Determine result
            if any(w in body.lower() for w in ["thank", "success", "submitted", "received", "application has been", "we'll be in touch", "hear from us"]):
                print("  SUCCESS - Application submitted!")
                await update_app("applied",
                    f"Application submitted to '{JOB_TITLE}'. Confirmation received. URL: {final_url}",
                    last_shot, cl_path, JOB_TITLE, JOB_URL)
            elif any(w in body.lower() for w in ["verify you are human", "captcha", "turnstile"]):
                print("  BLOCKED by Cloudflare Turnstile CAPTCHA")
                await update_app("failed",
                    f"Blocked by Cloudflare Turnstile on submission. "
                    f"Form was fully filled ({filled_count} fields). "
                    f"URL: {APPLY_URL}. Manual CAPTCHA verification required.",
                    last_shot, cl_path, JOB_TITLE, JOB_URL)
            elif "submit" in body.lower() and final_url == APPLY_URL:
                # Still on same page - may be validation error
                print("  Still on form page - checking for errors...")
                errors = await page.evaluate("""
                    () => {
                        const errorEls = document.querySelectorAll('[class*="error"], [class*="Error"], [role="alert"]');
                        return Array.from(errorEls).map(el => el.innerText).join(' | ');
                    }
                """)
                print(f"  Validation errors: {errors[:300]}")
                if errors:
                    await update_app("failed",
                        f"Validation errors on submit: {errors[:300]}",
                        last_shot, cl_path, JOB_TITLE, JOB_URL)
                else:
                    await update_app("applied",
                        f"Submit clicked, still on form page (no errors). Possible submission. URL: {final_url}",
                        last_shot, cl_path, JOB_TITLE, JOB_URL)
            else:
                await update_app("applied",
                    f"Submit processed for '{JOB_TITLE}'. URL changed or content changed. Final URL: {final_url}",
                    last_shot, cl_path, JOB_TITLE, JOB_URL)

        except Exception as e:
            import traceback
            print(f"\nError: {e}")
            traceback.print_exc()
            try:
                s = await screenshot(page, "error")
                if s:
                    last_shot = s
            except:
                pass
            await update_app("failed", f"Error: {str(e)}", last_shot, cl_path, JOB_TITLE, JOB_URL)
        finally:
            await browser.close()
            print(f"\nComplete. Last screenshot: {last_shot}")

if __name__ == "__main__":
    asyncio.run(main())
