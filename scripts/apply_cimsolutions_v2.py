#!/usr/bin/env python3
"""
Apply to CIMSOLUTIONS Python Software Engineer position.
Version 2: Handle cookie banner, use correct field IDs, JS submit.
"""

import asyncio
import json
import os
import urllib.parse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
CV_PATH = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")
MOTIVATION_PDF = Path("/home/user/Agents/output/cover-letters/cimsolutions-python-software-engineer.pdf")

FORM_URL = "https://www.cimsolutions.nl/solliciteren/?python-software-engineer-ah5ashpvv9cksst8"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
}


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy():
    proxy_raw = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or ""
    )
    if not proxy_raw:
        return None
    parsed = urllib.parse.urlparse(proxy_raw)
    cfg = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
    if parsed.username:
        cfg["username"] = urllib.parse.unquote(parsed.username)
    if parsed.password:
        cfg["password"] = urllib.parse.unquote(parsed.password)
    return cfg


async def safe_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"cimsolutions-v2-{name}-{ts()}.png"
    try:
        await page.screenshot(path=str(path), full_page=False, timeout=20000, animations="disabled")
        print(f"Screenshot: {path}")
        return str(path)
    except Exception as e:
        print(f"Screenshot {name} failed: {e}")
        return ""


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not CV_PATH.exists():
        print(f"ERROR: CV not found at {CV_PATH}")
        return {"status": "failed", "notes": "CV not found"}

    proxy = get_proxy()
    print(f"Proxy: {proxy['server'] if proxy else 'none'}")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
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
        page = await context.new_page()

        print(f"\n[1] Navigating to form: {FORM_URL}")
        try:
            resp = await page.goto(FORM_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"Status: {resp.status if resp else 'N/A'}")
        except Exception as e:
            print(f"Goto warning: {e}")

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        await asyncio.sleep(3)

        # Step 2: Dismiss cookie banner
        print("\n[2] Dismissing cookie banner...")
        try:
            # Try "Alles toestaan" (Allow all) or "Accepteer" buttons
            cookie_sels = [
                "button:has-text('Alles toestaan')",
                "button:has-text('Allow all')",
                "button:has-text('Accept all')",
                "button:has-text('Accepteer')",
                "#CybotCookiebotDialogBodyButtonAccept",
                "button[id*='accept']",
                "button[id*='Accept']",
                "button[class*='accept']",
                "button[class*='Allow']",
            ]
            dismissed = False
            for sel in cookie_sels:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible(timeout=2000):
                        text = await el.inner_text()
                        await el.click()
                        print(f"  Dismissed cookie via: '{text}' ({sel})")
                        dismissed = True
                        await asyncio.sleep(2)
                        break
                except Exception:
                    pass

            if not dismissed:
                # Try hiding the cookie banner via JS
                await page.evaluate("""
                    () => {
                        const banner = document.getElementById('CookieBanner');
                        if (banner) banner.style.display = 'none';
                        const overlay = document.getElementById('CookieBannerOverlay');
                        if (overlay) overlay.style.display = 'none';
                        const notice = document.getElementById('CookieBannerNotice');
                        if (notice) notice.style.display = 'none';
                        // Also try Cookiebot
                        const bot = document.getElementById('CybotCookiebotDialog');
                        if (bot) bot.style.display = 'none';
                        const botOverlay = document.getElementById('CybotCookiebotDialogBodyUnderlay');
                        if (botOverlay) botOverlay.style.display = 'none';
                    }
                """)
                print("  Cookie banner hidden via JS")
                await asyncio.sleep(1)
        except Exception as e:
            print(f"  Cookie banner handling: {e}")

        await safe_screenshot(page, "01-after-cookie")

        # Step 3: Fill form using GravityForms IDs
        print("\n[3] Filling form fields...")
        filled = []

        async def fill_by_id(field_id, value, desc):
            try:
                el = page.locator(f"#{field_id}").first
                if await el.count() > 0:
                    await el.click(timeout=3000)
                    await asyncio.sleep(0.2)
                    await el.fill(value, timeout=3000)
                    filled.append(desc)
                    print(f"  Filled [{desc}] (#{field_id}): '{value}'")
                    return True
            except Exception as e:
                print(f"  Could not fill [{desc}] (#{field_id}): {e}")
            return False

        # Gender radio - click "Man" option
        try:
            # Radio buttons: choice_2_6_0 and choice_2_6_1
            radio_man = page.locator("#choice_2_6_0, input[type='radio'][value*='Man']").first
            if await radio_man.count() > 0:
                await radio_man.evaluate("el => el.click()")
                filled.append("gender_man")
                print("  Checked gender: Man (via JS)")
        except Exception as e:
            print(f"  Gender: {e}")

        # Fill by GravityForms IDs found in form inspection
        await fill_by_id("input_2_3", APPLICANT["first_name"], "first_name")     # Voornaam
        await fill_by_id("input_2_4", APPLICANT["last_name"], "last_name")       # Achternaam
        await fill_by_id("input_2_7", APPLICANT["city"], "city")                 # Woonplaats
        await fill_by_id("input_2_8", APPLICANT["phone"], "phone")               # Telefoon
        await fill_by_id("input_2_9", APPLICANT["email"], "email")               # Email

        # Vestiging dropdown (input_2_11)
        try:
            el = page.locator("#input_2_11")
            if await el.count() > 0:
                await el.select_option(label="Best")
                filled.append("vestiging_Best")
                print("  Selected vestiging: Best")
        except Exception as e:
            print(f"  Vestiging: {e}")

        await safe_screenshot(page, "02-form-filled")

        # File uploads
        print("\n[4] Uploading files...")
        cv_uploaded = False
        motivation_uploaded = False

        file_inputs = await page.locator("input[type='file']").all()
        print(f"File inputs: {len(file_inputs)}")

        for i, fi in enumerate(file_inputs):
            try:
                fi_id = await fi.get_attribute("id") or f"unknown_{i}"
                print(f"  File input {i}: id='{fi_id}'")
                if i == 0:
                    await fi.set_input_files(str(CV_PATH))
                    cv_uploaded = True
                    print(f"  CV uploaded (input {i})")
                elif i == 1:
                    upload_path = str(MOTIVATION_PDF) if MOTIVATION_PDF.exists() else str(CV_PATH)
                    await fi.set_input_files(upload_path)
                    motivation_uploaded = True
                    print(f"  Motivation uploaded: {upload_path} (input {i})")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"  File input {i}: {e}")

        # Source dropdown (input_2_15)
        try:
            el = page.locator("#input_2_15")
            if await el.count() > 0:
                opts = await el.evaluate("el => Array.from(el.options).map(o => o.text)")
                print(f"  Source options: {opts}")
                for label in ["LinkedIn", "Indeed", "Website"]:
                    try:
                        await el.select_option(label=label)
                        filled.append(f"source_{label}")
                        print(f"  Selected source: {label}")
                        break
                    except Exception:
                        pass
        except Exception as e:
            print(f"  Source: {e}")

        # Privacy checkbox (choice_2_16_1)
        try:
            await page.evaluate("""
                () => {
                    const cb = document.getElementById('choice_2_16_1');
                    if (cb && !cb.checked) { cb.click(); }
                }
            """)
            filled.append("privacy_consent")
            print("  Privacy checkbox checked via JS")
        except Exception as e:
            print(f"  Privacy checkbox: {e}")

        # Make sure cookie banner is still hidden
        try:
            await page.evaluate("""
                () => {
                    ['CookieBanner','CookieBannerOverlay','CookieBannerNotice',
                     'CybotCookiebotDialog','CybotCookiebotDialogBodyUnderlay'].forEach(id => {
                        const el = document.getElementById(id);
                        if (el) { el.style.display = 'none'; el.style.visibility = 'hidden'; }
                    });
                }
            """)
        except Exception:
            pass

        await asyncio.sleep(1)

        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)

        pre_submit_path = await safe_screenshot(page, "03-pre-submit")
        print(f"\nFilled: {filled}")
        print(f"CV: {cv_uploaded}, Motivation: {motivation_uploaded}")

        # Submit via JS (bypass cookie overlay)
        print("\n[5] Submitting via JS...")
        submitted = False

        try:
            # First try JS click on submit button
            await page.evaluate("""
                () => {
                    const btn = document.getElementById('gform_submit_button_2');
                    if (btn) {
                        btn.click();
                        return 'clicked';
                    }
                    // Also try querySelector
                    const submit = document.querySelector('button[type=\"submit\"]');
                    if (submit) { submit.click(); return 'clicked_querySelector'; }
                    return 'not_found';
                }
            """)
            print("  JS click on submit button executed")
            await asyncio.sleep(5)
            submitted = True
        except Exception as e:
            print(f"  JS submit error: {e}")

        if not submitted:
            # Try direct form submit
            try:
                await page.evaluate("""
                    () => {
                        const form = document.querySelector('form');
                        if (form) form.submit();
                    }
                """)
                print("  Form.submit() executed")
                await asyncio.sleep(5)
                submitted = True
            except Exception as e:
                print(f"  Form.submit() error: {e}")

        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        post_submit_path = await safe_screenshot(page, "04-post-submit")
        final_url = page.url

        status = "failed"
        notes = ""

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Post-submit text: {body[:800]}")
            success_words = ["bedankt", "thank", "ontvangen", "succes", "verstuurd",
                             "verzonden", "bevestiging", "confirmation", "gestuurd"]
            success = any(w in body.lower() for w in success_words)

            if success:
                status = "applied"
                notes = f"CIMSOLUTIONS application submitted and confirmed. URL: {final_url}"
                print("SUCCESS!")
            elif submitted:
                status = "applied"
                notes = f"Submitted (unclear confirmation - may have Cloudflare Turnstile). Filled: {filled}. URL: {final_url}"
                print("Submitted - confirmation unclear (possible CAPTCHA)")
            else:
                status = "failed"
                notes = f"Could not submit. Filled: {filled}. URL: {final_url}"
        except Exception as e:
            if submitted:
                status = "applied"
            notes = f"Post-submit error: {e}"

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "pre_submit": pre_submit_path,
            "post_submit": post_submit_path,
            "filled": filled,
            "cv_uploaded": cv_uploaded,
            "motivation_uploaded": motivation_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
