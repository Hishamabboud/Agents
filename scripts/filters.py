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

import html
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


# EU/EEA set used to bound "remote". A remote flag alone is NOT enough: a Ukraine-anchored
# remote posting (Clario, Kyiv, country_code=UA, remote=True) passed the old check, which
# treated any remote job as in-scope regardless of where the role is actually based.
_EU_EEA = {"NL", "BE", "DE", "FR", "LU", "IE", "AT", "DK", "SE", "FI", "ES", "PT", "IT",
           "PL", "CZ", "SK", "HU", "SI", "HR", "RO", "BG", "EE", "LV", "LT", "GR", "CY",
           "MT", "NO", "IS", "LI"}


def in_scope_country(country_code, remote=False, allowed=("NL", "BE"), body=""):
    """Authoritative location check. Use this, NOT a city-name regex.

    country_code comes from the ATS API and is reliable; city names are not enumerable.

    `remote` only widens scope within the EU/EEA, or when the posting explicitly offers
    Europe-wide / NL / BE remote work. A remote role anchored outside the EEA is out of
    scope — the contract, pay band and time zone follow the anchor country.
    """
    if country_code in allowed:
        return True
    if not remote:
        return False
    if country_code in _EU_EEA:
        return True
    return bool(re.search(r"remote.{0,30}(europe|eu\b|emea|netherlands|belgium)|"
                          r"(europe|eu|emea|netherlands|belgium).{0,30}remote", body or "", re.I))


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
    # "onbetaald verlof" / "unpaid leave" is a sabbatical BENEFIT, not an unpaid role --
    # it cost Blue Green Solutions' Mendix vacancy a round-32 application before this
    # exclusion existed.
    if re.search(r"\b(unpaid|onbetaald)\b(?!\s*(verlof|leave|sabbatical))", body, re.I) \
            and not re.search(r"we do not|geen onbetaald", body, re.I):
        flags.append("unpaid")
    if re.search(r"\bdefen[cs]e\b|defensie|militair|military|avionics|weapons", title, re.I):
        flags.append("DEFENCE")
    if re.search(r"talent network|talent pool", title, re.I):
        flags.append("talent-pool-not-a-real-vacancy")
    is_fr, fr, _ = is_french_posting(body)
    if is_fr:
        flags.append(f"French posting (fr={fr:.3f})")
    return flags


# --- Personio-specific location check -----------------------------------------------
# Personio's XML `office` field is often blank or a free-text string, and unlike Recruitee
# there is no country_code. A TradeTracker role slipped through the recovery pass this way:
# office was unhelpful but the body read "TradeTracker International India Development Team
# ... Salary: INR 80,000-100,000/month ... Location: India remote". Check the body too.
_NON_EU_SIGNALS = re.compile(
    r"\b(INR|USD|CAD|AUD|SGD|MYR|PHP\s*[0-9])\b|"
    r"\b(india|bangalore|bengaluru|mumbai|delhi|pune|hyderabad|chennai|"
    r"kuala lumpur|singapore|manila|austin|duluth|new york|san francisco|toronto|"
    r"dubai|bratislava|warsaw|warszawa|belgrade|yerevan|"
    # round 33: a Fairphone Taipei role read as in-scope because Asia beyond India was
    # simply absent from this list.
    r"taiwan|taipei|shenzhen|shanghai|beijing|hong kong|tokyo|seoul|bangkok|jakarta)\b",
    re.I)

# Places that ARE in the EU but outside the NL/BE scope. Personio carries no country_code,
# so without this a Munich or Stuttgart office passes as readily as an Amsterdam one --
# round 33 surfaced Personio's own Munich board and two Scalian Stuttgart roles.
_OUT_OF_SCOPE_EU = re.compile(
    r"\b(munich|m[uü]nchen|stuttgart|berlin|hamburg|frankfurt|cologne|k[oö]ln|d[uü]sseldorf|"
    r"leipzig|dresden|hannover|nuremberg|n[uü]rnberg|vienna|wien|zurich|z[uü]rich|geneva|"
    r"paris|lyon|marseille|toulouse|london|manchester|dublin|madrid|barcelona|valencia|"
    r"lisbon|lisboa|porto|milan|milano|rome|roma|turin|prague|praha|budapest|bucharest|"
    r"sofia|athens|helsinki|stockholm|oslo|copenhagen|k[oø]benhavn|tallinn|riga|vilnius|"
    r"deutschland|germany|france|espa[nñ]a|italia|polska)\b", re.I)


