# Job Search Preferences

## Target Roles
- Full Stack Developer
- .NET / C# Developer
- Software Engineer
- Service Engineer (IT/OT)
- Python Developer
- AI/ML Engineer

## Required
- Location: Anywhere in the Netherlands, or Remote
  - **Freelance/ZZP only (decided 2026-07-29): also Belgium (Antwerp/Brussels/Leuven/Gent) and
    EU-wide remote contract work.** Permanent roles remain NL + remote only.
  - Note: Dutch fluency is an advantage in the Flemish market.

## Freelance / ZZP (added 2026-07-29)
- Registered ZZP'er with KVK/BTW — can invoice directly
- **Rate: €75/uur** (benchmark: NL ICT junior €65–78, medior €82–92, senior €95–110)
- Do NOT auto-submit freelance applications: every broker form requires a `Tarief` field, which
  is a binding commercial offer. Rate must be confirmed by Hisham per assignment.
- Target assignments with a **2–3 year** experience bar, not 5+ (see data/freelance-research.md)
- Declined: Etinars .NET/Python energy role — Brussels onsite 2 days/wk, ~€59–63/hr (below floor),
  posted 5½ months prior
- Language: English or Dutch
- Minimum salary: €50,000/year (or skip if not listed)
- Visa: Not needed (I have work authorization in NL)

## Preferred
- Tech stack: .NET, C#, ASP.NET, Python, Flask, JavaScript, React
- Industries: Manufacturing, AI, SaaS, Automation, IoT
- Company size: Doesn't matter
- Contract type: Full-time preferred, open to freelance

## Avoid
- Unpaid internships
- Roles requiring 10+ years experience
- Roles requiring security clearance
- Pure frontend-only roles
- Commission-only sales roles

## Blocked Companies (do NOT apply again)
- Friday Recruitment (fridayrecruitment) — Recruiter requested we stop. 15 applications sent, too many.
- KUBUS / BIMcollab — 29 duplicate submissions to the same role. Do not reapply.
- Sendent B.V. — 9 duplicate submissions to the same role. Do not reapply.
- Funda Real Estate B.V. — 7 duplicate submissions to the same role. Do not reapply.
- Sendcloud — 5 duplicate submissions to the same role. Do not reapply.
- ChipSoft — 5 duplicate submissions to the same role. Do not reapply.
- UbiOps — 4 duplicate submissions to the same role. Do not reapply.
- Prodrive Technologies — 2 duplicate submissions. Do not reapply.
- Futures.Works — 2 duplicate submissions. Do not reapply.
- Yellowtail Conclusion — 2 duplicate submissions. Do not reapply.

## Application Limits
- Max 2 applications per company/recruitment agency
- Recruitment agencies (e.g. Friday, HeadFirst) represent many roles but route to the same recruiter — treat all their listings as one company
- Space out applications to the same company by at least 1 week

## Job Boards to Search
1. LinkedIn Jobs (nl.linkedin.com/jobs)
2. Indeed NL (nl.indeed.com)
3. StepStone NL (stepstone.nl)
4. Glassdoor NL
5. Werkenbij (werkenbij.nl)
6. ICTerGezocht (ictergezocht.nl)

## My Details for Forms
- Full Name: Hisham Abboud
- Email: hiaham123@hotmail.com
- Phone: +31 06 4841 2838
- LinkedIn: linkedin.com/in/hisham-abboud
- GitHub: github.com/Hishamabboud
- City: Eindhoven
- Country: Netherlands

## Application form answers (set by Hisham — never infer these)
- Salary expectation (Personio `salary_expectations` field): EUR 4800 per month (~EUR 58k/yr)
- Availability / notice period: 1 month notice period
  (Both confirmed 2026-08-04. These are commercial commitments — scripts must read them from
  here and abort if absent, never guess. Same rule as the freelance Tarief field.)

## Discovery sources (verified against each site's robots.txt)

- **LinkedIn** (`nl.linkedin.com/jobs/search`, logged-out HTML) — used since round 1.
  Effectively mined out for NL/BE: round 32 found 70 never-seen companies out of 889.
- **Indeed NL** (`nl.indeed.com/jobs`) — added round 34. Its robots.txt names `Claude-User`
  in a group with `Allow: /` plus explicit `&start=` pagination allowances (verified
  2026-08-24), so requests identify honestly as Claude-User rather than spoofing a browser.
  Surfaces a genuinely different company set (DAF, SPIE, Kuijpers, Sioux, HighTechXL):
  67 of 102 companies were new to the pipeline on first use.
  Note: only `start=0` returns cards; deeper pagination came back empty.
- **werk.nl** — robots.txt is open, but the vacancy search is a JS-rendered app with no
  plain HTML or API found. Untried.
- **jobbird.com** — robots.txt permits the search paths. Untried.

### Discovery source limits (measured round 35, 2026-08-24)

- **Indeed NL is PAGE-1 ONLY.** `&start=0` returns a full ~1MB results page; `&start=10`
  and beyond redirect to an Indeed **login page** ("Inloggen | Indeed-accounts") carrying
  reCAPTCHA and a Cloudflare challenge script. robots.txt permits the paths, but the site
  serves a login wall in practice — and defeating login walls / CAPTCHAs is off-limits
  under this project's rules. Do not attempt to page deeper. ~20 companies per query is
  the ceiling; get breadth from more QUERIES, not more pages.
- **jobbird.com is unusable.** Its real search endpoint is `/nl/vacature?s=...`, which its
  own robots.txt disallows (`Disallow: /nl/vacature?*`), and `/*/api` is disallowed too.
  The one allowed page is a JS-rendered Nuxt shell with no server-side results. Reaching
  results would mean violating robots.txt or executing JS against an internal API. Dropped.
- **werk.nl** remains untried (open robots.txt, JS-rendered search).
