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
RESUME_PDF = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
COVER_LETTER_FILE = "/home/user/Agents/output/cover-letters/snelstart-net-developer.md"
VACANCY_URL = "https://www.werkenbijsnelstart.nl/vacatures/full-stack-developer-amersfoort-snelstart"
APPLY_URL = "https://www.werkenbijsnelstart.nl/solliciteren-nu?vacature_id=376d6c64-66ae-f011-bbd3-7ced8d73068c&functie=Full-Stack%20Developer"
SUCCESS_URL = "https://www.werkenbijsnelstart.nl/bedankt-pagina-sollicitatie"

APPLICANT = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "0648412838",  # Without country code
    "phone_country": "NL",
}

COVER_LETTER = """Geachte SnelStart Recruitment Team,

Ik schrijf u met enthousiasme voor de functie van Full-Stack Developer bij SnelStart Software B.V. SnelStart's reputatie als toonaangevend Nederlands boekhoud- en administratie-SaaS-platform, vertrouwd door duizenden ondernemers, maakt het een bedrijf waarbij ik graag wil bijdragen.

In mijn huidige functie als Software Service Engineer bij Actemium (VINCI Energies) ontwikkel ik full-stack applicaties met .NET, C#, ASP.NET en SQL Server, en lever ik REST API-integraties voor veeleisende industriele klanten in Agile-sprints. Eerder bij Delta Electronics heb ik een legacy Visual Basic-codebase gemigreerd naar C# en een HR-webapplicatie gebouwd voor budgetbeheer.

Mijn technische stack sluit goed aan bij SnelStart: C# en .NET backend, SQL Server, Azure DevOps en CI/CD-pipelines, en moderne JavaScript/TypeScript-frontends. Tijdens mijn stage bij ASML verdiepte ik mijn ervaring met Jira en Kubernetes in een agile omgeving.

Ik ben meertalig (Nederlands, Engels, Arabisch) en heb ondernemersgeest getoond door het oprichten van CogitatAI, een AI-klantenserviceplatform. Ik kijk uit naar de mogelijkheid om bij te dragen aan het engineeringteam van SnelStart.

Met vriendelijke groet,
Hisham Abboud
+31 06 4841 2838 | hiaham123@hotmail.com"""


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
    print(f"Resume PDF: {RESUME_PDF} (exists: {os.path.exists(RESUME_PDF)})")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            proxy=proxy,
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 1000},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = ctx.new_page()

        try:
            # Step 1: Vacancy page
            print("\n=== Step 1: Vacancy page ===")
            resp = page.goto(VACANCY_URL, wait_until="domcontentloaded", timeout=30000)
            print(f"Status: {resp.status if resp else 'N/A'}, Title: {page.title()}")
            time.sleep(2)
            s = save_screenshot(page, "01-vacancy-page")
            if s:
                result["screenshots"].append(s)

            # Step 2: Application form
            print("\n=== Step 2: Application form ===")
            resp = page.goto(APPLY_URL, wait_until="domcontentloaded", timeout=30000)
            print(f"Status: {resp.status if resp else 'N/A'}, Title: {page.title()}")
            print("Waiting 8s for HubSpot form to load...")
            time.sleep(8)

            s = save_screenshot(page, "02-apply-page-loaded")
            if s:
                result["screenshots"].append(s)

            # Verify form is present
            firstname_el = page.query_selector("input[name='firstname']")
            if not firstname_el:
                result["status"] = "skipped"
                result["notes"] = "HubSpot form not found. Apply manually: " + APPLY_URL
                return result

            # Step 3: Fill firstname
            print("\n=== Step 3: Fill form ===")
            print("  Filling firstname...")
            firstname_el.click()
            firstname_el.fill(APPLICANT["first_name"])
            time.sleep(0.3)

            # Fill lastname
            print("  Filling lastname...")
            lastname_el = page.query_selector("input[name='lastname']")
            lastname_el.click()
            lastname_el.fill(APPLICANT["last_name"])
            time.sleep(0.3)

            # Fill email
            print("  Filling email...")
            email_el = page.query_selector("input[name='email']")
            email_el.click()
            email_el.fill(APPLICANT["email"])
            time.sleep(0.3)

            # Set phone country to Netherlands first
            print("  Setting phone country to Netherlands...")
            phone_select = page.query_selector("select[id*='phone_ext']")
            if phone_select:
                # Select Netherlands by value
                page.evaluate(
                    """([el]) => {
                        const options = Array.from(el.options);
                        const nl = options.find(o => o.value === 'NL');
                        if (nl) {
                            el.value = 'NL';
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    }""",
                    [phone_select]
                )
                time.sleep(0.5)
                current_val = page.evaluate("(el) => el.value", phone_select)
                print(f"    Phone country set to: {current_val}")

            # Fill phone number (the visible tel input)
            print("  Filling phone number...")
            phone_tel = page.query_selector("input[type='tel']")
            if phone_tel:
                # Clear the field first and fill with just digits
                phone_tel.click()
                # Triple-click to select all, then type
                phone_tel.triple_click()
                time.sleep(0.2)
                phone_tel.fill(APPLICANT["phone"])
                time.sleep(0.3)
                phone_val = page.evaluate("(el) => el.value", phone_tel)
                print(f"    Phone value: {phone_val}")

            # Upload CV
            print("  Uploading CV...")
            cv_input = page.query_selector("input[name='upload_je_cv_bij_voorkeur_pdf_']")
            if cv_input and os.path.exists(RESUME_PDF):
                cv_input.set_input_files(RESUME_PDF)
                time.sleep(2)
                print(f"    Uploaded: {RESUME_PDF}")
            else:
                print(f"    CV input not found or file missing: {RESUME_PDF}")

            # "Hoe ben je bij ons terecht gekomen" - how did you find us
            print("  Selecting 'hoe ben je bij ons terecht gekomen'...")
            source_select = page.query_selector("select[name='hoe_ben_je_bij_ons_terecht_gekomen_']")
            if source_select:
                # Get available options
                options = page.evaluate(
                    "(el) => Array.from(el.options).map(o => ({value: o.value, text: o.text}))",
                    source_select
                )
                print(f"    Options: {options}")
                # Select "Internet" or first non-empty option
                for opt in options:
                    if opt["value"] and opt["value"] != "":
                        page.evaluate(
                            "([el, val]) => { el.value = val; el.dispatchEvent(new Event('change', {bubbles:true})); }",
                            [source_select, opt["value"]]
                        )
                        print(f"    Selected: {opt['text']}")
                        break

            # Fill cover letter textarea
            print("  Filling motivation/cover letter...")
            bericht = page.query_selector("textarea[name='bericht']")
            if bericht:
                bericht.click()
                bericht.fill(COVER_LETTER)
                time.sleep(0.3)
                actual_len = page.evaluate("(el) => el.value.length", bericht)
                print(f"    Textarea filled: {actual_len} chars")

            # Scroll to consent checkbox and click it
            print("  Checking consent checkbox...")
            consent = page.query_selector("input[name*='LEGAL_CONSENT']")
            if consent:
                # Scroll to make it visible and click
                consent.scroll_into_view_if_needed()
                time.sleep(0.5)
                consent.click()
                time.sleep(0.3)
                is_checked = page.evaluate("(el) => el.checked", consent)
                print(f"    Consent checkbox checked: {is_checked}")

            time.sleep(1)

            # Take screenshot of filled form (scroll to top first)
            page.evaluate("() => window.scrollTo(0, 0)")
            time.sleep(0.5)
            s = save_screenshot(page, "03-form-top-filled")
            if s:
                result["screenshots"].append(s)

            # Scroll to bottom to see full form
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.5)
            s = save_screenshot(page, "04-form-bottom-filled")
            if s:
                result["screenshots"].append(s)

            # Verify field values
            verification = page.evaluate("""() => ({
                firstname: document.querySelector("input[name='firstname']")?.value || '',
                lastname: document.querySelector("input[name='lastname']")?.value || '',
                email: document.querySelector("input[name='email']")?.value || '',
                phone: document.querySelector("input[type='tel']")?.value || '',
                bericht: document.querySelector("textarea[name='bericht']")?.value?.length || 0,
                consent: document.querySelector("input[name*='LEGAL_CONSENT']")?.checked || false,
            })""")
            print(f"\n  Field verification: {verification}")

            # Find and click submit
            print("\n=== Step 4: Submit ===")
            submit = page.query_selector("input[type='submit'][value='Verzenden']")
            if not submit:
                submit = page.query_selector("input[type='submit']")
            if not submit:
                submit = page.query_selector("button[type='submit']")

            if not submit:
                result["status"] = "skipped"
                result["notes"] = "Submit button not found. Apply manually: " + APPLY_URL
                return result

            print(f"  Found submit: {page.evaluate('(el) => el.value || el.innerText', submit)}")

            # Scroll to submit and take pre-submit screenshot
            submit.scroll_into_view_if_needed()
            time.sleep(0.5)
            s = save_screenshot(page, "05-pre-submit")
            if s:
                result["screenshots"].append(s)

            # Click submit
            print("  Clicking Verzenden...")
            submit.click()
            time.sleep(6)

            # Check if redirected to success page
            current_url = page.url
            print(f"  Post-submit URL: {current_url}")

            s = save_screenshot(page, "06-post-submit")
            if s:
                result["screenshots"].append(s)

            if "bedankt" in current_url.lower() or "thank" in current_url.lower():
                result["status"] = "applied"
                result["notes"] = f"Application submitted successfully. Redirected to: {current_url}. Applied via: {APPLY_URL}"
                print(f"  SUCCESS - Redirected to confirmation page!")
            else:
                # Check page content for success or errors
                body_text = page.evaluate("() => document.body?.innerText?.substring(0, 1000) || ''")
                print(f"  Page text: {body_text[:300]}")

                error_kws = ["vul", "verplicht", "required", "error", "fout"]
                success_kws = ["bedankt", "dank", "thank", "ontvangen", "ingediend", "bevestig"]

                if any(kw in body_text.lower() for kw in success_kws):
                    result["status"] = "applied"
                    result["notes"] = f"Application submitted. Confirmation keywords found. Via: {APPLY_URL}"
                elif any(kw in body_text.lower() for kw in error_kws):
                    result["status"] = "failed"
                    result["notes"] = (
                        f"Form validation errors after submit. Page still shows form. "
                        f"Verification: {verification}. "
                        f"Apply manually: {APPLY_URL}"
                    )
                else:
                    result["status"] = "applied"
                    result["notes"] = f"Form submitted via {APPLY_URL}. Check screenshot for details."

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
