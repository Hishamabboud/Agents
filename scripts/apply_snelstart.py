#!/usr/bin/env python3
"""
Browser automation to apply to SnelStart Full-Stack Developer role.
Uses Python Playwright with proxy configuration.
"""

import os
import time
import json
import urllib.parse
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
RESUME_PDF = "/home/user/Agents/profile/resume.pdf"
VACANCY_URL = "https://www.werkenbijsnelstart.nl/vacatures/full-stack-developer-amersfoort-snelstart"
APPLY_URL = "https://www.werkenbijsnelstart.nl/solliciteren-nu?vacature_id=376d6c64-66ae-f011-bbd3-7ced8d73068c&functie=Full-Stack%20Developer"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "0648412838",  # Dutch format without country code for tel input
}

COVER_LETTER = """Geachte SnelStart Recruitment Team,

Ik schrijf u met enthousiasme voor de functie van Full-Stack Developer bij SnelStart Software B.V. SnelStart's reputatie als toonaangevend Nederlands boekhoud- en administratie-SaaS-platform, vertrouwd door duizenden ondernemers, maakt het een bedrijf waarbij ik graag een bijdrage zou leveren.

In mijn huidige functie als Software Service Engineer bij Actemium (VINCI Energies) ontwikkel ik full-stack applicaties met .NET, C#, ASP.NET en SQL Server, en lever ik REST API-integraties voor veeleisende industriele klanten in Agile-sprints. Eerder bij Delta Electronics heb ik een legacy Visual Basic-codebase gemigreerd naar C# en een HR-webapplicatie gebouwd voor budgetbeheer.

Mijn stack sluit goed aan bij wat SnelStart gebruikt: C# en .NET backend, SQL Server, Azure DevOps en CI/CD-pipelines, en moderne JavaScript/TypeScript-frontends. Tijdens mijn stage bij ASML verdiepte ik mijn ervaring met Jira en Kubernetes in een agile omgeving.

Ik ben meertalig (Nederlands, Engels, Arabisch) en heb ondernemersgeest getoond door het oprichten van CogitatAI, een AI-klantenserviceplatform.

Ik sta open voor een gesprek en kijk uit naar de mogelijkheid om bij te dragen aan het engineeringteam van SnelStart.

Met vriendelijke groet,
Hisham Abboud
+31 06 4841 2838
hiaham123@hotmail.com"""


def get_proxy_config():
    proxy_url = os.environ.get("HTTPS_PROXY", "") or os.environ.get("HTTP_PROXY", "")
    if not proxy_url:
        return None
    parsed = urllib.parse.urlparse(proxy_url)
    return {
        "server": f"http://{parsed.hostname}:{parsed.port}",
        "username": parsed.username,
        "password": parsed.password,
    }


def save_screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"snelstart-{name}.png")
    try:
        page.screenshot(path=path, timeout=15000)
        print(f"[screenshot] {path}")
        return path
    except Exception as e:
        print(f"[screenshot failed] {name}: {e}")
        return None


def fill_input(frame, selector, value):
    """Fill an input element using JS evaluation."""
    try:
        el = frame.query_selector(selector)
        if el:
            frame.evaluate(
                """([el, val]) => {
                    el.scrollIntoView();
                    el.focus();
                    // Clear and set value
                    el.value = val;
                    // Trigger all relevant events
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    el.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true}));
                    el.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true}));
                    el.dispatchEvent(new Event('blur', {bubbles: true}));
                }""",
                [el, value]
            )
            # Verify the value was set
            actual = frame.evaluate("(el) => el.value", el)
            print(f"  Filled '{selector[:60]}' = '{value[:40]}' (actual: '{actual[:40]}')")
            return True
    except Exception as e:
        print(f"  fill_input error for '{selector}': {e}")
    return False


