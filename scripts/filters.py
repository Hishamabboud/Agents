#!/usr/bin/env python3
"""Shared filtering helpers — extracted after two filter bugs silently cost applications.

BUG 1 (found round 28): location pre-filtering matched a hardcoded list of city NAMES.
Dutch towns not on that list — Heemstede, Gorinchem, Enschede, Pijnacker, Duiven, Kwadijk,
Dordrecht, Almere — were dropped as "outside NL/BE" before ever reaching the live
verification step that reads the authoritative `country_code`. On one round this cut
26 engineering roles down to 6. Never filter location by city name; resolve country_code.

BUG 2 (found round 28): blocklist matching used `blocklist_entry in company_name`, which
is directionally wrong when the blocklist is more specific than the company string.
"Funda Real Estate B.V." is on the blocklist; the ATS reported the company as "Funda",
so the check passed and two applications were nearly sent to a company that had already
received seven duplicates. Match BOTH directions on normalised strings, and always check
the tenant slug too.
"""

import re

BLOCKED_SLUGS = {
    "fridayrecruitment", "bimcollab", "sendent", "funda", "sendcloud",
    "chipsoft", "ubiops", "prodrive", "futuresworks", "yellowtail",
}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def load_blocked_companies(prefs_path):
    """Parse the 'Blocked Companies' section out of preferences.md."""
    blocked, inside = set(), False
    for line in open(prefs_path).read().splitlines():
        if "Blocked Companies" in line:
            inside = True
            continue
        if line.startswith("## ") and inside:
            break
        if inside and line.startswith("- "):
            blocked.add(line.split("—")[0].split("(")[0].strip("- ").strip().lower())
    return blocked


def blocked_reason(company, slug, blocked_companies):
    """Return a reason string if this company must not be applied to, else None.

    Checks the tenant slug AND matches company names in BOTH directions, because the
    blocklist and the ATS often disagree on how much of the legal name they include.
    """
    if slug and slug.lower() in BLOCKED_SLUGS:
        return f"tenant slug '{slug}' is on the blocklist"
    c = _norm(company)
    for b in blocked_companies:
        nb = _norm(b)
        if not nb or not c:
            continue
        if nb in c or c in nb:
            return f"company matches blocklist entry '{b}'"
    return None


def in_scope_country(country_code, remote=False, allowed=("NL", "BE")):
    """Authoritative location check. Use this, NOT a city-name regex.

    country_code comes from the ATS API and is reliable; city names are not enumerable.
    """
    return bool(remote) or (country_code in allowed)


# --- language detection -------------------------------------------------------------
_FR = re.compile(r"\b(nous|vous|votre|notre|tes|ton|avec|pour|dans|une|des|les|est|sont|chez|"
                 r"développeur|entreprise|équipe|missions|profil|compétences|vos|leur)\b", re.I)
_NL = re.compile(r"\b(jij|jouw|onze|wij|met|voor|een|het|zijn|bij|werken|ervaring|team|van)\b", re.I)


def is_french_posting(text, threshold=0.04):
    """True if the posting body is predominantly French.

    Catches postings with an English/Dutch title but a fully French description — a
    title-only check misses these entirely.
    """
    words = max(len(text.split()), 1)
    fr = len(_FR.findall(text)) / words
    nl = len(_NL.findall(text)) / words
    return fr > threshold and fr > nl, fr, nl


def hard_blockers(title, body):
    """Non-negotiable exclusions, checked against the live offer text."""
    flags = []
    if re.search(r"\b(10\+|minimum.{0,15}10 years|10 years.{0,20}experience)\b", body, re.I):
        flags.append("10+yrs")
    if re.search(r"security clearance|veiligheidsmachtiging|nato secret", body, re.I):
        flags.append("clearance")
    if re.search(r"\bunpaid\b|\bonbetaald\b", body, re.I) and not re.search(
            r"we do not|geen onbetaald", body, re.I):
        flags.append("unpaid")
    if re.search(r"\bdefen[cs]e\b|defensie|militair|military|avionics|weapons", title, re.I):
        flags.append("DEFENCE")
    if re.search(r"talent network|talent pool", title, re.I):
        flags.append("talent-pool-not-a-real-vacancy")
    is_fr, fr, _ = is_french_posting(body)
    if is_fr:
        flags.append(f"French posting (fr={fr:.3f})")
    return flags
