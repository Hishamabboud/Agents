#!/usr/bin/env python3
"""
Fortanix job application via Playwright.
Target: Senior Software Engineer - Backend Microservices, Rust (Netherlands)
Apply URL: https://apply.workable.com/fortanix/j/DFCBABCC33/apply/

Flow:
1. Load job page
2. Accept cookie banner (removes backdrop overlay)
3. Click APPLICATION tab
4. Fill form fields
5. Upload resume
6. Submit
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
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31 06 4841 2838",
}

COVER_LETTER = """Dear Hiring Team at Fortanix,

I am writing to express my enthusiasm for the Software Engineer position at Fortanix in Eindhoven. As a Software Service Engineer at Actemium (VINCI Energies) with a background in full-stack development using .NET, C#, Python, and JavaScript, I am excited by the opportunity to contribute to Fortanix's mission of securing data in the cloud and beyond.

My experience includes building and maintaining industrial applications, developing REST APIs, working with cloud infrastructure (Azure, Kubernetes), and contributing to security-focused projects, including a GDPR data anonymization solution during my graduation project at Fontys ICT Cyber Security Research Group.

Fortanix's work on confidential computing and data security aligns strongly with my professional interests and background. I am based in Eindhoven and would welcome the chance to join the team at High Tech Campus.

Thank you for your consideration. I look forward to the opportunity to discuss how I can contribute.

