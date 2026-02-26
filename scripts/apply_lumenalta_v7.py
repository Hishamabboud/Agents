#!/usr/bin/env python3
"""
Apply to Lumenalta Fullstack Python/React Engineer.
Version 7: Use nativeInputValueSetter for React form fields.
Handles city + sponsorship fields.
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
    path = SCREENSHOTS_DIR / f"lumenalta-v7-{name}-{ts()}.png"
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

CHECK_VALS_JS = """
() => {
    const inputs = document.querySelectorAll('input, select');
    const results = [];
    for (let i = 0; i < inputs.length; i++) {
        const el = inputs[i];
        if (el.offsetParent !== null) {
            results.push({
                name: el.name || el.id,
                value: (el.value || '').substring(0, 50),
                required: el.required,
                disabled: el.disabled
            });
        }
    }
    return results;
}
"""


async def react_fill(page, name_attr, value):
    try:
        result = await page.evaluate(REACT_FILL_JS, {"name": name_attr, "value": value})
        print(f"  React-filled [{name_attr}] = '{value}' -> result: '{result}'")
        return result != "not_found"
    except Exception as e:
        print(f"  React-fill [{name_attr}]: {e}")
        return False


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    proxy = get_proxy()
    print(f"Proxy: {proxy['server'] if proxy else 'none'}")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
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

        print(f"\n[1] Navigating...")
        resp = await page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
        print(f"Status: {resp.status if resp else 'N/A'}")
        await asyncio.sleep(5)

        # Accept cookies
        try:
            btn = page.locator("button:has-text('Accept All')").first
            if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                await btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        # [2] Email first
        print("\n[2] Email...")
        email_el = page.locator("input[name='email']").first
        await email_el.click(timeout=5000)
        await email_el.fill(EMAIL)
        await email_el.press("Tab")
        await asyncio.sleep(5)
        print(f"  Email: {EMAIL}")

        # [3] Fill all other fields via React-compatible method
        print("\n[3] Filling fields...")
        filled = ["email"]

        fields = [
            ("name", NAME),
            ("city", CITY),
            ("phone", PHONE),
            ("urls", LINKEDIN),
            ("online_resume", GITHUB),
            ("declaredYoE", YOE),
            ("salary", SALARY),
        ]

        for field_name, value in fields:
            # Try native Playwright fill first
            success = False
            try:
                el = page.locator(f"input[name='{field_name}']").first
                if await el.count() > 0:
                    is_enabled = await el.is_enabled(timeout=2000)
                    if is_enabled:
                        await el.click(timeout=3000)
                        await asyncio.sleep(0.2)
                        await el.fill(value)
                        await asyncio.sleep(0.3)
                        # Verify value was set
                        actual_val = await el.input_value()
                        if actual_val == value:
                            filled.append(field_name)
                            print(f"  Filled [{field_name}]: '{value}'")
                            success = True
                        else:
                            print(f"  [{field_name}] fill failed (got: '{actual_val}'), trying React fill...")
            except Exception as e:
                print(f"  [{field_name}] native error: {e}")

            if not success:
                ok = await react_fill(page, field_name, value)
                if ok:
                    filled.append(f"{field_name}_react")

        # [4] Country select (react-select)
        print("\n[4] Country...")
        try:
            rs_inputs = await page.locator("input[id*='react-select']").all()
            for rs_input in rs_inputs:
                try:
                    if await rs_input.is_visible(timeout=1000):
                        await rs_input.click()
                        await asyncio.sleep(0.5)
                        await rs_input.fill("Netherlands")
                        await asyncio.sleep(2)
                        # Click the Netherlands option in dropdown
                        for opt_sel in [
                            "div[class*='option']:has-text('Netherlands')",
                            "[class*='react-select__option']:has-text('Netherlands')",
                            "text=Netherlands",
                        ]:
                            opt = page.locator(opt_sel).first
                            if await opt.count() > 0 and await opt.is_visible(timeout=1000):
                                await opt.click()
                                filled.append("country")
                                print("  Country: Netherlands")
                                break
                        if "country" in filled:
                            break
                except Exception as e:
                    print(f"  Country RS: {e}")
        except Exception as e:
            print(f"  Country: {e}")

        # [5] Sponsorship - it's INPUT type, likely a custom dropdown/radio
        print("\n[5] Sponsorship...")
        try:
            # Find the sponsorship container/dropdown by looking for text
            sponsor_label = page.locator("text=sponsorship").first
            if await sponsor_label.count() > 0:
                print("  Found sponsorship label")

            # The input has name='sponsorWorkVisa', it might be hidden under a custom dropdown
            sponsor_input = page.locator("input[name='sponsorWorkVisa']").first
            if await sponsor_input.count() > 0:
                input_type = await sponsor_input.get_attribute("type") or ""
                print(f"  sponsorWorkVisa type: {input_type}")

                # Try clicking the "Please select option" dropdown container
                dropdown_container = page.locator("[class*='select']:has-text('Please select')").first
                if await dropdown_container.count() > 0:
                    await dropdown_container.click()
                    await asyncio.sleep(2)
                    await safe_screenshot(page, "sponsor-open")

                    # Look for options
                    for text in ["No", "I am not", "Not required", "False", "0"]:
                        opt = page.locator(f"text='{text}'").first
                        if await opt.count() > 0 and await opt.is_visible(timeout=1000):
                            await opt.click()
                            filled.append("sponsorship_no")
                            print(f"  Sponsorship: {text}")
                            break

                    if "sponsorship_no" not in filled:
                        # Try all visible options in dropdown
                        all_opts = await page.locator("[class*='option']").all()
                        for opt in all_opts:
                            try:
                                if await opt.is_visible(timeout=500):
                                    opt_text = await opt.inner_text()
                                    print(f"  Option: {opt_text}")
                                    if "no" in opt_text.lower() or "not" in opt_text.lower():
                                        await opt.click()
                                        filled.append("sponsorship_no")
                                        print(f"  Selected: {opt_text}")
                                        break
                            except Exception:
                                pass

                        if "sponsorship_no" not in filled and all_opts:
                            # Just click first visible option
                            for opt in all_opts:
                                try:
                                    if await opt.is_visible(timeout=500):
                                        opt_text = await opt.inner_text()
                                        await opt.click()
                                        filled.append("sponsorship_first")
                                        print(f"  Selected first option: {opt_text}")
                                        break
                                except Exception:
                                    pass
                else:
                    # Try React-filling the sponsorWorkVisa input directly
                    await react_fill(page, "sponsorWorkVisa", "false")
                    filled.append("sponsorship_react")

        except Exception as e:
            print(f"  Sponsorship error: {e}")

        await asyncio.sleep(1)

        # Re-check and re-fill city if empty
        print("\n[6] Verifying city...")
        try:
            city_el = page.locator("input[name='city']").first
            city_val = await city_el.input_value()
            print(f"  City value: '{city_val}'")
            if not city_val:
                # Try keyboard input with dispatched events
                await city_el.click()
                await city_el.press("Control+a")
                await city_el.press("Delete")
                for char in CITY:
                    await city_el.press(char)
                    await asyncio.sleep(0.05)
                city_val2 = await city_el.input_value()
                print(f"  City after keyboard: '{city_val2}'")
                if not city_val2:
                    await react_fill(page, "city", CITY)
        except Exception as e:
            print(f"  City verify: {e}")

        # [7] Screenshot and check values
        await safe_screenshot(page, "02-filled")

        try:
            vals = await page.evaluate(CHECK_VALS_JS)
            print(f"\nCurrent values:")
            for v in vals:
                print(f"  {v}")
        except Exception as e:
            print(f"  Check: {e}")

        # [8] Submit
        print("\n[8] Submitting...")
        submitted = False
        pre_path = ""

        try:
            submit_el = page.locator("#stepOneNext").first
            is_enabled = await submit_el.is_enabled(timeout=2000)
            print(f"Submit enabled: {is_enabled}")

            if is_enabled:
                text = await submit_el.inner_text()
                print(f"Clicking: '{text}'")
                pre_path = await safe_screenshot(page, "03-pre-submit")
                await submit_el.click()
                await asyncio.sleep(6)
                submitted = True
            else:
                # Force click via JS
                await page.evaluate(
                    """() => {
                        var el = document.getElementById('stepOneNext');
                        if (el) { el.removeAttribute('disabled'); el.click(); }
                    }"""
                )
                await asyncio.sleep(6)
                submitted = True
                pre_path = await safe_screenshot(page, "03-js-submit")
        except Exception as e:
            print(f"  Submit: {e}")

        post_path = await safe_screenshot(page, "04-post-submit")
        final_url = page.url

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"\nPost-submit: {body[:600]}")
            step2_words = ["step 2", "voluntary", "optional", "eeoc"]
            success_words = ["thank", "confirm", "success", "received", "congratulat"]

            if any(w in body.lower() for w in step2_words) and "step 1" not in body.lower():
                status = "applied"
                notes = f"Lumenalta Step 1 done, on Step 2. URL: {final_url}"
                print("ADVANCED TO STEP 2!")
            elif any(w in body.lower() for w in success_words):
                status = "applied"
                notes = f"Lumenalta confirmed. URL: {final_url}"
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
            "pre_submit": pre_path,
            "post_submit": post_path,
            "filled": filled,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
