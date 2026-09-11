"""
Second research batch (same session, 2026-09-11), covering essentially
all remaining (shipping_line, service) combos with 2+ currently-listed
voyages, plus a couple of 1-voyage combos caught along the way. See
research/service_rotations_2026_09.py's docstring for the overall
approach and models.ServiceRotation for what each field means.

Same access constraints as the first batch: carrier sites and Flexport
Atlas both 403 automated fetches, so everything here is search-summary
synthesis, not a direct primary-source read.

DIRECTIONALITY: several services here (RWA-family, CIX-family, FIM-W)
are consortium/pendulum services shared across multiple carrier brands
on the same physical vessels/loop -- e.g. the same underlying rotation
gets called "RWA" by RCL, "RWA" by PIL/ECL (shared), and "CIX" by Wan
Hai. Where the full round-trip already reads as one continuous cycle
(most of these), direction="single" is correct -- the "eastbound" and
"westbound" halves are just two arcs of the same loop, both captured by
recording the whole thing in call order. HMM's FIM-W is the one case
here where the JNPT label itself is direction-specific and the source
describes a full out-and-back round trip visiting Nhava Sheva TWICE --
see its own notes for why that couldn't be cleanly split.
"""

ROTATIONS = [
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
                 "non-JNPT-calling rotation problem as UNF/AGI above. CAVEAT ADDED LATER: "
                 "batch3's research (EGI/CSX, EGI/CISC) makes it more likely 'EGI' actually "
                 "means Emirates Shipping Line, not Evergreen -- this entry's Evergreen "
                 "attribution is now doubtful, though it doesn't change the outcome (still "
                 "unresolved either way).",
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
                 "treat this one as the least confident 'needs_verification' entry in this batch.",
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
]
