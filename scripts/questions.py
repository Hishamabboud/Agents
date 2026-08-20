#!/usr/bin/env python3
"""Screening-question answering — factual answers only, everything else held.

WHY THIS EXISTS
---------------
Recruitee offers carry `open_questions`, frequently flagged required. Round 30 submitted 13
applications with required questions entirely blank. The API returns HTTP 201 either way, so
nothing in the pipeline noticed: a 201 proves the API accepted the request, not that the
recruiter received a complete application.

RULE
----
An answer is produced only when profile/answers.md can source it from the CV or from
preferences.md. Anything else — pronouns, age, references, "why do you want to work here" —
returns None, and the caller HOLDS the application rather than guessing. A fabricated answer
to a screening question is worse than no application at all.

Recruitee question `kind` values seen in the wild:
    boolean, legal          -> answered with flag (true/false)
    string, text, salary    -> answered with content (free text)
    single_choice, multi_choice -> content must match one of open_question_options
"""

import re

# Each entry: (compiled pattern, answer, kind_hint). Order matters — first match wins, so
# the more specific patterns come first.
_RULES = [
    # --- residence / work authorisation
    (r"(require|need).{0,25}(visa|work permit|sponsor)|visa sponsorship|werkvergunning", "no", "bool"),
    (r"(do you (currently )?live|are you based|woon je|woonachtig|gevestigd)"
     r".{0,30}(netherlands|nederland)(?!.{0,20}\bkm\b)", "yes", "bool"),
    (r"valid permit.{0,10}(to work|/visa)|eu passport|werkvergunning", "yes", "bool"),
    (r"(where are you|from what location|waar (woon|ben) je|current location|"
     r"currently located|looking to work)", "Eindhoven, Netherlands", "text"),
    # Willingness to the working arrangement the posting itself states (hybrid, on-site at a
    # client, N days in the office). Applying to a role already accepts its stated setup.
    (r"(okay with this|akkoord|comfortable with).{0,40}$|"
     r"(remote and in person|hybrid|on.?site|client site).{0,80}(okay|comfortable|akkoord)",
     "yes", "bool"),

    # --- previous employment with this employer. MUST come before the language rules:
    # "Heb je eerder in loondienst gewerkt voor RTL Nederland of DPG Media?" contains the
    # word "Nederland" inside a COMPANY NAME, and the broad Dutch-language rule below
    # answered it "yes" - a false statement about employment history.
    (r"(previously worked|eerder.{0,25}gewerkt|ooit gewerkt|worked for)", "no", "bool"),

    # --- language
    (r"(which|what|welk).{0,25}(level|niveau).{0,25}(dutch|nederlands)",
     "Fluent - professional working proficiency in both speech and writing.", "text"),
    # Require language CONTEXT, never the bare country/language word: the word "Nederland"
    # also appears inside company names ("RTL Nederland"), where "yes" would be a false
    # answer to a question about something else entirely.
    (r"(taal|talen|language|spreek|speak|beheers|schriftelijk|mondeling|werkoverleg|"
     r"verbal|written|fluen|proficien|\bb1\b|\bb2\b|\bc1\b)", "yes", "bool"),
    (r"\benglish\b|engels", "yes", "bool"),

    # --- education
    (r"(hoogst genoten opleiding|highest.{0,15}education|opleidingsniveau)",
     "BSc Software Engineering, Fontys University of Applied Sciences, Eindhoven", "text"),
    (r"(diploma|degree|bachelor).{0,60}(informatica|software|computer|elektronica|electronic|engineering)",
     "Yes - BSc Software Engineering, Fontys University of Applied Sciences, Eindhoven.", "text"),

    # --- contact
    (r"linkedin", "https://linkedin.com/in/hisham-abboud", "text"),

    # --- commercial commitments (set by Hisham in preferences.md, never inferred)
    (r"salar|bruto per maand|gross monthly|loonverwachting", None, "salary"),
    (r"(hoeveel uur|hours per week|uur per week|beschikbaar.{0,20}uur)",
     "40 hours per week (full-time)", "text"),
    (r"(vast dienstverband|loondienst|permanent employment|contract of employment|"
     r"fulltime|full.time) (position|functie|role)?", "yes", "bool"),
    (r"(when (can|are) you (able to )?start|beschikbaar per|wanneer.{0,15}beginnen|"
     r"availability|notice period|opzegtermijn|start date)", None, "notice"),

    # Willingness to be onsite where the role is. Applying to a role in that city already
    # asserts this; it is not a new claim. Distinct from "do you LIVE within X km of <town>",
    # which is a fact about distance and stays in _NEVER.
    (r"(comfortable|bereid|willing|akkoord).{0,40}(commut|working|work|reizen|days|dagen)|"
     r"(days|dagen).{0,25}(per week|/week).{0,25}(in|te|naar)", "yes", "bool"),

    # --- source of the vacancy
    (r"(how did you|hoe (ben je|heb je)|via welk kanaal|waar heb je).{0,40}"
     r"(vacature|vacancy|job|find|found|terechtgekomen|gevonden)", "LinkedIn", "choice"),

    # --- marketing vs. legal consent
    (r"newsletter|nieuwsbrief", "no", "bool"),
    (r"(privacy|persoonsgegevens|personal data|gdpr|avg\b|i agree|ermee akkoord)", "yes", "legal"),
]

