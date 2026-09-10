"""
Bharat Mumbai Container Terminal (BMCT, operated by PSA International).

Validated 2026-09-10 against a live fetch. The BMCT PDF puts THREE
panels on one page -- "VESSELS ON BERTHED", "SAILED VESSEL", and
"VESSELS EXPECTED ICD CFS" -- and the first two repeat the column
labels "LOA" and "Draft" in their own header rows, well above the
"VESSELS EXPECTED" panel we actually want. `snap_table_by_headers`
resolves an ambiguous label to its topmost occurrence on the page, so
without a `top_after` floor it was locking the "LOA" and "Draft" lanes
onto the BERTHED panel's header instead -- which put the "Draft" lane
far out at the BERTHED table's rightmost "Max Draft" column, causing
every unlabeled column between Draft and the page's right edge (ETA,
cargo counts, gate/reefer cut-off timestamps, CFS dest/moves/teus) to
collapse into whichever of LOA/Draft was nearest. VIA No./Vessel
Name/Line/Service aren't repeated elsewhere on the page so they came
through fine even before this fix -- only LOA and Draft were wrong,
and since `_to_float()` on the resulting garbage string just returns
None, it failed silently (loa_m NULL for every row) rather than
raising, so treat "run succeeded" as necessary but not sufficient here.
Fixed by anchoring the header search to the "VESSELS EXPECTED" panel
itself via `top_after`.

ETA and gate cut-off (added after that fix, same live PDF): the real
header row reads "ETA / CARGO / Gate Open / Reefer Opening / Reefer
Cut-OFF / Cut-OFF" left to right, each a Date(+Time) column with no
lane of its own previously -- so both were getting swallowed into
whichever of LOA/Draft/nothing was nearest before, and even with those
two fixed would still bleed into each other without dedicated lanes.
Added CARGO/Gate Open/Reefer Opening/Reefer Cut-OFF/Dest purely as
*boundary* lanes (their values aren't part of our schema and are
discarded) so ETA and the final "Cut-OFF" column resolve cleanly.

The final "Cut-OFF" column is the general gate cut-off (paired with
"Gate Open"); "Reefer Cut-OFF" a few columns to its left is a distinct,
reefer-specific deadline we don't want. Both header rows contain the
literal word "Cut-OFF" (one embedded in the phrase "Reefer Cut-OFF",
one standalone), so a plain label search can't tell them apart --
`_pick_gate_cutoff_word` finds both occurrences on the header row and
relabels the rightmost (standalone) one with a private sentinel before
handing the word list to `snap_table_by_headers`, so the lane search
binds to exactly that one word.

ETA prints without a year ("10-Sep 08:00"); gate cut-off prints with a
2-digit one ("09-Sep-26 16:00"). Both are parsed relative to the
report's own date so a same-day fetch never mis-attributes the year.

BERTHED PANEL (added after that): "VESSELS ON BERTHED" has its own
table -- Berth / Vessel / VIA / LOA / Berthing Side / [Alongside,
Ops Commenced, Ops Completed, ETD each Date+Time] / IMP / IMP BAL /
EXP / EXP BAL / Max Draft -- one row per berth (BMCT01..BMCT06), some
of which are simply blank (no vessel currently there). This panel sits
ABOVE "VESSELS EXPECTED" (and its own column labels repeat again in
"SAILED VESSEL" just below it), so it needs the same top_after/
bottom_before anchoring, scoped to "VESSELS ON BERTHED"..."SAILED
VESSEL" instead. These rows are kept in their own table
(models.BerthedVessel) rather than vessel_schedule -- see that table's
docstring for why. "IMP"/"EXP" print "NIL" instead of a number when a
vessel hasn't started that side of cargo ops yet; `_to_int` treats
that the same as a blank.

Confidence: HIGH for VIA/Vessel Name/Line/Service/Draft/LOA/ETA/gate
cut-off/berthed-panel fields now that row shape matches the real PDF;
re-spot-check if JNPT changes this one-page-three-panels layout or any
of the column orders noted above.
"""
import re

from dateutil import parser as dateutil_parser

from scrapers.base import ScrapedRow, ScrapeResult, find_phrase_boxes, snap_table_by_headers
from scrapers.pdf_common import PdfTerminalScraper, parse_relative_datetime, parse_report_date

EXPECTED_HEADERS = [
    "VIA No.", "LOA", "Vessel Name", "Line", "Draft", "Service",
    # boundary-only lanes below: not part of our schema, just here so
    # they don't bleed into ETA / gate cut-off (see module docstring)
    "ETA", "CARGO", "Gate Open", "Reefer Opening", "Reefer Cut-OFF", "Dest",
]
EXPECTED_STOP_BEFORE = ["VESSELS ON BERTH", "SAILED VESSEL", "VESSEL SAILED"]

BERTHED_HEADERS = [
    "Berth", "Vessel", "VIA", "LOA", "Berthing", "Side",
    "Alongside", "Ops Commenced", "Ops Completed", "ETD",
    "IMP", "IMP BAL", "EXP", "EXP BAL", "Max", "Draft",
]
BERTHED_STOP_BEFORE = ["SAILED VESSEL"]

_GATE_CUTOFF_SENTINEL = "__GATE_CUTOFF__"


def _to_float(s: str):
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _to_int(s: str):
    """BMCT prints "NIL" instead of a number when a vessel hasn't started
    that side of cargo ops yet -- treat it the same as blank."""
    s = (s or "").strip()
    if not s or s.upper() == "NIL":
        return None
    try:
        return int(float(s.replace(",", "")))
    except ValueError:
        return None