def personio_location_ok(office, body, allowed_hint=r"netherlands|nederland|belgi|\bNL\b|\bBE\b"):
    """Return (ok, reason). Rejects postings that name a non-EU location or quote a
    non-EU currency, even when the structured office field looks empty or ambiguous."""
    blob = f"{office or ''} {body or ''}"
    office_says_nl_be = bool(re.search(allowed_hint, str(office or ""), re.I))
    m = _NON_EU_SIGNALS.search(blob)
    if m and not office_says_nl_be:
        return False, f"non-NL/BE signal in posting: {m.group(0)!r}"
    # The office field is the strongest signal Personio gives. Only the office is checked
    # for EU-but-out-of-scope places -- the BODY routinely name-drops other offices
    # ("our teams in Berlin and Amsterdam") and would reject valid Dutch roles.
    m2 = _OUT_OF_SCOPE_EU.search(str(office or ""))
    if m2 and not office_says_nl_be:
        return False, f"office is outside NL/BE: {m2.group(0)!r}"
    return True, None


# --- Personio XML parsing ------------------------------------------------------------
# BUG 3 (found round 29): a naive `<name>` regex over the Personio feed also matches the
# <name> inside <jobDescriptions><jobDescription>, so section headings ("Your mission",
# "Dein Profil") were counted as job titles. That both inflated position counts and
# corrupted real titles — Salto CloudWorks' "Back-End Engineer" was missed this way.
# Strip <jobDescriptions> before reading the position name.
#
# BUG 4 (found round 29): many Personio tenants are set up but never populated, and serve
# Personio's sample content. 8 of 10 "hits" in one round were these. They are not real
# openings and must not be counted as reach.
_PERSONIO_DEMO = re.compile(
    r"^(general application|your mission|your profile|deine aufgaben|dein profil|"
    r"seo marketing manager|social media \(working student\)|social media \(werkstudent\)|"
    r"initiativbewerbung.*|open application|spontane sollicitatie)$", re.I)


def parse_personio_positions(xml):
    """Return [{id, title, office}] for REAL positions only. Skips demo/template boards."""
    out = []
    for m in re.finditer(r"<position>(.*?)</position>", xml, re.S):
        block = m.group(1)
        stripped = re.sub(r"<jobDescriptions>.*?</jobDescriptions>", "", block, flags=re.S)

        def field(tag, src=stripped):
            mm = re.search(rf"<{tag}>(.*?)</{tag}>", src, re.S)
            if not mm:
                return None
            return html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", mm.group(1))).strip()

        title = field("name")
        if not title or _PERSONIO_DEMO.match(title):
            continue
        out.append({"id": field("id"), "title": title, "office": field("office"),
                    "seniority": field("seniority"), "employment": field("employmentType")})
    return out


def is_demo_board(xml):
    """True if a Personio tenant exists but carries only sample content."""
    return len(parse_personio_positions(xml)) == 0


# --- role matching ------------------------------------------------------------------
# Widened after a round-29 audit found real roles the old pattern silently skipped:
#   "Junior/medior product engineer" (Azumuta)  -> "product engineer" was absent
#   "QA Engineer" (Twelve)                      -> only "test engineer" was covered
#   "ICT System Engineer" (ZORGI)               -> only plural "systems engineer" matched
ROLE_INCLUDE = re.compile(
    r"\.net\b|c#|\bpython\b|full.?stack|software engineer|software developer|backend|back-end|"
    r"devops|platform engineer|cloud engineer|data engineer|\bai engineer\b|machine learning|"
    r"application (developer|engineer)|embedded software|integration engineer|\bphp\b|golang|"
    r"mendix|node\.?js|systems? engineer|infrastructure engineer|kubernetes|automation engineer|"
    r"\bmes\b|scada|\bplc\b|software architect|microservice|typescript|test engineer|"
    r"test automation|\bqa\b|azure|\bjava\b(?!script)|\bc\+\+|ontwikkelaar|developer|"
    r"product engineer|principal engineer|\bsre\b|site reliability", re.I)

