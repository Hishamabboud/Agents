#!/usr/bin/env python3
"""
Apply to Lumenalta Senior Python/React Engineer position - V3
Intercepts network to find the actual apply form URL, then navigates directly.
"""

import asyncio
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31648412838",
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
}

CV_PATH = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
JOB_URL = "https://lumenalta.com/jobs/python-engineer-senior-python-react-engineer-92"
APPLY_URL = "https://lumenalta.com/apply/python-engineer-senior-python-react-engineer-92"

MOTIVATION = (
    "I am a full-stack developer with professional Python experience from ASML and "
    "React/JavaScript skills from building CogitatAI, my AI chatbot platform. At ASML "
    "I developed Python test suites in an Azure/Kubernetes CI/CD environment. Currently "
    "at Actemium (VINCI Energies) I build Python/Flask backends and JavaScript frontends "
    "for enterprise MES clients. CogitatAI is a full-stack project built with Python/Flask "
    "backend + React frontend, deployed on Azure with Docker/Kubernetes. I am excited to "
    "bring this full-stack Python/React experience to Lumenalta's enterprise client solutions."
)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


def ss_path(name):
    return os.path.join(SCREENSHOTS_DIR, f"lumenalta-{name}-{timestamp}.png")


async def safe_ss(page, name):
    path = ss_path(name)
    try:
        # Use clip to avoid waiting for fonts
        await page.screenshot(
            path=path,
            timeout=20000,
            full_page=False,
            clip={"x": 0, "y": 0, "width": 1280, "height": 900},
        )
        print(f"    [SS] {path}")
        return path
    except Exception as e:
        print(f"    [SS] {name} failed: {e}")
        # Try saving a blank image marker
        try:
            import subprocess
            subprocess.run(["convert", "-size", "1280x900", "xc:white",
                           "-pointsize", "30", "-fill", "black",
                           "-draw", f"text 100,450 'Screenshot failed: {name}'",
                           path], timeout=5, capture_output=True)
        except Exception:
            # Create a tiny placeholder
            with open(path + ".txt", "w") as f:
                f.write(f"Screenshot failed: {name} at {timestamp}")
        return path


