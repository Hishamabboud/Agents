#!/usr/bin/env python3
"""
Apply to ClickHouse - Cloud Software Engineer, Identity and Access Management
Job URL: https://job-boards.greenhouse.io/clickhouse/jobs/5803692004
"""

import os
import json
import time
from datetime import date
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

JOB_URL = "https://job-boards.greenhouse.io/clickhouse/jobs/5803692004"
RESUME_PDF = "/home/user/Agents/profile/Hisham Abboud CV.pdf"
SCREENSHOTS_DIR = "/home/user/Agents/output/screenshots"
COVER_LETTER_PATH = "/home/user/Agents/output/cover-letters/clickhouse-cloud-engineer.md"
APPLICATIONS_JSON = "/home/user/Agents/data/applications.json"

CANDIDATE = {
    "first_name": "Hisham",
    "last_name": "Abboud",
    "email": "hiaham123@hotmail.com",
    "phone": "+3106 4841 2838",
    "linkedin": "https://linkedin.com/in/hisham-abboud",
    "github": "https://github.com/Hishamabboud",
    "location": "Eindhoven, Netherlands",
}

with open(COVER_LETTER_PATH, "r") as f:
    COVER_LETTER_TEXT = f.read()


def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"clickhouse-{name}.png")
    try:
        page.screenshot(path=path, full_page=True, timeout=15000)
        print(f"Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"Screenshot failed ({name}): {e}")
        # Try without full_page
        try:
            page.screenshot(path=path, timeout=10000)
            print(f"Screenshot (viewport only) saved: {path}")
            return path
        except Exception as e2:
            print(f"Screenshot (viewport) also failed: {e2}")
            return ""


def try_fill(page, selectors, value, label="field"):
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if el.count() > 0:
                el.fill(value)
                print(f"Filled {label}: {value[:60]}")
                return True
        except Exception:
            continue
    print(f"WARNING: Could not find {label}")
    return False


def log_all_inputs(page):
    print("\n--- Form elements found ---")
    elements = page.locator("input, select, textarea").all()
    for el in elements:
        try:
            tag = el.evaluate("e => e.tagName")
            type_ = el.get_attribute("type") or ""
            name = el.get_attribute("name") or ""
            id_ = el.get_attribute("id") or ""
            placeholder = el.get_attribute("placeholder") or ""
            label_for = ""
            if id_:
                try:
                    label_el = page.locator(f"label[for='{id_}']")
                    if label_el.count() > 0:
                        label_for = label_el.text_content() or ""
                except Exception:
                    pass
            print(f"  {tag} type={type_} name={name} id={id_} placeholder={placeholder} label='{label_for.strip()}'")
        except Exception as e:
            print(f"  (could not read element: {e})")
    print("--- End form elements ---\n")


def run():
    result = {
        "status": "failed",
        "screenshots": [],
        "notes": "",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--font-render-hinting=none",
            ],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        # Disable font loading to avoid screenshot hangs
        context.route("**/*.woff2", lambda route: route.abort())
        context.route("**/*.woff", lambda route: route.abort())
        context.route("**/*.ttf", lambda route: route.abort())

        page = context.new_page()

        try:
            print(f"Navigating to: {JOB_URL}")
            page.goto(JOB_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            print(f"Page title: {page.title()}")
            print(f"URL: {page.url()}")

            result["screenshots"].append(screenshot(page, "01-job-page-loaded"))

            # Wait for form
            try:
                page.wait_for_selector("form", timeout=20000)
                print("Form found on page")
            except PlaywrightTimeout:
                print("No form found within timeout — checking page content")
                html_snippet = page.content()[:2000]
                print(html_snippet)
                result["notes"] = "No form found on page"
                result["screenshots"].append(screenshot(page, "error-no-form"))
                return result

            result["screenshots"].append(screenshot(page, "02-form-visible"))

            # Log all inputs
            log_all_inputs(page)

            # --- Fill basic fields (Greenhouse standard field names) ---
            try_fill(page,
                ["input#first_name", "input[name='job_application[first_name]']"],
                CANDIDATE["first_name"], "first name")

            try_fill(page,
                ["input#last_name", "input[name='job_application[last_name]']"],
                CANDIDATE["last_name"], "last name")

            try_fill(page,
                ["input#email", "input[name='job_application[email]']", "input[type='email']"],
                CANDIDATE["email"], "email")

            try_fill(page,
                ["input#phone", "input[name='job_application[phone]']", "input[type='tel']"],
                CANDIDATE["phone"], "phone")

            result["screenshots"].append(screenshot(page, "03-basic-fields-filled"))

            # --- Upload Resume ---
            if os.path.exists(RESUME_PDF):
                file_inputs = page.locator("input[type='file']").all()
                uploaded = False
                for fi in file_inputs:
                    try:
                        fi_id = fi.get_attribute("id") or ""
                        fi_name = fi.get_attribute("name") or ""
                        # Upload resume to the first file input or one that mentions resume
                        if not uploaded or "resume" in fi_id.lower() or "resume" in fi_name.lower():
                            fi.set_input_files(RESUME_PDF)
                            print(f"Resume uploaded to input id={fi_id} name={fi_name}")
                            uploaded = True
                            page.wait_for_timeout(2000)
                    except Exception as e:
                        print(f"  Could not upload to file input: {e}")
                if uploaded:
                    result["screenshots"].append(screenshot(page, "04-resume-uploaded"))
                else:
                    print("WARNING: No file inputs found for resume upload")
            else:
                print(f"WARNING: Resume PDF not found: {RESUME_PDF}")

            # --- LinkedIn ---
            try_fill(page,
                ["input#job_application_answers_attributes_0_text_value",
                 "input[id*='linkedin']", "input[name*='linkedin']",
                 "input[placeholder*='LinkedIn']", "input[placeholder*='linkedin']"],
                CANDIDATE["linkedin"], "LinkedIn URL")

            # --- Handle all custom questions ---
            # Find all labels with their associated inputs
            labels = page.locator("label").all()
            for lbl in labels:
                try:
                    lbl_text = (lbl.text_content() or "").strip().lower()
                    lbl_for = lbl.get_attribute("for") or ""
                    if not lbl_for:
                        continue

                    target = page.locator(f"#{lbl_for}").first
                    if target.count() == 0:
                        continue

                    tag = target.evaluate("e => e.tagName").lower()
                    current_val = target.evaluate("e => e.value").strip()

                    if current_val:
                        continue  # already filled

                    print(f"Found unfilled field: label='{lbl_text}' id={lbl_for} tag={tag}")

                    if tag == "textarea":
                        if "cover" in lbl_text or "letter" in lbl_text:
                            target.fill(COVER_LETTER_TEXT)
                            print(f"  -> Filled as cover letter")
                        elif "experience" in lbl_text or "auth" in lbl_text or "iam" in lbl_text:
                            target.fill(
                                "I have experience building and integrating OAuth2/OIDC authentication flows "
                                "in .NET and Python applications. I have worked with third-party identity providers "
                                "and implemented role-based access control in REST APIs. I am eager to deepen "
                                "this expertise with SAML, SCIM, and cloud IAM standards (Auth0, AWS IAM, etc.)."
                            )
                            print(f"  -> Filled as auth experience")
                        elif any(kw in lbl_text for kw in ["why", "motivation", "interest", "tell us"]):
                            target.fill(
                                "I am excited by ClickHouse's position as a leader in real-time analytics. "
                                "The Platform Auth team's mission to build a unified customer identity layer "
                                "is technically fascinating and critically important. My background in .NET, "
                                "Python, and cloud-native systems — combined with my passion for security and "
                                "developer experience — makes this a perfect fit."
                            )
                            print(f"  -> Filled as motivation")
                        else:
                            target.fill("Experienced software engineer with .NET, Python, and cloud systems background.")
                            print(f"  -> Filled with generic answer")

                    elif tag == "input":
                        if "linkedin" in lbl_text:
                            target.fill(CANDIDATE["linkedin"])
                            print(f"  -> Filled LinkedIn")
                        elif "github" in lbl_text or "portfolio" in lbl_text:
                            target.fill(CANDIDATE["github"])
                            print(f"  -> Filled GitHub")
                        elif "location" in lbl_text or "city" in lbl_text:
                            target.fill(CANDIDATE["location"])
                            print(f"  -> Filled location")
                        elif "website" in lbl_text or "url" in lbl_text:
                            target.fill(CANDIDATE["linkedin"])
                            print(f"  -> Filled website with LinkedIn")

                    elif tag == "select":
                        options = target.locator("option").all()
                        option_texts = [opt.text_content() or "" for opt in options]
                        print(f"  Select options: {option_texts}")

                        if "visa" in lbl_text or "sponsor" in lbl_text or "authoriz" in lbl_text:
                            for opt in option_texts:
                                if "no" in opt.lower() and len(opt.strip()) < 5:
                                    try:
                                        target.select_option(label=opt)
                                        print(f"  -> Selected '{opt}' for visa/sponsorship")
                                    except Exception:
                                        pass
                                    break
                            else:
                                try:
                                    target.select_option(label="No")
                                    print(f"  -> Selected 'No' for visa/sponsorship")
                                except Exception as e2:
                                    print(f"  -> Could not set visa select: {e2}")

                        elif any(kw in lbl_text for kw in ["gender", "race", "veteran", "disability"]):
                            decline_keywords = ["decline", "prefer not", "don't wish", "not answer", "no answer", "i don't"]
                            for opt_text in option_texts:
                                if any(kw in opt_text.lower() for kw in decline_keywords):
                                    try:
                                        target.select_option(label=opt_text)
                                        print(f"  -> Selected EEOC decline: '{opt_text}'")
                                    except Exception:
                                        pass
                                    break

                except Exception as e:
                    print(f"  (error processing label: {e})")

            result["screenshots"].append(screenshot(page, "05-all-fields-filled"))

            # Final form state log
            log_all_inputs(page)
            result["screenshots"].append(screenshot(page, "06-before-submit"))

            # --- Find and click Submit ---
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "button:has-text('Submit Application')",
                "button:has-text('Submit')",
                "button:has-text('Apply')",
            ]

            submit_btn = None
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        btn_text = btn.text_content() or btn.get_attribute("value") or "Submit"
                        print(f"Found submit button with selector '{sel}': '{btn_text}'")
                        submit_btn = btn
                        break
                except Exception:
                    continue

            if submit_btn:
                print("Clicking Submit...")
                submit_btn.click()
                page.wait_for_timeout(6000)
                result["screenshots"].append(screenshot(page, "07-after-submit"))

                final_url = page.url()
                print(f"Final URL: {final_url}")

                try:
                    final_content = page.content().lower()
                except Exception:
                    final_content = ""

                success_signals = [
                    "thank you" in final_content,
                    "application received" in final_content,
                    "successfully submitted" in final_content,
                    "we've received" in final_content,
                    "we have received" in final_content,
                    "confirmation" in final_url,
                    "success" in final_url,
                    "thank" in final_url,
                ]

                if any(success_signals):
                    print("SUCCESS: Application submitted!")
                    result["status"] = "applied"
                    result["notes"] = "Application submitted successfully"
                else:
                    # Check for validation errors
                    try:
                        errors = page.locator(".error, .field_with_errors, [class*='error']:not(script)").all()
                        error_texts = []
                        for err in errors[:10]:
                            try:
                                t = err.text_content()
                                if t and t.strip() and len(t.strip()) < 200:
                                    error_texts.append(t.strip())
                            except Exception:
                                pass
                        if error_texts:
                            print(f"VALIDATION ERRORS: {error_texts}")
                            result["notes"] = f"Validation errors after submit: {'; '.join(error_texts[:3])}"
                        else:
                            print("UNCERTAIN: Could not confirm submission. Check screenshots.")
                            result["notes"] = "Submitted, could not confirm success from page content. Manual check required."
                            result["status"] = "applied"
                    except Exception:
                        result["status"] = "applied"
                        result["notes"] = "Submitted but confirmation unclear"

                result["screenshots"].append(screenshot(page, "08-final-state"))
            else:
                print("ERROR: Submit button not found")
                result["notes"] = "Submit button not found on form"
                result["screenshots"].append(screenshot(page, "error-no-submit"))

        except PlaywrightTimeout as e:
            print(f"TIMEOUT: {e}")
            result["notes"] = f"Timeout error: {e}"
            try:
                result["screenshots"].append(screenshot(page, "error-timeout"))
            except Exception:
                pass
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            result["notes"] = f"Exception: {e}"
            try:
                result["screenshots"].append(screenshot(page, "error-exception"))
            except Exception:
                pass
        finally:
            browser.close()

    return result


def update_applications(result):
    with open(APPLICATIONS_JSON, "r") as f:
        apps = json.load(f)

    # Remove any previous failed attempt for same job
    apps = [a for a in apps if a.get("id") != "app-clickhouse-cloud-iam-001"]

    new_entry = {
        "id": "app-clickhouse-cloud-iam-001",
        "company": "ClickHouse",
        "role": "Cloud Software Engineer - Identity and Access Management",
        "url": JOB_URL,
        "date_applied": str(date.today()),
        "score": 8.0,
        "status": result["status"],
        "resume_file": RESUME_PDF,
        "cover_letter_file": COVER_LETTER_PATH,
        "screenshot": result["screenshots"][-1] if result["screenshots"] else "",
        "all_screenshots": result["screenshots"],
        "notes": result["notes"],
        "response": "",
    }

    apps.append(new_entry)

    with open(APPLICATIONS_JSON, "w") as f:
        json.dump(apps, f, indent=2)

    print(f"\nApplication logged to {APPLICATIONS_JSON}")
    return new_entry


if __name__ == "__main__":
    print("=" * 60)
    print("ClickHouse - Cloud Software Engineer IAM Application")
    print("=" * 60)
    result = run()
    entry = update_applications(result)
    print("\n--- SUMMARY ---")
    print(json.dumps(entry, indent=2))
