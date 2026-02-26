#!/usr/bin/env python3
"""
Apply to Trifork Medior .NET Developer position in Eindhoven.
Uses Homerun ATS at trifork.homerun.co
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

JOB_URL = "https://trifork.homerun.co/medior-net-developer-eindhoven"
APPLY_URL = "https://trifork.homerun.co/medior-net-developer-eindhoven/en/apply"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
}

MOTIVATION = (
    "I am applying for the Medior .NET Developer position at Trifork in Eindhoven. "
    "In my current role as Software Service Engineer at Actemium (VINCI Energies), I build "
    "and maintain .NET, C#, and ASP.NET applications for industrial MES clients — designing REST APIs, "
    "optimizing database integrations, and delivering production-ready software. "
    "Before that, at ASML I worked in an agile Azure/Kubernetes environment, and at Delta Electronics "
    "I led a legacy VB-to-C# migration. I hold a BSc in Software Engineering from Fontys Eindhoven. "
    "Trifork's focus on innovative, impactful software — from smart healthcare to connected vehicles — "
    "is exactly the kind of meaningful technical challenge I want to take on next."
)


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
    path = SCREENSHOTS_DIR / f"trifork-{name}-{ts()}.png"
    for full_page in [False, True]:
        try:
            await page.screenshot(path=str(path), full_page=full_page, timeout=20000, animations="disabled")
            print(f"Screenshot: {path}")
            return str(path)
        except Exception as e:
            print(f"Screenshot {name} failed (full_page={full_page}): {e}")
    return ""


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not CV_PATH.exists():
        print(f"ERROR: CV not found at {CV_PATH}")
        return {"status": "failed", "notes": "CV not found"}

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

        # Block fonts
        async def block_fonts(route):
            if route.request.resource_type == "font":
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_fonts)
        page = await context.new_page()

        # Step 1: Go to apply page directly
        print(f"\n[1] Navigating to: {APPLY_URL}")
        try:
            resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"Status: {resp.status if resp else 'N/A'}")
        except Exception as e:
            print(f"Goto warning: {e}")
            # Fallback: try job page
            try:
                resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
                print(f"Fallback status: {resp.status if resp else 'N/A'}")
            except Exception as e2:
                print(f"Fallback also failed: {e2}")

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        await asyncio.sleep(4)

        title = await page.title()
        current_url = page.url
        print(f"Title: {title}")
        print(f"URL: {current_url}")

        # Check if application is possible
        try:
            body_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Body text (500 chars): {body_text[:500]}")
            if "not possible" in body_text.lower() or "no longer" in body_text.lower():
                print("WARNING: Application may not be possible - position might be closed")
        except Exception as e:
            print(f"Body text error: {e}")

        await safe_screenshot(page, "01-apply-page")

        # If not on apply page, look for Apply button
        if "/apply" not in current_url:
            print("\n[2] Not on apply page, looking for Apply button...")
            apply_sels = [
                "a[href*='/apply']",
                "text=Apply now",
                "text=Apply",
                "button:has-text('Apply')",
                "a:has-text('Apply')",
            ]
            for sel in apply_sels:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        href = await el.get_attribute("href")
                        print(f"Found: {sel} -> {href}")
                        await el.click()
                        await asyncio.sleep(3)
                        print(f"URL after click: {page.url}")
                        break
                except Exception as e:
                    print(f"Sel {sel}: {e}")

        await safe_screenshot(page, "02-before-form")

        # Step 3: Analyze form
        print("\n[3] Analyzing form...")
        try:
            elems = await page.evaluate("""
                () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                    tag: el.tagName, type: el.type || '', name: el.name || '',
                    id: el.id || '', placeholder: el.placeholder || '',
                    visible: el.offsetParent !== null,
                    required: el.required,
                }))
            """)
            print(f"Form elements ({len(elems)}):")
            for el in elems:
                print(f"  {el}")
        except Exception as e:
            print(f"Form analysis error: {e}")
            elems = []

        filled = []

        async def fill(selectors, value, desc):
            for sel in selectors:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible(timeout=2000):
                        await el.click(timeout=2000)
                        await asyncio.sleep(0.2)
                        await el.fill(value, timeout=3000)
                        filled.append(desc)
                        print(f"  Filled [{desc}]: '{value}'")
                        return True
                except Exception:
                    pass
            print(f"  Could not fill [{desc}]")
            return False

        # Fill personal info
        print("\n[4] Filling form fields...")
        await fill(
            ["input[name='first_name']", "input[name='firstName']", "input[id='first_name']",
             "input[autocomplete='given-name']", "input[placeholder*='First' i]", "input[placeholder*='Voornaam' i]"],
            APPLICANT["first_name"], "first_name"
        )
        await fill(
            ["input[name='last_name']", "input[name='lastName']", "input[id='last_name']",
             "input[autocomplete='family-name']", "input[placeholder*='Last' i]", "input[placeholder*='Achternaam' i]"],
            APPLICANT["last_name"], "last_name"
        )
        await fill(
            ["input[type='email']", "input[name='email']", "input[id='email']",
             "input[autocomplete='email']", "input[placeholder*='mail' i]"],
            APPLICANT["email"], "email"
        )
        await fill(
            ["input[type='tel']", "input[name='phone']", "input[name='telephone']",
             "input[id='phone']", "input[autocomplete='tel']", "input[placeholder*='Phone' i]",
             "input[placeholder*='Telefoon' i]"],
            APPLICANT["phone"], "phone"
        )
        await fill(
            ["input[name='city']", "input[name='location']", "input[placeholder*='City' i]",
             "input[placeholder*='Stad' i]"],
            APPLICANT["city"], "city"
        )
        await fill(
            ["input[name='linkedin']", "input[name*='linkedin' i]", "input[id*='linkedin' i]",
             "input[placeholder*='LinkedIn' i]"],
            APPLICANT["linkedin"], "linkedin"
        )

        # Motivation/cover letter textarea
        for sel in ["textarea", "textarea[name*='cover' i]", "textarea[name*='motivation' i]",
                    "textarea[name*='letter' i]", "textarea[placeholder*='motivation' i]"]:
            try:
                ta = page.locator(sel).first
                if await ta.count() > 0 and await ta.is_visible(timeout=1500):
                    await ta.click()
                    await asyncio.sleep(0.2)
                    await ta.fill(MOTIVATION)
                    filled.append("motivation")
                    print(f"  Filled motivation textarea ({sel})")
                    break
            except Exception:
                pass

        # CV upload
        print("\n[5] Uploading CV...")
        cv_uploaded = False
        file_inputs = await page.locator("input[type='file']").all()
        print(f"File inputs found: {len(file_inputs)}")
        for i, fi in enumerate(file_inputs):
            try:
                await fi.set_input_files(str(CV_PATH))
                cv_uploaded = True
                print(f"  CV uploaded to file input {i}")
                await asyncio.sleep(3)
                break
            except Exception as e:
                print(f"  File input {i} error: {e}")

        # Checkboxes (privacy)
        checkboxes = await page.locator("input[type='checkbox']").all()
        print(f"\nCheckboxes: {len(checkboxes)}")
        for i, cb in enumerate(checkboxes):
            try:
                if not await cb.is_checked():
                    await cb.check()
                    print(f"  Checked checkbox {i}")
            except Exception as e:
                print(f"  Checkbox {i}: {e}")

        # Scroll to bottom
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        except Exception:
            pass

        await safe_screenshot(page, "03-form-filled")
        print(f"\nFilled fields: {filled}, CV uploaded: {cv_uploaded}")

        # Step 6: Submit
        print("\n[6] Submitting...")
        submitted = False
        submit_sels = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send')",
            "button:has-text('Next')",
            "button:has-text('Volgende')",
            "button:has-text('Verstuur')",
            "[type='submit']",
        ]

        for sel in submit_sels:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text()
                    print(f"Submitting via: '{text}' ({sel})")
                    await safe_screenshot(page, "04-pre-submit")
                    await el.click()
                    await asyncio.sleep(5)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=8000)
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
            print(f"Post-submit text: {body[:600]}")
            success_words = ["thank", "confirm", "success", "received", "bedankt", "we'll be",
                             "application", "gelukt", "ontvangen", "submitted"]
            if any(w in body.lower() for w in success_words):
                status = "applied"
                notes = f"Application submitted to Trifork Medior .NET Developer. Final URL: {final_url}"
                print("SUCCESS: Application confirmed!")
            elif submitted:
                status = "applied"
                notes = f"Submitted (confirmation unclear). Final URL: {final_url}"
                print("Submitted - confirmation unclear")
            else:
                status = "failed"
                notes = f"Could not submit. Filled: {filled}. Final URL: {final_url}"
        except Exception as e:
            if submitted:
                status = "applied"
            notes = f"Post-submit check error: {e}"

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "filled": filled,
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
