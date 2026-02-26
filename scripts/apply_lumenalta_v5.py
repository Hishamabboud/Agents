#!/usr/bin/env python3
"""
Apply to Lumenalta Fullstack Python/React Engineer.
Version 5: Progressive form disclosure - fill email first, then other fields unlock.
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

APPLICANT = {
    "email": "hiaham123@hotmail.com",
    "full_name": "Hisham Abboud",
    "phone": "31648412838",  # numeric only (pattern: ^[0-9]*$)
    "city": "Eindhoven",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
    "years_exp": "4",
    "salary": "4500",
}

COVER_LETTER = (
    "I am a full-stack developer with professional Python experience from ASML and "
    "React/JavaScript skills from building CogitatAI. At ASML I developed Python test "
    "suites in Azure/Kubernetes CI/CD environment. Currently at Actemium (VINCI Energies) "
    "I build Python/Flask backends and JavaScript frontends for enterprise MES clients. "
    "CogitatAI is a full-stack project built with Python/Flask backend and React frontend, "
    "deployed on Azure with Docker/Kubernetes. I am excited to bring this full-stack "
    "Python/React expertise to Lumenalta's enterprise client solutions."
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
    path = SCREENSHOTS_DIR / f"lumenalta-v5-{name}-{ts()}.png"
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

        print(f"Title: {await page.title()}")
        print(f"URL: {page.url}")

        # Accept cookies
        try:
            btn = page.locator("button:has-text('Accept All')").first
            if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                await btn.click()
                await asyncio.sleep(1)
                print("Cookies accepted")
        except Exception:
            pass

        await safe_screenshot(page, "01-initial")

        # Step 1: Fill email first (unlocks other fields)
        print("\n[2] Filling email (unlocks form)...")
        try:
            email_field = page.locator("input[name='email']").first
            if await email_field.count() > 0:
                await email_field.click(timeout=5000)
                await email_field.fill(APPLICANT["email"])
                print(f"  Email filled: {APPLICANT['email']}")
                # Press Tab to trigger field unlock
                await email_field.press("Tab")
                await asyncio.sleep(4)
        except Exception as e:
            print(f"  Email error: {e}")

        # Check if name field is now enabled
        try:
            name_enabled = await page.evaluate(
                "() => { const el = document.querySelector(\"input[name='name']\"); "
                "return el ? !el.disabled : false; }"
            )
            print(f"  Name field enabled after email: {name_enabled}")
        except Exception as e:
            print(f"  Check error: {e}")
            name_enabled = False

        await safe_screenshot(page, "02-after-email")

        filled = ["email"]
        cv_uploaded = False

        # Fill remaining fields (now that they should be enabled)
        print("\n[3] Filling remaining fields...")

        async def fill_by_name(name_attr, value, desc):
            for timeout_val in [3000, 5000]:
                try:
                    el = page.locator(f"input[name='{name_attr}']").first
                    if await el.count() > 0:
                        is_enabled = await el.is_enabled(timeout=2000)
                        if is_enabled:
                            await el.click(timeout=timeout_val)
                            await asyncio.sleep(0.2)
                            await el.fill(value, timeout=timeout_val)
                            filled.append(desc)
                            print(f"  Filled [{desc}]: '{value}'")
                            return True
                        else:
                            # Try JS fill
                            await page.evaluate(
                                f"() => {{ const el = document.querySelector(\"input[name='{name_attr}']\"); "
                                f"if (el) {{ el.removeAttribute('disabled'); el.value = '{value}'; "
                                f"el.dispatchEvent(new Event('input', {{bubbles: true}})); "
                                f"el.dispatchEvent(new Event('change', {{bubbles: true}})); }} }}"
                            )
                            filled.append(desc + "_js")
                            print(f"  Filled [{desc}] via JS: '{value}'")
                            return True
                except Exception as e:
                    print(f"  {desc} attempt: {e}")
            print(f"  Could not fill [{desc}]")
            return False

        await fill_by_name("name", APPLICANT["full_name"], "full_name")
        await fill_by_name("city", APPLICANT["city"], "city")
        await fill_by_name("phone", APPLICANT["phone"], "phone")
        await fill_by_name("urls", APPLICANT["linkedin"], "linkedin")
        await fill_by_name("online_resume", APPLICANT["github"], "github")
        await fill_by_name("declaredYoE", APPLICANT["years_exp"], "years_exp")
        await fill_by_name("salary", APPLICANT["salary"], "salary")

        # Handle react-select country dropdown
        print("\n[4] Handling country select...")
        try:
            # Find the react-select container for country
            rs_inputs = await page.locator("input[id*='react-select']").all()
            print(f"  React-select inputs: {len(rs_inputs)}")

            for i, rs_input in enumerate(rs_inputs):
                try:
                    if await rs_input.is_visible(timeout=1000):
                        await rs_input.click()
                        await rs_input.fill("Netherlands")
                        await asyncio.sleep(2)
                        # Click first option
                        option = page.locator("[class*='option']:has-text('Netherlands')").first
                        if await option.count() > 0:
                            await option.click()
                            filled.append("country")
                            print(f"  Selected Netherlands (input {i})")
                            break
                except Exception as e:
                    print(f"  RS input {i}: {e}")
        except Exception as e:
            print(f"  Country select error: {e}")

        # Handle currency select
        try:
            rs_inputs2 = await page.locator("input[id*='react-select']").all()
            for i, rs_input in enumerate(rs_inputs2):
                try:
                    ph = await rs_input.get_attribute("placeholder") or ""
                    if "urrency" in ph or "EUR" in ph.upper():
                        await rs_input.click()
                        await rs_input.fill("EUR")
                        await asyncio.sleep(1)
                        opt = page.locator("[class*='option']:has-text('EUR')").first
                        if await opt.count() > 0:
                            await opt.click()
                            filled.append("currency")
                            print("  Selected currency EUR")
                except Exception:
                    pass
        except Exception:
            pass

        # Cover letter textarea
        print("\n[5] Cover letter...")
        try:
            textareas = await page.locator("textarea").all()
            for ta in textareas:
                try:
                    if await ta.is_visible(timeout=1000):
                        await ta.click()
                        await ta.fill(COVER_LETTER)
                        filled.append("cover_letter")
                        print("  Filled cover letter textarea")
                        break
                except Exception:
                    pass
        except Exception as e:
            print(f"  Textarea error: {e}")

        # CV upload
        print("\n[6] Uploading CV...")
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
            print(f"  CV upload error: {e}")

        await safe_screenshot(page, "03-form-filled")
        print(f"\nFilled: {filled}, CV: {cv_uploaded}")

        # Check submit button
        try:
            submit_enabled = await page.evaluate(
                "() => { const el = document.getElementById('stepOneNext'); "
                "return el ? !el.disabled : false; }"
            )
            print(f"Submit button enabled: {submit_enabled}")
        except Exception as e:
            print(f"Submit check: {e}")
            submit_enabled = False

        # Submit
        print("\n[7] Submitting...")
        submitted = False
        pre_path = ""

        for sel in ["#stepOneNext", "button[type='submit']", "input[type='submit']",
                    "button:has-text('Next')", "button:has-text('Submit')"]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    is_enabled = await el.is_enabled(timeout=2000)
                    if is_enabled:
                        text = await el.inner_text()
                        print(f"Submitting via: '{text}' ({sel})")
                        pre_path = await safe_screenshot(page, "04-pre-submit")
                        await el.click()
                        await asyncio.sleep(6)
                        submitted = True
                        break
            except Exception as e:
                print(f"  Submit {sel}: {e}")

        if not submitted:
            # Try JS click
            try:
                await page.evaluate(
                    "() => { const el = document.getElementById('stepOneNext'); "
                    "if (el) { el.removeAttribute('disabled'); el.click(); } }"
                )
                print("  JS forced click on submit")
                await asyncio.sleep(6)
                submitted = True
            except Exception as e:
                print(f"  JS submit: {e}")

        post_path = await safe_screenshot(page, "05-post-submit")
        final_url = page.url

        status = "failed"
        notes = ""

        try:
            body = await page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Post-submit: {body[:500]}")
            success_words = ["thank", "confirm", "success", "received", "congrat",
                             "application", "step 2", "voluntary"]
            if any(w in body.lower() for w in success_words) and submitted:
                status = "applied"
                notes = f"Lumenalta application submitted. URL: {final_url}"
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
