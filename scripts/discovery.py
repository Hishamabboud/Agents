#!/usr/bin/env python3
"""ATS tenant discovery — multi-variant slug resolution with a collision guard.

WHY
---
Measured against 244 companies already confirmed to use Recruitee, the old single-slug
guess would only have rediscovered 202 of them (83%) on a cold sweep. Slugs frequently
do not follow from the display name:
    adesso Netherlands  -> werkenbijadesso
    IXON Cloud          -> ixonbv
    KUBUS / BIMcollab   -> bimcollab
    Xebia (via Xccelerated) -> xccelerated
Trying several variants lifts that to 91%. LinkedIn's logged-out job pages do NOT expose
the real apply URL (checked), so variant generation is the best available approach.

COLLISION GUARD
---------------
Generic slugs collide: probing "salesforce" or "share" or "change" returns *a* tenant,
but not necessarily the company we were looking for. Every hit is checked against the
tenant's own reported company name before being accepted.
"""

import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

H = {"User-Agent": "Mozilla/5.0"}

_STOP = (r"\b(b\.?v\.?|n\.?v\.?|gmbh|ag|se|kg|mbh|co|deutschland|germany|nederland|"
         r"netherlands|belgium|belgie|group|holding|inc|ltd|llc|the|international|"
         r"solutions|technologies|technology|consultancy|services|cloud|security|"
         r"benelux|center|centre|software|digital|labs|studio)\b")


def slug_variants(name):
    """Candidate slugs for a company display name, most-likely first."""
    # LinkedIn reports display names, not legal names, and they often carry a tagline:
    # "Ireckonu - Hotel Middleware & CDP+", "UbiOps - Private AI on any infra". The tagline
    # is never part of the slug, and leaving it in produced junk variants that then made the
    # collision guard reject the company's own real tenant.
    base = re.split(r"\s[-\u2013\u2014]\s", name.lower().split("|")[0])[0]
    base = base.split("/")[0].split("(")[0].strip()
    words = re.findall(r"[a-z0-9]+", base)
    out = []

    def add(s, allow_short=False):
        # 2-char slugs are real (EY, KP, G4) but only when they ARE the whole name,
        # otherwise short fragments generate noise.
        if s and s not in out and (len(s) >= 3 or allow_short):
            out.append(s)

    add(re.sub(r"[^a-z0-9]", "", re.sub(_STOP, "", base)))   # suffixes stripped
    add(re.sub(r"[^a-z0-9]", "", base))                       # full, unstripped
    if words:
        add(words[0], allow_short=(len(words[0]) == len(re.sub(r"[^a-z0-9]", "", base))))
    if len(words) >= 2:
        add(words[0] + words[1])                              # first two words
        add(words[0] + "-" + words[1])
    # common Dutch/Belgian career-site prefixes
    if words:
        add("werkenbij" + words[0])
        add("jobs" + words[0])
        add("careers" + words[0])
    return out


def _name_matches(company, tenant_name):
    """Guard against generic-slug collisions (salesforce, share, change, ...)."""
    if not tenant_name:
        return True          # tenant didn't report a name; accept but caller should verify
    a = re.sub(r"[^a-z0-9]", "", company.lower())
    b = re.sub(r"[^a-z0-9]", "", tenant_name.lower())
    if not a or not b:
        return True
    # accept if either contains the other, or they share a long prefix
    return a in b or b in a or a[:6] == b[:6]


def probe_recruitee(company, variants=None):
    """Return (slug, offers) for the first variant that resolves to THIS company."""
    for s in (variants or slug_variants(company)):
        try:
            r = requests.get(f"https://{s}.recruitee.com/api/offers/", headers=H, timeout=8)
            if r.status_code != 200:
                continue
            offers = r.json().get("offers", [])
            if not offers:
                continue
            tenant_name = (offers[0].get("company_name")
                           or offers[0].get("careers_company_name") or "")
            if not _name_matches(company, tenant_name):
                continue
            return s, offers
        except Exception:
            continue
    return None, None


def _strong_variants(name):
    """Variants derived from the COMPLETE company name, not a fragment of it.

    Used as evidence that a tenant slug really belongs to this company. A first-word-only
    slug is excluded unless that word is the entire name.
    """
    base = re.split(r"\s[-\u2013\u2014]\s", name.lower().split("|")[0])[0]
    words = re.findall(r"[a-z0-9]+", base)
    stripped = re.sub(r"[^a-z0-9]", "", re.sub(_STOP, "", base))
    strong = set(slug_variants(name)[:2])    # suffix-stripped full, and full unstripped
    # A bare first word is weak evidence ("royal" -> Royal Kaak?), UNLESS stripping the
    # legal/geographic suffixes leaves exactly that word — "Everience Benelux" reduces to
    # "everience", which is the company's whole meaningful name, not a fragment of it.
    if len(words) > 1 and words[0] != stripped:
        strong.discard(words[0])
    return strong


_TITLE_PREFIX = re.compile(
    r"^\s*(?:jobs|banen|vacatures|trabajos|empleos|emplois|karriere|karriär|lavori|praca|"
    r"stillinger|careers?|werken)\b[^a-z0-9]*\b(?:at|bei|bij|en|chez|hos|w|przy|presso)?\b\s*",
    re.I)
_LEGAL = re.compile(r"\b(gmbh|mbh|ag|se|kg|ug|bv|nv|slu|sl|srl|sarl|sa|spa|oy|ab|as|aps|plc|"
                    r"inc|ltd|llc|e\.?v|co|kgaa|holding|group|germany|deutschland|nederland|"
                    r"netherlands|belgium|belgie|benelux|international|the)\b", re.I)