# Questions that must never be auto-answered, even if a rule above would match.
_NEVER = [
    (r"pronoun|voornaamwoord", "pronouns are not in the profile, and a name is not evidence of them"),
    (r"\bgeslacht\b|\bgender\b|\bleeftijd\b|\bage\b|geboortedatum|date of birth",
     "not in the profile"),
    (r"\bwithin\b.{0,20}\bkm\b|straal van|radius of|\bkm\b.{0,25}(van|from)",
     "a distance fact, not a willingness statement - needs confirming"),
    (r"referent|\breference[sn]?\b", "requires real people who have agreed to be named"),
    # free-text motivational questions
    (r"why (do|would) you|waarom (wil|zou)|wat spreekt je aan|welke aspecten|"
     r"motivat|kom jij je bed|trots op|proud of|kernwaarde|tell us about|vertel",
     "needs Hisham's own words"),
]


def answer_for(question, kind, options=None, salary=None, notice=None):
    """Return (content, flag, reason_if_unanswerable).

    content/flag are what to submit; exactly one is set. If the third value is non-None the
    question could not be honestly answered and the application must be held.
    """
    body = re.sub(r"<[^>]+>", " ", question or "")
    body = re.sub(r"\s+", " ", body).strip()
    low = body.lower()

    for pat, why in _NEVER:
        if re.search(pat, low, re.I):
            return None, None, why

    for pat, ans, hint in _RULES:
        if not re.search(pat, low, re.I):
            continue
        if hint == "salary":
            ans = salary
        elif hint == "notice":
            ans = notice
        if ans is None:
            return None, None, "commercial commitment missing from preferences.md"

        if kind in ("boolean", "legal"):
            return None, str(ans).lower() in ("yes", "true", "1"), None
        if kind in ("single_choice", "multi_choice"):
            opts = [o.get("body") or "" for o in (options or [])]
            pick = next((o for o in opts if ans.lower() in o.lower()), None)
            if not pick:      # no matching option -> fall back to an "other" option
                pick = next((o for o in opts
                             if re.search(r"^(other|anders|overig)", o.strip(), re.I)), None)
            if not pick:
                return None, None, f"no option matches {ans!r} (options: {opts})"
            return pick, None, None
        return str(ans), None, None

    return None, None, "no profile-backed answer"


def build_answers(open_questions, salary, notice):
    """Return (answers, blockers).

    answers  = [{"id","content"|"flag","question"}] for everything answerable
    blockers = [{"question","kind","required","reason"}] for everything that is not
    """
    answers, blockers = [], []
    for q in open_questions or []:
        content, flag, why = answer_for(q.get("body"), q.get("kind"),
                                        q.get("open_question_options"), salary, notice)
        if why:
            blockers.append({"question": re.sub(r"<[^>]+>", " ", q.get("body") or "")[:200].strip(),
                             "kind": q.get("kind"), "required": bool(q.get("required")),
                             "reason": why})
            continue
        a = {"id": q.get("id"), "question": q.get("body")}
        if flag is None:
            a["content"] = content
        else:
            a["flag"] = flag
        answers.append(a)
    return answers, blockers
