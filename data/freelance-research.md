# Freelance / ZZP market research — 2026-07-29

## CORRECTION (same day, after further research)

An earlier version of this file concluded freelance was "not viable for this profile."
**That conclusion was wrong — it over-generalised from a government-heavy, senior-skewed
sample.** Correction below; the original findings are kept because they are still true of
the slice they came from.

What actually holds:
- **Wet DBA is real but NOT universal.** ZZPdock lists **351 current ZZP IT assignments**
  (updated daily). Of 42 software-relevant ones inspected, **28 are explicitly marked
  "ZZP: Toegestaan"**. The blanket "ZZP excluded" finding came from sampling de Publieke
  Partner / it-contracts, which skew to detachering-only public tenders.
- **The experience floor is the more binding constraint, and it is also not universal.**
  Several open ZZP-permitted assignments state no hard years knockout on the listing.
- **Best source found: zzpdock.nl** — free, public, no login, aggregates across brokers,
  de-duplicates, and exposes a structured `ZZP: Toegestaan / -` field plus rate, client,
  location and closing date. This is the source a freelance pipeline should be built on.

See `## Shortlist` at the end for concrete currently-open assignments.

---

## Original findings (accurate for the public-sector tender slice)

Two structural blockers, both verified firsthand (not just via search results).

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
| **Striive** | ~~Titles only~~ → **CORRECTED: fully public** | See correction table below. |

### CORRECTION to the table above — several entries were wrong

Verified by direct fetch 2026-07-29:

| Platform | Corrected finding |
|---|---|
| **Striive** | **`striive.com/nl/opdrachten` is fully public — no login.** Counter reads "Alle (122)", server-rendered, with named clients (IND, Belastingdienst, MinJenV, DICTU, Logius, ICTU, SVB, Rabobank, Shell, Alliander). The *SEO landing pages* (`/nl/zzp/opdrachten/ict`) ARE gated — that is what caused the earlier "titles only" error. Do not let a scraper conclude Striive is gated. Page is ~22 MB (base64 logos); strip script/style before parsing. |
| **Randstad Freelance** (ex-Yacht) | **`randstad.talent-pool.com/projects` public — "Toon 1–6 uit 7117 resultaten"**, verified. Exposes rate bands (€72,50–€107,50/uur) in list view. |
| **Gemeenteprojecten** | `gemeenteprojecten.talent-pool.com` — public, same white-label engine as Randstad, so one parser covers both. €8/uur platform fee paid by the municipality, not the freelancer. Requires eenmanszaak or BV-with-DGA; VOF/stichting excluded. |
| **Inhuurdesk** | `inhuurdesk.nl/aanvragen/` public with max rates. Bidding happens on Striive (same group). |
| **Circle8** | Client portals `np.circle8.nl/dynamic` (Politie), `rijkswaterstaat.circle8.nl/dynamic` are public **and expose an explicit "geschikt voor ZZP" / "niet geschikt voor ZZP" flag** — the single cleanest eligibility signal found anywhere. |
| **Flextender** | `app.flextender.nl/nologin/jobtopdf/<id>` returns the full assignment PDF **with no login** (path is literally named `nologin`). |
| **TenderNed** | JSON API responds unauthenticated. Keyword search is fuzzy — filter client-side. |

**Consolidation — four platforms no longer exist independently:** Between → redirects to Striive · FastFlex → HeadFirst · Brainnet → Magnit · Yacht Freelance → Randstad talent-pool. HeadFirst Group owns Striive, Between, FastFlex, Inhuurdesk, StarApple and others, so several "different" sources are one company.

**Benchmark ZZP ICT rates (Freelance.nl, 2024):** junior €65–78 · medior €82–92 · senior €95–110/uur.
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

## Shortlist — currently open, ZZP-permitted, from zzpdock.nl (as of 2026-07-29)

Scanned 16 public ZZPdock category slices → 215 unique assignments → 42 software-relevant →
28 marked "ZZP: Toegestaan". Best matches for this profile, senior-titled and non-dev removed:

**Closest stack fit**
| Role | Client | Rate | Closes | Link |
|---|---|---|---|---|
| Azure Specialist IaC / **.NET ontwikkelaar** — C#, Visual Studio, Bicep, Azure DevOps CI/CD, scrum | Hogeschool Arnhem/Nijmegen (HAN) | — | 7 Aug | https://zzpdock.nl/opdracht/ffc024ee-320d-4401-9c57-86548099ca0a/azure-specialist-infrastructure-as-code-net-ontwikkelaar |
| Backend Developer | Logius | — | 5 Aug | https://zzpdock.nl/opdracht/f53e8748-23eb-496f-937f-b5a469a0077f/backend-developer |
| Software Development Engineer | — (Den Haag) | — | 11 Aug | https://zzpdock.nl/opdracht/7af5829c-716c-40ac-9c48-b21fc6c16f9a/software-development-engineer |
| AWS Cloud Engineer | — (Den Haag) | — | 22 Sep | https://zzpdock.nl/opdracht/d95e4ede-d9b9-491b-9d0b-446b2b7c57dc/aws-cloud-engineer |

**Also open, ZZP-permitted (adjacent stack or higher bar)**
| Role | Client | Rate | Closes |
|---|---|---|---|
| Specialist/programmeur Allegro – cluster MO | Gemeente Rotterdam | max €103/hr | 4 Aug |
| Specialist/programmeur Allegro | Gemeente Rotterdam | max €92.70/hr | 4 Aug |
| DevOps engineer Elasticsearch – iHP | Nationale Politie (Utrecht) | max €108/hr | 3–4 Aug |
| Senior Software Engineer (shortlist) | — | €85–90/hr | — |
| Fullstack Java Developer | ICTU | — | 5 Aug |
| Java / Angular Developer (×3) | ICTU / — | — | 2–4 Aug |
| Senior (Mobile) QA/Test Automation Engineer | ICTU | — | 2 Aug |
| Freelance MS Teams engineer (2 yrs stated — lowest bar found) | — | — | — |
| Fullstack Developer (5 yrs TS/React stated) | Nederlandse Spoorwegen | max €100/hr | 5 Aug |

### Caveats — do not treat this as pre-qualified
- Mostly government / semi-government via brokers. ZZPdock aggregates; **applying goes through
  the originating broker**, which may require its own registration.
- "No years stated" means the ZZPdock listing shows no hard knockout — **the broker's full tender
  document may still impose one**. Verify before investing effort.
- Conflicting data seen between sources: the NS Fullstack role is "ZZP Toegestaan" on ZZPdock but
  was reported detachering-only on de Publieke Partner. Check the originating broker.
- Rate must be quoted by the user — never auto-generated.

## Recommendation

Freelance is **worth pursuing**, contrary to the earlier conclusion in this file — but as a
manual, deadline-driven process, not an auto-apply pipeline. Deadlines cluster 2–11 Aug 2026.

1. Start with the HAN .NET/Azure assignment — closest match to the actual stack.
2. Build a poller on **zzpdock.nl** (public, no login, daily-updated, structured ZZP field) rather
   than the government tender sites.
3. Registering free on **Striive** would materially widen visibility (claims 20.000+ assignments,
   all detail hidden publicly).
4. The permanent-role pipeline (332 applications, 276 companies) still runs in parallel — these
   are not mutually exclusive.
