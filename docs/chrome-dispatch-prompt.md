# Single dispatch prompt — Claude in Chrome

One self-contained block. Paste it into a Claude in Chrome session and it will run the
whole session, asking for what it needs. It assumes NO access to the `~/Agents` files, so
it asks you to paste the queue when it gets to that stage.

---

```
You're helping me (Hisham Abboud) with my job search, in my browser, with me present. I'll
be here the whole time — ask me whenever you're unsure. You can't read my local files, so
ask me to paste anything you need.

WHO I AM (use only this; never add to it)
  Hisham Abboud | hiaham123@hotmail.com | +31 6 48412838 | Eindhoven, Netherlands
  BSc Software Engineering, Fontys University of Applied Sciences, Eindhoven
  Stack: .NET/C#, Azure, SQL, Python, JavaScript, testing/QA. ~2-3 years' experience.
  Languages: English fluent, Dutch fluent, Arabic fluent.
  Work authorisation: I can work in NL, I need no visa sponsorship.
  Salary expectation: EUR 4800 gross/month. Notice period: 1 month. Full-time, 40h.
  CV file: "Hisham Abboud CV.pdf" — I'll upload it when a form asks.

HARD RULES (these matter more than finishing fast)
  - Never invent experience, skills, dates, a photo, a reference, or a GitHub link. If a
    form wants something not listed above, STOP and ask me.
  - Salary is exactly EUR 4800/month and notice exactly 1 month. Never a range you made up.
  - Never tick a consent for a background check, VOG, or screening on my behalf — ask me.
    Ticking "I accept the privacy policy" in order to submit is fine.
  - Never opt me into a newsletter or talent pool.
  - If you hit a CAPTCHA or "verify you're human", hand control back to me. Don't work
    around it.
  - Show me every completed form and WAIT for my go-ahead before submitting. Never submit
    on your own initiative.
  - Don't apply to any role I haven't given you.

DO THESE IN ORDER. Finish one, show me the result, then start the next.

── TASK 1: find six months of employer replies (do this first, it's the most valuable) ──
I've sent ~643 applications since 24 February 2026 and have systematically read almost
none of the replies. They're in my inbox at hiaham123@hotmail.com.

Search my mail — inbox, Spam/Junk, and any Promotions/Other tabs — using terms like:
  sollicitatie, vacature, application, "uw sollicitatie", helaas, afwijzing,
  unfortunately, interview, gesprek, kennismaking, recruitee.com, personio, no-reply@

Give me every employer reply as ONE line, exactly this format:

    Company | outcome | short note

outcome must be one of: interview, rejected, ghosted, offer, withdrawn, acknowledged
  acknowledged = automated "we received your application", nothing more
  rejected     = an actual no
  interview    = they proposed a call or meeting
Company name as the employer writes it. Note under 15 words.

Also:
  - Put anything ambiguous in a separate "UNCLEAR" list instead of guessing.
  - Separately flag anything addressed to Hisham123@hotmail.com (different spelling) —
    a few February applications used that wrong address.
  - Read only. Don't reply, delete, archive, or mark anything.
Output it as one plain-text block I can copy in a single go.

── TASK 2: fill in the answers that are blocking applications ──
Interview me for these. Ask one at a time, let me answer conversationally, then write my
answer back in 2-4 sentences in my own voice. Don't embellish and don't add anything I
didn't say. Let me correct each one.

Facts to confirm once:
  - my date of birth
  - do I have a valid driver's licence?
  - do I have a GitHub profile, and its URL?
  - how many years of professional experience do I count?
  - am I open to relocating to the Eindhoven area? to near Groningen? willing to commute
    to Leuven, Belgium?

Free text, needs my own words:
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

At the end, output all answers as one block I can save.

── TASK 3: submit the queued applications ──
Ask me to paste my apply queue (it's a markdown file listing roles, each with a URL, a
cover letter, and pre-computed answers). Then work it top to bottom, one role at a time:

  1. Open the role's URL in a new tab.
  2. Fill the form using my details above, the exact cover letter text given for that role,
     and that role's listed pre-computed answers, verbatim.
  3. Where the queue says "NEEDS YOUR OWN ANSWER", use what I gave you in Task 2. If it
     isn't covered there, ask me — don't compose it and don't leave it blank.
  4. Upload my CV when asked.
  5. Show me the filled form. Wait for my go-ahead. Then submit.
  6. Tell me the confirmation message you saw, or that there wasn't one. Keep a running
     list of what you submitted so I can log it afterwards.

── TASK 4 (only if I ask): LinkedIn, read-only ──
I'm logged in as myself. LinkedIn's terms prohibit automated use of an account, so we stay
strictly within what I'd do by hand, with me driving:
  - check my messages/InMail for recruiter replies I've missed, and format any real ones
    in the same "Company | outcome | note" style as Task 1
  - check notifications for anything from a company I've applied to
  - when I open a job posting, tell me honestly whether it fits my profile above and where
    the gaps are
Do NOT apply to anything, send messages, connect with anyone, use Easy Apply, or page
through search results in bulk.

Start with Task 1.
```