ROLE_EXCLUDE = re.compile(
    r"sales|account manager|account executive|marketing|marketeer|recruit|\bhr\b|finance|legal|"
    r"receptionist|warehouse|internship|\bstage\b|\bintern\b|stagiair|afstudeer|"
    r"working student|frontend|front-end|front end|"
    r"trader|business consultant|business develop|customer success|servicedesk|director|\bvp\b|"
    r"head of|chief|commercial|werkstudent|praktik|initiativ|open application|wordpress|"
    r"product manager|"
    # People-management titles. The old lookahead let "manager" through whenever
    # "software"/"engineering" followed it, so SIDN's "Manager Software Engineering" --
    # a team-lead role -- passed as an engineering job in round 37.
    r"\bmanager\s+(software|engineering|development|ict|it|data|team)\b|"
    r"\b(software|engineering|development|delivery|it)\s+manager\b|"
    r"manager\b(?!.*(engineer|software|technical))|"
    # Dutch "ontwikkelaar" means developer, but ALSO property/area developer. Dura Vermeer's
    # "Gebiedsontwikkelaar" (urban area development, a construction role) matched the
    # software pattern in round 33.
    r"gebiedsontwikkelaar|projectontwikkelaar|vastgoedontwikkelaar|"
    r"(gebied|vastgoed|project)s?ontwikkeling", re.I)


# --- employer identity ---------------------------------------------------------------
# BUG 6 (found round 31): the 2-applications-per-company cap keyed on the DISPLAY NAME the
# job board reported, so one employer under several names slipped past it repeatedly:
#     "DPG Media", "DPG Media Belgie", "DPG Media Nederland", "DPG Media / Independer"
#         -> all one tenant, `dpgmedia`, whose 77 offers all report company_name "DPG Media".
#            8 applications had gone out against a cap of 2.
#     "adesso Netherlands", "adesso Belgium", "adesso SE"
#         -> `adesso` 302-redirects to `werkenbijadesso`; 6 applications already sent.
# The ATS tenant is the employer: one board is one recruiting inbox. Cap on that.

def tenant_of(entry):
    """Canonical employer key for a tracker entry, or None if it cannot be determined."""
    host = entry.get("personio_host")
    if host:
        return f"personio:{host.split('.')[0].lower()}"
    for field in ("recruitee_api_url", "url"):
        m = re.search(r"https?://([^.]+)\.recruitee\.com", str(entry.get(field) or ""))
        if m:
            return f"recruitee:{m.group(1).lower()}"
    return None


def tenant_counts(apps, counted_statuses):
    """How many applications each tenant has already received."""
    out = {}
    for a in apps:
        if a.get("status") not in counted_statuses:
            continue
        k = tenant_of(a)
        if k:
            out[k] = out.get(k, 0) + 1
    return out


# --- seniority ----------------------------------------------------------------------
# Found while debugging why six months of applications produced no visible result: 92 of
# 448 (21%) went to Senior/Lead/Principal/Architect roles, against the stated 2-3 year
# experience bar in preferences.md. Those are near-certain rejections that ALSO burn the
# 2-per-tenant cap, locking out the medior application that could have been sent instead.
_SENIOR = re.compile(r"\bs[eé]nior\b|\bsr\.?\b|\bprincipal\b|\barchitect\b|"
                     # "Staff <anything>" is a seniority grade above senior; matching only
                     # "staff engineer" missed "Staff Software Engineer, Data Platform".
                     r"\bstaff\s+(engineer|software|developer|data|backend|frontend|"
                     r"platform|scientist)|"
                     r"\b(tech|team)\s?lead\b|\blead\b(?!\s*generation)", re.I)
