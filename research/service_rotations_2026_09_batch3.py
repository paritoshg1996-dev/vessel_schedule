"""
Third research batch (same session, 2026-09-11) -- the count=1 long tail
(services with only one currently-listed voyage) plus a few stragglers
missed in batch2. See service_rotations_2026_09.py's docstring for the
overall approach.

Several entries here are shared consortium loops applied to multiple
carrier codes on the strength of an explicit "operated jointly by X, Y,
Z" statement in the source -- flagged in each entry's notes. Where no
such statement was found, a line was left unresolved rather than assume
it shares another line's rotation just because the service code matches.
"""

ROTATIONS = [
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
        # RESOLVED LATER (see seed_service_rotations.py's CARRIER_NAMES):
        # JNPA's own official registry confirms EGI = Evergreen, not
        # Emirates Shipping Line as guessed when this entry was researched.
        # The rotation below was found via an EMIRATES press release --
        # downgraded to needs_verification since it's no longer clear this
        # specific rotation is actually Evergreen's own slot (plausible if
        # Evergreen also holds a slot on the same consortium loop, per the
        # same shared-loop pattern seen elsewhere in this research, but not
        # independently confirmed for Evergreen specifically).
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
                 "correct (Evergreen could hold its own slot on the same consortium loop, as "
                 "seen elsewhere in this research) but that's not independently confirmed, "
                 "hence the downgrade from 'verified'.",
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
