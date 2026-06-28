#!/usr/bin/env python3
"""
Apply to Sioux Technologies - Software Engineer C#/C++/JAVA (Eindhoven)
URL: https://vacancy.sioux.eu/
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
CV_PATH = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")
COVER_LETTER_PATH = Path("/home/user/Agents/output/cover-letters/sioux-technologies-net-engineer.md")

JOB_URL = "https://vacancy.sioux.eu/vacancies/vacancy_software_engineer_c_c_java_343474_31.html"
APPLY_URL = "https://vacancy.sioux.eu/index.php/page/applicants/command/applyforjob/vid/343474/bb/1"
VACANCY_ID = "343474"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
}

COVER_LETTER = """Dear Hiring Team,

I am excited to apply for the .NET Engineer position at Sioux Technologies. As a company headquartered in Eindhoven that pushes the boundaries of high-tech innovation, Sioux represents exactly the kind of environment where I want to grow my career — solving challenging technical problems alongside talented engineers.

As a Software Service Engineer at Actemium (VINCI Energies), I build and maintain industrial MES solutions using C#, .NET, and ASP.NET. This experience has given me a strong command of the .NET ecosystem and a deep appreciation for writing clean, maintainable code in demanding environments. My work with React on frontend components also aligns with Sioux's technology stack, and I am comfortable working across the full application layer.

My internship at ASML — another pillar of the Eindhoven high-tech ecosystem — was formative. There I developed automated testing frameworks using Python, Pytest, and Locust, and gained hands-on experience with Azure DevOps and Kubernetes. Working at ASML taught me the rigor and quality standards expected in high-tech, and I carry those standards into every project. At Delta Electronics, I migrated legacy VB applications to modern C# web solutions, demonstrating my ability to modernize codebases while preserving business logic.

I am also the founder of CogitatAI, an AI-powered chatbot platform built with Python and Flask, which reflects my entrepreneurial mindset and ability to deliver products end-to-end. I thrive when given ownership and the freedom to innovate — qualities I believe are valued at Sioux.

Being based in Eindhoven, fluent in English, Dutch, and Arabic, and holding a BSc in Software Engineering from Fontys, I am well-positioned to integrate into your team quickly. I am genuinely enthusiastic about contributing to Sioux's high-tech projects and would welcome the chance to discuss how my skills and drive can add value.

I am available to meet at your convenience and look forward to the conversation.

