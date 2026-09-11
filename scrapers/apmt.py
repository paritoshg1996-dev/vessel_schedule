"""
APM Terminals Mumbai ("APMT", operates GTI berths APM01/APM02).

Validated 2026-09-10 against a live fetch. Three things were wrong:

1. Same multi-panel-on-one-page problem as BMCT/NSICT/NSIGT: this page
   has TWO "ON BERTH VESSEL" panels (one per berth side) above the
   "Vessels Expected" panel we want, and all three repeat the "VIA" and
   "LOA" column labels in their own header rows. `snap_table_by_headers`
   resolved that to the topmost (wrong) occurrence, which put the VIA
   lane's x-position under the ON BERTH panel's VIA column instead of
   the real one -- so almost no row had a non-empty VIA, and the ~8
   rows that *did* pass the `if via: continue` filter were garbage
   (phone numbers and footer text from "Customer Service Desk", the
   monthly-summary "Group ALT/SMS/SVL" block, etc. -- accidentally
   landing in the VIA lane and getting written to vessel_schedule as if
   they were real vessels). Fixed the same way as BMCT: anchor with
   `top_after` on the "Vessels Expected" panel itself.
2. `EXPECTED_STOP_BEFORE` named phrases ("ON BERTH VESSEL", "APM
   Terminals Mumbai") that sit ABOVE the Vessels Expected panel, so they
   can never bound its bottom.

   CAUGHT LIVE 2026-09-11, a day after the above shipped: I'd originally
   bounded the bottom with "Group ALT", the first line of the monthly
   cargo-summary block below this panel -- but "ALT" there isn't a fixed
   label, it's DATA: the summary ranks destination codes by that day's
   TEU volume, so whichever code tops the list becomes "Group ALT" (or
   "Group CLP", or anything else) depending on the day. The morning this
   changed, "Group ALT" simply wasn't found anywhere on the page, so no
   bottom bound was set at all, and every row of that footer -- phone
   numbers, "Customer Service Desk", the whole cargo-summary block --
   got swept in as if it were vessel data (via lane picking up garbage
   like "GROUP"/"CUSTOMER"/"CARGODESK"/"GATE:", closest lane wins with
   nothing to stop it). Fixed by anchoring on "CFS PENDENCY" instead --
   the actual (fixed) header phrase directly above that block, same
   stable-structural-label pattern NSICT/NSFT already use for their own
   "...PENDENCY" boundaries. Lesson: a stop-before/top_after anchor must
   be verified as a fixed label, not a value that can vary with the
   day's data -- re-check this if APMT's footer layout changes again.
3. The header row has FOUR unlabeled date/time columns (Gate Open,
   Reefer Opening, Reefer Cut-Off, Cut-Off) between LOA and Service, and
   two more (Imp/Exp counts) after Line, with no lanes of their own.
   That makes LOA and Line each swallow real-value-first-then-garbage
   (their nearest lane is to their right), while Service swallows
   garbage-then-real-value-last (its nearest lane is to its *left*,
   across that 4-column gap) -- so the fields below take the first
   token for LOA/Line but the *last* token for Service. Added "Draft"
   as a lane purely to keep it from being absorbed into Vessel Name/LOA
   (its own value isn't in our schema, so it's discarded either way).

ETA AND GATE CUTOFF (added after that fix, same live PDF): the group
header above the expected table reads "Vessel ETA / ARRIVAL BFL / Gate
Open / Reefer Opening / Reefer Cut-Off / Cut-Off". "ETA" itself is an
unambiguous bare label here (unlike BMCT/NSICT, nothing else on the
page reuses that exact word), so it needs no relabeling trick. The
final "Cut-Off" column is the general gate cut-off (paired with "Gate
Open"); "Reefer Cut-Off" a few columns to its left is a distinct,
reefer-specific deadline. Both header rows contain the literal word
"Cut-Off" (once embedded in "Reefer Cut-Off", once standalone) so a
plain label search can't tell them apart -- same fix as BMCT:
`_pick_gate_cutoff_word` relabels the rightmost (standalone) occurrence
with a private sentinel before the lane search runs. ETA prints
without a year ("10-Sep 21:00"); gate cut-off prints with one
("10-Sep-26 23:00") -- both anchored/parsed via
`pdf_common.parse_relative_datetime`, same as every other terminal.

BERTHED PANEL (added after that): the FIRST "ON BERTH VESSEL" panel
(APM01/APM02, whichever is currently alongside) is what we want; the
SECOND repeats the same header wording but for vessels that have
already sailed (it ends in "Sailing Time" instead of "ETC" -- no
distinct section title of its own, just a second copy of the header
row). Bounded with `top_after` on "ON BERTH VESSEL" and
`bottom_before_labels=["Sailing Time"]` so only the first table's rows
are read. The bare words "Imp" and "Exp" each match twice on this
header row (once as their own column, once embedded in "Imp Bal" /
"Exp Bal" a few columns over) -- `disambiguate_leftmost` (in
pdf_common.py) relabels the leftmost (real) occurrence of each so the
lane search binds correctly.

Confidence: HIGH now that row shape has been checked against a real
fetched PDF for both the expected-vessel and berthed panels.
"""
import re

