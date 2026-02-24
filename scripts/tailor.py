#!/usr/bin/env python3
"""
Resume Tailor — generates tailored resumes and cover letters for high-scoring jobs.

For each qualifying job, uses Claude (via `claude -p` subprocess) to:
- Generate a tailored resume emphasizing relevant experience
- Generate a personalized cover letter
- Save both to output/ directories

Usage:
    python3 scripts/tailor.py
    python3 scripts/tailor.py --max-jobs 5
    python3 scripts/tailor.py --dry-run
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILE_DIR = BASE_DIR / "profile"
OUTPUT_DIR = BASE_DIR / "output"
RESUME_DIR = OUTPUT_DIR / "tailored-resumes"
COVER_DIR = OUTPUT_DIR / "cover-letters"


def sanitize_filename(text: str) -> str:
    """Create a safe filename from text."""
    # Remove/replace unsafe characters
    safe = re.sub(r"[^\w\s-]", "", text.lower())
    safe = re.sub(r"[\s]+", "-", safe.strip())
    return safe[:80]  # Limit length


def load_scored_jobs() -> list[dict]:
    """Load scored jobs from data/scored-jobs.json."""
    scored_path = DATA_DIR / "scored-jobs.json"
    if not scored_path.exists():
        print("ERROR: scored-jobs.json not found. Run score.py first.")
        sys.exit(1)
    try:
        return json.loads(scored_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in scored-jobs.json: {e}")
        sys.exit(1)


def load_resume() -> str:
    """Load the base resume."""
    resume_path = PROFILE_DIR / "resume.md"
    if not resume_path.exists():
        print("ERROR: resume.md not found in profile/")
        sys.exit(1)
    return resume_path.read_text()


def load_cover_template() -> str:
    """Load the cover letter template."""
    template_path = PROFILE_DIR / "cover-letter-template.md"
    if not template_path.exists():
        print("WARNING: cover-letter-template.md not found, using default structure.")
        return ""
    return template_path.read_text()


def load_applied_jobs() -> dict:
    """Load applications tracker to check what's already tailored."""
    apps_path = DATA_DIR / "applications.json"
    if not apps_path.exists():
        return {}
    try:
        applications = json.loads(apps_path.read_text())
        return {app["url"]: app for app in applications if "url" in app}
    except (json.JSONDecodeError, KeyError):
        return {}


def call_claude(prompt: str) -> str:
    """
    Call Claude via the `claude` CLI tool with a prompt.
    Falls back to a template-based approach if claude CLI is not available.
    """
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(BASE_DIR),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            print(f"    Claude CLI returned code {result.returncode}")
            if result.stderr:
                print(f"    stderr: {result.stderr[:200]}")
            return ""
    except FileNotFoundError:
        print("    WARNING: 'claude' CLI not found. Using template-based generation.")
        return ""
    except subprocess.TimeoutExpired:
        print("    WARNING: Claude CLI timed out after 120s.")
        return ""
    except Exception as e:
        print(f"    WARNING: Error calling Claude CLI: {e}")
        return ""


def generate_tailored_resume(job: dict, base_resume: str) -> str:
    """Generate a tailored resume for a specific job."""
    prompt = f"""You are a professional resume writer. Tailor the following resume for the specific job listing below.

RULES:
- NEVER fabricate experience, skills, or qualifications
- Only reorder sections and emphasize existing experience that's relevant
- Add keywords from the job description naturally where they match existing skills
- Keep the resume concise (max 2 pages equivalent in markdown)
- Use professional formatting in markdown

JOB LISTING:
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Description: {job.get('description', 'No description available')}

BASE RESUME:
{base_resume}

Generate the tailored resume in markdown format. Output ONLY the resume content, no explanations."""

    result = call_claude(prompt)

    if not result:
        # Fallback: return base resume with a header noting the target job
        return f"<!-- Tailored for: {job.get('title', '')} at {job.get('company', '')} -->\n\n{base_resume}"

    return result


