"""
Adani Ports' Mundra terminals -- AMCT, T2, AICTPL (the MSC joint
venture), and ACMTPL (the CMA CGM joint venture). Unlike JNPT, all four
are published in ONE combined PDF at a fixed, never-changing URL (no
daily-changing filename, no master-page link discovery needed) --
"VESSELS EXPECTED at <TERMINAL>" repeats once per terminal down the
page, and a TIDE TABLE / "VESSELS ON BERTH AT ADANI CTs" / "VESSELS
SAILED IN LAST 24 HRS AT ADANI CTs" panel sit above all four.

This is dispatched under the "MUNDRA_ADANI" terminal_code (see
registry.py) purely as a bookkeeping/IngestionRun label for the one
shared fetch -- exactly the same role JNPT_MASTER plays for the JNPA
page. No vessel row's own terminal_code is ever "MUNDRA_ADANI"; each
row sets its real one (AMCT/T2/AICTPL/ACMTPL) via `fields["terminal_code"]`,
and `ScrapeResult.terminals_seen` lists all four so normalize.py's
reconciliation (see pipeline/normalize.py) can prune stale rows across
all of them from this one run, not just the dispatch terminal.

Validated 2026-09-11 against a live fetch. Two things this needed that
no JNPT source ever has:

1. TWO PAGES. Every JNPT PDF is single-page; this one is two (AMCT/T2/
   AICTPL's "VESSELS EXPECTED" panels are on page 0, ACMTPL's is on page
   1). `PdfTerminalScraper.parse()` only ever reads `pdf.pages[0]`, so
   this class overrides `parse()` entirely: every page's words are
   pulled and each page's `top`/`bottom` is offset by `page_index *
   page.height`, giving one continuous coordinate space `snap_table_by_
   headers` can run over exactly as if it were one tall page. (There's
   no risk of a false phrase match spanning the page break --
   `find_phrase_boxes` still requires same-page-worth of vertical
   jitter, i.e. within 4pt, to count a multi-word phrase as one match.)

2. EXTREMELY TIGHT LINE SPACING dropped each panel's row 1. Real,
   caught-live bug: this report's row height is ~3.7pt (JNPT's own PDFs
   run more like 8-20pt), and `snap_table_by_headers`'s old hardcoded
   "header_bottom + 1" margin (meant to keep header words out of the
   data bucket) ate into that gap -- on live data, row 1's own top
   landed *inside* header_bottom+1 for every one of the four panels, so
   it was silently dropped every single run. Confirmed by comparing row
   counts (20/35/30/24) against a manual read of the fetched PDF text.
   Fixed generically in the engine (`snap_table_by_headers`'s new
   `header_margin` parameter -- see scrapers/base.py) rather than here,
   since this is a real property of *this* PDF's rendering, not
   something a per-terminal field mapping can work around; called here
   with `header_margin=0.1` (down from the engine's 1.0 default).

3. TWO "VCN" COLUMNS (and one "PCS") on the same header row, alongside
   "Voyage No." and "VESSEL NAME" -- both VCN columns are unlabeled
   boundary lanes we don't map to our schema, but without declaring them
   as lanes, "Voyage No." and "VESSEL NAME" swallow each other's
   neighbouring VCN digits (nearest-lane-wins with nothing declared in
   between). `disambiguate_leftmost` (pdf_common.py) relabels the
   leftmost of the two "VCN" occurrences per panel so both get their own
   lane; "PCS" only appears once per panel but is included the same way
   for symmetry/safety.

4. GLUED DATE+TIME, NO COLON, NO SLASH. "ATA / ETA" prints as e.g.
   "12-Sep Sat 1600" and "Gate Cut Off" as "12-Sep 0300" -- a bare
   4-digit HHMM glued straight onto the date with nothing marking it as
   a time at all (JNPT's own reports at least use a colon or a "/").
   `pdf_common.insert_glued_time_colon` reinserts the colon so
   `parse_relative_datetime` can read it normally; report_date supplies
   the year, as everywhere else. "ETB" (estimated time of berthing) is
   also published but has no home in our schema (`eta` is the one
   generic arrival-time field every terminal maps its own "the vessel is
   expected at ___" column onto) -- left in `raw` for staging, not
   promoted to a canonical column.

WHAT'S DELIBERATELY NOT IMPLEMENTED YET: "VESSELS ON BERTH AT ADANI
CTs" and "VESSELS SAILED IN LAST 24 HRS AT ADANI CTs". Checked on the
same live fetch and found genuinely corrupted at the *source* level,
not a lane-mapping problem this engine can fix: several words in the
VESSEL NAME (and, for AICTPL/ACMTPL specifically, nearly every) column
render with two DIFFERENT words sharing the *identical* x0/top -- i.e.
two separate PDF text-drawing operations stacked exactly on top of each
other (e.g. AMCT's on-berth row 1 has both "V"/"ZHAC" starting at
x0=351.9, top=71.6; the real vessel name, "ZHONG GU TAI YUAN", is
recoverable by eye from context but not mechanically from the
geometry -- there is no coordinate information left to tell the two
overlapping strings apart). This affects AMCT and T2 too, not only
AICTPL/ACMTPL as first assumed from an earlier, lighter sample. Until/
unless a cleaner export shows up, these two panels are left unscraped
rather than shipping a parser with silently-scrambled vessel names.

Confidence: HIGH on "VESSELS EXPECTED at <TERMINAL>" (all four; row
counts cross-checked against a manual read of the live PDF text) --
that's the only section this module scrapes.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Optional

import pdfplumber

from scrapers.base import ScrapedRow, ScrapeResult, find_phrase_boxes, snap_table_by_headers
from scrapers.pdf_common import (
    PdfTerminalScraper, disambiguate_leftmost, extract_label_value,
    insert_glued_time_colon, parse_relative_datetime,
)

TERMINALS_IN_ORDER = ["AMCT", "T2", "AICTPL", "ACMTPL"]

EXPECTED_HEADERS = [
    "Sr No", "Voyage No.", "VESSEL NAME", "ATA", "ETB", "Agent",
    "Gate Cut Off", "LoA", "Service", "GATE STATUS",
]
# This report's row height (~3.7pt) is far tighter than any JNPT source's --
# see module docstring point 2.
_HEADER_MARGIN = 0.1


def _to_float(s: str):
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _parse_report_date(words: list[dict]) -> Optional[date]:
    # "Adani Ports & SEZ Ltd - Vessel Schedule Report 11-09-26 18:10" --
    # a title line, not a "label: value" pair, and the date sits far
    # enough right of the label text that extract_label_value's default
    # max_x_gap (220) doesn't bridge it.
    raw = extract_label_value(words, "Vessel Schedule Report", max_x_gap=320)
    if not raw:
        return None
    from dateutil import parser as dateutil_parser
    try:
        return dateutil_parser.parse(raw, dayfirst=True, fuzzy=True).date()
    except (ValueError, OverflowError):
        return None


class AdaniMundraScraper(PdfTerminalScraper):
    terminal_code = "MUNDRA_ADANI"  # dispatch/logging label only -- see module docstring

    def __init__(self, url: str = None, fixture_path: str = None):
        super().__init__(
            url or "https://www.adaniports.com/-/media/project/ports/portsandterminals/"
                    "mundra-documents/berthing-report/latest_berthing-report_mundra.pdf",
            fixture_path,
        )

    def parse(self, raw_content: bytes) -> ScrapeResult:
        import io
        from scrapers.base import ParseError
        try:
            pdf = pdfplumber.open(io.BytesIO(raw_content))
        except Exception as e:
            raise ParseError(f"[{self.terminal_code}] not a readable PDF: {e}") from e
        try:
            # Unlike every JNPT source (always one page), this report is
            # two -- stitch every page's words into one continuous
            # coordinate space by offsetting top/bottom by page height *
            # page index, so snap_table_by_headers can run over it as if
            # it were one tall page (see module docstring point 1).
            all_words = []
            for i, page in enumerate(pdf.pages):
                page_words = page.extract_words()
                offset = i * page.height
                for w in page_words:
                    w = dict(w)
                    w["top"] += offset
                    w["bottom"] += offset
                    all_words.append(w)
            if not all_words:
                raise ParseError(f"[{self.terminal_code}] PDF had no extractable text (scanned image?)")
            return self.parse_words(all_words)
        finally:
            pdf.close()

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        report_date = _parse_report_date(words)

        rows = []
        for i, terminal_code in enumerate(TERMINALS_IN_ORDER):
            stop_labels = (
                [f"VESSELS EXPECTED at {TERMINALS_IN_ORDER[i + 1]}"]
                if i + 1 < len(TERMINALS_IN_ORDER)
                else ["Rail Company"]  # ACMTPL's panel is the last thing on the page;
                                        # the rail-destination summary footer follows it
            )
            rows += self._parse_expected_for_terminal(words, terminal_code, stop_labels, report_date)

        return ScrapeResult(report_date=report_date, rows=rows, terminals_seen=set(TERMINALS_IN_ORDER))

    def _parse_expected_for_terminal(self, words: list[dict], terminal_code: str,
                                      stop_labels: list[str], report_date) -> list[ScrapedRow]:
        title_boxes = find_phrase_boxes(words, f"VESSELS EXPECTED at {terminal_code}")
        if not title_boxes:
            return []
        top_after = min(b["top"] for b in title_boxes)

        sr_boxes = [b for b in find_phrase_boxes(words, "Sr No") if b["top"] >= top_after]
        if not sr_boxes:
            return []
        header_row_top = min(b["top"] for b in sr_boxes)
        # Two "VCN" columns (and one "PCS") on this header row that
        # "Voyage No."/"VESSEL NAME" would otherwise bleed into -- see
        # module docstring point 3.
        vcn_label = disambiguate_leftmost(words, "VCN", header_row_top)
        pcs_label = disambiguate_leftmost(words, "PCS", header_row_top)

        raw_rows = snap_table_by_headers(
            words,
            header_labels=EXPECTED_HEADERS + [pcs_label, vcn_label, "VCN"],
            top_after=top_after,
            bottom_before_labels=stop_labels,
            header_margin=_HEADER_MARGIN,
        )

        rows = []
        for r in raw_rows:
            via = r.get("Voyage No.", "").strip()
            vessel_name = r.get("VESSEL NAME", "").strip()
            # The rightmost VCN lane and VESSEL NAME's lane are only
            # ~44pt apart, with nothing declared in between -- nearest-
            # centroid assignment is a near-coin-flip for anything
            # landing close to the midpoint, and a short first word of a
            # vessel name ("DP" in "DP WORLD JEDDAH", "AL" in "AL SEEF")
            # can tip to the VCN side by under a point, silently
            # truncating the name (caught live: both real examples above
            # lost their first word before this fix). VCN itself is
            # always purely numeric, so anything non-numeric that landed
            # in that lane really belongs at the front of the vessel
            # name -- reattach it.
            vcn_match = re.match(r"^([\d,]*)\s*(.*)$", r.get("VCN", "").strip())
            vcn_overflow = vcn_match.group(2) if vcn_match else ""
            if vcn_overflow:
                vessel_name = f"{vcn_overflow} {vessel_name}".strip()
            if not via and not vessel_name:
                continue
            agent = r.get("Agent", "").strip() or None
            # ATA/ETA's own time value renders closer to the ETB lane's
            # x-position than to its own header label -- every row's ETB
            # lane picks up ATA's trailing HHMM as its own FIRST token,
            # ahead of ETB's genuine "DD/MM HHMM" value (blank when this
            # source doesn't publish a separate ETB at all). Confirmed
            # against a live fetch: without this, `eta` silently lost its
            # time-of-day on every single row (e.g. "27-Sep Sun" instead
            # of "27-Sep Sun 1500"). Reattach that first token to ATA
            # before parsing; the rest of ETB has no home in our schema
            # and is discarded either way (see module docstring point 4).
            etb_tokens = r.get("ETB", "").split()
            eta_raw = f"{r.get('ATA', '').strip()} {etb_tokens[0]}".strip() if etb_tokens else r.get("ATA", "")
            fields = {
                "terminal_code": terminal_code,
                "via_no": via or None,
                "vessel_name": vessel_name or None,
                "loa_m": _to_float(r.get("LoA", "")),
                "service": r.get("Service", "").strip() or None,
                # Per the user's own call on how to populate this source:
                # Adani's report only publishes one carrier-identifying
                # column ("Agent"), so both fields take its value rather
                # than leaving shipping_line unset the way APMT does.
                "shipping_line": agent,
                "agent": agent,
                "eta": parse_relative_datetime(insert_glued_time_colon(eta_raw), report_date),
                "gate_cutoff": parse_relative_datetime(
                    insert_glued_time_colon(r.get("Gate Cut Off", "")), report_date
                ),
            }
            rows.append(ScrapedRow(section="expected", fields=fields, raw=r))
        return rows