from scrapers.base import ScrapedRow, ScrapeResult, find_phrase_boxes, snap_table_by_headers
from scrapers.pdf_common import (
    PdfTerminalScraper, disambiguate_leftmost, parse_relative_datetime, parse_report_date,
)

EXPECTED_HEADERS = ["VIA", "Vessel Name", "Draft", "LOA", "Service", "Line"]
EXPECTED_STOP_BEFORE = ["CFS PENDENCY"]

BERTHED_HEADERS = [
    "Berth", "Vessel", "VIA", "LOA", "Alongside", "Berthing", "Side",
    "Ops Commenced", "Ops Completed", "QC Boom up", "Imp Bal", "Exp Bal",
    "Arrival", "BFL", "Max", "Draft", "ETC",
]
BERTHED_STOP_BEFORE = ["Sailing Time"]

_GATE_CUTOFF_SENTINEL = "__GATE_CUTOFF__"


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


def _pick_gate_cutoff_word(words: list[dict], near_top: float) -> None:
    """The expected-panel header row has TWO words reading "Cut-Off": one
    inside "Reefer Cut-Off", one standalone (the general gate cut-off, a
    few columns further right). Relabel the rightmost with a private
    sentinel so the lane search binds to exactly that one, not the
    "Reefer Cut-Off" one. Mutates `words` in place; a no-op if the
    header wording ever drops to fewer than two matches."""
    candidates = [w for w in words
                  if w["text"].strip().upper() == "CUT-OFF" and abs(w["top"] - near_top) < 3]
    if len(candidates) < 2:
        return
    gate_cutoff_word = max(candidates, key=lambda w: w["x0"])
    gate_cutoff_word["text"] = _GATE_CUTOFF_SENTINEL


