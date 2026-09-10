"""
Nhava Sheva Freeport Terminal (NSFT).

Validated 2026-09-10 against a live fetch. Two things were wrong:

1. The "Vessel Name" claim in the original docstring didn't hold on the
   live PDF -- "Vessels Expected"'s real header row is "SR No / Vessel
   Name / VIA No / LOA / Service / Line / ETA / ...", i.e. Vessel Name
   IS its own column here, right next to SR No. No cross-panel merge is
   needed at all; `merge_column_by_row` (still in `pdf_common.py` for
   any future terminal that does need it) has been dropped from this
   file.
2. Same multi-panel-on-one-page problem as BMCT/NSICT/NSIGT/APMT: this
   page has "Vessel Sailed in last 24 hours" and "Vessel at Berth"
   panels above "Vessels Expected", and all three repeat the "SR No" /
   "VIA No" / "LOA" / "Service" / "Line" column labels in their own
   header rows. `snap_table_by_headers` resolved that to the topmost
   (wrong, "Sailed") panel, and `EXPECTED_STOP_BEFORE`'s "Yard
   Inventory" phrase (which sits just after the *second* panel's
   header) then cut the data window off almost immediately -- 0 rows.
   Fixed the same way as the others: anchor with `top_after` on the
   "Vessels Expected" panel itself.

ETA AND GATE CUT-OFF (added after that fix, same live PDF): both are
real, unambiguous header labels here. ETA prints "07-09-2026 23:00"
(full date, no anchoring needed). Gate Cut-off is trickier: the header
group is "Gate Open / Gate Cut-off", each of which ALSO splits into
"Dry container" / "Reefer container" sub-columns -- four Date/Time
values between ETA and the Import/Export TEU counts, only two of which
("Gate Open", "Gate Cut-off") have their own clean top-level label. A
plain lane for "Gate Cut-off" ends up bounded only by "Import TEUs" to
its right, so it picks up BOTH its Dry and Reefer sub-values (usually
identical) plus a stray leading digit from the TEU count that follows
-- rather than fight that sub-column split with more relabeling tricks,
`_extract_gate_cutoff` just regex-searches that wider blob for the
first "DD-MM-YYYY HH:MM" pattern, which is reliably the Dry-container
(first, general) cut-off. "Gate Open" is added purely as a boundary
lane so it doesn't bleed into Gate Cut-off's own text.

BERTHED PANEL (added after that): "Vessel at Berth" has its own table
-- SR No / Vessel Name / VIA No / LOA / Service / Line / Berthed /
Ops. Commenced / ETC / Import Moves / Import Balance / Export Moves /
Export Balance -- one row seen live. Sits between "Vessel Sailed in
last 24 hours" and "Vessels Expected" and repeats their shared column
labels, so it gets the same top_after/bottom_before anchoring, scoped
to "Vessel at Berth"..."Vessels Expected" instead. These rows are kept
in their own table (models.BerthedVessel) rather than vessel_schedule
-- see that table's docstring for why.

Confidence: HIGH on SR No/Vessel Name/VIA No/LOA/Service/Line/ETA/Gate
Cut-off/berthed-panel fields now that row shape has been checked
against a real fetched PDF.
"""
import re

from scrapers.base import ScrapedRow, ScrapeResult, find_phrase_boxes, snap_table_by_headers
from scrapers.pdf_common import PdfTerminalScraper, parse_relative_datetime, parse_report_date

EXPECTED_HEADERS = ["SR No", "Vessel Name", "VIA No", "LOA", "Service", "Line",
                    "ETA", "Gate Open", "Gate Cut-off", "Import TEUs", "Export TEUs"]
EXPECTED_STOP_BEFORE = ["TOTAL ICD PENDENCY", "TOTAL CFS PENDENCY"]

BERTHED_HEADERS = ["SR No", "Vessel Name", "VIA No", "LOA", "Service", "Line",
                   "Berthed", "Ops. Commenced", "ETC",
                   "Import Moves", "Import Balance", "Export Moves", "Export Balance"]
BERTHED_STOP_BEFORE = ["Vessels Expected"]

_GATE_CUTOFF_RE = re.compile(r"\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}")


