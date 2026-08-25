# Instructions for Claude in Chrome

Three separate jobs, most valuable first. Each block is self-contained — open a Claude in
Chrome session, paste one block, and work through it with the browser open. Give it one job
at a time; these are not a single long script.

The pipeline in `~/Agents` handles discovery, filtering, dedup and the two open-API
submissions. Chrome's job is everything that needs a human present: gated forms, and the
inbox this system has never been able to see.

---

## JOB 1 — Harvest six months of employer replies (highest value by far)

**Why this first:** 643 applications have been sent since February and exactly **one**
outcome has ever been recorded. Every rejection, interview invite and acknowledgement went
to Hisham's inbox, which the pipeline cannot read. Until that data comes back, nothing can
say what actually converts — every improvement made so far is unproven. This one session
is worth more than the next several rounds of applying.

```
I'm in my email (hiaham123@hotmail.com). Since 2026-02-24 I've sent ~643 job applications
and I've never gone through the replies systematically. Help me extract them.

Search my inbox — including Spam/Junk and any Promotions/Other folders — for replies from
employers. Useful search terms: "sollicitatie", "vacature", "application", "uw
sollicitatie", "helaas", "afwijzing", "unfortunately", "interview", "gesprek",
"kennismaking", "bedankt voor je sollicitatie", plus the ATS senders "recruitee.com",
"personio", "no-reply@".

For each reply, give me ONE line in exactly this format:

    Company | outcome | short note

where outcome is one of: interview, rejected, ghosted, offer, withdrawn, acknowledged
  - "acknowledged" = automated "we received your application", nothing more
  - "rejected"     = an actual no
  - "interview"    = they proposed a call or meeting
Use the company name as the employer writes it. Keep the note under 15 words.

Rules:
- Do NOT reply to anything, do NOT delete or archive anything. Read only.
- If a message is ambiguous, put it in a separate "UNCLEAR" list rather than guessing.
- Also flag separately: anything sent to Hisham123@hotmail.com (note the different
  spelling) — a handful of February applications used that wrong address by mistake.
- Do not include anything that isn't a job-application reply.

Output the whole thing as one plain-text block I can copy in one go.
```

Then in the `~/Agents` repo: save that block as `replies.txt` and run

    python3 scripts/outcomes.py import replies.txt
    python3 scripts/outcomes.py report

That turns six months of invisible responses into the first real conversion data.

---

## JOB 2 — Work the manual apply queue

28 live roles that the automated path deliberately will not submit: captcha-gated careers
forms, Personio custom questions, and roles where a required question needs Hisham's own
words. `data/apply-queue.md` has, per role: the URL, the tailored cover letter, and the
answers already worked out from the profile.

```
Open ~/Agents/data/apply-queue.md (I'll paste it if you can't read files). Work through the
roles one at a time, top to bottom. For each one:

1. Open the URL in a new tab.
2. Fill the application form using ONLY:
   - CV: ~/Agents/profile/Hisham Abboud CV.pdf
   - Name: Hisham Abboud | Email: hiaham123@hotmail.com | Phone: +31648412838
   - Location: Eindhoven, Netherlands
   - Cover letter: the exact text in the "Cover letter" block for that role
   - The "Pre-computed answers" listed for that role — use them verbatim
3. Anything under "NEEDS YOUR OWN ANSWER": STOP and ask me. Do not compose an answer for
   me, and do not skip the field. I'll dictate it and you type what I say.
4. Show me the completed form and WAIT for my confirmation before submitting. Never submit
   without me looking at it.
5. If there's a CAPTCHA or "verify you're human", hand control back to me — I'll clear it.
6. After submitting, tell me the confirmation text you saw (or that there wasn't one), and
   move to the next role.

Hard rules:
- Never invent experience, skills, dates, a photo, or a reference. If the form wants
  something not in my CV or profile, ask me.
- Salary is EUR 4800 gross/month and notice is 1 month. Use exactly those; never a range
  you made up, never a different number.
- Never tick a consent for a background check / VOG / screening on my behalf — ask me.
- Never agree to a marketing or talent-pool opt-in. Privacy-policy consent needed to
  submit the application is fine.
- Do not apply to anything not in the queue file, even if it looks like a good match.

Keep a running list of which ones you submitted so I can log them afterwards.
```

