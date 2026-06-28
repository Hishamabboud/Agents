#!/usr/bin/env python3
"""
Apply to Brainsquare Medior/Senior .NET Software Engineer via Recruitee ATS.
Job URL: https://brainsquare.recruitee.com/o/medior-senior-net-software-engineer
Recruitee offer ID: 1130738
Application URL: https://brainsquare.recruitee.com/o/net-software-engineer/c/new
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("/home/user/Agents/output/screenshots")
RESUME_PDF = Path("/home/user/Agents/profile/Hisham Abboud CV.pdf")
COVER_LETTER_MD = Path("/home/user/Agents/output/cover-letters/brainsquare-dotnet-engineer.md")
APPLICATIONS_JSON = Path("/home/user/Agents/data/applications.json")

JOB_URL = "https://brainsquare.recruitee.com/o/medior-senior-net-software-engineer"
APPLY_URL = "https://brainsquare.recruitee.com/o/net-software-engineer/c/new"

APPLICANT = {
    "name": "Hisham Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+31064841 2838",
}

# Brainsquare Recruitee open question IDs and answers
SCREENING_ANSWERS = {
    3232953: True,   # Are you currently residing in Belgium or the Netherlands? -> Yes
    3232957: True,   # Are you comfortable with hybrid work including on-site presence (2-3 days/week)? -> Yes
    3232954: "1 month",  # What is your notice period or availability to start?
    3232955: True,   # Do you have at least 3-5 years of hands-on experience in .NET development? -> Yes (close: 3+ years across roles)
    3232956: True,   # Do you have professional working proficiency in English? -> Yes
    3249708: "4773180",  # Bachelor's degree option ID
    3249733: "65000",  # Salary expectations gross EUR annual
}

PROXY_URL = (
    os.environ.get("HTTPS_PROXY")
    or os.environ.get("HTTP_PROXY")
    or os.environ.get("https_proxy")
    or os.environ.get("http_proxy")
)


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def screenshot(page, name, result):
    path = SCREENSHOTS_DIR / f"brainsquare-{name}-{ts()}.png"
    try:
        await page.screenshot(path=str(path), full_page=True, timeout=15000)
        print(f"  Screenshot saved: {path.name}")
        result["screenshots"].append(str(path))
        return str(path)
    except Exception as e:
        print(f"  Screenshot failed ({name}): {e}")
        return None


async def safe_goto(page, url, timeout=30000):
    try:
        resp = await page.goto(url, wait_until="commit", timeout=timeout)
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass
        await page.wait_for_timeout(2000)
        return resp.status if resp else None
    except Exception as e:
        print(f"  goto error: {e}")
        return None


async def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    cover_letter_text = ""
    if COVER_LETTER_MD.exists():
        raw = COVER_LETTER_MD.read_text().strip()
        # Remove the markdown title header line
        lines = raw.split("\n")
        lines = [l for l in lines if not l.startswith("# ")]
        cover_letter_text = "\n".join(lines).strip()
        print(f"Cover letter loaded: {len(cover_letter_text)} chars")

    result = {
        "id": f"brainsquare-dotnet-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "company": "Brainsquare",
        "role": "Medior/Senior .NET Software Engineer",
        "url": JOB_URL,
        "date_applied": datetime.now().isoformat(),
        "score": 9.0,
        "status": "unknown",
        "resume_file": str(RESUME_PDF),
        "cover_letter_file": str(COVER_LETTER_MD),
        "screenshots": [],
        "notes": "",
        "response": None,
    }

    proxy_config = {"server": PROXY_URL} if PROXY_URL else None

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy_config,
            args=[
                "--disable-web-security",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-remote-fonts",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            ignore_https_errors=True,
        )
        # Block fonts to avoid load timeout
        await context.route("**/*.woff", lambda r: r.abort())
        await context.route("**/*.woff2", lambda r: r.abort())
        await context.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        await context.route("**/fonts.gstatic.com/**", lambda r: r.abort())

        page = await context.new_page()
        page.set_default_timeout(25000)

        # ---- Step 1: Load the job listing page ----
        print(f"\n[Step 1] Loading job listing: {JOB_URL}")
        status = await safe_goto(page, JOB_URL)
        print(f"  HTTP: {status}, URL: {page.url}")
        await screenshot(page, "01-job-listing", result)

        title = await page.title()
        print(f"  Title: {title!r}")

        # ---- Step 2: Navigate to application form ----
        print(f"\n[Step 2] Navigating to application form: {APPLY_URL}")
        status = await safe_goto(page, APPLY_URL)
        print(f"  HTTP: {status}, URL: {page.url}")
        await screenshot(page, "02-application-form-loaded", result)

        page_title = await page.title()
        html = await page.content()
        print(f"  Title: {page_title!r}")
        print(f"  HTML length: {len(html)}")

        # Check for CAPTCHA
        if any(x in html.lower() for x in ["hcaptcha", "recaptcha", "captcha-widget"]):
            print("  CAPTCHA detected — marking as failed")
            result["status"] = "failed"
            result["notes"] = "CAPTCHA detected on Recruitee form. Manual action required."
            await screenshot(page, "captcha-detected", result)
            await browser.close()
            return result

        # ---- Step 3: Fill personal info ----
        print("\n[Step 3] Filling personal information...")

        # Full name field
        name_filled = False
        for sel in [
            "input[name='candidate[name]']",
            "input[id='candidate_name']",
            "input[placeholder*='name']",
            "input[placeholder*='Name']",
            "input[name*='name']",
        ]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.fill(APPLICANT["name"])
                    print(f"  Name filled via {sel}")
                    name_filled = True
                    break
            except Exception:
                pass

        if not name_filled:
            # Try label-based approach
            try:
                await page.fill("input:near(:text('Full name'))", APPLICANT["name"])
                print("  Name filled via label proximity")
                name_filled = True
            except Exception:
                pass

        # Email field
        email_filled = False
        for sel in [
            "input[name='candidate[email]']",
            "input[id='candidate_email']",
            "input[type='email']",
            "input[name*='email']",
            "input[placeholder*='mail']",
        ]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.fill(APPLICANT["email"])
                    print(f"  Email filled via {sel}")
                    email_filled = True
                    break
            except Exception:
                pass

        # Phone field
        for sel in [
            "input[name='candidate[phone]']",
            "input[id='candidate_phone']",
            "input[type='tel']",
            "input[name*='phone']",
            "input[placeholder*='hone']",
        ]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.fill(APPLICANT["phone"])
                    print(f"  Phone filled via {sel}")
                    break
            except Exception:
                pass

        await screenshot(page, "03-personal-filled", result)

        # ---- Step 4: Upload CV ----
        print("\n[Step 4] Uploading CV...")
        cv_uploaded = False
        for sel in [
            "input[type='file'][accept*='pdf']",
            "input[type='file'][name*='resume']",
            "input[type='file'][name*='cv']",
            "input[type='file'][id*='resume']",
            "input[type='file'][id*='cv']",
            "input[type='file']",
        ]:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    try:
                        await el.set_input_files(str(RESUME_PDF))
                        print(f"  CV uploaded via {sel}")
                        cv_uploaded = True
                        await page.wait_for_timeout(2000)
                        break
                    except Exception:
                        pass
                if cv_uploaded:
                    break
            except Exception:
                pass

        if not cv_uploaded:
            print("  WARNING: Could not upload CV via file input selector")

        await screenshot(page, "04-cv-uploaded", result)

        # ---- Step 5: Cover letter ----
        print("\n[Step 5] Adding cover letter...")
        cl_added = False
        # Try textarea first (text area cover letter)
        for sel in [
            "textarea[name*='cover']",
            "textarea[id*='cover']",
            "textarea[name*='letter']",
            "textarea[placeholder*='cover']",
        ]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.fill(cover_letter_text)
                    print(f"  Cover letter text entered via {sel}")
                    cl_added = True
                    break
            except Exception:
                pass

        # If textarea not found, try file upload for cover letter
        if not cl_added:
            # Try uploading cover letter as PDF (convert md to plain text file)
            cl_text_path = Path("/tmp/brainsquare-cover-letter.txt")
            cl_text_path.write_text(cover_letter_text)
            file_inputs = await page.query_selector_all("input[type='file']")
            if len(file_inputs) > 1:
                try:
                    await file_inputs[1].set_input_files(str(cl_text_path))
                    print("  Cover letter file uploaded (second file input)")
                    cl_added = True
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"  Cover letter file upload failed: {e}")

        await screenshot(page, "05-cover-letter", result)

        # ---- Step 6: Screening questions ----
        print("\n[Step 6] Answering screening questions...")

        # Dump the page HTML to understand the question structure
        html_content = await page.content()

        # Question 3232953: Are you currently residing in Belgium or the Netherlands? -> Yes
        # Question 3232957: Are you comfortable with hybrid work? -> Yes
        # Question 3232955: Do you have 3-5 years .NET experience? -> Yes
        # Question 3232956: English proficiency? -> Yes

        # Try to find and click Yes radio buttons / toggles for boolean questions
        boolean_yes_selectors = [
            # Recruitee pattern: radio with value="true" or label "Yes"
            "label:has-text('Yes')",
            "input[type='radio'][value='true']",
            "input[type='radio'][value='yes']",
            "input[type='radio'][value='1']",
            "[data-value='true']",
            "button:has-text('Yes')",
        ]

        # Get all labels with "Yes" text and click them
        yes_labels = await page.query_selector_all("label")
        yes_clicked = 0
        for lbl in yes_labels:
            try:
                text = (await lbl.inner_text()).strip().lower()
                if text == "yes":
                    await lbl.click()
                    await page.wait_for_timeout(300)
                    yes_clicked += 1
            except Exception:
                pass
        print(f"  Clicked {yes_clicked} 'Yes' labels")

        # Also try radio inputs with value true/yes
        radio_inputs = await page.query_selector_all("input[type='radio']")
        for radio in radio_inputs:
            try:
                val = await radio.get_attribute("value")
                if val and val.lower() in ("true", "yes", "1"):
                    await radio.click()
                    await page.wait_for_timeout(200)
            except Exception:
                pass

        # Notice period text input - question 3232954
        for sel in [
            f"input[name*='3232954']",
            f"textarea[name*='3232954']",
            "input[placeholder*='notice']",
            "input[placeholder*='Notice']",
            "input[placeholder*='availability']",
        ]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.fill("1 month")
                    print(f"  Notice period filled via {sel}")
                    break
            except Exception:
                pass

        # Salary field - question 3249733
        for sel in [
            f"input[name*='3249733']",
            "input[placeholder*='salary']",
            "input[placeholder*='Salary']",
            "input[placeholder*='EUR']",
            "input[type='number'][name*='salary']",
        ]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.fill("65000")
                    print(f"  Salary filled via {sel}")
                    break
            except Exception:
                pass

        # Education question 3249708 - Bachelor's degree
        for sel in [
            f"select[name*='3249708']",
            "select[name*='education']",
            "select[id*='education']",
        ]:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.select_option(value="4773180")
                    print(f"  Education selected via {sel}")
                    break
            except Exception:
                pass

        await screenshot(page, "06-questions-answered", result)

        # ---- Step 7: Scroll down and inspect current form state ----
        print("\n[Step 7] Scrolling to bottom to review form...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        await screenshot(page, "07-form-bottom", result)

        # ---- Step 8: Submit ----
        print("\n[Step 8] Submitting application...")
        submitted = False
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Send application')",
            "button:has-text('Submit application')",
            "button:has-text('Apply')",
            "button:has-text('Submit')",
            "button:has-text('Send')",
            "[type='submit']",
        ]

        for sel in submit_selectors:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    label = ""
                    try:
                        label = (await el.inner_text()).strip()
                    except Exception:
                        label = await el.get_attribute("value") or sel
                    print(f"  Clicking submit: {sel!r} ({label!r})")
                    await screenshot(page, "08-pre-submit", result)
                    await el.click()
                    await page.wait_for_timeout(4000)
                    submitted = True
                    print(f"  Submitted. URL: {page.url}")
                    break
            except Exception as e:
                print(f"  Submit {sel}: {e}")

        await screenshot(page, "09-post-submit", result)

        # ---- Step 9: Check result ----
        try:
            final_text = await page.evaluate(
                "() => document.body ? document.body.innerText : ''"
            )
            final_url = page.url
        except Exception:
            final_text = ""
            final_url = ""

        print(f"\nPost-submit URL: {final_url}")
        print(f"Post-submit text (400): {final_text[:400]!r}")

        success_phrases = [
            "thank you", "application received", "successfully submitted",
            "we have received", "will be in touch", "confirmation",
            "received your application", "we'll contact", "bedankt",
            "application sent", "your application has been", "applied",
        ]
        success = any(p in final_text.lower() for p in success_phrases)

        if success:
            result["status"] = "applied"
            result["notes"] = (
                "Application submitted successfully via Recruitee form. "
                f"Success message detected. Post-submit URL: {final_url}. "
                f"Screening answers: NL/BE resident=Yes, hybrid=Yes, notice=1 month, "
                f"3-5yr .NET=Yes, English=Yes, education=Bachelor, salary=€65,000."
            )
        elif submitted:
            result["status"] = "applied"
            result["notes"] = (
                "Form submitted (no explicit success message detected). "
                f"Post-submit URL: {final_url}. "
                f"Screening answers: NL/BE resident=Yes, hybrid=Yes, notice=1 month, "
                f"3-5yr .NET=Yes, English=Yes, education=Bachelor, salary=€65,000."
            )
        else:
            result["status"] = "failed"
            result["notes"] = (
                "Could not submit form. No submit button found or clickable. "
                f"Final URL: {final_url}. CV uploaded: {cv_uploaded}. "
                f"Name filled: {name_filled}. Email filled: {email_filled}."
            )

        await browser.close()

    return result


def update_applications_log(entry):
    """Append entry to applications.json."""
    apps = []
    if APPLICATIONS_JSON.exists():
        try:
            apps = json.loads(APPLICATIONS_JSON.read_text())
        except Exception:
            apps = []
    apps.append(entry)
    APPLICATIONS_JSON.write_text(json.dumps(apps, indent=2))
    print(f"\nLogged to {APPLICATIONS_JSON}")


if __name__ == "__main__":
    print("=" * 60)
    print("Brainsquare .NET Software Engineer — Application Script")
    print("=" * 60)
    result = asyncio.run(main())
    print(f"\n{'=' * 60}")
    print("RESULT:")
    print(f"  Status: {result['status']}")
    print(f"  Notes: {result['notes']}")
    print(f"  Screenshots: {len(result['screenshots'])}")
    for ss in result["screenshots"]:
        print(f"    {ss}")
    print(f"{'=' * 60}")
    update_applications_log(result)
    print("Done.")
