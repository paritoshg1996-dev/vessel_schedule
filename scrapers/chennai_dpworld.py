"""
Chennai Container Terminal (CCT) -- DP World's own terminal at Chennai
Port, discovered the same way as MICT (see scrapers/dpworld_contenthub.py
for the shared GraphQL discovery mechanism); this terminal's own
`ports_and_terminals_id` is "DP.PortsandTerminals.ChennaiCCT", confirmed
from the berthing-report page's own CMS content fields the same way
MICT's was.

Validated 2026-09-12 against a live fetch. Single page, but a genuinely
richer/more compressed layout than MICT's:

ON BERTH PANEL -- four berths (CTB IV/III/II/I) laid out as side-by-side
VERTICAL key-value blocks (VESSEL / IGM DTD / VIA-LOA / SVS+AGENT /
ARRIVED / BERTHED / ETC, each printed as "LABEL value" on its own line),
not a row-per-vessel table -- at most one vessel per berth. Each of the
7 row labels (VESSEL, IGM DTD, VIA/LOA, SVS, ARRIVED, BERTHED, ETC)
repeats once per berth at a different x-position, so `_parse_berth_panel`
below buckets words into an x-window per berth (midpoint between each
berth's own title and its neighbours') rather than using
`snap_table_by_headers` at all -- this isn't a table, it's four parallel
label:value lists. CTB II was vacant on the day this was checked (no
words at all under its labels, not just blank cells) -- confirmed at
the word-position level, so "no vessel" here is real, not a parsing
miss. "SVS" holds SERVICE then AGENT as two space-separated tokens
("FIX1 SNL" -> service FIX1, agent SNL); "ARRIVED" is anchorage arrival
(no field for this in our schema, left in raw only) while "BERTHED" is
when she actually came alongside -> `alongside_at`.

EXPECTED-VESSELS TABLE. Two real bugs hit here, both fixed generically
rather than by hand-tuning this one report:

1. The header is printed across THREE slightly different y-baselines
   (170-178pt, a jitter under 8pt total) -- "FIRST"/"AMENDED"/"LOA"/
   "EGMNo./" sit ~3pt above the rest, "ETA"/"DRAFT"/"-Date" (their own
   second header line) sit ~4pt below. Anchoring `top_after` on any ONE
   header word's own top (as every other terminal does) excluded the
   others -- e.g. anchoring on "VesselName" (174.0) silently dropped
   "LOA" (171.2, *above* that threshold) from the header search
   entirely, which then let GATEOPEN's lane swallow LOA's value whole.
   Fixed by computing `top_after` as the MINIMUM top across every
   intended header label, minus a small buffer -- not a new engine
   parameter, just a different (more defensive) way of calling the
   existing one from this scraper.
2. "VIA" (a purely-numeric internal call reference, like the on-berth
   panel's own VIA/LOA numbers -- NOT the carrier's own voyage code,
   which prints separately as "VOY" a few columns over) sits close
   enough to VesselName's lane that a vessel name's first word can tip
   into it on a coin-flip nearest-centroid distance, exactly the "DP
   WORLD JEDDAH" bug already hit and fixed in mundra_adani.py --
   confirmed live on this report too ("DP WORLD THAMIRABARANI" lost its
   "DP"). Same fix: VIA is always digits-only, so a non-numeric tail
   found there is reattached to the front of the vessel name.

ETA is published as two columns that together need a small state
machine, not a plain coalesce: "FIRST ETA" is a bare date (no time);
"AMENDED ETA/ARRD/O\\A" is USUALLY just a time (implicitly the same date
as FIRST), but occasionally a full "DD/MM HHMM HRS" (a real amendment to
a *different* day, overriding FIRST's date entirely) -- `_parse_cct_eta`
below tells the two shapes apart by whether AMENDED's text itself
contains a date. One vessel (INTERASIA INSPIRATION, on the fetch this
was checked against) had been amended *twice*, wrapping its second
revision onto its own physical PDF line with no S.NO/VesselName of its
own -- `_merge_continuation_rows` below detects a row with blank
S.NO+VesselName but non-blank FIRST/AMENDED and folds its AMENDED value
into the row above (the newer of the two revisions), rather than
emitting it as a garbage phantom row or silently dropping it.

GATECUTOFF here (unlike MICT's/dpworld_common's "DD/HHMM"-glued shape)
prints as a normal full "DD-MM-YY HH:MM" -- no month-rollover ambiguity,
parsed directly with `pdf_common.parse_relative_datetime`.

"SECTOR" publishes the vessel's own onward port rotation as a plain
"MAA-KAT-PKG-TAO-BNP-SHA-SHK"-style string -- genuinely valuable (this
is exactly the kind of "next ports" data `service_rotations` currently
has to research by hand, see docs/service_rotations_research_notes.md)
but per-VISIT rather than a named recurring service, and not yet wired
into anything -- kept in `raw` for staging, not promoted to a canonical
column or cross-referenced against service_rotations in this pass.
"EGMNo./ IGM-Date" and "VOY" (the carrier's own voyage code, as opposed
to VIA's internal sequence number) are likewise staged but unmapped.

WHAT'S DELIBERATELY NOT IMPLEMENTED: the "SAILED VESSEL" panel below
the expected table -- consistent with every other source touched this
pass, sailed-vessel capture is out of scope for now.

Confidence: HIGH on the expected-vessel table (checked at the
word-position level, both bugs above caught and fixed against real
data). MEDIUM on the on-berth panel -- the extraction logic is
straightforward key:value reading, but only one live fetch has been
checked and 3 of its 4 berths were vacant that day, so the "real
vessel present" code path has only been exercised once (CTB IV).
"""
from __future__ import annotations

