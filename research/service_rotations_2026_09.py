"""
Researched port rotations for the highest-frequency named services
currently seen in vessel_schedule, gathered via public web search on
2026-09-11 (see pipeline/rotations.py and models.ServiceRotation for how
this data is used and what the confidence levels mean).

This is a PILOT batch, not exhaustive coverage -- see
docs/service_rotations_research_notes.md for what's covered, what isn't,
and the specific failure modes hit while researching this (multi-variant
service codes, carrier renames, and one clearly unreliable/conflated
search result). Re-run `seed_service_rotations.py` after adding more
entries here; it upserts by (shipping_line, service), so re-running is
always safe.

Each port dict: {"port": str, "country": str}. `jnpt_index` is computed
automatically at seed time by matching a port name against JNPT_ALIASES
below -- don't hand-set it here.
"""

ADHOC_LINES = [
    # (shipping_line, service) pairs currently in vessel_schedule where the
    # service itself is "ADHOC" -- a JNPT-side label meaning an unscheduled,
    # one-off call, not a named loop. There is genuinely no fixed rotation
    # to research for these; confidence="no_fixed_rotation" says so
    # explicitly rather than leaving them looking un-researched.
    "ESA", "UNF", "EMS", "MSK", "KIN", "EMT", "RGS", "SBB", "WAN", "RCL", "TNS",
]

