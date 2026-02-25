#!/usr/bin/env python3
"""
Apply to Lumenalta Senior Python/React Engineer position - V2
Handles JS-heavy Next.js page with dynamic apply button.
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

MOTIVATION = (
    "I am a full-stack developer with professional Python experience from ASML and "
    "React/JavaScript skills from building CogitatAI, my AI chatbot platform. At ASML "
    "I developed Python test suites in an Azure/Kubernetes CI/CD environment. Currently "
    "at Actemium (VINCI Energies) I build Python/Flask backends and JavaScript frontends "
    "for enterprise MES clients. CogitatAI is a full-stack project built with Python/Flask "
    "backend + React frontend, deployed on Azure with Docker/Kubernetes, demonstrating "
    "end-to-end ownership from architecture through production monitoring. I am excited "
    "to bring this full-stack Python/React experience to Lumenalta's enterprise client solutions."
)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


def ss_path(name):
    return os.path.join(SCREENSHOTS_DIR, f"lumenalta-{name}-{timestamp}.png")


async def safe_ss(page, name, full=False):
    path = ss_path(name)
    for timeout in [15000, 5000]:
        try:
            await page.screenshot(path=path, timeout=timeout, full_page=full)
            print(f"    [SS] {path}")
            return path
        except Exception as e:
            print(f"    [SS] timeout={timeout} failed: {e}")
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
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--font-render-hinting=none",
                "--disable-font-subpixel-positioning",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = await context.new_page()

        # Intercept navigation to track any redirects
        navigated_urls = []

        def on_response(response):
            if response.status in [200, 301, 302]:
                navigated_urls.append(response.url)

        page.on("response", on_response)

        print(f"[1] Loading job page...")
        try:
            response = await page.goto(JOB_URL, wait_until="domcontentloaded", timeout=45000)
            print(f"    Status: {response.status if response else 'N/A'}")
        except Exception as e:
            print(f"    Load error (continuing): {e}")

        # Wait for JS to execute and populate dynamic content
        print("    Waiting for JS hydration...")
        await asyncio.sleep(5)

        current_url = page.url
        print(f"    URL: {current_url}")

        # Check if page has loaded
        try:
            page_text = await page.evaluate("() => document.body ? document.body.innerText : 'NO BODY'")
            print(f"    Page text (first 300): {page_text[:300]}")
        except Exception as e:
            print(f"    Could not get page text: {e}")

        await safe_ss(page, "01-job-page")

        # Check the apply button's data-href after JS execution
        print("[2] Checking apply button data-href after JS execution...")
        try:
            apply_href = await page.evaluate("""
                () => {
                    const btn = document.getElementById('apply-button');
                    if (!btn) return null;
                    return {
                        dataHref: btn.getAttribute('data-href'),
                        onclick: btn.getAttribute('onclick'),
                        innerHTML: btn.innerHTML.substring(0, 100)
                    };
                }
            """)
            print(f"    Apply button info: {apply_href}")
        except Exception as e:
            print(f"    Could not check apply button: {e}")
            apply_href = None

        # Also check all clickable elements with "apply" text
        try:
            all_apply = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('[id*="apply"], [class*="apply"], a[href*="apply"], button');
                    return Array.from(elements).slice(0, 10).map(el => ({
                        tag: el.tagName,
                        id: el.id,
                        href: el.href || el.getAttribute('href') || el.getAttribute('data-href'),
                        text: el.innerText ? el.innerText.substring(0, 50) : '',
                        type: el.type
                    }));
                }
            """)
            print(f"    Apply-related elements: {json.dumps(all_apply, indent=2)}")
        except Exception as e:
            print(f"    Could not enumerate apply elements: {e}")

        # Click the apply button and watch for navigation/popup
        print("[3] Clicking apply button...")
        new_page_url = None

        # Listen for new pages/popups
        new_pages = []
        context.on("page", lambda p: new_pages.append(p))

        try:
            apply_btn = page.locator("#apply-button")
            if await apply_btn.count() > 0:
                print("    Clicking #apply-button...")
                await apply_btn.click()
                await asyncio.sleep(4)
                print(f"    URL after click: {page.url}")
                print(f"    New pages/popups: {len(new_pages)}")
            else:
                # Try by text
                btn = page.locator("button:has-text('Apply now')").first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(4)
                    print(f"    URL after text-click: {page.url}")
        except Exception as e:
            print(f"    Click error: {e}")

        # Check if a new page/popup opened
        if new_pages:
            print(f"    New page opened: {new_pages[0].url}")
            page = new_pages[0]  # Switch to the new page
            await asyncio.sleep(3)
            print(f"    New page URL: {page.url}")

        # Check if URL changed
        if page.url != JOB_URL:
            print(f"    Navigated to: {page.url}")
        else:
            # Maybe an inline form appeared
            try:
                page_text_after = await page.evaluate("() => document.body.innerText")
                print(f"    Page text after click (first 500): {page_text_after[:500]}")
            except Exception:
                pass

        await safe_ss(page, "02-after-click")

        # Save current page HTML
        try:
            content = await page.content()
            html_path = f"/home/user/Agents/output/screenshots/lumenalta-after-click-{timestamp}.html"
            with open(html_path, "w") as f:
                f.write(content)
            print(f"    After-click HTML saved: {html_path}")
            # Check for form in this HTML
            form_count = content.lower().count("<form")
            input_count = content.lower().count("<input")
            print(f"    Forms in HTML: {form_count}, Inputs: {input_count}")
        except Exception as e:
            print(f"    HTML save error: {e}")

        # Check what navigated URLs we saw
        print(f"    All navigated URLs: {list(set(navigated_urls))[:10]}")

        # Check if there's now a form on the page
        form_count = await page.locator("form").count()
        input_count = await page.locator("input").count()
        print(f"    Live forms: {form_count}, inputs: {input_count}")

        # If no form, check for iframes
        iframe_count = await page.locator("iframe").count()
        print(f"    Iframes: {iframe_count}")
        if iframe_count > 0:
            try:
                iframes = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('iframe')).map(f => ({
                        src: f.src, id: f.id, name: f.name
                    }))
                """)
                print(f"    Iframe srcs: {json.dumps(iframes)}")
                # Try to navigate into iframe
                if iframes:
                    iframe_src = iframes[0].get("src", "")
                    if iframe_src and iframe_src.startswith("http"):
                        print(f"    Navigating to iframe src: {iframe_src}")
                        await page.goto(iframe_src, wait_until="domcontentloaded", timeout=30000)
                        await asyncio.sleep(3)
            except Exception as e:
                print(f"    Iframe check error: {e}")

        # ---- Try to fill form if visible ----
        print("[4] Attempting form fill...")
        filled = {}

        fields_config = [
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
                "input[placeholder*='mail']", "input[placeholder*='Email']",
            ]),
            ("phone", APPLICANT["phone"], [
                "input[type='tel']", "input[name='phone']",
                "input[placeholder*='hone']",
            ]),
            ("linkedin", APPLICANT["linkedin"], [
                "input[name*='linkedin']", "input[placeholder*='LinkedIn']",
                "input[placeholder*='linkedin']",
            ]),
            ("github", APPLICANT["github"], [
                "input[name*='github']", "input[placeholder*='GitHub']",
                "input[placeholder*='github']",
            ]),
        ]

        for fname, fval, sels in fields_config:
            ok = await fill_field(page, fval, sels)
            if ok:
                filled[fname] = fval
                print(f"    Filled {fname}: {fval}")

        # Motivation textarea
        for sel in ["textarea", "textarea[name*='cover']", "textarea[name*='message']"]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible():
                    await el.fill(MOTIVATION)
                    print(f"    Filled motivation textarea")
                    break
            except Exception:
                continue

        # CV upload
        for sel in ["input[type='file']"]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.set_input_files(CV_PATH)
                    print(f"    Uploaded CV")
                    await asyncio.sleep(2)
                    break
            except Exception as e:
                print(f"    CV upload error: {e}")

        await safe_ss(page, "03-form-filled")

        # Find and click submit
        print("[5] Finding submit button...")
        submit_el = None
        for sel in [
            "button[type='submit']", "input[type='submit']",
            "button:has-text('Submit')", "button:has-text('Apply')",
            "button:has-text('Send')", "[type='submit']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible():
                    text = await el.inner_text()
                    print(f"    Submit found: '{text}' via {sel}")
                    submit_el = el
                    break
            except Exception:
                continue

        await safe_ss(page, "04-pre-submit")

        status = "failed"
        final_url = page.url

        if submit_el:
            print("[6] Submitting...")
            try:
                await submit_el.click()
                await asyncio.sleep(4)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                await safe_ss(page, "05-after-submit")
                final_url = page.url

                page_text = await page.evaluate("() => document.body.innerText.toLowerCase()")
                found_kw = [kw for kw in ["thank you", "thanks", "success", "received", "submitted", "confirm"] if kw in page_text]
                if found_kw:
                    print(f"    CONFIRMED: {found_kw}")
                    status = "applied"
                else:
                    print(f"    No confirmation found. Page: {page_text[:300]}")
                    status = "attempted"
            except Exception as e:
                print(f"    Submit error: {e}")
        else:
            print("    No submit button found on current page.")
            try:
                page_text = await page.evaluate("() => document.body.innerText")
                print(f"    Current page text: {page_text[:500]}")
            except Exception:
                pass
            status = "skipped"

        result = {
            "status": status,
            "final_url": final_url,
            "filled": filled,
            "screenshots": {
                "01_job_page": ss_path("01-job-page"),
                "02_after_click": ss_path("02-after-click"),
                "03_form_filled": ss_path("03-form-filled"),
                "04_pre_submit": ss_path("04-pre-submit"),
                "05_after_submit": ss_path("05-after-submit"),
            },
        }

        result_path = f"/home/user/Agents/output/screenshots/lumenalta-result-{timestamp}.json"
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)

        await browser.close()
        return result


if __name__ == "__main__":
    result = asyncio.run(run())
    print("\n=== RESULT ===")
    print(json.dumps(result, indent=2))
