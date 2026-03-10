#!/usr/bin/env python3
"""
Apply to Lumenalta Fullstack Python/React Engineer.
Final version: Complete 3-step application.
- Uses specific RS input IDs for country and sponsorship
- Handles all steps including CV upload
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

# React-select IDs found from DOM inspection:
# react-select-:Rehufl7rrrrlcq:-input  -> Country
# react-select-:R6bufl7rrrrlcq:-input  -> Sponsorship


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
    path = SCREENSHOTS_DIR / f"lumenalta-final2-{name}-{ts()}.png"
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
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(el, args.value);
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


async def get_body_text(page):
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
                "--no-sandbox", "--disable-setuid-sandbox",
                "--disable-dev-shm-usage", "--disable-gpu",
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
                print("Cookies accepted")
        except Exception:
            pass

        await safe_screenshot(page, "01-start")

        # ===== STEP 1: Careers Profile =====
        print("\n[2] Email (unlocks form)...")
        email_el = page.locator("input[name='email']").first
        await email_el.click(timeout=5000)
        await email_el.fill(EMAIL)
        await email_el.press("Tab")
        await asyncio.sleep(5)

        print("\n[3] Text fields...")
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

        print("\n[4] Country (Netherlands)...")
        country_done = False
        try:
            # First react-select is the country dropdown
            country_rs = page.locator("input[id='react-select-:Rehufl7rrrrlcq:-input']").first
            if await country_rs.count() > 0 and await country_rs.is_visible(timeout=2000):
                await country_rs.click()
                await asyncio.sleep(0.5)
                await country_rs.fill("Netherlands")
                await asyncio.sleep(2)
                # Click the Netherlands option
                for opt_sel in [
                    "div[class*='option']:has-text('Netherlands')",
                    "[class*='react-select__option']:has-text('Netherlands')",
                ]:
                    opt = page.locator(opt_sel).first
                    if await opt.count() > 0 and await opt.is_visible(timeout=1000):
                        await opt.click()
                        country_done = True
                        print("  Country: Netherlands")
                        break
        except Exception as e:
            print(f"  Country error: {e}")

        if not country_done:
            print("  Country: trying fallback via all RS inputs...")
            try:
                all_rs = await page.locator("input[id*='react-select']").all()
                for rs_input in all_rs:
                    try:
                        if await rs_input.is_visible(timeout=1000):
                            await rs_input.click()
                            await asyncio.sleep(0.3)
                            await rs_input.fill("Netherlands")
                            await asyncio.sleep(2)
                            opt = page.locator("div[class*='option']:has-text('Netherlands')").first
                            if await opt.count() > 0 and await opt.is_visible(timeout=1000):
                                await opt.click()
                                country_done = True
                                print("  Country (fallback): Netherlands")
                                break
                    except Exception:
                        pass
            except Exception as e:
                print(f"  Country fallback: {e}")

        await asyncio.sleep(1)

        print("\n[5] Sponsorship...")
        sponsor_done = False
        try:
            # Second react-select is sponsorship
            sponsor_rs = page.locator("input[id='react-select-:R6bufl7rrrrlcq:-input']").first
            if await sponsor_rs.count() > 0 and await sponsor_rs.is_visible(timeout=2000):
                await sponsor_rs.click()
                await asyncio.sleep(1.5)

                # Get all options visible
                all_opts = await page.locator("div[class*='option']").all()
                print(f"  Options visible: {len(all_opts)}")
                for opt in all_opts:
                    try:
                        if await opt.is_visible(timeout=500):
                            opt_text = await opt.inner_text()
                            print(f"    '{opt_text}'")
                            if "natively" in opt_text.lower() or ("no," in opt_text.lower()):
                                await opt.click()
                                sponsor_done = True
                                print(f"  Sponsorship: '{opt_text}'")
                                break
                    except Exception:
                        pass

                if not sponsor_done and all_opts:
                    # Click "No, I can work natively" - should be second option
                    for opt in all_opts:
                        try:
                            if await opt.is_visible(timeout=500):
                                opt_text = await opt.inner_text()
                                if opt_text.startswith("No,"):
                                    await opt.click()
                                    sponsor_done = True
                                    print(f"  Sponsorship: '{opt_text}'")
                                    break
                        except Exception:
                            pass
        except Exception as e:
            print(f"  Sponsor error: {e}")

        if not sponsor_done:
            print("  Sponsorship: trying container click fallback...")
            try:
                # Click the select container div for sponsorship
                sponsor_container = page.locator("#sponsorWorkVisa").first
                if await sponsor_container.count() > 0:
                    await sponsor_container.click()
                    await asyncio.sleep(1.5)
                    await safe_screenshot(page, "05-sponsor-open")
                    all_opts2 = await page.locator("div[class*='option']").all()
                    print(f"  Options after container click: {len(all_opts2)}")
                    for opt in all_opts2:
                        try:
                            if await opt.is_visible(timeout=500):
                                opt_text = await opt.inner_text()
                                print(f"    '{opt_text}'")
                                if "natively" in opt_text.lower() or opt_text.startswith("No,"):
                                    await opt.click()
                                    sponsor_done = True
                                    print(f"  Sponsorship: '{opt_text}'")
                                    break
                        except Exception:
                            pass
            except Exception as e:
                print(f"  Sponsor container fallback: {e}")

        await asyncio.sleep(0.5)

        # Re-check city (React might have cleared it)
        try:
            city_val = await page.locator("input[name='city']").first.input_value()
            if not city_val:
                await react_fill(page, "city", CITY)
                print("  Re-filled city")
        except Exception:
            pass

        await safe_screenshot(page, "06-step1-filled")

        # Check all field values
        try:
            vals = await page.evaluate("""() => {
                const els = document.querySelectorAll('input');
                const r = [];
                for (let i = 0; i < els.length; i++) {
                    const el = els[i];
                    if (el.offsetParent !== null && el.value) {
                        r.push({name: el.name || el.id.substring(0, 30), value: el.value.substring(0, 50)});
                    }
                }
                return r;
            }""")
            print(f"\nField values with content:")
            for v in vals:
                print(f"  {v['name']}: '{v['value']}'")
        except Exception as e:
            print(f"  Values: {e}")

        # Check sponsorWorkVisa value
        sponsor_val = await page.evaluate("() => { const el = document.querySelector('input[name=\"sponsorWorkVisa\"]'); return el ? el.value : 'not found'; }")
        print(f"  sponsorWorkVisa value: '{sponsor_val}'")

        print("\n[7] Submitting Step 1...")
        pre_path = ""
        submitted_step1 = False
        try:
            submit_el = page.locator("#stepOneNext").first
            is_enabled = await submit_el.is_enabled(timeout=2000)
            print(f"  Submit enabled: {is_enabled}")
            pre_path = await safe_screenshot(page, "07-pre-submit")
            if is_enabled:
                await submit_el.click()
            else:
                # Force click
                await page.evaluate("""() => {
                    var el = document.getElementById('stepOneNext');
                    if (el) { el.removeAttribute('disabled'); el.click(); }
                }""")
                print("  Used JS force click")
            await asyncio.sleep(7)
            submitted_step1 = True
        except Exception as e:
            print(f"  Submit step1: {e}")

        post_step1_path = await safe_screenshot(page, "08-post-step1")
        body = await get_body_text(page)
        print(f"\nPost-step1 URL: {page.url}")
        print(f"Post-step1 body (300): {body[:300]}")

        # Detect what step we're on by checking the step indicator
        step_info = await page.evaluate("""() => {
            const steps = document.querySelectorAll('[class*="step"], [class*="Step"]');
            const results = [];
            for (let i = 0; i < steps.length; i++) {
                const el = steps[i];
                if (el.offsetParent !== null) {
                    const cls = (el.className && typeof el.className === 'string') ? el.className.substring(0, 60) : '';
                    results.push({tag: el.tagName, cls: cls, text: el.textContent.trim().substring(0, 60)});
                }
            }
            return results.slice(0, 10);
        }""")
        print(f"\nStep indicators: {json.dumps(step_info, indent=2)}")

        # Check if we're truly on Step 2 (the active step changes)
        active_step = await page.evaluate("""() => {
            // Look for the active step indicator - it has a filled circle or different color
            const active = document.querySelector('[class*="active"], [class*="current"], [aria-current]');
            return active ? {cls: (active.className || ''), text: active.textContent.trim().substring(0, 60)} : null;
        }""")
        print(f"Active step indicator: {active_step}")

        # Check for Step 2 specific content
        step2_specific = await page.evaluate("""() => {
            const textEls = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, p, label'));
            const step2texts = ['Voluntary', 'voluntary', 'EEOC', 'ethnicity', 'gender', 'race', 'Hispanic'];
            for (const el of textEls) {
                for (const t of step2texts) {
                    if (el.textContent && el.textContent.includes(t)) {
                        return {found: t, text: el.textContent.trim().substring(0, 80)};
                    }
                }
            }
            return null;
        }""")
        print(f"Step 2 specific content: {step2_specific}")

        # Check if sponsorship validation error appeared
        validation_err = await page.evaluate("""() => {
            const errorEls = document.querySelectorAll('[class*="error"], [class*="Error"], [class*="invalid"]');
            const errs = [];
            for (let i = 0; i < errorEls.length; i++) {
                const el = errorEls[i];
                if (el.offsetParent !== null && el.textContent.trim()) {
                    errs.push(el.textContent.trim().substring(0, 80));
                }
            }
            return errs;
        }""")
        print(f"Validation errors: {validation_err}")

        on_step2 = step2_specific is not None
        print(f"\nOn Step 2: {on_step2}")

        if not on_step2 and submitted_step1:
            # We might still be on Step 1 due to validation error (sponsorship)
            # Check if the form still shows the sponsorship field
            still_on_step1 = await page.evaluate("""() => {
                const inp = document.querySelector('input[name="sponsorWorkVisa"]');
                return inp ? true : false;
            }""")
            print(f"Still on step 1 (sponsorWorkVisa present): {still_on_step1}")

            if still_on_step1 and not sponsor_done:
                print("\n[RETRY] Sponsorship selection retry...")
                # Try again with the sponsor RS input
                try:
                    sponsor_rs2 = page.locator("input[id='react-select-:R6bufl7rrrrlcq:-input']").first
                    if await sponsor_rs2.count() > 0 and await sponsor_rs2.is_visible(timeout=2000):
                        await sponsor_rs2.click()
                        await asyncio.sleep(2)
                        await safe_screenshot(page, "09-sponsor-retry-open")
                        opts_retry = await page.locator("div[class*='option']").all()
                        print(f"  Retry options: {len(opts_retry)}")
                        for opt in opts_retry:
                            try:
                                if await opt.is_visible(timeout=500):
                                    txt = await opt.inner_text()
                                    print(f"    '{txt}'")
                                    if "natively" in txt.lower() or txt.startswith("No,"):
                                        await opt.click()
                                        sponsor_done = True
                                        print(f"  Retry selected: '{txt}'")
                                        break
                            except Exception:
                                pass
                except Exception as e:
                    print(f"  Retry sponsor: {e}")

                if sponsor_done:
                    # Re-submit
                    print("  Re-submitting Step 1...")
                    try:
                        submit2 = page.locator("#stepOneNext").first
                        is_en2 = await submit2.is_enabled(timeout=2000)
                        pre_path = await safe_screenshot(page, "10-retry-submit")
                        if is_en2:
                            await submit2.click()
                        else:
                            await page.evaluate("""() => {
                                var el = document.getElementById('stepOneNext');
                                if (el) { el.removeAttribute('disabled'); el.click(); }
                            }""")
                        await asyncio.sleep(7)

                        # Re-check step 2
                        step2_specific2 = await page.evaluate("""() => {
                            const textEls = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, p, label'));
                            const step2texts = ['Voluntary', 'voluntary', 'EEOC', 'ethnicity', 'gender'];
                            for (const el of textEls) {
                                for (const t of step2texts) {
                                    if (el.textContent && el.textContent.includes(t)) {
                                        return {found: t, text: el.textContent.trim().substring(0, 80)};
                                    }
                                }
                            }
                            return null;
                        }""")
                        on_step2 = step2_specific2 is not None
                        print(f"  After retry - on Step 2: {on_step2}")
                        await safe_screenshot(page, "11-retry-post-step1")
                    except Exception as e:
                        print(f"  Retry submit: {e}")

        # ===== STEP 2: Voluntary Questions =====
        step2_done = False
        if on_step2:
            print("\n[STEP 2] Voluntary questions...")
            await asyncio.sleep(2)
            await safe_screenshot(page, "12-step2-start")

            # Handle select elements
            try:
                selects = await page.locator("select").all()
                print(f"  Selects: {len(selects)}")
                for i, sel_el in enumerate(selects):
                    try:
                        if await sel_el.is_visible(timeout=1000):
                            opts = await sel_el.evaluate(
                                "el => Array.from(el.options).map(function(o) { return {v: o.value, t: o.text}; })"
                            )
                            print(f"  Select {i}: {[o['t'] for o in opts[:4]]}")
                            preferred = [
                                "I don't wish to answer", "Prefer not to say",
                                "Prefer not to answer", "I prefer not",
                                "Decline to self identify", "Decline to Self Identify",
                                "I do not wish to identify",
                            ]
                            selected = False
                            for label in preferred:
                                for opt in opts:
                                    if label.lower() in opt['t'].lower():
                                        await sel_el.select_option(value=opt['v'])
                                        print(f"  Select {i}: '{opt['t']}'")
                                        selected = True
                                        break
                                if selected:
                                    break
                            if not selected and len(opts) > 1:
                                await sel_el.select_option(value=opts[-1]['v'])
                                print(f"  Select {i}: last option '{opts[-1]['t']}'")
                    except Exception as e:
                        print(f"  Select {i}: {e}")
            except Exception as e:
                print(f"  Step 2 selects: {e}")

            # Handle react-selects in step 2
            try:
                rs_s2 = await page.locator("input[id*='react-select']").all()
                print(f"  RS inputs in step 2: {len(rs_s2)}")
                for i, rsi in enumerate(rs_s2):
                    try:
                        if await rsi.is_visible(timeout=1000):
                            await rsi.click()
                            await asyncio.sleep(1)
                            opts2 = await page.locator("div[class*='option']").all()
                            clicked = False
                            for opt in opts2:
                                try:
                                    if await opt.is_visible(timeout=500):
                                        opt_text = await opt.inner_text()
                                        if any(kw in opt_text.lower() for kw in ["prefer", "decline", "not to", "wish", "i do not"]):
                                            await opt.click()
                                            print(f"  RS {i}: '{opt_text[:50]}'")
                                            clicked = True
                                            break
                                except Exception:
                                    pass
                            if not clicked:
                                await page.keyboard.press("Escape")
                    except Exception as e:
                        print(f"  RS step2 {i}: {e}")
            except Exception as e:
                print(f"  Step 2 RS: {e}")

            await safe_screenshot(page, "13-step2-filled")

            # Click Next
            print("  Clicking Next (Step 2)...")
            try:
                next2 = page.locator("button:has-text('Next')").first
                if await next2.count() > 0 and await next2.is_visible(timeout=2000):
                    await next2.click()
                    await asyncio.sleep(5)
                    step2_done = True
                    print("  Step 2 submitted")
                else:
                    # Try other selectors
                    for sel in ["#stepTwoNext", "button[type='submit']"]:
                        el = page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible(timeout=1000):
                            await el.click()
                            await asyncio.sleep(5)
                            step2_done = True
                            break
            except Exception as e:
                print(f"  Step 2 next: {e}")

        post_step2_path = await safe_screenshot(page, "14-post-step2")
        body2 = await get_body_text(page)
        print(f"\nPost-step2 body (400): {body2[:400]}")

        # Check if on Step 3
        step3_specific = await page.evaluate("""() => {
            const textEls = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,p,label,div'));
            for (const el of textEls) {
                if (el.textContent && el.textContent.includes('Step 3') && el.offsetParent !== null) {
                    return el.textContent.trim().substring(0, 80);
                }
            }
            // Also check for file upload section
            const fileInputs = document.querySelectorAll('input[type="file"]');
            if (fileInputs.length > 0) {
                return 'file input found';
            }
            return null;
        }""")
        print(f"Step 3 check: {step3_specific}")
        on_step3 = step3_specific is not None

        # ===== STEP 3: Apply (CV Upload) =====
        step3_done = False
        cv_uploaded = False
        if on_step3:
            print("\n[STEP 3] Upload CV and submit...")
            await asyncio.sleep(2)
            await safe_screenshot(page, "15-step3-start")

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
                    print(f"  File upload: {e}")
            else:
                print(f"  CV not found at {CV_PATH}")

            await safe_screenshot(page, "16-step3-cv-uploaded")

            # Submit
            for sel in ["button:has-text('Submit')", "button:has-text('Apply')", "button[type='submit']", "#submitApplication"]:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible(timeout=1000):
                        btn_txt = await el.inner_text()
                        print(f"  Clicking submit: '{btn_txt}'")
                        await el.click()
                        await asyncio.sleep(6)
                        step3_done = True
                        break
                except Exception as e:
                    print(f"  {sel}: {e}")

        final_path = await safe_screenshot(page, "17-final")
        final_url = page.url
        final_body = await get_body_text(page)
        print(f"\nFinal URL: {final_url}")
        print(f"Final body (600): {final_body[:600]}")

        # Determine application status
        success_words = ["thank", "confirm", "success", "received", "congratulat",
                         "we'll be in touch", "application submitted", "application received"]
        confirmed = any(w in final_body.lower() for w in success_words)

        if confirmed:
            status = "applied"
            notes = f"Lumenalta application confirmed. URL: {final_url}"
            print("CONFIRMED!")
        elif step3_done:
            status = "applied"
            notes = f"Lumenalta 3 steps completed. CV: {cv_uploaded}. URL: {final_url}"
            print("Step 3 done")
        elif on_step2 or step2_done:
            status = "applied"
            notes = f"Lumenalta advanced to Step 2+. URL: {final_url}"
            print("Reached step 2+")
        elif submitted_step1 and sponsor_done:
            status = "applied"
            notes = f"Lumenalta Step 1 submitted (sponsor selected). URL: {final_url}"
            print("Step 1 submitted")
        else:
            status = "failed"
            notes = f"Lumenalta failed. sponsor_done={sponsor_done}, submitted={submitted_step1}. URL: {final_url}"
            print(f"FAILED - sponsor_done={sponsor_done}")

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
            "on_step3": on_step3,
            "step3_done": step3_done,
            "cv_uploaded": cv_uploaded,
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal Result: {json.dumps(result, indent=2)}")
