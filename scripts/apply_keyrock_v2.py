#!/usr/bin/env python3
"""
Apply to Keyrock Full Stack Engineer position.
Version 2: Uses urllib.parse for proper proxy credential handling.
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
    "city": "Eindhoven",
    "country": "Netherlands",
    "linkedin": "linkedin.com/in/hisham-abboud",
    "github": "github.com/Hishamabboud",
}

ANSWERS = {
    "why_keyrock": (
        "I want to join Keyrock because it sits at the intersection of cutting-edge technology "
        "and financial markets. Keyrock's mission of bringing liquidity and efficiency to digital "
        "asset markets resonates with my passion for building systems that have real-world impact. "
        "Regarding Keyrock's values: Teamwork - I have consistently delivered in collaborative "
        "environments, from cross-functional work at Actemium with industrial clients, to agile "
        "sprints at ASML. Ownership - I founded CogitatAI as a solo founder, taking full "
        "responsibility from architecture to deployment. Passion - I invest personal time building "
        "AI systems and exploring financial technology."
    ),
    "digital_assets": (
        "While my professional experience has focused on industrial and enterprise software, "
        "I have a strong personal interest in digital assets. I have studied algorithmic trading "
        "concepts, order book mechanics, and DeFi protocols. My background in building high-performance "
        "Python systems at ASML gives me a solid foundation for trading systems, and I am highly "
        "motivated to deepen this expertise at Keyrock."
    ),
    "compensation": "EUR 70,000 - 85,000 per year, depending on the full benefits package.",
    "how_learned": "LinkedIn",
}


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_proxy():
    proxy_url = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
        or ""
    )
    if not proxy_url:
        return None
    parsed = urllib.parse.urlparse(proxy_url)
    cfg = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
    if parsed.username:
        cfg["username"] = urllib.parse.unquote(parsed.username)
    if parsed.password:
        cfg["password"] = urllib.parse.unquote(parsed.password)
    return cfg


async def safe_screenshot(page, name):
    path = SCREENSHOTS_DIR / f"keyrock-v2-{name}-{ts()}.png"
    try:
        await page.add_style_tag(content="* { font-family: Arial, sans-serif !important; }")
    except Exception:
        pass
    for full_page in [False]:
        try:
            await page.screenshot(path=str(path), full_page=full_page, timeout=20000, animations="disabled")
            print(f"Screenshot: {path}")
            return str(path)
        except Exception as e:
            print(f"Screenshot {name} failed: {e}")
    return ""


async def fill_field(page, selectors, value, desc):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible(timeout=2000):
                await el.click(timeout=2000)
                await asyncio.sleep(0.2)
                await el.fill(value, timeout=3000)
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
    if proxy:
        print(f"Using proxy: {proxy['server']} (user: {proxy.get('username', '')[:20]}...)")
    else:
        print("No proxy")

    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
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

        async def block_slow(route):
            blocked = [
                "fullstory.com", "datadoghq.com", "sentry.io",
                "recaptcha.net", "gstatic.com", "cdn.ashbyprd.com",
            ]
            if any(b in route.request.url for b in blocked):
                await route.abort()
            elif route.request.resource_type == "font":
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_slow)
        page = await context.new_page()

        print(f"\n[1] Navigating to: {APPLICATION_URL}")
        try:
            resp = await page.goto(APPLICATION_URL, wait_until="commit", timeout=30000)
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
            print(f"Body (1000): {body[:1000]}")
        except Exception as e:
            print(f"Body error: {e}")
            body = ""

        if "407" in title or not title or url == APPLICATION_URL and not body.strip():
            print("ERROR: Got 407 or empty page - proxy auth issue")
            await safe_screenshot(page, "00-error")
            await browser.close()
            return {"status": "failed", "notes": "Proxy authentication failed (407). Cannot reach Ashby ATS."}

        await safe_screenshot(page, "01-job-page")

        # Look for Apply Now button
        print("\n[2] Looking for Apply button...")
        new_pages = []
        context.on("page", lambda pg: new_pages.append(pg))

        apply_sels = [
            "text=Apply now",
            "text=Apply Now",
            "button:has-text('Apply')",
            "a:has-text('Apply')",
            "[data-testid*='apply']",
        ]

        apply_clicked = False
        for sel in apply_sels:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text()
                    print(f"Found: '{text}' ({sel})")
                    await el.click()
                    await asyncio.sleep(4)
                    apply_clicked = True
                    break
            except Exception as e:
                pass

        # Check for new tab
        active_page = page
        if new_pages:
            print(f"New tab: {new_pages[0].url}")
            active_page = new_pages[0]
            await asyncio.sleep(4)

        after_url = active_page.url
        print(f"URL after apply: {after_url}")
        await safe_screenshot(active_page, "02-after-apply")

        # Inspect form
        print("\n[3] Form elements...")
        try:
            elems = await active_page.evaluate("""
                () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                    tag: el.tagName, type: el.type || '', name: el.name || '',
                    id: el.id || '', placeholder: el.placeholder || '',
                    label: (() => { const l = document.querySelector('label[for=\"' + el.id + '\"]'); return l ? l.innerText : ''; })(),
                    visible: el.offsetParent !== null,
                }))
            """)
            print(f"Elements ({len(elems)}):")
            for el in elems:
                print(f"  {el}")
        except Exception as e:
            print(f"Form inspect error: {e}")
            elems = []

        filled = []
        cv_uploaded = False

        # Fill standard fields
        print("\n[4] Filling form...")
        fields = [
            ("first_name", APPLICANT["first_name"], [
                "input[name='_systemfield_name']", "input[name='firstName']",
                "input[name='first_name']", "input[id*='first']",
                "input[placeholder*='First' i]",
            ]),
            ("last_name", APPLICANT["last_name"], [
                "input[name='lastName']", "input[name='last_name']",
                "input[id*='last']", "input[placeholder*='Last' i]",
            ]),
            ("full_name", APPLICANT["full_name"], [
                "input[name='name']", "input[placeholder*='Full name' i]",
                "input[placeholder*='Name' i]",
            ]),
            ("email", APPLICANT["email"], [
                "input[type='email']", "input[name='email']", "input[id*='email']",
            ]),
            ("phone", APPLICANT["phone"], [
                "input[type='tel']", "input[name='phone']", "input[id*='phone']",
                "input[placeholder*='Phone' i]",
            ]),
            ("linkedin", APPLICANT["linkedin"], [
                "input[name*='linkedin' i]", "input[id*='linkedin' i]",
                "input[placeholder*='LinkedIn' i]",
            ]),
        ]

        for desc, val, sels in fields:
            ok = await fill_field(active_page, sels, val, desc)
            if ok:
                filled.append(desc)

        # Fill textareas (cover letter / why keyrock)
        textareas = await active_page.locator("textarea").all()
        print(f"Textareas: {len(textareas)}")
        for i, ta in enumerate(textareas):
            try:
                if await ta.is_visible(timeout=1500):
                    placeholder = await ta.get_attribute("placeholder") or ""
                    label_text = await active_page.evaluate(
                        f"() => {{ const ta = document.querySelectorAll('textarea')[{i}]; "
                        f"const id = ta.id; const l = document.querySelector('label[for=\"' + id + '\"]'); "
                        f"return l ? l.innerText : ''; }}"
                    )
                    print(f"  Textarea {i}: placeholder='{placeholder}', label='{label_text}'")

                    # Choose appropriate answer
                    if any(k in (placeholder + label_text).lower() for k in ["why", "keyrock", "motivation", "cover"]):
                        await ta.click()
                        await ta.fill(ANSWERS["why_keyrock"])
                        filled.append(f"textarea_{i}_why")
                    elif any(k in (placeholder + label_text).lower() for k in ["digital", "asset", "crypto"]):
                        await ta.click()
                        await ta.fill(ANSWERS["digital_assets"])
                        filled.append(f"textarea_{i}_digital")
                    elif i == 0 and "textarea" not in str(filled):
                        await ta.click()
                        await ta.fill(ANSWERS["why_keyrock"])
                        filled.append(f"textarea_{i}")
            except Exception as e:
                print(f"  Textarea {i} error: {e}")

        # File upload (CV)
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

        # Handle dropdowns/selects
        selects = await active_page.locator("select").all()
        for i, sel_el in enumerate(selects):
            try:
                opts = await sel_el.evaluate("el => Array.from(el.options).map(o => ({v:o.value, t:o.text}))")
                print(f"  Select {i} options: {opts[:5]}")
                # Try to select "Other" or first non-empty option
                for label in ["LinkedIn", "Other", "Yes"]:
                    try:
                        await sel_el.select_option(label=label)
                        print(f"  Selected '{label}'")
                        break
                    except Exception:
                        pass
            except Exception as e:
                print(f"  Select {i}: {e}")

        # Checkboxes
        checkboxes = await active_page.locator("input[type='checkbox']").all()
        for i, cb in enumerate(checkboxes):
            try:
                if not await cb.is_checked():
                    # Use JS click to avoid intercept issues
                    await active_page.evaluate(
                        f"() => document.querySelectorAll('input[type=\"checkbox\"]')[{i}].click()"
                    )
                    print(f"  Checked checkbox {i} via JS")
            except Exception as e:
                print(f"  Checkbox {i}: {e}")

        # Scroll to bottom
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
        for sel in [
            "button[type='submit']", "input[type='submit']",
            "button:has-text('Submit application')", "button:has-text('Submit')",
            "button:has-text('Apply')", "button:has-text('Send')",
            "[data-testid='submit']",
        ]:
            try:
                el = active_page.locator(sel).first
                if await el.count() > 0 and await el.is_visible(timeout=2000):
                    text = await el.inner_text()
                    print(f"Submitting via: '{text}'")
                    await safe_screenshot(active_page, "04-pre-submit")
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

        await safe_screenshot(active_page, "05-post-submit")

        final_url = active_page.url
        status = "failed"
        notes = ""

        try:
            body = await active_page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"Post-submit text: {body[:600]}")
            success_words = ["thank", "confirm", "success", "received", "submitted",
                             "application", "we'll be", "review"]
            if any(w in body.lower() for w in success_words) and submitted:
                status = "applied"
                notes = f"Application submitted to Keyrock Full Stack Engineer. URL: {final_url}"
                print("SUCCESS!")
            elif submitted:
                status = "applied"
                notes = f"Submitted (unclear confirmation). Filled: {filled}. URL: {final_url}"
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
            "filled": filled,
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
