"""
NSICT and NSIGT are both DP World-operated and share one report template
(same header row wording, same layout). One parser, two thin subclasses
(nsict.py / nsigt.py) supplying only terminal_code and URL -- this is the
"one engine, small per-terminal config" pattern the whole package follows.

Validated 2026-09-10 against live fetches of both terminals. Two things
were wrong before that:

1. Like BMCT, this report puts three panels on one page -- "VESSELS ON
   BERTH", "SAILED VESSELS", "VESSELS EXPECTED" -- and the first two
   repeat the "VESSEL NAME"/"VIA"/"LOA"/"SERVICE" column labels in their
   own header rows, above the "VESSELS EXPECTED" panel we want.
   `snap_table_by_headers` resolved that ambiguity to the topmost
   occurrence, i.e. the (near-empty) BERTH panel, which is why this was
   producing 0-1 rows instead of the real ~15-40. Fixed the same way as
   BMCT: anchor with `top_after` on the "VESSELS EXPECTED" panel itself.
2. There is no header literally spelled "LINE" anywhere on the page --
   the real column immediately after SERVICE is labeled "VOA", and its
   values (MSK, MSC, ESA, ISL, ...) are recognizable carrier codes, so
   this was the shipping line all along, just under the wrong label
   (previously silently never matched -> shipping_line was always
   None). Renamed the header we search for to "VOA".

There's also no clean "SR" column label to anchor on ("SR." sits so
close to "VESSEL NAME" that adding it as its own lane causes
single-word vessel names to be swallowed whole by the SR lane, leaving
"vessel_name" empty -- worse than not having it). Instead the leading
serial number rides into the front of the VESSEL NAME lane (e.g. "1
BENITA", "2 MAERSK SEBAROK") and gets stripped off in `_parse_expected`
below. Likewise "VOA" has nothing bounding it on the right (ETA/cargo/
gate-cutoff/ICD+CFS pendency columns aren't declared lanes), so it
picks up everything to the end of the row -- only its first token is
the actual line code; the rest is discarded the same way.

ETA AND GATE CUTOFF (added after that fix, same live PDFs): both are
real, unambiguous header labels ("ETA", "GATE CUTOFF") -- no relabeling
trick needed here, unlike BMCT's two "Cut-OFF" words. ETA prints as
"Thu/10/09 06:00" (weekday/day/month, no year -- dateutil handles the
weekday prefix fine on its own). GATE CUTOFF prints as "10/1500" --
day and 24h time glued together with NO month at all, so it gets its
own small parser (`_parse_gate_cutoff`) anchored to the report's own
month/year, with a rollover check for a cutoff landing just after
month-end. IMP/EXP/DRY/REEFER (unlabeled cargo-count columns between
VOA and ETA) are added as boundary-only lanes so they don't bleed into
either.

BERTHED PANEL (added after that): "VESSELS ON BERTH" has its own table
-- BERTH / VESSEL NAME / VIA / LOA / SERVICE / BERTH SIDE / IMPORT /
EXPORT / TTL MVS / ATA / OPS COMMENCE / ETC / ETD -- one row per berth,
often blank (no vessel currently there; both NSICT's berths were empty
on the day this was checked). Sits ABOVE "VESSELS EXPECTED" and repeats
its column labels again in "SAILED VESSELS" just below it, so it needs
the same top_after/bottom_before anchoring, scoped to "VESSELS ON
BERTH"..."SAILED VESSELS" instead. The bare word "BERTH" additionally
matches twice on its own header row -- once as the real Berth-number
column, once as part of "BERTH SIDE" a few columns over --
`_pick_berth_no_word` relabels the leftmost occurrence with a private
sentinel so the lane search binds to the right one. These rows are
kept in their own table (models.BerthedVessel) rather than
vessel_schedule -- see that table's docstring for why.

Confidence: HIGH on all of the above now that row shape has been
checked against real fetched PDFs for both terminals.
"""
import re

from scrapers.base import ScrapedRow, ScrapeResult, find_phrase_boxes, snap_table_by_headers
from scrapers.pdf_common import PdfTerminalScraper, parse_relative_datetime, parse_report_date

