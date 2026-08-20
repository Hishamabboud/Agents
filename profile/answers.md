# Application screening answers

Recruitee and Personio offers carry screening questions, often flagged required. Round 30
sent 13 applications with required questions left completely blank — HTTP 201 from the API,
but visibly half-filled to the recruiter reading it.

Every answer below is traceable to `profile/resume.md` or `profile/preferences.md`. The
`source:` line says where. Nothing here is inferred — anything the profile cannot answer is
sent to `data/pending-questions.md` for Hisham to answer, and the application is HELD until
he does.

Edit any answer here and it applies to every future application.

---

## Factual — answered from the profile

**Do you live in the Netherlands? / Woon je momenteel in Nederland?**
answer: yes
source: preferences.md — based in Eindhoven, Netherlands

**Do you require visa sponsorship / a work permit?**
answer: no
source: preferences.md line 27 — "Visa: Not needed (I have work authorization in NL)"

**Do you speak/write Dutch? / Beheers je de Nederlandse taal? / Kun je een werkoverleg in het Nederlands bijwonen?**
answer: yes
source: resume.md line 52 — "Dutch (fluent)"

**Which level of Dutch do you master? / Welk taalniveau Nederlands?**
answer: Fluent — professional working proficiency in both speech and writing.
source: resume.md line 52 — "Dutch (fluent)"

**Do you speak English?**
answer: yes
source: resume.md line 51 — "English (fluent)"

**What is your highest level of education? / Wat is jouw hoogst genoten opleiding?**
answer: BSc Software Engineering, Fontys University of Applied Sciences, Eindhoven
source: resume.md line 40

**Do you hold a degree in Computer Science / Software Engineering / Electronics or similar?**
answer: Yes — BSc Software Engineering, Fontys University of Applied Sciences, Eindhoven.
source: resume.md line 40

**Your LinkedIn profile / Could you share your LinkedIn link?**
answer: https://linkedin.com/in/hisham-abboud
source: preferences.md line 71

**What is your salary indication / expected gross monthly salary?**
answer: EUR 4800 gross per month
source: preferences.md — "Application form answers (set by Hisham)". A commercial
commitment: set by Hisham, never inferred.

**How many hours per week are you available? / Hoeveel uur per week?**
answer: 40 hours per week (full-time)
source: preferences.md line 33 — "Contract type: Full-time preferred"

**Are you looking for permanent employment? / Bent u op zoek naar vast dienstverband?**
answer: yes
source: preferences.md line 33 — "Full-time preferred, open to freelance"

**When can you start? / Availability / notice period**
answer: 1 month notice period
source: preferences.md — "Application form answers (set by Hisham)"

**How did you find this vacancy? / Via welk kanaal heb je deze vacature gevonden?**
answer: LinkedIn
source: factually true — every role in this pipeline is discovered via LinkedIn job search.
When the question is single-choice, pick the option matching LinkedIn; if there is no
LinkedIn option, pick the one meaning "other".

**Have you previously worked for this company (or its group)?**
answer: no
source: resume.md employment history — the company does not appear on it.

**Would you like to subscribe to our newsletter?**
answer: no
source: not requested by Hisham; a marketing opt-in is never assumed.

**Privacy policy / consent to process personal data (kind: legal)**
answer: yes
source: consenting to process the application is inherent in submitting it. This covers
processing-consent only — never a separate marketing or talent-pool opt-in.

---

## NOT answerable — always held for Hisham

These are never guessed. The application is held and the question is written to
`data/pending-questions.md`.

- **Pronouns.** Not in the profile, and a name is not evidence of anyone's pronouns.
- **Gender / age / date of birth.** Not in the profile.
- **"Do you live within X km of <town>?"** A fact about distance, not willingness.
  Answerable only if Hisham confirms it.
- **References.** Requires real people who have agreed to be named.
- **Any free-text motivational question** — "why this company", "what appeals to you about
  this role", "what gets you out of bed", "describe a project you are proud of". These need
  Hisham's own words. A generic answer here reads worse than no answer at all.

---

## Added round 31 — phrasings the first pass missed

**Are you based in the Netherlands? / Where are you currently located? / From what location are you looking to work?**
answer: Eindhoven, Netherlands
source: preferences.md — based in Eindhoven

**Do you have an EU passport or a valid permit/visa to work in the Netherlands?**
answer: yes
source: preferences.md line 27 — "Visa: Not needed (I have work authorization in NL)"

**When are you able to start? / Start date**
answer: 1 month notice period
source: preferences.md — "Application form answers (set by Hisham)"

**Are you looking for a fulltime position?**
answer: yes
source: preferences.md line 33 — "Contract type: Full-time preferred"

**The role is hybrid / on-site at a client / N days in the office — are you okay with this?**
answer: yes
source: applying to a role already accepts the working arrangement the posting states.
Distinct from "do you LIVE within X km of <town>", which stays held.

### Still held, deliberately
- **"Please share your GitHub"** — no GitHub URL in the profile. Add one to preferences.md
  and it will be answered automatically.
- **"Hoeveel jaar ervaring heb je in een vergelijkbare functie?"** — what counts as a
  comparable role is Hisham's judgement, not a lookup.
- **"Explain briefly your .NET experience" / "Describe the most complex solution you built"**
  — screening essays. The CV backs the facts, but the words should be his.
