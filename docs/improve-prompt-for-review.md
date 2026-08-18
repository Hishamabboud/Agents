# Improvement prompt — for the PowerShell job-agent reviewed on 2026-08-18

Hand the block below to the Claude Code session that owns that pipeline. It is written to
be self-contained: the receiving agent has none of the context this review came from, so
every defect carries its own evidence, fix, and verification step.

---

```
I want you to audit and fix my existing job-application pipeline. Do NOT rebuild it — keep
the PowerShell 5.1 + curl.exe design, the Indeed NL discovery source, the Recruitee/Personio
submit path, and all existing hard rules. Work through the defects below IN ORDER, and after
each one show me the verification output before moving on. Commit after each fix.

These came from an external review by someone running the same pipeline design at larger
scale (≈770 companies swept per round, 440+ applications sent). The numbers quoted are from
their measured data, not guesses.

=== DEFECT 1 (CRITICAL — fix before sending another application) ===
Slug guessing has no collision guard, so it can submit to the WRONG COMPANY.

My prober treats a 404 as "no board" and a 200 as "found the board". The second half is
unsafe: a guessed slug frequently returns 200 for a DIFFERENT company's board. Measured
cases from the reviewer's run of 766 companies:
    Royal Kaak / Royal Houdijk -> `royal`  = Personio's "Demo Datos" sample tenant
    Atlas Copco                -> `atlas`  = Atlas-Bildungs-Center e.V.
    Code for Good              -> `code`   = CODE Education GmbH
    KBC Bank & Verzekering     -> `kbc`    = Kemeny Boehme Consultants SE
    Vivid Resourcing           -> `vivid`  = Vivid Money, a Berlin fintech
Nothing downstream catches these: the offers parse, the titles match, and my CV goes to a
company I never searched for. Stripping legal-entity suffixes makes it WORSE by shortening
slugs into more collision-prone words.

Fix:
  - Recruitee: /api/offers/ already returns company_name on each offer. Compare it to the
    company I searched for; reject the board on mismatch.
  - Personio: the XML feed has no company-name field. Fetch https://<slug>.jobs.personio.de/
    and read the tenant's real name from the page <title>, which Personio renders in the
    tenant's own language — strip a leading "Jobs at" / "Jobs bei" / "Banen bij" /
    "Trabajos en" / "Karriere bei" / "Emplois chez" prefix, then compare.
  - Comparison rule: strip legal suffixes (GmbH, B.V., N.V., SE, SLU, AG, e.V., Ltd, Holding,
    Group, Germany, Nederland, Benelux, International) and stopwords from BOTH names, then
    require every remaining word of the SHORTER name to appear in the longer one.
      "HMS Networks" vs "HMS INDUSTRIAL NETWORKS, SLU"  -> accept
      "Code for Good" vs "CODE Education GmbH"          -> reject (shares only a lead word)
  - Two traps the reviewer hit while building this, both of which produced wrong results
    on the first attempt:
      (a) A single shared word is NOT enough unless it is the WHOLE of both names. The
          `vivid` tenant is titled just "Vivid", and a plain subset test accepted it as
          "Vivid Resourcing". Require >=2 shared words, OR a one-word name on both sides.
      (b) Do NOT discount the slug word as "not evidence". A slug that IS the company name
          (Avisi -> avisi) is the STRONGEST possible signal, and a guard that ignored it
          rejected every single-word company.
  - Reject Personio demo tenants explicitly: a page titled "...Demo..." or containing
    "Demo Datos"/"Demo Data" is Personio's own sample content, not an employer.
  - Also strip taglines from company names before slugging. Job boards report display
    names like "Ireckonu - Hotel Middleware & CDP+" and "UbiOps - Private AI on any infra";
    the text after " - " is never part of the slug and breaks both the guess and the match.

Verify: build a fixture list of company/slug pairs with the real tenant titles captured as
strings, and assert accept/reject offline (no network) so the cases stay pinned as tests.
Then re-run the guard over every board I have ALREADY found and show me which ones it now
rejects — those are companies I may have already applied to in error.

=== DEFECT 2: the "0 Personio boards is a genuine result" conclusion is unverified ===
I validated my Personio prober against stark/flatpay/faceland — all three on .personio.COM.
That test passes even if my prober never tries .personio.DE, which is where essentially all
European tenants live. In the reviewer's data every confirmed Personio tenant was on .de:
6/6 applied through, 8/8 found in the latest round, 0 on .com.
Fix: probe BOTH hosts, .jobs.personio.de FIRST, then .jobs.personio.com.
Also correct the framing: their post-collision-guard Personio rate is ~1% of companies, so
over my 154 companies the expected yield is ~1.6 boards and seeing 0 has ~20% probability.
That is sampling noise, not a finding about my role or region. Stop treating it as evidence.

=== DEFECT 3: the Indeed backward-scan can pair fields from ADJACENT cards ===
My parser scans backward up to 3000 chars from each `jobkey` for the nearest title/company,
justified by "the blob is alphabetically key-ordered within a card". That invariant only
holds for keys that sort BEFORE the anchor. `companyOverviewLink` does (c < j); a field
keyed `title` does NOT (t > j), so scanning backward for it lands on the PREVIOUS card.
This is worse than a dropped record: my "drop unless title+company are both found" guard
does not fire, because both ARE found — just from different jobs. The output is a
plausible, wrong job record that survives every downstream check.
Fix: bound the backward scan at the PREVIOUS `jobkey` occurrence instead of a fixed 3000
characters. Then a scan can never cross a card boundary regardless of key ordering.
Verify: print 10 parsed cards next to the raw text they came from and confirm each
title/company pair belongs to one job.

=== DEFECT 4: applications are going out with required screening questions blank ===
HTTP 201 proves the API accepted the submission. It does NOT mean the recruiter sees a
complete application. Recruitee offers carry `open_questions`, often flagged required, and
a submission that omits them lands visibly half-filled. In the reviewer's own latest round
17 of 33 offers had screening questions and 13 had REQUIRED ones — all submitted blank
(one employer had 5 of 5 unanswered). They rated this the most damaging thing the review
surfaced, and it is in their pipeline, not mine — but I should assume mine has it too.
Fix:
  - Before submitting, GET the offer and read `open_questions`.
  - If a required question needs free text I have not answered, HOLD the application and
    log it — never guess an answer. (I already do this for one role; make it systematic.)
  - Maintain an answers file keyed by normalised question text, so recurring questions
    ("Do you require visa sponsorship?", "Can you share your LinkedIn link?", "Are you
    willing to commute to X?") get answered by me ONCE and reused automatically.
  - Present me with a batch of unanswered questions to fill in, rather than blocking on
    each one as it appears.
This same reasoning applies to my `locations_question_required` workaround: the risk was
never API rejection, it was an incomplete-looking application. Keep it opt-in.

=== DEFECT 5: no live re-check at submit time ===
I filter on data captured at discovery time. Between discovery and submission a posting can
close, and a title alone never reveals a 10-year requirement, a security clearance, a
defence programme, or a description written in a language I don't speak. Re-checking the
LIVE posting body caught 4 of 33 in the reviewer's latest round (two defence/avionics roles,
one with a 10+ year bar, two written entirely in French).
Fix: immediately before each submission, re-fetch the offer, confirm it is still published,
and re-run the hard-blocker checks against the live body text. Detect language by
function-word density in the BODY, not the title.

=== DEFECT 6: the tracker is only durable at the end of a batch ===
My freshness guard compares the local entry count against the last git commit, which catches
a working-tree reset but NOT a batch that dies mid-run. The reviewer lost 24 real
submissions this way: a 2-minute command timeout killed the batch after ~24 applications had
already been sent, and because the tracker was written only at the end, none were recorded —
leaving the dedup guards blind, which is the exact state that caused 30 duplicate
applications to real employers earlier in their run.
Fix: write the tracker to disk after EVERY submission, not at the end of the loop. Keep the
freshness guard as well. An unrecorded application is worse than a slow loop.

=== DEFECT 7: single-attempt slug guessing loses ~10% of reachable boards ===
Measured against 244 companies confirmed to use Recruitee, a single naive slug recovered 83%
of them; trying several variants lifted it to 93%. Real cases: adesso Netherlands ->
`werkenbijadesso`, IXON Cloud -> `ixonbv`, KUBUS/BIMcollab -> `bimcollab`.
Fix: try variants in order — suffix-stripped full name, full unstripped, first word (only
when it IS the whole name, so "EY" works but "royal" doesn't become a free pass), first two
words joined and hyphenated, and the `werkenbij`/`jobs`/`careers` prefixed forms. Every hit
still has to pass the DEFECT 1 collision guard.
And answer my own open question properly: to measure how many boards I'm missing, harvest
`company_name` from boards I have ALREADY found to build a list of companies KNOWN to use
the ATS, then measure what fraction my guesser recovers cold. That measures recall directly
instead of estimating it.

=== DEFECT 8: my improvement priorities are inverted ===
My own analysis says the 10.4% discovery->ATS rate is near a structural ceiling and "scales
with company volume fed into the top" — then ranks discovery expansion #5 (medium-large) and
keyword-matcher tweaks #1. With a fixed conversion rate, top-of-funnel volume is the ONLY
lever that changes the absolute number of applications. 154 companies is small; the reviewer
sweeps ~766 NEW companies per round from a single source.
Fix, cheapest first:
  - Paginate deeper on Indeed and rotate to a NEW keyword set every round.
  - Internalise that keywords are COMPANY-DISCOVERY probes, not role matchers. An off-target
    keyword still surfaces a company whose board carries a matching role. This is a
    different job from my title-match list and should be tuned for breadth, not precision.
  - Stop gating re-probes on a permanent `Checked=true`. Large boards turn over; re-probe a
    known board on a TTL (say 7 days) — it is one cheap GET.
  - Only then add a second discovery source (jobbird.com robots.txt is open and untested).

=== DEFECT 9: exclusion list is dropping a bullseye role ===
`Get-SeniorityExclusions` contains `"lead "` with a trailing space, which matches "Lead
Generation Specialist" — a core target title for a sales profile — and silently excludes it.
Fix: match seniority terms on word boundaries against the title as a whole ("team lead",
"tech lead", "lead engineer"), not as a substring. Then audit the whole list against the
last 200 discovered titles and show me which exclusions actually fire and on what.
Also delete `"manager buitendienst regio-directeur"` unless you can point to why it exists.

=== DEFECT 10: cover letters are templated when tailoring is nearly free ===
One template with only company/role varying is honest but generic. Tailoring does NOT
require inventing anything — it requires SELECTING from true CV facts based on the posting
text I already fetch for filtering.
Fix: build an evidence table mapping topics to (detection regex, sentence), where every
sentence is traceable to a line in my resume.md. For each posting, include a claim ONLY if
it is BOTH on my CV AND present in the posting; cap at ~4 points, strongest differentiator
first. If nothing matches, fall back to the honest general letter. This makes fabrication
structurally impossible rather than merely discouraged: a posting about a stack I don't have
matches zero evidence and cannot produce a false claim.
Record which evidence keys fired on each application in the tracker.

=== DEFECT 11: two small honesty items ===
  - `--ssl-no-revoke` IS a security reduction, just a small and scoped one: a revoked
    certificate would now be accepted. It is a reasonable trade-off — describe it accurately
    rather than as "not a security downgrade".
  - My cover letter says my Dutch is "actively improving". That is a claim about my behaviour
    that is not in my CV, and it is the exact category my own hard rules exist to prevent.
    Remove it unless I confirm it is true.
  - Related judgement call for me, not you: I removed the Dutch-language exclusion. For
    SALES roles in NL specifically, client-facing Dutch fluency is usually non-negotiable in
    a way it is not for software roles. Keep applying if I say so, but track outcomes on
    Dutch-language postings separately so we can see whether they ever convert.

=== DEFECT 12 (the biggest blind spot in both pipelines): nothing measures outcomes ===
The reviewer has 440+ applications sent and ZERO recorded employer responses, so neither of
us can say what actually converts. Every "improvement" above is therefore unproven.
Fix: add an outcomes log now, before scaling volume further.
  - A command to record an outcome per application: interview / rejected / ghosted / offer /
    acknowledged / withdrawn, with a free-text note.
  - An import path so I can paste replies in bulk.
  - A report that buckets outcomes by seniority level, stack/role type, ATS, country,
    language of the posting, and tailored-vs-generic letter.
  - Treat "no response after 30 days" as ghosted automatically so the denominator is real.

=== HARD RULES (unchanged — do not relax any of these while fixing the above) ===
- Never invent experience, skills, degrees, or a photo. Only what is in my CV.
- Salary expectation, rate, and notice period are commercial positions, not facts: read them
  from preferences.md and ABORT if absent. Never infer them.
- Only automate genuinely open, public APIs (Recruitee, Personio). Do not defeat CAPTCHAs,
  device fingerprinting, login walls, or WAFs. Log those roles for manual application.
- Honour robots.txt as a policy wall, not an obstacle to route around.
- Respect the blocked-companies list and the 2-applications-per-company cap.
- Submission stays gated behind the explicit -Confirm flag.

=== WHAT I WANT BACK ===
After each defect: the diff, the verification output, and a one-line statement of what would
now fail that previously passed silently. At the end, re-run one full round and report
companies discovered, boards found, boards REJECTED by the collision guard, roles matched,
applications held back for unanswered questions, and applications actually sent — plus a
before/after comparison against my current numbers (154 companies, 16 boards, 7 matches,
6 sent).
```
