"""
Researched port rotations for the named services seen in vessel_schedule,
gathered via public web search (see pipeline/rotations.py and
models.ServiceRotation for how this data is used and what the
confidence levels mean).

FIRST PASS (2026-09-11, JNPT only): covers 74 of the 97 distinct
(shipping_line, service) combinations live at JNPT as of that date --
see docs/service_rotations_research_notes.md for exact coverage, the
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
fetches (both 403 at the time), so every entry here comes from
search-result synthesis, not a direct primary-source read -- read
`confidence` accordingly.

SECOND PASS (2026-09-14, adding Mundra/Cochin/Chennai): once the other
three ports were added, JNPT's original 97 combos grew to 193 total,
of which 128 were genuinely new (not just the same service reappearing
at a second port). See docs/service_rotations_research_notes.md for
the full coverage accounting. Two new patterns showed up that the first
pass hadn't seen:
  - Cross-port carrier-code duplication: the same global carrier can
    have a DIFFERENT local agent code at JNPT vs at Mundra/Cochin/
    Chennai (CCA at JNPT / CMA at Mundra are both CMA CGM; HLI / HLL
    are both Hapag-Lloyd; SEC / XPF are both X-Press Feeders; ISL / INT
    are both Interasia). Where this pass found the SAME service name
    under a different code, it reused the first pass's rotation
    directly rather than re-researching from scratch -- see each such
    entry's own notes.
  - A live vessel-reassignment check (comparing our own scraped
    `service` label for two real vessels against Flexport Atlas's and
    MSC's own current-voyage tools) showed that a vessel can be
    reassigned to a different named service than the one our pipeline
    last recorded for it -- confirmed for both MSC NAOMI (ours:
    MALABAR; Atlas's live answer: MSC CARIOCA) and MSC BARBARA (ours:
    IAS; MSC's own tool: Ingwe Service, not calling India at all). This
    means a rotation recorded here for a SERVICE can still be right
    while a specific CURRENTLY-ASSIGNED VESSEL has since moved off it
    -- expected drift, not a data bug, and not fixable by researching
    harder.

Re-run `seed_service_rotations.py` after editing this file; it upserts
by (shipping_line, service, direction), so re-running is always safe.

Each port dict: {"port": str, "country": str}. `jnpt_index` is computed
automatically at seed time by matching a port name against JNPT_ALIASES
in seed_service_rotations.py -- don't hand-set it here.

DIRECTIONALITY: a few services here (BIGEX, GSL/NIX, HMM/HYN's FIM)
run a genuinely different port set/order eastbound vs westbound, not
just each other's reverse -- these get two entries with the same
(shipping_line, service) and different `direction`, both loaded as
separate rows (see models.ServiceRotation's own docstring). Most
consortium/pendulum services below (the RWA/CIX/CISC/SI8/CI6/VGI/CWX
families) read as one continuous cycle already, so direction="single"
is correct for them -- the "eastbound" and "westbound" halves are just
two arcs of the same loop, both captured by recording the whole thing
in call order.
"""