def _pick_gate_cutoff_word(words: list[dict]) -> None:
    """The header row has TWO words reading "Cut-OFF": one inside the
    phrase "Reefer Cut-OFF", one standalone (the general gate cut-off,
    a few columns further right). Relabel the rightmost one with a
    private sentinel so `snap_table_by_headers` can bind a lane to it
    without also matching the "Reefer Cut-OFF" one. Mutates `words` in
    place; a no-op if the header wording ever drops to fewer than two
    matches (the lane just won't be found, same as any other
    schema-drift case)."""
    candidates = [w for w in words if w["text"].strip().upper() == "CUT-OFF"]
    if len(candidates) < 2:
        return
    gate_cutoff_word = max(candidates, key=lambda w: w["x0"])
    gate_cutoff_word["text"] = _GATE_CUTOFF_SENTINEL


def _parse_dt_no_year(s: str, report_date) -> "datetime | None":
    """Several BMCT date/time columns ("10-Sep 08:00" style) print with
    no year -- anchor them to the report's own date so a same-day fetch
    can't mis-attribute one."""
    s = (s or "").strip()
    if not s:
        return None
    # Seen live: an occasional stray "." before the ":" in the time
    # ("12.:30" for "12:30") -- a source typo, not a column-snapping
    # issue. Quietly repair it rather than dropping the value.
    s = re.sub(r"(\d)\.:(\d)", r"\1:\2", s)
    return parse_relative_datetime(s, report_date)


def _parse_dt_with_year(s: str) -> "datetime | None":
    """'09-Sep-26 16:00' already carries its own year -- no anchoring
    needed."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        return dateutil_parser.parse(s, dayfirst=True)
    except (ValueError, OverflowError):
        return None


class BmctScraper(PdfTerminalScraper):
    terminal_code = "BMCT"

    def __init__(self, url: str = None, fixture_path: str = None):
        super().__init__(
            url or "https://www.jnport.gov.in/uploads/berthing_report/pdf/17/Berthing_Sheet_09_SEP_2026.pdf",
            fixture_path,
        )

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        report_date = parse_report_date(words, ["Date :", "Date:", "Date"])

        rows = []
        rows += self._parse_berthed(words, report_date)
        rows += self._parse_expected(words, report_date)

        return ScrapeResult(report_date=report_date, rows=rows)

    def _parse_berthed(self, words: list[dict], report_date) -> list[ScrapedRow]:
        berthed_panel_boxes = find_phrase_boxes(words, "VESSELS ON BERTHED")
        top_after = min((b["top"] for b in berthed_panel_boxes), default=None)
        if top_after is None:
            return []  # panel not found at all -- treat like any other schema-drift miss

        raw_rows = snap_table_by_headers(
            words,
            header_labels=BERTHED_HEADERS,
            top_after=top_after,
            bottom_before_labels=BERTHED_STOP_BEFORE,
            min_filled=2,
        )

        rows = []
        for r in raw_rows:
            vessel_name = r.get("Vessel", "").strip() or None
            via = r.get("VIA", "").strip()
            if not vessel_name and not via:
                continue  # an empty berth slot (e.g. "BMCT02" with nothing else)
            fields = {
                "terminal_code": self.terminal_code,
                "berth_no": r.get("Berth", "").strip() or None,
                "vessel_name": vessel_name,
                "via_no": via or None,
                "loa_m": _to_float(r.get("LOA", "")),
                "draft_m": _to_float(r.get("Draft", "")),
                "side": r.get("Berthing", "").strip() or None,
                "alongside_at": _parse_dt_no_year(r.get("Alongside", ""), report_date),
                "ops_commenced_at": _parse_dt_no_year(r.get("Ops Commenced", ""), report_date),
                "ops_completed_at": _parse_dt_no_year(r.get("Ops Completed", ""), report_date),
                "next_event_at": _parse_dt_no_year(r.get("ETD", ""), report_date),  # estimated departure
                "import_moves": _to_int(r.get("IMP", "")),
                "export_moves": _to_int(r.get("EXP", "")),
            }
            rows.append(ScrapedRow(section="berthed", fields=fields, raw=r))
        return rows

    def _parse_expected(self, words: list[dict], report_date) -> list[ScrapedRow]:
        # This page also carries "VESSELS ON BERTHED" and "SAILED VESSEL"
        # panels above this one, repeating the "LOA"/"Draft" column labels
        # in their own headers -- anchor past those so the lanes bind to
        # *this* panel's header row, not an earlier one (see module
        # docstring).
        expected_panel_boxes = find_phrase_boxes(words, "VESSELS EXPECTED")
        top_after = min((b["top"] for b in expected_panel_boxes), default=None)

        _pick_gate_cutoff_word(words)

        raw_rows = snap_table_by_headers(
            words,
            header_labels=EXPECTED_HEADERS + [_GATE_CUTOFF_SENTINEL],
            top_after=top_after,
            bottom_before_labels=EXPECTED_STOP_BEFORE,
            min_filled=2,  # lower bar than other terminals -- rows here are more sparse
        )

        rows = []
        for r in raw_rows:
            via = r.get("VIA No.", "").strip()
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
                "eta": _parse_dt_no_year(r.get("ETA", ""), report_date),
                "gate_cutoff": _parse_dt_with_year(r.get(_GATE_CUTOFF_SENTINEL, "")),
            }
            rows.append(ScrapedRow(section="expected", fields=fields, raw=r))
        return rows