EXPECTED_HEADERS = [
    "VESSEL NAME", "VIA", "LOA", "SERVICE", "VOA", "ETA", "GATE CUTOFF",
    # boundary-only lanes: not part of our schema, just here so the
    # unlabeled cargo columns don't bleed into VOA/ETA/GATE CUTOFF, and
    # GATE CUTOFF (nothing else declared to its right) doesn't bleed into
    # the ICD/CFS pendency columns that follow it
    "IMP", "EXP", "DRY", "REEFER", "GATE OPEN", "ICD PENDENCY",
]
EXPECTED_STOP_BEFORE = ["VESSELS ON BERTH", "SAILED VESSELS", "ICD PENDENCY"]

BERTHED_HEADERS = [
    "VESSEL NAME", "VIA", "LOA", "SERVICE", "BERTH SIDE",
    "IMPORT", "EXPORT", "TTL MVS", "ATA", "OPS COMMENCE", "ETC", "ETD",
]
BERTHED_STOP_BEFORE = ["SAILED VESSELS"]

_BERTH_NO_SENTINEL = "__BERTH_NO__"


def _to_float(s: str):
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _degarble_char_spaced(s: str) -> str:
    """Very rarely (seen live on one row out of ~37) pdfplumber extracts
    part of a row -- VOA/ETA/GATE CUTOFF, never the left-hand columns --
    as one "word" per individual CHARACTER instead of per token, which
    `snap_table_by_headers` then joins back with a space between every
    letter ("F r i / 2 5 / 0 9 0 4 : 0 0"). A font/kerning quirk in the
    source PDF for that specific line, not a column-snapping issue.
    Detect it (every token is exactly one character) and collapse it
    back into one string; a no-op on any normally-extracted value."""
    tokens = s.split()
    if tokens and all(len(t) == 1 for t in tokens):
        return "".join(tokens)
    return s


def _to_int(s: str):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return int(float(s.replace(",", "")))
    except ValueError:
        return None


def _pick_berth_no_word(words: list[dict], header_row_top: float) -> None:
    """The bare word "BERTH" matches twice on this header row: the real
    Berth-number column (leftmost) and the one embedded in "BERTH SIDE"
    a few columns over. Relabel the leftmost with a private sentinel so
    `snap_table_by_headers` can bind a lane to it without also matching
    "BERTH SIDE"'s. Mutates `words` in place; a no-op if the header
    wording ever drops to fewer than two matches on this row."""
    candidates = [w for w in words
                  if w["text"].strip().upper() == "BERTH" and abs(w["top"] - header_row_top) < 3]
    if len(candidates) < 2:
        return
    berth_no_word = min(candidates, key=lambda w: w["x0"])
    berth_no_word["text"] = _BERTH_NO_SENTINEL


def _parse_gate_cutoff(s: str, report_date, max_backward_days: int = 20):
    """"10/1500" -- day and 24h time glued together, with NO month at all
    (unlike ETA, which at least carries day/month). Anchored to the
    report's own month/year, with a rollover check for a cutoff landing
    just after month-end."""
    s = (s or "").strip()
    if not s or report_date is None:
        return None
    m = re.match(r"^(\d{1,2})/(\d{3,4})$", s)
    if not m:
        return None
    day = int(m.group(1))
    hhmm = m.group(2).zfill(4)
    try:
        from datetime import datetime
        dt = datetime(report_date.year, report_date.month, day, int(hhmm[:2]), int(hhmm[2:]))
    except ValueError:
        return None
    if (dt.date() - report_date).days < -max_backward_days:
        month, year = report_date.month + 1, report_date.year
        if month > 12:
            month, year = 1, year + 1
        try:
            dt = dt.replace(year=year, month=month)
        except ValueError:
            return None
    return dt


