# JNPT Vessel Schedule

A pipeline + website that pulls container-vessel berthing data from JNPT
(Jawaharlal Nehru Port), cleans it into one consistent schema, and shows
it on a website with a live status strip so you know when a source has
gone stale or stopped responding.

**Read this whole README before deploying.** The honest-status section
below tells you exactly what's verified against real data today and what
still needs a live-network validation pass.

## Architecture

```
 JNPA master page (HTML)  ──┐
 NSFT terminal PDF         ─┤
 NSICT terminal PDF        ─┼──▶ scrapers/*.py ──▶ staging_raw ──▶ normalize ──▶ vessel_schedule ──▶ frontend/data.json ──▶ website
 NSIGT terminal PDF        ─┤         │                                              │
 APMT terminal PDF         ─┤         └──▶ ingestion_runs ◀────── alert checks ◀─────┘
 BMCT terminal PDF        ──┘                   │
                                                 └──▶ notify_admin() ──▶ console / Slack / email
```

- **`scrapers/`** — one module per source. `base.py` holds the interface
  and the coordinate-snapping PDF table engine every terminal parser
  shares; each terminal file is a small config (which header labels to
  look for) on top of that engine. `jnpa_master.py` also discovers each
  terminal's *current* PDF URL, since JNPT's filenames encode the date
  and change daily.
- **`models.py`** — SQLAlchemy schema: `terminals` (config), `ingestion_runs`
  (one row per scrape attempt — the audit trail), `staging_raw` (near-verbatim
  landing zone), `vessel_schedule` (the clean table the site reads), `alerts`.
- **`pipeline/`** — `staging.py` lands raw rows, `normalize.py` cleans,
  de-duplicates, and upserts them (see "Duplicate handling" below),
  `alerts.py` checks freshness/failures and notifies.
- **`run_pipeline.py`** — orchestrator; run it on a schedule (cron / GitHub
  Actions — see `.github/workflows/scrape.yml`).
- **`frontend/`** — the website (`index.html` + `data.json`).

## Honest status: what's real vs. what needs validation

I built and tested this against real JNPT data pulled during development,
but this sandbox's network can't reach jnport.gov.in at all (only
package registries are reachable), so the five PDF parsers below could
not be run against a live fetch. Validate them yourself with `--only`
(see "Deploying for real") before trusting them operationally.

| Source | What it gives you | Status |
|---|---|---|
| **JNPA master page** (HTML) | Vessel, berth, voyage no., cargo, berthed/completion times, across *every* terminal | ✅ **Tested against real, saved page content.** Working. |
| **APMT** (PDF) | Vessel, voyage, LOA, service, line | 🟡 High-confidence header labels from a real fetched copy; extraction engine proven on synthetic adversarial data; not yet run against a live fetch |
| **NSICT / NSIGT** (PDF) | Vessel, voyage, LOA, service, line | 🟡 Same as above; "Line" column position is inferred, not a confirmed header label |
| **BMCT** (PDF) | Voyage, LOA, vessel, line, service | 🟠 Lower confidence — real extracted text for this one came through more fragmented than the others. Validate first. |
| **NSFT** (PDF) | Voyage, LOA, service, line, ETA | 🟡 SR/VIA/LOA/Service/Line/ETA high-confidence; vessel *name* sits in a separate panel and needs the best-effort cross-panel merge (`merge_column_by_row`) — treat name pairing as unverified until checked |
| **Agent** field | — | Not published as its own column on any source I found. Schema supports it (nullable); JNPA's "List of Shipping Agencies Registered" page could be a future enrichment source if you need it |

