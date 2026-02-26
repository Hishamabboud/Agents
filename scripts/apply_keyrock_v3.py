#!/usr/bin/env python3
"""
Apply to Keyrock Full Stack Engineer position.
Version 3: Proper proxy parsing + don't block CDN needed by Ashby.
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
APPLICATION_URL = "https://jobs.ashbyhq.com/keyrock/13432bba-3821-4ca9-a994-9a13ba307fd2"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "full_name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
}

WHY_KEYROCK = (
    "I want to join Keyrock because it sits at the intersection of cutting-edge technology "
    "and financial markets. Keyrock's mission of bringing liquidity and efficiency to digital "
    "asset markets resonates with my passion for building systems that have real-world impact. "
    "Teamwork: I have delivered in collaborative environments at Actemium (VINCI Energies) and "
    "ASML. Ownership: I founded CogitatAI as a solo founder, taking full responsibility from "
    "architecture to deployment. Passion: I invest personal time building AI systems and "
    "exploring financial technology."
)

DIGITAL_ASSETS = (
    "While my professional experience focused on industrial and enterprise software, I have "
    "a strong personal interest in digital assets. I have studied algorithmic trading concepts, "
    "order book mechanics, and DeFi protocols. My background in high-performance Python systems "
    "(Locust/Pytest at ASML at scale) gives me a solid foundation for trading systems, and I am "
    "highly motivated to deepen this expertise at Keyrock."
)

COMPENSATION = "EUR 70,000 - 85,000 per year, open to discussion based on role scope."


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
    path = SCREENSHOTS_DIR / f"keyrock-v3-{name}-{ts()}.png"
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

        # Block only tracking/analytics (NOT cdn.ashbyprd.com which is needed)
        async def route_handler(route):
            blocked = ["fullstory.com", "datadoghq.com", "sentry.io", "recaptcha.net"]
            if any(b in route.request.url for b in blocked):
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", route_handler)
        page = await context.new_page()

        print(f"\n[1] Navigating to: {APPLICATION_URL}")
        try:
            resp = await page.goto(APPLICATION_URL, wait_until="domcontentloaded", timeout=30000)
            print(f"Status: {resp.status if resp else 'N/A'}")
        except Exception as e:
            print(f"Goto warning: {e}")

        await asyncio.sleep(8)

        title = await page.title()
        url = page.url
        print(f"Title: {title}")
        print(f"URL: {url}")

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Body ({len(body)} chars): {body[:400]}")
        except Exception as e:
            print(f"Body error: {e}")
            body = ""

        await safe_screenshot(page, "01-job-page")

        if not body or len(body) < 100:
            print("ERROR: Page body too short - JS not rendered")
            await browser.close()
            return {"status": "failed", "notes": "Page did not render properly"}

        # Look for Apply button
        print("\n[2] Looking for Apply button...")
        new_pages = []
        context.on("page", lambda pg: new_pages.append(pg))

        apply_clicked = False
        for sel in [
            "text=Apply now",
            "text=Apply Now",
            "button:has-text('Apply')",
            "a:has-text('Apply now')",
            "a[href*='apply']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text()
                    print(f"Found Apply: '{text}' ({sel})")
                    await el.click()
                    await asyncio.sleep(5)
                    apply_clicked = True
                    break
            except Exception:
                pass

        if not apply_clicked:
            print("No Apply button found by text, trying URL pattern...")
            try:
                apply_link = await page.evaluate("""
                    () => {
                        const links = Array.from(document.querySelectorAll('a'));
                        const btn = links.find(l => l.href.includes('apply') ||
                                                    l.textContent.toLowerCase().includes('apply'));
                        return btn ? btn.href : null;
                    }
                """)
                if apply_link:
                    print(f"Found apply link: {apply_link}")
                    await page.goto(apply_link, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(5)
            except Exception as e:
                print(f"Apply link error: {e}")

        # Check for new tab
        active_page = page
        if new_pages:
            print(f"New tab opened: {new_pages[0].url}")
            active_page = new_pages[0]
            await asyncio.sleep(4)

        after_url = active_page.url
        print(f"URL after apply: {after_url}")
        await safe_screenshot(active_page, "02-after-apply")

        # Inspect form elements
        print("\n[3] Inspecting form...")
        try:
            elems = await active_page.evaluate("""
                () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    visible: el.offsetParent !== null,
                }))
            """)
            print(f"Form elements ({len(elems)}):")
            for el in elems:
                print(f"  {el}")
        except Exception as e:
            print(f"Form inspect error: {e}")
            elems = []

        filled = []
        cv_uploaded = False

        # Fill fields
        print("\n[4] Filling form...")
        await fill_field(active_page, [
            "input[name='_systemfield_name']", "input[name='name']",
            "input[placeholder*='Full name' i]", "input[placeholder*='Name' i]",
        ], APPLICANT["full_name"], "full_name", filled)

        await fill_field(active_page, [
            "input[name='firstName']", "input[name='first_name']",
            "input[id*='first']", "input[placeholder*='First' i]",
        ], APPLICANT["first_name"], "first_name", filled)

        await fill_field(active_page, [
            "input[name='lastName']", "input[name='last_name']",
            "input[id*='last']", "input[placeholder*='Last' i]",
        ], APPLICANT["last_name"], "last_name", filled)

        await fill_field(active_page, [
            "input[type='email']", "input[name='email']", "input[id*='email']",
        ], APPLICANT["email"], "email", filled)

        await fill_field(active_page, [
            "input[type='tel']", "input[name='phone']", "input[id*='phone']",
            "input[placeholder*='Phone' i]",
        ], APPLICANT["phone"], "phone", filled)

        await fill_field(active_page, [
            "input[name*='linkedin' i]", "input[id*='linkedin' i]",
            "input[placeholder*='LinkedIn' i]",
        ], APPLICANT["linkedin"], "linkedin", filled)

        # Textareas
        textareas = await active_page.locator("textarea").all()
        print(f"Textareas found: {len(textareas)}")
        for i, ta in enumerate(textareas):
            try:
                if await ta.is_visible(timeout=1500):
                    ph = await ta.get_attribute("placeholder") or ""
                    name_attr = await ta.get_attribute("name") or ""
                    print(f"  Textarea {i}: name='{name_attr}', placeholder='{ph[:50]}'")

                    if any(k in (ph + name_attr).lower() for k in ["why", "keyrock", "cover", "letter"]):
                        content = WHY_KEYROCK
                    elif any(k in (ph + name_attr).lower() for k in ["digital", "asset", "crypto", "experience"]):
                        content = DIGITAL_ASSETS
                    elif any(k in (ph + name_attr).lower() for k in ["salary", "compensation"]):
                        content = COMPENSATION
                    else:
                        content = WHY_KEYROCK  # default

                    await ta.click()
                    await asyncio.sleep(0.2)
                    await ta.fill(content)
                    filled.append(f"textarea_{i}")
                    print(f"  Filled textarea {i}")
            except Exception as e:
                print(f"  Textarea {i}: {e}")

        # Handle selects
        selects = await active_page.locator("select").all()
        for i, sel_el in enumerate(selects):
            try:
                opts = await sel_el.evaluate(
                    "el => Array.from(el.options).map(o => ({v: o.value, t: o.text}))"
                )
                print(f"  Select {i} options: {opts[:5]}")
                # Try common answers
                for label in ["Yes", "Other", "LinkedIn", "I consent"]:
                    try:
                        await sel_el.select_option(label=label)
                        print(f"  Selected '{label}'")
                        break
                    except Exception:
                        pass
            except Exception as e:
                print(f"  Select {i}: {e}")

        # Checkboxes - use JS click to avoid label intercept
        cbs = await active_page.locator("input[type='checkbox']").all()
        print(f"Checkboxes: {len(cbs)}")
        for i in range(len(cbs)):
            try:
                checked = await active_page.evaluate(
                    f"() => document.querySelectorAll('input[type=\"checkbox\"]')[{i}].checked"
                )
                if not checked:
                    await active_page.evaluate(
                        f"() => document.querySelectorAll('input[type=\"checkbox\"]')[{i}].click()"
                    )
                    print(f"  Checked checkbox {i} via JS")
            except Exception as e:
                print(f"  Checkbox {i}: {e}")

        # CV upload
        print("\n[5] Uploading CV...")
        file_inputs = await active_page.locator("input[type='file']").all()
        print(f"File inputs: {len(file_inputs)}")
        for i, fi in enumerate(file_inputs):
            try:
                await fi.set_input_files(str(CV_PATH))
                cv_uploaded = True
                print(f"  CV uploaded to file input {i}")
                await asyncio.sleep(2)
                break
            except Exception as e:
                print(f"  File input {i}: {e}")

        # Scroll and screenshot
        try:
            await active_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        except Exception:
            pass

        await safe_screenshot(active_page, "03-form-filled")
        print(f"\nFilled: {filled}, CV: {cv_uploaded}")

        # Submit
        print("\n[6] Submitting...")
        submitted = False
        pre_submit_path = ""

        for sel in [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit application')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send')",
            "[data-testid='submit']",
        ]:
            try:
                el = active_page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text()
                    print(f"Submitting via: '{text}'")
                    pre_submit_path = await safe_screenshot(active_page, "04-pre-submit")
                    await el.click()
                    await asyncio.sleep(6)
                    try:
                        await active_page.wait_for_load_state("networkidle", timeout=8000)
                    except Exception:
                        pass
                    submitted = True
                    break
            except Exception as e:
                print(f"  Submit {sel}: {e}")

        post_submit_path = await safe_screenshot(active_page, "05-post-submit")
        final_url = active_page.url

        status = "failed"
        notes = ""

        try:
            body2 = await active_page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Post-submit text: {body2[:600]}")
            success_words = ["thank", "confirm", "success", "received", "submitted",
                             "application", "review", "hear from us"]
            success = any(w in body2.lower() for w in success_words)

            if success and submitted:
                status = "applied"
                notes = f"Keyrock Full Stack Engineer application submitted and confirmed. URL: {final_url}"
                print("SUCCESS: Application confirmed!")
            elif submitted:
                status = "applied"
                notes = f"Submitted (unclear confirmation). Filled: {filled}. URL: {final_url}"
                print("Submitted - confirmation unclear")
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
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
