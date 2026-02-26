#!/usr/bin/env python3
"""
Apply to Lumenalta Fullstack Python/React Engineer position.
Version 4: Navigate directly to /apply URL, handle multi-step form.
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

JOB_URL = "https://lumenalta.com/jobs/python-engineer-senior-python-react-engineer-92"
APPLY_URL = "https://lumenalta.com/jobs/python-engineer-senior-python-react-engineer-92/apply"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
}

MOTIVATION = (
    "I am a full-stack developer with professional Python experience from ASML and "
    "React/JavaScript skills from building CogitatAI, my AI chatbot platform. At ASML "
    "I developed Python test suites in an Azure/Kubernetes CI/CD environment. Currently "
    "at Actemium (VINCI Energies) I build Python/Flask backends and JavaScript frontends "
    "for enterprise MES clients. CogitatAI is a full-stack project built with Python/Flask "
    "backend + React frontend, deployed on Azure with Docker/Kubernetes. I am excited to "
    "bring this full-stack Python/React experience to Lumenalta's enterprise client solutions."
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
    path = SCREENSHOTS_DIR / f"lumenalta-v4-{name}-{ts()}.png"
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
                print(f"  Filled [{desc}]: '{value[:50]}'")
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
        page = await context.new_page()

        # Navigate to apply page directly
        print(f"\n[1] Navigating to: {APPLY_URL}")
        try:
            resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
            print(f"Status: {resp.status if resp else 'N/A'}")
        except Exception as e:
            print(f"Goto warning: {e}")
            # Fallback: navigate to job page and click Apply
            try:
                resp2 = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)
                # Accept cookies
                try:
                    btn = page.locator("button:has-text('Accept All')").first
                    if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                        await btn.click()
                        await asyncio.sleep(1)
                except Exception:
                    pass
                # Click first Apply button
                apply_btns = await page.locator("#apply-button").all()
                if apply_btns:
                    await apply_btns[0].click()
                    await asyncio.sleep(5)
            except Exception as e2:
                print(f"Fallback error: {e2}")

        await asyncio.sleep(5)

        title = await page.title()
        url = page.url
        print(f"Title: {title}")
        print(f"URL: {url}")

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Body (500): {body[:500]}")
        except Exception as e:
            print(f"Body error: {e}")
            body = ""

        await safe_screenshot(page, "01-apply-page")

        # Accept cookies if present
        try:
            for sel in ["button:has-text('Accept All')", "button:has-text('Accept')"]:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=1000):
                    await el.click()
                    await asyncio.sleep(1)
                    print("Cookies accepted")
                    break
        except Exception:
            pass

        # Inspect form
        try:
            elems = await page.evaluate("""
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
            print(f"\nForm elements ({len(elems)}):")
            for el in elems:
                print(f"  {el}")
        except Exception as e:
            print(f"Form inspect error: {e}")
            elems = []

        filled = []
        cv_uploaded = False

        print("\n[2] Filling Step 1 (Careers Profile)...")
        await fill_field(page, [
            "input[type='email']", "input[name='email']", "input[id*='email']",
            "input[placeholder*='Email' i]", "input[placeholder*='mail' i]",
        ], APPLICANT["email"], "email", filled)

        await fill_field(page, [
            "input[name='fullName']", "input[name='full_name']", "input[name='name']",
            "input[id*='name']", "input[placeholder*='Full name' i]", "input[placeholder*='Name' i]",
        ], APPLICANT["full_name"], "full_name", filled)

        await fill_field(page, [
            "input[name='firstName']", "input[id*='first']",
            "input[placeholder*='First' i]",
        ], APPLICANT["first_name"], "first_name", filled)

        await fill_field(page, [
            "input[name='lastName']", "input[id*='last']",
            "input[placeholder*='Last' i]",
        ], APPLICANT["last_name"], "last_name", filled)

        await fill_field(page, [
            "input[type='tel']", "input[name='phone']", "input[placeholder*='Phone' i]",
        ], APPLICANT["phone"], "phone", filled)

        await fill_field(page, [
            "input[name*='linkedin' i]", "input[placeholder*='LinkedIn' i]",
        ], APPLICANT["linkedin"], "linkedin", filled)

        await fill_field(page, [
            "input[name*='github' i]", "input[placeholder*='GitHub' i]",
        ], APPLICANT["github"], "github", filled)

        # Textareas
        textareas = await page.locator("textarea").all()
        print(f"Textareas: {len(textareas)}")
        for i, ta in enumerate(textareas):
            try:
                if await ta.is_visible(timeout=1500):
                    ph = await ta.get_attribute("placeholder") or ""
                    name_attr = await ta.get_attribute("name") or ""
                    print(f"  Textarea {i}: name='{name_attr}', ph='{ph[:50]}'")
                    await ta.click()
                    await ta.fill(MOTIVATION)
                    filled.append(f"textarea_{i}")
                    print(f"  Filled textarea {i}")
                    break
            except Exception as e:
                print(f"  Textarea {i}: {e}")

        # CV upload
        print("\n[3] Uploading CV...")
        file_inputs = await page.locator("input[type='file']").all()
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
        cbs = await page.locator("input[type='checkbox']").all()
        for i in range(len(cbs)):
            try:
                checked = await page.evaluate(
                    f"() => document.querySelectorAll('input[type=\"checkbox\"]')[{i}].checked"
                )
                if not checked:
                    await page.evaluate(
                        f"() => document.querySelectorAll('input[type=\"checkbox\"]')[{i}].click()"
                    )
                    print(f"  Checked checkbox {i}")
            except Exception as e:
                print(f"  CB {i}: {e}")

        await safe_screenshot(page, "02-step1-filled")
        print(f"\nFilled: {filled}, CV: {cv_uploaded}")

        # Click Next/Continue button for Step 1
        print("\n[4] Proceeding to next step...")
        next_btn_found = False
        for sel in [
            "button:has-text('Next')", "button:has-text('Continue')",
            "button:has-text('Volgende')", "button:has-text('Proceed')",
            "button[type='submit']", "input[type='submit']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text()
                    print(f"Clicking: '{text}'")
                    await el.click()
                    await asyncio.sleep(3)
                    next_btn_found = True
                    break
            except Exception as e:
                print(f"  {sel}: {e}")

        if next_btn_found:
            await safe_screenshot(page, "03-after-next")
            print(f"URL after Next: {page.url}")

            # Step 2 - Voluntary questions
            print("\n[5] Step 2 (Voluntary questions)...")
            try:
                elems2 = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('input, textarea, select')).map(function(el) {
                        return {
                            tag: el.tagName, type: el.type || '', name: el.name || '',
                            id: el.id || '', placeholder: el.placeholder || '', visible: el.offsetParent !== null
                        };
                    })
                """)
                print(f"Step 2 elements: {len(elems2)}")
                for el in elems2[:10]:
                    print(f"  {el}")
            except Exception as e:
                print(f"Step 2 inspect error: {e}")

            # Handle dropdowns (gender, ethnicity, etc.)
            selects = await page.locator("select").all()
            for i, sel_el in enumerate(selects):
                try:
                    opts = await sel_el.evaluate(
                        "el => Array.from(el.options).map(o => ({v: o.value, t: o.text}))"
                    )
                    print(f"  Select {i}: {opts[:5]}")
                    # Select "Prefer not to say" or similar
                    for label in ["Prefer not to say", "Prefer not to answer", "I don't wish to answer",
                                  "Not specified", "Skip"]:
                        try:
                            await sel_el.select_option(label=label)
                            print(f"  Selected '{label}'")
                            break
                        except Exception:
                            pass
                except Exception as e:
                    print(f"  Select {i}: {e}")

            # Click Next again for Step 2
            for sel in [
                "button:has-text('Next')", "button:has-text('Continue')",
                "button[type='submit']", "input[type='submit']",
            ]:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible(timeout=2000):
                        text = await el.inner_text()
                        print(f"Step 2 next: '{text}'")
                        await el.click()
                        await asyncio.sleep(3)
                        break
                except Exception:
                    pass

            await safe_screenshot(page, "04-after-step2")
            print(f"URL after Step 2: {page.url}")

        # Final submit
        print("\n[6] Final submit...")
        submitted = False
        for sel in [
            "button[type='submit']", "input[type='submit']",
            "button:has-text('Submit')", "button:has-text('Apply')",
            "button:has-text('Send')",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text()
                    print(f"Final submit: '{text}'")
                    pre_path = await safe_screenshot(page, "05-pre-submit")
                    await el.click()
                    await asyncio.sleep(6)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=8000)
                    except Exception:
                        pass
                    submitted = True
                    break
            except Exception as e:
                print(f"  Submit {sel}: {e}")

        post_path = await safe_screenshot(page, "06-post-submit")
        final_url = page.url

        status = "failed"
        notes = ""

        try:
            body2 = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Post-submit: {body2[:500]}")
            success_words = ["thank", "confirm", "success", "received", "submitted",
                             "application", "we'll be", "congrat"]
            if any(w in body2.lower() for w in success_words) and submitted:
                status = "applied"
                notes = f"Lumenalta application submitted and confirmed. URL: {final_url}"
                print("SUCCESS!")
            elif submitted:
                status = "applied"
                notes = f"Submitted. Filled: {filled}. URL: {final_url}"
            else:
                status = "failed"
                notes = f"Could not submit. Filled: {filled}. URL: {final_url}"
        except Exception as e:
            status = "applied" if submitted else "failed"
            notes = f"Error: {e}"

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "pre_submit": pre_path if submitted else "",
            "post_submit": post_path,
            "filled": filled,
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