import re
from datetime import date
from typing import Optional

from scrapers.base import ScrapedRow, ScrapeResult, find_phrase_boxes, snap_table_by_headers
from scrapers.dpworld_contenthub import DpWorldContentHubScraper
from scrapers.pdf_common import parse_relative_datetime

BERTH_TITLES = ["CTB IV", "CTB III", "CTB II", "CTB I"]
BERTH_ROW_LABELS = ["VESSEL", "IGM DTD", "VIA/LOA", "SVS", "ARRIVED", "BERTHED", "ETC"]

EXPECTED_HEADERS = [
    "S.NO", "VIA", "VesselName", "FIRST", "AMENDED", "LOA", "GATEOPEN",
    "GATECUTOFF", "SERVICE", "AGENT", "SECTOR", "EGMNo./", "VOY", "IMPORT",
]


def _to_float(s: str):
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _parse_report_date(words: list[dict]) -> Optional[date]:
    """Prints as a bare "12/9/2026" token near the top of the page --
    no label at all, so scan the whole page for the shape directly
    rather than anchoring off adjacent text or a fixed y-position
    (confirmed unique on this report; nothing else on the page uses a
    plain D/D/YYYY shape)."""
    for w in words:
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", w["text"].strip())
        if m:
            d, mo, y = (int(x) for x in m.groups())
            try:
                return date(y, mo, d)
            except ValueError:
                continue
    return None


def _parse_berth_panel(words: list[dict], terminal_code: str, report_date) -> list[ScrapedRow]:
    titles = []
    for label in BERTH_TITLES:
        boxes = find_phrase_boxes(words, label)
        if boxes:
            titles.append((label, boxes[0]["x0"]))
    if not titles:
        return []
    titles.sort(key=lambda t: t[1])

    # The rightmost berth's window has nothing declared to its right to
    # bound it against -- left unbounded, it swallows the "CALENDAR-"
    # wall-calendar block that sits further right on the same lines
    # (caught live: CTB I's vessel name absorbed "MON 7 14 21 28" off the
    # calendar). Anchor that edge to the calendar's own x0 instead.
    calendar_boxes = find_phrase_boxes(words, "CALENDAR-")
    page_right_edge = min((b["x0"] for b in calendar_boxes), default=10_000)

    windows = []
    for i, (label, x0) in enumerate(titles):
        left = 0 if i == 0 else (titles[i - 1][1] + x0) / 2
        right = ((x0 + page_right_edge) / 2) if i == len(titles) - 1 else (x0 + titles[i + 1][1]) / 2
        windows.append((label, left, right))

    rows = []
    for berth_label, left, right in windows:
        values = {}
        for row_label in BERTH_ROW_LABELS:
            label_boxes = [b for b in find_phrase_boxes(words, row_label) if left <= b["x0"] < right]
            if not label_boxes:
                continue
            box = min(label_boxes, key=lambda b: b["top"])
            same_line = sorted(
                [w for w in words
                 if abs(w["top"] - box["top"]) <= 3 and w["x0"] >= box["x1"] and left <= w["x0"] < right],
                key=lambda w: w["x0"],
            )
            values[row_label] = " ".join(w["text"] for w in same_line).strip()

        vessel_name = values.get("VESSEL", "").strip()
        if not vessel_name:
            continue  # vacant berth -- confirmed at word-position level, not a miss (see module docstring)

        svs_tokens = values.get("SVS", "").split()
        via_loa_tokens = values.get("VIA/LOA", "").split()
        fields = {
            "terminal_code": terminal_code,
            "berth_no": berth_label,
            "vessel_name": vessel_name,
            "via_no": via_loa_tokens[0] if via_loa_tokens else None,
            "loa_m": _to_float(via_loa_tokens[1]) if len(via_loa_tokens) > 1 else None,
            "service": svs_tokens[0] if svs_tokens else None,
            "shipping_line": svs_tokens[1] if len(svs_tokens) > 1 else None,
            "alongside_at": parse_relative_datetime(values.get("BERTHED", ""), report_date),
            "next_event_at": parse_relative_datetime(values.get("ETC", ""), report_date),
        }
        rows.append(ScrapedRow(section="berthed", fields=fields, raw=values))
    return rows


