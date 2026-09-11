"""
Shared machinery for the five PDF-based terminal scrapers. Each terminal
module (apmt.py, nsict.py, nsigt.py, bmct.py, nsft.py) subclasses
PdfTerminalScraper and only supplies parse_words() -- the header labels to
look for and how to map them to our canonical fields. fetch(), PDF
opening, and report-date extraction live here once.
"""
from __future__ import annotations

import io
import re
from datetime import date, datetime
from typing import Optional

import pdfplumber
import requests
from dateutil import parser as dateutil_parser

from scrapers.base import FetchError, ParseError, ScrapeResult, TerminalScraper, find_phrase_boxes


class PdfTerminalScraper(TerminalScraper):
    scope = "terminal"

    def __init__(self, url: str, fixture_path: Optional[str] = None):
        self.url = url
        self.fixture_path = fixture_path  # for tests/demo: read local PDF bytes instead of the network

    def fetch(self) -> bytes:
        if self.fixture_path:
            with open(self.fixture_path, "rb") as f:
                return f.read()
        try:
            resp = requests.get(self.url, timeout=self.timeout_seconds, headers={
                "User-Agent": "Mozilla/5.0 (compatible; vessel-schedule-bot/1.0)"
            })
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as e:
            raise FetchError(f"[{self.terminal_code}] could not fetch {self.url}: {e}") from e

    def parse(self, raw_content: bytes) -> ScrapeResult:
        try:
            pdf = pdfplumber.open(io.BytesIO(raw_content))
        except Exception as e:
            raise ParseError(f"[{self.terminal_code}] not a readable PDF: {e}") from e
        try:
            page = pdf.pages[0]
            words = page.extract_words()
            if not words:
                raise ParseError(f"[{self.terminal_code}] PDF had no extractable text (scanned image?)")
            return self.parse_words(words)
        finally:
            pdf.close()

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        raise NotImplementedError


def extract_label_value(words: list[dict], label: str, max_x_gap: float = 220, same_line_tol: float = 4) -> Optional[str]:
    """Find `label` on the page, then read whatever text sits to its right
    on the same visual line. Used for one-off fields like the report date
    ("Date : 09 SEP 2026") where trusting linear text order risks grabbing
    an unrelated number that happens to follow the label in the stream."""
    boxes = find_phrase_boxes(words, label)
    if not boxes:
        return None
    box = boxes[0]
    same_line = sorted(
        [w for w in words if abs(w["top"] - box["top"]) <= same_line_tol and w["x0"] >= box["x1"]],
        key=lambda w: w["x0"],
    )
    value_words, last_x1 = [], box["x1"]
    for w in same_line:
        if w["x0"] - last_x1 > max_x_gap:
            break
        value_words.append(w["text"])
        last_x1 = w["x1"]
    joined = " ".join(value_words).strip()
    return joined or None


def parse_report_date(words: list[dict], label_candidates: list[str]) -> Optional[date]:
    for label in label_candidates:
        raw = extract_label_value(words, label)
        if not raw:
            continue
        try:
            return dateutil_parser.parse(raw, dayfirst=True, fuzzy=True).date()
        except (ValueError, OverflowError):
            continue
    return None


def parse_relative_datetime(s: Optional[str], report_date: Optional[date],
                             max_backward_days: int = 30):
    """Parse a date/time string that omits the year (common across these
    reports -- "10-Sep 08:00", "Thu/10/09 06:00") anchored to the report's
    own date, so a same-day fetch can't mis-attribute one: dateutil fills
    in whatever year `report_date` carries, and if the result still lands
    more than `max_backward_days` before `report_date`, we assume it
    actually belongs to next year (handles a report run near year-end
    whose date is really next January) and correct for it.

    Returns None on a blank/unparseable string or a missing report_date.
    """
    s = (s or "").strip()
    if not s or report_date is None:
        return None
    try:
        dt = dateutil_parser.parse(s, dayfirst=True,
                                    default=datetime(report_date.year, 1, 1))
    except (ValueError, OverflowError):
        return None
    if (dt.date() - report_date).days < -max_backward_days:
        dt = dt.replace(year=dt.year + 1)
    return dt


