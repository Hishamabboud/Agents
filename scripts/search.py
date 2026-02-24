#!/usr/bin/env python3
"""
Job Board Scraper — searches configured job boards and saves raw listings.

Scrapes job listings from Indeed NL, ICTerGezocht, and other boards.
Uses requests + BeautifulSoup for static sites.
For JS-heavy sites (LinkedIn, Glassdoor), outputs instructions for Playwright MCP.

Usage:
    python3 scripts/search.py
    python3 scripts/search.py --keywords "Python Developer" --location "Eindhoven"
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILE_DIR = BASE_DIR / "profile"
LOG_DIR = BASE_DIR / "logs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
}

REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 3  # seconds


def load_preferences() -> dict:
    """Load search preferences from profile/preferences.md."""
    prefs_path = PROFILE_DIR / "preferences.md"
    if not prefs_path.exists():
        print(f"ERROR: Preferences file not found at {prefs_path}")
        sys.exit(1)

    content = prefs_path.read_text()

    preferences = {
        "roles": [],
        "location": "Eindhoven",
        "boards": [],
    }

    # Parse target roles
    in_roles = False
    in_boards = False
    for line in content.splitlines():
        line = line.strip()

        if line.startswith("## Target Roles"):
            in_roles = True
            in_boards = False
            continue
        elif line.startswith("## Job Boards"):
            in_boards = True
            in_roles = False
            continue
        elif line.startswith("## "):
            in_roles = False
            in_boards = False
            continue

        if in_roles and line.startswith("- "):
            role = line[2:].strip()
            if role:
                preferences["roles"].append(role)

        if in_boards and line and line[0].isdigit():
            # Extract board name from numbered list
            match = re.search(r"\d+\.\s+(.+?)(?:\s*\(|$)", line)
            if match:
                preferences["boards"].append(match.group(1).strip())

    # Parse location
    for line in content.splitlines():
        if "Location:" in line:
            loc_match = re.search(r"Location:\s*(.+)", line)
            if loc_match:
                # Take first location option
                preferences["location"] = loc_match.group(1).split(",")[0].strip()
                break

    return preferences


def generate_job_id(url: str) -> str:
    """Generate a deterministic ID from a job URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def scrape_indeed_nl(keyword: str, location: str, max_pages: int = 3) -> list[dict]:
    """Scrape job listings from Indeed NL."""
    jobs = []
    base_url = "https://nl.indeed.com/jobs"

    for page in range(max_pages):
        params = {
            "q": keyword,
            "l": location,
            "start": page * 10,
        }

        try:
            print(f"  Searching Indeed NL: '{keyword}' in {location} (page {page + 1})")
            resp = requests.get(
                base_url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Indeed uses various class patterns for job cards
            job_cards = soup.select("div.job_seen_beacon, div.jobsearch-SerpJobCard, div.result")

            for card in job_cards:
                try:
                    # Title
                    title_el = card.select_one("h2.jobTitle a, a.jcs-JobTitle, h2 a")
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    link = title_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = urljoin("https://nl.indeed.com", link)

                    # Company
                    company_el = card.select_one(
                        "span.companyName, span[data-testid='company-name'], "
                        "div.company_location span.companyName"
                    )
                    company = company_el.get_text(strip=True) if company_el else "Unknown"

                    # Location
                    loc_el = card.select_one(
                        "div.companyLocation, div[data-testid='text-location']"
                    )
                    job_location = loc_el.get_text(strip=True) if loc_el else location

                    # Description snippet
                    desc_el = card.select_one("div.job-snippet, td.resultContent div.css-1dbjc4n")
                    description = desc_el.get_text(strip=True) if desc_el else ""

                    # Salary (if available)
                    salary_el = card.select_one(
                        "div.salary-snippet-container, span.estimated-salary, "
                        "div[data-testid='attribute_snippet_testid']"
                    )
                    salary = salary_el.get_text(strip=True) if salary_el else ""

                    if link:
                        jobs.append({
                            "id": generate_job_id(link),
                            "title": title,
                            "company": company,
                            "location": job_location,
                            "url": link,
                            "description": description,
                            "salary": salary,
                            "date_posted": "",
                            "source": "Indeed NL",
                            "scraped_at": datetime.now().isoformat(),
                        })

                except Exception as e:
                    print(f"    Warning: Failed to parse a job card: {e}")
                    continue

            time.sleep(DELAY_BETWEEN_REQUESTS)

        except requests.RequestException as e:
            print(f"    Error fetching Indeed NL page {page + 1}: {e}")
            break

    return jobs


def scrape_ictergezocht(keyword: str, location: str) -> list[dict]:
    """Scrape job listings from ICTerGezocht.nl."""
    jobs = []
    search_url = f"https://www.ictergezocht.nl/vacatures?q={quote_plus(keyword)}&location={quote_plus(location)}"

    try:
        print(f"  Searching ICTerGezocht: '{keyword}' in {location}")
        resp = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # ICTerGezocht job listing cards
        job_cards = soup.select("div.vacancy-item, article.vacancy, div.search-result")

        for card in job_cards:
            try:
                title_el = card.select_one("h2 a, h3 a, a.vacancy-title")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = urljoin("https://www.ictergezocht.nl", link)

                company_el = card.select_one("span.company, div.company-name")
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                loc_el = card.select_one("span.location, div.vacancy-location")
                job_location = loc_el.get_text(strip=True) if loc_el else location

                desc_el = card.select_one("div.description, p.vacancy-description")
                description = desc_el.get_text(strip=True) if desc_el else ""

                if link:
                    jobs.append({
                        "id": generate_job_id(link),
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "url": link,
                        "description": description,
                        "salary": "",
                        "date_posted": "",
                        "source": "ICTerGezocht",
                        "scraped_at": datetime.now().isoformat(),
                    })

            except Exception as e:
                print(f"    Warning: Failed to parse ICTerGezocht card: {e}")
                continue

    except requests.RequestException as e:
        print(f"    Error fetching ICTerGezocht: {e}")

    return jobs


def scrape_werkenbij(keyword: str, location: str) -> list[dict]:
    """Scrape job listings from werkenbij.nl."""
    jobs = []
    search_url = f"https://www.werkenbij.nl/vacatures?query={quote_plus(keyword)}&location={quote_plus(location)}"

    try:
        print(f"  Searching Werkenbij: '{keyword}' in {location}")
        resp = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.select("div.vacancy-card, article.vacancy, li.search-result")

        for card in job_cards:
            try:
                title_el = card.select_one("h2 a, h3 a, a.vacancy-link")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = urljoin("https://www.werkenbij.nl", link)

                company_el = card.select_one("span.company, div.company")
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                loc_el = card.select_one("span.location, div.location")
                job_location = loc_el.get_text(strip=True) if loc_el else location

                desc_el = card.select_one("div.description, p.summary")
                description = desc_el.get_text(strip=True) if desc_el else ""

                if link:
                    jobs.append({
                        "id": generate_job_id(link),
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "url": link,
                        "description": description,
                        "salary": "",
                        "date_posted": "",
                        "source": "Werkenbij",
                        "scraped_at": datetime.now().isoformat(),
                    })

            except Exception as e:
                print(f"    Warning: Failed to parse Werkenbij card: {e}")
                continue

    except requests.RequestException as e:
        print(f"    Error fetching Werkenbij: {e}")

    return jobs


def generate_linkedin_urls(keyword: str, location: str) -> list[dict]:
    """
    Generate LinkedIn search URLs for Playwright MCP to navigate.
    LinkedIn requires JS rendering and authentication, so we output
    URLs for the agent to handle via browser automation.
    """
    encoded_keyword = quote_plus(keyword)
    # LinkedIn geoId for Eindhoven area / Netherlands
    geo_id = "102890719"  # Netherlands

    urls = [
        {
            "board": "LinkedIn",
            "search_url": (
                f"https://www.linkedin.com/jobs/search/"
                f"?keywords={encoded_keyword}"
                f"&location={quote_plus(location)}"
                f"&geoId={geo_id}"
                f"&f_TPR=r604800"  # Past week
            ),
            "note": "Requires login. Use Playwright MCP to navigate and scrape.",
        }
    ]
    return urls


def generate_glassdoor_urls(keyword: str, location: str) -> list[dict]:
    """Generate Glassdoor search URLs for Playwright MCP."""
    encoded_keyword = quote_plus(keyword)
    return [
        {
            "board": "Glassdoor NL",
            "search_url": (
                f"https://www.glassdoor.nl/Vacature/"
                f"{quote_plus(location)}-{encoded_keyword}-vacatures-"
                f"SRCH_IL.0,{len(location)}_IC{quote_plus(location)}_KO{len(location)+1},{len(location)+1+len(keyword)}.htm"
            ),
            "note": "May require Playwright MCP for full rendering.",
        }
    ]


def generate_stepstone_urls(keyword: str, location: str) -> list[dict]:
    """Generate StepStone NL search URLs for Playwright MCP."""
    encoded_keyword = quote_plus(keyword)
    return [
        {
            "board": "StepStone NL",
            "search_url": (
                f"https://www.stepstone.nl/vacatures/{encoded_keyword}/in-{quote_plus(location)}"
            ),
            "note": "May require Playwright MCP for full rendering.",
        }
    ]


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    """Remove duplicate jobs based on URL."""
    seen_urls = set()
    unique = []
    for job in jobs:
        url = job.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(job)
    return unique


def load_existing_jobs() -> list[dict]:
    """Load previously scraped jobs to avoid re-adding."""
    raw_path = DATA_DIR / "raw-jobs.json"
    if raw_path.exists():
        try:
            return json.loads(raw_path.read_text())
        except json.JSONDecodeError:
            return []
    return []


def merge_jobs(existing: list[dict], new_jobs: list[dict]) -> list[dict]:
    """Merge new jobs into existing list, avoiding duplicates."""
    existing_urls = {job["url"] for job in existing}
    merged = list(existing)
    added = 0
    for job in new_jobs:
        if job["url"] not in existing_urls:
            merged.append(job)
            existing_urls.add(job["url"])
            added += 1
    print(f"  Added {added} new jobs (total: {len(merged)})")
    return merged


def main():
    parser = argparse.ArgumentParser(description="Job board scraper")
    parser.add_argument("--keywords", type=str, help="Override search keywords (comma-separated)")
    parser.add_argument("--location", type=str, help="Override search location")
    parser.add_argument("--max-pages", type=int, default=3, help="Max pages per board")
    args = parser.parse_args()

    # Load preferences
    prefs = load_preferences()
    keywords = args.keywords.split(",") if args.keywords else prefs["roles"]
    location = args.location or prefs["location"]

    print(f"Job Search Configuration:")
    print(f"  Keywords: {keywords}")
    print(f"  Location: {location}")
    print()

    # Collect all scraped jobs
    all_jobs: list[dict] = []

    # Scrape static boards
    for keyword in keywords:
        keyword = keyword.strip()
        print(f"\nSearching for: '{keyword}'")

        # Indeed NL
        indeed_jobs = scrape_indeed_nl(keyword, location, max_pages=args.max_pages)
        all_jobs.extend(indeed_jobs)
        print(f"    Indeed NL: {len(indeed_jobs)} listings found")

        # ICTerGezocht
        ict_jobs = scrape_ictergezocht(keyword, location)
        all_jobs.extend(ict_jobs)
        print(f"    ICTerGezocht: {len(ict_jobs)} listings found")

        # Werkenbij
        werkenbij_jobs = scrape_werkenbij(keyword, location)
        all_jobs.extend(werkenbij_jobs)
        print(f"    Werkenbij: {len(werkenbij_jobs)} listings found")

        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Deduplicate
    all_jobs = deduplicate_jobs(all_jobs)
    print(f"\nTotal unique jobs scraped: {len(all_jobs)}")

    # Merge with existing
    existing_jobs = load_existing_jobs()
    merged = merge_jobs(existing_jobs, all_jobs)

    # Save raw jobs
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = DATA_DIR / "raw-jobs.json"
    raw_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    print(f"Saved to {raw_path}")

    # Generate URLs for JS-heavy boards (for Playwright MCP)
    js_boards: list[dict] = []
    for keyword in keywords:
        keyword = keyword.strip()
        js_boards.extend(generate_linkedin_urls(keyword, location))
        js_boards.extend(generate_glassdoor_urls(keyword, location))
        js_boards.extend(generate_stepstone_urls(keyword, location))

    if js_boards:
        js_path = DATA_DIR / "js-board-urls.json"
        js_path.write_text(json.dumps(js_boards, indent=2, ensure_ascii=False))
        print(f"\nGenerated {len(js_boards)} URLs for JS-heavy boards (Playwright MCP required)")
        print(f"Saved to {js_path}")

    print("\nSearch phase complete.")


if __name__ == "__main__":
    main()