ROTATIONS = [
    {
        "shipping_line": "MSC",
        "service": "INDUSA",
        "ports": [
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Valencia", "country": "Spain"},
            {"port": "New York", "country": "USA"},
            {"port": "Savannah", "country": "USA"},
            {"port": "Norfolk", "country": "USA"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.itln.in/msc-launches-new-indiaus-service-indusa-revises-indus-express-shipping",
        "notes": "Source dated Aug 2020 -- MSC has since made several port-skip changes on "
                 "India-touching services generally (per other search hits found the same day). "
                 "Confirm against a current MSC advisory before relying on this.",
    },
    {
        # Flexport Atlas confirmed this service runs as two directional legs
        # (EASTBOUND Fujairah->Nhava Sheva, WESTBOUND Nhava Sheva->Fujairah)
        # rather than one symmetric loop -- see models.ServiceRotation's
        # docstring for why that means two rows, not one.
        "shipping_line": "CCA", "service": "BIGEX", "direction": "eastbound",
        "ports": [
            {"port": "Fujairah", "country": "UAE"},
            {"port": "Sohar", "country": "Oman"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.cma-cgm.com/news/4997/cma-cgm-to-strengthen-its-bigex-lines-network-connecting-the-indian-subcontinent-gulf-amp-red-sea",
        "notes": "CMA CGM runs MULTIPLE named BIGEX variants (BIGEX 1/2/3/4), each a different "
                 "rotation -- vessel_schedule's plain 'BIGEX' label doesn't say which one. Port "
                 "SET is reasonably confident (Flexport Atlas); this eastbound CALL ORDER "
                 "within that set is a guess, not confirmed -- treat with real caution.",
    },
    {
        "shipping_line": "CCA", "service": "BIGEX", "direction": "westbound",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Sohar", "country": "Oman"},
            {"port": "Fujairah", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.cma-cgm.com/news/4997/cma-cgm-to-strengthen-its-bigex-lines-network-connecting-the-indian-subcontinent-gulf-amp-red-sea",
        "notes": "Westbound leg of the same service as the eastbound entry above -- assumed to "
                 "be the reverse of the eastbound port SET (confirmed) in the same guessed order "
                 "(not confirmed). Same BIGEX-1/2/3/4 variant-ambiguity caveat applies.",
    },
    {
        "shipping_line": "MAE",
        "service": "FI2",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Nansha", "country": "China"},
            {"port": "Tanjung Pelepas", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Pipavav", "country": "India"},
            {"port": "Port Qasim", "country": "Pakistan"},
        ],
        "confidence": "verified",
        "source_url": "https://www.maersk.com/news/articles/2026/05/26/maersk-fi2-ocean-service-india-china-connectivity",
        "notes": "Maersk's own launch announcement, May 2026 -- a genuinely new service, "
                 "so this is current as of research date.",
    },
    {
        "shipping_line": "MSK",
        "service": "MECL",
        "ports": [
            {"port": "Charleston", "country": "USA"},
            {"port": "Savannah", "country": "USA"},
            {"port": "Houston", "country": "USA"},
            {"port": "Norfolk", "country": "USA"},
            {"port": "Newark", "country": "USA"},
            {"port": "Tangiers", "country": "Morocco"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Salalah", "country": "Oman"},
            {"port": "Mundra", "country": "India"},
            {"port": "Pipavav", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
        ],
        "confidence": "verified",
        "source_url": "https://www.maersk.com/news/articles/2026/07/09/structural-changes-to-mecl",
        "notes": "Maersk's own July 2026 announcement of the Aug 2026 rotation (return to "
                 "trans-Suez via a new Jeddah call) -- the most current structural change found.",
    },
    {
        "shipping_line": "HLI",
        "service": "TPI",
        "ports": [
            {"port": "Port Qasim", "country": "Pakistan"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "New York", "country": "USA"},
            {"port": "Norfolk", "country": "USA"},
            {"port": "Savannah", "country": "USA"},
            {"port": "Charleston", "country": "USA"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.hapag-lloyd.com/en/services-information/news/2024/06/shipping-with-our-indamex--tpi--service--here-s-an-update-.html",
        "notes": "Hapag-Lloyd's own page, but from June 2024 -- over a year old relative to "
                 "research date; a Jan 2026 Hapag-Lloyd operational update exists that wasn't "
                 "checked for whether it changed this rotation. Also branded 'INDAMEX' by "
                 "Hapag-Lloyd -- NOT the same service as CCA's own, differently-owned 'INDAMEX'.",
    },
    {
        "shipping_line": "WHI",
        "service": "CI2",
        "ports": [
            {"port": "Tuticorin", "country": "India"},
            {"port": "Penang", "country": "Malaysia"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Hong Kong", "country": "China"},
            {"port": "Qingdao", "country": "China"},
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.xindemarinenews.com/m/view.php?aid=9149",
        "notes": "Intra-Asia consortium service (Wan Hai + Interasia Lines + COSCO) -- Port "
                 "Klang appears twice in the source description, which may be a genuine "
                 "double-call or a synthesis artifact. Order not independently confirmed.",
    },
    {
        "shipping_line": "COS",
        "service": "AGI2",
        "ports": [],
        "confidence": "unresolved",
        "source_url": "https://www.linerlytica.com/post/cosco-oocl-launch-asia-gulf-india-2-agi2/",
        "notes": "CONFLICTING info found: AGI2 as originally launched (Aug 2022) was Singapore-"
                 "Mundra-Abu Dhabi-Hamad-Khalifa bin Salman-Abu Dhabi-Singapore -- no Nhava "
                 "Sheva call at all. A search result also claims AGI2 was replaced by a "
                 "'UIG2' service (from Nov 2023) that DOES call Nhava Sheva. But BMCT's live "
                 "report (checked 2026-09-11) still labels a real, currently-arriving vessel's "
                 "service as plain 'AGI2' -- terminal-side labels often lag a carrier's own "
                 "renames. Left unresolved rather than guessing which rotation actually applies "
                 "to today's 'AGI2' label.",
    },
    {
        "shipping_line": "ONE",
        "service": "PS3",
        "ports": [],
        "confidence": "unresolved",
        "source_url": None,
        "notes": "Search returned an implausible 14-port rotation spanning India, Southeast "
                 "Asia, East Asia AND the US West Coast in one loop (Nhava Sheva-Pipavav-"
                 "Singapore-Cai Mep-Yantian-LA/Long Beach-Oakland-Tokyo-Busan-Shanghai-Ningbo-"
                 "Shekou-Singapore-Port Klang-Nhava Sheva) -- almost certainly a conflation of "
                 "multiple distinct ONE services by the search summary, not one real rotation. "
                 "Discarded rather than recorded as anything -- this is the clearest example "
                 "hit of why every result here needs a skeptical read, not just a search hit.",
    },
]
