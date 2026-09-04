#!/usr/bin/env python3
"""
English-language NL job search.

Searches sources that carry English-language vacancies located in the
Netherlands, applies a hard Netherlands location gate, tags each listing
with its language, and removes anything already applied to or blocklisted.

Sources:
  - englishjobsearch.nl  (English-only NL aggregator, static HTML)
  - Greenhouse job board API (per-company, English-first NL employers)

Usage:
    python3 scripts/search_english_nl.py
    python3 scripts/search_english_nl.py --pages 3 --out data/new-jobs.json
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILE_DIR = BASE_DIR / "profile"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
}
TIMEOUT = 30
DELAY = 2

# Queries map to englishjobsearch.nl URL slugs.
EJS_QUERIES = [
    "software_engineer",
    "net_developer",
    "c_developer",
    "python_developer",
    "full_stack_developer",
    "backend_developer",
]

# Greenhouse board tokens for employers that hire in the Netherlands and
# post in English. Verified reachable via boards-api.greenhouse.io.
GREENHOUSE_BOARDS = [
    "adyen",
    "optiver",
    "elastic",
    "gitlab",
    "trivago",
    "catawiki",
    "databricks",
]

# --- Netherlands location gate ---------------------------------------------

NL_CITIES = {
    "amsterdam", "rotterdam", "the hague", "den haag", "utrecht", "eindhoven",
    "groningen", "tilburg", "almere", "breda", "nijmegen", "apeldoorn",
    "haarlem", "arnhem", "enschede", "amersfoort", "zaanstad", "hertogenbosch",
    "den bosch", "zwolle", "leiden", "leeuwarden", "maastricht", "dordrecht",
    "ede", "alphen aan den rijn", "westland", "alkmaar", "emmen", "delft",
    "venlo", "deventer", "helmond", "oss", "amstelveen", "hilversum",
    "heerlen", "hengelo", "purmerend", "roosendaal", "schiedam", "spijkenisse",
    "vlaardingen", "almelo", "gouda", "zoetermeer", "lelystad", "veldhoven",
    "hoofddorp", "capelle aan den ijssel", "nieuwegein", "veenendaal",
    "woerden", "waalwijk", "drachten", "sittard", "assen", "hoorn",
    "middelburg", "vlissingen", "terneuzen", "bergen op zoom", "uden",
    "veghel", "best", "geldrop", "valkenswaard", "son en breugel", "nuenen",
    "wageningen", "houten", "zeist", "bunnik", "soest", "baarn", "naarden",
    "bussum", "weesp", "diemen", "duiven", "doetinchem", "zutphen",
    "harderwijk", "barneveld", "nunspeet", "epe", "raalte", "rijssen",
    "oldenzaal", "losser", "borne", "goor", "delden", "haaksbergen",
}

NL_PROVINCES = {
    "noord-brabant", "north brabant", "noord-holland", "north holland",
    "zuid-holland", "south holland", "gelderland", "utrecht", "overijssel",
    "limburg", "friesland", "fryslan", "groningen", "drenthe", "flevoland",
    "zeeland",
}

NL_COUNTRY = {"netherlands", "nederland", "the netherlands", "holland", "nl"}

# Locations that look Dutch-adjacent but are not in the Netherlands.
NON_NL_HINTS = {
    "belgium", "germany", "deutschland", "france", "spain", "portugal",
    "poland", "romania", "bulgaria", "india", "united states", "usa",
    "united kingdom", "london", "berlin", "paris", "madrid", "lisbon",
    "warsaw", "bucharest", "dublin", "brussels", "antwerp", "dusseldorf",
    "hamburg", "munich", "cologne", "frankfurt", "milan", "barcelona",
    "singapore", "canada", "australia", "brazil", "mexico", "japan",
}


def is_in_netherlands(location: str, extra_text: str = "") -> tuple[bool, str]:
    """
    Hard gate: the job must be located in the Netherlands.

    Returns (passes, reason). Remote roles only pass when the listing shows
    a Netherlands tie somewhere in the location or supporting text.
    """
    loc = (location or "").lower().strip()
    if not loc:
        return False, "no location given"

    # Explicit non-NL country wins over anything else.
    for hint in NON_NL_HINTS:
        if re.search(rf"\b{re.escape(hint)}\b", loc):
            # "Amsterdam, Netherlands / London" style multi-location listings
            # still pass if a Dutch location is named too.
            if not _has_nl_token(loc):
                return False, f"located outside NL ({hint})"

    if _has_nl_token(loc):
        return True, "NL location"

    if "remote" in loc or "hybrid" in loc:
        combined = f"{loc} {(extra_text or '').lower()}"
        if _has_nl_token(combined):
            return True, "remote with NL tie"
        return False, "remote without NL tie"

    return False, "no NL location match"


def _has_nl_token(text: str) -> bool:
    """True when the text names a Dutch city, province or the country."""
    for token in NL_COUNTRY | NL_CITIES | NL_PROVINCES:
        if re.search(rf"\b{re.escape(token)}\b", text):
            return True
    return False


# --- Language detection -----------------------------------------------------

DUTCH_STOPWORDS = {
    "de", "het", "een", "en", "van", "voor", "met", "je", "we", "bij", "aan",
    "wij", "onze", "ons", "jij", "jouw", "zijn", "wordt", "worden", "naar",
    "die", "dat", "deze", "als", "ook", "maar", "over", "door", "uit", "op",
    "werken", "ervaring", "kennis", "binnen", "samen", "functie", "jaar",
}
ENGLISH_STOPWORDS = {
    "the", "and", "for", "with", "you", "we", "our", "your", "are", "is",
    "will", "have", "this", "that", "from", "they", "their", "about", "into",
    "experience", "team", "work", "years", "role", "within", "together",
}

DUTCH_REQUIRED_PATTERNS = [
    r"dutch\s+(?:language\s+)?(?:is\s+)?(?:required|mandatory|essential|a\s+must)",
    r"fluent\s+in\s+dutch",
    r"dutch\s+speaking",
    r"native\s+dutch",
    r"nederlands\s+sprekend",
    r"beheersing\s+van\s+de\s+nederlandse\s+taal",
    r"nederlandse\s+taal\s+(?:in\s+woord\s+en\s+geschrift|vereist)",
    r"goede\s+beheersing\s+van\s+het\s+nederlands",
]


def detect_language(text: str) -> str:
    """Classify a listing as 'en', 'nl' or 'unknown' by stopword frequency."""
    words = re.findall(r"[a-zàéëïöü]+", (text or "").lower())
    if len(words) < 15:
        return "unknown"
    nl_hits = sum(1 for w in words if w in DUTCH_STOPWORDS)
    en_hits = sum(1 for w in words if w in ENGLISH_STOPWORDS)
    if nl_hits > en_hits * 1.2:
        return "nl"
    if en_hits > nl_hits * 1.2:
        return "en"
    return "unknown"


def requires_dutch(text: str) -> bool:
    """True when the listing explicitly demands Dutch fluency."""
    lowered = (text or "").lower()
    return any(re.search(p, lowered) for p in DUTCH_REQUIRED_PATTERNS)


# --- Dedupe helpers ---------------------------------------------------------

# Brand names that belong to an already-tracked legal entity. Job boards list
# the brand while applications.json records the entity, so without this map a
# role already applied to reads as new (e.g. Squla is FutureWhiz, applied
# 2026-06-25).
COMPANY_ALIASES = {
    "squla": "futurewhiz",
    "scoyo": "futurewhiz",
    "bimcollab": "kubus",
    "independer": "dpgmedia",
    "speedhive": "mylaps",
    "sporthive": "mylaps",
    "tournamentsoftware": "visualreality",
}


def normalize_company(name: str) -> str:
    """Normalize a company name so 'CM.com' and 'cm com' collide."""
    cleaned = re.sub(r"\b(b\.?v\.?|n\.?v\.?|holding|group|nederland|netherlands)\b", " ", (name or "").lower())
    # Listings often join a parent and a brand ("KUBUS / BIMcollab"); resolve
    # each part so either half matches the tracked entity.
    for part in re.split(r"[/|,]|\s+-\s+", cleaned):
        part_key = re.sub(r"[^a-z0-9]", "", part)
        if part_key in COMPANY_ALIASES:
            return COMPANY_ALIASES[part_key]
    key = re.sub(r"[^a-z0-9]", "", cleaned)
    return COMPANY_ALIASES.get(key, key)


def load_applied() -> tuple[set[str], set[str]]:
    """Return (applied company keys, applied URLs) from the tracker."""
    path = DATA_DIR / "applications.json"
    if not path.exists():
        return set(), set()
    try:
        apps = json.loads(path.read_text())
    except json.JSONDecodeError:
        return set(), set()
    companies = {normalize_company(a.get("company", "")) for a in apps if a.get("company")}
    urls = {a["url"] for a in apps if a.get("url")}
    companies.discard("")
    return companies, urls


def load_blocklist() -> set[str]:
    """Parse the 'Blocked Companies' section out of preferences.md."""
    path = PROFILE_DIR / "preferences.md"
    if not path.exists():
        return set()
    blocked = set()
    in_section = False
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = "blocked companies" in stripped.lower()
            continue
        if in_section and stripped.startswith("- "):
            name = stripped[2:].split("—")[0].split("(")[0].strip()
            if name:
                blocked.add(normalize_company(name))
    blocked.discard("")
    return blocked


def job_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


# --- Scrapers ---------------------------------------------------------------

def scrape_englishjobsearch(query: str, pages: int) -> list[dict]:
    """Scrape englishjobsearch.nl, an English-only aggregator for NL roles."""
    jobs = []
    for page in range(1, pages + 1):
        url = f"https://englishjobsearch.nl/jobs/{query}"
        params = {"page": page} if page > 1 else {}
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"    englishjobsearch '{query}' page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        links = [a for a in soup.find_all("a", href=True) if "clickout" in a["href"]]
        if not links:
            break

        for link in links:
            card = link.parent
            title_el = card.select_one("h3")
            title = title_el.get_text(" ", strip=True) if title_el else link.get_text(" ", strip=True)

            # The card's <ul> holds company, location and posting date.
            meta = [li.get_text(" ", strip=True) for li in card.select("ul li")]
            company = meta[0] if len(meta) > 0 else "Unknown"
            location = meta[1] if len(meta) > 1 else ""
            posted = meta[2] if len(meta) > 2 else ""

            desc_el = card.select_one("div.text-gray-400")
            description = desc_el.get_text(" ", strip=True) if desc_el else ""

            href = link["href"]
            full_url = href if href.startswith("http") else f"https://englishjobsearch.nl{href}"

            jobs.append({
                "id": job_id(full_url.split("?")[0]),
                "title": title,
                "company": company,
                "location": location,
                "url": full_url,
                "description": description,
                "salary": "",
                "date_posted": posted,
                "source": "englishjobsearch.nl",
                "search_query": query,
                "scraped_at": datetime.now().isoformat(),
            })

        time.sleep(DELAY)
    return jobs


def fetch_greenhouse(board: str) -> list[dict]:
    """Fetch a company's Greenhouse board and keep the NL-located roles."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"    greenhouse '{board}': {e}")
        return []

    jobs = []
    for item in payload.get("jobs", []):
        location = (item.get("location") or {}).get("name", "")
        content = item.get("content", "") or ""
        # Greenhouse returns HTML-escaped content; strip to plain text.
        description = BeautifulSoup(content, "html.parser").get_text(" ", strip=True)
        jobs.append({
            "id": job_id(item.get("absolute_url", "")),
            "title": item.get("title", ""),
            "company": board.title(),
            "location": location,
            "url": item.get("absolute_url", ""),
            "description": description[:4000],
            "salary": "",
            "date_posted": (item.get("updated_at") or "")[:10],
            "source": f"greenhouse:{board}",
            "search_query": "",
            "scraped_at": datetime.now().isoformat(),
        })
    return jobs