_JUNIOR_OK = re.compile(r"\bjunior\b|\bmedior\b|\bgraduate\b|\bstarter\b|"
                        r"\(\s*senior\s*\)", re.I)   # "(Senior)" = seniority optional


def seniority_mismatch(title):
    """True if the title demands seniority beyond the profile's 2-3 year bar.

    A range like "Junior/Medior/Senior" or a parenthesised "(Senior)" marker means the
    employer will consider a medior candidate, so those stay eligible.
    """
    t = title or ""
    return bool(_SENIOR.search(t)) and not _JUNIOR_OK.search(t)


# --- discipline ---------------------------------------------------------------------
# BUG 7 (found round 33, after two applications had already gone out): a title-only role
# filter cannot tell a software developer from a property developer.
#     Dura Vermeer, "Ontwikkelaar"            -> dept "Bouw en Vastgoed", residential
#                                                property development
#     GreenV, "Product Engineer Paneelbouw"   -> dept "Stolze Installatietechniek",
#                                                electrical panel design
# Both matched ROLE_INCLUDE on an ambiguous word and neither is a software role. Excluding
# the specific titles is whack-a-mole; a real software posting always describes software.
# Require positive evidence in the live body text instead.
_SOFTWARE_EVIDENCE = re.compile(
    r"\bsoftware|\bcode\b|coding|programmeer|programmer|\bdeveloper\b|\bapi\b|"
    r"\bdatabase|\bsql\b|\bpython\b|\bjava\b|c#|\.net\b|javascript|typescript|"
    r"\bcloud\b|azure|\baws\b|kubernetes|docker|devops|\bgit\b|linux|embedded|"
    r"front.?end|back.?end|full.?stack|micro.?service|\bscrum\b|\bagile\b|\bci/cd\b|"
    r"\bplc\b|scada|\bmes\b|firmware|applicatie|\bit\b\s|informatica", re.I)

_NON_SOFTWARE_DEPT = re.compile(
    r"bouw en vastgoed|vastgoed|installatietechniek|werktuigbouw|civiel|gebiedsontwikkeling|"
    r"logistiek|warehouse|productie|facilit|hrm?\b|finance|marketing|sales", re.I)


# Merely containing the word "software" is not evidence -- GreenV's electrical-panel role
# says "Kun je goed overweg met CAD-software, MS Office". Naming a language, platform or
# engineering practice is.
_STRONG_SOFTWARE = re.compile(
    r"\bpython\b|\bjava\b|c#|c\+\+|\.net\b|javascript|typescript|\bgolang\b|\bphp\b|"
    r"\bsql\b|\bapi\b|azure|\baws\b|kubernetes|docker|devops|\bgit\b|linux|"
    r"micro.?service|front.?end|back.?end|full.?stack|\bci/cd\b|firmware|embedded|"
    r"\bplc\b|scada|\bmes\b|programmeer|programming|\bcoding\b|\bcode\b|"
    r"software (engineer|develop|architect|ontwikkel)", re.I)


def wrong_discipline(title, body, department=""):
    """Return a reason if this is not a software role, else None.

    Checked against the LIVE posting, because the discipline lives in the description --
    "woningbouwprojecten" and "elektrotechnische installaties" are unmistakable, while the
    titles ("Ontwikkelaar", "Product Engineer") are not.
    """
    blob = f"{title or ''} {body or ''}"
    dept_is_off = bool(_NON_SOFTWARE_DEPT.search(f"{department or ''} {title or ''}"))
    if dept_is_off:
        # A construction/installation/real-estate posting has to name real software work,
        # not just mention a tool it happens to use.
        if _STRONG_SOFTWARE.search(blob):
            return None
        return (f"non-software context ({department or title!r}) with no real software work "
                f"described")
    if _SOFTWARE_EVIDENCE.search(blob):
        return None
    return "no software terms anywhere in the posting"