def _to_float(s: str):
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _to_int(s: str):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return int(float(s.replace(",", "")))
    except ValueError:
        return None


def _extract_gate_cutoff(s: str):
    """The "Gate Cut-off" lane also picks up its own Dry/Reefer
    sub-column split (usually identical values) plus a stray leading
    digit from the TEU count after it -- regex out just the first
    "DD-MM-YYYY HH:MM", which is reliably the (Dry-container, general)
    cut-off itself. See module docstring."""
    m = _GATE_CUTOFF_RE.search(s or "")
    return m.group() if m else None


class NsftScraper(PdfTerminalScraper):
    terminal_code = "NSFT"

    def __init__(self, url: str = None, fixture_path: str = None):
        super().__init__(
            url or "https://www.jnport.gov.in/uploads/berthing_report/pdf/15/Daily_Berthing_Report_9_9_2026.pdf",
            fixture_path,
        )

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        report_date = parse_report_date(words, ["Date", "Date "])

        rows = []
        rows += self._parse_berthed(words, report_date)
        rows += self._parse_expected(words, report_date)

        return ScrapeResult(report_date=report_date, rows=rows)

    def _parse_berthed(self, words: list[dict], report_date) -> list[ScrapedRow]:
        berth_panel_boxes = find_phrase_boxes(words, "Vessel at Berth")
        if not berth_panel_boxes:
            return []
        top_after = min(b["bottom"] for b in berth_panel_boxes) + 0.5

        raw_rows = snap_table_by_headers(
            words,
            header_labels=BERTHED_HEADERS,
            top_after=top_after,
            bottom_before_labels=BERTHED_STOP_BEFORE,
            min_filled=2,
        )

        rows = []
        for r in raw_rows:
            vessel_name = r.get("Vessel Name", "").strip() or None
            via = r.get("VIA No", "").strip()
            if not vessel_name and not via:
                continue
            fields = {
                "terminal_code": self.terminal_code,
                "vessel_name": vessel_name,
                "via_no": via or None,
                "loa_m": _to_float(r.get("LOA", "")),
                "service": r.get("Service", "").strip() or None,
                "shipping_line": r.get("Line", "").strip() or None,
                "alongside_at": parse_relative_datetime(r.get("Berthed", ""), report_date),
                "ops_commenced_at": parse_relative_datetime(r.get("Ops. Commenced", ""), report_date),
                "next_event_at": parse_relative_datetime(r.get("ETC", ""), report_date),
                "import_moves": _to_int(r.get("Import Moves", "")),
                "export_moves": _to_int(r.get("Export Moves", "")),
            }
            rows.append(ScrapedRow(section="berthed", fields=fields, raw=r))
        return rows

    def _parse_expected(self, words: list[dict], report_date) -> list[ScrapedRow]:
        # This page also carries "Vessel Sailed in last 24 hours" and
        # "Vessel at Berth" panels above this one, repeating the same
        # column labels in their own headers -- anchor past those so the
        # lanes bind to *this* panel's header row (see module docstring).
        expected_panel_boxes = find_phrase_boxes(words, "Vessels Expected")
        top_after = min((b["top"] for b in expected_panel_boxes), default=None)

        raw_rows = snap_table_by_headers(
            words,
            header_labels=EXPECTED_HEADERS,
            top_after=top_after,
            bottom_before_labels=EXPECTED_STOP_BEFORE,
        )

        rows = []
        for r in raw_rows:
            via = r.get("VIA No", "").strip()
            if not via:
                continue
            fields = {
                "terminal_code": self.terminal_code,
                "via_no": via,
                "vessel_name": r.get("Vessel Name", "").strip() or None,
                "loa_m": _to_float(r.get("LOA", "")),
                "service": r.get("Service", "").strip() or None,
                "shipping_line": r.get("Line", "").strip() or None,
                "agent": None,
                "eta": parse_relative_datetime(r.get("ETA", ""), report_date),
                "gate_cutoff": parse_relative_datetime(_extract_gate_cutoff(r.get("Gate Cut-off", "")), report_date),
            }
            rows.append(ScrapedRow(section="expected", fields=fields, raw=r))

        return rows
