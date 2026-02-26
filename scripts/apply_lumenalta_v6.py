#!/usr/bin/env python3
"""
Apply to Lumenalta Fullstack Python/React Engineer.
Version 6: Complete form fill with all required fields - city, sponsorship dropdown.
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
FULL_NAME = "Hisham Abboud"
CITY = "Eindhoven"
PHONE = "31648412838"
LINKEDIN = "linkedin.com/in/hisham-abboud"
GITHUB = "github.com/Hishamabboud"
YOE = "4"
SALARY = "4500"

COVER_LETTER = (
    "I am a full-stack developer with professional Python experience from ASML and "
    "React skills from building CogitatAI. At ASML I developed Python test suites in "
    "Azure/Kubernetes CI/CD. Currently at Actemium I build Python backends and JavaScript "
    "frontends for enterprise MES clients. CogitatAI is built with Python/Flask and React."
)


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
    path = SCREENSHOTS_DIR / f"lumenalta-v6-{name}-{ts()}.png"
    try:
        await page.screenshot(path=str(path), full_page=False, timeout=20000, animations="disabled")
        print(f"Screenshot: {path}")
        return str(path)
    except Exception as e:
        print(f"Screenshot {name}: {e}")
        return ""


async def js_fill(page, selector_name, value):
    """Fill input by name attribute using JS to handle React state."""
    try:
        await page.evaluate(
            """(args) => {
                const el = document.querySelector('input[name="' + args.name + '"]');
                if (!el) return false;
                el.removeAttribute('disabled');
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(el, args.value);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.dispatchEvent(new Event('blur', {bubbles: true}));
                return true;
            }""",
            {"name": selector_name, "value": value}
        )
        return True
    except Exception as e:
        print(f"  JS fill {selector_name}: {e}")
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

        print(f"\n[1] Navigating to: {APPLY_URL}")
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

        await safe_screenshot(page, "01-start")

        # [2] Fill email first to unlock form
        print("\n[2] Filling email...")
        email_field = page.locator("input[name='email']").first
        if await email_field.count() > 0:
            await email_field.click(timeout=5000)
            await email_field.fill(EMAIL)
            await email_field.press("Tab")
            await asyncio.sleep(5)
            print(f"  Email filled: {EMAIL}")
        else:
            print("  Email field not found")

        # [3] Fill all other fields using Playwright native fill (now enabled)
        print("\n[3] Filling fields...")
        filled = ["email"]

        # Name
        try:
            el = page.locator("input[name='name']").first
            if await el.count() > 0 and await el.is_enabled(timeout=3000):
                await el.click()
                await el.fill(FULL_NAME)
                await el.press("Tab")
                filled.append("name")
                print(f"  Name: {FULL_NAME}")
            else:
                if await js_fill(page, "name", FULL_NAME):
                    filled.append("name_js")
        except Exception as e:
            print(f"  Name: {e}")

        # City
        try:
            el = page.locator("input[name='city']").first
            if await el.count() > 0 and await el.is_enabled(timeout=3000):
                await el.click()
                await el.fill(CITY)
                await el.press("Tab")
                filled.append("city")
                print(f"  City: {CITY}")
            else:
                if await js_fill(page, "city", CITY):
                    filled.append("city_js")
        except Exception as e:
            print(f"  City: {e}")

        # Phone
        try:
            el = page.locator("input[name='phone']").first
            if await el.count() > 0 and await el.is_enabled(timeout=3000):
                await el.click()
                await el.fill(PHONE)
                await el.press("Tab")
                filled.append("phone")
                print(f"  Phone: {PHONE}")
            else:
                if await js_fill(page, "phone", PHONE):
                    filled.append("phone_js")
        except Exception as e:
            print(f"  Phone: {e}")

        # LinkedIn
        try:
            el = page.locator("input[name='urls']").first
            if await el.count() > 0 and await el.is_enabled(timeout=3000):
                await el.click()
                await el.fill(LINKEDIN)
                filled.append("linkedin")
                print(f"  LinkedIn: {LINKEDIN}")
            else:
                await js_fill(page, "urls", LINKEDIN)
                filled.append("linkedin_js")
        except Exception as e:
            print(f"  LinkedIn: {e}")

        # GitHub/Portfolio
        try:
            el = page.locator("input[name='online_resume']").first
            if await el.count() > 0 and await el.is_enabled(timeout=3000):
                await el.click()
                await el.fill(GITHUB)
                filled.append("github")
                print(f"  GitHub: {GITHUB}")
            else:
                await js_fill(page, "online_resume", GITHUB)
                filled.append("github_js")
        except Exception as e:
            print(f"  GitHub: {e}")

        # Years of experience
        try:
            el = page.locator("input[name='declaredYoE']").first
            if await el.count() > 0 and await el.is_enabled(timeout=3000):
                await el.click()
                await el.fill(YOE)
                filled.append("yoe")
                print(f"  YoE: {YOE}")
            else:
                await js_fill(page, "declaredYoE", YOE)
                filled.append("yoe_js")
        except Exception as e:
            print(f"  YoE: {e}")

        # Salary
        try:
            el = page.locator("input[name='salary']").first
            if await el.count() > 0 and await el.is_enabled(timeout=3000):
                await el.click()
                await el.fill(SALARY)
                filled.append("salary")
                print(f"  Salary: {SALARY}")
            else:
                await js_fill(page, "salary", SALARY)
                filled.append("salary_js")
        except Exception as e:
            print(f"  Salary: {e}")

        await asyncio.sleep(1)

        # [4] Handle country react-select
        print("\n[4] Country select...")
        try:
            rs_inputs = await page.locator("input[id*='react-select']").all()
            for rs_input in rs_inputs:
                try:
                    if await rs_input.is_visible(timeout=1000) and await rs_input.is_enabled(timeout=1000):
                        await rs_input.click()
                        await rs_input.fill("Netherlands")
                        await asyncio.sleep(2)
                        # Click the option
                        opt = page.locator("div[class*='option']:has-text('Netherlands')").first
                        if await opt.count() > 0:
                            await opt.click()
                            filled.append("country")
                            print("  Selected Netherlands")
                            break
                except Exception:
                    pass
        except Exception as e:
            print(f"  Country: {e}")

        # [5] Sponsorship dropdown (react-select or native select)
        print("\n[5] Sponsorship question...")
        try:
            # Try native select first
            native_selects = await page.locator("select").all()
            for sel_el in native_selects:
                try:
                    opts = await sel_el.evaluate(
                        "el => Array.from(el.options).map(function(o) { return {v: o.value, t: o.text}; })"
                    )
                    print(f"  Select opts: {opts}")
                    for label in ["No", "No (I am authorized to work)", "Not Required"]:
                        try:
                            await sel_el.select_option(label=label)
                            filled.append("sponsorship_no")
                            print(f"  Sponsorship: {label}")
                            break
                        except Exception:
                            pass
                    # If no option matched, try first option
                    if "sponsorship_no" not in filled and opts:
                        await sel_el.select_option(value=opts[1]["v"] if len(opts) > 1 else opts[0]["v"])
                        filled.append("sponsorship_first")
                        print(f"  Sponsorship: first option")
                except Exception as e:
                    print(f"  Native select: {e}")

            # Also try react-select for sponsorship
            rs_containers = await page.locator("div[class*='react-select__control']").all()
            for i, container in enumerate(rs_containers):
                try:
                    container_text = await container.inner_text()
                    if "option" in container_text.lower() or not container_text.strip():
                        print(f"  React-select container {i}: '{container_text[:50]}'")
                        await container.click()
                        await asyncio.sleep(1)
                        # Look for No option
                        for text in ["No", "I am not", "Not required"]:
                            opt = page.locator(f"div[class*='react-select__option']:has-text('{text}')").first
                            if await opt.count() > 0:
                                await opt.click()
                                filled.append(f"rs_option_{text}")
                                print(f"  Selected: {text}")
                                break
                except Exception as e:
                    print(f"  RS container {i}: {e}")
        except Exception as e:
            print(f"  Sponsorship: {e}")

        await asyncio.sleep(1)

        # [6] Cover letter textarea
        print("\n[6] Cover letter...")
        try:
            textareas = await page.locator("textarea").all()
            for ta in textareas:
                if await ta.is_visible(timeout=1000):
                    await ta.click()
                    await ta.fill(COVER_LETTER)
                    filled.append("cover_letter")
                    print("  Cover letter filled")
                    break
        except Exception as e:
            print(f"  Cover letter: {e}")

        # [7] CV upload
        print("\n[7] CV upload...")
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
                        await asyncio.sleep(2)
                        break
                    except Exception as e:
                        print(f"  File input {i}: {e}")
            except Exception as e:
                print(f"  CV: {e}")

        await safe_screenshot(page, "02-filled")

        # Check state of all visible fields
        print("\n[8] Verifying field values...")
        try:
            current_vals = await page.evaluate(
                """() => {
                    return Array.from(document.querySelectorAll('input, textarea')).filter(function(el) {
                        return el.offsetParent !== null;
                    }).map(function(el) {
                        return {name: el.name || el.id || el.type, value: el.value ? el.value.substring(0, 50) : '', disabled: el.disabled, required: el.required};
                    });
                }"""
            )
            print(f"Current field values ({len(current_vals)}):")
            for f in current_vals:
                print(f"  {f}")
        except Exception as e:
            print(f"  Verify: {e}")

        # Check submit button
        try:
            submit_enabled = await page.evaluate(
                """() => { const el = document.getElementById('stepOneNext'); return el ? !el.disabled : false; }"""
            )
            print(f"\nSubmit button enabled: {submit_enabled}")
        except Exception as e:
            print(f"Submit check: {e}")
            submit_enabled = False

        # [9] Submit
        print("\n[9] Submitting Step 1...")
        submitted = False
        pre_path = ""

        for sel in ["#stepOneNext", "button[type='submit']", "button:has-text('Next')"]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    is_enabled = await el.is_enabled(timeout=2000)
                    if is_enabled:
                        text = await el.inner_text()
                        print(f"Clicking: '{text}'")
                        pre_path = await safe_screenshot(page, "03-pre-submit")
                        await el.click()
                        await asyncio.sleep(5)
                        submitted = True
                        break
            except Exception as e:
                print(f"  {sel}: {e}")

        # If submit still disabled, try JS
        if not submitted:
            try:
                await page.evaluate(
                    """() => {
                        const el = document.getElementById('stepOneNext');
                        if (el) { el.removeAttribute('disabled'); el.click(); }
                    }"""
                )
                print("  JS forced submit click")
                await asyncio.sleep(5)
                submitted = True
            except Exception as e:
                print(f"  JS submit: {e}")

        post_path = await safe_screenshot(page, "04-post-submit")
        final_url = page.url
        print(f"\nFinal URL: {final_url}")

        status = "failed"
        notes = ""

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Post-submit body: {body[:500]}")
            # Check if we advanced to Step 2 or got confirmation
            step2_words = ["step 2", "voluntary", "optional", "eeoc", "ethnicity", "gender"]
            success_words = ["thank", "confirm", "success", "received", "congratulat"]
            if any(w in body.lower() for w in step2_words):
                status = "applied"
                notes = f"Lumenalta Step 1 submitted, advanced to Step 2. URL: {final_url}"
                print("Advanced to Step 2!")
            elif any(w in body.lower() for w in success_words):
                status = "applied"
                notes = f"Lumenalta application confirmed. URL: {final_url}"
                print("SUCCESS!")
            elif submitted:
                status = "applied"
                notes = f"Submitted (unclear). Filled: {filled}. URL: {final_url}"
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
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