Afterwards, record each submission so the caps and dedup stay correct:

    python3 scripts/outcomes.py log "<Company>" --outcome acknowledged --note "manual apply via Chrome"

---

## JOB 3 — Answer the questions that are blocking 21 applications

These are the real bottleneck now — not discovery. Most are short. Doing them once unblocks
those applications permanently, because recurring answers get stored in
`profile/answers.md` and reused forever.

```
I need to answer some job-application screening questions in my own words. Interview me —
ask me each one, let me answer conversationally, then write my answer back concisely in my
voice. Do not embellish, and do not add any experience I didn't state.

The questions (from ~/Agents/data/apply-queue.md):

FACTS I need to confirm once:
- Date of birth
- Do I have a valid driver's licence?
- Do I have a GitHub profile? (if yes, the URL)
- How many years of professional experience do I count?
- Am I open to relocating to the Eindhoven area / near Groningen? Am I willing to commute
  to Leuven, Belgium?

FREE TEXT, needs my own words:
- "Beschrijf een moment waarop data leidde tot een andere beslissing dan vooraf werd
  verwacht. Wat was jouw rol?"
- "Beschrijf een situatie waarin je zelf actief mensen hebt opgezocht om een vraagstuk
  verder te brengen."
- "Als je morgen bij Greenchoice start, welk vraagstuk rondom klantgedrag of
  energieverbruik zou je als eerste willen onderzoeken?"
- "Do you have hands-on programming experience through professional work, university
  coursework/projects, or internships?"
- "Do you have at least 2 years of experience in an SRE, DevOps or Systems Engineering
  role?"

For each: ask, listen, write it back in 2-4 sentences in my voice, and let me correct it.
At the end, output all the answers as one block I can paste into a file.
```

The factual answers go into `profile/answers.md` (they'll then be filled automatically on
every future application). The free-text ones are per-company and go straight into those
forms.

---

## JOB 4 (optional) — LinkedIn, and an honest warning about it

**Read the caveat before doing this one.** LinkedIn's User Agreement prohibits automated
access, and automating a logged-in account risks having that account restricted. This
pipeline deliberately only reads LinkedIn's **logged-out public** job pages and never
touches the account. That's why it has never been asked to do Easy Apply.

So: do **not** point Claude in Chrome at bulk LinkedIn scraping or automated Easy Apply.
The account being restricted would cost the top of the discovery funnel to save minutes at
the bottom — a bad trade.

What *is* reasonable is using it the way a person uses their own browser, with Hisham
driving and reading along:

```
I'm on LinkedIn, logged in as myself. Help me review — I'll drive, you read and summarise.

1. Open my messages/InMail and tell me if any recruiter has replied and I've missed it.
   Format any that are real replies as: Company | outcome | note   (same format as my
   email harvest, so I can log them the same way.)
2. Open my notifications and flag anything from a company I've applied to.
3. When I open a job posting, summarise it against my profile: my stack is .NET/C#, Azure,
   SQL, Python, testing/QA; I have ~2-3 years' experience; I'm in Eindhoven; I want
   €4800/month. Tell me honestly whether it's a fit and where the gaps are.

Don't apply to anything, don't send messages, don't connect with anyone, and don't page
through search results in bulk. I'm just reading with you.
```

If you want more discovery volume, the pipeline is the right tool — it reads only the
public logged-out pages, which is the part that's actually permitted.

---

## What NOT to ask Claude in Chrome to do

- Solve a CAPTCHA, or work around a "verify you're human" check. Hand those back to Hisham.
- Automate LinkedIn Easy Apply or bulk-scrape any logged-in account.
- Apply to roles not in the queue file — the queue has already passed the blocklist,
  the 2-per-employer cap, the seniority bar and the discipline check. Applying outside it
  bypasses guards that exist because each one caught a real mistake.
- Invent an answer to anything. If it isn't in the CV or `profile/preferences.md`, ask.