class DpWorldTerminalScraper(PdfTerminalScraper):
    """Base for the DP World template. Subclasses set terminal_code + URL."""

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        report_date = parse_report_date(words, ["DATE:", "DATE :", "DATE"])

        rows = []
        rows += self._parse_berthed(words, report_date)
        rows += self._parse_expected(words, report_date)

        return ScrapeResult(report_date=report_date, rows=rows)

    def _parse_berthed(self, words: list[dict], report_date) -> list[ScrapedRow]:
        berthed_panel_boxes = find_phrase_boxes(words, "VESSELS ON BERTH")
        top_after = min((b["top"] for b in berthed_panel_boxes), default=None)
        if top_after is None:
            return []

        vessel_name_boxes = [b for b in find_phrase_boxes(words, "VESSEL NAME") if b["top"] >= top_after]
        if not vessel_name_boxes:
            return []
        header_row_top = min(b["top"] for b in vessel_name_boxes)
        _pick_berth_no_word(words, header_row_top)

        raw_rows = snap_table_by_headers(
            words,
            header_labels=BERTHED_HEADERS + [_BERTH_NO_SENTINEL],
            top_after=top_after,
            bottom_before_labels=BERTHED_STOP_BEFORE,
            min_filled=2,
        )

        rows = []
        for r in raw_rows:
            vessel_name = r.get("VESSEL NAME", "").strip() or None
            via = r.get("VIA", "").strip()
            if not vessel_name and not via:
                continue  # an empty berth slot
            fields = {
                "terminal_code": self.terminal_code,
                "berth_no": r.get(_BERTH_NO_SENTINEL, "").strip() or None,
                "vessel_name": vessel_name,
                "via_no": via or None,
                "loa_m": _to_float(r.get("LOA", "")),
                "service": r.get("SERVICE", "").strip() or None,
                "side": r.get("BERTH SIDE", "").strip() or None,
                "alongside_at": parse_relative_datetime(r.get("ATA", ""), report_date),
                "ops_commenced_at": parse_relative_datetime(r.get("OPS COMMENCE", ""), report_date),
                "ops_completed_at": parse_relative_datetime(r.get("ETC", ""), report_date),  # ETC doubles
                                                                                              # as "ops completed
                                                                                              # by" here -- see
                                                                                              # module docstring
                "next_event_at": parse_relative_datetime(r.get("ETD", ""), report_date),
                "import_moves": _to_int(r.get("IMPORT", "")),
                "export_moves": _to_int(r.get("EXPORT", "")),
            }
            rows.append(ScrapedRow(section="berthed", fields=fields, raw=r))
        return rows

    def _parse_expected(self, words: list[dict], report_date) -> list[ScrapedRow]:
        # This page also carries "VESSELS ON BERTH" and "SAILED VESSELS"
        # panels above this one, repeating the same column labels in their
        # own headers -- anchor past those so the lanes bind to *this*
        # panel's header row, not an earlier one (see module docstring).
        expected_panel_boxes = find_phrase_boxes(words, "VESSELS EXPECTED")
        top_after = min((b["top"] for b in expected_panel_boxes), default=None)

        raw_rows = snap_table_by_headers(
            words,
            header_labels=EXPECTED_HEADERS,
            top_after=top_after,
            bottom_before_labels=EXPECTED_STOP_BEFORE,
        )

        rows = []
        for r in raw_rows:
            via = r.get("VIA", "").strip()
            if not via:
                continue
            # The lane has no "SR" column to its left bounding it, so the
            # row's leading serial number rides into this lane's text --
            # strip it back off (see module docstring).
            vessel_name = re.sub(r"^\d+\s+", "", r.get("VESSEL NAME", "")).strip() or None
            # "VOA" has nothing bounding it on the right, so it picks up
            # every later column's text too -- only the first token is
            # the actual line code.
            voa_tokens = _degarble_char_spaced(r.get("VOA", "")).split()
            eta_raw = _degarble_char_spaced(r.get("ETA", ""))
            # Collapsing the char-spaced form can glue the date to the
            # time (no token marks where the real space belonged) --
            # reinsert it for ETA's known "Xxx/DD/MM" + "HH:MM" shape.
            m = re.match(r"^([A-Za-z]{3}/\d{2}/\d{2})(\d{2}:\d{2})$", eta_raw)
            if m:
                eta_raw = f"{m.group(1)} {m.group(2)}"
            fields = {
                "terminal_code": self.terminal_code,
                "via_no": via,
                "vessel_name": vessel_name,
                "loa_m": _to_float(r.get("LOA", "")),
                "service": r.get("SERVICE", "").strip() or None,
                "shipping_line": voa_tokens[0] if voa_tokens else None,
                "agent": None,
                "eta": parse_relative_datetime(eta_raw, report_date),
                "gate_cutoff": _parse_gate_cutoff(_degarble_char_spaced(r.get("GATE CUTOFF", "")), report_date),
            }
            rows.append(ScrapedRow(section="expected", fields=fields, raw=r))

        return rows