class ApmtScraper(PdfTerminalScraper):
    terminal_code = "APMT"

    def __init__(self, url: str = None, fixture_path: str = None):
        super().__init__(
            url or "https://www.jnport.gov.in/uploads/berthing_report/pdf/16/APMT_Berthing_Report_-_09-Sep-2026.pdf",
            fixture_path,
        )

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        report_date = parse_report_date(words, ["Date :", "Date:", "Date"])

        rows = []
        rows += self._parse_berthed(words, report_date)
        rows += self._parse_expected(words, report_date)

        return ScrapeResult(report_date=report_date, rows=rows)

    def _parse_berthed(self, words: list[dict], report_date) -> list[ScrapedRow]:
        berthed_panel_boxes = find_phrase_boxes(words, "ON BERTH VESSEL")
        if not berthed_panel_boxes:
            return []
        # Anchor on the title's BOTTOM, not its top: the title text itself
        # ("ON BERTH VESSEL") contains the literal word "Berth", so a
        # >=top comparison would let the title's own line match as a
        # "Berth" header candidate.
        top_after = min(b["bottom"] for b in berthed_panel_boxes) + 0.5

        loa_boxes = [b for b in find_phrase_boxes(words, "LOA") if b["top"] >= top_after]
        if not loa_boxes:
            return []
        header_row_top = min(b["top"] for b in loa_boxes)
        imp_label = disambiguate_leftmost(words, "Imp", header_row_top)
        exp_label = disambiguate_leftmost(words, "Exp", header_row_top)

        raw_rows = snap_table_by_headers(
            words,
            header_labels=BERTHED_HEADERS + [imp_label, exp_label],
            top_after=top_after,
            bottom_before_labels=BERTHED_STOP_BEFORE,
            min_filled=2,
        )

        rows = []
        for r in raw_rows:
            # "Berth" and "Vessel" sit close enough together that a short
            # first word of the vessel name (e.g. "OOCL") can land in the
            # Berth lane instead -- the berth code itself is reliably the
            # combined text's first token ("APM01", "APM02", ...), so
            # split on that rather than trusting the lane boundary.
            combined = f"{r.get('Berth', '').strip()} {r.get('Vessel', '').strip()}".strip()
            berth_no, _, vessel_name = combined.partition(" ")
            berth_no = berth_no or None
            vessel_name = vessel_name.strip() or None
            via = r.get("VIA", "").strip()
            if not vessel_name and not via:
                continue
            # Side is a closed vocabulary (PORT/STBD), but its lane sits
            # close enough to "Ops Commenced" that the latter's own DATE
            # token lands in Side instead on a wafer-thin nearest-lane
            # call (its TIME token still lands correctly) -- reattach
            # anything that isn't PORT/STBD to the front of Ops Commenced
            # rather than just discarding it.
            side_tokens = r.get("Side", "").split()
            side = next((tok for tok in side_tokens if tok.upper() in ("PORT", "STBD")), None)
            stray_tokens = [tok for tok in side_tokens if tok.upper() not in ("PORT", "STBD")]
            ops_commenced_raw = " ".join(stray_tokens + [r.get("Ops Commenced", "")]).strip()
            fields = {
                "terminal_code": self.terminal_code,
                "berth_no": berth_no,
                "vessel_name": vessel_name,
                "via_no": via or None,
                "loa_m": _to_float(r.get("LOA", "")),
                "draft_m": _to_float(r.get("Draft", "")),
                "side": side,
                "alongside_at": parse_relative_datetime(r.get("Alongside", ""), report_date),
                "ops_commenced_at": parse_relative_datetime(ops_commenced_raw, report_date),
                "ops_completed_at": parse_relative_datetime(r.get("Ops Completed", ""), report_date),
                "next_event_at": parse_relative_datetime(r.get("ETC", ""), report_date),
                "import_moves": _to_int(r.get(imp_label, "")),
                "export_moves": _to_int(r.get(exp_label, "")),
            }
            rows.append(ScrapedRow(section="berthed", fields=fields, raw=r))
        return rows

    def _parse_expected(self, words: list[dict], report_date) -> list[ScrapedRow]:
        # This page also carries two "ON BERTH VESSEL" panels above this
        # one, repeating the same VIA/LOA column labels in their own
        # headers -- anchor past those so the lanes bind to *this*
        # panel's header row, not an earlier one (see module docstring).
        expected_panel_boxes = find_phrase_boxes(words, "Vessels Expected")
        top_after = min((b["top"] for b in expected_panel_boxes), default=None)

        eta_boxes = [b for b in find_phrase_boxes(words, "ETA") if b["top"] >= top_after]
        header_row_top = min((b["top"] for b in eta_boxes), default=top_after)
        _pick_gate_cutoff_word(words, header_row_top)

        raw_rows = snap_table_by_headers(
            words,
            header_labels=EXPECTED_HEADERS + [
                "ETA", "Gate Open", "Reefer Opening", "Reefer Cut-Off", _GATE_CUTOFF_SENTINEL,
            ],
            top_after=top_after,
            bottom_before_labels=EXPECTED_STOP_BEFORE,
        )

        rows = []
        for r in raw_rows:
            via = r.get("VIA", "").strip()
            if not via:
                continue
            # LOA and Line each have unlabeled columns to their right
            # (gate/reefer/cutoff date-times; Imp/Exp counts) with no
            # lane of their own, so they pick up that text too -- the
            # real value is always the first token (see module
            # docstring).
            loa_tokens = r.get("LOA", "").split()
            line_tokens = r.get("Line", "").split()
            # Service instead has unlabeled columns to its *left* (the
            # same gate/reefer/cutoff date-times, closer to Service's
            # lane than to LOA's), so here the real value is the *last*
            # token.
            service_tokens = r.get("Service", "").split()
            fields = {
                "terminal_code": self.terminal_code,
                "via_no": via,
                "vessel_name": r.get("Vessel Name", "").strip() or None,
                "loa_m": _to_float(loa_tokens[0]) if loa_tokens else None,
                "service": service_tokens[-1] if service_tokens else None,
                "shipping_line": line_tokens[0] if line_tokens else None,
                "agent": None,  # not published as a distinct field in this report
                "eta": parse_relative_datetime(r.get("ETA", ""), report_date),
                "gate_cutoff": parse_relative_datetime(r.get(_GATE_CUTOFF_SENTINEL, ""), report_date),
            }
            rows.append(ScrapedRow(section="expected", fields=fields, raw=r))

        return rows
