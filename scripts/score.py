#!/usr/bin/env python3
"""
Job Matching Scorer — scores and ranks scraped jobs against the user's profile.

Reads raw-jobs.json and resume.md, scores each job 1-10 based on:
- Skills overlap
- Experience level match
- Location match
- Salary range match

Filters out already-applied jobs and saves scored results to data/scored-jobs.json.

Usage:
    python3 scripts/score.py
    python3 scripts/score.py --min-score 7
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILE_DIR = BASE_DIR / "profile"


def load_resume() -> str:
    """Load the resume markdown file."""
    resume_path = PROFILE_DIR / "resume.md"
    if not resume_path.exists():
        print("ERROR: resume.md not found in profile/")
        sys.exit(1)
    return resume_path.read_text().lower()


def load_preferences() -> dict:
    """Load and parse preferences."""
    prefs_path = PROFILE_DIR / "preferences.md"
    if not prefs_path.exists():
        print("ERROR: preferences.md not found in profile/")
        sys.exit(1)

    content = prefs_path.read_text()
    prefs = {
        "target_roles": [],
        "required_location": [],
        "preferred_stack": [],
        "preferred_industries": [],
        "avoid": [],
        "min_salary": 50000,
    }

    section = None
    for line in content.splitlines():
        line_stripped = line.strip()

        if line_stripped.startswith("## "):
            section = line_stripped[3:].strip().lower()
            continue

        if not line_stripped.startswith("- "):
            # Check for salary
            if "minimum salary" in line_stripped.lower():
                match = re.search(r"€([\d,]+)", line_stripped)
                if match:
                    prefs["min_salary"] = int(match.group(1).replace(",", ""))
            continue

        item = line_stripped[2:].strip().lower()

        if section == "target roles":
            prefs["target_roles"].append(item)
        elif section == "required":
            if "location" in item:
                locations = re.search(r"location:\s*(.+)", item)
                if locations:
                    prefs["required_location"] = [
                        loc.strip() for loc in locations.group(1).split(",")
                    ]
        elif section == "preferred":
            if "tech stack" in item:
                stack = re.search(r"tech stack:\s*(.+)", item)
                if stack:
                    prefs["preferred_stack"] = [
                        s.strip() for s in stack.group(1).split(",")
                    ]
            elif "industries" in item:
                industries = re.search(r"industries:\s*(.+)", item)
                if industries:
                    prefs["preferred_industries"] = [
                        i.strip() for i in industries.group(1).split(",")
                    ]
        elif section == "avoid":
            prefs["avoid"].append(item)

    return prefs


def load_raw_jobs() -> list[dict]:
    """Load scraped jobs from raw-jobs.json."""
    raw_path = DATA_DIR / "raw-jobs.json"
    if not raw_path.exists():
        print("ERROR: raw-jobs.json not found. Run search.py first.")
        sys.exit(1)
    try:
        return json.loads(raw_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in raw-jobs.json: {e}")
        sys.exit(1)


def load_applied_jobs() -> set:
    """Load URLs of already-applied jobs."""
    apps_path = DATA_DIR / "applications.json"
    if not apps_path.exists():
        return set()
    try:
        applications = json.loads(apps_path.read_text())
        return {app["url"] for app in applications if "url" in app}
    except (json.JSONDecodeError, KeyError):
        return set()


def extract_skills_from_text(text: str) -> set[str]:
    """Extract known tech skills/keywords from text."""
    # Common tech skills to look for
    skill_patterns = [
        # Languages
        r"\bc#\b", r"\b\.net\b", r"\basp\.net\b", r"\bpython\b", r"\bjavascript\b",
        r"\btypescript\b", r"\bjava\b", r"\bsql\b", r"\bhtml\b", r"\bcss\b",
        r"\bc\+\+\b", r"\bgo\b", r"\brust\b", r"\bruby\b", r"\bphp\b",
        r"\bkotlin\b", r"\bswift\b", r"\br\b", r"\bscala\b",
        # Frameworks
        r"\breact\b", r"\bangular\b", r"\bvue\b", r"\bnode\.?js\b",
        r"\bflask\b", r"\bdjango\b", r"\bfastapi\b", r"\bspring\b",
        r"\b\.net\s*core\b", r"\blazor\b", r"\bnext\.?js\b",
        r"\bexpress\b", r"\brails\b", r"\blaravel\b",
        # Tools & Platforms
        r"\bdocker\b", r"\bkubernetes\b", r"\bk8s\b", r"\bazure\b", r"\baws\b",
        r"\bgcp\b", r"\bgit\b", r"\bci/cd\b", r"\bjenkins\b", r"\bterraform\b",
        r"\blinux\b", r"\bredis\b", r"\bmongodb\b", r"\bpostgresql?\b",
        r"\belasticsearch\b", r"\brabbitmq\b", r"\bkafka\b",
        # Domains
        r"\bmachine learning\b", r"\bml\b", r"\bai\b", r"\bdeep learning\b",
        r"\bdata science\b", r"\bdevops\b", r"\bscrum\b", r"\bagile\b",
        r"\bmicroservices\b", r"\brest\s*api\b", r"\bgraphql\b",
        r"\biot\b", r"\bmes\b", r"\bmanufacturing\b", r"\bautomation\b",
        r"\bsaas\b", r"\bfull.?stack\b",
    ]

    found = set()
    text_lower = text.lower()
    for pattern in skill_patterns:
        if re.search(pattern, text_lower):
            # Normalize the matched skill name
            match = re.search(pattern, text_lower)
            if match:
                found.add(match.group(0).strip())
    return found


def score_job(job: dict, resume_text: str, resume_skills: set, prefs: dict) -> dict:
    """
    Score a single job listing against the profile. Returns the job dict
    with added 'score' and 'score_breakdown' fields.
    """
    score = 0.0
    breakdown = {}

    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}".lower()
    job_skills = extract_skills_from_text(job_text)

    # 1. Skills overlap (0-4 points)
    if resume_skills and job_skills:
        overlap = resume_skills & job_skills
        overlap_ratio = len(overlap) / max(len(job_skills), 1)
        skills_score = min(4.0, overlap_ratio * 5)
        breakdown["skills_match"] = {
            "score": round(skills_score, 1),
            "matched": sorted(overlap),
            "job_requires": sorted(job_skills),
        }
    else:
        skills_score = 2.0  # Neutral if we can't determine
        breakdown["skills_match"] = {"score": 2.0, "note": "Could not determine skills"}
    score += skills_score

    # 2. Title/Role match (0-3 points)
    title_score = 0.0
    job_title = job.get("title", "").lower()
    for role in prefs.get("target_roles", []):
        role_words = role.lower().split()
        matches = sum(1 for word in role_words if word in job_title)
        role_match = matches / max(len(role_words), 1)
        title_score = max(title_score, role_match * 3)
    breakdown["title_match"] = round(title_score, 1)
    score += title_score

    # 3. Location match (0-1.5 points)
    job_location = job.get("location", "").lower()
    location_score = 0.0
    if "remote" in job_location:
        location_score = 1.5
    else:
        for loc in prefs.get("required_location", []):
            if loc.lower() in job_location:
                location_score = 1.5
                break
        if location_score == 0 and ("netherlands" in job_location or "nederland" in job_location):
            location_score = 0.75
    breakdown["location_match"] = round(location_score, 1)
    score += location_score

    # 4. Salary check (0-1 points)
    salary_text = job.get("salary", "").lower()
    salary_score = 0.5  # Neutral if not listed
    if salary_text:
        # Try to extract numeric salary
        amounts = re.findall(r"€?\s*([\d.,]+)", salary_text)
        if amounts:
            try:
                # Take the highest number as upper bound
                max_salary = max(
                    float(a.replace(".", "").replace(",", ".")) for a in amounts
                )
                # If it looks like monthly, multiply
                if max_salary < 10000:
                    max_salary *= 12
                if max_salary >= prefs.get("min_salary", 50000):
                    salary_score = 1.0
                else:
                    salary_score = 0.0
            except ValueError:
                salary_score = 0.5
    breakdown["salary_match"] = round(salary_score, 1)
    score += salary_score

    # 5. Industry match (0-0.5 points)
    industry_score = 0.0
    for industry in prefs.get("preferred_industries", []):
        if industry.lower() in job_text:
            industry_score = 0.5
            break
    breakdown["industry_match"] = round(industry_score, 1)
    score += industry_score

    # Penalty: check "avoid" criteria
    penalty = 0.0
    for avoid_item in prefs.get("avoid", []):
        if avoid_item in job_text:
            penalty += 2.0
            breakdown.setdefault("penalties", []).append(avoid_item)
    score -= penalty

    # Clamp to 1-10
    final_score = max(1.0, min(10.0, score))

    job["score"] = round(final_score, 1)
    job["score_breakdown"] = breakdown
    return job


def main():
    parser = argparse.ArgumentParser(description="Job matching scorer")
    parser.add_argument("--min-score", type=float, default=7.0, help="Minimum score threshold")
    args = parser.parse_args()

    print("Loading profile data...")
    resume_text = load_resume()
    resume_skills = extract_skills_from_text(resume_text)
    prefs = load_preferences()
    print(f"  Resume skills detected: {sorted(resume_skills)}")
    print(f"  Target roles: {prefs['target_roles']}")

    print("\nLoading jobs...")
    raw_jobs = load_raw_jobs()
    applied_urls = load_applied_jobs()
    print(f"  Raw jobs: {len(raw_jobs)}")
    print(f"  Already applied: {len(applied_urls)}")

    # Filter out already-applied jobs
    jobs_to_score = [j for j in raw_jobs if j.get("url") not in applied_urls]
    print(f"  Jobs to score: {len(jobs_to_score)}")

    # Score each job
    print("\nScoring jobs...")
    scored_jobs = []
    for job in jobs_to_score:
        scored = score_job(job, resume_text, resume_skills, prefs)
        scored_jobs.append(scored)

    # Sort by score descending
    scored_jobs.sort(key=lambda j: j["score"], reverse=True)

    # Filter by minimum score
    qualifying = [j for j in scored_jobs if j["score"] >= args.min_score]

    print(f"\nResults:")
    print(f"  Total scored: {len(scored_jobs)}")
    print(f"  Qualifying (>= {args.min_score}): {len(qualifying)}")

    if scored_jobs:
        print(f"\nTop 10 jobs:")
        for i, job in enumerate(scored_jobs[:10], 1):
            print(f"  {i}. [{job['score']}/10] {job['title']} @ {job['company']}")
            print(f"     {job['url']}")

    # Save scored jobs
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    scored_path = DATA_DIR / "scored-jobs.json"
    scored_path.write_text(json.dumps(qualifying, indent=2, ensure_ascii=False))
    print(f"\nSaved {len(qualifying)} qualifying jobs to {scored_path}")

    # Also save all scores for reference
    all_scored_path = DATA_DIR / "all-scored-jobs.json"
    all_scored_path.write_text(json.dumps(scored_jobs, indent=2, ensure_ascii=False))
    print(f"Saved all {len(scored_jobs)} scored jobs to {all_scored_path}")


if __name__ == "__main__":
    main()