async def run():
    async with async_playwright() as p:
        # Try Firefox which may handle font loading differently
        browser = await p.firefox.launch(
            headless=True,
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        )
        page = await context.new_page()
        page.set_default_timeout(30000)

        # Track all XHR/fetch requests for API calls
        api_calls = []

        async def handle_request(request):
            if any(x in request.url for x in ["apply", "form", "api", "job", "candidate", "application"]):
                api_calls.append({"url": request.url, "method": request.method})

        page.on("request", handle_request)

        print(f"[1] Loading job page with Firefox...")
        try:
            await page.goto(JOB_URL, wait_until="load", timeout=40000)
            print(f"    Loaded successfully")
        except Exception as e:
            print(f"    Load warning: {e}")

        await asyncio.sleep(3)
        print(f"    URL: {page.url}")

        # Get page text
        try:
            page_text = await page.evaluate("() => document.body ? document.body.innerText : 'EMPTY'")
            print(f"    Page text: {page_text[:300]}")
        except Exception as e:
            print(f"    Page text error: {e}")

        # Take screenshot
        await safe_ss(page, "01-job-page")

        # Get the apply button data-href after JS hydration
        try:
            btn_info = await page.evaluate("""
                () => {
                    const btn = document.getElementById('apply-button');
                    if (!btn) return 'button not found';
                    return JSON.stringify({
                        dataHref: btn.getAttribute('data-href'),
                        text: btn.innerText,
                        disabled: btn.disabled
                    });
                }
            """)
            print(f"    Apply button info: {btn_info}")
        except Exception as e:
            print(f"    Button check error: {e}")

        # Click apply button
        print("[2] Clicking apply button...")
        try:
            btn = page.locator("#apply-button")
            if await btn.count() > 0:
                await btn.click()
                print("    Clicked #apply-button")
            else:
                btn = page.locator("button:has-text('Apply now')")
                if await btn.count() > 0:
                    await btn.click()
                    print("    Clicked 'Apply now' button")
        except Exception as e:
            print(f"    Click error: {e}")

        await asyncio.sleep(4)
        current_url = page.url
        print(f"    URL after click: {current_url}")

        # Check for form appearing inline
        form_count = await page.locator("form").count()
        input_count = await page.locator("input").count()
        print(f"    Forms: {form_count}, Inputs: {input_count}")

        # Log API calls observed
        if api_calls:
            print(f"    API calls: {json.dumps(api_calls[:10], indent=2)}")

        await safe_ss(page, "02-after-click")

        # Save HTML
        try:
            content = await page.content()
            html_path = f"/home/user/Agents/output/screenshots/lumenalta-v3-{timestamp}.html"
            with open(html_path, "w") as f:
                f.write(content)
            print(f"    HTML saved: {html_path} ({len(content)} bytes)")
        except Exception as e:
            print(f"    HTML save error: {e}")

        # If page changed, try filling form
        filled = {}
        status = "failed"

        if current_url != JOB_URL or form_count > 0 or input_count > 0:
            print("[3] Filling form...")

            # Name fields
            for fname, fval, sels in [
                ("first_name", APPLICANT["first_name"], [
                    "input[name='first_name']", "input[name='firstName']",
                    "input[placeholder*='First']", "input[id*='first']",
                ]),
                ("last_name", APPLICANT["last_name"], [
                    "input[name='last_name']", "input[name='lastName']",
                    "input[placeholder*='Last']", "input[id*='last']",
                ]),
                ("email", APPLICANT["email"], [
                    "input[type='email']", "input[name='email']",
                    "input[placeholder*='mail']",
                ]),
                ("phone", APPLICANT["phone"], [
                    "input[type='tel']", "input[name='phone']",
                    "input[placeholder*='Phone']",
                ]),
            ]:
                for sel in sels:
                    try:
                        el = page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            await el.fill(fval)
                            filled[fname] = fval
                            print(f"    Filled {fname}")
                            break
                    except Exception:
                        continue

            # Motivation
            try:
                ta = page.locator("textarea").first
                if await ta.count() > 0:
                    await ta.fill(MOTIVATION)
                    print("    Filled motivation")
            except Exception:
                pass

            # CV
            try:
                fu = page.locator("input[type='file']").first
                if await fu.count() > 0:
                    await fu.set_input_files(CV_PATH)
                    print("    Uploaded CV")
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"    CV upload error: {e}")

            await safe_ss(page, "03-form-filled")

            # Submit
            for sel in ["button[type='submit']", "button:has-text('Submit')", "button:has-text('Apply')"]:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible():
                        await safe_ss(page, "04-pre-submit")
                        await el.click()
                        await asyncio.sleep(4)
                        await safe_ss(page, "05-after-submit")
                        page_text = await page.evaluate("() => document.body.innerText.toLowerCase()")
                        if any(kw in page_text for kw in ["thank", "success", "received", "submitted"]):
                            status = "applied"
                            print(f"    APPLIED - confirmation found")
                        else:
                            status = "attempted"
                        break
                except Exception:
                    continue
        else:
            print("[3] No form found after click - page did not change")
            # Try navigating to common apply URL patterns
            apply_urls_to_try = [
                f"https://lumenalta.com/apply/python-engineer-senior-python-react-engineer-92",
                f"https://lumenalta.com/jobs/python-engineer-senior-python-react-engineer-92/apply",
            ]
            for try_url in apply_urls_to_try:
                print(f"    Trying: {try_url}")
                try:
                    resp = await page.goto(try_url, wait_until="load", timeout=20000)
                    await asyncio.sleep(3)
                    fc = await page.locator("form").count()
                    ic = await page.locator("input").count()
                    print(f"    Status: {resp.status if resp else 'N/A'}, Forms: {fc}, Inputs: {ic}")
                    if fc > 0 or ic > 0:
                        print(f"    Form found at {try_url}!")
                        break
                except Exception as e:
                    print(f"    Error: {e}")

            await safe_ss(page, "03-final-state")
            status = "skipped"

        result = {
            "status": status,
            "final_url": page.url,
            "filled": filled,
            "api_calls_seen": api_calls[:10],
            "screenshots": {
                "01_job_page": ss_path("01-job-page"),
                "02_after_click": ss_path("02-after-click"),
                "03": ss_path("03-form-filled"),
                "04_pre_submit": ss_path("04-pre-submit"),
                "05_after_submit": ss_path("05-after-submit"),
            },
        }

        result_path = f"/home/user/Agents/output/screenshots/lumenalta-v3-result-{timestamp}.json"
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)

        await browser.close()
        return result


if __name__ == "__main__":
    result = asyncio.run(run())
    print("\n=== RESULT ===")
    print(json.dumps(result, indent=2))
