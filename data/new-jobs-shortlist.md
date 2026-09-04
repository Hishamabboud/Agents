# New Job Shortlist — 2026-09-04

Search run: `python3 scripts/search_english_nl.py --pages 3`
Sources: englishjobsearch.nl (6 role queries × 3 pages) + Greenhouse boards.

**201 new listings** passed the Netherlands gate, relevance filter and dedupe.
199 are English-language, 0 explicitly require Dutch. 134 are direct employers
(the rest are recruitment agencies, capped at 2 applications each by policy).

## Verification outcome — do NOT apply to these three

I checked the stated requirements against the resume before drafting anything.
All three of the roles first flagged as top picks fail on requirements.

| Role | Stated requirement | Profile | Verdict |
|---|---|---|---|
| Cirrix — Medior .NET / DevOps (Azure), Rotterdam | "Strong C# developer and architect track record (5+ years)" | ~2.5 yrs, no architect role | Mismatch despite the "Medior" title |
| Portbase — Full-Stack Developer, Rotterdam | Min. 5 yrs; Angular, Java, AWS | ~2.5 yrs; React, C#/.NET/Python, Azure | Mismatch on both tenure and stack |
| Portbase — Java Developer (English), Rotterdam | 3+ yrs Java | No Java on the resume at all | Mismatch |

Cirrix could not be reached from this container on any of cirrix.nl,
www.cirrix.nl, cirrix.io or cirrix.com, so the only evidence is a 163-character
aggregator snippet. If the full posting turns out to be genuinely medior, it is
worth a second look — but on the text available it asks for double the
experience.

The agent rules say to skip roles requiring skills not on the resume and never
to fabricate experience, so none of these were submitted.

## Genuine fits found instead

| Company | Role | Location | Posted | Why it fits |
|---|---|---|---|---|
| Research & Development | Jr/Mr/Sr Fullstack Developer (JavaScript/C#/.NET) | The Hague | Aug 1 | Posting reads "As a **Junior** full-stack .NET developer"; asks for C#, .NET, JavaScript, HTML/CSS and a Bachelor's — an exact match |
| Tournament Software (Visual Reality) | C#/.NET + React Full-Stack Developer | Alkmaar | Aug 7 | "C#, .NET, React and SQL — non-negotiable" is precisely the Actemium stack |

Neither could be turned into an apply URL from here: the aggregator's links
pass through tdrct.com, a JS redirector Playwright could not follow through the
proxy, and tournamentsoftware.com sits behind a cookiewall. Both need either a
LinkedIn lookup or a manual visit to get the application route.

## Also checked and rejected

- **MYLAPS — Back End Developer, Haarlem.** Reads as a .NET role in the
  aggregator, but the posting is Java/Spring Boot; the .NET solution is being
  phased out and .NET experience is only "a plus".
- **Capgemini — Python Backend Developer (Gen AI), Utrecht.** Requires 7+ years.
- **ORTEC — Full-Stack Developer, Zoetermeer.** No longer on ortec.com/careers;
  treat as expired.
- **Squla — Medior Python Backend Developer, Amsterdam.** Already applied
  2026-06-25 (Recruitee candidate ID 125164382). Squla is FutureWhiz's brand,
  so the tracker held it under a different name. Now handled by the alias map
  in `search_english_nl.py`, which drops this listing and two sibling Squla
  roles on re-run (204 results became 201).

## Notes on source reachability

- englishjobsearch.nl — works, 20 listings per page, `?page=N` pagination.
  Descriptions are snippets (median 431 chars), so stated requirements often
  cannot be verified without opening the original posting.
- Greenhouse API — works for adyen, optiver, elastic, gitlab, trivago,
  catawiki, databricks. Most Dutch scale-ups are not on Greenhouse.
- Recruitee — full descriptions and a working submission path already proven in
  this repo (82 company slugs used to date). A sweep of ~90 candidate Dutch
  employer slugs turned up only 9 live boards, mostly senior roles. Portbase is
  a new slug worth keeping for future runs.
- Indeed NL and ICTerGezocht — both return HTTP 403 to this container.
- Lever — no Dutch employer slugs resolved from the set tried.