ADHOC_LINES = [
    # (shipping_line, service) pairs currently in vessel_schedule where the
    # service itself is "ADHOC" -- a JNPT-side label meaning an unscheduled,
    # one-off call, not a named loop. There is genuinely no fixed rotation
    # to research for these; confidence="no_fixed_rotation" says so
    # explicitly rather than leaving them looking un-researched.
    "ESA", "UNF", "EMS", "MSK", "KIN", "EMT", "RGS", "SBB", "WAN", "RCL", "TNS",
    # Added in the second pass (Mundra/Cochin/Chennai): same "ADHOC" label,
    # newly observed under these lines' own codes.
    "ECL", "EMC", "MSC", "MSI", "RCF", "SMI",
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

    # ==================================================================
    # SECOND PASS (2026-09-14): Mundra/Cochin/Chennai backlog.
    # See the module docstring above for the two new patterns this pass
    # ran into (cross-port carrier-code duplication, vessel reassignment)
    # and docs/service_rotations_research_notes.md for the coverage
    # accounting. Organized in three groups below: (A) direct reuse where
    # a same-carrier code correspondence was established with reasonable
    # confidence, (B) reuse applied more cautiously because the carrier
    # correspondence itself isn't confirmed, (C) genuinely new research,
    # (D) unresolved -- looked, didn't find a usable ordered rotation (or
    # found one that contradicts vessel_schedule), recorded honestly
    # rather than guessed.
    # ==================================================================

    # --- (A) direct cross-port carrier-code reuse -----------------------
    {
        "shipping_line": "CMA", "service": "BIGEX", "direction": "eastbound",
        "ports": [
            {"port": "Fujairah", "country": "UAE"},
            {"port": "Sohar", "country": "Oman"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.cma-cgm.com/news/4997/cma-cgm-to-strengthen-its-bigex-lines-network-connecting-the-indian-subcontinent-gulf-amp-red-sea",
        "notes": "Same CMA CGM service as CCA/BIGEX above -- 'CMA' is the code Mundra/Cochin/"
                 "Chennai's own registries use for CMA CGM, where JNPT's registry uses 'CCA'. "
                 "Same BIGEX-1/2/3/4 variant-ambiguity caveat applies -- see CCA/BIGEX's notes.",
    },
    {
        "shipping_line": "CMA", "service": "BIGEX", "direction": "westbound",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Sohar", "country": "Oman"},
            {"port": "Fujairah", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.cma-cgm.com/news/4997/cma-cgm-to-strengthen-its-bigex-lines-network-connecting-the-indian-subcontinent-gulf-amp-red-sea",
        "notes": "Westbound leg -- see CMA/BIGEX eastbound entry above.",
    },
    {
        "shipping_line": "CMA", "service": "INDAMEX", "direction": "single",
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
        "notes": "Same CMA CGM service as CCA/INDAMEX above -- see CMA/BIGEX's note on the CCA/CMA "
                 "cross-port code correspondence.",
    },
    {
        "shipping_line": "CMA", "service": "MEDEX", "direction": "single",
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
        "notes": "Same CMA CGM service as CCA/MEDEX above -- same June-2025-predates-a-known-Dec-2025 "
                 "revision caveat applies.",
    },
    {
        "shipping_line": "CMA", "service": "SWAX", "direction": "single",
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
        "notes": "Same CMA CGM service as CCA/SWAX above.",
    },
    {
        "shipping_line": "HLL", "service": "TPI", "direction": "single",
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
        "notes": "Same Hapag-Lloyd service as HLI/TPI above -- 'HLL' is the code Mundra/Cochin/"
                 "Chennai's own registries use for Hapag-Lloyd, where JNPT's registry uses 'HLI'.",
    },
    {
        "shipping_line": "HLL", "service": "MIAX", "direction": "single",
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
        "notes": "Same Hapag-Lloyd service as HLI/MIAX above -- see HLL/TPI's note on the HLI/HLL "
                 "cross-port code correspondence.",
    },
    {
        "shipping_line": "XPF", "service": "RGI", "direction": "single",
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
        "notes": "Same service as SEC/RGI above -- 'XPF' is X-Press Feeders' own operating-company "
                 "code where 'SEC' (Sea Consortium, X-Press's corporate parent) is the code JNPT's "
                 "registry uses for the same carrier.",
    },
    {
        "shipping_line": "XPF", "service": "HLS", "direction": "single",
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
        "notes": "Same service as SEC/HLS above -- see XPF/RGI's note on the SEC/XPF correspondence; "
                 "this source is literally X-Press Feeders' own announcement, strengthening it.",
    },
    {
        "shipping_line": "KMT", "service": "CWX", "direction": "single",
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
        "notes": "Same CWX family as SEC/CWX, EGI/CWX and KMD/CWX above -- 'KMT' likely another code "
                 "for KMTC (same guess already made for 'KMD' elsewhere in this file).",
    },
    {
        "shipping_line": "INT", "service": "CI6", "direction": "single",
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
        "notes": "Same consortium loop as ISL/CI6, UNF/CI6 and WHL/CI6 above -- 'INT' is very likely "
                 "another code for Interasia, the same carrier 'ISL' denotes elsewhere in this file.",
    },
    {
        "shipping_line": "INT", "service": "VTI", "direction": "single",
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
        "notes": "Same service as ISL/VTI above -- see INT/CI6's note; this is Interasia's own "
                 "service-route page, so the carrier identity is solid even if the 'INT'-vs-'ISL' "
                 "code correspondence isn't independently confirmed.",
    },
    {
        "shipping_line": "CUS", "service": "IMR", "direction": "single",
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
        "notes": "Same service as CUL/IMR above -- 'CUS' is very likely another code for CU Lines "
                 "(joint operation with CStar and UGL, per CUL/IMR's own source).",
    },
    {
        "shipping_line": "HYN", "service": "IOX", "direction": "single",
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
        "confidence": "needs_verification",
        "source_url": "https://www.porttechnology.org/news/shipping/one-unveils-new-indian-ocean-express-service/",
        "notes": "Same service as ONE/IOX above -- applied to 'HYN' (HMM's own code elsewhere in "
                 "this file) on the strength of the shared exact service name; not independently "
                 "confirmed that HMM holds its own slot on ONE's IOX loop, so downgraded from "
                 "ONE/IOX's own 'verified' to 'needs_verification'.",
    },

    # --- (B) cautious reuse -- carrier correspondence NOT confirmed -----
    {
        "shipping_line": "OCE", "service": "MIAX", "direction": "single",
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
        "notes": "Applied the same MIAX rotation as HLI/MIAX and HLL/MIAX on the strength of the "
                 "identical service name -- but unlike HLL, 'OCE' is NOT independently confirmed as "
                 "a Hapag-Lloyd code (could be a joint-slot partner). Treat the carrier-identity "
                 "part of this entry with real caution.",
    },
    {
        "shipping_line": "ECL", "service": "IG1", "direction": "single",
        "ports": [
            {"port": "Kandla", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Khorfakkan", "country": "UAE"},
            {"port": "Sohar", "country": "Oman"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/hapag-lloyd-revises-india-gulf-service-1-rotation/",
        "notes": "Applied HLI/IG1's rotation here on the same reasoning PIL/RWA used elsewhere in "
                 "this file: vessel_schedule pairs 'ECL' with this exact service name, but no "
                 "source independently confirms ECL (already used for a consortium slot on RWA "
                 "above) holds a joint slot on Hapag-Lloyd's own IG1 -- treat cautiously.",
    },
    {
        "shipping_line": "CEA", "service": "CIX3", "direction": "single",
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
        "notes": "Applied the same rotation as OCL/CIX3 above on the strength of the identical "
                 "service name -- 'CEA' not independently confirmed as OOCL or a partner's own "
                 "code (a COSCO/OOCL guess, consistent with CEA/SEI2 elsewhere in this pass, but "
                 "not confirmed). Also inherits OCL/CIX3's own over-5-years-old-source caveat.",
    },
    {
        "shipping_line": "EMC", "service": "CWX", "direction": "single",
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
        "notes": "Same CWX family as SEC/CWX, EGI/CWX, KMD/CWX and KMT/CWX above -- same caveat: "
                 "this is specifically TS Lines' own CWX2 rotation, applied across the family on "
                 "the shared naming pattern, not independently confirmed for each line.",
    },
    {
        "shipping_line": "EMC", "service": "RWA2", "direction": "single",
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
        "notes": "The PIL/RWA and ECL/RWA entries above are already RCL's own 'RWA2' rotation "
                 "specifically (see PIL/RWA's own notes) -- vessel_schedule's separate 'RWA2' "
                 "string for EMC/PID/RCF (see those entries too) is very likely the exact same "
                 "rotation under its fuller name. 'EMC' not independently identified as a specific "
                 "carrier.",
    },
    {
        "shipping_line": "PID", "service": "RWA2", "direction": "single",
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
        "notes": "See EMC/RWA2 above -- same reasoning and same caveat.",
    },
    {
        "shipping_line": "RCF", "service": "RWA2", "direction": "single",
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
        "notes": "See EMC/RWA2 above -- 'RCF' plausibly RCL's own code (RCL is this rotation's "
                 "actual operator per the source), making this the most confident of the three "
                 "RWA2 entries in this group.",
    },
    {
        "shipping_line": "FZE", "service": "CSX2", "direction": "single",
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
        "notes": "Same rotation and source as EGI/CSX above, which recorded the exact string "
                 "'CSX2' from an Emirates Shipping Line (ESL) press release while 'EGI' was "
                 "mis-identified as Emirates (EGI is actually Evergreen, per JNPA's registry). "
                 "'FZE' (a Fujairah free-zone-style code) is arguably a BETTER fit for ESL's own "
                 "identity than EGI ever was, given the source is literally an ESL announcement "
                 "-- but this is still a guess, not a confirmed code mapping.",
    },
    {
        "shipping_line": "EMC", "service": "AGI", "direction": "single",
        "ports": [
            {"port": "Laem Chabang", "country": "Thailand"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Mundra", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.unifeeder.com/hubfs/AGI_SERVICE.pdf?hsLang=en",
        "notes": "Same rotation as UNF/AGI and EGI/AGI above (Unifeeder's own AGI / ASEAN-Gulf-"
                 "India Subcontinent Service), both of which were left 'unresolved' at JNPT "
                 "because the rotation does NOT call Nhava Sheva. It DOES call Mundra, though -- "
                 "so for this pass's Mundra-side EMC/AGI combo, the same rotation is actually "
                 "consistent with the data rather than contradicting it, hence 'needs_verification' "
                 "here instead of 'unresolved'. 'EMC' itself not independently identified.",
    },

    # --- (C) new research from this pass ---------------------------------
    {
        "shipping_line": "HLL", "service": "EA2", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mombasa", "country": "Kenya"},
            {"port": "Dar Es Salaam", "country": "Tanzania"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.hapag-lloyd.com/en/services-information/news/2025/07/shipping-with-our-east-africa-service-2--ea2---here-s-a-rotation.html",
        "notes": "Hapag-Lloyd's own East Africa Service 2 (EA2), operated in partnership with ESL "
                 "(Emirates Shipping Line) per Hapag-Lloyd's own July 2025 update -- applied the "
                 "same rotation to ESA/EA2 and FZE/EA2 below on that explicit joint-operation basis.",
    },
    {
        "shipping_line": "ESA", "service": "EA2", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mombasa", "country": "Kenya"},
            {"port": "Dar Es Salaam", "country": "Tanzania"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.hapag-lloyd.com/en/services-information/news/2025/07/shipping-with-our-east-africa-service-2--ea2---here-s-a-rotation.html",
        "notes": "ESL's own slot on the joint EA2 service -- see HLL/EA2 above.",
    },
    {
        "shipping_line": "FZE", "service": "EA2", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mombasa", "country": "Kenya"},
            {"port": "Dar Es Salaam", "country": "Tanzania"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.hapag-lloyd.com/en/services-information/news/2025/07/shipping-with-our-east-africa-service-2--ea2---here-s-a-rotation.html",
        "notes": "See HLL/EA2 above -- 'FZE' plausibly ESL's own code (see FZE/CSX2's note on the "
                 "same guess).",
    },
    {
        "shipping_line": "AKS", "service": "EAS", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mombasa", "country": "Kenya"},
            {"port": "Dar Es Salaam", "country": "Tanzania"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.hapag-lloyd.com/en/services-information/news/2025/07/shipping-with-our-east-africa-service-2--ea2---here-s-a-rotation.html",
        "notes": "Search results used 'East Africa Service 2 (EAS 2)' and 'EA2' near-interchangeably "
                 "for what looks like the same Hapag-Lloyd/ESL joint service (see HLL/EA2 above) "
                 "-- applied the same rotation here on that basis, but 'AKS' as a carrier code is "
                 "not independently identified, so treat both the naming-overlap and carrier-"
                 "identity assumptions with caution.",
    },
    {
        "shipping_line": "NIL", "service": "EAS", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mombasa", "country": "Kenya"},
            {"port": "Dar Es Salaam", "country": "Tanzania"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.hapag-lloyd.com/en/services-information/news/2025/07/shipping-with-our-east-africa-service-2--ea2---here-s-a-rotation.html",
        "notes": "See AKS/EAS above -- same EAS/EA2 naming-overlap caveat; 'NIL' not independently "
                 "identified as a carrier either.",
    },
    {
        "shipping_line": "FZE", "service": "ECSX", "direction": "single",
        "ports": [
            {"port": "Qingdao", "country": "China"},
            {"port": "Xiamen", "country": "China"},
            {"port": "Nansha", "country": "China"},
            {"port": "Dachan Bay", "country": "China"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Qingdao", "country": "China"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://theloadstar.com/",
        "notes": "Evergreen + Emirates Shipping Line (ESL) joint China-India Express 8 (CIX8) / "
                 "ESL China Subcontinent Express (ECSX) service, effective 6 July 2025 -- 4 ships "
                 "from ESL, 2 from Evergreen, 42-day turn. Applied to EMC/ECSX below too.",
    },
    {
        "shipping_line": "EMC", "service": "ECSX", "direction": "single",
        "ports": [
            {"port": "Qingdao", "country": "China"},
            {"port": "Xiamen", "country": "China"},
            {"port": "Nansha", "country": "China"},
            {"port": "Dachan Bay", "country": "China"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Qingdao", "country": "China"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://theloadstar.com/",
        "notes": "See FZE/ECSX above -- same joint Evergreen/ESL service.",
    },
    {
        "shipping_line": "MSC", "service": "MALABAR", "direction": "single",
        "ports": [
            {"port": "Cochin", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Abu Dhabi", "country": "UAE"},
            {"port": "Shuwaikh", "country": "Kuwait"},
            {"port": "Hamad", "country": "Qatar"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Cochin", "country": "India"},
        ],
        "confidence": "verified",
        "source_url": "https://container-news.com/msc-adds-south-india-middle-east-string-for-transshipment-trade/",
        "notes": "MSC's own weekly South India-Middle East string, first DP World Cochin (ICTT/"
                 "Vallarpadam) call 6 April 2023 -- corroborated by maritimegateway.com's own "
                 "coverage of the same launch. Distinct from 'MALABAR EXPRESS', a different MSC "
                 "service connecting Colombo with Tuticorin/Vizhinjam -- don't conflate the two.",
    },
    {
        "shipping_line": "MSC", "service": "IAS", "direction": "single",
        "ports": [
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Khalifa", "country": "UAE"},
            {"port": "Sohar", "country": "Oman"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Ngqura", "country": "South Africa"},
            {"port": "Abidjan", "country": "Ivory Coast"},
            {"port": "Tema", "country": "Ghana"},
            {"port": "Lome", "country": "Togo"},
            {"port": "Cotonou", "country": "Benin"},
            {"port": "Kribi", "country": "Cameroon"},
            {"port": "Cape Town", "country": "South Africa"},
            {"port": "Jebel Ali", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.msc.com/en/newsroom/customer-advisories/2024/december/msc-adds-eastbound-call-in-cape-town-on-ias-india-africa-service",
        "notes": "MSC's own India-Africa Service (IAS) -- this is the rotation as of Jan 2026 per "
                 "the most recent update found; MSC's own advisories show this rotation has "
                 "changed more than once (a Dec 2024-Jan 2026 version ran Jebel Ali-Abu Dhabi-"
                 "Sohar-Mundra-Nhava Sheva-Colombo-Lome-Cotonou-Abidjan-Tema-Cape Town-Jebel Ali "
                 "instead), and MSC has separately dropped Vizhinjam from a related ME/ISC-Africa "
                 "loop -- treat the exact current order as liable to keep shifting. NOTE: our own "
                 "pipeline recorded MSC BARBARA under this service, but MSC's own live vessel-"
                 "schedule tool (checked 2026-09-14) showed her actually on 'Ingwe Service', not "
                 "calling India -- see the module docstring's vessel-reassignment note. That's "
                 "about the VESSEL, not this rotation; not a reason to distrust the rotation itself.",
    },
    {
        "shipping_line": "MSC", "service": "ILANGA", "direction": "single",
        "ports": [
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Abu Dhabi", "country": "UAE"},
            {"port": "Sohar", "country": "Oman"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Lome", "country": "Togo"},
            {"port": "Cotonou", "country": "Benin"},
            {"port": "Abidjan", "country": "Ivory Coast"},
            {"port": "Tema", "country": "Ghana"},
            {"port": "Cape Town", "country": "South Africa"},
            {"port": "Jebel Ali", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://logistics-manager.com/msc-enhances-ias-india-africa-service-with-new-cape-town-call/",
        "notes": "One search result named an 'Ilanga Express (ILE)' alongside MSC's IAS in a way "
                 "that suggests it's an earlier/alternate name for the same India-Africa loop -- "
                 "this is that predecessor rotation (identical India ports to MSC/IAS above, minor "
                 "African-leg differences). Not confirmed as a genuinely distinct, still-active "
                 "service versus simply an older name for IAS.",
    },
    {
        "shipping_line": "MSC", "service": "SHIKRA", "direction": "single",
        "ports": [
            {"port": "Qingdao", "country": "China"},
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Kaohsiung", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Tanjung Pelepas", "country": "Malaysia"},
            {"port": "Vung Tau", "country": "Vietnam"},
            {"port": "Qingdao", "country": "China"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.ajot.com/news/msc-introduces-asia-india-shikra-service",
        "notes": "MSC's own Asia-India Shikra service (MSC MARA, voyage QS321A, was the source's "
                 "example vessel). NOTE: MSC/SENTOSA above documents a LATER merger of Sentosa and "
                 "Shikra into one combined pendulum service -- if that merger is fully in effect, "
                 "this standalone Shikra rotation may already be superseded by MSC/SENTOSA's; kept "
                 "as its own entry since vessel_schedule still logs 'SHIKRA' as a distinct label.",
    },
    {
        "shipping_line": "MSC", "service": "HIMEXP", "direction": "single",
        "ports": [
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "King Abdullah Port", "country": "Saudi Arabia"},
            {"port": "Piraeus", "country": "Greece"},
            {"port": "Barcelona", "country": "Spain"},
            {"port": "Felixstowe", "country": "UK"},
            {"port": "Rotterdam", "country": "Netherlands"},
            {"port": "Hamburg", "country": "Germany"},
            {"port": "Antwerp", "country": "Belgium"},
            {"port": "Sines", "country": "Portugal"},
            {"port": "Colombo", "country": "Sri Lanka"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://atlas.flexport.com/service/code:MSCU:HIMALAYA",
        "notes": "MSC's own 'Himalaya Express' (HIMEXP is very likely the same service, abbreviated "
                 "differently by the terminal) -- a separate description frames this as two "
                 "directional legs (WESTBOUND Mundra->Valencia, EASTBOUND Valencia->Mundra) rather "
                 "than one symmetric loop, but only this one full port list was found; recorded as "
                 "a single loop rather than guessing how to split it, similar to HMM/FIM-W's own "
                 "unsplit treatment elsewhere in this file.",
    },
    {
        "shipping_line": "HYN", "service": "FIM(W)", "direction": "westbound",
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
        "notes": "Same service and same outbound-half caveat as HMM/FIM-W above -- 'HYN' is "
                 "presumably another code for HMM (Hyundai Merchant Marine, HMM's former name). "
                 "Unlike JNPT (which only ever showed 'FIM-W'), Mundra/Cochin/Chennai's data shows "
                 "BOTH 'FIM(W)' and 'FIM(E)' -- see FIM(E) below for the return half, now filled "
                 "in using the full round-trip description this pass found.",
    },
    {
        "shipping_line": "HYN", "service": "FIM(E)", "direction": "eastbound",
        "ports": [
            {"port": "Barcelona", "country": "Spain"},
            {"port": "Piraeus", "country": "Greece"},
            {"port": "Damietta", "country": "Egypt"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Kattupalli", "country": "India"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Da Chan Bay", "country": "China"},
            {"port": "Busan", "country": "South Korea"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.hmm21.com/e-service/general/schedule/serviceNetwork/serviceNetworkLoop.do?route=FIM&svcNwCd=MED&siteTp=C",
        "notes": "Return half of the same 84-day HMM FIM round trip as FIM(W) above -- HMM's own "
                 "source describes this as one continuous loop calling Nhava Sheva/Mundra once "
                 "each direction, not two independently-published rotations, so this half is "
                 "reconstructed from the same source rather than separately confirmed.",
    },
    {
        "shipping_line": "HMM", "service": "FIM-E", "direction": "eastbound",
        "ports": [
            {"port": "Barcelona", "country": "Spain"},
            {"port": "Piraeus", "country": "Greece"},
            {"port": "Damietta", "country": "Egypt"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Kattupalli", "country": "India"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Da Chan Bay", "country": "China"},
            {"port": "Busan", "country": "South Korea"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.hmm21.com/e-service/general/schedule/serviceNetwork/serviceNetworkLoop.do?route=FIM&svcNwCd=MED&siteTp=C",
        "notes": "Same return leg as HYN/FIM(E) above, under HMM's own plain code -- pairs with "
                 "the existing HMM/FIM-W entry earlier in this file.",
    },
    {
        "shipping_line": "UNF", "service": "MJI", "direction": "single",
        "ports": [
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mombasa", "country": "Kenya"},
            {"port": "Beira", "country": "Mozambique"},
            {"port": "Maputo", "country": "Mozambique"},
            {"port": "Jebel Ali", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.dpworld.com/en/news/india/dp-world-nhava-sheva-welcomes-new-weekly-mji-service",
        "notes": "Joint Unifeeder Group / ONE Line service, per DP World Nhava Sheva's own "
                 "announcement -- 35-day turn, 3 ships of 1,700-2,000 TEU. Evergreen (EGI, which "
                 "also shows a single EGI/MJI call in vessel_schedule) is NOT named as an operator "
                 "by this source -- left EGI/MJI unresolved below rather than assume it shares "
                 "this rotation.",
    },
    {
        "shipping_line": "MSK", "service": "MW2 MEWA", "direction": "single",
        "ports": [
            {"port": "Tanjung Pelepas", "country": "Malaysia"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Tema", "country": "Ghana"},
            {"port": "Lome", "country": "Togo"},
            {"port": "Abidjan", "country": "Ivory Coast"},
            {"port": "Tanjung Pelepas", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/maersk-announces-commencement-of-new-service-from-india-and-middle-east-to-west-africa-mw2-mewa/",
        "notes": "Maersk's second India/Middle East-West Africa service (MW2/MEWA), additional to "
                 "the existing MESAWA/MW1 already in this file -- WAFMAX vessels, first sailing "
                 "Maersk Chachai/408W on 23 Feb 2024.",
    },
    {
        "shipping_line": "WAN", "service": "CI7", "direction": "single",
        "ports": [
            {"port": "Haiphong", "country": "Vietnam"},
            {"port": "Zhanjiang", "country": "China"},
            {"port": "Nansha", "country": "China"},
            {"port": "Cat Lai", "country": "Vietnam"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Chennai", "country": "India"},
            {"port": "Vizag", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Haiphong", "country": "Vietnam"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.porttechnology.org/news/wan-hai-launches-ci7-express-service/",
        "notes": "Wan Hai's own South China-Vietnam-East India (CI7) service, 4 ships of 1,200 "
                 "TEU, maiden voyage 27 March 2022. A separate, later source (Tuticorin Container "
                 "Terminal, Nov 2024) also names a Tuticorin call on 'CI7' not present in the "
                 "original launch rotation above -- may reflect a since-added stop; not merged in "
                 "since the exact updated order wasn't found.",
    },
    {
        "shipping_line": "CMA", "service": "MIDAS2", "direction": "single",
        "ports": [
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Durban", "country": "South Africa"},
            {"port": "Jebel Ali", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.cma-cgm.com/news/3814/cma-cgm-to-reshuffle-midas-2-service-connecting-south-africa-with-the-middle-east-gulf-above",
        "notes": "This resolves the ambiguity flagged for CMA/MIDAS2 during this pass's initial "
                 "search round -- CMA CGM's own MIDAS 2 (distinct from CCA/MIDAS = MIDAS 1 "
                 "elsewhere in this file), 49-day rotation, 7 vessels up to 2,800 TEU. Durban is "
                 "now the only South African call (Pointe des Galets moved to a new 'KARIBU' "
                 "service); Port Elizabeth served via a Durban feeder, not a direct call.",
    },
    {
        "shipping_line": "CMA", "service": "TVI", "direction": "single",
        "ports": [
            {"port": "Laem Chabang", "country": "Thailand"},
            {"port": "Vung Tau", "country": "Vietnam"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Chennai", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Laem Chabang", "country": "Thailand"},
        ],
        "confidence": "verified",
        "source_url": "https://www.cma-cgm.com/news/5252/launch-of-tvi-service-connecting-thailand-vietnam-and-malaysia-to-south-east-india-amp-sri-lanka",
        "notes": "CMA CGM's Thailand-Vietnam-India (TVI) service, relaunched from the former IEX2 "
                 "-- maiden voyage CNC JAGUAR departed Laem Chabang 22 Dec 2025. Corroborated by "
                 "CMA CGM's own site plus several independent trade-press write-ups (itln.in, "
                 "container-news, linerlytica, indiashippingnews, gccports), all agreeing on this "
                 "rotation -- the strongest-sourced entry in this whole second pass.",
    },
    {
        "shipping_line": "INA", "service": "CI5", "direction": "single",
        "ports": [
            {"port": "Qingdao", "country": "China"},
            {"port": "Busan", "country": "South Korea"},
            {"port": "Shanghai", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Chennai", "country": "India"},
            {"port": "Kattupalli", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Pasir Gudang", "country": "Malaysia"},
            {"port": "Shekou", "country": "China"},
            {"port": "Kaohsiung", "country": "China"},
            {"port": "Qingdao", "country": "China"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://logistics-manager.com/interasia-lines-to-launch-new-ci5-service-for-china-east-india/",
        "notes": "'INA' = Interasia Lines, and this is their own China-East India Service V (CI5), "
                 "launched mid-Dec 2020 -- a 5-carrier consortium (Wan Hai, Interasia, KMTC, "
                 "Goldstar Lines, BTL), 6 vessels of 4,250 TEU, 42-day round trip. Applied to "
                 "WAN/CI5 below on the strength of Wan Hai being an explicitly named co-operator.",
    },
    {
        "shipping_line": "WAN", "service": "CI5", "direction": "single",
        "ports": [
            {"port": "Qingdao", "country": "China"},
            {"port": "Busan", "country": "South Korea"},
            {"port": "Shanghai", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Chennai", "country": "India"},
            {"port": "Kattupalli", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Pasir Gudang", "country": "Malaysia"},
            {"port": "Shekou", "country": "China"},
            {"port": "Kaohsiung", "country": "China"},
            {"port": "Qingdao", "country": "China"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://logistics-manager.com/interasia-lines-to-launch-new-ci5-service-for-china-east-india/",
        "notes": "See INA/CI5 above -- Wan Hai's own slot on the same 5-carrier consortium loop "
                 "(a separate Wan Hai-branded launch of what looks like this same CI5 concept was "
                 "also found, corroborating the consortium framing).",
    },
    {
        "shipping_line": "CEA", "service": "AIS", "direction": "single",
        "ports": [
            {"port": "Durban", "country": "South Africa"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Abu Dhabi", "country": "UAE"},
            {"port": "Ad Dammam", "country": "Saudi Arabia"},
            {"port": "Bahrain", "country": "Bahrain"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Port Louis", "country": "Mauritius"},
            {"port": "Durban", "country": "South Africa"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.shipinfo.net/find_vessel_Msc-India_IMO-9231248_MMSI-255806005",
        "notes": "Search results described this as MSC's own India-South Africa service (first "
                 "vessel MSC ROBERTA, voy IA317R) without giving it a plain-text 'AIS' label -- "
                 "'AIS' here is inferred to mean 'Africa India Service' or similar, matching this "
                 "rotation's shape, but that expansion is a guess. 'CEA' also not independently "
                 "confirmed as MSC's own code (used elsewhere in this pass on a COSCO/OOCL guess "
                 "instead, e.g. CEA/SEI2 and CEA/CIX3) -- both the naming match AND the carrier "
                 "identity are unconfirmed here, more so than most other entries in this file.",
    },
    {
        "shipping_line": "CSS", "service": "AIS", "direction": "single",
        "ports": [
            {"port": "Durban", "country": "South Africa"},
            {"port": "Jebel Ali", "country": "UAE"},
            {"port": "Abu Dhabi", "country": "UAE"},
            {"port": "Ad Dammam", "country": "Saudi Arabia"},
            {"port": "Bahrain", "country": "Bahrain"},
            {"port": "Mundra", "country": "India"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Hazira", "country": "India"},
            {"port": "Colombo", "country": "Sri Lanka"},
            {"port": "Port Louis", "country": "Mauritius"},
            {"port": "Durban", "country": "South Africa"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.shipinfo.net/find_vessel_Msc-India_IMO-9231248_MMSI-255806005",
        "notes": "See CEA/AIS above -- same rotation, same unconfirmed naming/carrier caveats.",
    },
    {
        "shipping_line": "CEA", "service": "SEI2", "direction": "single",
        "ports": [
            {"port": "Qinzhou", "country": "China"},
            {"port": "Yangpu", "country": "China"},
            {"port": "Haiphong", "country": "Vietnam"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Mundra", "country": "India"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Hong Kong", "country": "China"},
            {"port": "Qinzhou", "country": "China"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.linerlytica.com/post/cosco-adds-southeast-asia-india-service-2-sei2/",
        "notes": "COSCO/OOCL's own Southeast Asia India Service 2 (SEI2/SIS2), effective 4 June "
                 "2026 -- closed-loop, 35-day cycle, 5 ships of 3,300-4,400 TEU. 'CEA' not "
                 "independently confirmed as COSCO's or OOCL's own code, but is a plausible guess "
                 "given 'OCL' (used elsewhere in this file for OOCL) and 'CEA' both show up "
                 "against China-origin services in this pass.",
    },
    {
        "shipping_line": "CSS", "service": "SEI1", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Surabaya", "country": "Indonesia"},
            {"port": "Jakarta", "country": "Indonesia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/psa-mumbai-launches-sei1-service-to-strengthen-southeast-asia-india-trade-corridor/",
        "notes": "PSA Mumbai's own launch coverage (inaugural COSCO SHIPPING vessel, 9 Oct 2025) "
                 "names these five ports as the SEI1 corridor but does not give a call SEQUENCE -- "
                 "listed here in the order the source mentioned them, which is NOT confirmed as "
                 "the actual rotation order. 'CSS' not independently confirmed as the operating "
                 "carrier (the source doesn't name one beyond 'a COSCO SHIPPING vessel').",
    },
    {
        "shipping_line": "WHL", "service": "PMX", "direction": "single",
        "ports": [
            {"port": "Shanghai", "country": "China"},
            {"port": "Ningbo", "country": "China"},
            {"port": "Shekou", "country": "China"},
            {"port": "Hong Kong", "country": "China"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Karachi", "country": "Pakistan"},
            {"port": "Mundra", "country": "India"},
            {"port": "Port Klang", "country": "Malaysia"},
            {"port": "Singapore", "country": "Singapore"},
            {"port": "Hong Kong", "country": "China"},
            {"port": "Shanghai", "country": "China"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.seatrade-maritime.com/containers/four-container-lines-to-start-new-pmx-service",
        "notes": "4-carrier consortium (Coscon, Wan Hai -- 2 ships each -- plus CSCL and PIL, 1 "
                 "ship each), 6 vessels of 4,250 TEU -- 'WHL' is Wan Hai's own code, an explicitly "
                 "named operator, so the carrier identity here is solid even though the exact "
                 "double Port Klang call (West/North) is simplified to one repeated stop.",
    },
    {
        "shipping_line": "ARK", "service": "IMS2", "direction": "single",
        "ports": [
            {"port": "Istanbul (Marport)", "country": "Turkey"},
            {"port": "Gebze (Evyap)", "country": "Turkey"},
            {"port": "Izmir (Aliaga)", "country": "Turkey"},
            {"port": "Mersin", "country": "Turkey"},
            {"port": "Aqaba", "country": "Jordan"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Jeddah", "country": "Saudi Arabia"},
            {"port": "Aqaba", "country": "Jordan"},
            {"port": "Alexandria", "country": "Egypt"},
            {"port": "Istanbul (Marport)", "country": "Turkey"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://arkasline.com.tr/en/india/",
        "notes": "'ARK' = Arkas Line, whose own India Med Service (branded plain 'IMS' by Arkas "
                 "itself, not 'IMS2') launched 10 Feb 2025 -- 4-5 vessels of 2,500-2,800 TEU, "
                 "weekly. The trailing '2' in vessel_schedule's label isn't explained by anything "
                 "found (perhaps a leg/phase indicator); recorded Arkas's own single published "
                 "rotation since it's an unambiguous carrier match on every other detail.",
    },
    {
        "shipping_line": "HYN", "service": "GIA1", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Dar Es Salaam", "country": "Tanzania"},
            {"port": "Mombasa", "country": "Kenya"},
            {"port": "Nhava Sheva", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://theloadstar.com/new-liner-services-give-growing-india-africa-tradelane-a-welcome-boost/",
        "notes": "3-carrier consortium (HMM, COSCO, PIL) branded Gulf-India-East Africa (GIA), "
                 "35-day rotation -- 'HYN' plausibly HMM's own code (per this file's other HYN "
                 "entries). Applied cautiously to OCL/GIA2 below given the numbered-variant "
                 "ambiguity already seen elsewhere in this file (BIGEX/EPIC/MIDAS) -- GIA1 and "
                 "GIA2 may not be the same rotation.",
    },
    {
        "shipping_line": "OCL", "service": "GIA2", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Dar Es Salaam", "country": "Tanzania"},
            {"port": "Mombasa", "country": "Kenya"},
            {"port": "Nhava Sheva", "country": "India"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://theloadstar.com/new-liner-services-give-growing-india-africa-tradelane-a-welcome-boost/",
        "notes": "Same GIA consortium as HYN/GIA1 above (OCL = OOCL/COSCO family elsewhere in "
                 "this file, and COSCO IS a named GIA operator) -- but 'GIA2' as a distinctly-"
                 "numbered variant of 'GIA1' is NOT confirmed to share the exact same rotation; "
                 "see the BIGEX/EPIC precedent elsewhere in this file for why numbered variants "
                 "can differ. Treat this entry as the weaker of the two GIA entries.",
    },

    # --- (D) unresolved -- looked, no usable ordered rotation found ------
    {"shipping_line": "HLL", "service": "ME04", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Searches surfaced several other real Hapag-Lloyd Mediterranean-Middle East-ISC "
              "services (IMX, IOS, IO3, GEM, SE1, SE3, JD3) but nothing labeled 'ME04' specifically "
              "-- may be a newer internal code not yet covered by indexed trade press."},
    {"shipping_line": "LMC", "service": "INDME", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://indiashippingnews.com/tag/india-mediterranean-indme-service/",
     "notes": "Real, current service -- Ignazio Messina's India-Mediterranean (INDME), fortnightly "
              "(moving to weekly), inaugural vessel Jolly Rosa, maiden call at PSA Mumbai Sep 2025. "
              "'LMC' matches Messina's own container-prefix family (LMCU is their most-used "
              "prefix per one source) far better than any other code, so the carrier identity is "
              "fairly solid -- but no ordered port-by-port rotation was found, only the single "
              "confirmed call at Mumbai. Messina also runs a separate 'Red Sea Express' loop "
              "(JNPA-Sohar-Jeddah) -- don't conflate the two."},
    {"shipping_line": "MSK", "service": "MAWINGU", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://www.maersk.com/local-information/intra-imea-shipping-routes/mawingu-express",
     "notes": "Real, current Maersk service (weekly India-East Africa, several rotation revisions "
              "found dated 2020/2022/2024) -- one older description names Jawaharlal Nehru, "
              "Mesawa(sic), Durban and Colombo as ports served, but not in a confirmed call order, "
              "and given at least 2 known revisions since, likely stale. Left unresolved rather "
              "than guess an order or use a possibly-outdated one."},
    {"shipping_line": "SMI", "service": "JJS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result -- searches returned unrelated India-Sri Lanka coastal shipping "
              "news instead of a named 'JJS' container service."},
    {"shipping_line": "SMM", "service": "JJS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Same search, same non-result as SMI/JJS above."},
    {"shipping_line": "ASD", "service": "FEX", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result -- 'FEX' not found as a named Sea Consortium/X-Press service; "
              "neither 'ASD' identified as a carrier code."},
    {"shipping_line": "CEA", "service": "CI1", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://atlas.flexport.com/service/code:CMDU:CIMEX1",
     "notes": "Found CMA CGM's CIMEX1 (China India Middle East Express 1, Fujairah<->Shekou legs) "
              "as a similarly-named near-miss, but not confirmed as the same thing as a plain "
              "'CI1' label -- also found X-Press Feeders' own Chennai-Singapore-Colombo feeder "
              "service (with CMA CGM) as another candidate, again not an exact code match. Left "
              "unresolved rather than pick one on a guess."},
    {"shipping_line": "CSS", "service": "CI1", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Same non-match as CEA/CI1 above."},
    {"shipping_line": "CMA", "service": "CIMEX2K", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Ambiguous -- search found CIMEX2K2 and CIMEX2E as real CMA CGM variants, but "
              "neither is an exact match to plain 'CIMEX2K', and neither was confirmed to match "
              "Mundra/ACMTPL's specific port pattern for this label. Same multi-variant-code "
              "failure mode as BIGEX/EPIC/MIDAS elsewhere in this file."},
    {"shipping_line": "CMA", "service": "EPIC3", "direction": "single", "ports": [], "confidence": "unresolved",
     "source_url": "https://world.lines.coscoshipping.com/lines_resource/local/india/defaultContentAttachment/20260514/PAN%20INDIA%20LTS%20MAY%202026.pdf",
     "notes": "Same EPIC3 variant as COS/EPIC above (COSCO's own slot on it) -- known port SET "
              "(Nhava Sheva, Mundra, Jeddah, Tangier, Southampton, Rotterdam, Bremerhaven, "
              "Antwerp, Le Havre, Algeciras) but no confirmed call order, so not recorded as a "
              "guessed sequence. This is CMA CGM's own slot on the same consortium loop."},
    {"shipping_line": "COC", "service": "EPIC3", "direction": "single", "ports": [], "confidence": "unresolved",
     "source_url": "https://world.lines.coscoshipping.com/lines_resource/local/india/defaultContentAttachment/20260514/PAN%20INDIA%20LTS%20MAY%202026.pdf",
     "notes": "Same known port SET as CMA/EPIC3 and COS/EPIC above -- 'COC' likely another code "
              "for COSCO (COS's own code elsewhere in this file), given the literal 'EPIC3' string "
              "match to COS/EPIC's own already-documented COSCO slot."},
    {"shipping_line": "COC", "service": "AGI2", "direction": "single", "ports": [], "confidence": "unresolved",
     "source_url": "https://www.linerlytica.com/post/cosco-oocl-launch-asia-gulf-india-2-agi2/",
     "notes": "Same unresolved AGI2 ambiguity as COS/AGI2 above (conflicting original-vs-'UIG2'-"
              "replacement info, and a live terminal label that may lag a carrier rename) -- 'COC' "
              "likely another COSCO code, same underlying problem either way."},
    {"shipping_line": "MSC", "service": "FUJAIRAH SHUTTLE", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result across two separate search attempts -- searches kept returning "
              "MSC's Osprey (China-Southeast India) and Shikra services instead of anything "
              "specifically labeled a Fujairah shuttle."},
    {"shipping_line": "MSC", "service": "NEW FALCON", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://www.gocomet.com/transportation-and-logistics-industry-news/msc-discontinues-calls-to-indian-ports-on-its-falcon-service/",
     "notes": "CONTRADICTION found, same pattern as this file's existing MSK/SAFINA entry: the "
              "original (2015) Falcon rotation called Mundra and Nhava Sheva, but MSC's own March "
              "2023 revision explicitly DROPPED both Indian ports (new rotation runs Xingang-"
              "Busan-Qingdao-Shanghai-Ningbo-Xiamen-Shekou-Singapore-Jebel Ali-Abu Dhabi-Hamad-Ad "
              "Dammam-Umm Qasr-Abu Dhabi-Xingang, no India calls at all). Left unresolved rather "
              "than record a rotation MSC's own more recent advisory contradicts."},
    {"shipping_line": "MIL", "service": "MIX", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result -- no service named plain 'MIX' found for any carrier plausibly "
              "matching 'MIL' (tried Messina and Shipping Corporation of India)."},
    {"shipping_line": "MIM", "service": "MIX", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Same non-result as MIL/MIX above."},
    {"shipping_line": "MSK", "service": "NWX", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://www.scribd.com/document/690546797/North-China-India-West-Coast-X-PRESS-NWX-1",
     "notes": "Confirmed 'NWX' (North China India West Coast X-PRESS) is a real X-Press Feeders "
              "service (vessel X-Press Phoenix seen on it) -- see XPF's own entries elsewhere for "
              "that carrier's confirmed codes. No source found naming Maersk as an operator or "
              "slot-holder on this specific service, so NOT applied here; also couldn't retrieve "
              "an ordered port list even for X-Press's own slot (the source PDF's schedule table "
              "wasn't extractable via search)."},
    {"shipping_line": "UNF", "service": "WCC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": "https://www.unifeeder.com/feeder-asia-middle_east-africa",
     "notes": "'WCC' appears in Unifeeder's own service listings as one of their 'Domestic India "
              "Services' but without an accompanying rotation -- not confirmed whether this even "
              "calls Nhava Sheva/Mundra directly or is purely coastal Indian trans-shipment."},
    {"shipping_line": "EGI", "service": "MJI", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": "https://www.dpworld.com/en/news/india/dp-world-nhava-sheva-welcomes-new-weekly-mji-service",
     "notes": "MJI's own confirmed operators (per UNF/MJI above) are Unifeeder Group and ONE Line "
              "-- Evergreen (EGI) is not named as a joint operator by that source, so NOT assumed "
              "to share the rotation despite the exact service-name match."},
    {"shipping_line": "CMA", "service": "PIKEX", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://www.cma-cgm.com/ebusiness/schedules/line-services/flyer/PIKEX",
     "notes": "CONFIRMED this does not call India, in either version found: the original 'Pakistan "
              "Gulf Express' ran Karachi-Jebel Ali-Khalifa Port-Sohar-Karachi, and the revised (9 "
              "May 2025, post India-Pakistan tensions) rotation runs Jebel Ali-Khalifa-Karachi-"
              "Port Qasim-Colombo-Karachi-Jebel Ali -- neither touches an Indian port. CMA CGM's "
              "own advisory explains PIKEX was set up specifically to absorb the Pakistan-bound "
              "cargo that EPIC/MEDEX/INDAMEX/AS1 used to carry, once those services delinked "
              "Pakistan from India. Left unresolved rather than record a rotation that contradicts "
              "a real Mundra/Cochin/Chennai-side PIKEX call -- same pattern as MSK/SAFINA."},
    {"shipping_line": "CMA", "service": "PIKEX 2", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No source distinctly describing a separate 'PIKEX 2' (as opposed to the single "
              "PIKEX covered above) was found -- left unresolved rather than assume it's the same "
              "service as plain PIKEX."},
    {"shipping_line": "CMA", "service": "BIGEX2", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "CCA/BIGEX and CMA/BIGEX above are already flagged as one unidentified variant among "
              "CMA CGM's known BIGEX-1/2/3/4 family -- since it isn't confirmed WHICH variant "
              "those entries actually cover, this explicitly-numbered 'BIGEX2' can't be safely "
              "assumed to be the same one. Left unresolved rather than guess."},
    {"shipping_line": "MSI", "service": "MIDAS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "CCA/MIDAS above is CMA CGM's own MIDAS 1 -- 'MSI' not independently confirmed as "
              "CMA CGM or a joint-slot partner, so not assumed to share that rotation (same "
              "reasoning this file already applies to MSK/MIDAS above)."},
    {"shipping_line": "MSI", "service": "MIDAS2", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Same reasoning as MSI/MIDAS above, against CMA/MIDAS2's now-documented rotation."},
    {"shipping_line": "CUL", "service": "CSC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result -- 'CSC' returned only generic China-India freight-forwarder "
              "listings and old CSCL (China Shipping Container Lines) vessel-name trivia, nothing "
              "matching a current named loop. Same non-result for CUS/CSC, HUE/CSC, SIR/CSC and "
              "SNK/CSC below -- recorded separately since carrier identity differs across all five."},
    {"shipping_line": "CUS", "service": "CSC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See CUL/CSC above."},
    {"shipping_line": "HUE", "service": "CSC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See CUL/CSC above."},
    {"shipping_line": "SIR", "service": "CSC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See CUL/CSC above."},
    {"shipping_line": "SNK", "service": "CSC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See CUL/CSC above."},
    {"shipping_line": "MOL", "service": "PCC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result -- 'PCC' returned only Pakistan International Container Terminal "
              "and unrelated PCC-branded logistics companies, nothing matching a named MOL/NYK/ULA "
              "consortium loop. Same non-result for NYK/PCC and ULA/PCC below."},
    {"shipping_line": "NYK", "service": "PCC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See MOL/PCC above."},
    {"shipping_line": "ULA", "service": "PCC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See MOL/PCC above."},
    {"shipping_line": "BTL", "service": "TTX", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Confirmed real -- a direct Vietnam/Thailand-to-Indian-east-coast route that "
              "started around April, in the same period Wan Hai was expanding regional capacity "
              "-- but no ordered port list was found. 'BTL' (Bengal Tiger Line) is a plausible "
              "operator given its other consortium appearances in this file (RWA family)."},
    {"shipping_line": "WAN", "service": "TTX", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See BTL/TTX above."},
    {"shipping_line": "RCL", "service": "RWP", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://www.linerlytica.com/post/rcl-launch/",
     "notes": "Near miss: found RCL's own West India-Gulf (RWG) service (Mundra-Nhava Sheva-Jebel "
              "Ali-Umm Qasr-Mundra, 21-day turn, launched Oct 2024) -- but 'RWG' is not an exact "
              "match to vessel_schedule's 'RWP' label. Could be the same service under a terminal-"
              "side typo/variant, or a genuinely different one; left unresolved rather than guess "
              "which."},
    {"shipping_line": "RCL", "service": "IMI", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://www.npct1.co.id/npct1-welcomes-rcl-rga3-service-connecting-jakarta-to-india-and-middle-east-1724329982",
     "notes": "Near miss: found RCL's own RGA3 (Cai Mep-Jakarta-Port Klang-Mundra(MICT)-Jebel Ali-"
              "Dammam-Mundra(Adani)-Port Klang-Laem Chabang), which does connect India/Malaysia/"
              "Indonesia/Middle East -- but 'RGA3' isn't an exact match to 'IMI' either. Left "
              "unresolved rather than guess."},
    {"shipping_line": "CCA", "service": "KMAMBO", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://www.maritimegateway.com/cma-cgm-revamps-india-east-africa-container-network-for-better-reliability/",
     "notes": "Very likely a terminal-side abbreviation of CMA CGM's own 'KANIMAMBO' service (a "
              "Mozambique-focused loop via Colombo, part of a March 2026 India/Middle East/East "
              "Africa network reshuffle that also upgraded a separate 'KARIBU' service to call "
              "Mundra and Cochin directly) -- but no ordered port list specific to KANIMAMBO/"
              "KMAMBO was found, only that it exists and its general purpose."},
    {"shipping_line": "CLANGA", "service": "MSC", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Almost certainly a data-quality artifact rather than a real (shipping_line, "
              "service) pair -- 'CLANGA' isn't a recognizable carrier code and 'MSC' as a SERVICE "
              "name (rather than carrier) strongly suggests the source report had shipping_line "
              "and service transposed, or 'CLANGA' is itself a mis-scraped service name (e.g. a "
              "vessel named similarly) with MSC as the real carrier. Not researched as if it were "
              "a genuine named loop; worth checking against the raw source report before trusting "
              "this combination at all."},
    {"shipping_line": "DMA", "service": "ISX", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Confirmed real -- one source described 'the ISX service operating on a 14-day "
              "rotation covering Mundra and Nhava Sheva' -- but named only those two ports, not a "
              "full ordered rotation (likely a short India-coastal or India-Gulf loop). Not "
              "recorded as a two-port 'rotation' since that would misrepresent an incomplete list "
              "as a complete one."},
    {"shipping_line": "HUB", "service": "MIREX", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "No usable result found."},
    {"shipping_line": "ELP", "service": "FIE", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "No usable result found."},
    {"shipping_line": "FOS", "service": "FBS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result found. Same for FOS/FIL below."},
    {"shipping_line": "FOS", "service": "FIL", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See FOS/FBS above."},
    {"shipping_line": "EMS", "service": "IXS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result -- distinct from DMA/ISX above (different letter order); not "
              "assumed to be the same service."},
    {"shipping_line": "MBK", "service": "IMS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Two near-miss candidates found, neither confirmed: Wan Hai/Unifeeder's own joint "
              "'IMS/IM1' service (India-Middle East, Jebel Ali-focused), and X-Press Feeders' "
              "'Malabar X-Press (MBX)' shuttle (Colombo-New Mangalore-Cochin-Colombo) -- the "
              "latter's 'MBX' code is suggestively close to 'MBK' but that's a weak basis alone. "
              "Left unresolved rather than pick one."},
    {"shipping_line": "MBK", "service": "IMSW", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See MBK/IMS above -- same candidates, same caveat."},
    {"shipping_line": "ONE", "service": "C13", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "No usable result found."},
    {"shipping_line": "OIL", "service": "CI3", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "No usable result found."},
    {"shipping_line": "PCI", "service": "CVI", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "No usable result found."},
    {"shipping_line": "SNL", "service": "FIX1", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "No usable result found."},
    {"shipping_line": "FZE", "service": "NRS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "No usable result found. Same for FZE/SRS below."},
    {"shipping_line": "FZE", "service": "SRS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None, "notes": "See FZE/NRS above."},
    {"shipping_line": "FZE", "service": "EVGI", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://atlas.flexport.com/service/code:EPIR:EVGI",
     "notes": "Confirmed real -- Flexport Atlas lists an EPIR:EVGI 'Vietnam Gulf India Service', "
              "operated by Emirates per that listing -- but no port-by-port rotation was "
              "retrievable (Atlas's own API responses are encrypted and not scraped -- see the "
              "module docstring's note on that). 'FZE' plausibly an Emirates-family code (see "
              "FZE/CSX2 and FZE/EA2 above) but not confirmed for this specific service."},
    {"shipping_line": "SMM", "service": "EVGI", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": "https://atlas.flexport.com/service/code:EPIR:EVGI",
     "notes": "See FZE/EVGI above -- same real-but-rotation-unavailable service."},

    # --- non-loop pseudo-ADHOC labels (distinct strings from plain
    # "ADHOC", so not picked up by ADHOC_LINES -- same no_fixed_rotation
    # treatment, recorded explicitly so each looks researched rather than
    # skipped) ------------------------------------------------------------
    {"shipping_line": "OIL", "service": "ADHC", "direction": "single", "ports": [],
     "confidence": "no_fixed_rotation", "source_url": None,
     "notes": "'ADHC' is the same kind of terminal-side unscheduled-call label as 'ADHOC' "
              "elsewhere in this file (see ADHOC_LINES) -- just abbreviated differently here. No "
              "fixed rotation to research."},
    {"shipping_line": "SMI", "service": "ADHOC/MSC", "direction": "single", "ports": [],
     "confidence": "no_fixed_rotation", "source_url": None,
     "notes": "Compound unscheduled-call label (literally 'ADHOC/MSC') -- same no_fixed_rotation "
              "reasoning as plain 'ADHOC' elsewhere in this file."},
    {"shipping_line": "TCC", "service": "ADHC", "direction": "single", "ports": [],
     "confidence": "no_fixed_rotation", "source_url": None,
     "notes": "See OIL/ADHC above -- same label, different line."},
    {"shipping_line": "TIS", "service": "FEEDER", "direction": "single", "ports": [],
     "confidence": "no_fixed_rotation", "source_url": None,
     "notes": "Generic 'FEEDER' label -- same unscheduled/non-loop reasoning as 'ADHOC' elsewhere "
              "in this file, just named differently by this terminal."},
    {"shipping_line": "WAN", "service": "ADHC", "direction": "single", "ports": [],
     "confidence": "no_fixed_rotation", "source_url": None,
     "notes": "See OIL/ADHC above -- same label, different line. Distinct from plain 'WAN'/'ADHOC' "
              "(already in ADHOC_LINES) -- this is the differently-spelled 'ADHC' variant."},

    # --- final stragglers found only after a first coverage-diff pass ---
    {
        "shipping_line": "ONE", "service": "MIAX", "direction": "single",
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
        "notes": "Same MIAX rotation as HLI/MIAX, HLL/MIAX and OCE/MIAX above, applied on the same "
                 "identical-service-name basis -- 'ONE' is a real carrier (Ocean Network Express) "
                 "but not independently confirmed as a joint-slot holder on Hapag-Lloyd's MIAX. "
                 "Same caution as OCE/MIAX applies.",
    },
    {
        "shipping_line": "SSP", "service": "KIX", "direction": "single",
        "ports": [
            {"port": "Nhava Sheva", "country": "India"},
            {"port": "Mundra", "country": "India"},
            {"port": "Khorfakkan", "country": "UAE"},
        ],
        "confidence": "needs_verification",
        "source_url": "https://www.maritimegateway.com/gt-lines-kix1-weekly/",
        "notes": "Same GT Lines KIX 1 rotation as SMD/KIX and DMA/KIX above -- 'SSP' not "
                 "independently confirmed as GT Lines' own or a partner's code, same caveat as "
                 "those two entries.",
    },
    {"shipping_line": "NIL", "service": "TIP", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Same non-result as this file's existing AKS/TIP entry -- searches keep surfacing "
              "Hapag-Lloyd's differently-coded TPI/INDAMEX instead of a plain 'TIP' service; 'NIL' "
              "not identified as a carrier."},
    {"shipping_line": "PID", "service": "RGS", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": None,
     "notes": "Odd combination worth flagging: 'RGS' is itself one of the shipping_line codes in "
              "ADHOC_LINES elsewhere in this file (i.e. normally a CARRIER code, not a service "
              "name) -- this row has 'PID' as the line and 'RGS' as the service, which may be a "
              "genuine service coincidentally sharing a string with another line's code, or a "
              "data-quality artifact similar to CLANGA/MSC above. Not researched as a real named "
              "loop without first checking the raw source report."},
    {"shipping_line": "UNF", "service": "ECH", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": "https://www.unifeeder.com/hubfs/UFISC%20Feeder%20Services%20Routes%20maps%202025%2007%2005.pdf?hsLang=en",
     "notes": "Confirmed as a real code in Unifeeder's own published Asia/Middle East/Africa "
              "service-overview PDF, but no rotation was extractable from a search snippet of that "
              "document -- would need the PDF opened directly to confirm ports."},
    {"shipping_line": "UNF", "service": "FME", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": "https://www.unifeeder.com/hubfs/UFISC%20Feeder%20Services%20Routes%20maps%202025%2007%2005.pdf?hsLang=en",
     "notes": "See UNF/ECH above -- same source, same limitation."},
    {"shipping_line": "UNF", "service": "PIC2", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": "https://www.unifeeder.com/hubfs/UFISC%20Feeder%20Services%20Routes%20maps%202025%2007%2005.pdf?hsLang=en",
     "notes": "See UNF/ECH above -- same source, same limitation."},
    {"shipping_line": "UNF", "service": "RGI", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": "https://www.linerlytica.com/post/x-press-feeders-feedertech-and-wan-hai-team-up-for-new/",
     "notes": "SEC/RGI and XPF/RGI above already document this service's rotation (X-Press "
              "Feeders/Sea Consortium + Feedertech + Wan Hai) -- Unifeeder is not named as a joint "
              "operator by that source, so not assumed to share it despite the exact service-name "
              "match."},
    {"shipping_line": "UNF", "service": "SEI1", "direction": "single", "ports": [],
     "confidence": "unresolved", "source_url": "https://www.maritimegateway.com/psa-mumbai-launches-sei1-service-to-strengthen-southeast-asia-india-trade-corridor/",
     "notes": "CSS/SEI1 above already documents the ports named for this service -- that source "
              "names only 'a COSCO SHIPPING vessel' for the inaugural call, not Unifeeder, so not "
              "assumed to share it despite the exact service-name match."},
    {"shipping_line": "XPF", "service": "ASX GULF", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://www.aseanlines.com/Show.aspx?id=544",
     "notes": "Confirmed real -- X-Press Feeders' own ASX (UAE-Gulf India service), one of four "
              "weekly Middle East Gulf-West India box services X-Press jointly runs with Simatech "
              "and OEL; slot-chartered by Cosco, Hapag-Lloyd and Evergreen. No ordered port list "
              "found for ASX specifically -- a related but DIFFERENT X-Press service found in the "
              "same search, India Middle East X-Press (IMEX: Mundra-Nhava Sheva-Jebel Ali-Dammam-"
              "Umm Qasr-Mundra), was NOT assumed to be the same rotation since both are explicitly "
              "named as separate services in the source.",
    },
    {"shipping_line": "XPF", "service": "NWX", "direction": "single", "ports": [],
     "confidence": "unresolved",
     "source_url": "https://www.scribd.com/document/690546797/North-China-India-West-Coast-X-PRESS-NWX-1",
     "notes": "X-Press Feeders' own North China India West Coast X-PRESS service (vessel X-Press "
              "Phoenix seen on it, per its own vessel schedule document) -- carrier identity is "
              "solid (this is literally XPF's own service), but the ordered port list wasn't "
              "extractable from that document via search. See also MSK/NWX above (same service "
              "name, Maersk not confirmed as an operator on it).",
    },
]
