# Service rotation research — coverage notes (2026-09-11)

## What this is

`service_rotations` is reference data (which ports a named carrier service
loop calls at, in order) that a vessel's onward journey from JNPT is
computed against — see `models.ServiceRotation` and `pipeline/rotations.py`
for the schema and join logic. It is **not** scraped from JNPT; no port's
berthing report publishes a vessel's rotation beyond its own call.

## Scope of the current data

As of this date, `vessel_schedule` (expected status) has **97 distinct
(shipping_line, service) combinations**. Of those:

- **18 voyages** (across 11 different lines) use the service label
  `ADHOC` — a JNPT-side code for an unscheduled, one-off call. There is
  genuinely no fixed rotation for these; seeded with
  `confidence="no_fixed_rotation"` rather than left looking unresearched.
- **86 distinct named-service combinations** remain, of which **8 have
  been researched** so far (`research/service_rotations_2026_09.py`) —
  the highest-frequency ones, covering roughly a third of all
  named-service *voyages* even though it's a small fraction of the
  86 distinct combos (frequency is heavily skewed: most combos have
  only 1 vessel currently listed).

## Confidence breakdown of the 8 researched

| Line/Service | Confidence | Why |
|---|---|---|
| MAE/FI2 | verified | Maersk's own May 2026 launch announcement |
| MSK/MECL | verified | Maersk's own July 2026 structural-change announcement |
| MSC/INDUSA | needs_verification | Source from 2020; MSC has since made port-skip changes on India services generally |
| CCA/BIGEX | needs_verification | Port set fairly confident; exact call order is a guess (CMA CGM runs 4 differently-named BIGEX variants, and vessel_schedule's plain "BIGEX" label doesn't say which) |
| HLI/TPI | needs_verification | Hapag-Lloyd's own page, but 2+ years old relative to research date |
| WHI/CI2 | needs_verification | Intra-Asia consortium loop; one port (Port Klang) appears twice in the source description, unconfirmed if that's a real double-call |
| COS/AGI2 | **unresolved** | Conflicting info: the original AGI2 (2022) never called JNPT at all; a later "UIG2" service that replaced it does. JNPT's own live report still labels a real current vessel's service as "AGI2" — left unresolved rather than guessing which rotation actually applies today |
| ONE/PS3 | **unresolved** | Search returned an implausible 14-port rotation spanning India, SE Asia, East Asia, and the US West Coast in one loop — almost certainly a search-summary conflation of multiple distinct ONE services. Discarded entirely. |

## What this demonstrates about the "research via web search" approach

- Carrier sites and the one schedule aggregator tried (Flexport Atlas)
  both return HTTP 403 to automated fetches — every result here came
  from search-result synthesis, not a direct primary-source read. That's
  a real reliability ceiling: "verified" here means "matched a carrier's
  own press release found via search," not "confirmed against a live
  schedule database."
- Real failure modes hit in just 8 lookups: a carrier renaming/replacing
  a service code without the port terminal's own label catching up
  (COS/AGI2), multiple similarly-named variants of one service
  (CCA/BIGEX), and one clearly-hallucinated/conflated multi-service
  answer (ONE/PS3) that had to be thrown out rather than recorded.
- Extrapolating: covering the remaining ~78 combos at this level of care
  is a large, slow effort with a non-trivial "unresolved" and
  "needs_verification" rate baked in — not a one-shot batch job.

## Next steps (not yet done)

- Continue researching the remaining ~78 named-service combos (most with
  only 1 currently-listed voyage — lower payoff per lookup than the pilot
  batch, but still real gaps).
- Wire `service_rotations` + the `next_ports_for` join into
  `pipeline/mongo_export.py` (a new collection, or precomputed
  `next_ports`/`confidence` fields added to each `vessel_schedule`
  document) so the app backend and website can actually display this.
- Decide how to surface confidence to end users — e.g. "verified" shown
  plainly, "needs_verification" with a visible caveat, "unresolved"
  omitted or shown as "rotation not yet confirmed" rather than blank.
- Re-run `seed_service_rotations.py` periodically (not on the 3-hourly
  schedule — rotations change rarely) and reconcile stale entries whose
  `last_seen_in_schedule_at` is old.
