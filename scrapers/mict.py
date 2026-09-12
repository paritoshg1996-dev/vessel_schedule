"""
Mundra International Container Terminal (MICT) -- DP World's own
terminal at Mundra Port, entirely separate from Adani's four (see
scrapers/mundra_adani.py): different operator, different report
template, different URL-discovery mechanism.

URL DISCOVERY. Unlike every other source in this package, MICT's PDF
doesn't sit at a stable filename (JNPT: daily-changing filename,
discovered via the JNPA master page; Adani Mundra: one fixed URL
forever). DP World's berthing-report page is a Next.js site that loads
its document list client-side from a GraphQL endpoint backed by
Sitecore Content Hub -- see scrapers/dpworld_contenthub.py for the
shared discovery mechanism (also used by scrapers/chennai_dpworld.py's
CCT terminal) and how it was reverse-engineered.

Validated 2026-09-11 against a live fetch (both the GraphQL discovery
call and the resulting PDF). This report is, refreshingly, NOT built
like JNPT's or Adani's Excel-style exports -- single page, three panels
("ON BERTH VESSELS", "VESSELS SAILED IN LAST 24 HOURS", and a third,
untitled panel that's functionally "vessels expected" -- same column
set as JNPT's own expected tables), all sharing one consistent
left-hand column layout with no header-row jitter and no overlapping/
garbled text anywhere -- checked at the word-position level, not just
by eye. The only real quirk: a "TIDE TABLE" panel and, on two of the
three vessel tables, an adjacent "ICD PENDENCY" rail-cargo side-table
sit to the right with no header of their own on some rows -- both
ignored the same way JNPT/Adani's own rail-summary blocks already are
(see AGENT handling below, and mundra_adani.py's module docstring).

Column mapping notes:
- "Vsl ID / Voyage" is ONE combined header cell (not two columns) --
  its own data token ("ARLI637S", "HONS69IN", ...) is both the vessel's
  ID and voyage number combined; there's no separate "via_no" the way
  JNPT publishes one, so this is what via_no maps to here.
- "AGENT" has nothing bounding it on the right on the untitled third
  table (no header labels itself to its right on that specific row --
  the ICD-rail side-table's own columns aren't labelled at all there),
  so its lane absorbs every rail-destination word that follows too;
  only the first token is the real agent code, same "take the first
  token" pattern as dpworld_common.py's VOA handling for NSICT/NSIGT.
  Per the user's own call on how to populate this source: both `agent`
  and `shipping_line` take this same value (MICT's report, like
  Adani's, only publishes one carrier-identifying column).
- "CUT-OFF" prints as "11/0500" -- day + glued 24h time, no month, same
  shape as dpworld_common.py's own GATE CUTOFF column -- reuses
  pdf_common.parse_gate_cutoff rather than re-deriving it.
- "READINESS" ("GATE CLOSED"/"GATE OPEN"/blank) has no home in our
  schema (nothing else publishes it) -- left in `raw` for staging, not
  promoted to a canonical column.

WHAT'S DELIBERATELY NOT IMPLEMENTED YET: "VESSELS SAILED IN LAST 24
HOURS". Extracts cleanly (verified the same way as the other two
panels) but per the user's own explicit call, sailed-vessel capture is
out of scope for this pass across both Mundra sources.

Confidence: HIGH on "ON BERTH VESSELS" and the untitled expected-style
panel -- both checked against real fetched word positions, no
overlap/garbling found anywhere on this report (unlike Adani's).
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from dateutil import parser as dateutil_parser

from scrapers.base import ScrapedRow, ScrapeResult, find_phrase_boxes, snap_table_by_headers
from scrapers.dpworld_contenthub import DpWorldContentHubScraper
from scrapers.pdf_common import parse_gate_cutoff, parse_relative_datetime

BERTH_HEADERS = ["SR", "Voyage", "VCN", "VESSEL NAME", "SERVICE", "AGENT", "REMARKS"]
EXPECTED_HEADERS = [
    "SR", "Voyage", "VCN", "VESSEL NAME", "READINESS", "ETA", "Time",
    "CUT-OFF", "LOA", "SERVICE", "AGENT",
]


def _to_float(s: str):
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _parse_report_date(words: list[dict]) -> Optional[date]:
    # Title line reads "Fri, 11 Sep 2026 Vessel Schedule Report Mundra
    # International Container Terminal" -- the date sits to the LEFT of
    # the "Vessel Schedule Report" anchor phrase, not the right, so
    # pdf_common.extract_label_value (right-only) doesn't apply here.
    boxes = find_phrase_boxes(words, "Vessel Schedule Report")
    if not boxes:
        return None
    box = boxes[0]
    same_line = sorted(
        [w for w in words if abs(w["top"] - box["top"]) <= 3 and w["x1"] <= box["x0"]],
        key=lambda w: w["x0"],
    )
    raw = " ".join(w["text"] for w in same_line).strip()
    if not raw:
        return None
    try:
        return dateutil_parser.parse(raw, dayfirst=True, fuzzy=True).date()
    except (ValueError, OverflowError):
        return None


class MictScraper(DpWorldContentHubScraper):
    terminal_code = "MICT"
    ports_and_terminals_id = "DP.PortsandTerminals.MundraMICT"

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        report_date = _parse_report_date(words)

        rows = []
        rows += self._parse_berthed(words, report_date)
        rows += self._parse_expected(words, report_date)
        return ScrapeResult(report_date=report_date, rows=rows)

    def _parse_berthed(self, words: list[dict], report_date) -> list[ScrapedRow]:
        berth_boxes = find_phrase_boxes(words, "ON BERTH VESSELS")
        sailed_boxes = find_phrase_boxes(words, "VESSELS SAILED IN LAST 24 HOURS")
        if not berth_boxes or not sailed_boxes:
            return []
        top_after = min(b["top"] for b in berth_boxes)

        raw_rows = snap_table_by_headers(
            words, header_labels=BERTH_HEADERS,
            top_after=top_after, bottom_before_labels=["VESSELS SAILED IN LAST 24 HOURS"],
        )
        rows = []
        for r in raw_rows:
            via = r.get("Voyage", "").strip()
            vessel_name = r.get("VESSEL NAME", "").strip()
            if not via and not vessel_name:
                continue
            fields = {
                "terminal_code": self.terminal_code,
                "vessel_name": vessel_name or None,
                "via_no": via or None,
                "service": r.get("SERVICE", "").strip() or None,
                "shipping_line": (r.get("AGENT", "").split() or [None])[0],
            }
            rows.append(ScrapedRow(section="berthed", fields=fields, raw=r))
        return rows

    def _parse_expected(self, words: list[dict], report_date) -> list[ScrapedRow]:
        # This panel has no section title of its own -- "READINESS" is a
        # header label unique to this row (see module docstring), so it
        # anchors top_after directly rather than needing a title search.
        readiness_boxes = find_phrase_boxes(words, "READINESS")
        if not readiness_boxes:
            return []
        top_after = min(b["top"] for b in readiness_boxes) - 2

        raw_rows = snap_table_by_headers(
            words, header_labels=EXPECTED_HEADERS,
            top_after=top_after, bottom_before_labels=["TOTAL"],
        )
        rows = []
        for r in raw_rows:
            via = r.get("Voyage", "").strip()
            vessel_name = r.get("VESSEL NAME", "").strip()
            if not via and not vessel_name:
                continue
            agent_tokens = r.get("AGENT", "").split()
            agent = agent_tokens[0] if agent_tokens else None
            eta_raw = f"{r.get('ETA', '').strip()} {r.get('Time', '').strip()}".strip()
            # "11/09 11:00" -- day/month + colon time, no year, same shape
            # every other terminal's ETA already comes in.
            eta = parse_relative_datetime(eta_raw, report_date)
            fields = {
                "terminal_code": self.terminal_code,
                "via_no": via or None,
                "vessel_name": vessel_name or None,
                "loa_m": _to_float(r.get("LOA", "")),
                "service": r.get("SERVICE", "").strip() or None,
                "shipping_line": agent,
                "agent": agent,
                "eta": eta,
                # This report's own "vessels expected" list runs weeks
                # out, further than a fixed report-relative threshold can
                # safely disambiguate a month-end rollover -- anchor to
                # this row's own eta instead (see pdf_common docstring).
                "gate_cutoff": parse_gate_cutoff(r.get("CUT-OFF", ""), report_date, near=eta),
            }
            rows.append(ScrapedRow(section="expected", fields=fields, raw=r))
        return rows