def _parse_cct_eta(first_raw: str, amended_raw: str, report_date):
    """FIRST is a bare date ("12-09-26"); AMENDED is usually just a time
    ("1100 HRS" -- same date as FIRST) but sometimes a full "DD/MM HHMM
    HRS" revision to a genuinely different day. Tell them apart by
    whether AMENDED itself carries a date."""
    first_raw, amended_raw = (first_raw or "").strip(), (amended_raw or "").strip()
    m = re.match(r"^(\d{1,2}/\d{1,2})\s+(\d{3,4})\s*HRS", amended_raw, re.I)
    if m:
        hhmm = m.group(2).zfill(4)
        return parse_relative_datetime(f"{m.group(1)} {hhmm[:2]}:{hhmm[2:]}", report_date)
    m = re.match(r"^(\d{3,4})\s*HRS", amended_raw, re.I)
    if m and first_raw:
        hhmm = m.group(1).zfill(4)
        return parse_relative_datetime(f"{first_raw} {hhmm[:2]}:{hhmm[2:]}", report_date)
    if first_raw:
        return parse_relative_datetime(first_raw, report_date)
    return None


def _merge_continuation_rows(raw_rows: list[dict]) -> list[dict]:
    """A vessel amended more than once wraps its later revision(s) onto
    their own physical PDF line, with no S.NO/VesselName -- fold each
    continuation's AMENDED text into the row above (the newer revision
    wins) instead of emitting it as its own phantom row."""
    merged: list[dict] = []
    for r in raw_rows:
        is_continuation = not r.get("S.NO", "").strip() and not r.get("VesselName", "").strip()
        if is_continuation and merged:
            if r.get("AMENDED", "").strip():
                merged[-1]["AMENDED"] = r["AMENDED"].strip()
            continue
        merged.append(r)
    return merged


def _parse_expected(words: list[dict], terminal_code: str, report_date) -> list[ScrapedRow]:
    # The header prints across a ~7pt jitter band -- anchoring top_after
    # on any single header word's own top can exclude others outside
    # that word's own tolerance window (see module docstring point 1).
    header_tops = []
    for label in EXPECTED_HEADERS:
        boxes = find_phrase_boxes(words, label)
        if boxes:
            header_tops.append(min(b["top"] for b in boxes))
    if not header_tops:
        return []
    top_after = min(header_tops) - 2

    raw_rows = snap_table_by_headers(
        words, header_labels=EXPECTED_HEADERS,
        top_after=top_after, bottom_before_labels=["SAILED VESSEL"],
    )
    raw_rows = _merge_continuation_rows(raw_rows)

    rows = []
    for r in raw_rows:
        via = r.get("VIA", "").strip()
        vessel_name = r.get("VesselName", "").strip()
        # VIA is always digits-only -- a vessel name's short first word
        # ("DP" in "DP WORLD THAMIRABARANI") can tip into this lane on a
        # near-tied nearest-centroid call; reattach it (see module
        # docstring point 2, same fix as mundra_adani.py's DP WORLD bug).
        m = re.match(r"^([\d,]*)\s*(.*)$", via)
        via_digits, via_overflow = (m.group(1), m.group(2)) if m else (via, "")
        if via_overflow:
            vessel_name = f"{via_overflow} {vessel_name}".strip()
        if not via_digits and not vessel_name:
            continue

        agent = r.get("AGENT", "").strip() or None
        fields = {
            "terminal_code": terminal_code,
            "via_no": via_digits or None,
            "vessel_name": vessel_name or None,
            "loa_m": _to_float(r.get("LOA", "")),
            "service": r.get("SERVICE", "").strip() or None,
            "shipping_line": agent,
            "agent": agent,
            "eta": _parse_cct_eta(r.get("FIRST", ""), r.get("AMENDED", ""), report_date),
            "gate_cutoff": parse_relative_datetime(r.get("GATECUTOFF", ""), report_date),
        }
        rows.append(ScrapedRow(section="expected", fields=fields, raw=r))
    return rows


class ChennaiDpWorldScraper(DpWorldContentHubScraper):
    terminal_code = "CCT"
    ports_and_terminals_id = "DP.PortsandTerminals.ChennaiCCT"

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        report_date = _parse_report_date(words)
        rows = []
        rows += _parse_berth_panel(words, self.terminal_code, report_date)
        rows += _parse_expected(words, self.terminal_code, report_date)
        return ScrapeResult(report_date=report_date, rows=rows)
