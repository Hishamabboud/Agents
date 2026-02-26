#!/usr/bin/env python3
"""
Apply to iO Digital .NET Developer position (Antwerpen campus).
Version 2: Proper proxy parsing, handle modal/form after clicking Solliciteer.
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

JOB_URL = "https://www.iodigital.com/nl/carriere/vacatures/net-developer-7"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "linkedin": "linkedin.com/in/hisham-abboud",
}

MOTIVATION = (
    "Als .NET developer met professionele ervaring bij Actemium (VINCI Energies) - waar ik "
    "dagelijks .NET/C# applicaties bouw voor Manufacturing Execution Systems - zie ik een "
    "uitstekende match met deze rol bij iO Digital.\n\n"
    "Mijn achtergrond omvat REST API ontwikkeling met ASP.NET, VB-naar-C# migratie bij Delta "
    "Electronics, Azure cloud-omgevingen via ASML-stage, en een BSc Software Engineering van "
    "Fontys Eindhoven. Ik werk graag in een agile team aan uitdagende digitale oplossingen voor "
    "diverse klanten en combineer technische diepgang met klantgerichte communicatie."
)


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy():
    proxy_raw = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
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
    path = SCREENSHOTS_DIR / f"iodigital-v2-{name}-{ts()}.png"
    try:
        await page.screenshot(path=str(path), full_page=False, timeout=20000, animations="disabled")
        print(f"Screenshot: {path}")
        return str(path)
    except Exception as e:
        print(f"Screenshot {name} failed: {e}")
        return ""


async def fill_field(page, selectors, value, desc, filled):
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

        new_pages = []
        context.on("page", lambda pg: new_pages.append(pg))

        page = await context.new_page()

        print(f"\n[1] Navigating to: {JOB_URL}")
        resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
        print(f"Status: {resp.status if resp else 'N/A'}")
        await asyncio.sleep(4)

        title = await page.title()
        print(f"Title: {title}")

        # Dismiss cookie banner
        print("[2] Dismiss cookies...")
        for sel in [
            "button:has-text('Alle cookies toestaan')",
            "button:has-text('Accepteer alles')",
            "button:has-text('Accept all')",
            "button:has-text('Alles accepteren')",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    await el.click()
                    await asyncio.sleep(2)
                    print(f"  Dismissed: {sel}")
                    break
            except Exception:
                pass

        await safe_screenshot(page, "01-job-page")

        # Click Solliciteer nu
        print("[3] Clicking Solliciteer nu...")
        btn = page.locator("button:has-text('Solliciteer nu')").first
        if await btn.count() > 0:
            await btn.click()
            await asyncio.sleep(5)
            print(f"  URL after click: {page.url}")
        else:
            print("  No Solliciteer nu button found")

        # Check for new page/tab
        active_page = page
        if new_pages:
            active_page = new_pages[-1]
            await asyncio.sleep(3)
            print(f"  New tab URL: {active_page.url}")

        await safe_screenshot(active_page, "02-after-solliciteer")

        # Check if a modal appeared
        try:
            modal = await active_page.evaluate("""
                () => {
                    const modals = document.querySelectorAll('[role="dialog"], .modal, [class*="modal"], [class*="overlay"]');
                    return Array.from(modals).map(m => ({class: m.className, visible: m.offsetParent !== null}));
                }
            """)
            print(f"Modals: {modal}")
        except Exception as e:
            print(f"Modal check: {e}")

        # Check form elements
        try:
            elems = await active_page.evaluate("""
                () => Array.from(document.querySelectorAll('input, textarea, select')).map(function(el) {
                    return {
                        tag: el.tagName,
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        placeholder: el.placeholder || '',
                        visible: el.offsetParent !== null
                    };
                })
            """)
            print(f"Form elements ({len(elems)}):")
            for el in elems:
                print(f"  {el}")
        except Exception as e:
            print(f"Form inspect error: {e}")
            elems = []

        filled = []
        cv_uploaded = False
        status = "failed"
        notes = ""

        if len(elems) > 0:
            print("\n[4] Filling form...")
            await fill_field(active_page, [
                "input[name='firstName']", "input[name='first_name']",
                "input[id*='first']", "input[placeholder*='First']",
                "input[placeholder*='Voornaam']",
            ], APPLICANT["first_name"], "first_name", filled)

            await fill_field(active_page, [
                "input[name='lastName']", "input[name='last_name']",
                "input[id*='last']", "input[placeholder*='Last']",
                "input[placeholder*='Achternaam']",
            ], APPLICANT["last_name"], "last_name", filled)

            await fill_field(active_page, [
                "input[type='email']", "input[name='email']", "input[id*='email']",
            ], APPLICANT["email"], "email", filled)

            await fill_field(active_page, [
                "input[type='tel']", "input[name='phone']", "input[id*='phone']",
                "input[placeholder*='Telefoon']", "input[placeholder*='Phone']",
            ], APPLICANT["phone"], "phone", filled)

            await fill_field(active_page, [
                "input[name*='linkedin']", "input[placeholder*='LinkedIn']",
            ], APPLICANT["linkedin"], "linkedin", filled)

            # Textareas
            textareas = await active_page.locator("textarea").all()
            for i, ta in enumerate(textareas):
                try:
                    if await ta.is_visible(timeout=1500):
                        await ta.click()
                        await ta.fill(MOTIVATION)
                        filled.append(f"textarea_{i}")
                        print(f"  Filled textarea {i}")
                        break
                except Exception:
                    pass

            # CV upload
            file_inputs = await active_page.locator("input[type='file']").all()
            print(f"File inputs: {len(file_inputs)}")
            for i, fi in enumerate(file_inputs):
                try:
                    await fi.set_input_files(str(CV_PATH))
                    cv_uploaded = True
                    print(f"  CV uploaded to input {i}")
                    await asyncio.sleep(2)
                    break
                except Exception as e:
                    print(f"  File input {i}: {e}")

            # Checkboxes
            try:
                cbs = await active_page.locator("input[type='checkbox']").all()
                for i in range(len(cbs)):
                    try:
                        checked = await active_page.evaluate(
                            f"() => document.querySelectorAll('input[type=\"checkbox\"]')[{i}].checked"
                        )
                        if not checked:
                            await active_page.evaluate(
                                f"() => document.querySelectorAll('input[type=\"checkbox\"]')[{i}].click()"
                            )
                            print(f"  Checked checkbox {i}")
                    except Exception:
                        pass
            except Exception as e:
                print(f"  Checkboxes: {e}")

            await safe_screenshot(active_page, "03-form-filled")
            print(f"\nFilled: {filled}, CV: {cv_uploaded}")

            # Submit
            print("\n[5] Submitting...")
            submitted = False
            for sel in [
                "button[type='submit']", "input[type='submit']",
                "button:has-text('Verstuur')", "button:has-text('Verzenden')",
                "button:has-text('Submit')", "button:has-text('Solliciteer')",
                "button:has-text('Send')",
            ]:
                try:
                    el = active_page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible(timeout=2000):
                        text = await el.inner_text()
                        print(f"Submitting: '{text}'")
                        await safe_screenshot(active_page, "04-pre-submit")
                        await el.click()
                        await asyncio.sleep(5)
                        submitted = True
                        break
                except Exception as e:
                    print(f"  Submit {sel}: {e}")

            post_path = await safe_screenshot(active_page, "05-post-submit")

            try:
                body = await active_page.evaluate(
                    "() => document.body ? document.body.innerText : ''"
                )
                print(f"Post-submit: {body[:400]}")
                success_words = ["bedankt", "thank", "ontvangen", "bevestiging", "success"]
                if any(w in body.lower() for w in success_words):
                    status = "applied"
                    notes = f"iO Digital .NET Developer application submitted and confirmed."
                elif submitted:
                    status = "applied"
                    notes = f"Submitted. Filled: {filled}. URL: {active_page.url}"
                else:
                    status = "failed"
                    notes = f"Could not submit. Filled: {filled}."
            except Exception as e:
                status = "applied" if submitted else "failed"
                notes = f"Error: {e}"

        else:
            # No form found - the application might be via LinkedIn or different mechanism
            body = await active_page.evaluate(
                "() => document.body ? document.body.innerText : ''"
            )
            print(f"No form found. Page body: {body[:500]}")

            # Try clicking "Solliciteer met Linkedin" - but we can't authenticate
            # Mark as skipped since form is not accessible
            status = "skipped"
            notes = "iO Digital Antwerpen .NET Developer - form not found after clicking Solliciteer nu. May require LinkedIn authentication or different flow."
            post_path = await safe_screenshot(active_page, "03-no-form")

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": active_page.url,
            "filled": filled,
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
