"""
Researched port rotations for the named services seen in vessel_schedule,
gathered via public web search on 2026-09-11 (see pipeline/rotations.py
and models.ServiceRotation for how this data is used and what the
confidence levels mean).

Covers 74 of the 97 distinct (shipping_line, service) combinations
live in vessel_schedule as of that date -- see
docs/service_rotations_research_notes.md for exact coverage, the
confidence breakdown, and the specific failure modes hit while
researching this: multi-variant service codes (BIGEX/EPIC/MIDAS/CWX,
each run by their carrier as several differently-numbered loops, with
vessel_schedule's plain label not saying which), a carrier rename the
terminal's own label hadn't caught up to (COS/AGI2), a carrier-identity
guess (EGI) later corrected against JNPA's own official shipping-agency
registry (see seed_service_rotations.py's CARRIER_NAMES), consortium
loops shared across carrier brands (applied to more than one line only
where a source explicitly named the joint operators), and one discarded
hallucinated/conflated search result (ONE/PS3). Neither carrier sites
nor the one schedule aggregator tried (Flexport Atlas) allow automated
fetches (both 403), so every entry here comes from search-result
synthesis, not a direct primary-source read -- read `confidence`
accordingly.

Re-run `seed_service_rotations.py` after editing this file; it upserts
by (shipping_line, service, direction), so re-running is always safe.

Each port dict: {"port": str, "country": str}. `jnpt_index` is computed
automatically at seed time by matching a port name against JNPT_ALIASES
in seed_service_rotations.py -- don't hand-set it here.

DIRECTIONALITY: a few services here (BIGEX, GSL/NIX) run a genuinely
different port set/order eastbound vs westbound, not just each other's
reverse -- these get two entries with the same (shipping_line, service)
and different `direction`, both loaded as separate rows (see
models.ServiceRotation's own docstring). HMM's FIM-W is a case where
the JNPT label is direction-specific but the source only publishes one
84-day round trip that calls Nhava Sheva twice -- see its own notes for
why that couldn't be cleanly split. Most consortium/pendulum services
below (the RWA/CIX/CISC/SI8/CI6/VGI/CWX families) read as one
continuous cycle already, so direction="single" is correct for them --
the "eastbound" and "westbound" halves are just two arcs of the same
loop, both captured by recording the whole thing in call order.
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
    {
        "shipping_line": "SEC", "service": "RGI", "direction": "single",
        "ports": [
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Sokhna", "country": "Egypt"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Jebel Ali", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.linerlytica.com/post/x-press-feeders-feedertech-and-wan-hai-team-up-for-new/",
        "notes": "X-Press Feeders (SEC = Sea Consortium, X-Press's parent) / Feedertech / Wan Hai "
                 "joint service, also branded IRX / IM1 by partners. Pendulum shape (Jeddah and "
                 "Jebel Ali each visited twice) taken as described, not independently confirmed.",
    },
    {
        "shipping_line": "MSK", "service": "MESAWA", "direction": "single",
        "ports": [
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Pointe Noire", "country": "Congo"},
            {"port": "Tema", "country": "Ghana"},
            {"port": "Apapa", "country": "Nigeria"},
            {"port": "Cape Town", "country": "South Africa"},
            {"port": "Port Elizabeth", "country": "South Africa"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maersk.com/news/articles/2026/04/07/mesawa-temporary-service-adjustment-2026",
        "notes": "Found via a search for a different service (MWE) that surfaced this one instead -- "
                 "port set from search synthesis, not independently cross-checked.",
    },
    {
        "shipping_line": "MSK", "service": "MWE", "direction": "single", "ports": [],
        "confidence": "unresolved", "source_url": None,
        "notes": "No usable result found -- searches kept returning other Maersk services "
                 "(MECL, ME1, Mesawa) instead.",
    },
    {
        "shipping_line": "MSC", "service": "HEX", "direction": "single", "ports": [],
        "confidence": "unresolved", "source_url": None,
        "notes": "No usable result found -- searches returned unrelated MSC port-rotation-change "
                 "advisories (SAEC, EMUSA, Swan-Sentosa) instead.",
    },
    {
        "shipping_line": "CUL", "service": "IMR", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Djibouti", "country": "Djibouti"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Aden", "country": "Yemen"},
        ],
        "confidence": "verified",
        "source_url": "https://www.culines.com/en/site/details/611",
        "notes": "CU Lines' own site, joint operation with CStar and UGL.",
    },
    {
        "shipping_line": "CCA", "service": "INDAMEX", "direction": "single",
        "ports": [
            {"port": "Port Qasim", "country": "Pakistan"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "New York", "country": "USA"},
            {"port": "Norfolk", "country": "USA"},
            {"port": "Savannah", "country": "USA"},
            {"port": "Charleston", "country": "USA"},
        ],
        "confidence": "verified",
        "source_url": "https://www.cma-cgm.com/news/4753/cma-cgm-to-strengthen-its-indamex-service-connecting-indian-subcontinent-with-us-east-coast",
        "notes": "CMA CGM's own INDAMEX (distinct from Hapag-Lloyd's differently-owned "
                 "'INDAMEX'-branded TPI service -- same name, unrelated rotation, different line).",
    },
    {
        "shipping_line": "CCA", "service": "EPIC", "direction": "single",
        "ports": [
            {"port": "Mundra", "country": "India"},
            {"port": "King Abdullah Port", "country": "Saudi Arabia"},
            {"port": "Gioia Tauro", "country": "Italy"},
            {"port": "Tanger", "country": "Morocco"},
            {"port": "Southampton", "country": "UK"},
            {"port": "Rotterdam", "country": "Netherlands"},
            {"port": "Antwerp", "country": "Belgium"},
            {"port": "Felixstowe", "country": "UK"},
            {"port": "Dunkirk", "country": "France"},
            {"port": "Le Havre", "country": "France"},
            {"port": "King Abdullah Port", "country": "Saudi Arabia"},
            {"port": "Djibouti", "country": "Djibouti"},
            {"port": "Port Qasim", "country": "Pakistan"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.cma-cgm.com/news/1237/the-cma-cgm-group-optimizes-its-offer-towards-india-with-two-new-weekly-services-epic-1-and-epic-2",
        "notes": "This is specifically EPIC 1's rotation -- CMA CGM also runs an EPIC 2 with a "
                 "different (Europe-focused) rotation, and vessel_schedule's plain 'EPIC' label "
                 "doesn't say which. Used EPIC 1 since it's the one confirmed to call Nhava Sheva.",
    },
    {
        "shipping_line": "HLI", "service": "IG1", "direction": "single",
        "ports": [
            {"port": "Kandla", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Khorfakkan", "country": "UAE"},
            {"port": "Sohar", "country": "Oman"},
        ],
        "confidence": "verified",
        "source_url": "https://www.maritimegateway.com/hapag-lloyd-revises-india-gulf-service-1-rotation/",
        "notes": "Reinstated July 2026 after a temporary suspension -- current as of research date.",
    },
    {
        "shipping_line": "CCA", "service": "SWAX", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Khor Fakkan", "country": "UAE"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mombasa", "country": "Kenya"},
            {"port": "Dar Es Salaam", "country": "Tanzania"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.cma-cgm.com/local/india/news/981/swax-service-position-sliding",
        "notes": "CMA CGM's own site explicitly disclaims schedules as indicative/non-contractual.",
    },
    {
        # Consortium loop shared by RCL (native "RWA"/"RWA2" brand), PIL, and
        # ECL -- all three currently show up in vessel_schedule labeled "RWA".
        "shipping_line": "PIL", "service": "RWA", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Haiphong", "country": "Vietnam"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/rcl-upsizes-china-west-asia-rwa-2-service-to-india-with-7000-teu-vessel/",
        "notes": "This is RCL's own 'RWA2' variant specifically; PIL's own branding for its slot "
                 "on this consortium loop is actually 'CSE', not 'RWA' -- but vessel_schedule's "
                 "'PIL'+'RWA' combination implies the terminal logs PIL's slot under RCL's brand "
                 "name. Applied the same rotation to ECL/RWA below on that assumption.",
    },
    {
        "shipping_line": "ECL", "service": "RWA", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Haiphong", "country": "Vietnam"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/rcl-upsizes-china-west-asia-rwa-2-service-to-india-with-7000-teu-vessel/",
        "notes": "Same consortium loop as PIL/RWA above -- see that entry's notes. 'ECL' itself "
                 "not independently identified as a specific named carrier.",
    },
    {
        "shipping_line": "MSC", "service": "IPAK", "direction": "single",
        "ports": [
            {"port": "Sines", "country": "Portugal"},
            {"port": "Felixstowe", "country": "UK"},
            {"port": "Rotterdam", "country": "Netherlands"},
            {"port": "Hamburg", "country": "Germany"},
            {"port": "Bremerhaven", "country": "Germany"},
            {"port": "Antwerp", "country": "Belgium"},
            {"port": "Le Havre", "country": "France"},
            {"port": "London Gateway", "country": "UK"},
            {"port": "Port Louis", "country": "Mauritius"},
            {"port": "Port Reunion", "country": "Reunion (France)"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
        ],
        "confidence": "verified",
        "source_url": "https://www.maritimegateway.com/msc-and-sci-expand-ipak-service-with-addition-of-portugals-port-of-sines/",
        "notes": "Joint MSC / Shipping Corporation of India service; Sines call added Oct 2025.",
    },
    {
        "shipping_line": "AKS", "service": "TIP", "direction": "single", "ports": [],
        "confidence": "unresolved", "source_url": None,
        "notes": "'AKS' as a carrier code not identified; no usable rotation found for a "
                 "service named plain 'TIP' (searches surfaced Hapag-Lloyd's differently-coded "
                 "TPI/INDAMEX instead, already captured separately).",
    },
    {
        "shipping_line": "UNF", "service": "AGI", "direction": "single", "ports": [],
        "confidence": "unresolved",
        "source_url": "https://www.unifeeder.com/hubfs/AGI_SERVICE.pdf?hsLang=en",
        "notes": "Found Unifeeder's own AGI (ASEAN-Gulf-India Subcontinent Service) rotation -- "
                 "Laem Chabang - Singapore - Port Klang - Colombo - Jebel Ali - Karachi - Mundra "
                 "- back to Laem Chabang -- but it does NOT call Nhava Sheva at all, despite a "
                 "real current voyage in vessel_schedule using this exact (line, service). Left "
                 "unresolved rather than record a rotation JNPT itself contradicts.",
    },
    {
        "shipping_line": "EGI", "service": "AGI", "direction": "single", "ports": [],
        "confidence": "unresolved",
        "source_url": "https://atlas.flexport.com/service/code:EGLV:AGI",
        "notes": "Same AGI service, found under Evergreen's own SCAC (EGLV) -- same "
                 "non-JNPT-calling rotation problem as UNF/AGI above. JNPA's own official "
                 "shipping-agencies registry (see seed_service_rotations.py's CARRIER_NAMES) "
                 "later confirmed EGI really is Evergreen -- doesn't change this entry's own "
                 "outcome though (still unresolved -- the rotation just doesn't call JNPT).",
    },
    {
        "shipping_line": "ISL", "service": "VTI", "direction": "single",
        "ports": [
            {"port": "Ho Chi Minh City", "country": "Vietnam"},
            {"port": "Laem Chabang", "country": "Thailand"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://yourinterasia.app/en/service-routes/vti-service/",
        "notes": "Interasia's own service-route page, launched Dec 2024/Jan 2025.",
    },
    {
        "shipping_line": "MSC", "service": "SENTOSA", "direction": "single",
        "ports": [
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Laem Chabang", "country": "Thailand"},
            {"port": "Vung Tau", "country": "Vietnam"},
            {"port": "Busan", "country": "South Korea"},
            {"port": "Los Angeles", "country": "USA"},
            {"port": "Oakland", "country": "USA"},
            {"port": "Busan", "country": "South Korea"},
            {"port": "Qingdao", "country": "China"},
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Mundra", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
        ],
        "confidence": "verified",
        "source_url": "https://container-news.com/msc-adds-karachi-port-to-sentosa-shikra-pendulum-service-rotation/",
        "notes": "Merged Sentosa-Shikra pendulum service; Karachi call is a recent addition.",
    },
    {
        "shipping_line": "MAE", "service": "FM3", "direction": "single", "ports": [],
        "confidence": "unresolved", "source_url": None,
        "notes": "No usable result -- searches returned other Maersk services only.",
    },
    {
        # Same underlying consortium loop as PIL/ECL's "RWA" above, branded
        # "CIX" by Wan Hai specifically.
        "shipping_line": "WHI", "service": "CIX", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Haiphong", "country": "Vietnam"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/wan-hai-lines-launches-china-india-express-2-service-cochin-port/",
        "notes": "Multiple conflicting historical rotations found for CIX across 2006/2020/2023/"
                 "2024 -- used the most recent (2024) one found. A 2023 description also noted "
                 "the eastbound leg makes an extra Colombo call that the westbound leg skips; "
                 "not reflected in the single sequence above.",
    },
    {
        "shipping_line": "HLI", "service": "IOS", "direction": "single",
        "ports": [
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Tangier", "country": "Morocco"},
            {"port": "Rotterdam", "country": "Netherlands"},
            {"port": "Wilhelmshaven", "country": "Germany"},
            {"port": "Antwerp", "country": "Belgium"},
            {"port": "London Gateway", "country": "UK"},
            {"port": "Tangier", "country": "Morocco"},
        ],
        "confidence": "verified",
        "source_url": "https://www.hapag-lloyd.com/en/services-information/news/2024/10/shipping-with-our-ios--here-s-a-service-update.html",
        "notes": "Wilhelmshaven currently substitutes for Hamburg due to congestion "
                 "(temporary, per Hapag-Lloyd's own note).",
    },
    {
        "shipping_line": "HMM", "service": "FIM-W", "direction": "westbound",
        "ports": [
            {"port": "Busan", "country": "South Korea"},
            {"port": "Kwangyang", "country": "South Korea"},
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Kattupalli", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Damietta", "country": "Egypt"},
            {"port": "Piraeus", "country": "Greece"},
            {"port": "Genoa", "country": "Italy"},
            {"port": "Valencia", "country": "Spain"},
            {"port": "Barcelona", "country": "Spain"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.hmm21.com/e-service/general/schedule/serviceNetwork/serviceNetworkLoop.do?route=FIM&svcNwCd=MED&siteTp=C",
        "notes": "HMM's own FIM service is one 84-day round trip that calls Nhava Sheva TWICE "
                 "(once each direction) -- Busan...Nhava Sheva...Barcelona...Nhava "
                 "Sheva(again)...back to Busan. vessel_schedule's 'FIM-W' label implies JNPT "
                 "distinguishes which leg a given voyage is on, but it's unclear from the source "
                 "which of the two Nhava Sheva calls that corresponds to. Recorded only the "
                 "first (outbound) half up to Barcelona as a best guess for 'westbound' -- "
                 "treat this one as the least confident 'needs_verification' entry in this file.",
    },
    {
        "shipping_line": "OCL", "service": "CIX3", "direction": "single",
        "ports": [
            {"port": "Xingang", "country": "China"},
            {"port": "Busan", "country": "South Korea"},
            {"port": "Shanghai", "country": "China"},
            {"port": "Xiamen", "country": "China"},
            {"port": "Hong Kong", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Pipavav", "country": "India"},
            {"port": "Port Kelang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Hong Kong", "country": "China"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.oocl.com/eng/aboutoocl/corporatemessages/2020/Pages/09Sep2020.aspx",
        "notes": "Source dated Sep 2020 -- over 5 years old relative to research date; not "
                 "confirmed still current.",
    },
    {
        "shipping_line": "ONE", "service": "JTI", "direction": "single",
        "ports": [
            {"port": "Tokyo", "country": "Japan"},
            {"port": "Yokohama", "country": "Japan"},
            {"port": "Shimizu", "country": "Japan"},
            {"port": "Nagoya", "country": "Japan"},
            {"port": "Osaka", "country": "Japan"},
            {"port": "Kobe", "country": "Japan"},
            {"port": "Cai Mep", "country": "Vietnam"},
            {"port": "Laem Chabang", "country": "Thailand"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Pipavav", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Bin Qasim", "country": "Pakistan"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Laem Chabang", "country": "Thailand"},
            {"port": "Cai Mep", "country": "Vietnam"},
        ],
        "confidence": "verified",
        "source_url": "https://www.one-line.com/en/news/one-announces-updated-east-west-service-network-2026",
        "notes": "ONE's own April 2026 announcement -- JTI is a newly-integrated merge of three "
                 "prior services (TIP, JT1, JV2). Very current as of research date.",
    },
    {
        "shipping_line": "CCA", "service": "MEDEX", "direction": "single",
        "ports": [
            {"port": "Abu Dhabi", "country": "UAE"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Piraeus", "country": "Greece"},
            {"port": "Malta", "country": "Malta"},
            {"port": "Genoa", "country": "Italy"},
            {"port": "Fos-sur-Mer", "country": "France"},
            {"port": "Barcelona", "country": "Spain"},
            {"port": "Valencia", "country": "Spain"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/cma-cgm-reshapes-india-mediterranean-service-amid-red-sea-disruptions/",
        "notes": "This is the June 2025 rotation. A further Dec 2025 revision is known to have "
                 "added Port Said/Beirut and dropped Valencia/Barcelona/Fos-sur-Mer, but the "
                 "exact new order wasn't found -- this entry predates that change.",
    },
    {
        "shipping_line": "HLI", "service": "MIAX", "direction": "single",
        "ports": [
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mundra", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Durban", "country": "South Africa"},
            {"port": "Tema", "country": "Ghana"},
            {"port": "Tincan/Apapa", "country": "Nigeria"},
            {"port": "Durban", "country": "South Africa"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.porttechnology.org/news/hapag-lloyd-updates-miax-service-port-rotation/",
        "notes": "Jebel Ali calls reportedly suspended currently due to regional security "
                 "concerns per a separate note found -- current exact rotation uncertain.",
    },
    {
        "shipping_line": "CCA", "service": "AS1", "direction": "single",
        "ports": [
            {"port": "Qingdao", "country": "China"},
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Nansha", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Port Qasim", "country": "Pakistan"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Singapore", "country": "Singapore"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.cma-cgm.com/news/3220/cma-cgm-to-reorganize-its-as1-service-connecting-asia-with-the-indian-subcontinent",
        "notes": "Source dated March 2021 -- over 5 years old relative to research date.",
    },
    {
        # Shared by X-Press Feeders, EGI and KMD per source ("China-West India
        # Express" family; multiple similarly-named variants exist, e.g. TS
        # Lines' own CWX2 -- this is that specific one, applied here on the
        # strength of the shared-service-family pattern, not independently
        # confirmed for each line).
        "shipping_line": "SEC", "service": "CWX", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://logistics-manager.com/ts-lines-expands-intra-asia-footprint-with-new-china-west-india-express-cwx2-service/",
        "notes": "This is TS Lines' 'CWX2' rotation specifically (Aug 2026, very current) -- "
                 "applied to SEC/CWX on the strength of the shared 'China-West India Express' "
                 "naming family, but X-Press Feeders' own original 'CWX' may differ from TS "
                 "Lines' CWX2. Same rotation applied to EGI/CWX and KMD/CWX below.",
    },
    {
        "shipping_line": "EGI", "service": "CWX", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://logistics-manager.com/ts-lines-expands-intra-asia-footprint-with-new-china-west-india-express-cwx2-service/",
        "notes": "See SEC/CWX above -- same caveat applies.",
    },
    {
        "shipping_line": "KMD", "service": "CWX", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://logistics-manager.com/ts-lines-expands-intra-asia-footprint-with-new-china-west-india-express-cwx2-service/",
        "notes": "See SEC/CWX above -- same caveat applies. KMD likely = KMTC.",
    },
    {
        "shipping_line": "CCA", "service": "MIDAS", "direction": "single",
        "ports": [
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Pointe Noire", "country": "Congo"},
            {"port": "Tema", "country": "Ghana"},
            {"port": "Apapa", "country": "Nigeria"},
            {"port": "Cotonou", "country": "Benin"},
            {"port": "Cape Town", "country": "South Africa"},
            {"port": "Durban", "country": "South Africa"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.cma-cgm.com/news/1455/midas-service-rotation-change",
        "notes": "This is MIDAS 1 specifically -- CMA CGM also runs a MIDAS 2 with a shorter, "
                 "different rotation; plain 'MIDAS' label doesn't say which.",
    },
    {
        "shipping_line": "MSK", "service": "MIDAS", "direction": "single", "ports": [],
        "confidence": "unresolved", "source_url": None,
        "notes": "Only found CMA CGM's differently-owned MIDAS service (recorded separately "
                 "under CCA/MIDAS) -- no evidence Maersk shares that branding for a joint slot, "
                 "so not assumed to be the same rotation.",
    },
    {
        "shipping_line": "MSK", "service": "SAFINA", "direction": "single", "ports": [],
        "confidence": "unresolved", "source_url": "https://www.maersk.com/local-information/shipping-from-asia-pacific-to-imea/safina-westbound",
        "notes": "Found Maersk's own SAFINA rotation (both current and prior versions) but "
                 "NEITHER calls at Nhava Sheva -- Singapore-Tanjung Pelepas-Salalah-Duqm-Jebel "
                 "Ali-Colombo (current) or Ningbo-Shanghai-Shekou-Tanjung Pelepas-Port "
                 "Klang-Jebel Ali-Colombo-Singapore (prior). Left unresolved rather than record "
                 "a rotation JNPT's own data contradicts.",
    },
    {
        # Wan Hai + COSCO consortium, per source. Applied to all three lines
        # in vessel_schedule using this exact service code.
        "shipping_line": "ISL", "service": "CI6", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Nansha", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Pipavav", "country": "India"},
            {"port": "Penang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://en.portnews.ru/news/303498/",
        "notes": "Source describes a 2018/2019 Wan Hai + COSCO joint launch -- 7-8 years old "
                 "relative to research date, likely stale. Applied the same rotation to UNF/CI6 "
                 "and WHL/CI6 (Wan Hai's own code) on the strength of the stated joint operation.",
    },
    {
        "shipping_line": "UNF", "service": "CI6", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Nansha", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Pipavav", "country": "India"},
            {"port": "Penang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://en.portnews.ru/news/303498/",
        "notes": "See ISL/CI6 above -- same source/caveat.",
    },
    {
        "shipping_line": "WHL", "service": "CI6", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Nansha", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Pipavav", "country": "India"},
            {"port": "Penang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://en.portnews.ru/news/303498/",
        "notes": "See ISL/CI6 above -- same source/caveat. WHL = Wan Hai Lines, the service's own operator.",
    },
    {"shipping_line": "MSC", "service": "EAF", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result -- searches returned unrelated MSC advisories only."},
    {"shipping_line": "SEC", "service": "FM3", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result found for X-Press Feeders' own FM3."},
    {
        "shipping_line": "SMM", "service": "UIG", "direction": "single",
        "ports": [
            {"port": "Abu Dhabi", "country": "UAE"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Abu Dhabi", "country": "UAE"},
            {"port": "Umm Qasr", "country": "Iraq"},
            {"port": "Dammam", "country": "Saudi Arabia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.linerlytica.com/post/safeen-upgrades-uae-india-iraq-service/",
        "notes": "Safeen Feeders' 2023 upgrade, operated in partnership with Bengal Tiger Line "
                 "(BTL) -- 'SMM' not independently confirmed as one of the operating partners' "
                 "own code, applied on the strength of the (line, service) pair appearing "
                 "together in vessel_schedule.",
    },
    {
        "shipping_line": "ONE", "service": "IOX", "direction": "single",
        "ports": [
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "London Gateway", "country": "UK"},
            {"port": "Rotterdam", "country": "Netherlands"},
            {"port": "Hamburg", "country": "Germany"},
            {"port": "Antwerp", "country": "Belgium"},
        ],
        "confidence": "verified",
        "source_url": "https://www.porttechnology.org/news/shipping/one-unveils-new-indian-ocean-express-service/",
        "notes": "ONE's own launch announcement, Feb 2025 inaugural voyage.",
    },
    {"shipping_line": "PMA", "service": "IMS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Found Unifeeder's own IMS service but without a full ordered rotation, and "
              "'PMA' not confirmed as a Unifeeder-affiliated code."},
    {"shipping_line": "MSC", "service": "MES", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result -- searches returned unrelated MSC Middle East services."},
    {
        # Emirates Shipping Line's own service, per source -- applied to both
        # lines in vessel_schedule using it.
        "shipping_line": "ESA", "service": "VGI", "direction": "single",
        "ports": [
            {"port": "Ho Chi Minh City", "country": "Vietnam"},
            {"port": "Laem Chabang", "country": "Thailand"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Sohar", "country": "Oman"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://logistics-manager.com/emirates-shipping-line-to-launch-vietnam-gulf-india-service/",
        "notes": "Jointly operated by ESL (=ESA here), KMTC, RCL, CU Lines, Global Feeder "
                 "Shipping and (from Sep 2023) CMA CGM.",
    },
    {
        "shipping_line": "SMM", "service": "VGI", "direction": "single",
        "ports": [
            {"port": "Ho Chi Minh City", "country": "Vietnam"},
            {"port": "Laem Chabang", "country": "Thailand"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Sohar", "country": "Oman"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://logistics-manager.com/emirates-shipping-line-to-launch-vietnam-gulf-india-service/",
        "notes": "See ESA/VGI above -- same consortium loop.",
    },
    {
        # EGI is confirmed Evergreen (JNPA's own official registry -- see
        # seed_service_rotations.py's CARRIER_NAMES). This rotation was
        # found via an EMIRATES press release while EGI was still
        # mis-identified as Emirates -- downgraded from 'verified' to
        # 'needs_verification' accordingly, since it isn't independently
        # confirmed as Evergreen's own slot (plausible if Evergreen also
        # holds a slot on the same consortium loop, as seen elsewhere in
        # this file, but not confirmed).
        "shipping_line": "EGI", "service": "CSX", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://logistics-manager.com/emirates-shipping-line-launches-csx2-service-to-boost-china-india-trade-and-red-sea-transshipment/",
        "notes": "Found via Emirates Shipping Line's own CSX2 launch announcement (11 June "
                 "2026) while EGI was mis-identified as Emirates -- JNPA's official registry "
                 "has since confirmed EGI is actually Evergreen. This rotation may still be "
                 "correct (Evergreen could hold its own slot on the same consortium loop) but "
                 "that's not independently confirmed, hence the downgrade from 'verified'.",
    },
    {
        "shipping_line": "TSC", "service": "CISC", "direction": "single",
        "ports": [
            {"port": "Xingang", "country": "China"},
            {"port": "Qingdao", "country": "China"},
            {"port": "Kaohsiung", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
        ],
        "confidence": "needs_verification", "source_url": None,
        "notes": "China India Sub-Continent (CISC) service -- applied to UNF/CISC and "
                 "EGI/CISC below as the same named service.",
    },
    {
        "shipping_line": "UNF", "service": "CISC", "direction": "single",
        "ports": [
            {"port": "Xingang", "country": "China"}, {"port": "Qingdao", "country": "China"},
            {"port": "Kaohsiung", "country": "China"}, {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"}, {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"}, {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Port Klang", "country": "Malaysia"}, {"port": "Singapore", "country": "Singapore"},
        ],
        "confidence": "needs_verification", "source_url": None,
        "notes": "See TSC/CISC above -- same service.",
    },
    {
        "shipping_line": "EGI", "service": "CISC", "direction": "single",
        "ports": [
            {"port": "Xingang", "country": "China"}, {"port": "Qingdao", "country": "China"},
            {"port": "Kaohsiung", "country": "China"}, {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"}, {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"}, {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Port Klang", "country": "Malaysia"}, {"port": "Singapore", "country": "Singapore"},
        ],
        "confidence": "needs_verification", "source_url": None,
        "notes": "See TSC/CISC above -- same service.",
    },
    {
        "shipping_line": "SMD", "service": "KIX", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Khorfakkan", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/gt-lines-kix1-weekly/",
        "notes": "GT Lines' own KIX 1, upgraded to weekly from 15 July 2026 -- current, but "
                 "'SMD' not independently confirmed as GT Lines' own or a partner's code.",
    },
    {
        "shipping_line": "DMA", "service": "KIX", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Khorfakkan", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/gt-lines-kix1-weekly/",
        "notes": "See SMD/KIX above -- same caveat.",
    },
    {
        "shipping_line": "KMD", "service": "SI8", "direction": "single",
        "ports": [
            {"port": "Jakarta", "country": "Indonesia"},
            {"port": "Surabaya", "country": "Indonesia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Kelang", "country": "Malaysia"},
            {"port": "Tuticorin", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://indiashippingnews.com/international-shipping/evergreen-expands-southeast-asia-india-network-through-si8-ais5-service/",
        "notes": "Multi-carrier consortium confirmed (Interasia, KMTC, Wan Hai, plus Evergreen "
                 "taking slots) -- KMD likely = KMTC. Applied same rotation to WHL/SI8 below.",
    },
    {
        "shipping_line": "WHL", "service": "SI8", "direction": "single",
        "ports": [
            {"port": "Jakarta", "country": "Indonesia"}, {"port": "Surabaya", "country": "Indonesia"},
            {"port": "Singapore", "country": "Singapore"}, {"port": "Port Kelang", "country": "Malaysia"},
            {"port": "Tuticorin", "country": "India"}, {"port": "Nhava Sheva", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://indiashippingnews.com/international-shipping/evergreen-expands-southeast-asia-india-network-through-si8-ais5-service/",
        "notes": "See KMD/SI8 above -- Wan Hai is this service's own named operator.",
    },
    {
        "shipping_line": "SEC", "service": "HLS", "direction": "single",
        "ports": [
            {"port": "Laem Chabang", "country": "Thailand"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
        ],
        "confidence": "verified",
        "source_url": "https://indiashippingnews.com/x-press-feeders-updates-hls-service/",
        "notes": "X-Press Feeders' own update, effective 24 April 2026 -- current.",
    },
    {"shipping_line": "TST", "service": "HLS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "'TST' not identified as a carrier; not assumed to share X-Press Feeders' "
              "HLS rotation without confirmation."},
    {
        # Directional split confirmed by source ("WESTBOUND Shanghai to Nhava
        # Sheva and EASTBOUND Port Klang to Shanghai") but only endpoints, not
        # a full ordered intermediate stop list -- reconstructed as a mirror
        # of each other around the same 5 named "key ports", NOT confirmed.
        "shipping_line": "GSL", "service": "NIX", "direction": "westbound",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://gocargonet.com/shipping-lines-restructure-far-east-india-services-to-enhance-network-efficiency-and-service-reliability/",
        "notes": "Gold Star Line (GSL) + Global Feeder Shipping joint service. Source confirms "
                 "westbound is Shanghai->Nhava Sheva and eastbound is Port Klang->Shanghai, but "
                 "not the full intermediate order -- this is a reconstruction from the 'key "
                 "ports' named (Port Klang/Nhava Sheva/Hazira/Mundra), not a confirmed sequence. "
                 "This is the clearest example in this research pass of the "
                 "eastbound-differs-from-westbound pattern, but the LEAST confident one for "
                 "exact call order.",
    },
    {
        "shipping_line": "GSL", "service": "NIX", "direction": "eastbound",
        "ports": [
            {"port": "Mundra", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Shanghai", "country": "China"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://gocargonet.com/shipping-lines-restructure-far-east-india-services-to-enhance-network-efficiency-and-service-reliability/",
        "notes": "Eastbound leg -- see westbound entry's notes for the same caveats.",
    },
    {
        # WHI/CIX's own source explicitly named this as a Wan Hai + Hapag-Lloyd
        # + Evergreen joint service -- Hapag-Lloyd's own slot gets the same
        # rotation with the same confidence, unlike the other "shared" guesses
        # in this file that lacked that explicit confirmation.
        "shipping_line": "HLI", "service": "CIX", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Haiphong", "country": "Vietnam"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/wan-hai-lines-launches-china-india-express-2-service-cochin-port/",
        "notes": "Source explicitly confirms this service is jointly operated by Wan Hai, "
                 "Hapag-Lloyd and Evergreen -- see WHI/CIX for the same rotation and its "
                 "own caveats (multiple conflicting historical versions found; used most recent).",
    },
    {
        "shipping_line": "COS", "service": "EPIC", "direction": "single", "ports": [],
        "confidence": "unresolved",
        "source_url": "https://world.lines.coscoshipping.com/lines_resource/local/india/defaultContentAttachment/20260514/PAN%20INDIA%20LTS%20MAY%202026.pdf",
        "notes": "This is COSCO's own slot on the EPIC3 variant (distinct from CCA/EPIC, which "
                 "is CMA CGM's EPIC1) -- known port set (Nhava Sheva, Mundra, Jeddah, Tangier, "
                 "Southampton, Rotterdam, Bremerhaven, Antwerp, Le Havre, Algeciras) but no "
                 "confirmed call order found, so not recorded as a guessed sequence.",
    },
]