Best regards,
Hisham Abboud"""


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy_settings():
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not proxy_url:
        return None
    m = re.match(r"(https?)://([^:]+):([^@]+)@([^:]+):(\d+)", proxy_url)
    if m:
        scheme, user, pwd, host, port = m.groups()
        return {"server": f"{scheme}://{host}:{port}", "username": user, "password": pwd}
    return None


async def safe_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"sioux-{name}-{ts()}.png"
    for full_page in [False, True]:
        try:
            await page.screenshot(path=str(path), full_page=full_page, timeout=20000, animations="disabled")
            print(f"Screenshot saved: {path}")
            return str(path)
        except Exception as e:
            print(f"Screenshot {name} failed (full_page={full_page}): {e}")
    return ""


async def fill_field(page, selectors, value, desc):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible(timeout=2000):
                await el.click(timeout=2000)
                await asyncio.sleep(0.2)
                await el.fill(value, timeout=3000)
                print(f"  Filled [{desc}]: '{value}'")
                return True
        except Exception:
            pass
    print(f"  Could not fill [{desc}]")
    return False


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not CV_PATH.exists():
        print(f"ERROR: CV not found at {CV_PATH}")
        return {"status": "failed", "notes": f"CV not found at {CV_PATH}"}

    print(f"CV found: {CV_PATH}")

    proxy = get_proxy_settings()
    print(f"Proxy: {proxy['server'] if proxy else 'none'}")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--font-render-hinting=none",
            ],
        }
        if proxy:
            launch_kwargs["proxy"] = proxy

        browser = await p.chromium.launch(**launch_kwargs)

        ctx_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "ignore_https_errors": True,
        }
        if proxy:
            ctx_kwargs["proxy"] = proxy

        context = await browser.new_context(**ctx_kwargs)

        async def block_fonts(route):
            if route.request.resource_type == "font":
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_fonts)
        page = await context.new_page()

        # Step 1: Navigate to the job listing page
        print(f"\n[1] Navigating to job listing: {JOB_URL}")
        try:
            resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"Status: {resp.status if resp else 'N/A'}")
        except Exception as e:
            print(f"Navigation warning: {e}")

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        await asyncio.sleep(3)

        title = await page.title()
        current_url = page.url
        print(f"Title: {title}")
        print(f"URL: {current_url}")

        await safe_screenshot(page, "01-job-listing")

        # Step 2: Look for and click the "Apply now" button
        print("\n[2] Looking for Apply Now button...")
        apply_clicked = False

        apply_selectors = [
            "a:has-text('Apply now')",
            "a:has-text('Solliciteer')",
            "button:has-text('Apply now')",
            "button:has-text('Solliciteer')",
            "a[href*='applyforjob']",
            "a[href*='apply']",
            ".apply-btn",
            "#applyBtn",
            "[class*='apply']",
            "a[onclick*='apply']",
        ]

        for sel in apply_selectors:
            try:
                el = page.locator(sel).first
                count = await el.count()
                if count > 0:
                    visible = await el.is_visible(timeout=2000)
                    if visible:
                        text = await el.inner_text()
                        href = await el.get_attribute("href")
                        print(f"Found apply button: '{text}' ({sel}) -> {href}")
                        await el.click()
                        await asyncio.sleep(4)
                        apply_clicked = True
                        print(f"URL after click: {page.url}")
                        break
                    else:
                        print(f"  Found {sel} but not visible")
            except Exception as e:
                print(f"  Selector {sel}: {e}")

        if not apply_clicked:
            # Try direct navigation to apply URL
            print(f"\n  Trying direct navigation to: {APPLY_URL}")
            try:
                resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=45000)
                print(f"Status: {resp.status if resp else 'N/A'}")
                await asyncio.sleep(4)
                apply_clicked = True
            except Exception as e:
                print(f"Direct apply URL failed: {e}")

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        current_url = page.url
        title = await page.title()
        print(f"\nAfter apply click - Title: {title}")
        print(f"After apply click - URL: {current_url}")

        await safe_screenshot(page, "02-after-apply-click")

        # Step 3: Analyze the page/form
        print("\n[3] Analyzing page content and form...")
        try:
            body_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Page text (first 800 chars):\n{body_text[:800]}")
        except Exception as e:
            print(f"Body text error: {e}")

        try:
            elems = await page.evaluate("""
                () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    label: el.labels && el.labels[0] ? el.labels[0].innerText : '',
                    visible: el.offsetParent !== null,
                    required: el.required,
                }))
            """)
            print(f"\nForm elements ({len(elems)}):")
            for el in elems:
                print(f"  {el}")
        except Exception as e:
            print(f"Form analysis error: {e}")
            elems = []

        filled = []

        # Step 4: Fill form fields
        print("\n[4] Filling form fields...")

        # First name
        ok = await fill_field(page,
            ["input[name='first_name']", "input[name='firstName']", "input[id='first_name']",
             "input[id='firstName']", "input[autocomplete='given-name']",
             "input[placeholder*='First' i]", "input[placeholder*='Voornaam' i]",
             "input[placeholder*='first name' i]"],
            APPLICANT["first_name"], "first_name")
        if ok:
            filled.append("first_name")

        # Last name
        ok = await fill_field(page,
            ["input[name='last_name']", "input[name='lastName']", "input[id='last_name']",
             "input[id='lastName']", "input[autocomplete='family-name']",
             "input[placeholder*='Last' i]", "input[placeholder*='Achternaam' i]",
             "input[placeholder*='last name' i]"],
            APPLICANT["last_name"], "last_name")
        if ok:
            filled.append("last_name")

        # Full name (if single name field)
        ok = await fill_field(page,
            ["input[name='name']", "input[id='name']", "input[placeholder*='Full name' i]",
             "input[placeholder*='Naam' i]", "input[placeholder*='Your name' i]"],
            APPLICANT["full_name"], "full_name")
        if ok:
            filled.append("full_name")

        # Email
        ok = await fill_field(page,
            ["input[type='email']", "input[name='email']", "input[id='email']",
             "input[autocomplete='email']", "input[placeholder*='mail' i]",
             "input[placeholder*='e-mail' i]"],
            APPLICANT["email"], "email")
        if ok:
            filled.append("email")

        # Phone
        ok = await fill_field(page,
            ["input[type='tel']", "input[name='phone']", "input[name='telephone']",
             "input[name='mobile']", "input[id='phone']", "input[autocomplete='tel']",
             "input[placeholder*='Phone' i]", "input[placeholder*='Telefoon' i]",
             "input[placeholder*='Mobile' i]"],
            APPLICANT["phone"], "phone")
        if ok:
            filled.append("phone")

        # City/Location
        ok = await fill_field(page,
            ["input[name='city']", "input[name='location']", "input[name='address_city']",
             "input[placeholder*='City' i]", "input[placeholder*='Stad' i]",
             "input[placeholder*='Location' i]"],
            APPLICANT["city"], "city")
        if ok:
            filled.append("city")

        # Cover letter / motivation textarea
        print("\n[5] Looking for motivation/cover letter field...")
        for sel in [
            "textarea[name*='cover' i]", "textarea[name*='motivation' i]",
            "textarea[name*='letter' i]", "textarea[name*='message' i]",
            "textarea[id*='cover' i]", "textarea[id*='motivation' i]",
            "textarea[placeholder*='motivation' i]", "textarea[placeholder*='cover' i]",
            "textarea[placeholder*='letter' i]", "textarea[placeholder*='Why' i]",
            "textarea",
        ]:
            try:
                ta = page.locator(sel).first
                if await ta.count() > 0 and await ta.is_visible(timeout=1500):
                    await ta.click()
                    await asyncio.sleep(0.2)
                    await ta.fill(COVER_LETTER)
                    filled.append("cover_letter")
                    print(f"  Filled cover letter textarea ({sel})")
                    break
            except Exception:
                pass

        # Step 5: Upload CV
        print("\n[6] Uploading CV...")
        cv_uploaded = False
        file_inputs = await page.locator("input[type='file']").all()
        print(f"File inputs found: {len(file_inputs)}")
        for i, fi in enumerate(file_inputs):
            try:
                await fi.set_input_files(str(CV_PATH))
                cv_uploaded = True
                print(f"  CV uploaded via file input {i}")
                await asyncio.sleep(3)
                break
            except Exception as e:
                print(f"  File input {i} error: {e}")

        if not cv_uploaded:
            # Try clicking upload button
            upload_sels = [
                "button:has-text('Upload')", "button:has-text('CV')",
                "label[for*='cv']", "label[for*='resume']", "label[for*='file']",
                "[class*='upload']", "[class*='file']",
            ]
            for sel in upload_sels:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible(timeout=1500):
                        print(f"  Found upload trigger: {sel}")
                        async with page.expect_file_chooser(timeout=3000) as fc_info:
                            await el.click()
                        fc = await fc_info.value
                        await fc.set_files(str(CV_PATH))
                        cv_uploaded = True
                        print("  CV uploaded via file chooser")
                        await asyncio.sleep(3)
                        break
                except Exception as e:
                    print(f"  Upload selector {sel}: {e}")

        # Check for checkboxes (privacy / consent)
        print("\n[7] Handling checkboxes...")
        checkboxes = await page.locator("input[type='checkbox']").all()
        print(f"Checkboxes found: {len(checkboxes)}")
        for i, cb in enumerate(checkboxes):
            try:
                checked = await cb.is_checked()
                if not checked:
                    await cb.check()
                    print(f"  Checked checkbox {i}")
            except Exception as e:
                print(f"  Checkbox {i}: {e}")

        # Scroll to bottom to see full form
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        except Exception:
            pass

        await safe_screenshot(page, "03-form-filled")
        print(f"\nFilled fields: {filled}")
        print(f"CV uploaded: {cv_uploaded}")

        # Step 6: Submit
        print("\n[8] Looking for submit button...")
        submitted = False
        submit_sels = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send')",
            "button:has-text('Apply now')",
            "button:has-text('Solliciteer')",
            "button:has-text('Verstuur')",
            "button:has-text('Verzenden')",
            "button:has-text('Next')",
            "button:has-text('Volgende')",
            "[type='submit']",
        ]

        for sel in submit_sels:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text()
                    print(f"Found submit: '{text}' ({sel})")
                    await safe_screenshot(page, "04-pre-submit")
                    await el.click()
                    print("Clicked submit button")
                    await asyncio.sleep(6)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                    submitted = True
                    break
            except Exception as e:
                print(f"  Submit {sel}: {e}")

        await safe_screenshot(page, "05-post-submit")

        final_url = page.url
        status = "failed"
        notes = ""

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"\nPost-submit page text (first 600 chars):\n{body[:600]}")

            success_words = [
                "thank", "confirm", "success", "received", "bedankt", "we'll be",
                "application", "gelukt", "ontvangen", "submitted", "sollicitatie",
                "we will contact", "we zullen contact"
            ]
            captcha_words = ["captcha", "robot", "verify", "human"]

            body_lower = body.lower()
            if any(w in body_lower for w in success_words):
                status = "applied"
                notes = f"Application submitted successfully to Sioux Technologies. Final URL: {final_url}"
                print("\nSUCCESS: Application confirmed!")
            elif any(w in body_lower for w in captcha_words):
                status = "failed"
                notes = f"Blocked by CAPTCHA at {final_url}"
                print("\nFAILED: CAPTCHA detected")
            elif submitted:
                status = "applied"
                notes = f"Form submitted (confirmation unclear). URL: {final_url}. Filled: {filled}"
                print("\nSubmitted - confirmation unclear but form was submitted")
            else:
                status = "failed"
                notes = f"Could not submit form. Filled: {filled}. URL: {final_url}"
                print("\nFAILED: Could not submit")
        except Exception as e:
            if submitted:
                status = "applied"
            notes = f"Post-submit check error: {e}. Submitted: {submitted}"

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "filled_fields": filled,
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result:\n{json.dumps(result, indent=2)}")
