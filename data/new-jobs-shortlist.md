# New Job Shortlist — 2026-09-04

Search run: `python3 scripts/search_english_nl.py --pages 3`
Sources: englishjobsearch.nl (6 role queries × 3 pages) + Greenhouse boards.

**204 new listings** passed the Netherlands gate, relevance filter and dedupe.
202 are English-language, 0 explicitly require Dutch. 134 are direct employers
(the rest are recruitment agencies, capped at 2 applications each by policy).

## Top picks — .NET / C# (strongest profile match)

| Company | Role | Location | Posted | Status |
|---|---|---|---|---|
| Cirrix | Medior .NET / DevOps Engineer (Azure) | Rotterdam | Sep 2 | Site unreachable from container — needs manual check |
| Tournament Software | C#/.NET + React Full-Stack Developer | Alkmaar | Aug 7 | Careers page behind cookiewall |
| Research & Development | Jr/Mr/Sr Fullstack Developer (JavaScript/C#/.NET) | The Hague | Aug 1 | Not yet verified |
| MYLAPS Sports Technology | Back End Developer (.NET in description) | Haarlem | Aug 1 | Careers page is JS-rendered |

Cirrix is the freshest and the closest match: medior level, .NET plus Azure,
which lines up with both the Actemium and ASML experience.

## Top picks — Python / Full-stack

| Company | Role | Location | Posted | Apply route |
|---|---|---|---|---|
| Portbase | Full-Stack Developer | Rotterdam | Jul 31 | **Recruitee API** — https://werkenbij.portbase.com/o/full-stack-developer |
| Portbase | Java Developer (English) | Rotterdam | live | **Recruitee API** — https://werkenbij.portbase.com/o/java-developer-english |
| Capgemini | Python Backend Developer (Gen AI / Agentic AI) | Utrecht | Aug 31 | Not yet verified |
| Zypp | Python Developer | Rotterdam | Aug 15 | Careers page is JS-rendered |
| FIRM24 | Full Stack Engineer | Amsterdam | Jun 11 | Careers URL 404 — likely stale |

Portbase is the most actionable: it runs on Recruitee, which the repo already
submits to successfully via `scripts/submit_batch_v6.py`. Note the Full-Stack
posting is written in Dutch (Angular/TypeScript front-end, cloud back-end);
the Java Developer posting is explicitly flagged English.

## Verified duplicate — do not apply

**Squla / Futurewhiz — Medior Python Backend Developer, Amsterdam.**
Already applied 2026-06-25 (Recruitee candidate ID 125164382, HTTP 201).
The aggregator lists it under the brand name "Squla" while the tracker holds
the legal entity "FutureWhiz", and the aggregator's tracking URL differs from
the canonical one, so both the company-name and URL dedupe checks missed it.
Worth adding a brand-to-entity alias map before the next run.

## Stale listing

**ORTEC — Full-Stack Developer, Zoetermeer (Aug 21).** Not present on
ortec.com/careers/jobs today; the board currently lists only Data Engineer,
Software Engineer (Angular), Senior Software Engineer and two security roles.
Treat the aggregator entry as expired.

## Notes on source reachability

- englishjobsearch.nl — works, 20 listings per page, `?page=N` pagination.
- Greenhouse API — works for adyen, optiver, elastic, gitlab, trivago,
  catawiki, databricks. Most Dutch scale-ups are not on Greenhouse.
- Indeed NL and ICTerGezocht — both return HTTP 403 to this container.
- Lever — no Dutch employer slugs resolved from the set tried.
- Aggregator clickout links pass through tdrct.com, a JS redirector that
  Playwright could not follow through the proxy. Resolving to real apply URLs
  currently means looking the role up on the employer's own site.
