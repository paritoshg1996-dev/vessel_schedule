# CLAUDE.md — context for working on this repo

This pipeline scrapes JNPT (Jawaharlal Nehru Port) container-vessel
berthing data, normalizes it, and serves it on a static website with a
live source-health status strip. Full architecture is in `README.md` —
read that first. This file is the "things I'd tell the next person"
context that doesn't belong in user-facing docs.

## Where this stands right now

Built and tested in a sandboxed environment **with no network access to
jnport.gov.in at all** (only package registries were reachable). That
means:

- `scrapers/jnpa_master.py` (the HTML aggregator page) is tested against
  real, saved page content and works.
- The five PDF terminal scrapers (`apmt.py`, `nsict.py`, `nsigt.py`,
  `bmct.py`, `nsft.py`) are written from real fetched-and-inspected copies
  of each PDF, and the underlying extraction engine
  (`scrapers/base.py::snap_table_by_headers`) is proven against an
  adversarial synthetic PDF test — but **none of the five have been run
  against a live fetch**. That's the single highest-value thing to do
  in an environment with real internet access. See "First things to do"
  below.

Per-terminal confidence (see README's honest-status table for the fuller
version): APMT/NSICT/NSIGT are high-confidence on header labels; BMCT is
lower confidence (its real extracted text came through more fragmented);
NSFT's vessel-name column is a best-effort cross-panel merge
(`merge_column_by_row`) since the name sits in a separate panel from its
own SR/VIA/LOA row.

The "vessels expected" sample rows (`SAMPLE VESSEL ALPHA` etc, seeded by
`seed_sample_expected.py`) are **deliberately fictional**, not
best-effort real transcriptions — the real PDF text was too visually
scrambled to hand-transcribe without a real risk of pairing the wrong
voyage to the wrong ship. Don't "fix" them to look more real; retire
them by making the real parsers work (see the reconciliation logic in
`pipeline/normalize.py` — a successful real scrape for a terminal
automatically deletes that terminal's sample rows).

## First things to do with real network access

1. `python3 run_pipeline.py --only NSICT` (swap terminal code), one at a
   time, starting with BMCT and NSFT (lowest confidence).
2. Compare what landed in `staging_raw` for that run against the actual
   PDF at the URL the run's `ingestion_runs.error_message`/stdout shows
   it fetched. staging_raw is deliberately near-verbatim so this is a
   direct diff, not a guessing game.
3. If a terminal's header labels don't match reality, fix them in that
   terminal's file in `scrapers/` — e.g. `EXPECTED_HEADERS` in
   `scrapers/apmt.py`. The engine (`snap_table_by_headers`) shouldn't
   need to change; the per-terminal files are meant to be the only thing
   that does.
4. Once all five terminals are validated, delete the call to
   `seed_sample_expected.py` from whatever demo/setup docs reference it
   — real data will have already superseded the samples via
   reconciliation, but there's no reason to keep seeding fake data at
   that point.
5. Re-run `tests/test_extraction_engine.py` and
   `tests/test_normalize.py` after any change to the engine or
   normalization logic — both are fast, real (not mocked) tests.

## Design decisions worth knowing before changing things

- **Coordinate snapping, not text order**, is why the PDF parsers work
  at all — these reports are dense multi-panel Excel exports where
  naive text extraction scrambles which column a value belongs to. See
  the big comment at the top of `scrapers/base.py` before "simplifying"
  anything there.
- **staging_raw is intentionally near-verbatim.** Resist the urge to
  clean data before it lands there — normalization happens exactly once,
  in `pipeline/normalize.py`, so there's one place to fix a bug rather
  than N places to keep in sync.
- **Dedup key is `(terminal_code, via_no, status, report_date)`**, with
  a fallback to vessel_name when via_no is missing. Stale-row cleanup
  only touches a `(terminal, section)` pair the current run can *confirm*
  it observed (`ScrapeResult.terminals_seen`) — a terminal whose block
  silently disappears from a page redesign is left alone rather than
  wiped. Don't loosen this without re-reading `tests/test_normalize.py`;
  it encodes several non-obvious edge cases (two ships with no voyage
  number, whitespace drift in codes, sample-vs-real supersession).
- **JNPT's PDF filenames encode the date and change daily.** The master
  scraper discovers each terminal's *current* URL every run
  (`ScrapeResult.discovered_links`) rather than trusting a hardcoded one
  — don't remove that and go back to the static registry URLs.

## Commands

```bash
# Full pipeline, live network:
python3 run_pipeline.py

# Demo mode (master page from a saved fixture, terminals still live):
python3 run_pipeline.py --master-fixture fixtures/jnpa_master_2026-09-09.html

# One terminal only, for validation:
python3 run_pipeline.py --only NSICT

# Tests:
python3 tests/test_extraction_engine.py
python3 tests/test_normalize.py

# Rebuild the static frontend's embedded-data fallback after a pipeline run:
python3 build_frontend.py
```