def _tenant_name_from_page(page):
    """Personio renders the tenant's real name in the page title, in the tenant's own
    language: 'Jobs at IRECKONU', 'Jobs bei Scalian Germany AG', 'Banen bij Twelve',
    'Trabajos en HMS INDUSTRIAL NETWORKS, SLU'. This is the closest thing Personio has to
    Recruitee's company_name field, and it is far more reliable than looking for the
    company's words somewhere in the page body."""
    m = re.search(r"<title>([^<]*)", page, re.I)
    if not m:
        return ""
    return _TITLE_PREFIX.sub("", m.group(1)).strip()


def _display_base(name):
    """Strip the tagline LinkedIn appends to display names before comparing."""
    base = re.split(r"\s[-\u2013\u2014]\s", (name or "").lower().split("|")[0])[0]
    return base.split("/")[0].split("(")[0].strip()


def _tokens(name):
    return {w for w in re.findall(r"[a-z0-9]{2,}", _LEGAL.sub(" ", _display_base(name)))
            if w not in ("for", "and", "van", "der", "den", "und", "met", "on", "any")}


def _personio_tenant_matches(company, host, xml, page=None):
    """Collision guard for Personio. Pass `page` to test without network access.

    Personio's XML feed carries no company-name field, so a generic slug resolves happily
    to an unrelated tenant. Measured on round 30, probing by name alone claimed:
        Royal Kaak / Royal Houdijk -> `royal`   = Personio's "Demo Datos" sample tenant
        Atlas Copco                -> `atlas`   = Atlas-Bildungs-Center e.V.
        Code for Good              -> `code`    = CODE Education GmbH
        KBC Bank & Verzekering     -> `kbc`     = Kemeny Boehme Consultants SE
    All four would have sent an application to a company that was never searched for.
    """
    if page is None:
        try:
            page = requests.get(f"https://{host}/", headers=H, timeout=10).text
        except Exception:
            return False
    low = page.lower()

    # Personio sample tenants are set up but never populated and answer to short slugs.
    if re.search(r"<title>[^<]*\bdemo\b", low) or "demo datos" in low or "demo data" in low:
        return False

    tenant = _tenant_name_from_page(page)
    if tenant:
        a, b = _tokens(company), _tokens(tenant)
        if not a or not b:
            return False
        # Every meaningful word of the shorter name must appear in the longer one.
        # "HMS Networks" vs "HMS INDUSTRIAL NETWORKS, SLU" passes; "Code for Good" vs
        # "CODE Education GmbH" does not, despite sharing a lead word.
        short, long_ = (a, b) if len(a) <= len(b) else (b, a)
        if not short <= long_:
            return False
        # A single shared word is only enough when it is the WHOLE of both names. The
        # `vivid` tenant is titled just "Vivid" — Vivid Money, a Berlin fintech — and a
        # subset test alone accepted it as "Vivid Resourcing".
        return len(short) >= 2 or len(long_) == 1

    # No name in the title (some tenants render it client-side). Fall back to requiring the
    # slug to be derived from the COMPLETE company name — Avisi -> avisi is acceptable,
    # Open Home Foundation -> `open` is not.
    return host.split(".")[0] in _strong_variants(company)


def probe_personio(company, variants=None):
    """Return (host, raw_xml) for the first variant with a real (non-demo) board."""
    from filters import parse_personio_positions
    for s in (variants or slug_variants(company)):
        for host in (f"{s}.jobs.personio.de", f"{s}.jobs.personio.com"):
            try:
                r = requests.get(f"https://{host}/xml", headers=H, timeout=8)
                # Personio serves UTF-8 but often omits the charset, and requests then
                # falls back to latin-1 - which renders an em-dash as "a" + junk in the
                # job title that goes on to the tracker and the cover letter.
                r.encoding = "utf-8"
                if r.status_code == 200 and "<position>" in r.text:
                    if not parse_personio_positions(r.text):   # demo/empty board
                        continue
                    if not _personio_tenant_matches(company, host, r.text):
                        continue
                    return host, r.text
            except Exception:
                continue
    return None, None


def probe_company(company):
    """Probe one company across both ATSs. Returns dict or None."""
    v = slug_variants(company)
    slug, offers = probe_recruitee(company, v)
    host, xml = probe_personio(company, v)
    if not slug and not host:
        return None
    return {"company": company, "recruitee_slug": slug, "recruitee_offers": offers,
            "personio_host": host, "personio_xml": xml, "variants_tried": v}


def probe_many(companies, workers=25, progress=True):
    hits = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(probe_company, c): c for c in companies}
        done = 0
        for f in as_completed(futs):
            done += 1
            r = f.result()
            if r:
                hits.append(r)
                if progress:
                    tag = []
                    if r["recruitee_slug"]:
                        tag.append(f"Recruitee:{r['recruitee_slug']}({len(r['recruitee_offers'])})")
                    if r["personio_host"]:
                        tag.append(f"Personio:{r['personio_host'].split('.')[0]}")
                    print(f"[HIT {len(hits)}] {r['company'][:32]:32s} {' + '.join(tag)}", flush=True)
            if progress and done % 150 == 0:
                print(f"...{done}/{len(companies)}", flush=True)
    return hits


if __name__ == "__main__":
    for n in ["adesso Netherlands", "IXON Cloud", "KUBUS / BIMcollab",
              "Xebia (via Xccelerated)", "Funda Real Estate B.V."]:
        print(f"{n:28s} -> {slug_variants(n)}")
