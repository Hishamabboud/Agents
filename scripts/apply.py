#!/usr/bin/env python3
"""
Application Submitter — automates job application form filling via Playwright.

Uses Playwright browser automation to:
- Navigate to job application pages
- Fill in personal details
- Upload tailored resume
- Type/paste cover letter
- Take screenshots before submission
- Submit and log results

This script is designed to work standalone OR be called by the Job Applier agent
which uses Playwright MCP for more intelligent form handling.

Usage:
    python3 scripts/apply.py
    python3 scripts/apply.py --max-applications 5
    python3 scripts/apply.py --dry-run
"""

import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILE_DIR = BASE_DIR / "profile"
OUTPUT_DIR = BASE_DIR / "output"
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"

# Rate limiting
MIN_DELAY_BETWEEN_APPS = 30  # seconds
MAX_DELAY_BETWEEN_APPS = 60  # seconds


def load_preferences() -> dict:
    """Load personal details from preferences."""
    prefs_path = PROFILE_DIR / "preferences.md"
    if not prefs_path.exists():
        print("ERROR: preferences.md not found")
        sys.exit(1)

    content = prefs_path.read_text()
    details = {}

    in_details = False
    for line in content.splitlines():
        line = line.strip()
        if "My Details for Forms" in line:
            in_details = True
            continue
        if line.startswith("## ") and in_details:
            break

        if in_details and line.startswith("- "):
            match = re.match(r"-\s*(.+?):\s*(.+)", line)
            if match:
                key = match.group(1).strip().lower().replace(" ", "_")
                value = match.group(2).strip()
                if value != "[FILL IN]":
                    details[key] = value

    return details


def load_tailored_manifest() -> list[dict]:
    """Load the manifest of tailored resumes/cover letters."""
    manifest_path = DATA_DIR / "tailored-manifest.json"
    if not manifest_path.exists():
        print("ERROR: tailored-manifest.json not found. Run tailor.py first.")
        sys.exit(1)
    try:
        return json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in tailored-manifest.json: {e}")
        sys.exit(1)


def load_applications() -> list[dict]:
    """Load existing applications tracker."""
    apps_path = DATA_DIR / "applications.json"
    if not apps_path.exists():
        return []
    try:
        return json.loads(apps_path.read_text())
    except json.JSONDecodeError:
        return []


def save_applications(applications: list[dict]) -> None:
    """Save applications tracker."""
    apps_path = DATA_DIR / "applications.json"
    apps_path.write_text(json.dumps(applications, indent=2, ensure_ascii=False))


def is_already_applied(url: str, applications: list[dict]) -> bool:
    """Check if we've already applied to this URL."""
    return any(app.get("url") == url for app in applications)


def detect_ats_platform(url: str) -> str:
    """Detect the ATS platform from the URL."""
    url_lower = url.lower()

    if "greenhouse.io" in url_lower or "boards.greenhouse" in url_lower:
        return "greenhouse"
    elif "lever.co" in url_lower or "jobs.lever" in url_lower:
        return "lever"
    elif "workday" in url_lower or "myworkdayjobs" in url_lower:
        return "workday"
    elif "smartrecruiters" in url_lower:
        return "smartrecruiters"
    elif "indeed.com" in url_lower:
        return "indeed"
    elif "linkedin.com" in url_lower:
        return "linkedin"
    elif "recruitee" in url_lower:
        return "recruitee"
    elif "bamboohr" in url_lower:
        return "bamboohr"
    else:
        return "unknown"


