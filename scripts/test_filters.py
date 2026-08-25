#!/usr/bin/env python3
"""Regression tests for every bug that has silently cost applications.

Run:  python3 scripts/test_filters.py
Each test names the round where the bug was found, so nobody re-introduces it.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filters import (blocked_reason, load_blocked_companies, in_scope_country,
                     is_french_posting, parse_personio_positions, personio_location_ok,
                     ROLE_INCLUDE, ROLE_EXCLUDE)
from discovery import slug_variants
import cover_letter

PREFS = Path(__file__).resolve().parent.parent / "profile" / "preferences.md"
fails = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        fails.append(name)


print("BUG 1 (r28) — location must use country_code, never city names")
check("Dutch town not on any city list is in scope", in_scope_country("NL"))
check("Kwadijk/Heemstede irrelevant — country decides", in_scope_country("NL", False))
check("US onsite rejected", not in_scope_country("US", False))

print("\nBUG 2 (r28) — blocklist must match BOTH directions + slug")
bc = load_blocked_companies(PREFS)
check("'Funda' caught by blocklist entry 'Funda Real Estate B.V.'",
      blocked_reason("Funda", None, bc) is not None)
check("'Funda' caught by tenant slug", blocked_reason("Funda", "funda", bc) is not None)
check("innocent company not blocked", blocked_reason("Xsens", "xsens", bc) is None)

print("\nBUG 3 (r29) — Personio parser must ignore jobDescription section headings")
xml = """<positions><position><id>1</id><name>Back-End Engineer</name><office>Gent</office>
<jobDescriptions><jobDescription><name>Your mission</name><value>x</value></jobDescription>
<jobDescription><name>Your profile</name><value>y</value></jobDescription></jobDescriptions>
</position></positions>"""
pos = parse_personio_positions(xml)
check("exactly one position parsed", len(pos) == 1, f"got {len(pos)}")
check("title is the job, not a section heading",
      pos and pos[0]["title"] == "Back-End Engineer", pos[0]["title"] if pos else "none")

print("\nBUG 4 (r29) — Personio demo/template boards must not count as reach")
demo = """<positions><position><id>9</id><name>General Application</name></position>
<position><id>8</id><name>SEO Marketing Manager</name></position></positions>"""
check("demo board yields zero real positions", len(parse_personio_positions(demo)) == 0)

print("\nBUG 5 (r29) — remote must not bypass the country check")
check("Ukraine remote rejected", not in_scope_country("UA", True, body="a company"))
check("Ukraine remote accepted only with explicit EU wording",
      in_scope_country("UA", True, body="fully remote across Europe"))
check("Germany remote accepted (EEA)", in_scope_country("DE", True))

print("\nRole matching — titles that were silently skipped before r29")
for t in ["Junior/medior product engineer", "QA Engineer", "ICT System Engineer",
          "Back-End Engineer", "Senior .NET Developer"]:
    check(f"matches {t!r}", ROLE_INCLUDE.search(t) and not ROLE_EXCLUDE.search(t))
for t in ["Account Executive", "SEO Marketing Manager", "Product Manager",
          "Business Development Representative"]:
    check(f"rejects {t!r}", not (ROLE_INCLUDE.search(t) and not ROLE_EXCLUDE.search(t)))

print("\nLanguage detection — body text, not just title")
fr, _, _ = is_french_posting("Rejoins Vertuoza et deviens Platform Engineer. TES MISSIONS: "
                             "tu es le référent infrastructure avec notre équipe pour dans une des les")
check("French body detected under an English title", fr)
nl, _, _ = is_french_posting("Wij zoeken een software engineer met ervaring in het bouwen van "
                             "applicaties voor onze klanten bij een mooi team")
check("Dutch body not flagged as French", not nl)

print("\nPersonio location — office field is unreliable, check the body")
ok, _ = personio_location_ok("", "TradeTracker India Development Team Salary: INR 80,000/month")
check("India/INR posting rejected", not ok)
ok, _ = personio_location_ok("Arnhem", "Wij zoeken een engineer in Arnhem")
check("Dutch posting accepted", ok)

print("\nDiscovery — multi-variant slugs")
check("adesso -> werkenbijadesso reachable", "werkenbijadesso" in slug_variants("adesso Netherlands"))
check("IXON Cloud -> ixon reachable", "ixon" in slug_variants("IXON Cloud"))
check("two-letter slug kept for EY", "ey" in slug_variants("EY (Ernst & Young)"))

print("\nPersonio tenant collision guard (round 30)")
from discovery import _personio_tenant_matches as _ptm
# Real tenant titles captured 2026-08-18. Probing by company name alone reached all of
# these; four belong to companies that were never searched for.
_TENANT = {
    "atlas":           "<title>Jobs bei Atlas-Bildungs-Center e.V.",
    "code":            "<title>Jobs at CODE Education GmbH",
    "kbc":             "<title>Jobs bei Kem\u00e9ny Boehme Consultants SE",
    "gambit":          "<title>Jobs bei Gambit Consulting GmbH",
    "vivid":           "<title>Jobs at Vivid",
    "royal":           "<title>Trabajos en Demo Datos",
    "everience":       "<title>Jobs bei everience Germany GmbH",
    "hms-networks":    "<title>Trabajos en HMS INDUSTRIAL NETWORKS, SLU",
    "ireckonu":        "<title>Jobs at IRECKONU",
    "saltocloudworks": "<title>Jobs at Salto CloudWorks",
    "scalian-germany": "<title>Jobs bei Scalian Germany AG",
    "twelve":          "<title>Banen bij Twelve",
    "ubiops":          "<title>Jobs at UbiOps",
    "open":            "<title>Jobs at ",
    "avisi":           "<title>Banen bij ",
}
for company, slug, want in [
        ("Royal Kaak", "royal", False),           # Personio's own "Demo Datos" sample tenant
        ("Royal Houdijk", "royal", False),
        ("Atlas Copco", "atlas", False),          # Atlas-Bildungs-Center e.V.
        ("Code for Good", "code", False),         # CODE Education GmbH — shares only a lead word
        ("KBC Bank & Verzekering", "kbc", False), # Kemeny Boehme Consultants SE
        ("GAMBIT Financial Solutions", "gambit", False),
        ("Vivid Resourcing", "vivid", False),     # tenant is Vivid Money, a Berlin fintech
        ("Open Home Foundation", "open", False),  # no name in title, and `open` is a fragment
        ("HMS Networks", "hms-networks", True),   # vs "HMS INDUSTRIAL NETWORKS, SLU"
        ("Everience Benelux", "everience", True), # vs "everience Germany GmbH"
        ("Ireckonu - Hotel Middleware & CDP+", "ireckonu", True),   # LinkedIn tagline stripped
        ("UbiOps - Private AI on any infra", "ubiops", True),
        ("Salto CloudWorks", "saltocloudworks", True),
        ("Scalian Germany AG", "scalian-germany", True),
        ("Twelve", "twelve", True),
        # Regression: the slug being the WHOLE company name is evidence, not the absence of
        # it. An earlier guard discounted the slug word, found no words left, and rejected
        # every single-word company — a false negative on Avisi, a tenant already applied to.
        ("Avisi", "avisi", True)]:
    got = _ptm(company, f"{slug}.jobs.personio.de", "", page=_TENANT[slug])
    check(f"{company[:30]:32s} vs {slug:16s} -> {want}", got == want, f"got {got}")

print("\nRound-33 gaps: seniority grades, Personio geography, Dutch homonym")
from filters import personio_location_ok as _pl, seniority_mismatch, ROLE_EXCLUDE
check("Staff <role> is a seniority grade", seniority_mismatch("Staff Software Engineer, Data Platform"))
check("accented Senior caught", seniority_mismatch("Ing\u00e9nieur S\u00e9nior en MES F/H"))
check("Staffing Coordinator is not seniority", not seniority_mismatch("Staffing Coordinator"))
# Personio carries no country_code, so the office field is the only geography signal.
check("Personio Taipei office rejected", not _pl("Taiwan", "")[0])
check("Personio Munich office rejected", not _pl("Munich", "")[0])
check("Personio Amsterdam office kept", _pl("Amsterdam", "")[0])
check("body name-dropping Berlin does not reject a Dutch role",
      _pl("Hybrid", "our teams in Berlin and Amsterdam collaborate")[0])
# "ontwikkelaar" is developer AND property developer
check("Gebiedsontwikkelaar excluded", bool(ROLE_EXCLUDE.search("Gebiedsontwikkelaar")))
check("Software Ontwikkelaar kept", not ROLE_EXCLUDE.search("Software Ontwikkelaar"))

print("\nPersonio custom fields + answer-safety (round 35)")
import questions as _q
_O = [{"body": "Yes"}, {"body": "No"}, {"body": "LinkedIn"}]
def _ans(q, kind="string"):
    c, f, why = _q.answer_for(q, kind, _O, "EUR 4800", "1 month")
    return "HOLD" if why else (c if c is not None else f"flag={f}")
# A background/VOG screening is a personal consent, not the processing consent that is
# inherent in applying. Auto-answering it Yes is a commitment only Hisham can make.
check("VOG screening consent held", _ans("I agree to participate in a screening, incl. VOG", "single_choice") == "HOLD")
check("background check consent held", _ans("Are you willing to undergo a background check?", "single_choice") == "HOLD")
# A yes/no is a category error on a free-text field, but valid on an option field.
check("yes/no not written into a free-text field",
      _ans("We need someone who communicates in English and understands what it takes") == "HOLD")
check("Yes still valid on an option field",
      _ans("Do you currently have the legal authorization to work in the Netherlands?", "single_choice") == "Yes")
check("visa sponsor option answered No",
      _ans("Would you require a Visa Sponsor to work in The Netherlands", "single_choice") == "No")
# specific free-text rules must precede the broad language yes/no rule
check("languages listed, not answered yes",
      _ans("Languages you speak").startswith("English (fluent)"))
check("Dutch boolean still yes", _ans("Beheers je de Nederlandse taal?", "boolean") == "flag=True")
check("Nationality held (not in profile)", _ans("Nationality") == "HOLD")
check("University answered from CV", "Fontys" in _ans("University"))
check("bare 'How did you hear from us?' answered", _ans("How did you hear from us?") == "LinkedIn")

print("\nDiscipline check — a title-only filter cannot tell developer from property developer")
from filters import wrong_discipline
check("property development rejected",
      wrong_discipline("Ontwikkelaar", "ontwikkelen van nieuwe woningbouwprojecten en het "
                       "opbouwen van een relatienetwerk", "Bouw en Vastgoed Amsterdam"))
check("electrical panel design rejected (CAD-software is a tool, not the job)",
      wrong_discipline("Product Engineer Paneelbouw", "technisch ontwerp van elektrotechnische "
                       "installaties. Kun je goed overweg met CAD-software, MS Office",
                       "Stolze Installatietechniek"))
check("real software role kept",
      not wrong_discipline("Software Engineer (SQL)", "je bouwt met C# en SQL aan ons platform", "Development"))
check("SCADA/PLC engineering kept",
      not wrong_discipline("Scada Engineer", "PLC en SCADA programmeren voor onze machines", "Engineering"))

print("\nUnpaid-role blocker vs unpaid-leave benefit")
from filters import hard_blockers
check("unpaid internship still blocked", "unpaid" in hard_blockers("x", "This is an unpaid internship position"))
check("onbetaald verlof (sabbatical perk) not blocked",
      "unpaid" not in hard_blockers("x", "Elke 4 jaar kun je 4 maanden onbetaald verlof nemen"))
check("unpaid leave benefit not blocked",
      "unpaid" not in hard_blockers("x", "option of unpaid leave after each project"))

print("\nSeniority bar — 21% of historical volume went to senior-only roles")
from filters import seniority_mismatch
check("Senior .NET Engineer excluded", seniority_mismatch("Senior .NET Engineer"))
check("Principal excluded", seniority_mismatch("Principal Engineer - Discovery"))
check("Tech Lead excluded", seniority_mismatch("Tech Lead / Solution Architect (.NET)"))
check("range Junior/Medior/Senior stays eligible",
      not seniority_mismatch("PLC Software Engineer (Junior/Medior/Senior)"))
check("(Senior) marker stays eligible", not seniority_mismatch("(Senior) Data Engineer"))
check("Lead Generation not a seniority word", not seniority_mismatch("Lead Generation Specialist"))
check("plain title stays eligible", not seniority_mismatch("Software Engineer"))

print("\nCover letter — must never claim a skill absent from the CV")
letter, keys = cover_letter.build("X", "Rust Engineer", "Gent", "BE",
                                  "Deep Rust and Erlang expertise required for our ledger.")
check("no Rust claim invented", "rust" not in letter.lower() or "Rust Engineer" in letter)
check("no evidence matched for an unrelated stack", keys == [], str(keys))
letter2, keys2 = cover_letter.build("Y", ".Net Developer", "Dordrecht", "NL",
                                    "We build in .NET and C# with Azure DevOps and REST APIs.")
check("dotnet matched for a .NET posting", "dotnet" in keys2, str(keys2))
check("ASML testing claim only appears when relevant",
      ("ASML" in letter2) == ("testing" in keys2))

print()
if fails:
    print(f"{len(fails)} FAILING: {fails}")
    sys.exit(1)
print("all regression tests passed")
