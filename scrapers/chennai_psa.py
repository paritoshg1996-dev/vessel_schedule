"""
Chennai International Terminal Pvt Ltd (CIT) -- Global PSA's terminal at
Chennai Port. The berthing-report page
(https://india.globalpsa.com/vessel-schedule/vessel-schedule-chennai/)
is a bare `<embed src="...pdf">` stub whose src IS today's PDF, no
API/discovery mechanism needed at all -- just re-fetch that tiny page
each run and regex out the current `.pdf` URL (the filename itself
encodes the date, e.g. "VESSEL-STATUS-AS-ON-12.09.2026.pdf", and
changes daily -- see `discover_pdf_url` below).

Validated 2026-09-12 against a live fetch. Single page, and -- unlike
every other multi-panel report in this package -- its text already
reads in clean, correct order without any coordinate-snapping tricks
needed for the one table this scrapes:

- A 4-berth "ON BERTH" panel (SCB I (N)/SCB I/SCB II/SCB III) sits above
  the main table, laid out the same "vertical key:value block per berth"
  way as chennai_dpworld.py's CTB panel (VESSEL/VIA-LOA/SVS+AGENT/
  ARRIVED/BERTHED/ETC). All four were vacant on the fetch this was
  checked against -- no words at all under any of the four blocks'
  labels, confirmed at the word-position level -- so this panel's
  extraction logic is UNVALIDATED against a real occupied berth; not
  implemented this pass (see WHAT'S NOT IMPLEMENTED below).
- An "EXCHANGE RATE" table (USD rate by date) sits alongside it --
  irrelevant, ignored the same way every other terminal's own
  cargo-summary/currency furniture is.
- The main "S.NO / VIA / VESSEL NAME / ETA / REVISED ETA / LOA /
  GATE OPEN / GATE CUTOFF / SERVICE / AGENT / EGM NO/DATE / VOYAGE"
  table is what this scrapes -- 12 rows on the fetch checked, and
  `snap_table_by_headers` reconstructs it correctly with only the one
  fix below.

Column mapping notes:
- "VIA" here is CIT's own internal sequence number (269011, 269013,
  ...), same role as every other terminal's "VIA"/"via_no" column --
  matched by label, not by which one looks more like a carrier voyage
  code. The genuine carrier voyage code prints separately as "VOYAGE"
  (e.g. "'2633W/2633E", an inbound/outbound pair) -- staged in `raw`,
  not promoted to a canonical column (same call made for CCT's "VOY" in
  chennai_dpworld.py).
- Bare "ETA" is ambiguous with the "ETA" embedded inside "REVISED ETA"
  (both literally contain the word) -- `disambiguate_leftmost` relabels
  the leftmost (the real standalone ETA column) with a private sentinel
  so the lane search binds correctly to each, same pattern used
  throughout this package (e.g. APMT's "Cut-Off"/"Reefer Cut-Off").
- `eta` coalesces REVISED ETA over ETA when both are present (the more
  current estimate), falling back to whichever one the row actually
  has -- some rows only publish one or the other.
- GATE OPEN has no home in our schema (nothing else publishes a
  distinct "gate opens" timestamp either) -- staged, not promoted.
  GATE CUTOFF sometimes reads "WILL ADVICE" instead of a real
  timestamp -- parsed as None rather than raising, same as any other
  unparseable value.
- Both `agent` and `shipping_line` take AGENT's value (this report only
  publishes one carrier-identifying column) -- same call made for every
  other non-JNPT source this pass.

WHAT'S DELIBERATELY NOT IMPLEMENTED:
- The ON BERTH panel (see above -- unvalidated against real occupied-
  berth data; revisit once a fetch catches one populated).
- "Sailed" vessels -- CIT's table doesn't separate them into their own
  section at all; a vessel that has already sailed just doesn't appear
  once removed from CIT's own live list, so there's no "sailed" rows to
  capture here in the first place (unlike IGTPL Cochin, whose page keeps
  weeks of sailed history inline).

Confidence: HIGH on the expected-vessel table -- checked at the
word-position level, text order and lane assignment both confirmed
correct with no scrambling found anywhere on this report.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Optional

import requests
from dateutil import parser as dateutil_parser

from scrapers.base import FetchError, ParseError, ScrapedRow, ScrapeResult, find_phrase_boxes, snap_table_by_headers
from scrapers.pdf_common import PdfTerminalScraper, disambiguate_leftmost, parse_relative_datetime

PAGE_URL = "https://india.globalpsa.com/vessel-schedule/vessel-schedule-chennai/"
_USER_AGENT = "Mozilla/5.0 (compatible; vessel-schedule-bot/1.0)"

EXPECTED_HEADERS = [
    "S.NO", "VIA", "VESSEL NAME", "REVISED ETA", "LOA",
    "GATE OPEN", "GATE CUTOFF", "SERVICE", "AGENT", "EGM NO/DATE", "VOYAGE",
]


def discover_pdf_url(timeout: int = 20) -> str:
    """The berthing-report page is a bare `<embed src="...pdf">` stub --
    today's PDF URL IS the page, no JSON API involved. Re-fetched every
    run since the filename (and therefore the URL) encodes the date and
    changes daily."""
    try:
        resp = requests.get(PAGE_URL, timeout=timeout, headers={"User-Agent": _USER_AGENT})
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"[CIT] could not reach the berthing-report page: {e}") from e
    m = re.search(r'https?://[^\s"\'<>]+\.pdf', resp.text, re.I)
    if not m:
        raise FetchError(f"[CIT] no .pdf link found on the berthing-report page "
                          f"(page may have changed shape): {resp.text[:200]!r}")
    return m.group(0)


def _to_float(s: str):
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _parse_report_date(words: list[dict]) -> Optional[date]:
    """"CHENNAI INTERNATIONAL TERMINAL PVT LTD 12.09.2026" -- a trailing
    DD.MM.YYYY token on the title line, no label at all. Scans the whole
    page rather than restricting to a top-of-page y-band: unlike CCT's
    title (which sits right at the very top), this one prints around
    top=106pt, and a fixed cutoff picked for one report's title position
    isn't a safe bet for another's -- the dot-separated DD.MM.YYYY shape
    itself is distinctive enough not to collide with anything else on
    this page (the exchange-rate table's own dates use "DD- MON -YYYY").
    """
    for w in words:
        m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", w["text"].strip())
        if m:
            d, mo, y = (int(x) for x in m.groups())
            try:
                return date(y, mo, d)
            except ValueError:
                continue
    return None


class ChennaiPsaScraper(PdfTerminalScraper):
    terminal_code = "CIT"

    def __init__(self, url: str = None, fixture_path: str = None):
        # `url` accepted for interface consistency (run_pipeline.py always
        # constructs `scraper_cls(url=url)`) but unused -- CIT's real PDF
        # location changes daily and is discovered fresh in fetch() below.
        super().__init__(url or PAGE_URL, fixture_path)

    def fetch(self) -> bytes:
        if self.fixture_path:
            with open(self.fixture_path, "rb") as f:
                return f.read()
        pdf_url = discover_pdf_url(timeout=self.timeout_seconds)
        try:
            resp = requests.get(pdf_url, timeout=self.timeout_seconds, headers={"User-Agent": _USER_AGENT})
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as e:
            raise FetchError(f"[{self.terminal_code}] could not fetch discovered PDF {pdf_url}: {e}") from e

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        report_date = _parse_report_date(words)

        vessel_name_boxes = find_phrase_boxes(words, "VESSEL NAME")
        if not vessel_name_boxes:
            raise ParseError(f"[{self.terminal_code}] could not find the 'VESSEL NAME' header -- "
                              f"source layout may have changed")
        header_row_top = min(b["top"] for b in vessel_name_boxes)
        eta_label = disambiguate_leftmost(words, "ETA", header_row_top)

        raw_rows = snap_table_by_headers(
            words, header_labels=EXPECTED_HEADERS + [eta_label],
            top_after=header_row_top - 2,
        )

        rows = []
        for r in raw_rows:
            via = r.get("VIA", "").strip()
            vessel_name = r.get("VESSEL NAME", "").strip()
            if not via and not vessel_name:
                continue
            agent = r.get("AGENT", "").strip() or None
            eta_raw = r.get("REVISED ETA", "").strip() or r.get(eta_label, "").strip()
            fields = {
                "terminal_code": self.terminal_code,
                "via_no": via or None,
                "vessel_name": vessel_name or None,
                "loa_m": _to_float(r.get("LOA", "")),
                "service": r.get("SERVICE", "").strip() or None,
                "shipping_line": agent,
                "agent": agent,
                "eta": parse_relative_datetime(eta_raw, report_date),
                "gate_cutoff": parse_relative_datetime(r.get("GATE CUTOFF", ""), report_date),
            }
            rows.append(ScrapedRow(section="expected", fields=fields, raw=r))
        return ScrapeResult(report_date=report_date, rows=rows)