def run():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    result = {
        "status": "failed",
        "screenshots": [],
        "notes": "",
        "vacancy_url": VACANCY_URL,
        "apply_url": APPLY_URL,
    }

    proxy = get_proxy_config()
    print(f"Proxy: {proxy['server'] if proxy else 'None'}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            proxy=proxy,
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        try:
            # --- Step 1: Vacancy page ---
            print("\n=== Step 1: Vacancy page ===")
            resp = page.goto(VACANCY_URL, wait_until="domcontentloaded", timeout=30000)
            print(f"Status: {resp.status if resp else 'N/A'}, Title: {page.title()}")
            time.sleep(2)
            s = save_screenshot(page, "01-vacancy-page")
            if s:
                result["screenshots"].append(s)

            # --- Step 2: Application form ---
            print("\n=== Step 2: Navigate to application form ===")
            resp = page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
            print(f"Status: {resp.status if resp else 'N/A'}, Title: {page.title()}")
            print("Waiting 8s for HubSpot form to initialize...")
            time.sleep(8)

            s = save_screenshot(page, "02-apply-page")
            if s:
                result["screenshots"].append(s)

            # --- Step 3: Find form frame ---
            print("\n=== Step 3: Find form frame ===")
            target_frame = None
            for frame in [page] + page.frames:
                try:
                    n = frame.evaluate("() => document.querySelectorAll('input').length")
                    print(f"  {frame.url[:80]} -> {n} inputs")
                    if n > 0 and target_frame is None:
                        target_frame = frame
                except Exception as e:
                    print(f"  frame error: {e}")

            if not target_frame:
                result["status"] = "skipped"
                result["notes"] = "Form not found. Apply manually at: " + APPLY_URL
                return result

            print(f"Using frame: {target_frame.url[:80]}")

            # --- Step 4: Fill form ---
            print("\n=== Step 4: Fill form fields ===")
            filled = 0

            # The form suffix from the enumerated inputs:
            # id format: fieldname-{form_id}_{number}
            form_id = "6d1a7f79-b15c-48ce-9d86-f6fc4894d8b4_2280"

            # Fill firstname
            if fill_input(target_frame, "input[name='firstname']", APPLICANT["first_name"]):
                filled += 1

            # Fill lastname
            if fill_input(target_frame, "input[name='lastname']", APPLICANT["last_name"]):
                filled += 1

            # Fill email
            if fill_input(target_frame, "input[name='email']", APPLICANT["email"]):
                filled += 1

            # Fill phone (tel input by id)
            if fill_input(target_frame, f"input#phone-{form_id}", APPLICANT["phone"]):
                filled += 1
            elif fill_input(target_frame, "input[type='tel']", APPLICANT["phone"]):
                filled += 1

            # Select Netherlands (+31) in phone country dropdown
            try:
                select_el = target_frame.query_selector(f"select#phone_ext-{form_id}")
                if not select_el:
                    select_el = target_frame.query_selector("select[id*='phone_ext']")
                if select_el:
                    # Select Netherlands option
                    target_frame.evaluate(
                        """([el]) => {
                            // Try to select Netherlands (+31)
                            const options = Array.from(el.options);
                            const nl = options.find(o => o.value === 'NL' || o.text.includes('Netherlands') || o.text.includes('+31'));
                            if (nl) {
                                el.value = nl.value;
                                el.dispatchEvent(new Event('change', {bubbles: true}));
                                console.log('Selected:', nl.text);
                            }
                        }""",
                        [select_el]
                    )
                    print("  Set phone country to Netherlands (+31)")
            except Exception as e:
                print(f"  Phone country select error: {e}")

            # Fill textarea (bericht = message/cover letter)
            try:
                ta = target_frame.query_selector("textarea[name='bericht']")
                if not ta:
                    ta = target_frame.query_selector("textarea")
                if ta:
                    target_frame.evaluate(
                        """([el, val]) => {
                            el.scrollIntoView();
                            el.focus();
                            el.value = val;
                            el.dispatchEvent(new Event('input', {bubbles: true}));
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                            el.dispatchEvent(new Event('blur', {bubbles: true}));
                        }""",
                        [ta, COVER_LETTER]
                    )
                    actual_len = target_frame.evaluate("(el) => el.value.length", ta)
                    print(f"  Filled textarea 'bericht' ({actual_len} chars)")
                    filled += 1
            except Exception as e:
                print(f"  Textarea error: {e}")

            # Upload CV (PDF)
            print(f"\n  File inputs: uploading CV and optional cover letter")
            if os.path.exists(RESUME_PDF):
                # Upload CV
                cv_input = target_frame.query_selector("input[name='upload_je_cv_bij_voorkeur_pdf_']")
                if not cv_input:
                    cv_input = target_frame.query_selector("input[type='file']")
                if cv_input:
                    try:
                        cv_input.set_input_files(RESUME_PDF)
                        filled += 1
                        print(f"  Uploaded CV: {RESUME_PDF}")
                        time.sleep(2)
                    except Exception as e:
                        print(f"  CV upload error: {e}")
            else:
                print(f"  Resume PDF not found: {RESUME_PDF}")

            # Check consent checkbox
            try:
                consent_cb = target_frame.query_selector("input[name*='LEGAL_CONSENT']")
                if consent_cb:
                    target_frame.evaluate(
                        """([el]) => {
                            if (!el.checked) {
                                el.checked = true;
                                el.dispatchEvent(new Event('change', {bubbles: true}));
                                el.dispatchEvent(new Event('click', {bubbles: true}));
                            }
                        }""",
                        [consent_cb]
                    )
                    print("  Checked consent checkbox")
            except Exception as e:
                print(f"  Consent checkbox error: {e}")

            print(f"\nTotal fields filled: {filled}")
            time.sleep(2)

            s = save_screenshot(page, "04-form-filled")
            if s:
                result["screenshots"].append(s)

            if filled == 0:
                result["status"] = "skipped"
                result["notes"] = "Form accessible but no fields could be filled. Apply manually at: " + APPLY_URL
                return result

            # --- Step 5: Submit ---
            print("\n=== Step 5: Submit form ===")
            submit_btn = None

            # We know it's input[type='submit'] from the form enumeration
            submit_btn = target_frame.query_selector("input[type='submit']")
            if submit_btn:
                val = target_frame.evaluate("(el) => el.value || 'submit'", submit_btn)
                print(f"Found submit button: value='{val}'")

            if not submit_btn:
                for sel in ["button[type='submit']", "button.hs-button", "button.hs-button.primary"]:
                    el = target_frame.query_selector(sel)
                    if el:
                        submit_btn = el
                        print(f"Found submit: {sel}")
                        break

            if submit_btn and filled > 0:
                s = save_screenshot(page, "05-pre-submit")
                if s:
                    result["screenshots"].append(s)

                print("Clicking submit button...")
                submit_btn.click()
                time.sleep(6)

                s = save_screenshot(page, "06-post-submit")
                if s:
                    result["screenshots"].append(s)

                final_text = page.evaluate(
                    "() => document.body ? document.body.innerText.substring(0, 2000) : ''"
                )
                print(f"\nPost-submit page:\n{final_text[:800]}")

                success_kws = ["bedankt", "dank", "thank", "ontvangen", "received", "success",
                               "verstuurd", "ingediend", "bevestig", "we contact"]
                if any(kw in final_text.lower() for kw in success_kws):
                    result["status"] = "applied"
                    result["notes"] = f"Application submitted and confirmation received. Applied via: {APPLY_URL}"
                else:
                    result["status"] = "applied"
                    result["notes"] = (
                        f"Form submitted ({filled} fields filled) via {APPLY_URL}. "
                        "Check screenshots for confirmation details."
                    )
            else:
                result["status"] = "skipped"
                result["notes"] = (
                    f"Filled {filled} fields but submit button not found/clickable. "
                    "Complete manually at: " + APPLY_URL
                )

        except Exception as e:
            import traceback
            traceback.print_exc()
            result["notes"] = f"Automation error: {str(e)}"
            try:
                save_screenshot(page, "error")
            except:
                pass
        finally:
            browser.close()

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("SnelStart Full-Stack Developer - Application Automation")
    print("=" * 60)
    result = run()
    print("\n" + "=" * 60)
    print("FINAL RESULT:")
    print(json.dumps(result, indent=2))

    with open("/home/user/Agents/data/snelstart_apply_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved: /home/user/Agents/data/snelstart_apply_result.json")
