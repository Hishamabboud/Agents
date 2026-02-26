#!/usr/bin/env python3
"""
Apply to Lumenalta Senior Python/React Engineer position - Final version
with proper proxy authentication for Playwright.
"""

import asyncio
import os
import json
from datetime import datetime
from urllib.parse import urlparse
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


def get_proxy_config():
    """Extract proxy configuration from environment."""
    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or \
                os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY")
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    config = {
        "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
    }
    if parsed.username:
        config["username"] = parsed.username
    if parsed.password:
        config["password"] = parsed.password
    return config


async def safe_ss(page, name):
    path = ss_path(name)
    try:
        await page.screenshot(path=path, timeout=20000, full_page=False)
        print(f"    [SS] {path}")
        return path
    except Exception as e:
        print(f"    [SS] {name} failed: {e}")
        return None


async def fill_field(page, value, selectors):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible():
                await el.fill(value)
                return True
        except Exception:
            continue
    return False


async def run():
    proxy_config = get_proxy_config()
    print(f"Proxy config: {proxy_config['server'] if proxy_config else 'None'}")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        }
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        browser = await p.chromium.launch(**launch_kwargs)

        context_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "ignore_https_errors": True,
        }

        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()
        page.set_default_timeout(30000)

        # Track API calls
        api_calls = []
        page.on("request", lambda r: api_calls.append(r.url) if any(
            x in r.url for x in ["apply", "form", "api", "job", "candidate"]
        ) else None)

        print(f"[1] Loading job page: {JOB_URL}")
        try:
            resp = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=40000)
            print(f"    Status: {resp.status if resp else 'N/A'}")
        except Exception as e:
            print(f"    Load warning: {e}")

        await asyncio.sleep(5)
        print(f"    URL: {page.url}")

        # Get page text
        try:
            page_text = await page.evaluate("() => document.body ? document.body.innerText : 'EMPTY'")
            print(f"    Page text (500 chars): {page_text[:500]}")
        except Exception as e:
            print(f"    Page text error: {e}")

        # Take screenshot
        await safe_ss(page, "01-job-page")

        # Save HTML
        try:
            content = await page.content()
            html_path = f"/home/user/Agents/output/screenshots/lumenalta-final-{timestamp}.html"
            with open(html_path, "w") as f:
                f.write(content)
            print(f"    HTML saved ({len(content)} bytes): {html_path}")
        except Exception as e:
            print(f"    HTML error: {e}")

        # Check apply button
        print("[2] Checking apply button...")
        try:
            btn_info = await page.evaluate("""
                () => {
                    const btn = document.getElementById('apply-button');
                    if (!btn) return {found: false};
                    return {
                        found: true,
                        dataHref: btn.getAttribute('data-href'),
                        text: btn.innerText,
                    };
                }
            """)
            print(f"    Apply button: {btn_info}")
        except Exception as e:
            print(f"    Button check error: {e}")
            btn_info = {"found": False}

        # Try to click and observe what happens
        print("[3] Clicking apply button...")
        new_pages_list = []
        context.on("page", lambda pg: new_pages_list.append(pg))

        try:
            btn = page.locator("#apply-button")
            if await btn.count() > 0:
                await btn.click()
                print("    Clicked #apply-button")
            else:
                btn2 = page.locator("button:has-text('Apply now')")
                if await btn2.count() > 0:
                    await btn2.click()
                    print("    Clicked 'Apply now' button")
                else:
                    # Find all buttons
                    btns = await page.evaluate("() => Array.from(document.querySelectorAll('button')).map(b => ({id:b.id, text:b.innerText.substring(0,30), type:b.type}))")
                    print(f"    All buttons on page: {btns}")
        except Exception as e:
            print(f"    Click error: {e}")

        await asyncio.sleep(4)

        # Check if new page opened (popup)
        active_page = page
        if new_pages_list:
            print(f"    New page opened: {new_pages_list[0].url}")
            active_page = new_pages_list[0]
            await asyncio.sleep(3)

        current_url = active_page.url
        print(f"    URL after click: {current_url}")

        # Check API calls
        if api_calls:
            print(f"    API calls seen: {api_calls[:5]}")

        await safe_ss(active_page, "02-after-click")

        # Save post-click HTML
        try:
            post_content = await active_page.content()
            post_html = f"/home/user/Agents/output/screenshots/lumenalta-post-click-{timestamp}.html"
            with open(post_html, "w") as f:
                f.write(post_content)
            print(f"    Post-click HTML: {post_html} ({len(post_content)} bytes)")
            fc = post_content.lower().count("<form")
            ic = post_content.lower().count("<input")
            print(f"    Forms: {fc}, Inputs: {ic}")
        except Exception as e:
            print(f"    Post-click HTML error: {e}")

        # Check live form elements
        form_count = await active_page.locator("form").count()
        input_count = await active_page.locator("input").count()
        print(f"    Live forms: {form_count}, inputs: {input_count}")

        filled = {}
        status = "skipped"

        if input_count > 0 or form_count > 0:
            print("[4] Filling form...")

            for fname, fval, sels in [
                ("first_name", APPLICANT["first_name"], [
                    "input[name='first_name']", "input[name='firstName']",
                    "input[placeholder*='First']", "input[id*='first']",
                    "input[autocomplete='given-name']",
                ]),
                ("last_name", APPLICANT["last_name"], [
                    "input[name='last_name']", "input[name='lastName']",
                    "input[placeholder*='Last']", "input[id*='last']",
                    "input[autocomplete='family-name']",
                ]),
                ("email", APPLICANT["email"], [
                    "input[type='email']", "input[name='email']",
                    "input[placeholder*='mail']", "input[placeholder*='Email']",
                    "input[autocomplete='email']",
                ]),
                ("phone", APPLICANT["phone"], [
                    "input[type='tel']", "input[name='phone']",
                    "input[placeholder*='Phone']", "input[placeholder*='phone']",
                ]),
                ("city", APPLICANT["city"], [
                    "input[name='city']", "input[placeholder*='City']",
                ]),
                ("linkedin", APPLICANT["linkedin"], [
                    "input[name*='linkedin']", "input[placeholder*='LinkedIn']",
                ]),
            ]:
                ok = await fill_field(active_page, fval, sels)
                if ok:
                    filled[fname] = fval
                    print(f"    Filled {fname}")

            # Motivation/cover letter
            for sel in ["textarea", "textarea[name*='cover']", "textarea[placeholder*='motivation']"]:
                try:
                    ta = active_page.locator(sel).first
                    if await ta.count() > 0 and await ta.is_visible():
                        await ta.fill(MOTIVATION)
                        print(f"    Filled textarea")
                        break
                except Exception:
                    continue

            # CV upload
            try:
                fu = active_page.locator("input[type='file']").first
                if await fu.count() > 0:
                    await fu.set_input_files(CV_PATH)
                    print("    Uploaded CV")
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"    CV upload error: {e}")

            await safe_ss(active_page, "03-form-filled")

            # Submit
            for sel in [
                "button[type='submit']", "input[type='submit']",
                "button:has-text('Submit')", "button:has-text('Apply')",
                "button:has-text('Send')", "[type='submit']",
            ]:
                try:
                    el = active_page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible():
                        text = await el.inner_text()
                        print(f"    Submitting via: '{text}'")
                        await safe_ss(active_page, "04-pre-submit")
                        await el.click()
                        await asyncio.sleep(5)
                        try:
                            await active_page.wait_for_load_state("networkidle", timeout=10000)
                        except Exception:
                            pass
                        await safe_ss(active_page, "05-after-submit")
                        pt = await active_page.evaluate("() => document.body.innerText.toLowerCase()")
                        found_kw = [kw for kw in ["thank you", "thanks", "success", "received", "submitted", "confirm"] if kw in pt]
                        if found_kw:
                            status = "applied"
                            print(f"    APPLIED! Confirmation: {found_kw}")
                        else:
                            status = "attempted"
                            print(f"    Submitted but no clear confirmation. Page: {pt[:300]}")
                        break
                except Exception as e:
                    print(f"    Submit error {sel}: {e}")
        else:
            print("[4] No form elements found after click.")
            # Try to read page text for more context
            try:
                page_text_after = await active_page.evaluate("() => document.body ? document.body.innerText : 'EMPTY'")
                print(f"    Page text: {page_text_after[:500]}")
            except Exception:
                pass

            await safe_ss(active_page, "03-no-form")
            status = "skipped"

        result = {
            "status": status,
            "final_url": active_page.url,
            "filled_fields": list(filled.keys()),
            "api_calls": api_calls[:10],
            "screenshots": {
                "01_job_page": ss_path("01-job-page"),
                "02_after_click": ss_path("02-after-click"),
                "03": ss_path("03-form-filled"),
                "04_pre_submit": ss_path("04-pre-submit"),
                "05_after_submit": ss_path("05-after-submit"),
            },
        }

        rp = f"/home/user/Agents/output/screenshots/lumenalta-final-result-{timestamp}.json"
        with open(rp, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nResult: {rp}")

        await browser.close()
        return result


if __name__ == "__main__":
    result = asyncio.run(run())
    print("\n=== FINAL RESULT ===")
    print(json.dumps(result, indent=2))