# --- Relevance --------------------------------------------------------------

ROLE_KEYWORDS = [
    "software engineer", "software developer", "developer", ".net", "c#",
    "python", "full stack", "fullstack", "backend", "back-end", "back end",
    "engineer", "programmer",
]
EXCLUDE_TITLE = [
    "intern", "internship", "stage", "sales", "recruiter", "hr ",
    "marketing", "designer", "manager", "director", "principal",
    "head of", "vp ", "lead ", "architect", "data scientist",
    "frontend", "front-end", "front end",
]
SENIOR_MARKERS = ["senior", "staff", "principal", "lead", "expert"]


def is_relevant(job: dict) -> tuple[bool, str]:
    """Filter to junior/medior software engineering roles."""
    title = (job.get("title") or "").lower()
    if not any(k in title for k in ROLE_KEYWORDS):
        return False, "title not a software engineering role"
    for bad in EXCLUDE_TITLE:
        if bad in title:
            return False, f"excluded title keyword: {bad.strip()}"
    text = f"{title} {job.get('description', '')}".lower()
    if re.search(r"\b(?:1[0-9]|[89])\+?\s*years", text):
        return False, "requires 8+ years experience"
    return True, "relevant"


def main():
    parser = argparse.ArgumentParser(description="English-language NL job search")
    parser.add_argument("--pages", type=int, default=3, help="Pages per englishjobsearch query")
    parser.add_argument("--out", type=str, default="data/new-jobs.json", help="Output path")
    parser.add_argument("--include-applied", action="store_true", help="Skip the dedupe filter")
    args = parser.parse_args()

    applied_companies, applied_urls = load_applied()
    blocked = load_blocklist()
    print(f"Dedupe: {len(applied_companies)} companies applied to, {len(blocked)} blocked")

    raw: list[dict] = []

    print("\nSearching englishjobsearch.nl...")
    for query in EJS_QUERIES:
        found = scrape_englishjobsearch(query, args.pages)
        print(f"  {query}: {len(found)} listings")
        raw.extend(found)

    print("\nFetching Greenhouse boards...")
    for board in GREENHOUSE_BOARDS:
        found = fetch_greenhouse(board)
        print(f"  {board}: {len(found)} listings")
        raw.extend(found)
        time.sleep(1)

    # Deduplicate on URL (ignoring tracking query strings).
    seen, unique = set(), []
    for job in raw:
        key = job["url"].split("?")[0]
        if key and key not in seen:
            seen.add(key)
            unique.append(job)
    print(f"\nTotal unique listings: {len(unique)}")

    kept, rejected = [], {}
    for job in unique:
        text = f"{job.get('title','')} {job.get('description','')}"

        in_nl, reason = is_in_netherlands(job.get("location", ""), text)
        if not in_nl:
            rejected[reason] = rejected.get(reason, 0) + 1
            continue

        relevant, reason = is_relevant(job)
        if not relevant:
            rejected[reason] = rejected.get(reason, 0) + 1
            continue

        company_key = normalize_company(job.get("company", ""))
        if not args.include_applied:
            if company_key in blocked:
                rejected["blocklisted company"] = rejected.get("blocklisted company", 0) + 1
                continue
            if company_key in applied_companies:
                rejected["already applied to company"] = rejected.get("already applied to company", 0) + 1
                continue
            if job["url"] in applied_urls:
                rejected["already applied to job"] = rejected.get("already applied to job", 0) + 1
                continue

        job["language"] = detect_language(text)
        job["dutch_required"] = requires_dutch(text)
        job["seniority_flag"] = "senior" if any(m in job["title"].lower() for m in SENIOR_MARKERS) else "junior/medior"
        kept.append(job)

    print("\nFiltered out:")
    for reason, count in sorted(rejected.items(), key=lambda kv: -kv[1]):
        print(f"  {count:4d}  {reason}")

    print(f"\nNew jobs kept: {len(kept)}")
    by_lang: dict[str, int] = {}
    for job in kept:
        by_lang[job["language"]] = by_lang.get(job["language"], 0) + 1
    print(f"  by language: {by_lang}")
    print(f"  Dutch required: {sum(1 for j in kept if j['dutch_required'])}")

    out_path = BASE_DIR / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(kept, indent=2, ensure_ascii=False))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