def parse_gate_cutoff(s: Optional[str], report_date: Optional[date],
                       max_backward_days: int = 20, near: Optional[datetime] = None):
    """"10/1500" -- day and 24h time glued together, with NO month at all
    (unlike ETA, which at least carries day/month). Anchored to the
    report's own month/year, with a rollover check for a cutoff landing
    just after month-end. Originally written for NSICT/NSIGT
    (dpworld_common.py); promoted here once MICT's own "CUT-OFF" column
    turned out to print the exact same shape (see scrapers/mict.py) --
    one parser, not two copies to keep in sync.

    `near` (added for MICT): pass this row's own already-parsed `eta`
    when the caller has one. NSICT/NSIGT's cutoffs are always within a
    day or two of the report itself, so the plain report_date + a fixed
    `max_backward_days` threshold was fine -- but MICT's "vessels
    expected" list runs three-plus weeks out, and CAUGHT LIVE: a cutoff
    of "01/1600" against a report_date of the 11th naively reads as the
    1st of the SAME month (10 days in the past, i.e. under any sane
    max_backward_days threshold) when it actually belonged to next
    month, matching a vessel whose own ETA was three weeks later still.
    A fixed distance-from-report_date threshold can't tell those two
    cases apart; comparing against the row's OWN eta (which carries a
    real month, unlike this column) can. When `near` is given, this
    replaces the max_backward_days heuristic entirely: whichever of
    "report_date's month" or "the next month" lands the cutoff closer
    to `near` wins."""
    s = (s or "").strip()
    if not s or report_date is None:
        return None
    m = re.match(r"^(\d{1,2})/(\d{3,4})$", s)
    if not m:
        return None
    day = int(m.group(1))
    hhmm = m.group(2).zfill(4)
    hour, minute = int(hhmm[:2]), int(hhmm[2:])

    next_month, next_year = report_date.month + 1, report_date.year
    if next_month > 12:
        next_month, next_year = 1, next_year + 1

    def _build(year, month):
        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None

    dt = _build(report_date.year, report_date.month)
    if dt is None:
        return None

    if near is not None:
        dt_next = _build(next_year, next_month)
        if dt_next is not None and abs((dt_next - near).total_seconds()) < abs((dt - near).total_seconds()):
            dt = dt_next
        return dt

    if (dt.date() - report_date).days < -max_backward_days:
        dt = _build(next_year, next_month) or dt
    return dt


def insert_glued_time_colon(s: Optional[str]) -> str:
    """Some sources (Adani's Mundra PDF) glue a bare 4-digit HHMM straight
    onto the end of a date string with no separator at all -- "12-Sep
    0300", "13-Sep Sat 1600" -- unlike JNPT's own reports, which at least
    put a colon or a "/" between date and time. dateutil reads a bare
    trailing "0300" as more date digits, not a time, unless something
    marks it as one. Inserts ":" before the last two digits of a
    trailing exactly-4-digit run and returns the result for
    `parse_relative_datetime` to parse normally; a no-op (returns the
    stripped input) on any string that doesn't end that way."""
    s = (s or "").strip()
    m = re.match(r"^(.*\D)(\d{2})(\d{2})$", s)
    if not m:
        return s
    return f"{m.group(1).strip()} {m.group(2)}:{m.group(3)}"


def disambiguate_leftmost(words: list[dict], text: str, near_top: float,
                          tolerance: float = 3.0) -> str:
    """Some report headers repeat a bare word on its own header row --
    e.g. "Imp" appearing both as its own column AND inside "Imp Bal" a
    few columns over -- so a plain search for it is ambiguous. Find
    every word matching `text` (case-insensitive) within `tolerance` of
    `near_top`; if there are two or more, relabel the LEFTMOST with a
    private sentinel and return that sentinel, so a lane search can bind
    to exactly the intended one. Returns `text` unchanged when there's
    nothing ambiguous to resolve (0 or 1 matches) -- callers should
    search for whatever this returns, not the original `text`."""
    candidates = [w for w in words
                  if w["text"].strip().upper() == text.upper() and abs(w["top"] - near_top) < tolerance]
    if len(candidates) < 2:
        return text
    target = min(candidates, key=lambda w: w["x0"])
    sentinel = f"__DISAMBIG_{text.upper().replace(' ', '_')}__"
    target["text"] = sentinel
    return sentinel


def merge_column_by_row(rows: list[dict], words: list[dict], header_label: str,
                         target_key: str, row_tolerance: float = 3.0) -> None:
    """Best-effort cross-panel merge: some terminals (NSFT) print the
    vessel-name list as its own panel rather than a column inside the main
    expected/berthed/sailed table. If we can find a `header_label` column
    elsewhere on the page, pull in whichever word sits at the same 'top'
    (row position) as each already-extracted row and store it under
    target_key. Mutates `rows` in place; leaves target_key unset on any
    row it can't confidently match, rather than guessing.

    This only works when the panel is genuinely row-aligned with the table
    already extracted -- true for an Excel-style export, but exact pixel
    alignment can vary by terminal. Treat merged values as best-effort
    until spot-checked against a real, live-fetched copy of that report.
    """
    boxes = find_phrase_boxes(words, header_label)
    if not boxes or "_row_top" not in (rows[0] if rows else {}):
        return
    col_x = (boxes[0]["x0"] + boxes[0]["x1"]) / 2
    header_bottom = boxes[0]["bottom"]
    candidates = [w for w in words if w["top"] > header_bottom + 1 and abs((w["x0"] + w["x1"]) / 2 - col_x) < 120]
    for row in rows:
        row_top = row.get("_row_top")
        if row_top is None:
            continue
        same_row = sorted(
            [w for w in candidates if abs(w["top"] - row_top) <= row_tolerance],
            key=lambda w: w["x0"],
        )
        if same_row:
            row[target_key] = " ".join(w["text"] for w in same_row).strip()
