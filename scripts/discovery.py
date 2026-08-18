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
    base = name.lower().split("|")[0].split("/")[0].split("(")[0].strip()
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


def probe_personio(company, variants=None):
    """Return (host, raw_xml) for the first variant with a real (non-demo) board."""
    from filters import parse_personio_positions
    for s in (variants or slug_variants(company)):
        for host in (f"{s}.jobs.personio.de", f"{s}.jobs.personio.com"):
            try:
                r = requests.get(f"https://{host}/xml", headers=H, timeout=8)
                if r.status_code == 200 and "<position>" in r.text:
                    if parse_personio_positions(r.text):   # skips demo/empty boards
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
