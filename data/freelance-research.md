# Freelance / ZZP market research — 2026-07-29

Investigated switching the pipeline from permanent roles to freelance/ZZP assignments.
**Conclusion: not viable for this profile right now.** Two structural blockers, both verified
firsthand (not just via search results).

## Blocker 1 — Wet DBA has closed direct ZZP contracting

Dutch public-sector and large-corporate interim assignments now overwhelmingly exclude
freelancers, routing through detachering (secondment) intermediaries instead.

Verified verbatim on the live listing at https://depubliekepartner.nl/senior-net-developer-7/
(Senior .NET developer, Ministerie van VWS, €97.50–107.50/hr, closing 03-08-2026):

> "Deze opdracht kan niet als ZZP'er worden uitgevoerd."

Same exclusion found across other clients, phrased differently:
- "Deze aanvraag leent zich er niet voor om door een ZZP'er uitgevoerd te worden" (Nationale Politie)
- "minder geschikt voor zzp'ers in verband met wet DBA" (Belastingdienst)
- "ZZP mogelijk: Nee" (Enexis)
- One posting required the candidate be "in loondienst bij Opdrachtnemer / Onderaannemer en geen ZZP'er"

Having a KVK/BTW registration does not help — the client has excluded the contract form itself.

## Blocker 2 — Seniority floor

Every open, relevant assignment found demanded 5–10 years. Verified verbatim on the same VWS listing:

> "Je hebt minimaal 5 jaar ervaring met ontwikkeling van .NET-applicaties."

Profile has ~1 year full-time (Actemium, since Jul 2025) plus two internships (ASML,
Delta Electronics). The €90–110/hr interim tier is out of reach on stated criteria.

Only junior-scoped opening surfaced anywhere: AI Adviseur *trainee*, Gemeente De Ronde Venen
(€80–95/hr, 0–2 years, closing 10-08-2026) — but it requires a **WO master's in Artificial
Intelligence**; profile has an HBO BSc from Fontys, so it fails the education criterion.

## Platform access map

| Platform | Browse without login? | Notes |
|---|---|---|
| **de Publieke Partner** | Yes — best public transparency | Shows status, rate, hours, start + closing dates. Apply via on-site form + CV, no account. Daily digest at predictable URL `/nieuwste-opdrachten/de-nieuwste-zzp-freelance-interim-opdrachten-DD-MM-YYYY/`. Overwhelmingly detachering. |
| **freelapp.nl** | Yes | Aggregator, shows deadlines + originating broker. Expired listings 404 (good freshness signal). |
| **it-contracts.nl** | Yes | Freshest source, items published same day. .NET + C# categories currently empty. |
| **zzpdock.nl** | Yes, free | Aggregator with vakgebied/location/tariff filters, de-duplicates across brokers. |
| **Hoofdkraan.nl** | List yes, details need account | Small-gig marketplace: WordPress/Squarespace/small sites, €50–1000 total or €25–40/hr. All .NET listings closed (newest national 04-12-2025; newest Eindhoven 12-02-2020). Not a fit. |
| **freep.nl** | Archive yes | Account needed to respond. Content stale. |
| **Freelance.nl** | Landing pages only | Actual assignments behind `mijn.freelance.nl` login. All four .NET category pages showed "Toon 0 resultaten". NB robots.txt explicitly allows ClaudeBot/Claude-User but disallows `User-agent: *` — use an honest UA, not spoofed Chrome. |
| **Striive** | Titles only | Rates/hours/deadlines hidden behind free account. Claims 20.000+ assignments; is the upstream source behind several de Publieke Partner listings. Highest-leverage registration. |
| **Flextender** | Broker | Government inhuur, robots permissive but listings load via admin-ajax; applying via app.flextender.nl login + DAS registration per contracting authority. |
| **Opdracht Overheid / Funle** | No | Forces login/register. |
| **Circle8** | Could not verify | HTTP 429 behind Vercel Security Checkpoint. Runs client-specific portals. |

## Why the auto-apply pipeline does not transfer

Unlike Recruitee's open submission API, freelance assignments require:
1. A platform login/account
2. **An hourly/day rate quote** — a commercial commitment that must come from the user, not be auto-generated
3. A tailored motivation per assignment

So freelance is inherently discover-and-shortlist, not auto-apply.

## Options if pursuing further

1. **Open up to detachering** rather than pure ZZP — unlocks most of the market, but is closer to
   contracting employment via an intermediary than true freelancing.
2. **Register free on Striive** — single highest-leverage action; hides all detail publicly.
3. **Poll de Publieke Partner's daily digest** — predictable URL, publicly readable, automatable.
4. **Revisit in 2–4 years** once the experience floor is cleared.

## Recommendation

The permanent-role pipeline (332 applications submitted, 276 companies) remains the far better
channel for this profile. Freelance is worth revisiting once experience passes the ~5-year mark,
or immediately if open to detachering rather than pure ZZP.