async def apply_with_playwright(
    job: dict,
    details: dict,
    resume_path: Path,
    cover_letter_path: Path,
    dry_run: bool = False,
) -> dict:
    """
    Apply to a job using Playwright browser automation.

    Returns a dict with application result.
    """
    from playwright.async_api import async_playwright

    url = job.get("url", "")
    company = job.get("company", "unknown")
    title = job.get("title", "unknown")
    ats = detect_ats_platform(url)

    result = {
        "id": str(uuid.uuid4()),
        "company": company,
        "role": title,
        "url": url,
        "date_applied": datetime.now().strftime("%Y-%m-%d"),
        "score": job.get("score", 0),
        "status": "pending",
        "resume_file": str(resume_path.relative_to(BASE_DIR)) if resume_path.exists() else "",
        "cover_letter_file": str(cover_letter_path.relative_to(BASE_DIR)) if cover_letter_path.exists() else "",
        "screenshot": "",
        "notes": f"ATS: {ats}",
        "response": "pending",
    }

    if dry_run:
        result["status"] = "skipped"
        result["notes"] = f"[DRY RUN] Would apply via {ats}"
        return result

    # Read cover letter content
    cover_text = ""
    if cover_letter_path.exists():
        cover_text = cover_letter_path.read_text()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()

            print(f"    Navigating to {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # Look for "Apply" button
            apply_buttons = await page.query_selector_all(
                'button:has-text("Apply"), a:has-text("Apply"), '
                'button:has-text("Solliciteer"), a:has-text("Solliciteer"), '
                'button:has-text("Apply Now"), a:has-text("Apply Now")'
            )

            if apply_buttons:
                print(f"    Found {len(apply_buttons)} apply button(s), clicking first...")
                await apply_buttons[0].click()
                await page.wait_for_timeout(3000)

            # Try to fill common form fields
            form_fields = {
                'input[name*="name" i], input[id*="name" i], input[placeholder*="name" i]': details.get("full_name", ""),
                'input[name*="email" i], input[id*="email" i], input[type="email"]': details.get("email", ""),
                'input[name*="phone" i], input[id*="phone" i], input[type="tel"]': details.get("phone", ""),
                'input[name*="linkedin" i], input[id*="linkedin" i]': details.get("linkedin", ""),
                'input[name*="github" i], input[id*="github" i]': details.get("github", ""),
                'input[name*="city" i], input[id*="city" i]': details.get("city", "Eindhoven"),
            }

            fields_filled = 0
            for selector, value in form_fields.items():
                if not value:
                    continue
                try:
                    elements = await page.query_selector_all(selector)
                    for el in elements:
                        if await el.is_visible():
                            await el.fill(value)
                            fields_filled += 1
                            break
                except Exception:
                    continue

            print(f"    Filled {fields_filled} form fields")

            # Try to fill cover letter textarea
            if cover_text:
                cover_selectors = [
                    'textarea[name*="cover" i]',
                    'textarea[id*="cover" i]',
                    'textarea[name*="letter" i]',
                    'textarea[name*="message" i]',
                    'textarea[placeholder*="cover" i]',
                    "textarea",  # Last resort: first textarea
                ]
                for selector in cover_selectors:
                    try:
                        textarea = await page.query_selector(selector)
                        if textarea and await textarea.is_visible():
                            await textarea.fill(cover_text)
                            print(f"    Filled cover letter textarea")
                            break
                    except Exception:
                        continue

            # Try to upload resume
            if resume_path.exists():
                file_inputs = await page.query_selector_all('input[type="file"]')
                if file_inputs:
                    # Look for a PDF version first, fall back to the .md
                    pdf_path = resume_path.with_suffix(".pdf")
                    upload_path = pdf_path if pdf_path.exists() else resume_path
                    try:
                        await file_inputs[0].set_input_files(str(upload_path))
                        print(f"    Uploaded resume: {upload_path.name}")
                    except Exception as e:
                        print(f"    Failed to upload resume: {e}")

            # Screenshot before submission
            SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
            safe_company = re.sub(r"[^\w-]", "", company.lower().replace(" ", "-"))
            safe_title = re.sub(r"[^\w-]", "", title.lower().replace(" ", "-"))
            screenshot_name = f"{safe_company}-{safe_title}.png"
            screenshot_path = SCREENSHOT_DIR / screenshot_name

            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"    Screenshot saved: {screenshot_path.relative_to(BASE_DIR)}")
            result["screenshot"] = str(screenshot_path.relative_to(BASE_DIR))

            # Look for submit button — but DO NOT click unless form seems complete
            submit_buttons = await page.query_selector_all(
                'button[type="submit"], button:has-text("Submit"), '
                'button:has-text("Verzenden"), input[type="submit"]'
            )

            if submit_buttons and fields_filled >= 2:
                print(f"    Found submit button. Submitting...")
                await submit_buttons[0].click()
                await page.wait_for_timeout(5000)

                # Take post-submission screenshot
                post_screenshot = SCREENSHOT_DIR / f"{safe_company}-{safe_title}-submitted.png"
                await page.screenshot(path=str(post_screenshot), full_page=True)

                result["status"] = "applied"
                result["notes"] = f"ATS: {ats}. Form fields filled: {fields_filled}."
                print(f"    Application submitted!")
            else:
                result["status"] = "skipped"
                reason = "No submit button found" if not submit_buttons else f"Too few fields filled ({fields_filled})"
                result["notes"] = f"ATS: {ats}. {reason}. Manual review needed."
                print(f"    Skipped: {reason}")

            await browser.close()

    except Exception as e:
        result["status"] = "failed"
        result["notes"] = f"ATS: {ats}. Error: {str(e)[:200]}"
        print(f"    FAILED: {e}")

    return result