def generate_cover_letter(job: dict, base_resume: str, template: str) -> str:
    """Generate a personalized cover letter for a specific job."""
    prompt = f"""You are a professional cover letter writer. Write a personalized cover letter for the job below.

RULES:
- NEVER fabricate experience, skills, or qualifications
- Reference specific details from the job description
- Highlight relevant experience from the resume
- Keep it concise: 3-4 paragraphs max
- Professional but personable tone
- Follow the template structure provided

JOB LISTING:
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Description: {job.get('description', 'No description available')}

RESUME:
{base_resume}

TEMPLATE STRUCTURE:
{template}

Write the cover letter now. Output ONLY the letter content, no explanations."""

    result = call_claude(prompt)

    if not result:
        # Fallback: basic template fill
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.get('title', 'open')} position at {job.get('company', 'your company')}.

Based on my experience and skills, I believe I would be a strong fit for this role. I would welcome the opportunity to discuss how my background aligns with your team's needs.

Please find my resume attached for your review. I look forward to hearing from you.

Best regards,
[Your Name]"""

    return result


def main():
    parser = argparse.ArgumentParser(description="Resume tailor and cover letter generator")
    parser.add_argument("--max-jobs", type=int, default=10, help="Maximum jobs to tailor for")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without generating")
    parser.add_argument("--force", action="store_true", help="Regenerate even if files already exist")
    args = parser.parse_args()

    print("Loading data...")
    scored_jobs = load_scored_jobs()
    base_resume = load_resume()
    cover_template = load_cover_template()
    applied_jobs = load_applied_jobs()

    print(f"  Scored jobs: {len(scored_jobs)}")
    print(f"  Already applied: {len(applied_jobs)}")

    # Filter out already-applied jobs
    jobs_to_tailor = [
        j for j in scored_jobs
        if j.get("url") not in applied_jobs
    ][:args.max_jobs]

    print(f"  Jobs to tailor: {len(jobs_to_tailor)}")

    if not jobs_to_tailor:
        print("\nNo jobs to tailor. Either all have been applied to or no qualifying jobs found.")
        return

    # Create output directories
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    COVER_DIR.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print("\n[DRY RUN] Would generate materials for:")
        for i, job in enumerate(jobs_to_tailor, 1):
            company = sanitize_filename(job.get("company", "unknown"))
            role = sanitize_filename(job.get("title", "unknown"))
            print(f"  {i}. {job['title']} @ {job['company']}")
            print(f"     Resume: output/tailored-resumes/{company}-{role}.md")
            print(f"     Cover:  output/cover-letters/{company}-{role}.md")
        return

    # Generate materials for each job
    generated = []
    for i, job in enumerate(jobs_to_tailor, 1):
        company = sanitize_filename(job.get("company", "unknown"))
        role = sanitize_filename(job.get("title", "unknown"))
        filename = f"{company}-{role}"

        resume_path = RESUME_DIR / f"{filename}.md"
        cover_path = COVER_DIR / f"{filename}.md"

        print(f"\n[{i}/{len(jobs_to_tailor)}] {job['title']} @ {job['company']} (score: {job.get('score', '?')})")

        # Check if already generated
        if resume_path.exists() and cover_path.exists() and not args.force:
            print(f"  Already generated, skipping (use --force to regenerate)")
            generated.append({
                "job": job,
                "resume_file": str(resume_path.relative_to(BASE_DIR)),
                "cover_letter_file": str(cover_path.relative_to(BASE_DIR)),
            })
            continue

        # Generate tailored resume
        print(f"  Generating tailored resume...")
        tailored_resume = generate_tailored_resume(job, base_resume)
        resume_path.write_text(tailored_resume)
        print(f"  Saved: {resume_path.relative_to(BASE_DIR)}")

        # Generate cover letter
        print(f"  Generating cover letter...")
        cover_letter = generate_cover_letter(job, base_resume, cover_template)
        cover_path.write_text(cover_letter)
        print(f"  Saved: {cover_path.relative_to(BASE_DIR)}")

        generated.append({
            "job": job,
            "resume_file": str(resume_path.relative_to(BASE_DIR)),
            "cover_letter_file": str(cover_path.relative_to(BASE_DIR)),
        })

    # Save generation manifest
    manifest_path = DATA_DIR / "tailored-manifest.json"
    manifest_path.write_text(json.dumps(generated, indent=2, ensure_ascii=False))
    print(f"\nGeneration complete. {len(generated)} jobs prepared.")
    print(f"Manifest saved to {manifest_path}")


if __name__ == "__main__":
    main()
