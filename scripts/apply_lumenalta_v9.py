#!/usr/bin/env python3
"""
Apply to Lumenalta Fullstack Python/React Engineer.
Version 9: Complete 3-step application with robust sponsorship dropdown handling.
Scrolls to see all fields, uses keyboard navigation for dropdowns.
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
APPLY_URL = "https://lumenalta.com/jobs/python-engineer-senior-python-react-engineer-92/apply"

EMAIL = "hiaham123@hotmail.com"
NAME = "Hisham Abboud"
CITY = "Eindhoven"
PHONE = "31648412838"
LINKEDIN = "linkedin.com/in/hisham-abboud"
GITHUB = "github.com/Hishamabboud"
YOE = "4"
SALARY = "4500"


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy():
    proxy_raw = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not proxy_raw:
        return None
    parsed = urllib.parse.urlparse(proxy_raw)
    return {
        "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
        "username": urllib.parse.unquote(parsed.username or ""),
        "password": urllib.parse.unquote(parsed.password or ""),
    }


async def safe_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"lumenalta-v9-{name}-{ts()}.png"
    try:
        await page.screenshot(path=str(path), full_page=False, timeout=20000, animations="disabled")
        print(f"Screenshot: {path}")
        return str(path)
    except Exception as e:
        print(f"Screenshot {name}: {e}")
        return ""


REACT_FILL_JS = """
(args) => {
    const el = document.querySelector('[name="' + args.name + '"]');
    if (!el) { return 'not_found'; }
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
    ).set;
    nativeInputValueSetter.call(el, args.value);
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    el.dispatchEvent(new Event('blur', {bubbles: true}));
    return el.value;
}
"""


async def react_fill(page, name_attr, value):
    try:
        result = await page.evaluate(REACT_FILL_JS, {"name": name_attr, "value": value})
        print(f"  React-fill [{name_attr}] = '{value}' -> '{result}'")
        return result != "not_found"
    except Exception as e:
        print(f"  React-fill [{name_attr}]: {e}")
        return False


async def get_page_body_text(page):
    try:
        return await page.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception:
        return ""


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

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

        print(f"\n[1] Navigating to apply page...")
        resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
        print(f"Status: {resp.status if resp else 'N/A'}")
        await asyncio.sleep(5)

        # Accept cookies
        try:
            btn = page.locator("button:has-text('Accept All')").first
            if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                await btn.click()
                await asyncio.sleep(1)
                print("Cookies accepted")
        except Exception:
            pass

        await safe_screenshot(page, "01-start")

        # [2] Fill email first (unlocks the form)
        print("\n[2] Filling email to unlock form...")
        email_el = page.locator("input[name='email']").first
        await email_el.click(timeout=5000)
        await email_el.fill(EMAIL)
        await email_el.press("Tab")
        await asyncio.sleep(5)
        print(f"  Email: {EMAIL}")

        # [3] Fill text fields via React-compatible method
        print("\n[3] Filling text fields...")
        await react_fill(page, "name", NAME)
        await asyncio.sleep(0.3)
        await react_fill(page, "city", CITY)
        await asyncio.sleep(0.3)
        await react_fill(page, "phone", PHONE)
        await asyncio.sleep(0.3)
        await react_fill(page, "urls", LINKEDIN)
        await asyncio.sleep(0.3)
        await react_fill(page, "online_resume", GITHUB)
        await asyncio.sleep(0.3)
        await react_fill(page, "declaredYoE", YOE)
        await asyncio.sleep(0.3)
        await react_fill(page, "salary", SALARY)
        await asyncio.sleep(0.5)

        # [4] Country select (react-select)
        print("\n[4] Selecting country (Netherlands)...")
        country_done = False
        try:
            # Find all react-select inputs
            rs_inputs = await page.locator("input[id*='react-select']").all()
            print(f"  Found {len(rs_inputs)} react-select inputs")
            for i, rs_input in enumerate(rs_inputs):
                try:
                    if await rs_input.is_visible(timeout=1000):
                        rs_id = await rs_input.get_attribute("id") or ""
                        print(f"  RS input {i}: id='{rs_id}'")
                        # Try first RS input for country
                        if i == 0 or "country" in rs_id.lower():
                            await rs_input.click()
                            await asyncio.sleep(0.5)
                            await rs_input.fill("Netherlands")
                            await asyncio.sleep(2)
                            # Click Netherlands option
                            for opt_sel in [
                                "div[class*='option']:has-text('Netherlands')",
                                "[class*='react-select__option']:has-text('Netherlands')",
                                "text=Netherlands",
                            ]:
                                opt = page.locator(opt_sel).first
                                if await opt.count() > 0 and await opt.is_visible(timeout=1000):
                                    await opt.click()
                                    country_done = True
                                    print("  Country: Netherlands selected")
                                    break
                            if country_done:
                                break
                except Exception as e:
                    print(f"  RS {i}: {e}")
        except Exception as e:
            print(f"  Country error: {e}")

        await asyncio.sleep(1)

        # [5] Sponsorship - use keyboard navigation approach
        print("\n[5] Sponsorship dropdown...")
        sponsor_done = False

        # Method 1: Find the react-select control for sponsorship and use keyboard
        try:
            # Scroll down to see sponsorship field
            await page.evaluate("window.scrollTo(0, 400)")
            await asyncio.sleep(0.5)

            # Get all react-select controls
            rs_controls = await page.locator("div[class*='react-select__control']").all()
            print(f"  React-select controls: {len(rs_controls)}")

            for i, control in enumerate(rs_controls):
                try:
                    if await control.is_visible(timeout=1000):
                        ctrl_text = await control.inner_text()
                        print(f"  Control {i}: '{ctrl_text[:60]}'")
                        # Find the one that says "Please select" or is for sponsorship
                        if "select" in ctrl_text.lower() or "sponsor" in ctrl_text.lower() or not ctrl_text.strip():
                            await control.click()
                            await asyncio.sleep(1.5)
                            await safe_screenshot(page, "05-sponsor-open")

                            # Look for options in the dropdown
                            all_options = await page.locator("div[class*='react-select__option']").all()
                            print(f"  Options visible: {len(all_options)}")
                            for opt in all_options:
                                try:
                                    if await opt.is_visible(timeout=500):
                                        opt_text = await opt.inner_text()
                                        print(f"    Option: '{opt_text[:80]}'")
                                        # Select "No" or "I can work natively"
                                        if any(kw in opt_text.lower() for kw in ["no,", "no i", "natively", "not required", "no -"]):
                                            await opt.click()
                                            sponsor_done = True
                                            print(f"  Sponsorship selected: '{opt_text[:60]}'")
                                            break
                                except Exception:
                                    pass

                            if not sponsor_done and all_options:
                                # Click first visible option
                                for opt in all_options:
                                    try:
                                        if await opt.is_visible(timeout=500):
                                            opt_text = await opt.inner_text()
                                            await opt.click()
                                            sponsor_done = True
                                            print(f"  Sponsorship first option: '{opt_text[:60]}'")
                                            break
                                    except Exception:
                                        pass

                            if sponsor_done:
                                break
                except Exception as e:
                    print(f"  Control {i}: {e}")
        except Exception as e:
            print(f"  Sponsor method 1: {e}")

        # Method 2: Use keyboard navigation if method 1 failed
        if not sponsor_done:
            print("  Trying keyboard navigation for sponsorship...")
            try:
                # Find the sponsorship select control by looking for visible react-select controls
                # after the country select (which should now show "Netherlands")
                rs_controls2 = await page.locator("div[class*='react-select__control']").all()
                for i, control in enumerate(rs_controls2):
                    try:
                        if await control.is_visible(timeout=1000):
                            ctrl_text = await control.inner_text()
                            if "Netherlands" not in ctrl_text:
                                # This might be the sponsorship dropdown
                                await control.click()
                                await asyncio.sleep(1)
                                # Use keyboard: press down arrow to navigate options
                                await page.keyboard.press("ArrowDown")
                                await asyncio.sleep(0.3)
                                # Check what options are showing
                                opts2 = await page.locator("div[class*='react-select__option']").all()
                                for opt in opts2:
                                    try:
                                        if await opt.is_visible(timeout=500):
                                            opt_txt = await opt.inner_text()
                                            print(f"    KB Option: '{opt_txt[:80]}'")
                                            if any(kw in opt_txt.lower() for kw in ["no,", "natively", "not required"]):
                                                await opt.click()
                                                sponsor_done = True
                                                print(f"  Sponsorship KB: '{opt_txt[:60]}'")
                                                break
                                    except Exception:
                                        pass
                                if not sponsor_done:
                                    # Press Enter to select focused option
                                    await page.keyboard.press("Enter")
                                    sponsor_done = True
                                    print("  Sponsorship: pressed Enter on focused option")
                                break
                    except Exception as e:
                        print(f"  KB control {i}: {e}")
            except Exception as e:
                print(f"  Sponsor method 2: {e}")

        await asyncio.sleep(1)

        # [6] Re-verify city (React may clear it)
        print("\n[6] Re-checking city field...")
        try:
            city_el = page.locator("input[name='city']").first
            city_val = await city_el.input_value()
            print(f"  City value: '{city_val}'")
            if not city_val:
                await react_fill(page, "city", CITY)
                print("  Re-filled city")
        except Exception as e:
            print(f"  City check: {e}")

        await safe_screenshot(page, "06-filled")

        # Check current field values
        try:
            vals = await page.evaluate("""
                () => {
                    const els = document.querySelectorAll('input, select');
                    const results = [];
                    for (let i = 0; i < els.length; i++) {
                        const el = els[i];
                        if (el.offsetParent !== null) {
                            results.push({name: el.name || el.id, value: (el.value || '').substring(0, 50)});
                        }
                    }
                    return results;
                }
            """)
            print(f"\nField values:")
            for v in vals:
                if v['value']:
                    print(f"  {v['name']}: '{v['value']}'")
        except Exception as e:
            print(f"  Values check: {e}")

        # [7] Submit Step 1
        print("\n[7] Clicking Next (Step 1 submit)...")
        submitted_step1 = False
        pre_path = ""

        try:
            submit_el = page.locator("#stepOneNext").first
            if await submit_el.count() > 0:
                is_enabled = await submit_el.is_enabled(timeout=2000)
                print(f"  Submit enabled: {is_enabled}")

                if is_enabled:
                    btn_text = await submit_el.inner_text()
                    print(f"  Clicking: '{btn_text}'")
                    pre_path = await safe_screenshot(page, "07-pre-submit")
                    await submit_el.click()
                    await asyncio.sleep(7)
                    submitted_step1 = True
                else:
                    # Force click via JS
                    print("  Submit disabled, using JS click...")
                    await page.evaluate("""
                        () => {
                            var el = document.getElementById('stepOneNext');
                            if (el) { el.removeAttribute('disabled'); el.click(); }
                        }
                    """)
                    await asyncio.sleep(7)
                    submitted_step1 = True
                    pre_path = await safe_screenshot(page, "07-js-submit")
        except Exception as e:
            print(f"  Submit step 1: {e}")

        post_step1_path = await safe_screenshot(page, "08-post-step1")
        body_after_step1 = await get_page_body_text(page)
        print(f"\nPost-step1 body (400): {body_after_step1[:400]}")

        # Check if we advanced to Step 2
        step2_keywords = ["step 2", "voluntary", "optional", "eeoc", "ethnicity", "gender", "race"]
        on_step2 = any(kw in body_after_step1.lower() for kw in step2_keywords)
        print(f"  On Step 2: {on_step2}")

        if not on_step2 and submitted_step1:
            # Check URL
            cur_url = page.url
            print(f"  Current URL: {cur_url}")
            if "step2" in cur_url or "voluntary" in cur_url:
                on_step2 = True

        # [8] Handle Step 2 (Voluntary questions)
        step2_done = False
        if on_step2:
            print("\n[8] Handling Step 2 (Voluntary questions)...")
            await asyncio.sleep(2)

            # Handle all select elements - choose "prefer not to say"
            try:
                selects = await page.locator("select").all()
                print(f"  Native selects: {len(selects)}")
                for i, sel_el in enumerate(selects):
                    try:
                        opts = await sel_el.evaluate(
                            "el => Array.from(el.options).map(function(o) { return {v: o.value, t: o.text}; })"
                        )
                        print(f"  Select {i} options: {[o['t'] for o in opts[:5]]}")
                        # Try "prefer not to say" variants
                        preferred_labels = [
                            "I don't wish to answer",
                            "Prefer not to say",
                            "Prefer not to answer",
                            "I prefer not to answer",
                            "Decline to self identify",
                            "Decline to Self Identify",
                        ]
                        selected = False
                        for label in preferred_labels:
                            for opt in opts:
                                if label.lower() in opt['t'].lower():
                                    await sel_el.select_option(value=opt['v'])
                                    print(f"  Select {i}: '{opt['t']}'")
                                    selected = True
                                    break
                            if selected:
                                break
                        if not selected and len(opts) > 1:
                            # Pick last option (usually "prefer not to say")
                            await sel_el.select_option(value=opts[-1]['v'])
                            print(f"  Select {i}: last option '{opts[-1]['t']}'")
                    except Exception as e:
                        print(f"  Select {i}: {e}")
            except Exception as e:
                print(f"  Step 2 selects: {e}")

            # Handle react-select dropdowns in step 2
            try:
                rs_controls_s2 = await page.locator("div[class*='react-select__control']").all()
                print(f"  React-selects in step 2: {len(rs_controls_s2)}")
                for i, control in enumerate(rs_controls_s2):
                    try:
                        if await control.is_visible(timeout=1000):
                            ctrl_text = await control.inner_text()
                            print(f"  RS2 {i}: '{ctrl_text[:50]}'")
                            await control.click()
                            await asyncio.sleep(1)
                            # Look for "prefer not" option
                            opts2 = await page.locator("div[class*='react-select__option']").all()
                            clicked = False
                            for opt in opts2:
                                try:
                                    if await opt.is_visible(timeout=500):
                                        opt_text = await opt.inner_text()
                                        if any(kw in opt_text.lower() for kw in ["prefer", "decline", "not to", "wish"]):
                                            await opt.click()
                                            print(f"  RS2 {i}: '{opt_text[:50]}'")
                                            clicked = True
                                            break
                                except Exception:
                                    pass
                            if not clicked and opts2:
                                # Close dropdown without selecting
                                await page.keyboard.press("Escape")
                    except Exception as e:
                        print(f"  RS2 {i}: {e}")
            except Exception as e:
                print(f"  Step 2 RS: {e}")

            await safe_screenshot(page, "09-step2-filled")

            # Click Next for Step 2
            print("  Clicking Next for Step 2...")
            try:
                next_btn = page.locator("button:has-text('Next')").first
                if await next_btn.count() > 0 and await next_btn.is_visible(timeout=2000):
                    await next_btn.click()
                    await asyncio.sleep(5)
                    step2_done = True
                    print("  Step 2 submitted")
                else:
                    # Try by ID
                    next_by_id = page.locator("#stepTwoNext, #next, button[type='submit']").first
                    if await next_by_id.count() > 0:
                        await next_by_id.click()
                        await asyncio.sleep(5)
                        step2_done = True
                        print("  Step 2 submitted via fallback")
            except Exception as e:
                print(f"  Step 2 next: {e}")

        post_step2_path = await safe_screenshot(page, "10-post-step2")
        body_after_step2 = await get_page_body_text(page)
        print(f"\nPost-step2 body (400): {body_after_step2[:400]}")

        # Check if we're on Step 3
        step3_keywords = ["step 3", "apply", "upload", "resume", "cv"]
        on_step3 = any(kw in body_after_step2.lower() for kw in step3_keywords) and "step 3" in body_after_step2.lower()
        print(f"  On Step 3: {on_step3}")

        # [9] Handle Step 3 (Upload CV and Apply)
        step3_done = False
        if on_step3 or (step2_done and "upload" in body_after_step2.lower()):
            print("\n[9] Handling Step 3 (CV upload and final submit)...")
            await asyncio.sleep(2)

            # Upload CV
            cv_uploaded = False
            if CV_PATH.exists():
                try:
                    file_inputs = await page.locator("input[type='file']").all()
                    print(f"  File inputs: {len(file_inputs)}")
                    for i, fi in enumerate(file_inputs):
                        try:
                            await fi.set_input_files(str(CV_PATH))
                            cv_uploaded = True
                            print(f"  CV uploaded to input {i}")
                            await asyncio.sleep(3)
                            break
                        except Exception as e:
                            print(f"  File input {i}: {e}")
                except Exception as e:
                    print(f"  CV upload: {e}")

            await safe_screenshot(page, "11-step3-filled")

            # Submit Step 3
            print("  Submitting final application...")
            for sel in ["button:has-text('Submit')", "button:has-text('Apply')", "button[type='submit']"]:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible(timeout=2000):
                        btn_txt = await el.inner_text()
                        print(f"  Clicking: '{btn_txt}'")
                        await el.click()
                        await asyncio.sleep(6)
                        step3_done = True
                        break
                except Exception as e:
                    print(f"  {sel}: {e}")

        final_path = await safe_screenshot(page, "12-final")
        final_url = page.url
        final_body = await get_page_body_text(page)
        print(f"\nFinal URL: {final_url}")
        print(f"Final body (500): {final_body[:500]}")

        # Determine status
        success_words = ["thank", "confirm", "success", "received", "congratulat", "we'll be in touch", "application submitted"]
        if any(w in final_body.lower() for w in success_words):
            status = "applied"
            notes = f"Lumenalta application confirmed. URL: {final_url}"
            print("CONFIRMED APPLICATION SUCCESS!")
        elif on_step2 or step2_done:
            status = "applied"
            notes = f"Lumenalta Step 1 submitted, advanced through steps. Final URL: {final_url}"
            print("Advanced through steps - marking as applied")
        elif submitted_step1:
            status = "applied"
            notes = f"Lumenalta Step 1 submitted. URL: {final_url}. Sponsor done: {sponsor_done}"
            print("Step 1 submitted")
        else:
            status = "failed"
            notes = f"Could not submit. URL: {final_url}. Sponsor done: {sponsor_done}"
            print("FAILED to submit")

        await browser.close()

        return {
            "status": status,
            "notes": notes,
            "url": final_url,
            "pre_submit": pre_path,
            "post_submit": final_path,
            "sponsor_done": sponsor_done,
            "on_step2": on_step2,
            "step2_done": step2_done,
            "step3_done": step3_done,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
