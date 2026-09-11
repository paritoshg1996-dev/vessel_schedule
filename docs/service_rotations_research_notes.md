# Service rotation research — coverage notes (updated 2026-09-11, full pass)

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

## Next steps (not yet done)

- The remaining 23 unresearched combos, plus spot-checking any
  `needs_verification` entry before treating it as reliable.
- Wire `service_rotations` + `rotation_summary()` into
  `pipeline/mongo_export.py` (e.g. a `rotation` field added to each
  exported `vessel_schedule` document) so the app backend and website can
  actually display this.
- Re-run `seed_service_rotations.py` periodically (not on the 3-hourly
  schedule — rotations change rarely) and reconcile entries whose
  `last_seen_in_schedule_at` goes stale (the service dropped out of
  current JNPT data).
