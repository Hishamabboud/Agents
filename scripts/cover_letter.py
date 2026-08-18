#!/usr/bin/env python3
"""Tailored cover-letter generation.

WHY THIS EXISTS
---------------
The first ~414 applications all sent the same five bullet points to every company.
That is the most likely reason for a weak response rate, and the job description was
already being fetched during verification and then thrown away.

SAFETY PROPERTY (the important part)
-----------------------------------
A claim only appears in the letter if it is BOTH:
  (a) present in EVIDENCE below, which is derived strictly from profile/resume.md, and
  (b) actually mentioned in the job posting.

The intersection means the letter can highlight *relevant* truths but can never invent
a skill. If the posting asks for Kubernetes and the CV has Kubernetes, we say so; if the
posting asks for Rust, we stay silent about Rust rather than implying exposure.
Nothing is generated from the posting alone.
"""

import re

# Every entry here is traceable to a specific line in profile/resume.md.
# key -> (regex that detects the topic in a posting, sentence to use if matched)
EVIDENCE = {
    "dotnet": (r"\.net\b|dotnet|c#\b|asp\.?net",
               "building and maintaining applications in .NET, C# and ASP.NET at Actemium"),
    "python": (r"\bpython\b|flask|django|fastapi",
               "day-to-day Python development, including a Flask backend for my own AI platform"),
    "testing": (r"\btest|pytest|locust|\bqa\b|automation|regression",
                "building a Python test suite with Pytest and Locust for performance and "
                "regression testing during my internship at ASML"),
    "mes": (r"\bmes\b|manufacturing|industrial|production line|scada|\bplc\b|factory|oem",
            "supporting Manufacturing Execution Systems for industrial clients, which means "
            "working on software that runs live production environments"),
    "azure": (r"\bazure\b|cloud|devops|ci/?cd|pipeline",
              "working with Azure and CI/CD pipelines in an agile setting"),
    "k8s": (r"kubernetes|k8s|docker|container",
            "hands-on experience with Docker and Kubernetes"),
    "js": (r"javascript|typescript|react|frontend|front-end|full.?stack",
           "full-stack work with JavaScript and React alongside the backend"),
    "sql": (r"\bsql\b|database|postgres|mysql|sql server|data model",
            "database work and query/schema optimisation as part of MES integrations"),
    "api": (r"\bapi\b|rest|integration|microservice|interface",
            "designing REST API connections and integrations between systems"),
    "data": (r"data engineer|etl|pipeline|analytics|data platform|databricks|warehouse",
             "building data pipelines, including a GDPR-compliant anonymisation pipeline "
             "for my graduation project"),
    "ai": (r"\bai\b|machine learning|\bml\b|llm|genai|nlp|sentiment",
           "building CogitatAI, an AI support platform with sentiment analysis, as my own project"),
    "legacy": (r"legacy|migrat|refactor|modernis|moderniz|vb\b|visual basic",
               "migrating a legacy Visual Basic codebase to C# at Delta Electronics"),
    "security": (r"gdpr|privacy|security|compliance|anonymis|anonymiz",
                 "a GDPR-compliant data anonymisation pipeline built with the Fontys Cyber "
                 "Security Research Group"),
}

# Ordered so the strongest differentiators lead when several match.
PRIORITY = ["dotnet", "mes", "python", "testing", "ai", "data", "azure", "api",
            "k8s", "js", "sql", "legacy", "security"]

MAX_POINTS = 4


def _clean(html):
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text)


def matched_evidence(job_text, max_points=MAX_POINTS):
    """Return the evidence sentences whose topic the posting actually mentions."""
    body = _clean(job_text).lower()
    hits = [k for k in PRIORITY
            if k in EVIDENCE and re.search(EVIDENCE[k][0], body, re.I)]
    return [EVIDENCE[k][1] for k in hits[:max_points]], hits[:max_points]


def build(company, role, location, country="NL", job_text="", dutch=False):
    """Compose a tailored letter. Falls back to a general (still truthful) letter when
    the posting yields no overlap at all."""
    points, keys = matched_evidence(job_text)

    if country == "BE":
        close = ("I am based in Eindhoven, close to the Belgian border, and am happy to work "
                 "in Belgium. I am fluent in Dutch and English.")
    else:
        close = ("I am based in Eindhoven and open to working anywhere in the Netherlands.")

    if not points:
        # No detectable overlap — say something honest and general rather than padding.
        body = ("I work as a Software Service Engineer at Actemium (VINCI Energies), where I "
                "do full-stack development in .NET, C# and Python for Manufacturing Execution "
                "Systems. Before that I built Python test automation at ASML and migrated a "
                "legacy VB codebase to C# at Delta Electronics. I hold a BSc in Software "
                "Engineering from Fontys.")
    else:
        lead = points[0]
        rest = points[1:]
        body = f"What drew me to this role is the overlap with my current work: {lead}."
        if rest:
            body += " I also bring " + "; ".join(rest) + "."
        body += (" I hold a BSc in Software Engineering from Fontys and currently work as a "
                 "Software Service Engineer at Actemium (VINCI Energies).")

    return (
        f"Dear Hiring Team at {company},\n\n"
        f"I would like to apply for the {role} position in {location}.\n\n"
        f"{body}\n\n"
        f"{close} I would be glad to discuss how I can contribute to {company}.\n\n"
        f"Best regards,\nHisham Abboud\n+31 6 4841 2838\nhiaham123@hotmail.com"
    ), keys


if __name__ == "__main__":
    samples = [
        ("Xsens", "Embedded Software Engineer", "Enschede", "NL",
         "You will work on embedded C++ and Python software for motion sensors, "
         "with CI/CD pipelines and automated testing."),
        ("SomeBank", "Data Engineer", "Amsterdam", "NL",
         "Build ETL pipelines on Databricks and Azure. SQL and Python required."),
        ("MysteryCo", "Rust Systems Programmer", "Gent", "BE",
         "We need deep Rust and Erlang expertise for a distributed ledger."),
    ]
    for co, role, loc, cc, jd in samples:
        letter, keys = build(co, role, loc, cc, jd)
        print("=" * 78)
        print(f"{co} / {role}   matched={keys}")
        print("-" * 78)
        print(letter)
        print()