Best regards,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com
"""

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
    print(f"  Tracker: status='{status}'")

async def dismiss_cookie_banner(page):
    """Try to click Accept/Accept all on any cookie consent banner."""
    cookie_selectors = [
        "button:has-text('Accept all')",
        "button:has-text('Accept All')",
        "button:has-text('Accept cookies')",
        "button:has-text('Accept')",
        "button:has-text('OK')",
        "[data-testid='cookie-accept']",
        "#accept-cookies",
        ".cookie-accept",
    ]
    for sel in cookie_selectors:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                text = await el.inner_text()
                print(f"  Cookie banner: clicking '{text.strip()}'")
                await el.click()
                await asyncio.sleep(1)
                return True
        except:
            pass
    # Also try to hide the backdrop via JS
    try:
        removed = await page.evaluate("""
            () => {
                let count = 0;
                // Remove backdrop elements
                document.querySelectorAll('[data-ui="backdrop"]').forEach(el => {
                    el.style.display = 'none';
                    el.remove();
                    count++;
                });
                // Also hide cookie banners
                document.querySelectorAll('[class*="cookie"], [id*="cookie"], [class*="consent"]').forEach(el => {
                    el.style.display = 'none';
                    count++;
                });
                return count;
            }
        """)
        if removed > 0:
            print(f"  Removed {removed} overlay/cookie elements via JS")
    except Exception as e:
        print(f"  JS banner removal failed: {e}")
    return False

async def js_click(page, selector):
    """Click an element using JavaScript to bypass overlay issues."""
    try:
        result = await page.evaluate(f"""
            () => {{
                const el = document.querySelector('{selector}');
                if (el) {{ el.click(); return true; }}
                return false;
            }}
        """)
        return result
    except Exception as e:
        print(f"  JS click failed for {selector}: {e}")
        return False

async def fill_field(page, selectors, value, label=""):
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.fill(value)
                actual = await el.input_value()
                if actual:
                    print(f"  Filled {label}: '{value[:50]}'")
                    return True
        except:
            pass
    return False

async def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    # Save cover letter
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
            # === Step 1: Load job page ===
            print(f"\n=== Step 1: Load job page ===")
            print(f"  URL: {JOB_URL}")
            resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"  Status: {resp.status if resp else 'N/A'}")
            await asyncio.sleep(4)
            last_shot = await screenshot(page, "01-job-page")
            print(f"  Title: {await page.title()}")

            # === Step 2: Dismiss cookie banner ===
            print(f"\n=== Step 2: Dismiss cookie consent banner ===")
            accepted = await dismiss_cookie_banner(page)
            await asyncio.sleep(1)

            # Check if backdrop is still there
            backdrop = await page.query_selector('[data-ui="backdrop"]')
            if backdrop:
                print("  Backdrop still present - removing via JS...")
                await page.evaluate("""
                    () => {
                        document.querySelectorAll('[data-ui="backdrop"]').forEach(el => el.remove());
                        document.querySelectorAll('[class*="backdrop"]').forEach(el => el.remove());
                    }
                """)
                await asyncio.sleep(0.5)
            else:
                print("  No backdrop found - cookie banner dismissed successfully")

            last_shot = await screenshot(page, "02-cookie-dismissed")

            # === Step 3: Click APPLICATION tab ===
            print(f"\n=== Step 3: Click APPLICATION tab ===")
            # Try normal click first
            app_tab_clicked = False

            # First try: direct click on APPLICATION tab
            for sel in [
                "a:has-text('APPLICATION')",
                "a[href*='apply']",
                f"a[href='/fortanix/j/{JOB_SHORTCODE}/apply/']",
                "[data-ui='tab']:has-text('APPLICATION')",
                "li:has-text('APPLICATION') a",
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        visible = await el.is_visible()
                        print(f"  Found '{sel}': visible={visible}")
                        if visible:
                            await el.click(timeout=5000)
                            app_tab_clicked = True
                            print(f"  Clicked APPLICATION tab")
                            break
                except Exception as e:
                    print(f"  Click {sel} failed: {e}")

            if not app_tab_clicked:
                # Try JS click
                print("  Trying JS click on APPLICATION link...")
                for js_sel in [
                    f"a[href*='{JOB_SHORTCODE}/apply']",
                    "a[href*='/apply/']",
                    "a[href*='/apply']",
                ]:
                    result = await js_click(page, js_sel)
                    if result:
                        print(f"  JS clicked: {js_sel}")
                        app_tab_clicked = True
                        break

            if not app_tab_clicked:
                # Navigate directly to apply URL
                print("  Navigating directly to apply URL...")
                resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
                print(f"  Apply URL status: {resp.status if resp else 'N/A'}")

            await asyncio.sleep(4)
            last_shot = await screenshot(page, "03-application-tab")
            print(f"  Current URL: {page.url}")
            print(f"  Title: {await page.title()}")

            # === Step 4: Handle cookie banner again (if it reappeared) ===
            await dismiss_cookie_banner(page)
            # Always remove backdrop
            await page.evaluate("""
                () => {
                    document.querySelectorAll('[data-ui="backdrop"]').forEach(el => el.remove());
                }
            """)
            await asyncio.sleep(1)

            # === Step 5: Inspect the form ===
            print(f"\n=== Step 5: Inspect form ===")
            inputs = await page.query_selector_all("input")
            textareas = await page.query_selector_all("textarea")
            print(f"  Inputs: {len(inputs)}, Textareas: {len(textareas)}")
            for inp in inputs:
                try:
                    t = await inp.get_attribute("type") or "text"
                    n = await inp.get_attribute("name") or ""
                    i = await inp.get_attribute("id") or ""
                    ph = await inp.get_attribute("placeholder") or ""
                    label_el = None
                    try:
                        label_el = await page.query_selector(f"label[for='{i}']")
                        label_text = await label_el.inner_text() if label_el else ""
                    except:
                        label_text = ""
                    print(f"    input[type={t}, name={n}, id={i}, ph='{ph[:25]}', label='{label_text[:25]}']")
                except:
                    pass
            for ta in textareas:
                try:
                    n = await ta.get_attribute("name") or ""
                    i = await ta.get_attribute("id") or ""
                    ph = await ta.get_attribute("placeholder") or ""
                    print(f"    textarea[name={n}, id={i}, ph='{ph[:30]}']")
                except:
                    pass

            # === Step 6: Fill form ===
            print(f"\n=== Step 6: Fill form ===")
            filled = 0

            if await fill_field(page,
                ["input[name='firstname']", "input[name='first_name']", "input[id*='firstname']",
                 "input[placeholder*='irst']", "input[autocomplete='given-name']",
                 "input[id*='first']"],
                APPLICANT["first_name"], "first_name"):
                filled += 1

            if await fill_field(page,
                ["input[name='lastname']", "input[name='last_name']", "input[id*='lastname']",
                 "input[placeholder*='ast']", "input[autocomplete='family-name']",
                 "input[id*='last']"],
                APPLICANT["last_name"], "last_name"):
                filled += 1

            if await fill_field(page,
                ["input[name='email']", "input[type='email']", "input[id*='email']",
                 "input[placeholder*='mail']", "input[autocomplete='email']"],
                APPLICANT["email"], "email"):
                filled += 1

            if await fill_field(page,
                ["input[name='phone']", "input[type='tel']", "input[id*='phone']",
                 "input[placeholder*='hone']", "input[autocomplete='tel']"],
                APPLICANT["phone"], "phone"):
                filled += 1

            # Cover letter
            if await fill_field(page,
                ["textarea[name='cover_letter']", "textarea[name='coverLetter']",
                 "textarea[id*='cover']", "textarea[placeholder*='over']", "textarea"],
                COVER_LETTER, "cover_letter"):
                filled += 1

            print(f"  Total filled: {filled}")
            if filled > 0:
                last_shot = await screenshot(page, "04-form-filled")

            # === Step 7: Upload resume ===
            print(f"\n=== Step 7: Upload resume ===")
            file_inputs = await page.query_selector_all("input[type='file']")
            print(f"  File inputs: {len(file_inputs)}")
            for fi in file_inputs:
                try:
                    if os.path.exists(RESUME_PDF):
                        await fi.set_input_files(RESUME_PDF)
                        print(f"  Resume uploaded")
                        await asyncio.sleep(3)
                        last_shot = await screenshot(page, "05-resume-uploaded")
                        break
                except Exception as e:
                    print(f"  Upload error: {e}")

            # === Step 8: Pre-submit screenshot ===
            print(f"\n=== Step 8: Pre-submit screenshot ===")
            s = await screenshot(page, "06-pre-submit")
            if s:
                last_shot = s
            print(f"  URL: {page.url}")
            try:
                body = await page.evaluate("document.body.innerText")
                print(f"  Body text (500 chars): {body[:500]}")
            except:
                pass

            # === Step 9: Find submit button and submit ===
            print(f"\n=== Step 9: Submit ===")
            submit_btn = None
            for sel in [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit application')",
                "button:has-text('Submit')",
                "button:has-text('Send application')",
                "button:has-text('Send')",
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        txt = await el.inner_text()
                        print(f"  Found submit: '{txt.strip()}' [{sel}]")
                        submit_btn = el
                        break
                except:
                    pass

            if filled > 0 and submit_btn:
                # Remove any backdrop again before submitting
                await page.evaluate("() => { document.querySelectorAll('[data-ui=\"backdrop\"]').forEach(e => e.remove()); }")
                print("  Clicking Submit...")
                await submit_btn.click(timeout=10000)
                await asyncio.sleep(6)
                s = await screenshot(page, "07-post-submit")
                if s:
                    last_shot = s
                try:
                    body = await page.evaluate("document.body.innerText")
                    final_url = page.url
                    print(f"  Post-submit URL: {final_url}")
                    print(f"  Body (300 chars): {body[:300]}")
                    if any(w in body.lower() for w in ["thank", "success", "submitted", "received", "confirmation"]):
                        await update_app("applied",
                            f"Application submitted. Confirmation text detected. URL: {final_url}",
                            last_shot, cl_path, JOB_TITLE, JOB_URL)
                    else:
                        await update_app("applied",
                            f"Submit clicked. No explicit confirmation detected. URL: {final_url}",
                            last_shot, cl_path, JOB_TITLE, JOB_URL)
                except Exception as e:
                    await update_app("applied",
                        f"Submit clicked, could not verify result: {e}",
                        last_shot, cl_path, JOB_TITLE, JOB_URL)

            elif filled == 0 and submit_btn is None:
                body = ""
                try:
                    body = await page.evaluate("document.body ? document.body.innerText : ''")
                except:
                    pass
                notes = (f"Form rendered but no fillable fields or submit button found. "
                         f"URL: {page.url}. Body sample: {body[:200]}")
                await update_app("skipped", notes, last_shot, cl_path, JOB_TITLE, JOB_URL)

            else:
                notes = (f"Partial: {filled} fields filled, "
                         f"submit={'found' if submit_btn else 'not found'}. URL: {page.url}")
                await update_app("partial", notes, last_shot, cl_path, JOB_TITLE, JOB_URL)

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
            print(f"\nDone. Last screenshot: {last_shot}")

if __name__ == "__main__":
    asyncio.run(main())
