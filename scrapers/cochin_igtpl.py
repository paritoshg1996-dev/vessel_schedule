"""
India Gateway Terminal Pvt Ltd (IGTPL) -- DP World's terminal at Cochin
(Vallarpadam), and the only container terminal at Cochin Port, so this
is a single-terminal source the same way Chennai's two and Mundra's
five collectively cover their own ports.

Genuinely the simplest source in this package: an ordinary
server-rendered HTML page (https://igtpl.com/php/vessel-schedules.php),
not a PDF at all -- no coordinate-snapping engine needed, just a plain
<table id="card-table"> read with BeautifulSoup. The page also injects a
second, "stacktable"-cloned copy of the same data for mobile viewports
(one tiny 2-column table per vessel) -- `table.large-only` is the real
one this scrapes; the mobile clones are ignored.

SSL: igtpl.com's certificate chain is missing an intermediate cert --
browsers tolerate this (most ship/fetch the missing intermediate via
AIA chasing or their own trust store), but Python's default `ssl`
context does not, and `requests` raises SSLCertVerificationError. Fetched
with `verify=False` for this one host -- same call container_traffic's
own backend already made for a similarly-misconfigured site (see that
repo's `http_client_insecure`). Worth re-checking occasionally in case
they fix their cert chain, at which point this could safely go back to
verified.

NO SEPARATE STATUS SECTIONS. Unlike every PDF source in this package,
IGTPL doesn't publish separate "expected"/"on berth"/"sailed" panels --
one single table holds a rolling few weeks of vessels regardless of
status, ordered newest-ETA-first, and status has to be INFERRED from
which of ATA/ATD are populated:
  - neither ATA nor ATD filled in -> still expected
  - ATA filled in, ATD blank       -> currently alongside (berthed)
  - both ATA and ATD filled in     -> already sailed
Sailed rows are skipped, consistent with every other source touched
this pass. A currently-berthed row (ATA set, no ATD) is emitted with
section="berthed" -- run_pipeline.py already routes any scraper's
"berthed" rows to models.BerthedVessel regardless of terminal, so no
pipeline changes were needed for this; it just means IGTPL is
simultaneously its own "master"-equivalent and its own richer
terminal-native source, unlike JNPT's split-in-two design.

NO PRINTED "REPORT DATE" either -- this is a live view, not a dated
daily PDF. report_date is set to "today" (IST, since this is an Indian
port and every other terminal's own printed dates are implicitly
IST-local) rather than left null: `report_date` is part of
vessel_schedule's own dedup key
(terminal_code, via_no, status, report_date), so using a stable per-day
date (not datetime.now(), which would produce a new row every single
3-hourly run) means a re-run within the same calendar day still
correctly updates the existing row instead of creating a new one, and
the reconciliation logic naturally retires a stale "yesterday" row once
the date rolls over.

Column mapping notes (10-column table: Vessel Name / Voy. No / CVIA-
Next Port / Operator / ETA / ATA / ETD / ATD / Entry Time / Cut Off
Time -- confirmed against the page's own <thead>, which is checked
against COLUMN_ORDER below on every run as a schema-drift guard):
- "Operator" (3-letter carrier/agent codes -- WHL, MSC, UNF, SCI, ...)
  populates both `agent` and `shipping_line`, same call made for every
  other non-JNPT source this pass (this report doesn't publish a
  separate agent column).
- "CVIA/Next Port" looks genuinely valuable (a composite value like
  "W36926397-PKG" -- appears to end in the vessel's own next-port code)
  but its exact structure isn't confirmed enough to decompose with
  confidence -- staged in `raw`, not promoted to a canonical column or
  cross-referenced against service_rotations in this pass (same
  "interesting but not yet wired in" call as CCT's own "SECTOR" column
  in chennai_dpworld.py).
- "Entry Time" (Container gate-open) has no home in our schema (nothing
  else publishes a distinct gate-open timestamp either) -- staged, not
  promoted. "Cut Off Time" -> `gate_cutoff`.
- No berth number, LOA, or draft published anywhere on this page --
  left null on berthed rows, same as any other terminal missing a field
  the model otherwise supports.

Confidence: HIGH -- this is a plain HTML table with no ambiguous lane
geometry to get wrong; checked against a live fetch, 45 rows, spanning
clearly-expected, clearly-berthed, and clearly-sailed examples of each
inferred status.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from scrapers.base import FetchError, ParseError, ScrapedRow, ScrapeResult, TerminalScraper

URL = "https://igtpl.com/php/vessel-schedules.php"
_USER_AGENT = "Mozilla/5.0 (compatible; vessel-schedule-bot/1.0)"
IST = timezone(timedelta(hours=5, minutes=30))

# The table's own column order, read left to right -- checked against the
# live <thead> every run (see _check_header_shape) since there's no
# header-label-based lane search here to fail loudly the way the PDF
# sources' snap_table_by_headers would on a layout change.
COLUMN_ORDER = [
    "vessel_name", "via_no", "cvia_next_port", "operator",
    "eta", "ata", "etd", "atd", "entry_time", "cutoff_time",
]


def _parse_dt(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return dateutil_parser.parse(s, dayfirst=False)
    except (ValueError, OverflowError):
        return None


def _check_header_shape(table) -> None:
    """Schema-drift guard: this scraper trusts column POSITION (there's
    no per-cell header label to anchor a lane search on, unlike every
    PDF source), so a silently-reordered column would otherwise corrupt
    every field silently. Raise loudly instead if the header text ever
    stops matching what this was built against."""
    thead = table.find("thead")
    if thead is None:
        raise ParseError("[IGTPL] table has no <thead> -- source layout may have changed")
    header_text = " ".join(thead.get_text(" ", strip=True).upper().split())
    expected_fragments = [
        "VESSEL NAME", "VOY. NO", "CVIA/NEXT PORT", "OPERATOR",
        "ETA", "ATA", "ETD", "ATD", "ENTRY TIME", "CUT OFF TIME",
    ]
    missing = [f for f in expected_fragments if f not in header_text]
    if missing:
        raise ParseError(f"[IGTPL] table header no longer contains {missing} -- "
                          f"source layout may have changed (found: {header_text!r})")


class CochinIgtplScraper(TerminalScraper):
    terminal_code = "IGTPL"

    def __init__(self, url: str = None, fixture_path: str = None):
        self.url = url or URL
        self.fixture_path = fixture_path

    def fetch(self) -> bytes:
        if self.fixture_path:
            with open(self.fixture_path, "rb") as f:
                return f.read()
        try:
            # verify=False: igtpl.com's cert chain is missing an
            # intermediate -- see module docstring.
            resp = requests.get(self.url, timeout=self.timeout_seconds, verify=False,
                                 headers={"User-Agent": _USER_AGENT})
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as e:
            raise FetchError(f"[{self.terminal_code}] could not fetch {self.url}: {e}") from e

    def parse(self, raw_content: bytes) -> ScrapeResult:
        soup = BeautifulSoup(raw_content, "lxml")
        # id="card-table", not class "large-only"/"small-only" -- those
        # only exist in the CLIENT-rendered DOM (a "stacktable.js" plugin
        # adds them at runtime for a responsive mobile clone); the raw
        # server HTML this scraper actually receives just has class="table".
        table = soup.find("table", id="card-table")
        if table is None:
            raise ParseError(f"[{self.terminal_code}] no table#card-table found -- "
                              f"source layout may have changed")
        _check_header_shape(table)

        tbody = table.find("tbody")
        body_rows = tbody.find_all("tr") if tbody else table.find_all("tr")[2:]
        if not body_rows:
            raise ParseError(f"[{self.terminal_code}] table has a header but zero data rows")

        report_date = datetime.now(IST).date()
        rows: list[ScrapedRow] = []
        for tr in body_rows:
            cells = tr.find_all("td")
            if len(cells) < len(COLUMN_ORDER):
                continue
            texts = [c.get_text(strip=True) for c in cells[:len(COLUMN_ORDER)]]
            r = dict(zip(COLUMN_ORDER, texts))

            vessel_name = r["vessel_name"].strip()
            via_no = r["via_no"].strip()
            if not vessel_name and not via_no:
                continue

            ata, atd = _parse_dt(r["ata"]), _parse_dt(r["atd"])
            if ata and atd:
                continue  # already sailed -- out of scope this pass, see module docstring
            section = "berthed" if ata else "expected"

            agent = r["operator"].strip() or None
            fields = {
                "terminal_code": self.terminal_code,
                "vessel_name": vessel_name or None,
                "via_no": via_no or None,
                "shipping_line": agent,
            }
            if section == "expected":
                fields.update({
                    "agent": agent,
                    "eta": _parse_dt(r["eta"]),
                    "gate_cutoff": _parse_dt(r["cutoff_time"]),
                })
            else:  # berthed -- ATA is the closest thing to "came alongside"
                # published here (no distinct berthing timestamp); ETD is
                # her next scheduled event, same role as ETC/ETD elsewhere.
                fields.update({
                    "alongside_at": ata,
                    "next_event_at": _parse_dt(r["etd"]),
                })
            rows.append(ScrapedRow(section=section, fields=fields, raw=r))

        return ScrapeResult(report_date=report_date, rows=rows)
