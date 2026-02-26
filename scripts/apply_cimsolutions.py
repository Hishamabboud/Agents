#!/usr/bin/env python3
"""
Apply to CIMSOLUTIONS Python Software Engineer position.
Uses the custom application form on cimsolutions.nl
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

JOB_URL = "https://www.cimsolutions.nl/vacatures/python-software-engineer/"
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
        or os.environ.get("HTTP_PROXY")
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
    path = SCREENSHOTS_DIR / f"cimsolutions-{name}-{ts()}.png"
    try:
        await page.add_style_tag(content="* { font-family: Arial, sans-serif !important; }")
    except Exception:
        pass
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

    if not MOTIVATION_PDF.exists():
        print(f"WARNING: Motivation PDF not found at {MOTIVATION_PDF}")
        # Will try to upload CV instead for motivation field

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
            # Try job page as fallback
            try:
                resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
                print(f"Fallback status: {resp.status if resp else 'N/A'}")
            except Exception as e2:
                print(f"Fallback failed: {e2}")

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        await asyncio.sleep(3)

        title = await page.title()
        url = page.url
        print(f"Title: {title}")
        print(f"URL: {url}")

        await safe_screenshot(page, "01-form-page")

        # Inspect form
        print("\n[2] Inspecting form...")
        try:
            elems = await page.evaluate("""
                () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    visible: el.offsetParent !== null,
                }))
            """)
            print(f"Elements ({len(elems)}):")
            for el in elems:
                print(f"  {el}")
        except Exception as e:
            print(f"Form inspect error: {e}")
            elems = []

        filled = []
        cv_uploaded = False
        motivation_uploaded = False

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

        # Fill gender radio (Man)
        print("\n[3] Filling form...")
        try:
            radio_man = page.locator("input[type='radio'][value*='Man'], input[type='radio'][value*='man'], input[type='radio'][id*='man']").first
            if await radio_man.count() > 0:
                await radio_man.check()
                filled.append("gender_man")
                print("  Checked gender: Man")
        except Exception as e:
            print(f"  Gender radio: {e}")

        await fill(
            ["input[name*='voornaam' i]", "input[id*='voornaam' i]",
             "input[name*='first' i]", "input[placeholder*='Voornaam' i]"],
            APPLICANT["first_name"], "first_name"
        )
        await fill(
            ["input[name*='achternaam' i]", "input[id*='achternaam' i]",
             "input[name*='last' i]", "input[placeholder*='Achternaam' i]"],
            APPLICANT["last_name"], "last_name"
        )
        await fill(
            ["input[name*='woonplaats' i]", "input[id*='woonplaats' i]",
             "input[name*='city' i]", "input[placeholder*='Woonplaats' i]",
             "input[placeholder*='City' i]"],
            APPLICANT["city"], "city"
        )
        await fill(
            ["input[type='tel']", "input[name*='telefoon' i]", "input[id*='telefoon' i]",
             "input[name*='phone' i]", "input[placeholder*='Telefoon' i]"],
            APPLICANT["phone"], "phone"
        )
        await fill(
            ["input[type='email']", "input[name*='email' i]", "input[id*='email' i]"],
            APPLICANT["email"], "email"
        )

        # Location dropdown
        print("\n[4] Handling dropdowns...")
        try:
            loc_select = page.locator("select[name*='vestiging' i], select[id*='vestiging' i], select").first
            if await loc_select.count() > 0:
                opts = await loc_select.evaluate(
                    "el => Array.from(el.options).map(o => ({v: o.value, t: o.text}))"
                )
                print(f"  Vestiging options: {opts}")
                # Try to select Best (closest to Eindhoven) or Amsterdam
                for label in ["Best", "Amsterdam"]:
                    try:
                        await loc_select.select_option(label=label)
                        filled.append(f"vestiging_{label}")
                        print(f"  Selected vestiging: {label}")
                        break
                    except Exception:
                        pass
        except Exception as e:
            print(f"  Vestiging select: {e}")

        # "Hoe ken je ons?" dropdown
        try:
            selects = await page.locator("select").all()
            for i, sel_el in enumerate(selects):
                try:
                    opts = await sel_el.evaluate(
                        "el => Array.from(el.options).map(o => ({v: o.value, t: o.text}))"
                    )
                    has_linkedin = any("linkedin" in o.get("t", "").lower() for o in opts)
                    if has_linkedin:
                        await sel_el.select_option(label="LinkedIn")
                        filled.append("source_linkedin")
                        print(f"  Selected source: LinkedIn")
                        break
                    elif any("indeed" in o.get("t", "").lower() for o in opts):
                        await sel_el.select_option(label="Indeed")
                        filled.append("source_indeed")
                        break
                except Exception:
                    pass
        except Exception as e:
            print(f"  Source dropdown: {e}")

        await safe_screenshot(page, "03-after-basic-fill")

        # File uploads
        print("\n[5] Uploading files...")
        file_inputs = await page.locator("input[type='file']").all()
        print(f"File inputs found: {len(file_inputs)}")

        for i, fi in enumerate(file_inputs):
            try:
                fi_name = await fi.get_attribute("name") or ""
                fi_id = await fi.get_attribute("id") or ""
                fi_accept = await fi.get_attribute("accept") or ""
                print(f"  File input {i}: name='{fi_name}', id='{fi_id}', accept='{fi_accept}'")

                # Determine which file to upload
                if "motivat" in fi_name.lower() or "motivat" in fi_id.lower() or "letter" in fi_name.lower():
                    # Motivation field - upload motivation PDF
                    upload_file = str(MOTIVATION_PDF) if MOTIVATION_PDF.exists() else str(CV_PATH)
                    await fi.set_input_files(upload_file)
                    motivation_uploaded = True
                    print(f"  Motivation uploaded: {upload_file}")
                elif i == 0:
                    # First file input - CV
                    await fi.set_input_files(str(CV_PATH))
                    cv_uploaded = True
                    print(f"  CV uploaded")
                elif i == 1:
                    # Second file input - motivation
                    upload_file = str(MOTIVATION_PDF) if MOTIVATION_PDF.exists() else str(CV_PATH)
                    await fi.set_input_files(upload_file)
                    motivation_uploaded = True
                    print(f"  Motivation uploaded: {upload_file}")

                await asyncio.sleep(1)
            except Exception as e:
                print(f"  File input {i}: {e}")

        # Privacy checkbox
        print("\n[6] Privacy checkbox...")
        cbs = await page.locator("input[type='checkbox']").all()
        for i, cb in enumerate(cbs):
            try:
                checked = await cb.is_checked()
                if not checked:
                    try:
                        await cb.check(timeout=5000)
                        filled.append(f"checkbox_{i}")
                        print(f"  Checked checkbox {i}")
                    except Exception:
                        # Try JS click
                        await page.evaluate(
                            f"() => document.querySelectorAll('input[type=\"checkbox\"]')[{i}].click()"
                        )
                        print(f"  Checked checkbox {i} via JS")
            except Exception as e:
                print(f"  Checkbox {i}: {e}")

        # Scroll and screenshot
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        except Exception:
            pass

        pre_submit_path = await safe_screenshot(page, "04-pre-submit")
        print(f"\nFilled: {filled}")
        print(f"CV uploaded: {cv_uploaded}, Motivation uploaded: {motivation_uploaded}")

        # Submit
        print("\n[7] Submitting...")
        submitted = False
        for sel in [
            "input[type='submit']",
            "button[type='submit']",
            "button:has-text('Verstuur')",
            "button:has-text('sollicitatie')",
            "input[value*='Verstuur']",
            "input[value*='Verzend']",
            "button:has-text('Submit')",
            "[class*='submit']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text() if el else ""
                    print(f"Submitting via: '{text}' ({sel})")
                    await el.scroll_into_view_if_needed()
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

        post_submit_path = await safe_screenshot(page, "05-post-submit")
        final_url = page.url

        status = "failed"
        notes = ""

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Post-submit text: {body[:600]}")
            success_words = ["bedankt", "thank", "ontvangen", "succes", "verstuurd",
                             "verzonden", "success", "bevestiging", "confirmation"]
            success = any(w in body.lower() for w in success_words)

            if success:
                status = "applied"
                notes = f"CIMSOLUTIONS Python Software Engineer application submitted and confirmed. URL: {final_url}"
                print("SUCCESS!")
            elif submitted:
                status = "applied"
                notes = f"Submitted (unclear confirmation). Filled: {filled}. URL: {final_url}"
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
