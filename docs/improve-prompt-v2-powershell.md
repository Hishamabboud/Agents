# Improvement prompt v2 — for Kourosh's PowerShell pipeline (Switzerland session)

Hand the block below to the Claude Code session that owns the PowerShell pipeline.
Follow-up to the first improvement prompt; every item comes from findings MEASURED live in
the sibling Python pipeline (633 applications, 34 rounds) after that first review.

---

```
Follow-up audit for my job-application pipeline. Do NOT rebuild anything — keep the
PowerShell 5.1 + Invoke-WebRequest design, the honest Claude-User UA, the robots.txt
checks, the two-ATS boundary, and the offline test suite. Work the items IN ORDER; after
each, show me the verification output and add a regression test before moving on. Commit
after each item.

Context: these come from the sibling pipeline this design was reviewed against. Since the
first review it has run 34 rounds and 633 real applications, and each item below is a
defect or win MEASURED there — the numbers are real, not hypothetical. Some items may
already be handled; for those, show me the code/test that proves it and move on.

=== ITEM 1 (VERIFY BEFORE THE NEXT -Confirm RUN): Recruitee silently discards
    structured screening answers ===
The open POST /api/offers/<slug>/candidates endpoint ACCEPTS open-question answers
without error and STORES NONE OF THEM. Measured repeatedly: every multipart format tried
(snake_case, camelCase, indexed, JSON-encoded) returned HTTP 201, and the response's
candidate object echoed open_question_answers with every content/flag null. The careers
page that does persist answers posts to a DIFFERENT endpoint gated by a captchaToken,
which is off-limits by our own rules.
So: HTTP 201 + "answers sent" can still mean the recruiter sees a half-blank application.
If Submit-Application.ps1 sends structured answers, it likely has this bug live right now.
Fix:
  a. After every submit, parse the 201 response and check whether ANY echoed answer has
     non-null content/flag. Log "sent N, recorded M" per application.
  b. Assume M=0 (that is what we measured on every tenant tried): append the Q&A as plain
     text at the end of the cover-letter field instead — recruiters read that field. Keep
     the structured attempt as best-effort.
  c. Keep the existing hold-if-unanswerable rule; this changes the DELIVERY of answers,
     never invents one.
Verify: one real submission (a role from the shortlist I approve), showing the sent/
recorded counts and the letter body containing the Q&A block.

=== ITEM 2 (BIGGEST YIELD WIN AVAILABLE): re-scan every known board every round ===
Measured in the sibling pipeline: when keyword sweeps bottomed out (70 never-seen
companies out of 889 in a round), re-fetching EVERY board ever discovered found 362 of
389 still live carrying 7,740 open positions -> 32 applications in one round, versus 3-6
from a keyword sweep. Cost: one GET per board.
If companies-seen.json still gates probing to once-ever, this is the highest-value change
in this list:
  - Maintain a known-tenants list (every Recruitee slug / Personio host ever confirmed,
    including ones that had no matching role at the time).
  - Every round, walk that list and diff current offers against applications.json and
    the shortlist history. New postings on old boards are the harvest.
  - Every future discovery permanently enlarges this pool, so the round yield compounds.
Verify: run one re-scan round and report boards still live, total open positions, and net
new candidates after all filters.

=== ITEM 3 (SWITZERLAND-SPECIFIC, do this before applying at volume in CH) ===
(a) LANGUAGE IS NOW A HARD BLOCKER. My languages: English C1, Dutch A2, Persian native —
    NO German, NO French. Most Swiss postings, and almost all Swiss SALES postings, are in
    German (French in Romandie). Detect language from BODY function-word density (not the
    title — titles are often English over a German body) and HARD-BLOCK German/French
    postings, don't just flag them. A client-facing sales application to a German-language
    role I cannot hold is noise that burns the employer relationship.
    Corollary to say out loud in the round report: English-only Swiss roles cluster in
    pharma/multinationals = exactly the Workday/SuccessFactors employers on the manual
    list. Expect the automatable pool in CH to be SMALL. That is a market fact, not a
    pipeline failure.
(b) PROBE BOTH PERSONIO HOSTS, .jobs.personio.DE FIRST. In the sibling pipeline every
    real European tenant sat on .de — including Dutch companies; .com hosted almost
    nothing real. A .com-only probe returns a clean, false zero. (A previous "0 Personio
    boards is a genuine result" conclusion was validated against three tenants that were
    all .com — the test could not detect a missing .de probe. Do not repeat that.)
(c) Recruitee is thin in DACH (~1.5% measured earlier). In CH, Personio IS the channel.

=== ITEM 4: Personio SUBMISSION — verified flow to port (if not built yet) ===
The stack lists Personio probing only. Submission works end-to-end on the tenant host
(never career-pages-api.personio.de — that returns 401):
  GET  /xml                                    feed (no auth)
  GET  /api/v1/jobs/<id>/application-form      field schema; HONOUR its required flags,
                                               abort on any field the profile can't fill
  POST /api/v1/documents                       multipart: file=@cv.pdf, category=cv
                                               -> returns {uuid, size, mimetype, ...}
  POST /api/v1/jobs/<id>/application           JSON submit
Traps that each cost an hour+ live:
  - files[] accepts ONLY {uuid, original_filename, category}. Spreading the whole upload
    response in (as Personio's own JS appears to) -> HTTP 400 with a kotlinx.serialization
    error naming the offending key.
  - SUCCESS IS HTTP 200 WITH AN EMPTY BODY. Not 201, no id returned. Don't treat empty as
    failure.
  - Header Idempotency-Key must EQUAL body.idempotencyToken (same uuid4).
  - x-company-id is scraped from the /job/<id>/apply page HTML (company_id in the JS).
  - sender: {id: "sender<random>", value: ""} is required boilerplate.
  - salary_expectations and available_from are commercial commitments: read from my
    preferences file, ABORT if absent. Never inferred (unchanged hard rule).

=== ITEM 5: key the 2-per-company cap on the RESOLVED TENANT, not the display name ===
Job boards report one employer under many names. Measured damage in the sibling tracker:
  "DPG Media" / "DPG Media Belgie" / "DPG Media Nederland" / "DPG Media / Independer"
     -> all ONE tenant (dpgmedia), which had received 9 applications against a cap of 2.
  adesso -> 302-redirects to werkenbijadesso, where 6 had already gone.
An audit with the tenant key found 21 employers over cap. Fix:
  - Cap key = "recruitee:<final-slug-after-redirects>" or "personio:<host-prefix>".
  - Resolve the redirect BEFORE the cap check (HEAD the offer URL; POSTs don't follow
    redirects anyway, so you need the real tenant to submit at all).
  - Run the audit over my applications.json and report which employers are already over.

=== ITEM 6: two PowerShell 5.1 traps that matter MORE in a German-language market ===
  - ENCODING: Personio serves UTF-8 but usually omits the charset. IWR on PS 5.1 then
    decodes as ISO-8859-1, so umlauts/em-dashes arrive as mojibake — which flows into job
    titles, the tracker, and any generated letter ("Ore Energy â Edge Systems" happened
    live). Decode explicitly: [Text.Encoding]::UTF8.GetString($resp.RawContentStream
    .ToArray()) or equivalent, and unescape HTML entities in titles (&amp; etc.).
  - NOMINATIM: pass countrycodes=ch (per active market) — bare city names resolve to the
    wrong country surprisingly often. City text that is "Hybrid"/"Remote"/multi-city goes
    to needs-review, NOT silently through the distance filter (a "TradeTracker India
    remote" role once passed a location filter this way). Keep <=1 req/s per their usage
    policy; the cache mostly covers it.

=== ITEM 7: honest outcome denominators, from day one in the new market ===
Cautionary number from the sibling pipeline: 633 applications before the FIRST employer
response was ever recorded — months of tuning send-rate with zero signal on conversion.
  - In the outcomes REPORT ONLY, count any application >30 days old with no logged reply
    as implied-ghosted. Never write it to the log; a late reply overwrites the implication.
  - Record per application: discovery source, letter variant, language of posting,
    tenant, seniority level. These are the buckets that will eventually say what converts.
  - Data point worth internalising: the sibling pipeline's first interview came from a
    LOCAL, mid-level, in-stack role with a GENERIC letter. Fit and proximity converted;
    volume and sophistication did not. For CH that predicts: the wins are the handful of
    English-OK roles near where I would actually work.

=== ITEM 8: guards worth porting if absent (each tied to a real incident) ===
  - Collision guard on slug-guessing: verify Recruitee's company_name / Personio's page
    <title> ("Jobs at X" / "Jobs bei X" / "Trabajos en X") against the searched company.
    Reject Personio DEMO tenants (title containing "Demo", "Demo Datos"). A single shared
    word only counts when it is the whole of both names — the `vivid` tenant is titled
    just "Vivid" (Vivid Money, Berlin) and a subset test accepted it as "Vivid
    Resourcing". Five real wrong-company hits measured in one round.
  - Discipline check on the LIVE body: a title-only filter cannot tell disciplines apart.
    Two applications went out to a residential PROPERTY developer ("Ontwikkelaar", dept
    Bouw en Vastgoed) and an electrical panel designer before this existed. For a sales
    profile the analogue: "Business Developer" in construction/staffing vs tech. Where
    the department/context is off-profile, require named evidence of the actual work in
    the body, not one ambiguous word.
  - Benefit-vs-blocker false positive: "onbetaald verlof" / "unpaid leave" is a
    sabbatical PERK; a naive unpaid-role blocker rejected a valid vacancy on it. German
    equivalent to guard now: "unbezahlter Urlaub" is a benefit, "unbezahlt" alone in a
    role context is a blocker.
  - Tracker written after EVERY submission (not end of batch) — a 2-minute timeout once
    killed a batch after ~24 real submissions with zero recorded; that state causes
    duplicate spam later. If already fixed from the first review, just point at the test.

=== UNCHANGED HARD RULES ===
Everything from the first review stands: never invent facts or answers; commitments only
from my preferences file; only the two open public APIs; robots.txt is a policy wall;
honest UA; blocked-companies list; -Confirm gate; start small after each change.

=== WHAT I WANT BACK ===
Per item: what you found (including "already handled, here is the test"), the diff, the
verification output, and one line on what would now fail that previously passed silently.
Then one full CH round with the new setup, reporting: boards re-scanned vs newly
discovered, positions seen, candidates after language filtering (with a count of German/
French roles blocked), applications sent, and answers sent-vs-recorded per submission.
```
