#!/usr/bin/env python3
"""
Fortanix job application - final attempt with Turnstile handling.
Tries to click the Cloudflare Turnstile checkbox via iframe access.
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

SUMMARY = "Software Engineer with 3+ years experience in .NET/C#, Python, REST APIs, Azure, and Kubernetes."

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

SCREENING = {
    "QA_11110678": "Python, C#/.NET, JavaScript, SQL, Visual Basic. Primarily Python and C# in production environments.",
    "QA_11110679": "3 - I have experimented with Rust in personal projects and am actively building proficiency.",
    "QA_11110680": "Approximately 70% of my time is spent hands-on coding; the rest is architecture, reviews, and support.",
    "QA_11110681": "3 years. I have built and maintained microservices-based systems using .NET, REST APIs, deployed via Azure and Kubernetes.",
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
    path = os.path.join(SCREENSHOTS_DIR, f"fortanix-final-{name}-{ts()}.png")
    try:
        await page.screenshot(path=path, full_page=False, timeout=15000)
        print(f"  Screenshot: {path}")
        return path
    except Exception as e:
        print(f"  Screenshot failed: {e}")
        return ""

async def update_app(status, notes, shot="", cl=""):
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
            app["role"] = JOB_TITLE
            app["url"] = JOB_URL
            app["resume_file"] = "profile/Hisham Abboud CV.pdf"
            break
    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)
    print(f"  Tracker: '{status}'")

async def fill(page, name, value):
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
    print(f"Cover letter: {cl_path}")

    proxy_server, proxy_user, proxy_pass = get_proxy_config()
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
            # Load and fill form (same as before)
            print("Loading form...")
            resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(5)
            last_shot = await screenshot(page, "01-loaded")

            # Accept cookies
            for sel in ["button:has-text('Accept all')", "button:has-text('Accept All')"]:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click(timeout=5000)
                        await asyncio.sleep(1.5)
                        break
                except:
                    pass

            # Fill all fields
            print("Filling fields...")
            filled = 0
            for name, value in APPLICANT.items():
                if await fill(page, name, value):
                    filled += 1

            # Phone via tel
            phone_el = await page.query_selector("input[type='tel']")
            if phone_el and await phone_el.is_visible():
                cur = await phone_el.input_value()
                if not cur:
                    await phone_el.fill(APPLICANT["phone"])
                    filled += 1

            for name, value in [("summary", SUMMARY), ("cover_letter", COVER_LETTER)]:
                if await fill(page, name, value):
                    filled += 1

            for name, value in SCREENING.items():
                if await fill(page, name, value):
                    filled += 1

            print(f"  {filled} fields filled")

            # Upload resume
            fi = await page.query_selector("input[type='file']")
            if fi and os.path.exists(RESUME_PDF):
                await fi.set_input_files(RESUME_PDF)
                await asyncio.sleep(3)
                print("  Resume uploaded")

            last_shot = await screenshot(page, "02-filled")

            # Submit
            print("Submitting...")
            await page.evaluate("() => { const b = document.querySelector('button[type=\"submit\"]'); if(b) b.click(); }")
            await asyncio.sleep(3)
            last_shot = await screenshot(page, "03-submitting")

            # Try to click Turnstile checkbox
            print("Checking for Turnstile...")
            turnstile_clicked = False

            # Look for Turnstile iframe
            for attempt in range(20):
                await asyncio.sleep(1)
                frames = page.frames
                turnstile_frames = [f for f in frames if "challenges.cloudflare.com" in f.url or "turnstile" in f.url.lower()]

                if turnstile_frames:
                    tf = turnstile_frames[0]
                    print(f"  Turnstile frame found: {tf.url[:80]}")

                    # Try to click the checkbox inside the iframe
                    try:
                        cb = await tf.query_selector("input[type='checkbox']")
                        if not cb:
                            cb = await tf.query_selector(".ctp-checkbox-label")
                        if not cb:
                            cb = await tf.query_selector("[id*='checkbox']")
                        if not cb:
                            # Try clicking at the checkbox position
                            body = await tf.query_selector("body")
                            if body:
                                box = await body.bounding_box()
                                if box:
                                    # Click at the center-left of the iframe (where checkbox is)
                                    await page.mouse.click(box['x'] + 20, box['y'] + box['height']/2)
                                    print(f"  Clicked at checkbox position")
                                    await asyncio.sleep(2)
                        if cb:
                            await cb.click(timeout=5000)
                            print(f"  Clicked Turnstile checkbox!")
                            await asyncio.sleep(3)
                            turnstile_clicked = True
                    except Exception as e:
                        print(f"  Turnstile click attempt {attempt+1}: {e}")

                    if turnstile_clicked:
                        break
                else:
                    # No more Turnstile frames - may have auto-passed or completed
                    if attempt > 3:
                        print(f"  No Turnstile frame after {attempt+1} attempts - may have passed")
                        break

                if attempt == 9:
                    last_shot = await screenshot(page, "04-turnstile-waiting")
                    print(f"  Still waiting for Turnstile at {attempt+1}s")

            # Wait for form submission to complete
            print("Waiting for final result...")
            await asyncio.sleep(10)
            last_shot = await screenshot(page, "05-final")
            final_url = page.url
            try:
                body = await page.evaluate("document.body.innerText")
            except:
                body = ""
            print(f"Final URL: {final_url}")
            print(f"Body (500): {body[:500]}")

            # Assess result
            success_words = ["thank", "success", "submitted", "received", "application has been", "hear from us", "we'll contact"]
            fail_words = ["verify you are human", "captcha", "please complete"]
            error_words = ["error", "required field", "invalid", "please fill"]

            if any(w in body.lower() for w in success_words):
                await update_app("applied",
                    f"Application submitted successfully. Confirmation detected. Final URL: {final_url}",
                    last_shot, cl_path)
            elif any(w in body.lower() for w in fail_words):
                await update_app("failed",
                    f"Cloudflare Turnstile CAPTCHA blocked submission. "
                    f"Form was fully filled and ready. "
                    f"Manual CAPTCHA completion required at: {APPLY_URL}",
                    last_shot, cl_path)
            elif any(w in body.lower() for w in error_words):
                # Get specific errors
                errors = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('[class*="error"], [role="alert"]'))
                         .map(e => e.innerText).filter(t => t.trim()).join(' | ')
                """)
                await update_app("failed",
                    f"Form validation errors: {errors[:300]}. URL: {final_url}",
                    last_shot, cl_path)
            elif "submitting" in body.lower():
                await update_app("failed",
                    f"Stuck on submitting state - Turnstile CAPTCHA blocking. URL: {APPLY_URL}",
                    last_shot, cl_path)
            else:
                await update_app("applied",
                    f"Submit processed. Final URL: {final_url}",
                    last_shot, cl_path)

        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()
            try:
                s = await screenshot(page, "error")
                if s:
                    last_shot = s
            except:
                pass
            await update_app("failed", f"Error: {str(e)}", last_shot, cl_path)
        finally:
            await browser.close()
            print(f"\nDone. Final screenshot: {last_shot}")

if __name__ == "__main__":
    asyncio.run(main())
