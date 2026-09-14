# Service rotation research — coverage notes (updated 2026-09-14, second pass)

## What this is

`service_rotations` is reference data (which ports a named carrier service
loop calls at, in order) that a vessel's onward journey from JNPT is
computed against — see `models.ServiceRotation` and `pipeline/rotations.py`
for the schema and join logic. It is **not** scraped from JNPT; no port's
berthing report publishes a vessel's rotation beyond its own call.

**Directionality**: some services run a genuinely different port set/order
eastbound vs westbound, not just each other's reverse (e.g. an extra
transshipment call on only one leg). `ServiceRotation` is keyed by
`(shipping_line, service, direction)`, so these get two rows, not one —
see the model's own docstring. Confirmed directional splits found this
pass: **CCA/BIGEX**, **GSL/NIX**, and (a genuine round-trip visiting JNPT
twice, only partially resolved) **HMM/FIM-W**.

## Coverage

Of the **97 distinct (shipping_line, service) combinations** currently in
`vessel_schedule` (expected status):

- **74 of 97** now have at least one `service_rotations` row (up from
  26 — 8 researched + 18 ADHOC — at the start of this pass).
- **23 combinations remain completely unresearched**: `RCL/RWP`,
  `MIL/MIX`, `LMC/INDME`, `MBK/IMSW`, `SIR/CSC`, `EGI/MJI`, `MSC/IAS`,
  `SMM/JJS`, `MSK/MW2`, `CSS/SEI1`, `AKS/EAS`, `ECL/IG1`, `CSS/AIS`,
  `UNF/SEI1`, `ESA/EA2`, `MIL/MGX`, `CCA/KMAMBO`, `CSS/CI1`, `CUL/CSC`,
  `ONE/MIAX`, `UNF/MJI`, `HUE/CSC` — mostly single-voyage, harder-to-find
  codes where a search turned up nothing usable at all.

76 rows total across those 74 combos (a few have 2 directional rows).

## Confidence breakdown (76 rows)

| Confidence | Count | Meaning |
|---|---|---|
| `needs_verification` | 38 | Found via search synthesis, not cross-checked against a primary carrier source |
| `unresolved` | 17 | Looked, found nothing usable OR found a rotation that contradicts JNPT's own data (doesn't call Nhava Sheva at all) |
| `verified` | 12 | Matched a carrier's own press release/page, reasonably current |
| `no_fixed_rotation` | 11 | "ADHOC" lines — genuinely no fixed loop, not a research gap |

**Read `verified` conservatively**: it means "found in the carrier's own
official announcement," not "confirmed live against a current schedule
database." Carrier sites and the one aggregator tried (Flexport Atlas)
both return HTTP 403 to automated fetches, so nothing here came from a
direct primary-source read — every result is search-summary synthesis.

## Real failure modes hit, by category

- **Rotation genuinely doesn't include JNPT.** `UNF/AGI`, `EGI/AGI`,
  `MSK/SAFINA`, `COS/AGI2` (from the first pass) all have a real, findable
  published rotation — that simply never calls Nhava Sheva — despite a
  real, currently-arriving voyage in `vessel_schedule` using that exact
  (line, service). Left `unresolved` rather than record a contradicted
  rotation. This is the single most common reason for `unresolved`.