**The "vessels expected" rows in the demo (`SAMPLE VESSEL ALPHA` etc.)
are fictional placeholders, not real transcriptions.** The real PDF text
was too visually scrambled to hand-transcribe field-by-field without a
real risk of pairing the wrong voyage number with the wrong vessel —
shipping a guess that looks like real data seemed worse than shipping an
obviously-fake one. They exist purely to show what the expected-arrivals
view looks like once a parser is validated; they're tagged `is_sample:
true` end to end (DB column → JSON → a visible "SAMPLE" badge in the UI)
so they can never be mistaken for a real schedule.

## Running the demo locally

```bash
pip install -r requirements.txt --break-system-packages   # or use a venv
python3 run_pipeline.py --master-fixture fixtures/jnpa_master_2026-09-09.html
python3 seed_sample_expected.py
python3 build_frontend.py
```

Then open `frontend/index.html`. The master-page fixture is a real,
saved copy of JNPA's page (see the file for the source URL and fetch
date) — this reproduces the exact "13 real rows, master report one day
stale, all 5 terminal PDFs unreachable" state you'd see if you ran this
in an environment without internet access, which is a genuine and useful
test of the alerting path even though it isn't what you'll see once
deployed with real access.

Run the engine's own test suite any time:
```bash
python3 tests/test_extraction_engine.py
```

## Duplicate handling

Re-running the pipeline (every 3 hours, per the GitHub Action) never
creates duplicate rows. `vessel_schedule` has a DB-level unique
constraint on `(terminal_code, via_no, status, report_date)`, and
`normalize_and_upsert` looks up that key before writing, so pulling the
same day's data five times updates one row instead of creating five —
verified by actually running the pipeline twice against identical real
data and diffing the row count (13 → 13, zero dupes).

Three edge cases beyond plain re-runs are also handled, each backed by a
test in `tests/test_normalize.py`:

- **No voyage number extracted.** Two different ships with a missing
  `via_no` fall back to matching on vessel name instead of colliding
  into one row.
- **Formatting drift.** `"S1480"` vs `"S 1480"` (a stray space from a
  parsing hiccup) are normalized to the same code before matching.
- **Stale rows.** If a vessel departs, or drops off a terminal's
  expected-list, its old row is actively deleted (not just never
  updated) once the pipeline can *confirm* that terminal's section was
  checked and no longer mentions it — see `terminals_seen` in
  `scrapers/base.py`. This is also how a sample placeholder row gets
  cleanly retired the moment a terminal's real parser starts
  succeeding. The safety rule: a terminal whose section isn't
  confirmed-observed in a given run (e.g. its block silently vanished
  from a page redesign) is never touched by cleanup at all — a parsing
  regression degrades to "a little stale," never to "data deleted."

## Deploying for real

1. **Put this in a GitHub repo.** `.github/workflows/scrape.yml` is ready
   to go — it runs the pipeline every 3 hours and commits the refreshed
   `frontend/data.json` back to the repo.
2. **Turn on GitHub Pages** for the repo (serve from `/frontend`, or move
   `frontend/`'s contents to `/docs` — either works, just keep
   `run_pipeline.py --out` pointed at wherever Pages serves from). The
   site will show live data with no rebuild step, since it fetches
   `data.json` at runtime.
3. **Add a `DATABASE_URL` secret** pointing at a small hosted Postgres
   instance (Supabase, Neon, and Railway all have a free tier that's
   plenty for this). GitHub's runners are ephemeral, so without an
   external DB you lose history/dedup between runs — see the comment in
   `scrape.yml` for the SQLite-cache fallback if you'd rather not stand
   up Postgres yet.
4. **Validate each PDF parser before trusting it**, one at a time:
   ```bash
   python3 run_pipeline.py --only NSICT
   ```
   then compare `staging_raw` for that run against the actual PDF at the
   URL `ingestion_runs.error_message`/logs show it fetched. Start with
   BMCT (lowest confidence) and NSFT (vessel-name merge is best-effort).
   Fix the header labels in that terminal's file in `scrapers/` if
   anything's off — the whole point of the staging table is that you're
   diffing against *exactly* what was scraped, not a downstream guess.
5. **Wire up real alerts** by adding whichever of these repo secrets you
   want (`pipeline/alerts.py` no-ops any channel that isn't configured):
   - `ADMIN_ALERT_SLACK_WEBHOOK_URL` — an incoming webhook URL
   - `ADMIN_ALERT_EMAIL_TO`, `ADMIN_ALERT_SMTP_HOST`, `_PORT`, `_USER`, `_PASSWORD`

## Adding another terminal or port

This is the part meant to stay cheap. To add a source:

1. Add one entry to `scrapers/registry.py` (port, terminal code, cargo
   type, source type, URL).
2. Write one small scraper file. If it's a PDF with the same "dense
   multi-panel Excel export" shape as JNPT's terminals, subclass
   `PdfTerminalScraper` and just declare which header labels
   `snap_table_by_headers` should look for — see `scrapers/apmt.py` for
   the shortest example, or `scrapers/dpworld_common.py` for how two
   terminals share one template.
3. Add it to `SCRAPER_CLASSES` in `scrapers/__init__.py`.

Nothing in `pipeline/`, `models.py`, or the frontend needs to change —
they're all written against the canonical schema, not any one source's
shape. Beyond JNPT, Mundra (APSEZ), Chennai, Vizag, Kolkata/Haldia,
Cochin, and Tuticorin are the other major container gateways if you want
to extend beyond one port; each will need its own quick "what does their
report actually look like" pass, the same way this README's honest-status
table came from actually fetching JNPT's pages rather than assuming.

## Known limitations

- **This sandbox can't reach jnport.gov.in**, so "live" fetch behavior
  here reflects that restriction (403s from the network layer), not a
  code bug — once running on a normal server/CI runner, those requests
  will go through.
- **No "sailed vessels" data yet.** The terminal PDFs have a sailed-in-
  last-24h section; none of the five parsers extract it yet. The
  frontend already has an (empty, explained) tab ready for it.
- **Agent** is schema-supported but not populated by any current source.
- **Staleness tolerance** defaults to 0 days (report must be dated
  today, IST). Pass `--staleness-tolerance-days 1` if JNPT's actual
  publish cadence turns out to lag by a day on weekends/holidays once
  you're watching it live.