async def run_applications(
    manifest: list[dict],
    details: dict,
    applications: list[dict],
    max_apps: int,
    dry_run: bool,
) -> list[dict]:
    """Run the application process for each job in the manifest."""
    import random

    applied_count = 0
    new_applications = []

    for entry in manifest:
        if applied_count >= max_apps:
            print(f"\nReached max applications limit ({max_apps})")
            break

        job = entry.get("job", {})
        url = job.get("url", "")

        if not url:
            continue

        if is_already_applied(url, applications):
            print(f"\nSkipping (already applied): {job.get('title', '')} @ {job.get('company', '')}")
            continue

        resume_file = entry.get("resume_file", "")
        cover_file = entry.get("cover_letter_file", "")
        resume_path = BASE_DIR / resume_file if resume_file else Path("/dev/null")
        cover_path = BASE_DIR / cover_file if cover_file else Path("/dev/null")

        print(f"\n{'='*60}")
        print(f"Applying: {job.get('title', '')} @ {job.get('company', '')} (score: {job.get('score', '?')})")
        print(f"URL: {url}")

        result = await apply_with_playwright(job, details, resume_path, cover_path, dry_run)
        new_applications.append(result)

        if result["status"] == "applied":
            applied_count += 1

        # Save after each application (in case of crash)
        all_apps = applications + new_applications
        save_applications(all_apps)

        # Rate limiting
        if not dry_run and applied_count < max_apps:
            delay = random.randint(MIN_DELAY_BETWEEN_APPS, MAX_DELAY_BETWEEN_APPS)
            print(f"    Waiting {delay}s before next application...")
            time.sleep(delay)

    return new_applications


def main():
    import asyncio

    parser = argparse.ArgumentParser(description="Job application submitter")
    parser.add_argument("--max-applications", type=int, default=5, help="Max applications per run")
    parser.add_argument("--dry-run", action="store_true", help="Preview without submitting")
    args = parser.parse_args()

    print("Loading data...")
    details = load_preferences()
    manifest = load_tailored_manifest()
    applications = load_applications()

    print(f"  Personal details loaded: {list(details.keys())}")
    print(f"  Jobs with tailored materials: {len(manifest)}")
    print(f"  Previous applications: {len(applications)}")

    if not manifest:
        print("\nNo jobs to apply to. Run tailor.py first.")
        return

    # Check for missing personal details
    required_fields = ["full_name", "email"]
    missing = [f for f in required_fields if f not in details]
    if missing:
        print(f"\nWARNING: Missing required details in preferences.md: {missing}")
        print("Please fill in the [FILL IN] fields in profile/preferences.md")
        if not args.dry_run:
            sys.exit(1)

    print(f"\nStarting application process (max: {args.max_applications})...")
    if args.dry_run:
        print("[DRY RUN MODE - no actual submissions]\n")

    new_apps = asyncio.run(
        run_applications(manifest, details, applications, args.max_applications, args.dry_run)
    )

    # Summary
    applied = sum(1 for a in new_apps if a["status"] == "applied")
    skipped = sum(1 for a in new_apps if a["status"] == "skipped")
    failed = sum(1 for a in new_apps if a["status"] == "failed")

    print(f"\n{'='*60}")
    print(f"Application Summary:")
    print(f"  Applied:  {applied}")
    print(f"  Skipped:  {skipped}")
    print(f"  Failed:   {failed}")
    print(f"  Total:    {len(new_apps)}")
    print(f"\nTracker updated: data/applications.json")


if __name__ == "__main__":
    main()