- **Multiple similarly-named variants, JNPT's label doesn't say which.**
  `CCA/BIGEX` (1/2/3/4), `CCA/EPIC` (EPIC1 vs EPIC2 vs COSCO's own EPIC3),
  `CCA/MIDAS` (MIDAS1 vs MIDAS2), `SEC/CWX` (vs TS Lines' differently-owned
  CWX2). Recorded the variant that's confirmed to call Nhava Sheva where
  more than one exists, flagged in `notes`.
- **Carrier identity assumed from context, not confirmed.** `EGI` was
  first guessed as Evergreen (via a Flexport SCAC match on `AGI`), then
  contradicted by later evidence (`EGI/CSX`, `EGI/CISC` line up with
  Emirates Shipping Line's own launches instead). Left both possibilities
  noted rather than silently "corrected" one over the other.
- **Consortium loops shared across carrier brands.** The RWA/CIX/CISC/SI8/
  CI6/VGI/CWX families are the same handful of physical loops, each
  carrier partner logging JNPT's report under its own code name. Applied
  the same rotation to multiple lines ONLY where a source explicitly
  named the joint operators (e.g. Wan Hai + Hapag-Lloyd + Evergreen on
  CIX) — never assumed sharing just because two lines used the same
  service string.
- **One discarded hallucination.** `ONE/PS3`'s first search returned an
  implausible 14-port loop spanning India, SE Asia, East Asia, and the US
  West Coast — almost certainly a conflation of multiple distinct ONE
  services. Discarded entirely rather than recorded.
- **A round trip that visits JNPT twice.** `HMM/FIM-W` is one 84-day loop
  that calls Nhava Sheva on both the outbound and return leg. JNPT's own
  "-W" (westbound) label implies it distinguishes which leg a given
  voyage is on, but the source didn't make clear which of the two Nhava
  Sheva calls that corresponds to — recorded a best guess, flagged as
  the least confident entry in the whole set.

## Displaying confidence (for whoever builds the UI/API layer next)

`pipeline/rotations.py` has a module-level `EXPOSE_CONFIDENCE` flag,
currently `True` — `rotation_summary()` includes `confidence`,
`source_url`, and `notes` in its output while this data is still being
built out and spot-checked. Flip it to `False` once the build is
considered finalized, to show a clean "next ports" list without the
research caveats attached; nothing about the underlying stored data
changes, only what gets exposed downstream.

## Carrier-name decoding (added 2026-09-11)

`shipping_line_name` (a new column on `service_rotations`) decodes the
abbreviation, using JNPA's own official "List of Shipping Agencies
Registered" (a Sr.No./Id/Name/SCAC/BIC table published at
`jnport.gov.in/uploads/content_manager/shipping_Agencies.pdf`) as the
primary source — see `seed_service_rotations.py`'s `CARRIER_NAMES` for
the full mapping and per-entry citations. **29 of 36** distinct line
codes now have a name; 7 remain unidentified (`AKS`, `EMT`, `RGS`,
`SBB`, `SMD`, `TST`, `WAN` — `TST` in particular turned out to be a
dummy/test entry in the registry itself, not a real carrier).

This also **corrected a mistake**: `EGI` was earlier guessed as Emirates
Shipping Line from circumstantial evidence (the `CSX`/`CISC` rotations
were found via Emirates' own press releases). The official registry
instead lists `EGI1` as "EVERGREEN SHIPPING AGENCY (INDIA)" — confirmed
as Evergreen. `EGI/CSX`'s confidence was downgraded from `verified` to
`needs_verification` accordingly, since the rotation itself was found
under the wrong carrier's announcement and hasn't been independently
confirmed as Evergreen's own slot.

## Second pass (2026-09-14): adding Mundra, Cochin, Chennai

Once vessel data existed for all four ports, the pool of distinct
`(shipping_line, service)` combinations grew from JNPT's original 97 to
**193** — 128 of them genuinely new (not just the same JNPT-era service
reappearing at a second port). This pass researched that backlog using
the same method as the first pass (public web search + manual synthesis
+ confidence tiering — explicitly **not** a fleet of per-carrier
scrapers; see the reasoning below).

### Why a research queue, not scrapers

Before this pass, individual carrier "vessel schedule" search tools
(Maersk, MSC) and Flexport Atlas were live-tested as a possible
automated data source for onward-rotation data:

- **Maersk's schedule search** is built from web components with an
  **open shadow DOM** — real `<input>` elements live inside
  `shadowRoot`, invisible to normal accessibility-tree tooling and only
  reachable via direct JS DOM-piercing, and even then a submitted search
  produced a broken "undefined" result without a real autocomplete-
  selection flow. Fragile, not a serious automation target.
- **MSC's schedule search** is a plain HTML form with working
  autocomplete and a clean results table — the easiest of the three to
  drive — and MSC also advertises an official "MSC Integration Suite"
  API as an alternative to the web form.
- **Flexport Atlas** loads fine through a real browser and its vessel
  search resolves a name to a real IMO/MMSI with a "Past/Upcoming port
  calls" tab that cross-validated MSC's own tool on a real vessel
  (MSC NAOMI) — but its underlying `/api/v1/public/...` REST endpoints
  return **encrypted ciphertext bodies**, not plain JSON, decryptable
  only by Flexport's own front-end JS, and its own Terms of Use
  explicitly prohibit both automated/bulk access AND circumventing
  "encryption ... protecting ... APIs and datasets." Ruled out entirely
  — both a technical wall and an explicit contractual one.
- A live spot-check also surfaced **vessel reassignment**: our own
  scraped `service` label for a real vessel can lag which named service
  that vessel is *currently* assigned to (confirmed for both MSC NAOMI
  and MSC BARBARA against Atlas's and MSC's own live tools — see the
  research file's module docstring). A live single-vessel lookup is
  therefore not a reliable stand-in for "what is service X's rotation,"
  since the vessel and the service can drift apart independently.

Given the stated real-world cadence (rotation data changes rarely —
once a day at most, only for newly-added vessels), none of this
justifies unattended per-carrier browser automation. The plan instead:
an occasional research queue (this pass, and future ones like it) using
WebSearch + manual synthesis, the same low-tech method that produced
the original 97-combo pass — plus free self-inference already available
from the pipeline's own multi-port data (the same vessel/voyage observed
at two of the four ports in a plausible sequence needs no external
lookup at all) — with light carrier-specific automation (MSC being the
best candidate, by data volume and how clean its form is) considered
only later, and only if manual pace actually becomes a bottleneck.

### New patterns hit this pass

- **Cross-port carrier-code duplication.** The same global carrier can
  have a *different* local agent code at JNPT vs at Mundra/Cochin/
  Chennai — confirmed for CMA CGM (`CCA` at JNPT / `CMA` elsewhere),
  Hapag-Lloyd (`HLI` / `HLL`), and X-Press Feeders (`SEC` / `XPF`), and
  suspected for several more (Interasia: `ISL` / `INT`; KMTC: `KMD` /
  `KMT`). Where the *service name* matched exactly, this pass reused the
  first pass's rotation directly rather than re-researching — the
  service name, not the local agent code, is the stable cross-port
  matching key, consistent with how carriers coordinate service
  branding globally while local port agents don't share a code registry.
- **More numbered-variant ambiguity, layered on the first pass's own.**
  Mundra's data adds even more specific numbered labels on top of
  JNPT's already-ambiguous unnumbered ones — `EPIC3`, `CIMEX2K`,
  `MIDAS2`, `PIKEX`/`PIKEX 2`, `BIGEX2`, `AGI2`/`GIA1`/`GIA2` — that
  sometimes *resolve* JNPT's own ambiguity (e.g. `CMA/MIDAS2` turned up
  a clean, current, well-sourced rotation distinct from `CCA/MIDAS`'s
  MIDAS-1) and sometimes just add a fresh layer of it (`CIMEX2K` matched
  neither `CIMEX2K2` nor `CIMEX2E`, the two real variants found;
  `PIKEX`'s own confirmed rotation doesn't call India *at all*, in
  either of two versions checked — same "found it, it contradicts the
  data" pattern as `MSK/SAFINA` in the first pass).
- **Cochin structurally contributes nothing to this analysis.** The
  IGTPL scraper (`scrapers/cochin_igtpl.py`) never captures a `service`
  field — only `shipping_line` — so Cochin adds zero new
  `(shipping_line, service)` combinations of its own; all 128 new combos
  this pass came from Mundra and Chennai. Cochin's own "CVIA/Next Port"
  field remains a separate, unmapped, promising lead for a future pass.

### Coverage

Of the **193 distinct (shipping_line, service) combinations** now live
in `vessel_schedule` across all four ports:

- **All 193 (100%)** now have at least one `service_rotations` row —
  up from 75 (74 real combos + `ADHOC`-family coverage, counted the
  first pass's way) before this pass started.
- Of the **128 combos that were genuinely new** this pass: 51 got a
  real or reused rotation (`verified`/`needs_verification`), 5 got the
  `no_fixed_rotation` treatment (non-loop pseudo-`ADHOC` labels like
  `ADHC`/`FEEDER`), 6 lines were added to `ADHOC_LINES` outright (`ECL`,
  `EMC`, `MSC`, `MSI`, `RCF`, `SMI`), and **66 stayed `unresolved`** —
  looked, and either found nothing usable, found a rotation that
  contradicts the data (same pattern as `MSK/SAFINA`/`CMA/PIKEX`), or
  found a near-miss code that couldn't be confirmed as the same service
  (e.g. `RCL/RWP` vs the real `RWG` service found, `RCL/IMI` vs `RGA3`).
  "100% coverage" here means **100% of combos have been looked at and
  recorded honestly**, not that 100% have a confirmed ordered rotation
  — treat `unresolved` exactly as its name says.

189 rows total across those combos (a few, e.g. `HYN/FIM(E)`/`FIM(W)`,
have 2 directional rows).

## Confidence breakdown (189 rows, both passes combined)

| Confidence | Count | Meaning |
|---|---|---|
| `needs_verification` | 89 | Found via search synthesis, not cross-checked against a primary carrier source |
| `unresolved` | 79 | Looked, found nothing usable OR found a rotation that contradicts the data (doesn't call an expected Indian port at all) |
| `verified` | 16 | Matched a carrier's own press release/page, reasonably current, often corroborated by multiple independent sources |
| `no_fixed_rotation` | 5 | Non-loop pseudo-`ADHOC` labels (`ADHC`, `FEEDER`, `ADHOC/MSC`) — genuinely no fixed loop, on top of the 17-line `ADHOC_LINES` family covering plain `ADHOC` |

**Read `verified` conservatively**, same caveat as the first pass:
found in the carrier's own official announcement, not confirmed live
against a current schedule database.

## New failure modes hit this pass (in addition to the first pass's own)

- **A rotation confirmed to actively contradict the data.** `CMA/PIKEX`
  is the clearest case: CMA CGM's own page gives two successive
  versions of this rotation (pre- and post-May-2025), and **neither
  touches an Indian port** — CMA CGM's own advisory explains PIKEX was
  set up specifically to absorb Pakistan-bound cargo that other
  services (`EPIC`/`MEDEX`/`INDAMEX`/`AS1`) used to carry before
  delinking Pakistan from India entirely. Same treatment as the first
  pass's `MSK/SAFINA`: left `unresolved` rather than record a rotation
  that contradicts a real observed call.
- **Near-miss codes that couldn't be confirmed as the same service.**
  `RCL/RWP` (real service found: `RWG`), `RCL/IMI` (real service found:
  `RGA3`), `CCA/KMAMBO` (real service found: `KANIMAMBO`) — each close
  enough to suspect a terminal-side abbreviation or typo, not close
  enough to treat as confirmed. Recorded the near-miss as a lead in
  `notes` rather than silently substituting it.
- **A likely data-quality artifact.** `CLANGA/MSC` (shipping_line
  "CLANGA", service "MSC") and `PID/RGS` (service name matching another
  line's *own* code elsewhere in `ADHOC_LINES`) both look more like a
  scraper field-mapping slip than a real named service — flagged as
  such rather than researched as if they were genuine loops.
- **A real service, but the operator doesn't match on every branch.**
  `UNF/MJI`'s rotation is solid (Unifeeder + ONE Line, per DP World's
  own announcement) — but the *same* exact service name also shows up
  as `EGI/MJI`, and Evergreen isn't named as a joint operator anywhere,
  so `EGI/MJI` was left `unresolved` rather than assumed to share it.
  Same pattern recurred for `UNF/RGI` vs `SEC/RGI`+`XPF/RGI`, and
  `UNF/SEI1` vs `CSS/SEI1` — matching service *names* across
  differently-coded lines is a lead, never proof of shared operation.
- **A rotation resolved by the extra port, not despite it.** `EMC/AGI`
  reuses the exact rotation that `UNF/AGI`/`EGI/AGI` recorded as
  `unresolved` at JNPT — *because* that rotation skips Nhava Sheva
  entirely. It does call Mundra, though, so the same rotation that was
  a contradiction at JNPT is actually consistent with the data at
  Mundra. Recorded as `needs_verification` there instead of inheriting
  the `unresolved` status by default.

## Next steps (not yet done)

- Spot-check `needs_verification` entries before treating any of them
  as reliable — especially the ones flagged with an unconfirmed
  carrier-code correspondence (`OCE/MIAX`, `ONE/MIAX`, `ECL/IG1`,
  `CEA/CIX3`, `CEA/AIS`/`CSS/AIS`, `FZE/CSX2`) rather than a confirmed
  one.
- The 79 `unresolved` combos remain open for a future pass, particularly
  the ones with a documented near-miss lead already in `notes` (`RCL/
  RWP`, `RCL/IMI`, `CCA/KMAMBO`, `MBK/IMS`/`IMSW`) — those are the
  cheapest to close out next since the likely real service is already
  identified, just not confirmed.
- Consider actually opening the two Unifeeder PDFs cited in the `UNF/
  ECH`, `UNF/FME`, `UNF/PIC2` and `UNF/WCC` entries directly (rather
  than relying on search snippets of them) — they're confirmed to
  contain the answer, just not extracted from it yet.
- Wire `service_rotations` + `rotation_summary()` into
  `pipeline/mongo_export.py` (e.g. a `rotation` field added to each
  exported `vessel_schedule` document) so the app backend and website can
  actually display this.
- Re-run `seed_service_rotations.py` periodically (not on the hourly
  scrape schedule — rotations change rarely) and reconcile entries whose
  `last_seen_in_schedule_at` goes stale (the service dropped out of
  current data at every port that used to report it).
- `models.ServiceRotation`'s `jnpt_index` field name is JNPT-specific
  naming left over from when this table only covered one port — now
  that it spans four, the name is a real (if cosmetic) wrinkle worth
  fixing whenever the schema next gets touched, e.g. to a
  port-agnostic `sequence_index` or similar.
